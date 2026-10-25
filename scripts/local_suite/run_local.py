#!/usr/bin/env python3
"""
Local real-drive benchmark suite.

Runs the pinned scanners of this repository against folders or whole drives on your own machine, then writes an
anonymized submission you can review and, if you want, send to the project as a GitHub issue:

  python scripts/local_suite/run_local.py --target D:\\ --target E:\\            # Windows (run elevated for cold scans)
  sudo python3 scripts/local_suite/run_local.py --target /home --target /data  # Linux / macOS
  python scripts/local_suite/run_local.py --target D:\\ --submit                 # review, then open the issue

Cold scans need the OS file cache purged before every scan, which needs admin / root. Without it the suite still
runs, but marks the volume cold_purged=false and its "cold" times are really warm times.

The submission holds only numbers, scanner ids, the OS / filesystem / bus type, and the CPU and disk model names.
No path, drive letter, volume label, host name, user name or serial number is ever read into it; see
docs/LOCAL_SUITE.md.
"""

import argparse
import ctypes
import datetime as dt
import json
import os
import platform
import plistlib
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
sys.path.insert(0, str(REPO / "scripts" / "wrappers"))
sys.path.insert(0, str(HERE))

from run_cli_scanners import detect_os_arch  # noqa: E402
from submission_schema import FS_VALUES, SCHEMA, TEXT_RE, validate  # noqa: E402

RUNNER = REPO / "scripts" / "wrappers" / "run_cli_scanners.py"
REGISTRY = REPO / "scripts" / "wrappers" / "scanners_registry.json"
MARKER = "<!-- dsb-local-submission -->"


def clean_text(value: str, fallback: str = "unknown") -> str:
    """Keeps only characters a submission may contain, so a model name can never smuggle a path or address."""
    text = re.sub(r"\s+", " ", re.sub(r"[^A-Za-z0-9 ()._+,#-]", " ", value or "")).strip()[:64]
    return text if text and TEXT_RE.match(text) else fallback


def round_gb(n_bytes: float) -> float:
    gb = n_bytes / 1e9
    return round(gb) if gb < 100 else round(gb, -1)


def suite_version() -> str:
    try:
        out = subprocess.run(
            ["git", "-C", str(REPO), "describe", "--always", "--dirty"], capture_output=True, text=True, check=False
        ).stdout.strip()
        return clean_text(out, "unknown")
    except OSError:
        return "unknown"


# --- machine information (no names: only CPU model, core count, memory size, OS version) ---


def cpu_model(os_key: str) -> str:
    try:
        if os_key == "windows":
            import winreg

            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0") as k:
                return clean_text(str(winreg.QueryValueEx(k, "ProcessorNameString")[0]))
        if os_key == "linux":
            for line in Path("/proc/cpuinfo").read_text().splitlines():
                if line.lower().startswith(("model name", "hardware", "cpu model")):
                    return clean_text(line.split(":", 1)[1])
        if os_key == "macos":
            out = subprocess.run(["sysctl", "-n", "machdep.cpu.brand_string"], capture_output=True, text=True).stdout
            return clean_text(out)
    except (OSError, IndexError):
        pass
    return clean_text(platform.processor())


def ram_gb(os_key: str) -> int:
    try:
        if os_key == "windows":

            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]

            st = MEMORYSTATUSEX()
            st.dwLength = ctypes.sizeof(st)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(st))  # type: ignore[attr-defined]
            return max(1, round(st.ullTotalPhys / 2**30))
        if os_key == "linux":
            kb = int(re.search(r"MemTotal:\s+(\d+)", Path("/proc/meminfo").read_text()).group(1))  # type: ignore
            return max(1, round(kb / 2**20))
        if os_key == "macos":
            out = subprocess.run(["sysctl", "-n", "hw.memsize"], capture_output=True, text=True).stdout
            return max(1, round(int(out) / 2**30))
    except (OSError, ValueError, AttributeError):
        pass
    return 1


def os_version(os_key: str) -> str:
    if os_key == "windows":
        return clean_text(platform.version())
    if os_key == "macos":
        return clean_text(platform.mac_ver()[0])
    return clean_text(platform.release())


# --- volume information (filesystem, size, bus, disk model; never the path, letter or label) ---


def volume_info(os_key: str, target: str) -> Dict[str, Any]:
    info: Dict[str, Any] = {"fs": "other", "media": "unknown", "bus": "unknown", "disk_model": "unknown"}
    usage = shutil.disk_usage(target)
    info["size_gb"], info["used_gb"] = round_gb(usage.total), round_gb(usage.used)
    try:
        if os_key == "windows":
            # The path goes to PowerShell through an environment variable, never into the command text
            ps = (
                "$v = Get-Volume -FilePath $env:DSB_TARGET; "
                "$d = $v | Get-Partition | Get-Disk; "
                "$p = Get-PhysicalDisk | Where-Object { $_.DeviceId -eq [string]$d.Number }; "
                "@{ fs = $v.FileSystemType; bus = [string]$d.BusType; model = $d.Model; "
                "media = [string]$p.MediaType } | ConvertTo-Json -Compress"
            )
            out = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps],
                capture_output=True,
                text=True,
                env={**os.environ, "DSB_TARGET": target},
                check=False,
            ).stdout
            d = json.loads(out or "{}")
            info["fs"] = str(d.get("fs", "")).lower()
            info["bus"] = str(d.get("bus", "")).lower()
            info["disk_model"] = clean_text(str(d.get("model", "")))
            info["media"] = str(d.get("media", "")).lower()
        elif os_key == "linux":
            fs = subprocess.run(["findmnt", "-no", "FSTYPE,SOURCE", "--target", target], capture_output=True, text=True)
            fstype, source = (fs.stdout.split() + ["", ""])[:2]
            info["fs"] = fstype.lower()
            lsblk = subprocess.run(
                ["lsblk", "-sJno", "NAME,TYPE,MODEL,ROTA,TRAN", source], capture_output=True, text=True
            ).stdout
            disks: List[Dict[str, Any]] = []

            def walk(nodes: List[Dict[str, Any]]) -> None:
                for n in nodes:
                    if n.get("type") == "disk":
                        disks.append(n)
                    walk(n.get("children", []) or [])

            walk(json.loads(lsblk or "{}").get("blockdevices", []))
            if disks:
                info["disk_model"] = clean_text(str(disks[0].get("model") or ""))
                rota = disks[0].get("rota")
                info["media"] = "hdd" if rota in (True, "1", 1) else "ssd"
                info["bus"] = str(disks[0].get("tran") or "unknown").lower()
        elif os_key == "macos":
            plist = subprocess.run(["diskutil", "info", "-plist", target], capture_output=True).stdout
            d = plistlib.loads(plist) if plist else {}
            info["fs"] = str(d.get("FilesystemType", "")).lower()
            info["media"] = "ssd" if d.get("SolidState") else "hdd" if "SolidState" in d else "unknown"
            info["bus"] = str(d.get("BusProtocol", "")).lower()
            info["disk_model"] = clean_text(str(d.get("MediaName", "")))
    except (OSError, ValueError, json.JSONDecodeError):
        pass
    fs_alias = {"hfs": "hfs+", "vfat": "fat32", "fat": "fat32", "msdos": "fat32"}
    info["fs"] = fs_alias.get(info["fs"], info["fs"])
    if info["fs"] not in FS_VALUES:
        info["fs"] = "other"
    info["media"] = info["media"] if info["media"] in ("ssd", "hdd") else "unknown"
    bus_alias = {"spaces": "virtual", "file backed virtual": "virtual", "pci express": "nvme", "ata": "sata"}
    info["bus"] = bus_alias.get(info["bus"], info["bus"])
    if info["bus"] not in ("nvme", "sata", "sas", "usb", "scsi", "virtual", "other", "unknown"):
        info["bus"] = "other"
    return info


# --- running the scanners ---


def run_scanners(target: str, args: argparse.Namespace, os_key: str) -> List[Dict[str, Any]]:
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "raw.json"
        cmd = [
            sys.executable,
            str(RUNNER),
            "--path",
            target,
            "--ground-truth",
            str(Path(tmp) / "none.json"),
            "--out",
            str(out),
            "--bin-dir",
            args.bin_dir,
            "--warm-runs",
            str(args.warm_runs),
            "--purge-mode",
            "none" if args.no_cold else "system",
        ]
        if args.scanners:
            cmd += ["--scanners", args.scanners]
        if args.timeout:
            cmd += ["--timeout", str(args.timeout)]
        subprocess.run(cmd, check=False)
        return json.loads(out.read_text(encoding="utf-8")) if out.exists() else []


def to_results(raw: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    results = []
    for e in raw:
        cold, warm = float(e.get("cold_time_ms") or 0), float(e.get("warm_time_ms") or 0)
        if cold <= 0 or warm <= 0 or not e.get("scanned_bytes") or e.get("runner_type") == "win_gui":
            continue  # failed scans, and GUI tools that report no size of their own
        cpu = (e.get("cpu_seconds_runs") or [None])[0]
        reads = (e.get("device_reads_runs") or [None])[0]
        results.append(
            {
                "scanner": e["id"],
                "version": clean_text(str(e.get("version", "")), "unknown"),
                "cold_ms": round(cold, 1),
                "warm_ms": round(warm, 1),
                "warm_runs_ms": [round(float(x), 1) for x in (e.get("warm_runs_ms") or [warm])][:20],
                "peak_rss_mb": round(float(e.get("peak_rss_mb") or 0), 1),
                "cpu_s": round(float(cpu), 2) if cpu is not None else None,
                "reads": int(reads) if reads is not None else None,
                "size_gb": round(float(e["scanned_bytes"]) / 1e9, 1),
                "files_k": round(float(e.get("scanned_files") or 0) / 1000, 1),
            }
        )
    return results


def render_preview(sub: Dict[str, Any], warnings: List[str]) -> str:
    m = sub["machine"]
    lines = [
        f"### 本地真实盘成绩 · {m['cpu']} · {m['logical_cores']} 线程 · {m['ram_gb']} GB",
        "",
        f"系统：{m['os']} {m['os_version']} ({m['arch']}) · 套件版本 `{sub['suite']}` · {sub['date']}",
        "",
    ]
    for i, v in enumerate(sub["volumes"], start=1):
        cold_note = "" if v["cold_purged"] else "（未能清缓存：冷扫实为热扫）"
        lines += [
            f"**盘 {i}**：{v['fs']} · {v['media']} · {v['bus']} · {v['disk_model']} · "
            f"{v['used_gb']}/{v['size_gb']} GB · 约 {v['items_k']}k 项{cold_note}",
            "",
            "| 扫描器 | 冷扫 (s) | 热扫 (s) | 峰值内存 (MB) | 报告大小 (GB) |",
            "| :--- | ---: | ---: | ---: | ---: |",
        ]
        for r in sorted(v["results"], key=lambda r: r["cold_ms"]):
            lines.append(
                f"| {r['scanner']} | {r['cold_ms'] / 1000:.2f} | {r['warm_ms'] / 1000:.2f} | {r['peak_rss_mb']:.0f} "
                f"| {r['size_gb']} |"
            )
        lines.append("")
    if warnings:
        lines += ["> [!WARNING]"] + [f"> {w}" for w in warnings] + [""]
    return "\n".join(lines)


def submit(sub: Dict[str, Any], preview: str, repo: str, out_dir: Path) -> None:
    body = (
        f"{MARKER}\n{preview}\n\n<details><summary>提交的数据（JSON）</summary>\n\n```json\n"
        f"{json.dumps(sub, ensure_ascii=False, indent=1)}\n```\n\n</details>\n"
    )
    body_file = out_dir / "issue_body.md"
    body_file.write_text(body, encoding="utf-8")
    title = f"[成绩] {sub['machine']['cpu']} · " + ", ".join(sorted({v["fs"] for v in sub["volumes"]}))
    gh = shutil.which("gh")
    if gh and subprocess.run([gh, "auth", "status"], capture_output=True).returncode == 0:
        subprocess.run(
            [gh, "issue", "create", "-R", repo, "--title", title, "--body-file", str(body_file)], check=False
        )
        return
    print(
        "\n没有找到已登录的 GitHub CLI（gh）。请手动提交：\n"
        f"  1. 打开 https://github.com/{repo}/issues/new?template=benchmark-submission.yml\n"
        f"  2. 把 {out_dir / 'submission.json'} 的全部内容粘贴到表单里\n"
    )


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    ap = argparse.ArgumentParser(description="Benchmark the pinned scanners on your own drives")
    ap.add_argument("--target", action="append", required=True, help="Folder or drive root to scan (repeatable)")
    ap.add_argument("--scanners", default="", help="Comma-separated scanner ids (default: all for this platform)")
    ap.add_argument("--bin-dir", default=str(REPO / "bin"))
    ap.add_argument("--out-dir", default=str(REPO / "local-results"))
    ap.add_argument("--warm-runs", type=int, default=3)
    ap.add_argument("--timeout", type=int, default=3600, help="Seconds allowed per scan")
    ap.add_argument("--no-cold", action="store_true", help="Skip the cache purge (warm-only results)")
    ap.add_argument("--submit", action="store_true", help="After review, open a GitHub issue with the submission")
    ap.add_argument("--yes", action="store_true", help="Do not ask before submitting")
    ap.add_argument("--repo", default="DuskXi/Disk-Scan-Benchmark")
    args = ap.parse_args()

    os_key, arch_key = detect_os_arch()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run([sys.executable, str(RUNNER), "--install-only", "--bin-dir", args.bin_dir], check=False)

    volumes: List[Dict[str, Any]] = []
    for target in args.target:
        print(f"\n######## 扫描第 {len(volumes) + 1} 个目标 ########")
        raw = run_scanners(target, args, os_key)
        results = to_results(raw)
        if not results:
            print("[local] 这个目标没有得到任何有效成绩，跳过")
            continue
        info = volume_info(os_key, target)
        counts = [r["files_k"] for r in results if r["files_k"] > 0]
        info["items_k"] = round(statistics.median(counts)) if counts else 0
        info["cold_purged"] = bool(raw) and all(e.get("cold_purged") for e in raw if "cold_purged" in e)
        info["results"] = results
        volumes.append(info)
    if not volumes:
        print("[local] 没有任何有效成绩")
        return 1

    sub = {
        "schema": SCHEMA,
        "suite": suite_version(),
        "date": dt.date.today().isoformat(),
        "machine": {
            "os": os_key,
            "os_version": os_version(os_key),
            "arch": arch_key,
            "cpu": cpu_model(os_key),
            "logical_cores": os.cpu_count() or 1,
            "ram_gb": ram_gb(os_key),
        },
        "volumes": volumes,
    }
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    errors, warnings = validate(sub, {s["id"] for s in registry["scanners"]})
    preview = render_preview(sub, warnings)
    (out_dir / "submission.json").write_text(json.dumps(sub, ensure_ascii=False, indent=1), encoding="utf-8")
    (out_dir / "submission.md").write_text(preview, encoding="utf-8")
    print("\n" + preview)
    print(f"\n完整的提交数据：{out_dir / 'submission.json'}（提交前请自己检查一遍）")
    if errors:
        print("\n这份数据没有通过校验，不能提交：\n  " + "\n  ".join(errors))
        return 1
    if args.submit:
        if not args.yes:
            answer = input("\n确认把上面的数据公开提交到 GitHub Issue？输入 yes 继续：").strip().lower()
            if answer != "yes":
                print("已取消，没有提交任何内容。")
                return 0
        submit(sub, preview, args.repo, out_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
