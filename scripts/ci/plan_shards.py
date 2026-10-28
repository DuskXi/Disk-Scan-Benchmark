#!/usr/bin/env python3
"""
Split one platform's scanners into shards that each fit in a GitHub job (benchmark-sharded.yml).

The time of every scanner is estimated from the largest published preset that has a valid result for it on this
platform (cold + warm runs, scaled by the file count), then the scanners are packed into as few shards as the budget
allows, longest first into the least loaded shard. The anchor scanner runs in every shard: the merge step scales each
shard's times by how fast the anchor ran there, so scanners measured on different runners stay comparable.

  python plan_shards.py --label macos-x86_64 --preset very-high --warm-runs 1 --github-output "$GITHUB_OUTPUT"
"""

import argparse
import json
import math
import statistics
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts" / "disk-mgr"))
from vdisk_capacity import PRESET_FILES  # noqa: E402

PRESET_ORDER = ["very-lite", "lite", "low", "mid", "high", "very-high", "before-death"]
ARCHES = {"x86_64": "x86_64", "arm64": "aarch64"}


def platform_of(label: str) -> Tuple[str, str]:
    """('macos', 'x86_64'), ('windows', 'aarch64'), ... from a target label like windows-x86_64-refs."""
    parts = label.split("-")
    return parts[0], ARCHES.get(parts[1], parts[1])


def scanners_for(label: str, registry: Path) -> List[str]:
    os_key, arch = platform_of(label)
    data = json.loads(registry.read_text(encoding="utf-8"))
    return [
        s["id"]
        for s in data["scanners"]
        if s.get("enabled", True) and os_key in s.get("platforms", []) and arch in s.get("architectures", [])
    ]


def history(label: str, data_dir: Path, preset: str) -> Tuple[Dict[str, Tuple[float, float]], Set[str]]:
    """
    (scanner id -> (cold, warm) seconds per million items from the largest stored preset up to `preset` with a valid
    result, ids that took part on this platform in any stored preset).
    """
    out: Dict[str, Tuple[float, float]] = {}
    seen: Set[str] = set()
    upto = PRESET_ORDER.index(preset) if preset in PRESET_ORDER else len(PRESET_ORDER) - 1
    for p in PRESET_ORDER[: upto + 1]:  # later (larger) presets overwrite smaller ones
        path = data_dir / f"standard-{p}.json"
        if not path.exists():
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))["payload"]
        files = (int(payload.get("files") or 0) + int(payload.get("dirs") or 0)) / 1e6
        for sid, e in payload.get("per_platform", {}).get(label, {}).items():
            seen.add(sid)
            if e.get("status") == "ok" and files > 0:
                out[sid] = (e["cold_s"] / files, e["warm_s"] / files)
    return out, seen


def plan(
    scanners: List[str],
    per_million: Dict[str, Tuple[float, float]],
    seen: Set[str],
    items_m: float,
    warm_runs: int,
    anchor: str,
    budget_s: float,
    max_shards: int,
    safety: float,
    min_shards: int = 1,
    reset_s: float = 0.0,
) -> Tuple[List[List[str]], Dict[str, float]]:
    est: Dict[str, float] = {}
    for sid in scanners:
        if sid in per_million:
            cold, warm = per_million[sid]
            est[sid] = (cold + warm_runs * warm) * items_m * safety
    known = list(est.values())
    # ran here before without a valid result (it may run until it fails): assume one of the slow ones; never seen on
    # this platform although the registry lists it (no native build: the runner skips it): a minute
    slow = max(known) if known else 3600.0
    for sid in scanners:
        est.setdefault(sid, slow if (sid in seen or not seen) else 60.0)
    for sid in scanners:
        est[sid] += reset_s  # the access times are set back before each scanner's cold scan
    anchor_s = est.get(anchor, 0.0)
    rest = sorted((s for s in scanners if s != anchor), key=lambda s: -est[s])
    total = sum(est[s] for s in rest)
    room = max(budget_s - anchor_s, budget_s * 0.25)
    n = max(1, min(max_shards, math.ceil(total / room)))
    n = min(max(n, min_shards), max(1, len(rest)))  # at least min_shards (testing), never an empty shard
    shards: List[List[str]] = [[] for _ in range(n)]
    load = [0.0] * n
    for sid in rest:
        i = load.index(min(load))
        shards[i].append(sid)
        load[i] += est[sid]
    if anchor in scanners:
        for sh in shards:
            sh.insert(0, anchor)
    return [sh for sh in shards if sh], est


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--label", required=True, help="Target label, e.g. macos-x86_64 or windows-x86_64-refs")
    ap.add_argument("--preset", required=True)
    ap.add_argument("--files", type=int, default=0, help="Item count of the tree when the preset is custom")
    ap.add_argument("--warm-runs", type=int, default=3)
    ap.add_argument("--anchor", default="dua", help="Scanner run in every shard to scale the shards to each other")
    ap.add_argument("--budget-min", type=float, default=200.0, help="Estimated scan minutes per shard (at most)")
    ap.add_argument(
        "--gen-min-per-million",
        type=float,
        default=0.0,
        help="Minutes the shard spends generating the tree per million items (0: the tree is downloaded)",
    )
    ap.add_argument("--job-minutes", type=float, default=350.0, help="Time limit of a shard job")
    ap.add_argument("--setup-min", type=float, default=20.0, help="Checkout, build, install, download, hw-probe")
    ap.add_argument("--overhead", type=float, default=1.25, help="Real scan time / estimate (purges, prewarms)")
    ap.add_argument(
        "--reset-min-per-million",
        type=float,
        default=0.0,
        help="Minutes the access-time reset before each scanner's cold scan takes per million items",
    )
    ap.add_argument("--max-shards", type=int, default=6)
    ap.add_argument("--min-shards", type=int, default=1, help="Split at least this far (to test the sharded path)")
    # 1.5: the estimates come from runs with access times off; with them on, cold scans on Windows ARM64 and macOS ARM64
    # took 2-3x as long in the very-lite audit
    ap.add_argument("--safety", type=float, default=1.5, help="Factor on the estimates (bigger trees scale worse)")
    ap.add_argument("--registry", default=str(REPO / "scripts" / "wrappers" / "scanners_registry.json"))
    ap.add_argument("--data-dir", default=str(REPO / "leaderboard" / "data"))
    ap.add_argument("--github-output", default="", help="Append matrix=<json> to this file (GitHub Actions)")
    args = ap.parse_args()

    files: Optional[int] = PRESET_FILES.get(args.preset) or args.files
    if not files:
        ap.error(f"unknown size for preset {args.preset!r}: pass --files")
    items_m = files * 1.12 / 1e6  # directories add ~12% to the items of the stored presets
    scanners = scanners_for(args.label, Path(args.registry))
    per_million, seen = history(args.label, Path(args.data_dir), args.preset)
    gen_min = args.gen_min_per_million * items_m
    budget_min = min(args.budget_min, (args.job_minutes - args.setup_min - gen_min) / args.overhead)
    if budget_min < 30:
        print(f"[plan] WARNING: generating the tree takes ~{gen_min:.0f} min, leaving {budget_min:.0f} min to scan")
        budget_min = 30.0
    shards, est = plan(
        scanners,
        per_million,
        seen,
        items_m,
        args.warm_runs,
        args.anchor,
        budget_min * 60,
        args.max_shards,
        args.safety,
        args.min_shards,
        args.reset_min_per_million * items_m * 60,
    )
    print(
        f"[plan] {args.label} | {args.preset} ({files:,} files) | {len(scanners)} scanners -> {len(shards)} shard(s)"
        f" | scan budget {budget_min:.0f} min per shard"
        + (f" after ~{gen_min:.0f} min of generation" if gen_min else "")
    )
    for i, sh in enumerate(shards, start=1):
        mins = sum(est[s] for s in sh) / 60
        print(f"[plan]   shard {i}: ~{mins:,.0f} min | " + ", ".join(f"{s} ~{est[s] / 60:,.0f}m" for s in sh))
        job = args.setup_min + gen_min + mins * args.overhead
        if job > args.job_minutes:
            # one scanner alone (with the anchor and the generation) can outgrow a job; no split can help then
            print(
                f"::warning::{args.label} shard {i} is estimated at {job:,.0f} min, over the {args.job_minutes:.0f}-minute"
                f" job limit ({', '.join(sh)})"
            )
    invalid = [s for s in scanners if s not in per_million and (s in seen or not seen)]
    absent = [s for s in scanners if s not in per_million and s not in invalid]
    if invalid:
        print(f"[plan] no earlier valid result on {args.label} (estimated as the slowest): {', '.join(invalid)}")
    if absent:
        print(f"[plan] never ran on {args.label} before (estimated at a minute): {', '.join(absent)}")
    matrix = {"include": [{"shard": i, "scanners": ",".join(sh)} for i, sh in enumerate(shards, start=1)]}
    if args.github_output:
        with open(args.github_output, "a", encoding="utf-8") as f:
            f.write(f"matrix={json.dumps(matrix)}\n")
            f.write(f"shards={len(shards)}\n")
            f.write(f"median_estimate_min={statistics.median(est.values()) / 60 if est else 0:.0f}\n")
    else:
        print(json.dumps(matrix))
    return 0


if __name__ == "__main__":
    sys.exit(main())
