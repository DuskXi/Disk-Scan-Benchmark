<#
.SYNOPSIS
    Headless Timer & I/O + CPU Settle Monitor for Windows GUI Disk Scanners (SpaceSniffer / WinDirStat)
.DESCRIPTION
    Launches a GUI scanner process, optionally minimizes its main window via Win32 ShowWindow(hwnd, SW_MINIMIZE)
    to eliminate GDI/Treemap animation CPU overhead (unless --with-gui-render is specified), polls
    GetProcessIoCounters (ReadOperationCount / ReadTransferCount) and CPU usage every 100ms, and declares
    completion when disk read delta is 0 for 1500ms continuously and CPU < 1%.
#>
param(
    [Parameter(Mandatory=$true)]
    [string]$ExePath,

    [Parameter(Mandatory=$true)]
    [string]$ScanArgs,

    [switch]$WithGuiRender,

    [int]$TimeoutSec = 600,

    [string]$JsonOut = ""
)

$ErrorActionPreference = "Stop"

$Win32Code = @"
using System;
using System.Runtime.InteropServices;

public struct IO_COUNTERS {
    public ulong ReadOperationCount;
    public ulong WriteOperationCount;
    public ulong OtherOperationCount;
    public ulong ReadTransferCount;
    public ulong WriteTransferCount;
    public ulong OtherTransferCount;
}

public static class Win32Monitor {
    public const int SW_MINIMIZE = 6;

    [DllImport("user32.dll")]
    public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);

    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern bool GetProcessIoCounters(IntPtr hProcess, out IO_COUNTERS lpIoCounters);
}
"@

if (-not ("Win32Monitor" -as [type])) {
    Add-Type -TypeDefinition $Win32Code -Language CSharp
}

$LogicalCpus = [Environment]::ProcessorCount
$PollIntervalMs = 100
$SettleWindowMs = 1500
$StartupGraceMs = 600

$Stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
$Proc = Start-Process -FilePath $ExePath -ArgumentList $ScanArgs -PassThru

$Minimized = $false
$PrevReadOps = [uint64]0
$PrevReadBytes = [uint64]0
$PrevCpuMs = [double]0.0
$PrevWallMs = [double]0.0
$QuietDurationMs = 0
$PeakRssBytes = [int64]0
$CompletedCleanly = $false

try {
    while (-not $Proc.HasExited) {
        Start-Sleep -Milliseconds $PollIntervalMs
        $Proc.Refresh()
        if ($Proc.HasExited) {
            $CompletedCleanly = $true
            break
        }

        $NowWallMs = $Stopwatch.Elapsed.TotalMilliseconds

        # Minimize GUI window as soon as MainWindowHandle becomes available (unless --with-gui-render)
        if ((-not $WithGuiRender) -and (-not $Minimized) -and ($Proc.MainWindowHandle -ne [IntPtr]::Zero)) {
            [void][Win32Monitor]::ShowWindow($Proc.MainWindowHandle, [Win32Monitor]::SW_MINIMIZE)
            $Minimized = $true
        }

        if ($Proc.PeakWorkingSet64 -gt $PeakRssBytes) {
            $PeakRssBytes = $Proc.PeakWorkingSet64
        }

        # Query I/O Counters via Win32 GetProcessIoCounters
        $Io = New-Object IO_COUNTERS
        $IoOk = [Win32Monitor]::GetProcessIoCounters($Proc.Handle, [ref]$Io)
        $DeltaReadOps = if ($IoOk) { $Io.ReadOperationCount - $PrevReadOps } else { [uint64]0 }
        $DeltaReadBytes = if ($IoOk) { $Io.ReadTransferCount - $PrevReadBytes } else { [uint64]0 }
        if ($IoOk) {
            $PrevReadOps = $Io.ReadOperationCount
            $PrevReadBytes = $Io.ReadTransferCount
        }

        # Calculate CPU usage percentage across all logical cores over this 100ms window
        $CurCpuMs = $Proc.TotalProcessorTime.TotalMilliseconds
        $DeltaWallMs = [Math]::Max(1.0, $NowWallMs - $PrevWallMs)
        $DeltaCpuMs = [Math]::Max(0.0, $CurCpuMs - $PrevCpuMs)
        $CpuPercent = ($DeltaCpuMs / ($DeltaWallMs * $LogicalCpus)) * 100.0

        $PrevCpuMs = $CurCpuMs
        $PrevWallMs = $NowWallMs

        if ($NowWallMs -ge $StartupGraceMs) {
            if (($DeltaReadOps -eq 0) -and ($DeltaReadBytes -eq 0) -and ($CpuPercent -lt 1.0)) {
                $QuietDurationMs += $PollIntervalMs
            } else {
                $QuietDurationMs = 0
            }

            if ($QuietDurationMs -ge $SettleWindowMs) {
                $CompletedCleanly = $true
                break
            }
        }

        if ($NowWallMs -ge ($TimeoutSec * 1000)) {
            break
        }
    }
} finally {
    $TotalRawMs = $Stopwatch.Elapsed.TotalMilliseconds
    try {
        if (-not $Proc.HasExited) {
            $Proc.Refresh()
            if ($Proc.PeakWorkingSet64 -gt $PeakRssBytes) {
                $PeakRssBytes = $Proc.PeakWorkingSet64
            }
            Stop-Process -Id $Proc.Id -Force -ErrorAction SilentlyContinue
        }
    } catch {}
}

$DeductedMs = if ($QuietDurationMs -ge $SettleWindowMs) {
    [Math]::Max(1.0, $TotalRawMs - $SettleWindowMs)
} else {
    $TotalRawMs
}

$PeakRssMb = [Math]::Round(($PeakRssBytes / (1024.0 * 1024.0)), 2)

$ResultObj = [ordered]@{
    exe = $ExePath
    with_gui_render = [bool]$WithGuiRender
    elapsed_ms = [Math]::Round($DeductedMs, 2)
    raw_elapsed_ms = [Math]::Round($TotalRawMs, 2)
    settle_deducted_ms = if ($QuietDurationMs -ge $SettleWindowMs) { $SettleWindowMs } else { 0 }
    peak_rss_mb = $PeakRssMb
    completed = $CompletedCleanly
}

$JsonText = $ResultObj | ConvertTo-Json -Compress
if ($JsonOut -ne "") {
    Set-Content -Path $JsonOut -Value $JsonText -Encoding UTF8
}
Write-Output $JsonText
