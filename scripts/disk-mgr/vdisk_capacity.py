#!/usr/bin/env python3
"""
Prints the virtual disk capacity (GiB) a benchmark volume needs.

fs-mirage preallocates the large media files on NTFS and ext4 (size on disk == logical size), so the volume must be
able to hold the whole preset volume. The backing images (sparse ext4 loop file / dynamic VHDX) only grow with metadata.
"""

import argparse
import math
import sys
from typing import Optional

PRESET_GB = {"very-lite": 100, "lite": 350, "low": 500, "mid": 1024, "high": 2048, "very-high": 3072}


def capacity_gb(preset: str, logical_gb: Optional[float], minimum_gb: int) -> int:
    base = PRESET_GB.get(preset)
    if base is None:
        base = float(logical_gb) if logical_gb else 100.0
    return max(minimum_gb, math.ceil(base * 1.15) + 20)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--preset", required=True)
    ap.add_argument("--logical-gb", default="")
    ap.add_argument("--min-gb", type=int, default=60)
    args = ap.parse_args()
    logical = float(args.logical_gb) if args.logical_gb else None
    print(capacity_gb(args.preset, logical, args.min_gb))
    return 0


if __name__ == "__main__":
    sys.exit(main())
