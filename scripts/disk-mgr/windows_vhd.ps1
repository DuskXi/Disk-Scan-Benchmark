<#
.SYNOPSIS
    Windows NTFS/ReFS Dynamic VHDX Manager & Cold-Cache Evictor for disk-scanner-bench
.DESCRIPTION
    Supports three subcommands:
      .\windows_vhd.ps1 create <size_gb> <mount_path> [ntfs|refs|btrfs]
      .\windows_vhd.ps1 attach <vhdx_path> <mount_path> btrfs|refs   (an image built elsewhere, e.g. btrfs_image.sh)
      .\windows_vhd.ps1 detach <mount_path> <dest_path>   (flush, dismount and move the VHDX to dest_path, kept)
      .\windows_vhd.ps1 freeze <mount_path>   (the volume is kept as it is and a copy of it mounted instead)
      .\windows_vhd.ps1 purge-cache <mount_path>   (after freeze: a fresh copy each time)
      .\windows_vhd.ps1 teardown <mount_path>
      .\windows_vhd.ps1 defender-on <mount_path>
#>
param(
    [Parameter(Mandatory=$true, Position=0)]
    [ValidateSet("create", "attach", "detach", "freeze", "purge-cache", "teardown", "defender-on")]
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
        if (($i -eq 10 -or $i -eq 30) -and $FileSystem) {
            # The letter can stay on the partition's old (raw) volume while the filesystem driver mounts its own volume
            # device: take the letter off the old one and give it to the volume that has the filesystem
            $vol = Get-CimInstance Win32_Volume -Filter "FileSystem='$FileSystem'" -ErrorAction SilentlyContinue | Select-Object -First 1
            if ($vol -and $vol.DriveLetter -ne "${Letter}:") {
                # A volume has one drive letter at a time: drop the one it was given (e.g. E:) before mounting at X:
                if ($vol.DriveLetter) { mountvol $vol.DriveLetter /D 2>$null | Out-Null }
                mountvol "${Letter}:" /D 2>$null | Out-Null
                mountvol "${Letter}:\" $vol.DeviceID | Out-Null
                Write-Host "[windows_vhd] moved the $FileSystem volume from '$($vol.DriveLetter)' to ${Letter}: ($($vol.DeviceID))"
            }
        }
        Start-Sleep -Seconds 1
    }
    if (-not (Test-Path "${Letter}:\")) {
        Write-Host "[windows_vhd] volumes:"
        Get-CimInstance Win32_Volume | Format-Table DriveLetter, FileSystem, Label, Capacity, DeviceID -AutoSize | Out-String -Width 220 | Write-Host
        Get-Partition -ErrorAction SilentlyContinue | Format-Table DiskNumber, PartitionNumber, DriveLetter, Size, Type -AutoSize | Out-String | Write-Host
        mountvol | Write-Host
        throw "Volume ${Letter}: did not come back"
    }
}

function Get-MasterState([string]$Letter) {
    return (Join-Path $env:TEMP "disk_scanner_bench_${Letter}.master")
}

function Purge-HostCache([string]$Path) {
    # With no handle open on it, opening the image with FILE_FLAG_NO_BUFFERING (0x20000000) makes the cache manager
    # (CcPurgeCacheSection) drop every page of it from the host's RAM.
    try {
        $fs = New-Object System.IO.FileStream(
            $Path,
            [System.IO.FileMode]::Open,
            [System.IO.FileAccess]::Read,
            [System.IO.FileShare]::ReadWrite,
            4096,
            ([System.IO.FileOptions]0x20000000)
        )
        $fs.Close()
    } catch {}
}

function Mount-FreshCopy([string]$Letter, [string]$Master) {
    # A new byte-for-byte copy of the frozen volume (unbuffered, robocopy /J), so a scan reads and writes the same
    # blocks as on the volume itself, and the next purge-cache throws the copy away. (A differencing disk is quicker to
    # make, but every write then allocates blocks in the child: on NTFS the cold scans that update access times took
    # 1.3x as long on Windows x64 and 1.7x on ARM64, and WinDirStat's 2.3x on ReFS.)
    $WorkDir = Join-Path (Split-Path -Parent $Master) "bench_copy"
    $Work = Join-Path $WorkDir (Split-Path -Leaf $Master)
    if (Test-Path $Work) {
        Dismount-VHD -Path $Work -ErrorAction SilentlyContinue
        Remove-Item -Path $Work -Force
    }
    New-Item -ItemType Directory -Force -Path $WorkDir | Out-Null
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    & robocopy (Split-Path -Parent $Master) $WorkDir (Split-Path -Leaf $Master) /J /R:1 /W:1 /NJH /NJS /NP /NFL /NDL | Out-Null
    $rc = $LASTEXITCODE
    $global:LASTEXITCODE = 0
    if ($rc -ge 8 -or -not (Test-Path $Work)) { throw "copying $Master failed (robocopy exit $rc)" }
    Purge-HostCache $Work
    Write-Host ("[windows_vhd] fresh copy of the frozen volume ({0:N1} GB) in {1:N0} s" -f ((Get-Item $Work).Length / 1GB), $sw.Elapsed.TotalSeconds)
    Set-Content -Path (Get-MasterState $Letter) -Value $Master -Encoding ASCII
    Set-Content -Path (Join-Path $env:TEMP "disk_scanner_bench_${Letter}.vhdpath") -Value $Work -Encoding ASCII
    Mount-VHD -Path $Work | Out-Null
    $disk = Get-Disk | Where-Object { $_.Location -eq $Work } | Select-Object -First 1
    if (-not $disk) { throw "no disk found for $Work after mounting it" }
    if ($disk.IsOffline) { Set-Disk -Number $disk.Number -IsOffline $false }
    if ($disk.IsReadOnly) { Set-Disk -Number $disk.Number -IsReadOnly $false }
    # the mount manager gives the letter back to the same partition (the copy has the volume's partition GUID); if it
    # does not, the volume gets it here
    for ($i = 0; $i -lt 10 -and -not (Test-Path "${Letter}:\"); $i++) { Start-Sleep -Seconds 1 }
    if (-not (Test-Path "${Letter}:\")) {
        $part = Get-Partition -DiskNumber $disk.Number | Where-Object { $_.Type -eq "Basic" } | Select-Object -First 1
        if ($part) {
            $part | Set-Partition -NewDriveLetter $Letter
            Write-Host "[windows_vhd] gave ${Letter}: to the volume of the copy"
        }
    }
    $FsState = Join-Path $env:TEMP "disk_scanner_bench_${Letter}.fs"
    $Fs = if (Test-Path $FsState) { (Get-Content $FsState -Raw).Trim() } else { "" }
    Wait-BenchVolume $Letter $(if ($Fs -eq "btrfs") { "Btrfs" } else { "" })
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
        Set-Content -Path (Join-Path $env:TEMP "disk_scanner_bench_${DriveLetter}.fs") -Value $FsType -Encoding ASCII
        if ($FsType -eq "btrfs") {
            # WinBtrfs (scripts/disk-mgr/install_winbtrfs.ps1) formats the raw partition and mounts it itself
            & (Join-Path $env:WINBTRFS_DIR "mkbtrfs.exe") "${DriveLetter}:" BenchVol
            Wait-BenchVolume $DriveLetter "Btrfs"
        }
        New-Item -ItemType Directory -Path "${DriveLetter}:\bench" -Force | Out-Null

        # last-access updates off for clean timings, or on (the daily-use setting) with BENCH_ATIME=daily; NTFS reads
        # it when a volume is mounted, so every remount of purge-cache applies it
        $LastAccessOff = if ($env:BENCH_ATIME -eq "daily") { 0 } else { 1 }
        try {
            & fsutil 8dot3name set "${DriveLetter}:" 1 | Out-Null
            & fsutil behavior set disablelastaccess $LastAccessOff | Out-Null
        } catch {}
        Write-Host "[windows_vhd] Mounted $FsName volume at ${DriveLetter}:\bench (8.3 names off, last-access updates $(if ($LastAccessOff) { 'off' } else { 'on' }))"
    }

    "attach" {
        # A disk image built elsewhere (scripts/disk-mgr/btrfs_image.sh builds the Btrfs tree on Linux): attached as it
        # is, then purge-cache and teardown work on it like on a created one
        $VhdPath = (Resolve-Path $Arg1).Path
        $DriveLetter = Get-DriveLetterFromPath $Arg2
        Set-Content -Path (Join-Path $env:TEMP "disk_scanner_bench_${DriveLetter}.vhdpath") -Value $VhdPath -Encoding ASCII
        Set-Content -Path (Join-Path $env:TEMP "disk_scanner_bench_${DriveLetter}.fs") -Value $FsType -Encoding ASCII
        Write-Host "[windows_vhd] Attaching $VhdPath ($([math]::Round((Get-Item $VhdPath).Length / 1MB)) MB on disk) at ${DriveLetter}:..."
        Disable-DefenderForBench $DriveLetter $VhdPath
        if ($HasHyperVCmdlets) {
            Mount-VHD -Path $VhdPath | Out-Null
        } else {
            Invoke-DiskpartScript "select vdisk file=`"$VhdPath`"`r`nattach vdisk`r`n"
        }
        $disk = Get-Disk | Where-Object { $_.Location -eq $VhdPath } | Select-Object -First 1
        if ($disk) {
            if ($disk.IsOffline) { Set-Disk -Number $disk.Number -IsOffline $false }
            if ($disk.IsReadOnly) { Set-Disk -Number $disk.Number -IsReadOnly $false }
            Get-Partition -DiskNumber $disk.Number -ErrorAction SilentlyContinue |
                Format-Table DiskNumber, PartitionNumber, DriveLetter, Size, Type, GptType -AutoSize | Out-String | Write-Host
        } else {
            Write-Warning "[windows_vhd] no disk found for $VhdPath after attaching"
        }
        $FsName = if ($FsType -eq "btrfs") { "Btrfs" } else { $FsType.ToUpper() }
        Wait-BenchVolume $DriveLetter $FsName
        $LastAccessOff = if ($env:BENCH_ATIME -eq "daily") { 0 } else { 1 }
        try { & fsutil behavior set disablelastaccess $LastAccessOff | Out-Null } catch {}
        Write-Host "[windows_vhd] $FsName volume from $VhdPath mounted at ${DriveLetter}:\"
    }

    "detach" {
        # The disk is handed to another job (ReFS: one job builds the tree, the next scans it): flush the volume,
        # dismount the VHDX cleanly and move it to the destination, keeping it
        $DriveLetter = Get-DriveLetterFromPath $Arg1
        $VhdPath = Get-VhdPath $DriveLetter
        $Dest = $Arg2
        if (Get-Command Write-VolumeCache -ErrorAction SilentlyContinue) {
            Write-VolumeCache -DriveLetter $DriveLetter -ErrorAction SilentlyContinue
        }
        if ($HasHyperVCmdlets) {
            Dismount-VHD -Path $VhdPath
        } else {
            Invoke-DiskpartScript "select vdisk file=`"$VhdPath`"`r`ndetach vdisk`r`n"
        }
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Dest) | Out-Null
        Move-Item -Path $VhdPath -Destination $Dest -Force
        Write-Host "[windows_vhd] Detached ${DriveLetter}: and kept the image at $Dest ($([math]::Round((Get-Item $Dest).Length / 1GB, 2)) GB on disk)"
    }

    "freeze" {
        # Daily-use access times without setting them back before every scan (a million files took 3-5 minutes, on
        # Windows ARM64, where Defender's real-time scanning can not be turned off, over 20): the volume, whose access
        # times the caller set back once, is kept as it is, and from now on each purge-cache mounts a fresh copy of it,
        # so every cold scan meets the same old access times on the same blocks. Needs room for one copy; without it
        # (exit 1) the caller sets the access times back before each scan instead.
        $DriveLetter = Get-DriveLetterFromPath $Arg1
        $Base = Get-VhdPath $DriveLetter
        if (-not $HasHyperVCmdlets) { throw "freeze needs the Hyper-V cmdlets (Mount-VHD)" }
        if (Test-Path (Get-MasterState $DriveLetter)) { throw "${DriveLetter}: is frozen already" }
        $Size = (Get-Item $Base).Length
        $Free = (Get-PSDrive -Name (Split-Path -Qualifier $Base).TrimEnd(":")).Free
        if ($Free -lt $Size + 10GB) {
            Write-Warning ("[windows_vhd] not freezing ${DriveLetter}: a copy of the {0:N1} GB volume needs more than the {1:N1} GB free" -f ($Size / 1GB), ($Free / 1GB))
            exit 1
        }
        if (Get-Command Write-VolumeCache -ErrorAction SilentlyContinue) {
            Write-VolumeCache -DriveLetter $DriveLetter -ErrorAction SilentlyContinue
        }
        Dismount-VHD -Path $Base
        try {
            Mount-FreshCopy $DriveLetter $Base
        } catch {
            Write-Warning "[windows_vhd] freeze failed ($($_.Exception.Message)); mounting $Base again as it was"
            $Copy = Join-Path (Join-Path (Split-Path -Parent $Base) "bench_copy") (Split-Path -Leaf $Base)
            Dismount-VHD -Path $Copy -ErrorAction SilentlyContinue
            Remove-Item -Path $Copy -Force -ErrorAction SilentlyContinue
            Remove-Item -Path (Get-MasterState $DriveLetter) -Force -ErrorAction SilentlyContinue
            Set-Content -Path (Join-Path $env:TEMP "disk_scanner_bench_${DriveLetter}.vhdpath") -Value $Base -Encoding ASCII
            Mount-VHD -Path $Base | Out-Null
            Wait-BenchVolume $DriveLetter ""
            exit 1
        }
        Write-Host "[windows_vhd] ${DriveLetter}: frozen: $Base is kept as it is, each purge-cache mounts a fresh copy of it"
        exit 0
    }

    "purge-cache" {
        $DriveLetter = Get-DriveLetterFromPath $Arg1
        $VhdPath = Get-VhdPath $DriveLetter
        $MasterState = Get-MasterState $DriveLetter
        $Master = if (Test-Path $MasterState) { (Get-Content $MasterState -Raw).Trim() } else { "" }
        if ($Master) {
            Write-Host "[windows_vhd] Evicting the cache via Dismount-VHD + a fresh, unbuffered copy of the frozen volume on ${DriveLetter}:..."
        } else {
            Write-Host "[windows_vhd] Evicting Windows NTFS cache via Dismount-VHD + Host VHDX Unbuffered Cache Purge + Mount-VHD on ${DriveLetter}:..."
        }
        if (-not (Test-Path $VhdPath)) {
            Write-Warning "[windows_vhd] VHDX not found at $VhdPath; skipping VHD remount."
            exit 0
        }

        # (the copy is thrown away: what it holds need not be written first)
        if (-not $Master -and (Get-Command Write-VolumeCache -ErrorAction SilentlyContinue)) {
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

        if ($Master) {
            Mount-FreshCopy $DriveLetter $Master  # (its pages leave the host's RAM there)
            Write-Host "[windows_vhd] Cold cache state restored for ${DriveLetter}:\ (fresh copy)"
            exit 0
        }
        # While the VHDX is dismounted and has no open cached handles, its pages leave the host's RAM
        Purge-HostCache $VhdPath

        if ($HasHyperVCmdlets) {
            Mount-VHD -Path $VhdPath | Out-Null
        } else {
            $dp = @"
select vdisk file="$VhdPath"
attach vdisk
"@
            Invoke-DiskpartScript $dp
        }
        $FsState = Join-Path $env:TEMP "disk_scanner_bench_${DriveLetter}.fs"
        $Fs = if (Test-Path $FsState) { (Get-Content $FsState -Raw).Trim() } else { "" }
        Wait-BenchVolume $DriveLetter $(if ($Fs -eq "btrfs") { "Btrfs" } else { "" })
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
        $MasterState = Get-MasterState $DriveLetter
        if (Test-Path $MasterState) {
            # frozen: $VhdPath was the copy, the volume itself is kept here
            $Master = (Get-Content $MasterState -Raw).Trim()
            Remove-Item -Path $Master -Force -ErrorAction SilentlyContinue
            Remove-Item -Path $MasterState -Force -ErrorAction SilentlyContinue
        }
        Write-Host "[windows_vhd] Teardown complete."
    }
}
