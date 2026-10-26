#!/usr/bin/env python3
"""
Cold scans of a few scanners with per-second I/O and CPU sampling (diagnostic, Windows CI).

Why WinDirStat wins cold scans on the slower CI disks (Win ARM64, ReFS) but ties on the fast one and loses on a local
NVMe drive: the suspicion is that it keeps more reads in flight. For each configuration this script

  1. applies the scanner's benchmark settings (WinDirStat: also ScanningThreads),
  2. prewarms the executable and drops the volume's caches exactly like the benchmark,
  3. starts typeperf on the benchmark volume (queue depth, reads/s, read latency, bytes per read, total CPU),
  4. runs the scanner's benchmark command once (a cold scan) while psutil samples its process tree,

and prints one Markdown table. Every configuration runs once in order and once in reverse order.

  python scanner_io_profile.py --path X:/bench --bin-dir ./bin --md-out io.md --json-out io.json
"""

import argparse
import csv
import datetime as dt
import json
import os
import statistics
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts" / "wrappers"))
import run_cli_scanners as rcs  # noqa: E402

try:
    import psutil  # type: ignore[import-untyped]
except ImportError:  # the disk counters still work without it
    psutil = None

# (label, scanner id, WinDirStat ScanningThreads: None = untouched, 0 = value removed as in the benchmark, else N)
CONFIGS: List[Tuple[str, str, Optional[int]]] = [
    ("gdu", "gdu", None),
    ("dua-cli", "dua", None),
    ("SpaceKnife", "spaceknife", None),
    ("WinDirStat default", "windirstat", 0),
    ("WinDirStat 1 thread", "windirstat", 1),
    ("WinDirStat 4 threads", "windirstat", 4),
    ("WinDirStat 8 threads", "windirstat", 8),
]
COUNTERS = [
    "\\LogicalDisk({vol})\\Current Disk Queue Length",
    "\\LogicalDisk({vol})\\Disk Reads/sec",
    "\\LogicalDisk({vol})\\Avg. Disk sec/Read",
    "\\LogicalDisk({vol})\\Avg. Disk Bytes/Read",
    "\\Processor(_Total)\\% Processor Time",
]


def set_windirstat_threads(threads: int) -> None:
    if threads == 0:  # the benchmark leaves the setting alone: WinDirStat's own default
        subprocess.run(
            ["reg", "delete", r"HKCU\Software\WinDirStat\WinDirStat\Options", "/v", "ScanningThreads", "/f"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        return
    subprocess.run(
        [
            "reg",
            "add",
            r"HKCU\Software\WinDirStat\WinDirStat\Options",
            "/v",
            "ScanningThreads",
            "/t",
            "REG_DWORD",
            "/d",
            str(threads),
            "/f",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )


def sample_process(pid: int, stop: threading.Event, out: Dict[str, float]) -> None:
    """Peak thread count and last CPU seconds of the scanner's process tree, every 0.5 s."""
    if psutil is None:
        return
    try:
        root = psutil.Process(pid)
    except Exception:
        return
    while not stop.is_set():
        try:
            procs = [root] + root.children(recursive=True)
            threads = sum(p.num_threads() for p in procs)
            cpu = sum(sum(p.cpu_times()[:2]) for p in procs)
            out["max_threads"] = max(out.get("max_threads", 0), threads)
            out["cpu_s"] = max(out.get("cpu_s", 0.0), cpu)
        except Exception:
            pass
        stop.wait(0.5)


def read_typeperf(path: Path, t0: dt.datetime, t1: dt.datetime) -> List[List[float]]:
    """Samples taken while the scanner ran: one list of counter values per second."""
    rows: List[List[float]] = []
    if not path.exists():
        return rows
    with open(path, encoding="utf-8", errors="replace", newline="") as f:
        for i, row in enumerate(csv.reader(f)):
            if i == 0 or len(row) < 1 + len(COUNTERS):
                continue
            try:
                ts = dt.datetime.strptime(row[0], "%m/%d/%Y %H:%M:%S.%f")
            except ValueError:
                continue
            if t0 <= ts <= t1 + dt.timedelta(seconds=1):
                try:
                    rows.append([float(v) if v.strip() else 0.0 for v in row[1 : 1 + len(COUNTERS)]])
                except ValueError:
                    continue
    return rows


def run_config(
    label: str, scanner: Dict[str, Any], threads: Optional[int], bin_path: str, scan_path: str, work: Path
) -> Dict[str, Any]:
    os_key = "windows"
    rcs.configure_windows_gui_scanner(scanner["id"], os_key, bin_path, False)
    if threads is not None:
        set_windirstat_threads(threads)
    rcs.prewarm_scanner_binary(scanner, bin_path, os_key)
    rcs.invoke_purge_cache(os_key, scan_path, REPO, False)

    vol = scan_path[:2].upper()
    perf_csv = work / f"perf_{label.replace(' ', '_')}_{int(time.time())}.csv"
    perf = subprocess.Popen(
        ["typeperf"] + [c.format(vol=vol) for c in COUNTERS] + ["-si", "1", "-o", str(perf_csv), "-f", "CSV", "-y"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(3)  # typeperf takes a moment before its first sample

    export_file = work / f"export_{scanner['id']}.csv"
    if export_file.exists():
        export_file.unlink()
    cmd = [
        tok.replace("{bin}", bin_path).replace("{path}", scan_path).replace("{export_file}", str(export_file))
        for tok in rcs.command_template_for(scanner, os_key)
    ]
    env = os.environ.copy()
    env["SPACEKNIFE_LANGUAGE"] = "en"
    env.update({k: str(v) for k, v in scanner.get("env", {}).items()})
    proc_stats: Dict[str, float] = {}
    stop = threading.Event()
    t0 = dt.datetime.now()
    start = time.perf_counter()
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
    sampler = threading.Thread(target=sample_process, args=(proc.pid, stop, proc_stats), daemon=True)
    sampler.start()
    output, _ = proc.communicate()
    wall = time.perf_counter() - start
    t1 = dt.datetime.now()
    stop.set()
    sampler.join(timeout=5)
    time.sleep(2)
    perf.terminate()
    try:
        perf.wait(timeout=10)
    except subprocess.TimeoutExpired:
        perf.kill()

    samples = read_typeperf(perf_csv, t0, t1)
    cols = list(zip(*samples)) if samples else [()] * len(COUNTERS)

    def mean(i: int) -> Optional[float]:
        return statistics.fmean(cols[i]) if cols[i] else None

    def peak(i: int) -> Optional[float]:
        return max(cols[i]) if cols[i] else None

    # read latency and size averaged over the seconds that actually read something
    reading = [s for s in samples if s[1] > 0]
    lat = statistics.fmean(s[2] for s in reading) * 1000 if reading else None
    size = statistics.fmean(s[3] for s in reading) / 1024 if reading else None
    return {
        "label": label,
        "wall_s": round(wall, 2),
        "exit": proc.returncode,
        "output_bytes": len(output or b"") + (export_file.stat().st_size if export_file.exists() else 0),
        "queue_mean": mean(0),
        "queue_peak": peak(0),
        "reads_per_s": mean(1),
        "read_ms": lat,
        "read_kib": size,
        "cpu_total_pct": mean(4),
        "proc_cpu_s": proc_stats.get("cpu_s"),
        "proc_max_threads": proc_stats.get("max_threads"),
        "samples": len(samples),
    }


def fmt(v: Optional[float], spec: str) -> str:
    return "-" if v is None else format(v, spec)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--path", required=True, help="Benchmark tree on its own volume, e.g. X:/bench")
    ap.add_argument("--bin-dir", default="bin")
    ap.add_argument("--rounds", type=int, default=2, help="Rounds over all configurations (odd rounds reversed)")
    ap.add_argument("--md-out", default="")
    ap.add_argument("--json-out", default="")
    args = ap.parse_args()

    os_key, arch_key = rcs.detect_os_arch()
    registry = json.loads((REPO / "scripts" / "wrappers" / "scanners_registry.json").read_text(encoding="utf-8"))
    by_id = {s["id"]: s for s in registry["scanners"]}
    work = Path(tempfile.mkdtemp(prefix="io_profile_"))
    print(f"[io-profile] {os_key}/{arch_key}, psutil {'on' if psutil else 'off'}, work dir {work}")

    results: List[Dict[str, Any]] = []
    for rnd in range(args.rounds):
        order = CONFIGS if rnd % 2 == 0 else list(reversed(CONFIGS))
        for label, sid, threads in order:
            scanner = by_id[sid]
            bin_path = rcs.resolve_installed_scanner(scanner, os_key, arch_key, Path(args.bin_dir))
            if not bin_path:
                print(f"[io-profile] {label}: not installed for {os_key}/{arch_key}, skipped")
                continue
            r = run_config(label, scanner, threads, bin_path, args.path, work)
            r["round"] = rnd + 1
            results.append(r)
            print(
                f"[io-profile] round {rnd + 1} {label}: {r['wall_s']} s, queue {fmt(r['queue_mean'], '.1f')} "
                f"(peak {fmt(r['queue_peak'], '.0f')}), {fmt(r['reads_per_s'], ',.0f')} reads/s, "
                f"{fmt(r['read_ms'], '.2f')} ms/read, threads {r['proc_max_threads']}, exit {r['exit']}",
                flush=True,
            )

    lines = [
        "| 配置 Config | 轮 Round | 冷扫 s | 队列均值 Queue | 队列峰值 Peak | 读/秒 Reads/s | 读延迟 ms | 每次读 KiB "
        "| 总 CPU % | 进程 CPU s | 最多线程 |",
        "| :--- | :---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for r in results:
        lines.append(
            f"| {r['label']} | {r['round']} | {r['wall_s']:.2f} | {fmt(r['queue_mean'], '.1f')} "
            f"| {fmt(r['queue_peak'], '.0f')} | {fmt(r['reads_per_s'], ',.0f')} | {fmt(r['read_ms'], '.2f')} "
            f"| {fmt(r['read_kib'], '.1f')} | {fmt(r['cpu_total_pct'], '.0f')} | {fmt(r['proc_cpu_s'], '.1f')} "
            f"| {r['proc_max_threads'] if r['proc_max_threads'] is not None else '-'} |"
        )
    md = "\n".join(lines) + "\n"
    print(md)
    if args.md_out:
        Path(args.md_out).write_text(md, encoding="utf-8")
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(results, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
