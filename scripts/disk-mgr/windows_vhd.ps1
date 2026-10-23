<#
.SYNOPSIS
    Windows NTFS Dynamic VHDX Manager & Cold-Cache Evictor for disk-scanner-bench
.DESCRIPTION
    Supports three subcommands:
      .\windows_vhd.ps1 create <size_gb> <mount_path>
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
    [string]$Arg2 = "X:\"
)

$ErrorActionPreference = "Stop"
$VhdPath = Join-Path $env:TEMP "disk_scanner_bench.vhdx"

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

$HasHyperVCmdlets = [bool](Get-Command New-VHD -ErrorAction SilentlyContinue)

switch ($Action) {
    "create" {
        $SizeGb = [int64]$Arg1
        $DriveLetter = Get-DriveLetterFromPath $Arg2
        Write-Host "[windows_vhd] Creating ${SizeGb}GB Dynamic NTFS VHDX at $VhdPath (Drive ${DriveLetter}:)..."

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
            Format-Volume -DriveLetter $DriveLetter -FileSystem NTFS -NewFileSystemLabel "BenchVol" -Confirm:$false | Out-Null
        } else {
            $sizeMb = $SizeGb * 1024
            $dp = @"
create vdisk file="$VhdPath" maximum=$sizeMb type=expandable
select vdisk file="$VhdPath"
attach vdisk
convert gpt
create partition primary
format fs=ntfs label="BenchVol" quick
assign letter=$DriveLetter
"@
            Invoke-DiskpartScript $dp
        }
        try {
            Add-MpPreference -ExclusionPath "${DriveLetter}:\" -ErrorAction SilentlyContinue
            Add-MpPreference -ExclusionPath $VhdPath -ErrorAction SilentlyContinue
            & fsutil 8dot3name set "${DriveLetter}:" 1 | Out-Null
            & fsutil behavior set disablelastaccess 1 | Out-Null
        } catch {}
        Write-Host "[windows_vhd] Mounted NTFS volume at ${DriveLetter}:\ (Defender excluded, 8.3 disabled)"
    }

    "purge-cache" {
        $DriveLetter = Get-DriveLetterFromPath $Arg1
        Write-Host "[windows_vhd] Evicting Windows NTFS cache via Dismount-VHD / Mount-VHD cycle on ${DriveLetter}:..."
        if (-not (Test-Path $VhdPath)) {
            Write-Warning "[windows_vhd] VHDX not found at $VhdPath; skipping VHD remount."
            exit 0
        }

        if (Get-Command Write-VolumeCache -ErrorAction SilentlyContinue) {
            Write-VolumeCache -DriveLetter $DriveLetter -ErrorAction SilentlyContinue
        }

        if ($HasHyperVCmdlets) {
            Dismount-VHD -Path $VhdPath
            Mount-VHD -Path $VhdPath | Out-Null
        } else {
            $dp = @"
select vdisk file="$VhdPath"
detach vdisk
attach vdisk
"@
            Invoke-DiskpartScript $dp
        }
        Start-Sleep -Milliseconds 500
        Write-Host "[windows_vhd] Cold cache state restored for ${DriveLetter}:\"
    }

    "teardown" {
        $DriveLetter = Get-DriveLetterFromPath $Arg1
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
