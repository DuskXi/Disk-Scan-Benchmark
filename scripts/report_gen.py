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
        "",
        "## 3. Normalized Scanner Benchmark Results",
        "",
        "| Rank | Scanner | Version | Cold Time (ms) | Warm Avg (ms) | Cold Speed (files/s) | $\\eta_{\\text{io}}$ Efficiency | Warm CPU Cost Ratio | Peak RSS (MB) | Accuracy Diff % | Est. PC 1M Scan (s) |",
        "| :---: | :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]

    for idx, r in enumerate(ranked_rows, start=1):
        lines.append(
            f"| {idx} | **{r['scanner']}** | `{r.get('version', '-')}` "
            f"| `{r['cold_time_ms']:,.1f}` "
            f"| `{r['warm_time_ms']:,.1f}` "
            f"| `{r['cold_files_per_sec']:,.0f}` "
            f"| **{r['eta_io_percent']:.1f}%** "
            f"| `{r['cpu_cost_ratio']:.2f}x` "
            f"| `{r['peak_rss_mb']:.1f}` "
            f"| `{r['accuracy_diff_pct']:+.2f}%` "
            f"| `{r['projected_nvme_1m_sec']:.2f}s` |"
        )

    if invalid_rows:
        lines.extend(
            [
                "",
                "### Excluded (failed traversal sanity check)",
                "",
                "| Scanner | Version | Raw Cold (ms) | Raw Warm (ms) | Reason |",
                "| :--- | :--- | ---: | ---: | :--- |",
            ]
        )
        for r in invalid_rows:
            lines.append(
                f"| **{r['scanner']}** | `{r.get('version', '-')}` | `{r['cold_time_ms']:,.1f}` "
                f"| `{r['warm_time_ms']:,.1f}` | {r.get('invalid_reason', '-')} |"
            )

    lines.extend(
        [
            "",
            "### Metric Definitions",
            "- **$\\eta_{\\text{io}}$ (Cold Cache I/O Efficiency)**: $\\eta_{\\text{io}} = \\frac{\\text{Scanner Cold Speed}}{B_{\\text{meta}}} \\times 100$ (%). All scanners are evaluated with raw `$MFT` bypass disabled (standard OS filesystem API traversal mode).",
            "- **Warm CPU Cost Ratio**: $\\text{CPU Cost Ratio} = \\frac{T_{\\text{scanner-warm}}}{T_{\\text{baseline-cpu}}}$. Lower values indicate less user-space tree construction, string allocation, and sorting overhead.",
            "- **Accuracy Diff %**: Percentage deviation between scanner-reported volume size and `ground_truth.json` (reveals hard-link double counting or sparse block miscalculation).",
            "",
        ]
    )

    return "\n".join(lines), normalized_rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Markdown & JSON benchmark reports")
    parser.add_argument("--ground-truth", default="ground_truth.json", help="Path to ground_truth.json")
    parser.add_argument("--baseline", default="baseline.json", help="Path to baseline.json")
    parser.add_argument("--raw-results", default="raw_results.json", help="Path to raw_results.json")
    parser.add_argument("--out", default="benchmark_report.md", help="Output Markdown report path")
    parser.add_argument("--json-out", default="normalized_results.json", help="Output normalized JSON path")
    parser.add_argument("--title-suffix", default="", help="Optional suffix for report heading")
    args = parser.parse_args()

    with open(args.ground_truth, "r", encoding="utf-8") as f:
        gt = json.load(f)
    with open(args.baseline, "r", encoding="utf-8") as f:
        baseline = json.load(f)
    with open(args.raw_results, "r", encoding="utf-8") as f:
        raw_results = json.load(f)

    md_text, norm_rows = generate_report(gt, baseline, raw_results, args.title_suffix)

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
