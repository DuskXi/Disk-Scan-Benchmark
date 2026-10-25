#!/usr/bin/env python3
"""
Scientific Benchmark Report Generator for disk-scanner-bench
Reads ground_truth.json, baseline.json, and raw_results.json, computes normalized
hardware-independent metrics (Cold I/O Efficiency eta_io %, Warm CPU Cost Ratio,
Accuracy Diff %), and generates a comprehensive Markdown report.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def format_bytes_gib(num_bytes: float) -> str:
    gib = num_bytes / (1024.0**3)
    if gib >= 1024.0:
        return f"{gib / 1024.0:.2f} TiB"
    if gib >= 1.0:
        return f"{gib:.2f} GiB"
    mib = num_bytes / (1024.0**2)
    return f"{mib:.2f} MiB"


BALANCE_WEIGHT = 0.5  # w: weight of wall time against resource time in the balanced index
SMALL_PRESETS = ("very-lite", "lite")


def small_preset_notice(preset: str) -> List[str]:
    """Disclaimer under the title of every report and leaderboard of a small preset."""
    if preset not in SMALL_PRESETS:
        return []
    return [
        "> [!WARNING]",
        f"> **仅供参考：** `{preset}` 测试体量过小，本榜单不一定具有真正的性能测试效力。"
        "榜单取的是扫描器进程从启动到退出的总墙钟时间（含启动、初始化等固定开销），"
        "没有采用软件自己上报的实际扫描时间；体量越小，这部分固定开销的占比越大。",
        "",
    ]


def balanced_index(
    wall_s: float, cpu_s: Optional[float], reads: Optional[float], cores: int, iops: float, items: int
) -> Optional[Dict[str, Any]]:
    """
    Balanced resource index of one scan:
      T_cpu = C / P          CPU time of the scanner's process tree spread over all logical CPUs (s)
      T_io  = Q / S_IOPS     device reads it caused, at the disk's random-read ceiling (s)
      M     = T_cpu + T_io   machine-seconds of resources it used
      eta   = max(T_cpu, T_io) / T_wall   how close it kept the busier resource to saturation
      B     = T_wall^w * M^(1-w)          balanced time (s); Score = items / B (items/s, higher is better)
    """
    if cpu_s is None or wall_s <= 0 or cores <= 0:
        return None
    io_counted = iops > 0 and reads is not None
    t_cpu = cpu_s / cores
    t_io = float(reads or 0) / iops if io_counted else 0.0
    m = t_cpu + t_io
    if m <= 0:
        return None
    b = wall_s**BALANCE_WEIGHT * m ** (1.0 - BALANCE_WEIGHT)
    return {
        "t_cpu_s": round(t_cpu, 4),
        "t_io_s": round(t_io, 4),
        "resource_s": round(m, 4),
        "eta": round(max(t_cpu, t_io) / wall_s, 3),
        "balanced_s": round(b, 4),
        "score": round(items / b, 1),
        "io_counted": io_counted,
    }


def defender_rows(raw_results: List[Dict[str, Any]]) -> List[str]:
    """Windows Defender state during the scans (recorded by run_cli_scanners.py on Windows)."""
    state = next((e["defender"] for e in raw_results if isinstance(e.get("defender"), dict)), None)
    if not state:
        return []
    if not state.get("realtime"):
        return ["| **Windows Defender (scans)** | `real-time off` | Scans ran without on-access antivirus scanning |"]
    scope = "benchmark volume excluded" if state.get("bench_excluded") else "benchmark volume **scanned** on access"
    tamper = "; tamper protection on (cannot be turned off)" if state.get("tamper") else ""
    return [f"| **Windows Defender (scans)** | `real-time on` | {scope}{tamper} |"]


def fmt_acc(value: Optional[float]) -> str:
    return "未核验" if value is None else f"{value:+.2f}%"


VERIFY_PARTS = {"size": "大小", "files": "文件数", "zones": "区域", "io-only": "仅 I/O", "none": "无"}


def verification_label(value: Optional[str]) -> str:
    """What the completeness check could look at for this scanner (from run_cli_scanners.py)."""
    if not value:
        return "-"
    return " + ".join(VERIFY_PARTS.get(part, part) for part in value.split("+"))


def _mean(values: List[Any]) -> Optional[float]:
    known = [float(v) for v in values if v is not None]
    return sum(known) / len(known) if known else None


def generate_report(
    gt: Dict[str, Any],
    baseline: Dict[str, Any],
    raw_results: List[Dict[str, Any]],
    title_suffix: str = "",
    cross_fs_checked: bool = False,
) -> Tuple[str, List[Dict[str, Any]]]:
    b_meta = float(baseline.get("b_meta_files_per_sec", 1.0)) or 1.0
    b_seq = float(baseline.get("b_seq_mb_per_sec", 1.0)) or 1.0
    b_cpu = float(baseline.get("b_cpu_ms", 1.0)) or 1.0
    os_name = baseline.get("os", "unknown")
    arch_name = baseline.get("arch", "unknown")
    cores = baseline.get("logical_cores", 1)
    rand_iops = float(baseline.get("b_rand_read_iops", 0.0) or 0.0)

    preset_name = gt.get("preset", "custom")
    total_files = int(gt.get("total_files", 0))
    total_dirs = int(gt.get("total_dirs", 0))
    apparent_bytes = int(gt.get("apparent_size_bytes", 0))
    allocated_bytes = int(gt.get("allocated_size_bytes", 0))
    hardlinks = int(gt.get("total_hardlinks", 0))
    symlinks = int(gt.get("total_symlinks", 0))

    # Consumer PCIe 4.0/5.0 NVMe reference baseline for PC projection
    ref_pc_b_meta = 450_000.0  # files/sec on 16-thread desktop NVMe

    normalized_rows: List[Dict[str, Any]] = []
    for entry in raw_results:
        cold_ms = float(entry.get("cold_time_ms", 0.0))
        warm_ms = float(entry.get("warm_time_ms", 0.0))
        # Throughput is items of the tree per second, whatever count the tool reports (or does not)
        scanned_files = int(entry.get("scanned_files") or total_files)
        scanned_bytes = int(entry.get("scanned_bytes") or 0)
        size_metric = entry.get("size_metric", "allocated")
        ref_bytes = apparent_bytes if size_metric == "apparent" else allocated_bytes

        cold_secs = max(cold_ms / 1000.0, 1e-6)
        cold_speed_fps = scanned_files / cold_secs

        # Core Formula 1: Cold Cache I/O Efficiency (eta_io %)
        eta_io_pct = (cold_speed_fps / b_meta) * 100.0

        # Core Formula 2: Warm Cache Normalized CPU Cost Ratio
        cpu_cost_ratio = warm_ms / b_cpu

        # Accuracy Diff %
        # None = the tool reported no size (GUI tools), so there is nothing to compare
        acc_diff_pct: Optional[float]
        if entry.get("accuracy_diff_pct") is not None and ref_bytes > 0:
            acc_diff_pct = float(entry["accuracy_diff_pct"])
        elif ref_bytes > 0 and scanned_bytes > 0:
            acc_diff_pct = ((scanned_bytes - ref_bytes) / ref_bytes) * 100.0
        else:
            acc_diff_pct = None

        # Projected 1M-file scan time on a Consumer NVMe PC
        effective_pc_fps = max(1.0, (eta_io_pct / 100.0) * ref_pc_b_meta)
        projected_pc_1m_sec = 1_000_000.0 / effective_pc_fps

        cpu_runs = entry.get("cpu_seconds_runs") or []
        read_runs = entry.get("device_reads_runs") or []
        items = total_files + total_dirs
        balanced_cold = balanced_index(
            cold_ms / 1000.0,
            cpu_runs[0] if cpu_runs else None,
            read_runs[0] if read_runs else None,
            int(cores),
            rand_iops,
            items,
        )
        balanced_warm = balanced_index(
            warm_ms / 1000.0, _mean(cpu_runs[1:]), _mean(read_runs[1:]), int(cores), rand_iops, items
        )

        row = {
            **entry,
            "balanced_cold": balanced_cold,
            "balanced_warm": balanced_warm,
            "cold_files_per_sec": round(cold_speed_fps, 1),
            "warm_files_per_sec": round(scanned_files / max(warm_ms / 1000.0, 1e-6), 1),
            "eta_io_percent": round(eta_io_pct, 2),
            "cpu_cost_ratio": round(cpu_cost_ratio, 3),
            "accuracy_diff_pct": round(acc_diff_pct, 2) if acc_diff_pct is not None else None,
            "projected_nvme_1m_sec": round(projected_pc_1m_sec, 2),
        }
        normalized_rows.append(row)

    # Sort by Cold Cache time ascending (fastest first); rows that failed the traversal sanity check are not ranked
    normalized_rows.sort(key=lambda r: r["cold_time_ms"])
    invalid_rows = [r for r in normalized_rows if r.get("valid", True) is False]
    ranked_rows = [r for r in normalized_rows if r.get("valid", True) is not False]

    header_title = f"# Disk Scanner Benchmark Report {title_suffix}".strip()
    lines = [
        header_title,
        "",
        *small_preset_notice(preset_name),
        "## 1. Environment & Hardware Ceiling Baseline (`hw-probe`)",
        "",
        "| Metric | Value | Description |",
        "| :--- | :--- | :--- |",
        f"| **Platform / Arch** | `{os_name} / {arch_name}` | `{cores}` Logical CPU Cores |",
        *defender_rows(raw_results),
        f"| **$B_{{\\text{{meta}}}}$ (Metadata Ceiling)** | `{b_meta:,.0f} files/sec` | Native OS concurrent traversal ceiling (`getdents64` / `FindFirstFileExW`) |",
        f"| **$B_{{\\text{{seq}}}}$ (Sequential Read)** | `{b_seq:,.2f} MB/s` | Unbuffered sequential disk throughput ceiling |",
        f"| **$B_{{\\text{{cpu}}}}$ (Memory Tree Sort)** | `{b_cpu:,.2f} ms` | Pure-memory 1,000,000-node tree aggregation & descending sort baseline |",
        (
            f"| **$S_{{\\text{{IOPS}}}}$ (Random 4 KiB Read)** | `{rand_iops:,.0f} reads/s` | Unbuffered random reads, "
            f"`{baseline.get('rand_detail', {}).get('threads', '-')}` in flight: the I/O ceiling of the balanced index |"
            if rand_iops > 0
            else "| **$S_{\\text{IOPS}}$ (Random 4 KiB Read)** | `-` | not measured by this hw-probe build |"
        ),
        "",
        "## 2. Synthetic Filesystem Ground Truth (`fs-mirage`)",
        "",
        "| Property | Ground Truth Value | Notes |",
        "| :--- | :--- | :--- |",
        f"| **Scale Preset Tier** | `{preset_name}` | Configurable scale preset (`very-lite` / `lite` / `low` / `mid` / `high` / `very-high`) |",
        f"| **Total File Items** | `{total_files:,}` | Includes `{hardlinks:,}` Hard Links & `{symlinks:,}` Symlinks/Loop Traps |",
        f"| **Total Directories** | `{total_dirs:,}` | Deep chains (8-25 levels) + Flat high-density buckets |",
        f"| **Apparent Logical Size** | `{format_bytes_gib(apparent_bytes)}` (`{apparent_bytes:,} B`) | Deduplicated logical volume across all zones |",
        f"| **Allocated Physical Size** | `{format_bytes_gib(allocated_bytes)}` (`{allocated_bytes:,} B`) | Dirty-Extent anchored physical blocks on disk |",
        (
            "| **Creation Timeline** | `aged` | Same tree, created in a years-of-use order: "
            "directory and file records scattered, directory indexes grown in pieces |"
            if gt.get("aged_timeline")
            else "| **Creation Timeline** | `fresh` (`FSM_AGING=0`) | Created directory by directory: records and indexes "
            "contiguous |"
        ),
    ]

    gt_zones: Dict[str, Dict[str, Any]] = gt.get("zones", {})
    if gt_zones:
        lines.extend(
            [
                "",
                "### Ground Truth Zone Topology",
                "",
                "| Zone Name | Role | Planned Files | Planned Dirs | Apparent Size |",
                "| :--- | :--- | ---: | ---: | ---: |",
            ]
        )
        zone_descriptions = {
            "zone_deep": "Deep dependency hierarchy (depth 8-25)",
            "zone_flat_cache": "High-density flat cache/logs",
            "zone_sparse_media": "Preallocated media + a few huge sparse hole files (>99% volume)",
            "zone_edge": "Hardlinks, symlink loops & long paths",
        }
        for z_name, z_data in gt_zones.items():
            desc = zone_descriptions.get(z_name, "Standard synthetic zone")
            z_files = int(z_data.get("files", 0))
            z_dirs = int(z_data.get("dirs", 0))
            z_bytes = int(z_data.get("apparent_size_bytes", 0))
            lines.append(f"| `{z_name}` | {desc} | `{z_files:,}` | `{z_dirs:,}` | `{format_bytes_gib(z_bytes)}` |")

    lines.extend(
        [
            "",
            "## 3. Normalized Scanner Benchmark Results (有效成绩排行榜)",
            "",
            "| Rank | Scanner | Version | Cold Time (ms) | Warm Avg (ms) | Cold Speed (files/s) | Warm Speed (files/s) | Tool-reported Scan (ms) | $\\eta_{\\text{io}}$ Efficiency | Warm CPU Cost Ratio | Peak RSS (MB) | Accuracy Diff % | Verified | Est. PC 1M Scan (s) |",
            "| :---: | :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :---: | ---: |",
        ]
    )

    for idx, r in enumerate(ranked_rows, start=1):
        reported = r.get("tool_reported_scan_ms")
        tool_ms = f"{reported:,.1f}" if reported is not None else "-"
        lines.append(
            f"| {idx} | **{r['scanner']}** | `{r.get('version', '-')}` "
            f"| `{r['cold_time_ms']:,.1f}` "
            f"| `{r['warm_time_ms']:,.1f}` "
            f"| `{r['cold_files_per_sec']:,.0f}` "
            f"| `{r['warm_files_per_sec']:,.0f}` "
            f"| `{tool_ms}` "
            f"| **{r['eta_io_percent']:.1f}%** "
            f"| `{r['cpu_cost_ratio']:.2f}x` "
            f"| `{r['peak_rss_mb']:.1f}` "
            f"| `{fmt_acc(r['accuracy_diff_pct'])}` "
            f"| {verification_label(r.get('verification'))} "
            f"| `{r['projected_nvme_1m_sec']:.2f}s` |"
        )

    lines.extend(
        [
            "",
            f"### 3b. Balanced Resource Index (均衡性能指数, w = {BALANCE_WEIGHT})",
            "",
            "$T_{\\text{cpu}} = C/P$（进程树的 CPU 时间摊到全部逻辑核）；$T_{\\text{io}} = Q/S_{\\text{IOPS}}$（设备读次数按随机读上限折算）；"
            "$M = T_{\\text{cpu}} + T_{\\text{io}}$（占用的机器秒）；$\\eta = \\max(T_{\\text{cpu}}, T_{\\text{io}})/T_{\\text{wall}}$（瓶颈资源利用率）；"
            "$B = T_{\\text{wall}}^{w} \\cdot M^{1-w}$，Score $= N_{\\text{items}}/B$（项/秒，越高越好）。",
            "",
            "| Rank | Scanner | Cold Wall (s) | Cold CPU (core·s) | Cold Reads | Cold $M$ (s) | Cold $\\eta$ | **Cold Score** "
            "| Warm Wall (s) | Warm CPU (core·s) | Warm $M$ (s) | Warm $\\eta$ | **Warm Score** |",
            "| :---: | :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )

    def _cell(v: Any, fmt: str) -> str:
        return f"`{v:{fmt}}`" if v is not None else "`-`"

    def _cold_score(r: Dict[str, Any]) -> float:
        bc = r.get("balanced_cold")
        return float(bc["score"]) if bc else -1.0

    for idx, r in enumerate(sorted(ranked_rows, key=_cold_score, reverse=True), start=1):
        bc, bw = r.get("balanced_cold") or {}, r.get("balanced_warm") or {}
        cpu_runs = r.get("cpu_seconds_runs") or []
        read_runs = r.get("device_reads_runs") or []
        lines.append(
            f"| {idx} | **{r['scanner']}** | {_cell(r['cold_time_ms'] / 1000.0, ',.2f')} "
            f"| {_cell(cpu_runs[0] if cpu_runs else None, ',.2f')} | {_cell(read_runs[0] if read_runs else None, ',')} "
            f"| {_cell(bc.get('resource_s'), ',.2f')} | {_cell(bc.get('eta'), '.2f')} | **{_cell(bc.get('score'), ',.0f')}** "
            f"| {_cell(r['warm_time_ms'] / 1000.0, ',.2f')} | {_cell(_mean(cpu_runs[1:]), ',.2f')} "
            f"| {_cell(bw.get('resource_s'), ',.2f')} | {_cell(bw.get('eta'), '.2f')} | **{_cell(bw.get('score'), ',.0f')}** |"
        )

    lines.extend(
        [
            "",
            "## 4. Disqualified & Invalid Scanners Audit (非法/违规与失败结果明示)",
            "",
        ]
    )
    if invalid_rows:
        lines.extend(
            [
                "| Status | Scanner | Version | Raw Cold (ms) | Raw Warm (ms) | Accuracy Diff % | Detailed Reason |",
                "| :---: | :--- | :--- | ---: | ---: | ---: | :--- |",
            ]
        )
        for r in invalid_rows:
            reason = r.get("invalid_reason", "-")
            if "CANNOT RUN" in reason:
                # never executed (see "unavailable" in scanners_registry.json): no times to show
                lines.append(
                    f"| `⛔ CANNOT RUN` | **{r['scanner']}** | `{r.get('version', '-')}` | - | - | - | {reason} |"
                )
                continue
            status_badge = "❌ DISQUALIFIED" if "DISQUALIFIED" in reason else "⚠️ INVALID"
            lines.append(
                f"| `{status_badge}` | **{r['scanner']}** | `{r.get('version', '-')}` | `{r['cold_time_ms']:,.1f}` "
                f"| `{r['warm_time_ms']:,.1f}` | `{fmt_acc(r['accuracy_diff_pct'])}` | {reason} |"
            )
    else:
        checks = "扫描边界与真实目录遍历完整性核验"
        if cross_fs_checked:
            checks += "，以及 NTFS/ReFS 跨文件系统一致性核验（排除 $MFT 逃逸）"
        lines.append(f"> [!NOTE]\n> 所有参与测试的扫描器均通过了{checks}，无违规或失败成绩。")

    # Section 5: Directory Structure Sampling Comparison Table
    lines.extend(
        [
            "",
            "## 5. Directory Structure Sampling & Ground Truth Verification (目录结构采样对比与完整性核对)",
            "",
            "每个分区统一写成「大小 · 文件数」。扫描器按自己的口径（逻辑大小或磁盘占用）与同口径的真值比较，"
            "括号里是相对真值的偏差；只报大小、不报文件数的扫描器只显示大小。",
            "",
            "| Scanner | 口径 | `zone_deep` | `zone_flat_cache` | `zone_sparse_media` | `zone_edge` |",
            "| :--- | :--- | ---: | ---: | ---: | ---: |",
        ]
    )
    zone_names = ("zone_deep", "zone_flat_cache", "zone_sparse_media", "zone_edge")
    metric_label = {"apparent": "逻辑大小", "allocated": "磁盘占用"}
    gt_key = {"apparent": "apparent_size_bytes", "allocated": "allocated_size_bytes"}

    def _gt_cell(z_name: str, metric: str) -> str:
        z = gt_zones.get(z_name, {})
        return f"{format_bytes_gib(int(z.get(gt_key[metric], 0)))} · {int(z.get('files', 0)):,} files"

    if gt_zones:
        # the on-disk truth per zone exists only in manifests written since fs-mirage measured it
        gt_metrics = ["apparent"] + (
            ["allocated"] if any(z.get("allocated_size_bytes", 0) for z in gt_zones.values()) else []
        )
        for metric in gt_metrics:
            cells = " | ".join(f"`{_gt_cell(z, metric)}`" for z in zone_names)
            lines.append(f"| **Ground Truth (基准真值)** | {metric_label[metric]} | {cells} |")

    for r in normalized_rows:
        if "CANNOT RUN" in str(r.get("invalid_reason", "")):
            continue
        samples: Dict[str, Dict[str, Any]] = r.get("structure_samples", {})
        metric = "apparent" if r.get("size_metric") == "apparent" else "allocated"

        if not samples:
            note = "N/A (GUI Monitor)" if r.get("runner_type") == "win_gui" else "N/A (Summary-only)"
            cells = " | ".join(f"`{note}`" for _ in zone_names)
            lines.append(f"| **{r['scanner']}** | {metric_label[metric]} | {cells} |")
            continue

        def _fmt_zone(z_name: str, metric: str = metric) -> str:
            if z_name not in samples:
                return "❌ Missing"
            data = samples[z_name]
            size = int(data.get("allocated_bytes") or data.get("apparent_bytes") or 0)
            if size <= 0:
                return "✅ Detected" if data.get("detected") else "✅ Matched"
            truth = gt_zones.get(z_name, {})
            cell = format_bytes_gib(size)
            ref = int(truth.get(gt_key[metric], 0))
            if ref > 0:
                cell += f" ({(size - ref) / ref * 100:+.1f}%)"
            files = int(data.get("files", 0))
            if files > 0:
                cell += f" · {files:,} files"
                missing = files - int(truth.get("files", files))
                if missing:
                    cell += f" ({missing:+,})"
            return cell

        cells = " | ".join(f"`{_fmt_zone(z)}`" for z in zone_names)
        lines.append(f"| **{r['scanner']}** | {metric_label[metric]} | {cells} |")

    lines.extend(
        [
            "",
            "### Metric Definitions",
            "- **Small presets (<= 400k files) and speed ranking**: whole-process wall time includes fixed start-up cost (interpreter / thread-pool init, and a 2.2 s floor for GUI monitors), so use `Warm Speed (files/s)` at `mid` or larger for throughput comparisons. `Tool-reported Scan (ms)` is the scan time a tool prints about itself, excluding start-up.",
            "- **$\\eta_{\\text{io}}$ (Cold Cache I/O Efficiency)**: $\\eta_{\\text{io}} = \\frac{\\text{Scanner Cold Speed}}{B_{\\text{meta}}} \\times 100$ (%). All scanners are evaluated with raw `$MFT` bypass disabled (standard OS filesystem API traversal mode).",
            "- **Warm CPU Cost Ratio**: $\\text{CPU Cost Ratio} = \\frac{T_{\\text{scanner-warm}}}{T_{\\text{baseline-cpu}}}$. Lower values indicate less user-space tree construction, string allocation, and sorting overhead.",
            "- **Accuracy Diff %**: Percentage deviation between scanner-reported volume size and `ground_truth.json` (reveals hard-link double counting or sparse block miscalculation). `未核验` = the tool reported no size of its own.",
            "- **Verified (核验)**: what the completeness check could use, all of it reported by the tool itself and never filled in from the ground truth: 大小 (total ≥ 75% of the truth), 文件数 (≥ 90% of the files), 区域 (every top-level folder present and ≥ 75% of its size); 仅 I/O = a GUI tool with no output, checked only by its directory-enumeration I/O count.",
            "",
        ]
    )

    return "\n".join(lines), normalized_rows


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    parser = argparse.ArgumentParser(description="Generate Markdown & JSON benchmark reports")
    parser.add_argument("--ground-truth", default="ground_truth.json", help="Path to ground_truth.json")
    parser.add_argument("--baseline", default="baseline.json", help="Path to baseline.json")
    parser.add_argument("--raw-results", default="raw_results.json", help="Path to raw_results.json")
    parser.add_argument("--out", default="benchmark_report.md", help="Output Markdown report path")
    parser.add_argument("--json-out", default="normalized_results.json", help="Output normalized JSON path")
    parser.add_argument("--title-suffix", default="", help="Optional suffix for report heading")
    parser.add_argument(
        "--cross-fs-checked",
        action="store_true",
        help="Mention the NTFS/ReFS cross-filesystem audit in the all-clear note (Windows only)",
    )
    args = parser.parse_args()

    with open(args.ground_truth, "r", encoding="utf-8") as f:
        gt = json.load(f)
    with open(args.baseline, "r", encoding="utf-8") as f:
        baseline = json.load(f)
    with open(args.raw_results, "r", encoding="utf-8") as f:
        raw_results = json.load(f)

    md_text, norm_rows = generate_report(gt, baseline, raw_results, args.title_suffix, args.cross_fs_checked)

    out_md = Path(args.out)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text(md_text, encoding="utf-8")

    out_json = Path(args.json_out)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(
            {
                "ground_truth": gt,
                "baseline": baseline,
                "results": norm_rows,
            },
            f,
            indent=2,
        )

    print(f"[report_gen] Generated Markdown report at {out_md} and JSON summary at {out_json}")
    return 0


if __name__ == "__main__":
    from typing import Tuple

    sys.exit(main())
