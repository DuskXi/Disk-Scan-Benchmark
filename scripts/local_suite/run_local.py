#!/usr/bin/env python3
"""
Local real-drive benchmark suite.

Runs the pinned scanners of this repository against folders or whole drives on your own machine, then writes an
anonymized submission you can review and, if you want, send to the project as a GitHub issue:

  python scripts/local_suite/run_local.py --target D:\\ --target E:\\            # Windows (run elevated for cold scans)
  sudo python3 scripts/local_suite/run_local.py --target /home --target /data  # Linux / macOS
  python scripts/local_suite/run_local.py --target D:\\ --submit                 # review, then open the issue

Before anything runs, the suite prints exactly what it collects and how to prepare the machine, and waits for your
confirmation. See docs/LOCAL_SUITE.md.
"""

import argparse
import ctypes
import datetime as dt
import json
import os
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
sys.path.insert(0, str(REPO / "scripts" / "wrappers"))
sys.path.insert(0, str(HERE))

from hwinfo import clean_text, disk_info, os_detail, physical_cores  # noqa: E402
from run_cli_scanners import detect_os_arch  # noqa: E402
from submission_schema import FS_VALUES, SCHEMA, validate  # noqa: E402

RUNNER = REPO / "scripts" / "wrappers" / "run_cli_scanners.py"
REGISTRY = REPO / "scripts" / "wrappers" / "scanners_registry.json"
MARKER = "<!-- dsb-local-submission -->"
IOPS_TEST_MB = 1024

DECLARATION = """
================================================================
  本地基准套件：收集的数据
================================================================
会收集（只有这些，提交前会再给你看一遍）：
  · 系统：Windows 版本到 25H2 级别加内部版本号 / Linux 发行版和完整内核版本号 / macOS 版本号
  · CPU：型号、物理核数、逻辑核数；内存总量（GB）
  · 每块被测的盘：文件系统、硬盘类型（NVMe SSD / SATA SSD / SATA HDD / SAS ...）、
    连接方式和速度（PCIe 代数与通道数、SATA / SAS 速率）、硬盘型号、容量与已用空间（取整）、
    大致项数、随机 4 KiB 读 IOPS
  · 每个扫描器的成绩：冷扫 / 热扫耗时、峰值内存、CPU 时间、读盘次数、报告的总大小和文件数

绝不收集：任何路径或文件名、盘符、卷标、计算机名、用户名、IP、序列号或其他硬件唯一标识、文件内容。

会写入你的盘：每块盘写入并随即删除一个 1 GB 的临时测试文件（测 IOPS 用，--no-iops 可跳过）。
扫描本身只读取目录信息，不修改任何文件。
"""

CHECKLIST = """
================================================================
  运行前请准备
================================================================
  1. 关掉一直在读写硬盘的软件：
     · 文件索引（Everything、Windows 搜索索引、Spotlight 正在建索引时）
     · 网盘与同步（OneDrive、Dropbox、坚果云、Syncthing……）
     · 下载与做种（BT / PT 客户端、游戏平台的更新下载）
     · 备份与快照（文件历史、Time Machine、Veeam……）
     · 杀毒软件的全盘扫描（实时防护可以保留，但不要正在全盘扫描）
     · 虚拟机、数据库、编译任务等
  2. 笔记本请插上电源，并使用高性能电源模式。
  3. 冷扫需要清空系统文件缓存：Windows 请用管理员终端运行，Linux / macOS 请用 sudo。
  4. 跑分期间不要使用这台电脑做别的事；大盘可能需要几十分钟。
  5. 每块盘要有 2 GB 以上的空闲空间（IOPS 测试用）。
"""


def round_gb(n_bytes: float) -> float:
    gb = n_bytes / 1e9
    return round(gb) if gb < 100 else round(gb, -1)


def suite_version() -> str:
    out = ""
    try:
        out = subprocess.run(
            ["git", "-C", str(REPO), "describe", "--always", "--dirty"], capture_output=True, text=True, check=False
        ).stdout.strip()
    except OSError:
        pass
    return clean_text(out, "unknown")


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
    return "unknown"


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
            m = re.search(r"MemTotal:\s+(\d+)", Path("/proc/meminfo").read_text())
            return max(1, round(int(m.group(1)) / 2**20)) if m else 1
        if os_key == "macos":
            out = subprocess.run(["sysctl", "-n", "hw.memsize"], capture_output=True, text=True).stdout
            return max(1, round(int(out) / 2**30))
    except (OSError, ValueError, AttributeError):
        pass
    return 1


# --- random-read IOPS of a drive (hw-probe --only-rand) ---


def hw_probe_binary(os_key: str) -> Optional[Path]:
    exe = REPO / "target" / "release" / ("hw-probe.exe" if os_key == "windows" else "hw-probe")
    if not exe.exists() and shutil.which("cargo"):
        print("[local] 编译 hw-probe（测 IOPS 用）……")
        subprocess.run(["cargo", "build", "--release", "-p", "hw-probe"], cwd=str(REPO), check=False)
    return exe if exe.exists() else None


def measure_iops(probe: Optional[Path], target: str) -> Optional[int]:
    if probe is None:
        print("[local] 没有 hw-probe（需要安装 Rust 才能编译），跳过 IOPS 测试")
        return None
    if shutil.disk_usage(target).free < 2 * IOPS_TEST_MB * 2**20:
        print("[local] 空闲空间不足 2 GB，跳过这块盘的 IOPS 测试")
        return None
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "rand.json"
        subprocess.run(
            [
                str(probe),
                "--root",
                target,
                "--only-rand",
                "--rand-mb",
                str(IOPS_TEST_MB),
                "--rand-secs",
                "5",
                "--out",
                str(out),
            ],
            check=False,
        )
        if not out.exists():
            return None
        return int(json.loads(out.read_text(encoding="utf-8")).get("b_rand_read_iops", 0)) or None


# --- running the scanners ---


def run_scanners(target: str, args: argparse.Namespace) -> List[Dict[str, Any]]:
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


KIND_LABEL = {
    "nvme_ssd": "NVMe SSD",
    "sata_ssd": "SATA SSD",
    "sata_hdd": "SATA HDD",
    "sas_ssd": "SAS SSD",
    "sas_hdd": "SAS HDD",
    "usb_ssd": "USB SSD",
    "usb_hdd": "USB HDD",
    "virtual": "虚拟盘",
}


def render_preview(sub: Dict[str, Any], warnings: List[str]) -> str:
    m = sub["machine"]
    cores = f"{m.get('physical_cores') or '?'} 核 / {m['logical_cores']} 线程"
    lines = [
        f"### 本地真实盘成绩 · {m['cpu']} · {cores} · {m['ram_gb']} GB",
        "",
        f"系统：{m['os_version']}（{m['arch']}）· 套件版本 `{sub['suite']}` · {sub['date']}",
        "",
    ]
    for i, v in enumerate(sub["volumes"], start=1):
        cold_note = "" if v["cold_purged"] else "（未能清缓存：冷扫实为热扫）"
        iops = f"{v['rand_read_iops']:,} IOPS" if v.get("rand_read_iops") else "IOPS 未测"
        lines += [
            f"**盘 {i}**：{v['fs']} · {KIND_LABEL.get(v['kind'], v['kind'])} · {v['link']} · {v['disk_model']} · "
            f"{iops} · {v['used_gb']}/{v['size_gb']} GB · 约 {v['items_k']}k 项{cold_note}",
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


def confirm(prompt: str) -> bool:
    try:
        return input(prompt).strip().lower() == "yes"
    except EOFError:
        return False


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
    ap.add_argument("--no-iops", action="store_true", help="Skip the random-read IOPS test (writes 1 GB per drive)")
    ap.add_argument("--submit", action="store_true", help="After review, open a GitHub issue with the submission")
    ap.add_argument("--yes", action="store_true", help="Do not ask for confirmation (declaration and submission)")
    ap.add_argument("--repo", default="DuskXi/Disk-Scan-Benchmark")
    args = ap.parse_args()

    print(DECLARATION)
    print(CHECKLIST)
    if not args.yes and not confirm("已阅读上面的说明并做好准备？输入 yes 开始："):
        print("已取消，没有运行任何测试。")
        return 0

    os_key, arch_key = detect_os_arch()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run([sys.executable, str(RUNNER), "--install-only", "--bin-dir", args.bin_dir], check=False)
    probe = None if args.no_iops else hw_probe_binary(os_key)

    volumes: List[Dict[str, Any]] = []
    for target in args.target:
        print(f"\n######## 第 {len(volumes) + 1} 个目标 ########")
        raw = run_scanners(target, args)
        results = to_results(raw)
        if not results:
            print("[local] 这个目标没有得到任何有效成绩，跳过")
            continue
        disk = disk_info(os_key, target)
        usage = shutil.disk_usage(target)
        counts = [r["files_k"] for r in results if r["files_k"] > 0]
        volumes.append(
            {
                "fs": disk["fs"] if disk["fs"] in FS_VALUES else "other",
                "kind": disk["kind"],
                "media": disk["media"],
                "bus": disk["bus"] if disk["bus"] in ("nvme", "sata", "sas", "usb", "scsi", "virtual") else "other",
                "link": disk["link"],
                "disk_model": disk["disk_model"],
                "rand_read_iops": None if args.no_iops else measure_iops(probe, target),
                "size_gb": round_gb(usage.total),
                "used_gb": round_gb(usage.used),
                "items_k": round(statistics.median(counts)) if counts else 0,
                "cold_purged": bool(raw) and all(e.get("cold_purged") for e in raw if "cold_purged" in e),
                "results": results,
            }
        )
    if not volumes:
        print("[local] 没有任何有效成绩")
        return 1

    sub = {
        "schema": SCHEMA,
        "suite": suite_version(),
        "date": dt.date.today().isoformat(),
        "machine": {
            "os": os_key,
            "os_version": os_detail(os_key),
            "arch": arch_key,
            "cpu": cpu_model(os_key),
            "physical_cores": physical_cores(os_key),
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
        if not args.yes and not confirm("\n确认把上面的数据公开提交到 GitHub Issue？输入 yes 继续："):
            print("已取消，没有提交任何内容。")
            return 0
        submit(sub, preview, args.repo, out_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
