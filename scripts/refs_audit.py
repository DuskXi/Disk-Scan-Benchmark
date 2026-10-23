#!/usr/bin/env python3
"""
NTFS vs ReFS cross-filesystem anti-cheat audit for disk-scanner-bench.

ReFS has no $MFT, so a scanner that quietly parses the raw NTFS MFT instead of walking the
directory tree gets a large speed-up on NTFS that disappears on ReFS. Honest API-based scanners
slow down by roughly the same factor when moving NTFS -> ReFS. This script computes, per scanner,
the ratio  refs_time / ntfs_time  (cold and warm), takes the median ratio over all scanners as the
"overall average difference", and flags scanners whose own ratio deviates from it by more than
--max-deviation (in either direction) as cheating.

Flagged scanners are marked valid=False / DISQUALIFIED in BOTH raw_results files (in place), so
report_gen.py ranks them nowhere and lists them in its disqualification audit.
"""

import argparse
import json
import statistics
import sys
from pathlib import Path
from typing import Any, Dict, List

METRICS = ("cold_time_ms", "warm_time_ms")


def audit(ntfs: List[Dict[str, Any]], refs: List[Dict[str, Any]], max_dev: float, min_scanners: int) -> Dict[str, Any]:
    ntfs_by_id = {e["id"]: e for e in ntfs if e.get("valid", True) is not False}
    refs_by_id = {e["id"]: e for e in refs if e.get("valid", True) is not False}
    common = [i for i in ntfs_by_id if i in refs_by_id]

    ratios: Dict[str, Dict[str, float]] = {m: {} for m in METRICS}
    for sid in common:
        for m in METRICS:
            n, r = float(ntfs_by_id[sid].get(m, 0.0)), float(refs_by_id[sid].get(m, 0.0))
            if n > 0 and r > 0:
                ratios[m][sid] = r / n

    report: Dict[str, Any] = {"max_deviation": max_dev, "centers": {}, "scanners": {}, "flagged": {}, "skipped": False}
    if len(common) < min_scanners:
        report["skipped"] = True
        report["note"] = f"only {len(common)} scanner(s) valid on both filesystems (< {min_scanners}); audit skipped"
        return report

    for m in METRICS:
        if len(ratios[m]) >= min_scanners:
            report["centers"][m] = statistics.median(ratios[m].values())

    for sid in common:
        info: Dict[str, Any] = {}
        for m, center in report["centers"].items():
            if sid not in ratios[m]:
                continue
            r = ratios[m][sid]
            dev = r / center
            info[m] = {"refs_over_ntfs": round(r, 3), "relative_to_median": round(dev, 3)}
            if dev > max_dev or dev < 1.0 / max_dev:
                report["flagged"].setdefault(sid, []).append(
                    f"{m} ReFS/NTFS ratio {r:.2f}x is {dev:.2f}x the overall median {center:.2f}x (allowed 1/{max_dev:g}..{max_dev:g})"
                )
        report["scanners"][sid] = info
    return report


def apply_flags(entries: List[Dict[str, Any]], flagged: Dict[str, List[str]], fs_label: str) -> None:
    for e in entries:
        reasons = flagged.get(e.get("id"))
        if not reasons:
            continue
        e["valid"] = False
        e["invalid_reason"] = (
            f"❌ DISQUALIFIED: NTFS/ReFS cross-check failed on {fs_label} (likely raw $MFT bypass; "
            + "; ".join(reasons)
            + ")"
        )


def render_md(report: Dict[str, Any], names: Dict[str, str]) -> str:
    lines = ["## NTFS vs ReFS Cross-Filesystem Audit", ""]
    if report["skipped"]:
        lines.append(f"> [!NOTE]\n> {report['note']}")
        return "\n".join(lines) + "\n"
    c = report["centers"]
    lines.append(
        "Median ReFS/NTFS slowdown: "
        + ", ".join(f"`{m}` = {v:.2f}x" for m, v in c.items())
        + f". Scanners deviating more than {report['max_deviation']:g}x from the median are disqualified."
    )
    lines += ["", "| Scanner | " + " | ".join(f"{m} ReFS/NTFS (vs median)" for m in c) + " | Verdict |", "| :--- | " + " | ".join("---:" for _ in c) + " | :---: |"]
    for sid, info in report["scanners"].items():
        cells = []
        for m in c:
            d = info.get(m)
            cells.append(f"`{d['refs_over_ntfs']:.2f}x` ({d['relative_to_median']:.2f}x)" if d else "-")
        verdict = "❌ DISQUALIFIED" if sid in report["flagged"] else "✅ Consistent"
        lines.append(f"| **{names.get(sid, sid)}** | " + " | ".join(cells) + f" | {verdict} |")
    return "\n".join(lines) + "\n"


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="NTFS vs ReFS cross-filesystem anti-cheat audit")
    ap.add_argument("--ntfs-results", required=True, help="raw_results.json from the NTFS run (updated in place)")
    ap.add_argument("--refs-results", required=True, help="raw_results.json from the ReFS run (updated in place)")
    ap.add_argument("--max-deviation", type=float, default=2.0, help="Max allowed factor between a scanner's ReFS/NTFS ratio and the median ratio")
    ap.add_argument("--min-scanners", type=int, default=3, help="Minimum scanners valid on both filesystems needed to run the audit")
    ap.add_argument("--md-out", default="", help="Optional Markdown summary path")
    args = ap.parse_args()

    ntfs = json.loads(Path(args.ntfs_results).read_text(encoding="utf-8"))
    refs = json.loads(Path(args.refs_results).read_text(encoding="utf-8"))

    report = audit(ntfs, refs, args.max_deviation, args.min_scanners)
    apply_flags(ntfs, report["flagged"], "NTFS")
    apply_flags(refs, report["flagged"], "ReFS")
    Path(args.ntfs_results).write_text(json.dumps(ntfs, indent=2), encoding="utf-8")
    Path(args.refs_results).write_text(json.dumps(refs, indent=2), encoding="utf-8")

    names = {e["id"]: e.get("scanner", e["id"]) for e in ntfs}
    md = render_md(report, names)
    print(md)
    if args.md_out:
        out = Path(args.md_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(md, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
