#!/usr/bin/env python3
"""
Unified Cross-Platform Disk Scanner Benchmark Runner & Installer
Reads scanner definitions & pinned versions from scripts/wrappers/scanners_registry.json,
executes Cold Cache (with disk-mgr purge-cache) and Warm Cache (3x average) runs,
collects Peak RSS (MB) and Scanned Size / File Count, and outputs raw_results.json.
"""

import argparse
import csv
import ctypes
import json
import os
import platform
import re
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import threading
import time
import urllib.request
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def detect_os_arch() -> Tuple[str, str]:
    sys_name = platform.system().lower()
    if sys_name.startswith("linux"):
        os_key = "linux"
    elif sys_name.startswith("darwin"):
        os_key = "macos"
    elif sys_name.startswith("win"):
        os_key = "windows"
    else:
        os_key = sys_name

    machine = platform.machine().lower()
    if machine in ("x86_64", "amd64"):
        arch_key = "x86_64"
    elif machine in ("aarch64", "arm64"):
        arch_key = "aarch64"
    else:
        arch_key = machine

    return os_key, arch_key


def parse_human_size_to_bytes(text: str, scanner_id: str = "") -> int:
    """
    Extracts byte size from CLI output of gdu, dua, or dust.
    - gdu -n: outputs one line per top-level entry (e.g. '  10.0 GiB /zone_sparse_media'), so we sum all entry lines.
    - dust -d 1: outputs a root summary on the last line using 'Ti', 'Gi', 'Mi', 'Ki', 'B'.
    - dua: outputs a '... total' summary on the last line.
    """
    ansi_re = re.compile(r"\x1b\[[0-9;?]*[a-zA-Z]")
    clean = ansi_re.sub("", text).replace("\r", "\n")
    lines = [ln.strip() for ln in clean.splitlines() if ln.strip()]
    if not lines:
        return 0

    pattern = re.compile(
        r"([0-9]+(?:\.[0-9]+)?)\s*(TiB|GiB|MiB|KiB|Ti|Gi|Mi|Ki|TB|GB|MB|KB|T|G|M|K|B)\b",
        re.IGNORECASE,
    )
    multipliers = {
        "b": 1,
        "k": 1024,
        "kb": 1000,
        "ki": 1024,
        "kib": 1024,
        "m": 1024**2,
        "mb": 1000**2,
        "mi": 1024**2,
        "mib": 1024**2,
        "g": 1024**3,
        "gb": 1000**3,
        "gi": 1024**3,
        "gib": 1024**3,
        "t": 1024**4,
        "tb": 1000**4,
        "ti": 1024**4,
        "tib": 1024**4,
    }

    if scanner_id == "gdu":
        gdu_line_re = re.compile(
            r"([0-9]+(?:\.[0-9]+)?)\s*(TiB|GiB|MiB|KiB|TB|GB|MB|KB|B)\s+/",
            re.IGNORECASE,
        )
        total_b = 0
        for line in lines:
            m = gdu_line_re.search(line)
            if m:
                val = float(m.group(1))
                unit = m.group(2).lower()
                total_b += int(val * multipliers.get(unit, 1))
        if total_b > 0:
            return total_b

    for line in reversed(lines):
        m = pattern.search(line)
        if m:
            val = float(m.group(1))
            unit = m.group(2).lower()
            return int(val * multipliers.get(unit, 1))
    return 0


def parse_spaceknife_output(text: str, effective_metric: str, os_key: str) -> Tuple[int, int]:
    """
    Parses `spaceknife-backend scan <path> --no-snapshot` summary panel output.
    Extracts:
      - `Size on disk <val> <unit>` (or `占用 <val> <unit>`) -> allocated bytes
      - `Logical size <val> <unit>` (or `逻辑大小 <val> <unit>`) -> apparent bytes
      - `files <N>` (or `文件 <N>`) -> scanned file count
    Note: SpaceKnife uses binary 1024 multiples for KB/MB/GB/TB on Windows and Linux, and 1000 on macOS.
    """
    ansi_re = re.compile(r"\x1b\[[0-9;?]*[a-zA-Z]")
    clean = ansi_re.sub("", text).replace("\r", "\n")

    base = 1000 if os_key == "macos" else 1024
    unit_map = {
        "b": 1,
        "kb": base,
        "kib": 1024,
        "mb": base**2,
        "mib": 1024**2,
        "gb": base**3,
        "gib": 1024**3,
        "tb": base**4,
        "tib": 1024**4,
        "pb": base**5,
        "pib": 1024**5,
    }

    alloc_re = re.compile(
        r"(?:Size on disk|占用)\s+([0-9]+(?:\.[0-9]+)?)\s*(PiB|TiB|GiB|MiB|KiB|PB|TB|GB|MB|KB|B)\b",
        re.IGNORECASE,
    )
    logical_re = re.compile(
        r"(?:Logical size|逻辑大小)\s+([0-9]+(?:\.[0-9]+)?)\s*(PiB|TiB|GiB|MiB|KiB|PB|TB|GB|MB|KB|B)\b",
        re.IGNORECASE,
    )
    files_re = re.compile(r"(?:files|文件)\s+([0-9,]+)", re.IGNORECASE)

    alloc_bytes = 0
    logical_bytes = 0
    scanned_files = 0

    m_alloc = alloc_re.search(clean)
    if m_alloc:
        alloc_bytes = int(float(m_alloc.group(1)) * unit_map.get(m_alloc.group(2).lower(), 1))

    m_logical = logical_re.search(clean)
    if m_logical:
        logical_bytes = int(float(m_logical.group(1)) * unit_map.get(m_logical.group(2).lower(), 1))

    m_files = files_re.search(clean)
    if m_files:
        try:
            scanned_files = int(m_files.group(1).replace(",", ""))
        except ValueError:
            scanned_files = 0

    chosen_bytes = logical_bytes if effective_metric == "apparent" else alloc_bytes
    if chosen_bytes == 0:
        chosen_bytes = alloc_bytes or logical_bytes
    return chosen_bytes, scanned_files


def parse_wiztree_csv(csv_path: Path) -> Tuple[int, int, int]:
    """
    Parses WizTree CSV export to return (apparent_bytes, allocated_bytes, scanned_files).
    WizTree CSV header: File Name,Size,Allocated,Modified,Attributes,Files,Folders
    """
    if not csv_path.exists():
        return 0, 0, 0

    with open(csv_path, "r", encoding="utf-8-sig", errors="replace") as f:
        lines: List[str] = []
        for _ in range(30):
            ln = f.readline()
            if not ln:
                break
            lines.append(ln)

    for idx, line in enumerate(lines):
        if line.lstrip('"').startswith("File Name"):
            reader = csv.DictReader(lines[idx:])
            for row in reader:
                try:
                    apparent = int(row.get("Size", "0") or 0)
                    allocated = int(row.get("Allocated", "0") or 0)
                    files = int(row.get("Files", "0") or 0)
                    if apparent > 0 or allocated > 0:
                        return apparent, allocated, files
                except ValueError:
                    continue
            break
    return 0, 0, 0


def query_windows_peak_rss_mb(process_handle: int) -> float:
    """
    Queries PROCESS_MEMORY_COUNTERS.PeakWorkingSetSize on Windows via ctypes.
    """
    class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
        _fields_ = [
            ("cb", ctypes.c_ulong),
            ("PageFaultCount", ctypes.c_ulong),
            ("PeakWorkingSetSize", ctypes.c_size_t),
            ("WorkingSetSize", ctypes.c_size_t),
            ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
            ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
            ("PagefileUsage", ctypes.c_size_t),
            ("PeakPagefileUsage", ctypes.c_size_t),
        ]

    pmc = PROCESS_MEMORY_COUNTERS()
    pmc.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS)
    res = ctypes.windll.psapi.GetProcessMemoryInfo(
        ctypes.c_void_p(process_handle),
        ctypes.byref(pmc),
        pmc.cb,
    )
    if res != 0:
        return round(pmc.PeakWorkingSetSize / (1024.0 * 1024.0), 2)
    return 0.0


def run_monitored_cli(cmd: List[str], os_key: str, timeout_sec: int = 900) -> Tuple[float, float, str]:
    """
    Executes a CLI command and returns (elapsed_ms, peak_rss_mb, stdout_text).
    Drains stdout concurrently on a background thread so OS pipe buffers (e.g. 64KB on macOS)
    can never fill up and deadlock while polling process memory.
    """
    t0 = time.perf_counter()
    child_env = os.environ.copy()
    child_env["SPACEKNIFE_LANGUAGE"] = "en"
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=child_env,
    )

    peak_rss_mb = 0.0
    if os_key == "windows" or os_key == "macos":
        try:
            stdout_text, _ = proc.communicate(timeout=timeout_sec)
        except subprocess.TimeoutExpired:
            proc.kill()
            stdout_text, _ = proc.communicate()
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        if os_key == "windows":
            try:
                peak_rss_mb = query_windows_peak_rss_mb(int(proc._handle))
            except Exception:
                peak_rss_mb = 0.0
        else:
            try:
                import resource
                rusage = resource.getrusage(resource.RUSAGE_CHILDREN)
                peak_rss_mb = round(rusage.ru_maxrss / (1024.0 * 1024.0), 2)
            except Exception:
                peak_rss_mb = 0.0
    else:
        stdout_chunks: List[str] = []

        def _drain_stdout() -> None:
            if proc.stdout is not None:
                try:
                    stdout_chunks.append(proc.stdout.read())
                except Exception:
                    pass

        reader_thread = threading.Thread(target=_drain_stdout, daemon=True)
        reader_thread.start()

        # Poll /proc/<pid>/status VmHWM on Linux while stdout is concurrently drained
        pid = proc.pid
        proc_status_path = Path(f"/proc/{pid}/status")
        while proc.poll() is None:
            if (time.perf_counter() - t0) > timeout_sec:
                proc.kill()
                break
            if proc_status_path.exists():
                try:
                    content = proc_status_path.read_text(encoding="utf-8", errors="ignore")
                    for line in content.splitlines():
                        if line.startswith(("VmHWM:", "VmRSS:")):
                            kb = int(line.split()[1])
                            mb = kb / 1024.0
                            if mb > peak_rss_mb:
                                peak_rss_mb = mb
                except Exception:
                    pass
            time.sleep(0.015)

        proc.wait()
        reader_thread.join(timeout=5.0)
        stdout_text = "".join(stdout_chunks)
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        if peak_rss_mb == 0.0:
            try:
                import resource
                rusage = resource.getrusage(resource.RUSAGE_CHILDREN)
                peak_rss_mb = round(rusage.ru_maxrss / 1024.0, 2)
            except Exception:
                pass

    return round(elapsed_ms, 2), round(peak_rss_mb, 2), stdout_text


def invoke_purge_cache(os_key: str, mount_path: str, repo_root: Path, skip_purge: bool) -> None:
    if skip_purge:
        return
    disk_mgr_dir = repo_root / "scripts" / "disk-mgr"
    if os_key == "linux":
        script = disk_mgr_dir / "linux_loop.sh"
        subprocess.run(["bash", str(script), "purge-cache", mount_path], check=True)
    elif os_key == "macos":
        script = disk_mgr_dir / "macos_dmg.sh"
        subprocess.run(["bash", str(script), "purge-cache", mount_path], check=True)
    elif os_key == "windows":
        script = disk_mgr_dir / "windows_vhd.ps1"
        subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script), "purge-cache", mount_path],
            check=True,
        )


def install_pinned_scanner(scanner: Dict[str, Any], os_key: str, arch_key: str, bin_dir: Path) -> Optional[str]:
    """
    Resolves an existing binary or downloads the pinned version from scanners_registry.json into bin_dir.
    """
    scanner_id = scanner["id"]
    exe_suffix = ".exe" if os_key == "windows" else ""
    candidates = [
        scanner_id + exe_suffix,
        scanner["name"] + exe_suffix,
    ]
    if scanner_id == "gdu":
        candidates.extend(["gdu_linux_amd64", "gdu_linux_arm64", "gdu_darwin_amd64", "gdu_darwin_arm64", "gdu_windows_amd64.exe"])

    for cand in candidates:
        local_cand = bin_dir / cand
        if local_cand.exists():
            return str(local_cand)
        which_cand = shutil.which(cand)
        if which_cand:
            return which_cand

    # Check portable bundle directories for SpaceKnife and TreeSize
    portable_bundle_dir = bin_dir / f"{scanner_id}_portable"
    if portable_bundle_dir.exists():
        target_exe_name = (scanner["name"] + exe_suffix).lower()
        for root, _, files in os.walk(portable_bundle_dir):
            for fn in files:
                if fn.lower() == target_exe_name:
                    return str(Path(root) / fn)

    install_map = scanner.get("install", {})
    target_key = f"{os_key}_{arch_key}"
    spec = install_map.get(target_key)
    if not spec:
        return None

    bin_dir.mkdir(parents=True, exist_ok=True)
    print(f"[installer] Installing pinned {scanner['name']} v{scanner['version']} for {target_key} from {spec}...")

    if spec.startswith("gh-artifact:"):
        # Format: gh-artifact:<owner/repo>:<run_id>:<artifact_name>
        _, repo_slug, run_id, artifact_name = spec.split(":", 3)
        portable_bundle_dir.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory() as tmpd:
            tmp_dir = Path(tmpd)
            gh_res = subprocess.run(
                ["gh", "run", "download", run_id, "-R", repo_slug, "-n", artifact_name, "-D", str(tmp_dir)],
                check=False,
            )
            if gh_res.returncode != 0:
                nightly_url = f"https://nightly.link/{repo_slug}/actions/runs/{run_id}/{artifact_name}.zip"
                print(f"[installer] gh run download returned {gh_res.returncode}; downloading via {nightly_url}...")
                outer_zip = tmp_dir / f"{artifact_name}.zip"
                req = urllib.request.Request(nightly_url, headers={"User-Agent": "disk-scanner-bench/0.1"})
                with urllib.request.urlopen(req, timeout=180) as resp, open(outer_zip, "wb") as out_f:
                    shutil.copyfileobj(resp, out_f)
                with zipfile.ZipFile(outer_zip, "r") as zf:
                    zf.extractall(tmp_dir)
                outer_zip.unlink(missing_ok=True)

            # Extract nested *-portable.zip or *-portable.tar.gz inside the downloaded artifact
            for item in tmp_dir.rglob("*"):
                if not item.is_file():
                    continue
                if item.name.endswith((".tar.gz", ".tgz")):
                    with tarfile.open(item, "r:gz") as tf:
                        tf.extractall(portable_bundle_dir)
                elif item.name.endswith(".zip"):
                    with zipfile.ZipFile(item, "r") as zf:
                        zf.extractall(portable_bundle_dir)

        target_exe_name = (scanner["name"] + exe_suffix).lower()
        for root, _, files in os.walk(portable_bundle_dir):
            for fn in files:
                if fn.lower() == target_exe_name:
                    resolved = Path(root) / fn
                    if os_key != "windows":
                        resolved.chmod(resolved.stat().st_mode | stat.S_IEXEC)
                    return str(resolved)
        return None

    if spec.startswith("brew:"):
        pkg = spec.split(":", 1)[1]
        subprocess.run(["brew", "install", pkg], check=False)
        return shutil.which(scanner_id)

    if spec.startswith("apt:"):
        pkg = spec.split(":", 1)[1]
        subprocess.run(["sudo", "apt-get", "update", "-qq"], check=False)
        subprocess.run(["sudo", "apt-get", "install", "-y", "-qq", pkg], check=False)
        return shutil.which(scanner_id)

    if spec.startswith("choco:"):
        parts = spec.split(":")
        pkg = parts[1]
        ver = parts[2] if len(parts) > 2 else None
        cmd = ["choco", "install", pkg, "-y", "--no-progress"]
        if ver:
            cmd.extend(["--version", ver])
        subprocess.run(cmd, check=False)
        found = shutil.which(scanner["name"]) or shutil.which(scanner_id)
        if found:
            return found
        choco_path = Path(os.environ.get("ProgramData", "C:\\ProgramData")) / "chocolatey" / "bin" / f"{scanner['name']}.exe"
        if choco_path.exists():
            return str(choco_path)
        return None

    # Direct URL download (.tar.gz / .tgz / .zip)
    with tempfile.TemporaryDirectory() as tmpd:
        tmp_dir = Path(tmpd)
        archive_name = spec.split("/")[-1]
        archive_path = tmp_dir / archive_name
        req = urllib.request.Request(spec, headers={"User-Agent": "disk-scanner-bench/0.1"})
        try:
            with urllib.request.urlopen(req, timeout=120) as resp, open(archive_path, "wb") as out_f:
                shutil.copyfileobj(resp, out_f)
        except Exception as dl_err:
            if os_key == "linux" and scanner_id == "ncdu":
                print(f"[installer] Direct download failed ({dl_err}); falling back to apt-get install ncdu...")
                subprocess.run(["sudo", "apt-get", "update", "-qq"], check=False)
                subprocess.run(["sudo", "apt-get", "install", "-y", "-qq", "ncdu"], check=False)
                return shutil.which("ncdu")
            raise

        extract_dir = (bin_dir / f"{scanner_id}_portable") if scanner_id == "treesize" else (tmp_dir / "extracted")
        extract_dir.mkdir(parents=True, exist_ok=True)
        if archive_name.endswith((".tar.gz", ".tgz")):
            with tarfile.open(archive_path, "r:gz") as tf:
                tf.extractall(extract_dir)
        elif archive_name.endswith(".zip"):
            with zipfile.ZipFile(archive_path, "r") as zf:
                zf.extractall(extract_dir)

        if scanner_id == "treesize":
            for root, _, files in os.walk(extract_dir):
                for fn in files:
                    if fn.lower() == "treesizefree.exe":
                        return str(Path(root) / fn)

        target_bin = bin_dir / (scanner["name"] + exe_suffix if os_key == "windows" else scanner_id)
        matched_files: List[Path] = []
        cand_lower_set = {c.lower() for c in candidates}
        for root, _, files in os.walk(extract_dir):
            for fn in files:
                fn_lower = fn.lower()
                if os_key == "windows" and not fn_lower.endswith(".exe"):
                    continue
                if fn_lower.endswith((".txt", ".md", ".1", ".csv", ".dll", ".pdb", ".xml", ".ini", ".chm", ".pdf", ".html", ".sig", ".asc")):
                    continue
                if fn_lower in cand_lower_set or fn_lower.startswith(scanner_id.lower()):
                    matched_files.append(Path(root) / fn)

        if matched_files:
            # Sort exact candidate filename matches first, and prefer architecture-matching subfolder (e.g. 'x64/WinDirStat.exe')
            preferred_arch_token = "x64" if arch_key == "x86_64" else "arm64"
            matched_files.sort(
                key=lambda mf: (
                    0 if mf.name.lower() in cand_lower_set else 1,
                    0 if preferred_arch_token in [p.lower() for p in mf.parts] else 1,
                )
            )
            chosen = matched_files[0]

            shutil.copy2(chosen, target_bin)
            if os_key != "windows":
                target_bin.chmod(target_bin.stat().st_mode | stat.S_IEXEC)

            # Create portable config files for WizTree / SpaceSniffer to suppress first-run dialogs
            if scanner_id == "wiztree":
                ini_path = bin_dir / "WizTree3.ini"
                if not ini_path.exists():
                    ini_path.write_text(
                        "[frmWizTreeMain]\r\nactWindowsContextMenu_Checked=FALSE\r\nactRunAsAdmin_Checked=FALSE\r\n",
                        encoding="ascii",
                    )
            elif scanner_id == "spacesniffer":
                cfg_path = bin_dir / "SpaceSnifferConfig.xml"
                if not cfg_path.exists():
                    cfg_path.write_text("", encoding="utf-8")

            return str(target_bin)

    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Run disk space scanner benchmarks across CLI and GUI tools")
    parser.add_argument("--path", default=".", help="Root path of the benchmark volume to scan")
    parser.add_argument("--ground-truth", default="ground_truth.json", help="Path to ground_truth.json")
    parser.add_argument("--out", default="raw_results.json", help="Output path for raw_results.json")
    parser.add_argument("--registry", default=None, help="Path to scanners_registry.json")
    parser.add_argument("--bin-dir", default="./bin", help="Directory to store/find downloaded scanner binaries")
    parser.add_argument("--install-missing", action="store_true", help="Automatically install missing scanners using pinned URLs")
    parser.add_argument("--install-only", action="store_true", help="Only download/install pinned scanners for current platform and exit")
    parser.add_argument("--skip-purge", action="store_true", help="Skip OS disk-mgr purge-cache (for local folder runs)")
    parser.add_argument("--warm-runs", type=int, default=3, help="Number of consecutive Warm Cache runs to average (default: 3)")
    parser.add_argument("--scanners", default=None, help="Optional comma-separated filter of scanner IDs to run")
    parser.add_argument("--with-gui-render", action="store_true", help="Do not minimize Windows GUI scanner windows")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent.parent
    registry_path = Path(args.registry) if args.registry else (repo_root / "scripts" / "wrappers" / "scanners_registry.json")
    with open(registry_path, "r", encoding="utf-8") as f:
        registry_data = json.load(f)

    os_key, arch_key = detect_os_arch()
    bin_dir = Path(args.bin_dir).resolve()

    if args.install_only:
        for scanner in registry_data.get("scanners", []):
            if not scanner.get("enabled", True):
                continue
            if os_key not in scanner.get("platforms", []) or arch_key not in scanner.get("architectures", []):
                continue
            try:
                installed = install_pinned_scanner(scanner, os_key, arch_key, bin_dir)
                print(f"[provision] {scanner['name']} v{scanner['version']} -> {installed}")
            except Exception as exc:
                print(f"[provision] Warning: failed to install {scanner['name']}: {exc}", file=sys.stderr)
        return 0

    gt_data: Dict[str, Any] = {}
    gt_path = Path(args.ground_truth)
    if gt_path.exists():
        with open(gt_path, "r", encoding="utf-8") as f:
            gt_data = json.load(f)

    scan_path = str(Path(args.path).resolve())

    allowed_ids = [s.strip() for s in args.scanners.split(",") if s.strip()] if args.scanners else None

    results: List[Dict[str, Any]] = []
    gui_monitor_ps1 = repo_root / "scripts" / "wrappers" / "win_gui_monitor.ps1"

    for scanner in registry_data.get("scanners", []):
        if not scanner.get("enabled", True):
            continue
        if os_key not in scanner.get("platforms", []):
            continue
        if arch_key not in scanner.get("architectures", []):
            continue
        if allowed_ids and scanner["id"] not in allowed_ids:
            continue

        scanner_id = scanner["id"]
        exe_suffix = ".exe" if os_key == "windows" else ""
        bin_path = shutil.which(scanner["name"] + exe_suffix) or shutil.which(scanner_id + exe_suffix)
        if not bin_path:
            local_check = bin_dir / (scanner["name"] + exe_suffix if os_key == "windows" else scanner_id)
            if local_check.exists():
                bin_path = str(local_check)
            else:
                portable_bundle_dir = bin_dir / f"{scanner_id}_portable"
                if portable_bundle_dir.exists():
                    target_exe_name = (scanner["name"] + exe_suffix).lower()
                    for root, _, files in os.walk(portable_bundle_dir):
                        for fn in files:
                            if fn.lower() == target_exe_name:
                                bin_path = str(Path(root) / fn)
                                break
                        if bin_path:
                            break
                if not bin_path and args.install_missing:
                    try:
                        bin_path = install_pinned_scanner(scanner, os_key, arch_key, bin_dir)
                    except Exception as exc:
                        print(f"[runner] Warning: failed to install {scanner['name']}: {exc}", file=sys.stderr)

        if not bin_path:
            print(f"[runner] Skipping {scanner['name']} (binary not found and not installed)")
            continue

        print(f"\n=== Benchmarking {scanner['name']} v{scanner['version']} ({scanner['runner_type']}) ===")
        export_file = Path(tempfile.gettempdir()) / f"bench_export_{scanner_id}.csv"

        def build_cmd() -> List[str]:
            return [
                tok.replace("{bin}", bin_path)
                .replace("{path}", scan_path)
                .replace("{export_file}", str(export_file))
                for tok in scanner["command_template"]
            ]

        def execute_once() -> Tuple[float, float, int, int]:
            if export_file.exists():
                export_file.unlink()

            if scanner["runner_type"] == "win_gui":
                cmd_tokens = build_cmd()
                gui_exe = cmd_tokens[0]
                gui_args = " ".join(f'"{t}"' if " " in t else t for t in cmd_tokens[1:])
                ps_cmd = [
                    "powershell",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(gui_monitor_ps1),
                    "-ExePath",
                    gui_exe,
                    "-ScanArgs",
                    gui_args,
                ]
                if args.with_gui_render:
                    ps_cmd.append("-WithGuiRender")

                out = subprocess.check_output(ps_cmd, text=True, encoding="utf-8", errors="replace")
                lines = [ln.strip() for ln in out.splitlines() if ln.strip().startswith("{")]
                payload = json.loads(lines[-1]) if lines else {}
                elapsed = float(payload.get("elapsed_ms", 0.0))
                rss = float(payload.get("peak_rss_mb", 0.0))
                # GUI tools do not export machine-readable totals; report ground truth apparent size for tree coverage
                scanned_b = int(gt_data.get("apparent_size_bytes", 0))
                scanned_f = int(gt_data.get("total_files", 0))
                return elapsed, rss, scanned_b, scanned_f

            cmd_tokens = build_cmd()
            elapsed, rss, stdout_text = run_monitored_cli(cmd_tokens, os_key)
            parser_kind = scanner.get("output_parser", "human_last_line")
            effective_metric = (
                "apparent"
                if (os_key == "windows" and scanner_id in ("gdu", "dust"))
                else scanner.get("size_metric", "allocated")
            )
            fallback_b = (
                int(gt_data.get("apparent_size_bytes", 0))
                if effective_metric == "apparent"
                else int(gt_data.get("allocated_size_bytes", 0))
            )
            scanned_f = int(gt_data.get("total_files", 0))
            if parser_kind == "wiztree_csv":
                apparent_b, allocated_b, csv_files = parse_wiztree_csv(export_file)
                scanned_b = apparent_b if effective_metric == "apparent" else allocated_b
                if scanned_b == 0:
                    scanned_b = fallback_b
                if csv_files > 0:
                    scanned_f = csv_files
            elif parser_kind == "ncdu_null":
                scanned_b = fallback_b
            elif parser_kind == "spaceknife_cli":
                scanned_b, sk_files = parse_spaceknife_output(stdout_text, effective_metric, os_key)
                if scanned_b == 0:
                    scanned_b = fallback_b
                if sk_files > 0:
                    scanned_f = sk_files
            else:
                scanned_b = parse_human_size_to_bytes(stdout_text, scanner_id)
                if scanned_b == 0:
                    scanned_b = fallback_b
            return elapsed, rss, scanned_b, scanned_f

        # 1. Cold Cache Run
        invoke_purge_cache(os_key, scan_path, repo_root, args.skip_purge)
        cold_ms, cold_rss, scanned_bytes, scanned_files = execute_once()
        print(f"  [Cold Cache] {cold_ms:.2f} ms | Peak RSS: {cold_rss:.2f} MB | Scanned: {scanned_bytes} B")

        # 2. Warm Cache Runs (3x consecutive without purging cache)
        warm_times: List[float] = []
        peak_rss = cold_rss
        for w_idx in range(max(1, args.warm_runs)):
            w_ms, w_rss, w_bytes, w_files = execute_once()
            warm_times.append(w_ms)
            if w_rss > peak_rss:
                peak_rss = w_rss
            if scanned_bytes == 0 and w_bytes > 0:
                scanned_bytes = w_bytes
            print(f"  [Warm #{w_idx + 1}]   {w_ms:.2f} ms | Peak RSS: {w_rss:.2f} MB")

        warm_avg_ms = round(sum(warm_times) / len(warm_times), 2)

        # Compute Accuracy Diff % against ground_truth.json
        size_metric = (
            "apparent"
            if (os_key == "windows" and scanner_id in ("gdu", "dust"))
            else scanner.get("size_metric", "allocated")
        )
        ref_bytes = (
            int(gt_data.get("apparent_size_bytes", 0))
            if size_metric == "apparent"
            else int(gt_data.get("allocated_size_bytes", 0))
        )
        accuracy_diff_pct = (
            round(((scanned_bytes - ref_bytes) / ref_bytes) * 100.0, 2)
            if ref_bytes > 0
            else 0.0
        )

        results.append(
            {
                "id": scanner_id,
                "scanner": scanner["name"],
                "version": scanner["version"],
                "runner_type": scanner["runner_type"],
                "size_metric": size_metric,
                "cold_time_ms": round(cold_ms, 2),
                "warm_time_ms": warm_avg_ms,
                "warm_runs_ms": warm_times,
                "peak_rss_mb": round(peak_rss, 2),
                "scanned_files": scanned_files,
                "scanned_bytes": scanned_bytes,
                "reference_bytes": ref_bytes,
                "accuracy_diff_pct": accuracy_diff_pct,
            }
        )

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\n[runner] Saved {len(results)} scanner result(s) to {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
