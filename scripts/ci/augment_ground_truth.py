#!/usr/bin/env python3
"""
Adds a real (non-generated) directory to an fs-mirage ground_truth.json.

The real part has no manifest, so its numbers come from the independent walker in treewalk.py; the report then marks
the resulting reference as approximate. Reparse points (pnpm junctions) are scanner-dependent, so they widen the
"too many files" slack instead of being added to the expected count.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from treewalk import walk_stats  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ground-truth", required=True)
    ap.add_argument("--real-dir", required=True)
    ap.add_argument("--zone-name", default="real_pnpm")
    args = ap.parse_args()

    gt_path = Path(args.ground_truth)
    gt = json.loads(gt_path.read_text(encoding="utf-8"))
    real = walk_stats(args.real_dir)

    gt["total_files"] += real["files"]
    gt["total_regular_files"] = gt.get("total_regular_files", 0) + real["files"]
    gt["total_dirs"] += real["dirs"]
    gt["apparent_size_bytes"] += real["apparent_bytes"]
    gt["apparent_size_with_hardlinks_bytes"] = gt.get("apparent_size_with_hardlinks_bytes", 0) + real["apparent_bytes"]
    for key in ("allocated_size_bytes", "allocated_size_with_hardlinks_bytes", "allocated_files_only_bytes"):
        if key in gt:
            gt[key] += real["allocated_bytes"]
    gt.setdefault("zones", {})[args.zone_name] = {
        "files": real["files"],
        "dirs": real["dirs"],
        "apparent_size_bytes": real["apparent_bytes"],
    }
    gt["real_tree"] = {**real, "note": "independent walker reference (approximate); junctions are not counted"}
    gt["scan_slack_files"] = gt.get("scan_slack_files", 0) + 2 * real["reparse_points"]
    gt_path.write_text(json.dumps(gt, indent=2), encoding="utf-8")
    print(json.dumps(gt["real_tree"], indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
