#!/usr/bin/env python3
"""
NTFS vs ReFS cross-filesystem anti-cheat audit for disk-scanner-bench.

ReFS has no $MFT, so a scanner that quietly parses the raw NTFS MFT instead of walking the directory tree gets a
large speed-up on NTFS that disappears on ReFS. A raw MFT read also costs the same whether the cache is cold or warm
(it reads the whole table either way), so such a scanner's NTFS cold and warm times come out nearly equal.

A scanner is disqualified for an MFT escape only when BOTH signs show up:
  1. ReFS is clearly much slower for it than for the others: its ReFS/NTFS time ratio (cold or warm) exceeds the
     median ratio of all scanners by more than --max-deviation;
  2. its NTFS cold and warm times are nearly the same: cold / warm <= --max-cold-warm.
A scanner that is only slow on ReFS (sign 1 without sign 2) does ordinary per-file work that ReFS answers more
slowly, so it is listed as such and keeps its result.

Disqualified scanners are marked valid=False / DISQUALIFIED in the NTFS raw_results file only (in place), so
report_gen.py drops their NTFS ranking and lists it in its disqualification audit. ReFS has no $MFT to take a
shortcut through, so the ReFS run is an ordinary directory walk and stays ranked as long as its own traversal and
accuracy checks passed.
"""

import argparse
import json
import statistics
import sys
from pathlib import Path
from typing import Any, Dict, List

METRICS = ("cold_time_ms", "warm_time_ms")


def audit(
    ntfs: List[Dict[str, Any]],
    refs: List[Dict[str, Any]],
    max_dev: float,
    min_scanners: int,
    max_cold_warm: float = 1.3,
) -> Dict[str, Any]:
    ntfs_by_id = {e["id"]: e for e in ntfs if e.get("valid", True) is not False}
    refs_by_id = {e["id"]: e for e in refs if e.get("valid", True) is not False}
    common = [i for i in ntfs_by_id if i in refs_by_id]

    ratios: Dict[str, Dict[str, float]] = {m: {} for m in METRICS}
    for sid in common:
        for m in METRICS:
            n, r = float(ntfs_by_id[sid].get(m, 0.0)), float(refs_by_id[sid].get(m, 0.0))
            if n > 0 and r > 0:
                ratios[m][sid] = r / n

    report: Dict[str, Any] = {
        "max_deviation": max_dev,
        "max_cold_warm": max_cold_warm,
        "centers": {},
        "scanners": {},
        "flagged": {},
        "slow_on_refs": {},
        "skipped": False,
    }
    if len(common) < min_scanners:
        report["skipped"] = True
        report["note"] = f"only {len(common)} scanner(s) valid on both filesystems (< {min_scanners}); audit skipped"
        return report

    for m in METRICS:
        if len(ratios[m]) >= min_scanners:
            report["centers"][m] = statistics.median(ratios[m].values())

    for sid in common:
        info: Dict[str, Any] = {}
        slower: List[str] = []
        for m, center in report["centers"].items():
            if sid not in ratios[m]:
                continue
            r = ratios[m][sid]
            dev = r / center
            info[m] = {
                "refs_over_ntfs": round(r, 3),
                "relative_to_median": round(dev, 3),
                "ntfs_ms": float(ntfs_by_id[sid][m]),
                "refs_ms": float(refs_by_id[sid][m]),
            }
            if dev > max_dev:
                slower.append(
                    f"{m} ReFS/NTFS ratio {r:.2f}x is {dev:.2f}x the overall median {center:.2f}x"
                    f" (allowed up to {max_dev:g}x)"
                )
        cold = float(ntfs_by_id[sid].get("cold_time_ms", 0.0))
        warm = float(ntfs_by_id[sid].get("warm_time_ms", 0.0))
        cold_warm = cold / warm if cold > 0 and warm > 0 else None
        info["ntfs_cold_over_warm"] = round(cold_warm, 3) if cold_warm is not None else None
        report["scanners"][sid] = info
        if not slower:
            continue
        if cold_warm is not None and cold_warm <= max_cold_warm:
            report["flagged"][sid] = slower + [
                f"NTFS cold/warm {cold_warm:.2f}x <= {max_cold_warm:g}x (cold and warm equally fast, like a raw MFT read)"
            ]
        else:
            report["slow_on_refs"][sid] = slower + [
                (
                    f"NTFS cold/warm {cold_warm:.2f}x: the cold scan reads the disk, not the MFT"
                    if cold_warm is not None
                    else "NTFS cold/warm unknown"
                )
            ]
    return report


def apply_flags(entries: List[Dict[str, Any]], flagged: Dict[str, List[str]], fs_label: str) -> None:
    for e in entries:
        reasons = flagged.get(e["id"])
        if not reasons:
            continue
        e["valid"] = False
        e["invalid_reason"] = (
            f"❌ DISQUALIFIED: NTFS/ReFS cross-check failed on {fs_label} (raw $MFT escape: " + "; ".join(reasons) + ")"
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
        + f". A scanner loses its NTFS result for a raw $MFT escape only when ReFS is more than "
        f"{report['max_deviation']:g}x slower for it than the median **and** its NTFS cold and warm times are within "
        f"{report['max_cold_warm']:g}x of each other. Being only slow on ReFS is listed but not penalised, and the ReFS "
        "result itself is never disqualified here (ReFS has no $MFT)."
    )
    lines += [
        "",
        "| Scanner | "
        + " | ".join(f"{m}: NTFS / ReFS / ratio (vs median)" for m in c)
        + " | NTFS cold/warm | Verdict |",
        "| :--- | " + " | ".join("---:" for _ in c) + " | ---: | :---: |",
    ]
    for sid, info in report["scanners"].items():
        cells = []
        for m in c:
            d = info.get(m)
            cells.append(
                (
                    f"`{d['ntfs_ms']:,.0f}` / `{d['refs_ms']:,.0f}` / "
                    f"`{d['refs_over_ntfs']:.2f}x` ({d['relative_to_median']:.2f}x)"
                )
                if d
                else "-"
            )
        cw = info.get("ntfs_cold_over_warm")
        cells.append(f"`{cw:.2f}x`" if cw is not None else "-")
        if sid in report["flagged"]:
            verdict = "❌ MFT escape (NTFS disqualified)"
        elif sid in report["slow_on_refs"]:
            verdict = "⚠️ Slow on ReFS (not MFT-like)"
        else:
            verdict = "✅ Consistent"
        lines.append(f"| **{names.get(sid, sid)}** | " + " | ".join(cells) + f" | {verdict} |")
    return "\n".join(lines) + "\n"


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    ap = argparse.ArgumentParser(description="NTFS vs ReFS cross-filesystem anti-cheat audit")
    ap.add_argument("--ntfs-results", required=True, help="raw_results.json from the NTFS run (updated in place)")
    ap.add_argument("--refs-results", required=True, help="raw_results.json from the ReFS run (updated in place)")
    ap.add_argument(
        "--max-deviation",
        type=float,
        default=2.0,
        help="Max allowed factor between a scanner's ReFS/NTFS ratio and the median ratio",
    )
    ap.add_argument(
        "--max-cold-warm",
        type=float,
        default=1.3,
        help="NTFS cold/warm ratio at or below which cold and warm count as equally fast (raw MFT read)",
    )
    ap.add_argument(
        "--min-scanners", type=int, default=3, help="Minimum scanners valid on both filesystems needed to run the audit"
    )
    ap.add_argument("--md-out", default="", help="Optional Markdown summary path")
    ap.add_argument("--json-out", default="", help="Optional JSON copy of the audit (for the leaderboard)")
    args = ap.parse_args()

    ntfs = json.loads(Path(args.ntfs_results).read_text(encoding="utf-8"))
    refs = json.loads(Path(args.refs_results).read_text(encoding="utf-8"))

    report = audit(ntfs, refs, args.max_deviation, args.min_scanners, args.max_cold_warm)
    apply_flags(ntfs, report["flagged"], "NTFS")  # the ReFS run cannot use the $MFT, so it keeps its own verdict
    Path(args.ntfs_results).write_text(json.dumps(ntfs, indent=2), encoding="utf-8")
    Path(args.refs_results).write_text(json.dumps(refs, indent=2), encoding="utf-8")

    names = {e["id"]: e.get("scanner", e["id"]) for e in ntfs}
    md = render_md(report, names)
    print(md)
    if args.md_out:
        out = Path(args.md_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(md, encoding="utf-8")
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(report, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
