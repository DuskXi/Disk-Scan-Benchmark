<#
.SYNOPSIS
    Windows NTFS/ReFS Dynamic VHDX Manager & Cold-Cache Evictor for disk-scanner-bench
.DESCRIPTION
    Supports three subcommands:
      .\windows_vhd.ps1 create <size_gb> <mount_path> [ntfs|refs]
      .\windows_vhd.ps1 purge-cache <mount_path>
      .\windows_vhd.ps1 teardown <mount_path>
      .\windows_vhd.ps1 defender-on <mount_path>
#>
param(
    [Parameter(Mandatory=$true, Position=0)]
    [ValidateSet("create", "purge-cache", "teardown", "defender-on")]
    [string]$Action,

    [Parameter(Position=1)]
    [string]$Arg1 = "60",

    [Parameter(Position=2)]
    [string]$Arg2 = "X:\",

    [Parameter(Position=3)]
    [ValidateSet("ntfs", "refs", "btrfs")]
    [string]$FsType = "ntfs"
)

$ErrorActionPreference = "Stop"

function Get-VhdPath([string]$Letter, [int64]$VirtualGb = 0) {
    # One backing VHDX per drive letter so NTFS and ReFS volumes can coexist. The chosen location is remembered in a
    # small state file so purge-cache / teardown find the same image.
    $State = Join-Path $env:TEMP "disk_scanner_bench_${Letter}.vhdpath"
    if ($VirtualGb -le 0 -and (Test-Path $State)) {
        return (Get-Content -Path $State -Raw).Trim()
    }
    # On GitHub-hosted runners RUNNER_TEMP lives on the D: scratch drive (~146 GB free) while the system drive C: has
    # only ~30 GB free. The dynamic VHDX of the 3M-file preset grew past that and C: filled up completely, which made
    # the virtual disk vanish (os error 433) - so D: is the right place. BENCH_VHD_DRIVE=system forces C: if needed.
    $Base = if ($env:RUNNER_TEMP) { $env:RUNNER_TEMP } else { $env:TEMP }
    if ($env:BENCH_VHD_DRIVE -eq "system") { $Base = $env:TEMP }
    $Path = Join-Path $Base "disk_scanner_bench_${Letter}.vhdx"
    Set-Content -Path $State -Value $Path -Encoding ASCII
    return $Path
}

function Get-DriveLetterFromPath([string]$PathStr) {
    $clean = $PathStr.Trim()
    if ($clean -match "^([A-Za-z]):?") {
        return $Matches[1].ToUpper()
    }
    return "X"
}

function Invoke-DiskpartScript([string]$ScriptContent) {
    $tmpScript = Join-Path $env:TEMP ("diskpart_" + [guid]::NewGuid().ToString("N") + ".txt")
    Set-Content -Path $tmpScript -Value $ScriptContent -Encoding ASCII
    try {
        $out = & diskpart /s $tmpScript 2>&1
        if ($LASTEXITCODE -ne 0) {
            throw "diskpart failed ($LASTEXITCODE): $out"
        }
    } finally {
        Remove-Item -Path $tmpScript -Force -ErrorAction SilentlyContinue
    }
}

function Disable-DefenderForBench([string]$Letter, [string]$Vhd) {
    # Turn Defender real-time scanning off and exclude the benchmark volume BEFORE the VHDX is mounted, so neither the
    # mount nor the millions of file creations are scanned. Failures used to be swallowed silently; verify and report.
    $errors = @()
    try {
        Set-MpPreference -DisableRealtimeMonitoring $true -DisableIOAVProtection $true -DisableBehaviorMonitoring $true `
            -DisableScriptScanning $true -DisableBlockAtFirstSeen $true -DisableArchiveScanning $true `
            -MAPSReporting 0 -SubmitSamplesConsent 2 -ErrorAction Stop
    } catch { $errors += "Set-MpPreference: $($_.Exception.Message)" }
    foreach ($path in @("${Letter}:\", $Vhd, $PWD.Path, $env:TEMP, $env:RUNNER_TEMP)) {
        if (-not $path) { continue }
        try { Add-MpPreference -ExclusionPath $path -ErrorAction Stop } catch { $errors += "Add-MpPreference($path): $($_.Exception.Message)" }
    }
    try { Add-MpPreference -ExclusionProcess "fs-mirage.exe", "hw-probe.exe", "python.exe" -ErrorAction Stop } catch { $errors += "Exclusion process: $($_.Exception.Message)" }

    $rtDisabled = "unknown"; $tamper = "unknown"; $rtEnabled = "unknown"
    try { $rtDisabled = (Get-MpPreference -ErrorAction Stop).DisableRealtimeMonitoring } catch {}
    try {
        $st = Get-MpComputerStatus -ErrorAction Stop
        $rtEnabled = $st.RealTimeProtectionEnabled
        $tamper = $st.IsTamperProtected
    } catch {}
    Write-Host "[windows_vhd] Defender status: DisableRealtimeMonitoring=$rtDisabled RealTimeProtectionEnabled=$rtEnabled IsTamperProtected=$tamper"
    foreach ($e in $errors) { Write-Warning "[windows_vhd] Defender: $e" }
    if ($rtEnabled -eq $true) {
        Write-Warning "[windows_vhd] Defender real-time protection is STILL ENABLED; file creation / scan timings will include its overhead."
    }
}

function New-BenchVhdx([string]$Path, [uint64]$SizeBytes, [uint32]$BlockBytes) {
    # A dynamic VHDX allocates a whole payload block (default 32 MB) the first time any byte inside it is written.
    # NTFS metadata for millions of files is scattered over the volume, so with 32 MB blocks 100k files already grew the
    # image by 7 GB (measured: 1 GB with 1 MB blocks) and the 3M-file preset filled the runner's disk (os error 433).
    # New-VHD and diskpart can not be told about this reliably, so the image is created through virtdisk.dll directly.
    if (-not ("BenchVhd" -as [type])) {
        Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
public static class BenchVhd {
    [StructLayout(LayoutKind.Sequential)]
    public struct VIRTUAL_STORAGE_TYPE { public uint DeviceId; public Guid VendorId; }
    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    public struct CREATE_VIRTUAL_DISK_PARAMETERS_V1 {
        public uint Version;
        public Guid UniqueId;
        public ulong MaximumSize;
        public uint BlockSizeInBytes;
        public uint SectorSizeInBytes;
        public string ParentPath;
        public string SourcePath;
    }
    [DllImport("virtdisk.dll", CharSet = CharSet.Unicode)]
    static extern uint CreateVirtualDisk(ref VIRTUAL_STORAGE_TYPE type, string path, uint access, IntPtr sd, uint flags,
        uint providerFlags, ref CREATE_VIRTUAL_DISK_PARAMETERS_V1 parameters, IntPtr overlapped, out IntPtr handle);
    [DllImport("kernel32.dll")] static extern bool CloseHandle(IntPtr h);
    public static uint Create(string path, ulong size, uint block) {
        VIRTUAL_STORAGE_TYPE t = new VIRTUAL_STORAGE_TYPE();
        t.DeviceId = 3; // VIRTUAL_STORAGE_TYPE_DEVICE_VHDX
        t.VendorId = new Guid("EC984AEC-A0F9-47e9-901F-71415A66345B");
        CREATE_VIRTUAL_DISK_PARAMETERS_V1 p = new CREATE_VIRTUAL_DISK_PARAMETERS_V1();
        p.Version = 1; p.MaximumSize = size; p.BlockSizeInBytes = block; p.SectorSizeInBytes = 512;
        IntPtr h;
        uint rc = CreateVirtualDisk(ref t, path, 0x00100000, IntPtr.Zero, 0, 0, ref p, IntPtr.Zero, out h);
        if (rc == 0) CloseHandle(h);
        return rc;
    }
}
"@
    }
    $rc = [BenchVhd]::Create($Path, $SizeBytes, $BlockBytes)
    if ($rc -ne 0) { throw "CreateVirtualDisk failed with Win32 error $rc" }
}

$HasHyperVCmdlets = [bool](Get-Command New-VHD -ErrorAction SilentlyContinue)

function Wait-BenchVolume([string]$Letter, [string]$FileSystem) {
    # After attach the letter comes back within a second on NTFS/ReFS; WinBtrfs mounts its own volume device and can
    # take longer, or (rarely) come back without the letter, in which case it is mounted at the letter again.
    for ($i = 0; $i -lt 60; $i++) {
        if (Test-Path "${Letter}:\") {
            if (-not $FileSystem -or ((fsutil fsinfo volumeinfo "${Letter}:" | Out-String) -match $FileSystem)) { return }
        }
        if ($i -eq 20 -and $FileSystem) {
            $vol = Get-CimInstance Win32_Volume -Filter "FileSystem='$FileSystem'" -ErrorAction SilentlyContinue | Select-Object -First 1
            if ($vol) { mountvol "${Letter}:" $vol.DeviceID | Out-Null }
        }
        Start-Sleep -Seconds 1
    }
    if (-not (Test-Path "${Letter}:\")) { throw "Volume ${Letter}: did not come back" }
}

switch ($Action) {
    "create" {
        $SizeGb = [int64]$Arg1
        $DriveLetter = Get-DriveLetterFromPath $Arg2
        $VhdPath = Get-VhdPath $DriveLetter $SizeGb
        $FsName = $FsType.ToUpper()
        Write-Host "[windows_vhd] Creating ${SizeGb}GB Dynamic $FsName VHDX at $VhdPath (Drive ${DriveLetter}:)..."
        Disable-DefenderForBench $DriveLetter $VhdPath

        if (Test-Path $VhdPath) {
            try {
                if ($HasHyperVCmdlets) {
                    Dismount-VHD -Path $VhdPath -ErrorAction SilentlyContinue
                } else {
                    Invoke-DiskpartScript "select vdisk file=`"$VhdPath`"`r`ndetach vdisk`r`n"
                }
            } catch {}
            Remove-Item -Path $VhdPath -Force -ErrorAction SilentlyContinue
        }

        New-BenchVhdx -Path $VhdPath -SizeBytes ([uint64]$SizeGb * 1GB) -BlockBytes 1MB
        Write-Host "[windows_vhd] VHDX created with 1 MB payload blocks (Hyper-V cmdlets available: $HasHyperVCmdlets)"
        if ($HasHyperVCmdlets) {
            $disk = Mount-VHD -Path $VhdPath -Passthru | Get-Disk
            Initialize-Disk -Number $disk.Number -PartitionStyle GPT -ErrorAction SilentlyContinue
            $part = New-Partition -DiskNumber $disk.Number -UseMaximumSize -DriveLetter $DriveLetter
            if ($FsType -ne "btrfs") {
                Format-Volume -DriveLetter $DriveLetter -FileSystem $FsName -NewFileSystemLabel "BenchVol" -Confirm:$false | Out-Null
            }
        } else {
            $dp = @"
select vdisk file="$VhdPath"
attach vdisk
convert gpt
create partition primary
assign letter=$DriveLetter
"@
            if ($FsType -ne "btrfs") { $dp = $dp -replace "create partition primary", "create partition primary`r`nformat fs=$FsType label=`"BenchVol`" quick" }
            Invoke-DiskpartScript $dp
        }
        if ($FsType -eq "btrfs") {
            # WinBtrfs (scripts/disk-mgr/install_winbtrfs.ps1) formats the raw partition and mounts it itself
            & (Join-Path $env:WINBTRFS_DIR "mkbtrfs.exe") "${DriveLetter}:" BenchVol
            Wait-BenchVolume $DriveLetter "Btrfs"
        }
        New-Item -ItemType Directory -Path "${DriveLetter}:\bench" -Force | Out-Null

        try {
            & fsutil 8dot3name set "${DriveLetter}:" 1 | Out-Null
            & fsutil behavior set disablelastaccess 1 | Out-Null
        } catch {}
        Write-Host "[windows_vhd] Mounted $FsName volume at ${DriveLetter}:\bench (8.3 names and last-access updates disabled)"
    }

    "purge-cache" {
        $DriveLetter = Get-DriveLetterFromPath $Arg1
        $VhdPath = Get-VhdPath $DriveLetter
        Write-Host "[windows_vhd] Evicting Windows NTFS cache via Dismount-VHD + Host VHDX Unbuffered Cache Purge + Mount-VHD on ${DriveLetter}:..."
        if (-not (Test-Path $VhdPath)) {
            Write-Warning "[windows_vhd] VHDX not found at $VhdPath; skipping VHD remount."
            exit 0
        }

        if (Get-Command Write-VolumeCache -ErrorAction SilentlyContinue) {
            Write-VolumeCache -DriveLetter $DriveLetter -ErrorAction SilentlyContinue
        }

        if ($HasHyperVCmdlets) {
            Dismount-VHD -Path $VhdPath
        } else {
            $dp = @"
select vdisk file="$VhdPath"
detach vdisk
"@
            Invoke-DiskpartScript $dp
        }

        # While the VHDX is dismounted and has no open cached handles, opening it on the host C:\ drive
        # with FILE_FLAG_NO_BUFFERING (0x20000000) forces the Windows NT Cache Manager (CcPurgeCacheSection)
        # to evict all cached pages of the VHDX backing file from host RAM.
        try {
            $fs = New-Object System.IO.FileStream(
                $VhdPath,
                [System.IO.FileMode]::Open,
                [System.IO.FileAccess]::Read,
                [System.IO.FileShare]::ReadWrite,
                4096,
                ([System.IO.FileOptions]0x20000000)
            )
            $fs.Close()
        } catch {}

        if ($HasHyperVCmdlets) {
            Mount-VHD -Path $VhdPath | Out-Null
        } else {
            $dp = @"
select vdisk file="$VhdPath"
attach vdisk
"@
            Invoke-DiskpartScript $dp
        }
        Wait-BenchVolume $DriveLetter ""
        Write-Host "[windows_vhd] Cold cache state restored for ${DriveLetter}:\"
    }

    "defender-on" {
        # Scan phase with Defender scanning like on a desktop: real-time protection back on, and neither the benchmark
        # volume nor the scanner binaries (under the repository) excluded. The VHDX file, temp folders (export files)
        # and the harness processes stay excluded. Generation ran with it off, so only the scans pay its cost.
        $DriveLetter = Get-DriveLetterFromPath $Arg1
        $errors = @()
        try {
            Set-MpPreference -DisableRealtimeMonitoring $false -DisableIOAVProtection $false `
                -DisableBehaviorMonitoring $false -DisableScriptScanning $false -ErrorAction Stop
        } catch { $errors += "Set-MpPreference: $($_.Exception.Message)" }
        foreach ($path in @("${DriveLetter}:\", $PWD.Path)) {
            try { Remove-MpPreference -ExclusionPath $path -ErrorAction Stop } catch { $errors += "Remove-MpPreference($path): $($_.Exception.Message)" }
        }
        Start-Sleep -Seconds 3
        $st = Get-MpComputerStatus
        $excl = @((Get-MpPreference).ExclusionPath) -join "; "
        Write-Host "[windows_vhd] Defender for scans: RealTimeProtectionEnabled=$($st.RealTimeProtectionEnabled) OnAccessProtectionEnabled=$($st.OnAccessProtectionEnabled) IsTamperProtected=$($st.IsTamperProtected)"
        Write-Host "[windows_vhd] Remaining exclusions: $excl"
        foreach ($e in $errors) { Write-Warning "[windows_vhd] Defender: $e" }
        if (-not $st.RealTimeProtectionEnabled) {
            throw "Defender real-time protection could not be turned on; the Defender-on scan would measure nothing"
        }
    }

    "teardown" {
        $DriveLetter = Get-DriveLetterFromPath $Arg1
        $VhdPath = Get-VhdPath $DriveLetter
        Write-Host "[windows_vhd] Tearing down ${DriveLetter}: and removing $VhdPath..."
        if (Test-Path $VhdPath) {
            try {
                if ($HasHyperVCmdlets) {
                    Dismount-VHD -Path $VhdPath -ErrorAction SilentlyContinue
                } else {
                    Invoke-DiskpartScript "select vdisk file=`"$VhdPath`"`r`ndetach vdisk`r`n"
                }
            } catch {}
            Remove-Item -Path $VhdPath -Force -ErrorAction SilentlyContinue
        }
        Write-Host "[windows_vhd] Teardown complete."
    }
}
