#!/usr/bin/env python3
"""
Merge the shards of one platform (benchmark-sharded.yml) into one raw_results.json.

Every shard ran on its own runner, and runners of the same kind differ (the CI disks of two Windows runners were
measured up to twice apart). So every shard also ran the anchor scanner, and each shard's times are scaled by
anchor time in the reference shard / anchor time in this shard, cold and warm on their own. The reference shard is the
first one with a valid anchor result; its baseline and ground truth describe the merged platform. Memory, CPU time
and device reads are not scaled: they do not depend on how fast the runner is.

  python merge_shards.py --shards-dir shards/ --anchor dua --out-dir results/macos-x86_64
"""

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def anchor_times(rows: List[Dict[str, Any]], anchor: str) -> Optional[Tuple[float, float]]:
    """(cold ms, warm ms) of the anchor if its result in this shard is valid."""
    for r in rows:
        if r.get("id") == anchor and r.get("valid", True) is not False:
            cold, warm = float(r.get("cold_time_ms") or 0), float(r.get("warm_time_ms") or 0)
            if cold > 0 and warm > 0:
                return cold, warm
    return None


def scale_row(row: Dict[str, Any], sc: float, sw: float) -> Dict[str, Any]:
    out = dict(row)
    out["unscaled_cold_time_ms"] = row.get("cold_time_ms")
    out["unscaled_warm_time_ms"] = row.get("warm_time_ms")
    if row.get("cold_time_ms") is not None:
        out["cold_time_ms"] = round(float(row["cold_time_ms"]) * sc, 2)
    if row.get("warm_time_ms") is not None:
        out["warm_time_ms"] = round(float(row["warm_time_ms"]) * sw, 2)
    if row.get("warm_runs_ms"):
        out["warm_runs_ms"] = [None if v is None else round(float(v) * sw, 2) for v in row["warm_runs_ms"]]
    if row.get("tool_reported_scan_ms") is not None:
        out["tool_reported_scan_ms"] = round(float(row["tool_reported_scan_ms"]) * sc, 2)
    out["shard_scale_cold"] = round(sc, 4)
    out["shard_scale_warm"] = round(sw, 4)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--shards-dir", required=True, help="Folder holding one sub-folder per shard (with shard.json)")
    ap.add_argument("--anchor", default="dua")
    ap.add_argument("--out-dir", required=True, help="Platform result folder: raw_results.json, baseline.json, ...")
    args = ap.parse_args()

    shards: List[Tuple[int, Path, List[Dict[str, Any]]]] = []
    for meta in sorted(Path(args.shards_dir).rglob("shard.json")):
        info = json.loads(meta.read_text(encoding="utf-8"))
        raw = meta.parent / "raw_results.json"
        rows = json.loads(raw.read_text(encoding="utf-8")) if raw.exists() else []
        shards.append((int(info["shard"]), meta.parent, rows))
    shards.sort(key=lambda s: s[0])
    if not shards:
        print("[merge] no shard results found", file=sys.stderr)
        return 1

    anchors = {n: anchor_times(rows, args.anchor) for n, _, rows in shards}
    ref = next((n for n, _, _ in shards if anchors[n]), shards[0][0])
    ref_dir = next(d for n, d, _ in shards if n == ref)
    ref_anchor = anchors[ref]
    if not ref_anchor:
        print(f"[merge] WARNING: the anchor {args.anchor} has no valid result in any shard; times are left unscaled")

    merged: List[Dict[str, Any]] = []
    summary: List[Dict[str, Any]] = []
    seen: Dict[str, int] = {}
    for n, sdir, rows in shards:
        a = anchors[n]
        sc = ref_anchor[0] / a[0] if (ref_anchor and a) else 1.0
        sw = ref_anchor[1] / a[1] if (ref_anchor and a) else 1.0
        baseline = sdir / "baseline.json"
        iops = json.loads(baseline.read_text(encoding="utf-8")).get("b_rand_read_iops") if baseline.exists() else None
        summary.append(
            {
                "shard": n,
                "reference": n == ref,
                "anchor_cold_ms": a[0] if a else None,
                "anchor_warm_ms": a[1] if a else None,
                "scale_cold": round(sc, 4),
                "scale_warm": round(sw, 4),
                "rand_read_iops": iops,
                "scanners": [r.get("id") for r in rows],
                "scaled": bool(ref_anchor and a),
            }
        )
        for r in rows:
            sid = str(r.get("id"))
            if sid == args.anchor and n != ref:
                continue  # the anchor's result comes from the reference shard only
            if sid in seen:
                print(f"[merge] WARNING: {sid} ran in shards {seen[sid]} and {n}; keeping shard {seen[sid]}")
                continue
            seen[sid] = n
            row = scale_row(r, sc, sw) if n != ref else dict(r, shard_scale_cold=1.0, shard_scale_warm=1.0)
            row["shard"] = n
            merged.append(row)

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "raw_results.json").write_text(json.dumps(merged, indent=2), encoding="utf-8")
    for name in ("baseline.json", "ground_truth.json", "layout.json"):
        if (ref_dir / name).exists():
            shutil.copyfile(ref_dir / name, out / name)
    (out / "shards.json").write_text(
        json.dumps({"anchor": args.anchor, "reference": ref, "shards": summary}, indent=2), encoding="utf-8"
    )

    lines = [
        f"### Shards (anchor `{args.anchor}`, reference shard {ref})",
        "",
        "| Shard | Anchor cold s | Anchor warm s | Scale cold | Scale warm | Random reads/s | Scanners |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | :--- |",
    ]
    for s in summary:
        cold = f"{s['anchor_cold_ms'] / 1000:.1f}" if s["anchor_cold_ms"] else "-"
        warm = f"{s['anchor_warm_ms'] / 1000:.1f}" if s["anchor_warm_ms"] else "-"
        iops = f"{s['rand_read_iops']:,.0f}" if s["rand_read_iops"] else "-"
        mark = " (reference)" if s["reference"] else ("" if s["scaled"] else " (unscaled)")
        lines.append(
            f"| {s['shard']}{mark} | {cold} | {warm} | {s['scale_cold']:.3f} | {s['scale_warm']:.3f} | {iops} "
            f"| {', '.join(str(x) for x in s['scanners'])} |"
        )
    (out / "shards.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    print(f"[merge] {len(merged)} scanner result(s) from {len(shards)} shard(s) -> {out / 'raw_results.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
