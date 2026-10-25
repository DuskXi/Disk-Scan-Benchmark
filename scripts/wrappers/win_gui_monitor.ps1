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

    # Keep the caller's (admin) token so the scanner may read the raw NTFS $MFT (MFT benchmark mode)
    [switch]$Elevated,

    [int]$TimeoutSec = 90,

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
    public const uint SAFER_SCOPEID_USER = 2;
    public const uint SAFER_LEVELID_NORMALUSER = 0x20000;
    public const uint SAFER_LEVEL_OPEN = 1;

    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    public struct STARTUPINFOW {
        public int cb;
        public string lpReserved;
        public string lpDesktop;
        public string lpTitle;
        public int dwX;
        public int dwY;
        public int dwXSize;
        public int dwYSize;
        public int dwXCountChars;
        public int dwYCountChars;
        public int dwFillAttribute;
        public int dwFlags;
        public short wShowWindow;
        public short cbReserved2;
        public IntPtr lpReserved2;
        public IntPtr hStdInput;
        public IntPtr hStdOutput;
        public IntPtr hStdError;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct PROCESS_INFORMATION {
        public IntPtr hProcess;
        public IntPtr hThread;
        public int dwProcessId;
        public int dwThreadId;
    }

    [DllImport("user32.dll")]
    public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);

    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern bool GetProcessIoCounters(IntPtr hProcess, out IO_COUNTERS lpIoCounters);

    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern bool CloseHandle(IntPtr hObject);

    [DllImport("advapi32.dll", SetLastError = true)]
    public static extern bool SaferCreateLevel(
        uint dwScopeId,
        uint dwLevelId,
        uint OpenFlags,
        out IntPtr pLevelHandle,
        IntPtr lpReserved);

    [DllImport("advapi32.dll", SetLastError = true)]
    public static extern bool SaferComputeTokenFromLevel(
        IntPtr LevelHandle,
        IntPtr InAccessToken,
        out IntPtr OutAccessToken,
        uint dwFlags,
        IntPtr lpReserved);

    [DllImport("advapi32.dll", SetLastError = true)]
    public static extern bool SaferCloseLevel(IntPtr hLevelHandle);

    [DllImport("advapi32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
    public static extern bool CreateProcessAsUserW(
        IntPtr hToken,
        string lpApplicationName,
        string lpCommandLine,
        IntPtr lpProcessAttributes,
        IntPtr lpThreadAttributes,
        bool bInheritHandles,
        uint dwCreationFlags,
        IntPtr lpEnvironment,
        string lpCurrentDirectory,
        ref STARTUPINFOW lpStartupInfo,
        out PROCESS_INFORMATION lpProcessInformation);

    public static int StartNonAdmin(string exePath, string scanArgs) {
        IntPtr hLevel = IntPtr.Zero;
        IntPtr hToken = IntPtr.Zero;
        try {
            if (!SaferCreateLevel(SAFER_SCOPEID_USER, SAFER_LEVELID_NORMALUSER, SAFER_LEVEL_OPEN, out hLevel, IntPtr.Zero)) {
                return -1;
            }
            if (!SaferComputeTokenFromLevel(hLevel, IntPtr.Zero, out hToken, 0, IntPtr.Zero)) {
                return -2;
            }
            STARTUPINFOW si = new STARTUPINFOW();
            si.cb = Marshal.SizeOf(typeof(STARTUPINFOW));
            PROCESS_INFORMATION pi;
            string cmdLine = "\"" + exePath + "\" " + scanArgs;
            if (!CreateProcessAsUserW(hToken, null, cmdLine, IntPtr.Zero, IntPtr.Zero, false, 0, IntPtr.Zero, null, ref si, out pi)) {
                return -3;
            }
            CloseHandle(pi.hProcess);
            CloseHandle(pi.hThread);
            return pi.dwProcessId;
        } finally {
            if (hToken != IntPtr.Zero) CloseHandle(hToken);
            if (hLevel != IntPtr.Zero) SaferCloseLevel(hLevel);
        }
    }
}
"@

if (-not ("Win32Monitor" -as [type])) {
    Add-Type -TypeDefinition $Win32Code -Language CSharp
}

$LogicalCpus = [Environment]::ProcessorCount
$PollIntervalMs = 100
$SettleWindowMs = 1500
$StartupGraceMs = 1200

$Stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
# Launch with a normal-user (non-admin) token via Win32 Safer API so scanners (e.g. TreeSizeFree, WinDirStat)
# cannot access raw NTFS $MFT (\\.\X:) even when the runner executes as Administrator.
$StartedPid = if ($Elevated) { -100 } else { [Win32Monitor]::StartNonAdmin($ExePath, $ScanArgs) }
if ($StartedPid -gt 0) {
    $Proc = [System.Diagnostics.Process]::GetProcessById($StartedPid)
} else {
    $Proc = Start-Process -FilePath $ExePath -ArgumentList $ScanArgs -PassThru
}

$Minimized = $false
$PrevReadOps = [uint64]0
$PrevReadBytes = [uint64]0
$PrevOtherOps = [uint64]0
$PrevOtherBytes = [uint64]0
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

        # Query I/O Counters via Win32 GetProcessIoCounters.
        # Note: Standard Win32 directory traversal (FindFirstFileExW / NtQueryDirectoryFile) increments
        # OtherOperationCount and OtherTransferCount in the Windows NT kernel, whereas raw file/MFT reads
        # increment ReadOperationCount and ReadTransferCount. Both must be monitored!
        $Io = New-Object IO_COUNTERS
        $IoOk = [Win32Monitor]::GetProcessIoCounters($Proc.Handle, [ref]$Io)
        $DeltaReadOps = if ($IoOk) { $Io.ReadOperationCount - $PrevReadOps } else { [uint64]0 }
        $DeltaReadBytes = if ($IoOk) { $Io.ReadTransferCount - $PrevReadBytes } else { [uint64]0 }
        $DeltaOtherOps = if ($IoOk) { $Io.OtherOperationCount - $PrevOtherOps } else { [uint64]0 }
        $DeltaOtherBytes = if ($IoOk) { $Io.OtherTransferCount - $PrevOtherBytes } else { [uint64]0 }
        if ($IoOk) {
            $PrevReadOps = $Io.ReadOperationCount
            $PrevReadBytes = $Io.ReadTransferCount
            $PrevOtherOps = $Io.OtherOperationCount
            $PrevOtherBytes = $Io.OtherTransferCount
        }

        # Calculate CPU usage percentage across all logical cores over this 100ms window
        $CurCpuMs = $Proc.TotalProcessorTime.TotalMilliseconds
        $DeltaWallMs = [Math]::Max(1.0, $NowWallMs - $PrevWallMs)
        $DeltaCpuMs = [Math]::Max(0.0, $CurCpuMs - $PrevCpuMs)
        $CpuPercent = ($DeltaCpuMs / ($DeltaWallMs * $LogicalCpus)) * 100.0

        $PrevCpuMs = $CurCpuMs
        $PrevWallMs = $NowWallMs

        # Wait until initial GUI initialization finishes (either >= StartupGraceMs or directory traversal has begun)
        if (($NowWallMs -ge $StartupGraceMs) -and (($Io.OtherOperationCount -gt 2000) -or ($NowWallMs -ge 2200))) {
            $IsIoIdle = ($DeltaReadBytes -eq 0) -and ($DeltaOtherBytes -eq 0) -and ($DeltaReadOps -le 5) -and ($DeltaOtherOps -le 10)
            if ($IsIoIdle -and ($CpuPercent -lt 2.5)) {
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
    launched_non_admin = [bool]($StartedPid -gt 0)
    # Cumulative directory-enumeration (Other) / file-content (Read) I/O ops issued by the scanner process.
    # Used by run_cli_scanners.py as a sanity check: a real traversal of N directories must issue >= N
    # NtQueryDirectoryFile calls, so near-zero OtherOps means the GUI never actually scanned (e.g. blocked by a dialog).
    other_ops_total = [uint64]$PrevOtherOps
    read_ops_total = [uint64]$PrevReadOps
    with_gui_render = [bool]$WithGuiRender
    elapsed_ms = [Math]::Round($DeductedMs, 2)
    raw_elapsed_ms = [Math]::Round($TotalRawMs, 2)
    settle_deducted_ms = if ($QuietDurationMs -ge $SettleWindowMs) { $SettleWindowMs } else { 0 }
    peak_rss_mb = $PeakRssMb
    # CPU time (user + kernel) the GUI process used up to its last sample, for the balanced resource index
    cpu_ms = [Math]::Round($PrevCpuMs, 1)
    completed = $CompletedCleanly
}

$JsonText = $ResultObj | ConvertTo-Json -Compress
if ($JsonOut -ne "") {
    Set-Content -Path $JsonOut -Value $JsonText -Encoding UTF8
}
Write-Output $JsonText
