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
from typing import Any, Dict, List, Tuple


def format_bytes_gib(num_bytes: float) -> str:
    gib = num_bytes / (1024.0**3)
    if gib >= 1024.0:
        return f"{gib / 1024.0:.2f} TiB"
    if gib >= 1.0:
        return f"{gib:.2f} GiB"
    mib = num_bytes / (1024.0**2)
    return f"{mib:.2f} MiB"


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
        scanned_files = int(entry.get("scanned_files", total_files) or total_files)
        scanned_bytes = int(entry.get("scanned_bytes", 0))
        size_metric = entry.get("size_metric", "allocated")
        ref_bytes = apparent_bytes if size_metric == "apparent" else allocated_bytes

        cold_secs = max(cold_ms / 1000.0, 1e-6)
        cold_speed_fps = scanned_files / cold_secs

        # Core Formula 1: Cold Cache I/O Efficiency (eta_io %)
        eta_io_pct = (cold_speed_fps / b_meta) * 100.0

        # Core Formula 2: Warm Cache Normalized CPU Cost Ratio
        cpu_cost_ratio = warm_ms / b_cpu

        # Accuracy Diff %
        if "accuracy_diff_pct" in entry and ref_bytes > 0:
            acc_diff_pct = float(entry["accuracy_diff_pct"])
        elif ref_bytes > 0:
            acc_diff_pct = ((scanned_bytes - ref_bytes) / ref_bytes) * 100.0
        else:
            acc_diff_pct = 0.0

        # Projected 1M-file scan time on a Consumer NVMe PC
        effective_pc_fps = max(1.0, (eta_io_pct / 100.0) * ref_pc_b_meta)
        projected_pc_1m_sec = 1_000_000.0 / effective_pc_fps

        row = {
            **entry,
            "cold_files_per_sec": round(cold_speed_fps, 1),
            "warm_files_per_sec": round(scanned_files / max(warm_ms / 1000.0, 1e-6), 1),
            "eta_io_percent": round(eta_io_pct, 2),
            "cpu_cost_ratio": round(cpu_cost_ratio, 3),
            "accuracy_diff_pct": round(acc_diff_pct, 2),
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
        "## 1. Environment & Hardware Ceiling Baseline (`hw-probe`)",
        "",
        "| Metric | Value | Description |",
        "| :--- | :--- | :--- |",
        f"| **Platform / Arch** | `{os_name} / {arch_name}` | `{cores}` Logical CPU Cores |",
        f"| **$B_{{\\text{{meta}}}}$ (Metadata Ceiling)** | `{b_meta:,.0f} files/sec` | Native OS concurrent traversal ceiling (`getdents64` / `FindFirstFileExW`) |",
        f"| **$B_{{\\text{{seq}}}}$ (Sequential Read)** | `{b_seq:,.2f} MB/s` | Unbuffered sequential disk throughput ceiling |",
        f"| **$B_{{\\text{{cpu}}}}$ (Memory Tree Sort)** | `{b_cpu:,.2f} ms` | Pure-memory 1,000,000-node tree aggregation & descending sort baseline |",
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
            "| Rank | Scanner | Version | Cold Time (ms) | Warm Avg (ms) | Cold Speed (files/s) | Warm Speed (files/s) | Tool-reported Scan (ms) | $\\eta_{\\text{io}}$ Efficiency | Warm CPU Cost Ratio | Peak RSS (MB) | Accuracy Diff % | Est. PC 1M Scan (s) |",
            "| :---: | :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
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
            f"| `{r['accuracy_diff_pct']:+.2f}%` "
            f"| `{r['projected_nvme_1m_sec']:.2f}s` |"
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
            status_badge = "❌ DISQUALIFIED" if "DISQUALIFIED" in reason else "⚠️ INVALID"
            lines.append(
                f"| `{status_badge}` | **{r['scanner']}** | `{r.get('version', '-')}` | `{r['cold_time_ms']:,.1f}` "
                f"| `{r['warm_time_ms']:,.1f}` | `{r['accuracy_diff_pct']:+.2f}%` | {reason} |"
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
            "采样对比各扫描器对顶层分区（`zone_deep`, `zone_flat_cache`, `zone_sparse_media`, `zone_edge`）的识别情况：",
            "",
            "| Scanner | `zone_deep` | `zone_flat_cache` | `zone_sparse_media` | `zone_edge` |",
            "| :--- | :--- | :--- | :--- | :--- |",
        ]
    )

    # Format Ground Truth reference row
    gt_deep_str = f"{gt_zones.get('zone_deep', {}).get('files', 0):,} files" if gt_zones else "-"
    gt_flat_str = f"{gt_zones.get('zone_flat_cache', {}).get('files', 0):,} files" if gt_zones else "-"
    gt_media_bytes = (
        int(gt_zones.get("zone_sparse_media", {}).get("apparent_size_bytes", apparent_bytes))
        if gt_zones
        else apparent_bytes
    )
    gt_media_str = format_bytes_gib(gt_media_bytes)
    gt_edge_str = f"{gt_zones.get('zone_edge', {}).get('files', 0):,} files" if gt_zones else "-"

    lines.append(
        f"| **Ground Truth (基准真值)** | `{gt_deep_str}` | `{gt_flat_str}` | `{gt_media_str}` | `{gt_edge_str}` |"
    )

    for r in normalized_rows:
        samples: Dict[str, Dict[str, Any]] = r.get("structure_samples", {})

        if not samples:
            if r.get("runner_type") == "win_gui":
                note = "N/A (GUI Monitor)"
            else:
                note = "N/A (Summary-only)"
            lines.append(f"| **{r['scanner']}** | `{note}` | `{note}` | `{note}` | `{note}` |")
            continue

        def _fmt_zone(z_name: str) -> str:
            if z_name not in samples:
                return "❌ Missing"
            data = samples[z_name]
            if z_name == "zone_sparse_media":
                if "apparent_bytes" in data and data["apparent_bytes"] > 0:
                    return format_bytes_gib(data["apparent_bytes"])
                if "allocated_bytes" in data and data["allocated_bytes"] > 0:
                    return format_bytes_gib(data["allocated_bytes"])
            if "files" in data and data["files"] > 0:
                return f"{data['files']:,} files"
            if "apparent_bytes" in data and data["apparent_bytes"] > 0:
                return format_bytes_gib(data["apparent_bytes"])
            if "allocated_bytes" in data and data["allocated_bytes"] > 0:
                return format_bytes_gib(data["allocated_bytes"])
            if data.get("detected"):
                return "✅ Detected"
            return "✅ Matched"

        lines.append(
            f"| **{r['scanner']}** | `{_fmt_zone('zone_deep')}` | `{_fmt_zone('zone_flat_cache')}` "
            f"| `{_fmt_zone('zone_sparse_media')}` | `{_fmt_zone('zone_edge')}` |"
        )

    lines.extend(
        [
            "",
            "### Metric Definitions",
            "- **Small presets (<= 400k files) and speed ranking**: whole-process wall time includes fixed start-up cost (interpreter / thread-pool init, and a 2.2 s floor for GUI monitors), so use `Warm Speed (files/s)` at `mid` or larger for throughput comparisons. `Tool-reported Scan (ms)` is the scan time a tool prints about itself, excluding start-up.",
            "- **$\\eta_{\\text{io}}$ (Cold Cache I/O Efficiency)**: $\\eta_{\\text{io}} = \\frac{\\text{Scanner Cold Speed}}{B_{\\text{meta}}} \\times 100$ (%). All scanners are evaluated with raw `$MFT` bypass disabled (standard OS filesystem API traversal mode).",
            "- **Warm CPU Cost Ratio**: $\\text{CPU Cost Ratio} = \\frac{T_{\\text{scanner-warm}}}{T_{\\text{baseline-cpu}}}$. Lower values indicate less user-space tree construction, string allocation, and sorting overhead.",
            "- **Accuracy Diff %**: Percentage deviation between scanner-reported volume size and `ground_truth.json` (reveals hard-link double counting or sparse block miscalculation).",
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
