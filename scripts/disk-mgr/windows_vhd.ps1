<#
.SYNOPSIS
    Windows NTFS/ReFS Dynamic VHDX Manager & Cold-Cache Evictor for disk-scanner-bench
.DESCRIPTION
    Supports three subcommands:
      .\windows_vhd.ps1 create <size_gb> <mount_path> [ntfs|refs]
      .\windows_vhd.ps1 purge-cache <mount_path>
      .\windows_vhd.ps1 teardown <mount_path>
#>
param(
    [Parameter(Mandatory=$true, Position=0)]
    [ValidateSet("create", "purge-cache", "teardown")]
    [string]$Action,

    [Parameter(Position=1)]
    [string]$Arg1 = "60",

    [Parameter(Position=2)]
    [string]$Arg2 = "X:\",

    [Parameter(Position=3)]
    [ValidateSet("ntfs", "refs")]
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
    # On GitHub-hosted runners RUNNER_TEMP lives on the fast D: scratch SSD (only ~14 GB free), whereas TEMP is on the
    # much slower but roomy system drive C:. A dynamic VHDX that outgrows D: makes the virtual disk vanish mid-run
    # (ERROR_NO_SUCH_DEVICE, os error 433), which killed the 3M-file preset, so big volumes go to C:.
    $Base = $env:TEMP
    if ($env:RUNNER_TEMP -and $VirtualGb -gt 0 -and $VirtualGb -le 700) {
        $Base = $env:RUNNER_TEMP
    } elseif ($env:RUNNER_TEMP -and $VirtualGb -le 0) {
        $Base = $env:RUNNER_TEMP
    }
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

$HasHyperVCmdlets = [bool](Get-Command New-VHD -ErrorAction SilentlyContinue)

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

        if ($HasHyperVCmdlets) {
            $sizeBytes = $SizeGb * 1GB
            $vhd = New-VHD -Path $VhdPath -SizeBytes $sizeBytes -Dynamic
            $disk = $vhd | Mount-VHD -Passthru | Get-Disk
            Initialize-Disk -Number $disk.Number -PartitionStyle GPT -ErrorAction SilentlyContinue
            $part = New-Partition -DiskNumber $disk.Number -UseMaximumSize -DriveLetter $DriveLetter
            Format-Volume -DriveLetter $DriveLetter -FileSystem $FsName -NewFileSystemLabel "BenchVol" -Confirm:$false | Out-Null
        } else {
            $sizeMb = $SizeGb * 1024
            $dp = @"
create vdisk file="$VhdPath" maximum=$sizeMb type=expandable
select vdisk file="$VhdPath"
attach vdisk
convert gpt
create partition primary
format fs=$FsType label="BenchVol" quick
assign letter=$DriveLetter
"@
            Invoke-DiskpartScript $dp
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
        Start-Sleep -Milliseconds 1000
        Write-Host "[windows_vhd] Cold cache state restored for ${DriveLetter}:\"
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
