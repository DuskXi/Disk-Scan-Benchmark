<#
.SYNOPSIS
    Samples free space of the runner drives and the size of the benchmark VHDX every few seconds into a CSV.
.DESCRIPTION
    Used to find out why the virtual disk sometimes vanishes in the middle of a run (os error 433): the CSV shows
    whether C:/D: ran out of space while the dynamic VHDX was growing, and how fast it grew.
    Usage: disk_monitor.ps1 -Out results\disk_monitor.csv [-IntervalSec 15]
#>
param(
    [Parameter(Mandatory = $true)][string]$Out,
    [int]$IntervalSec = 15
)

$ErrorActionPreference = "SilentlyContinue"
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Out) | Out-Null
"time,c_free_gb,d_free_gb,x_free_gb,vhdx_gb" | Set-Content -Path $Out -Encoding ASCII

function Free-Gb([string]$Letter) {
    $d = Get-PSDrive -Name $Letter -PSProvider FileSystem
    if ($d) { return [math]::Round($d.Free / 1GB, 2) }
    return ""
}

while ($true) {
    $vhd = Get-ChildItem -Path $env:TEMP, $env:RUNNER_TEMP -Filter "disk_scanner_bench_*.vhdx" -ErrorAction SilentlyContinue |
        Sort-Object Length -Descending | Select-Object -First 1
    $vhdGb = if ($vhd) { [math]::Round($vhd.Length / 1GB, 2) } else { "" }
    ("{0},{1},{2},{3},{4}" -f (Get-Date -Format "HH:mm:ss"), (Free-Gb "C"), (Free-Gb "D"), (Free-Gb "X"), $vhdGb) |
        Add-Content -Path $Out -Encoding ASCII
    Start-Sleep -Seconds $IntervalSec
}
