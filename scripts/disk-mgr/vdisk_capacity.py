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

PRESET_GB = {
    "very-lite": 100,
    "lite": 350,
    "low": 500,
    "mid": 1024,
    "high": 2048,
    "very-high": 3072,
    "before-death": 3446,
}
PRESET_FILES = {
    "very-lite": 100_000,
    "lite": 400_000,
    "low": 1_000_000,
    "mid": 3_000_000,
    "high": 5_000_000,
    "very-high": 9_000_000,
    "before-death": 14_000_000,
}
# Headroom for metadata, directory index allocation and the reserved tail of small files (see fs-mirage topology).
PER_FILE_HEADROOM_BYTES = 64 * 1024


def capacity_gb(preset: str, logical_gb: Optional[float], minimum_gb: int, total_files: Optional[int] = None) -> int:
    base: float = float(PRESET_GB[preset]) if preset in PRESET_GB else (logical_gb or 100.0)
    files = PRESET_FILES.get(preset, total_files or 1_000_000)
    headroom_gb = files * PER_FILE_HEADROOM_BYTES / 1024**3
    return max(minimum_gb, math.ceil(base * 1.15 + headroom_gb) + 20)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--preset", required=True)
    ap.add_argument("--logical-gb", default="")
    ap.add_argument("--min-gb", type=int, default=60)
    ap.add_argument("--files", default="")
    args = ap.parse_args()
    logical = float(args.logical_gb) if args.logical_gb else None
    print(capacity_gb(args.preset, logical, args.min_gb, int(args.files) if args.files else None))
    return 0


if __name__ == "__main__":
    sys.exit(main())
