#!/usr/bin/env python3
"""
Print the Windows platforms run in shards (benchmark-sharded.yml) for a preset, as a GitHub output line
(include=<json>), from mid up:

  python windows_shards.py <preset>

  mid, high          Windows ARM64 and ReFS
  very-high and up   Windows ARM64 and Windows x64 NTFS. ReFS is left out there: generating its tree took 4 h at high
                     (14x NTFS on the same runner, and growing far faster than the tree: 192 s at low, 25 min at mid),
                     and one shard of dua and one scanner took 4-5 h, so neither fits in a 6-hour job at very-high.
                     NTFS x64 took 172 min in one job at high, too close to the limit at very-high.

Every value is a benchmark-sharded.yml input ("warm" is warm_runs); "share" builds the volume once (on build_runner)
and hands it to the shards. NTFS images are built on Windows x64 for both architectures: on the ARM64 runners
Defender's real-time scanning stays on (tamper protection), and generating a very-high tree there took 5 h, against
31-47 min on x64.
"""

import json
import sys
from typing import Any, Dict, List

ARM64: Dict[str, Any] = {
    "label": "windows-arm64",
    "runner": "windows-11-arm",
    "build_runner": "windows-latest",
    "fs": "ntfs",
    "fs_label": "NTFS",
    # built once and shared: generating took 2.4 h per shard at high (Defender on). Its very-high image (~70 GB) does not
    # fit twice on the runner: each shard keeps it packed (zstd, windows_vhd.ps1 freeze) beside the copy it scans
    "share": True,
    "gen": "26",  # (share: not used) 15-26 min per million items measured at mid and high on ARM64
    "once": "1",  # checking what moved; files are created with old access times
    "max_shards": "8",
    "safety": "1.5",
    "warm": "3",
    "normalize": True,
    "python_arch": "arm64",
}

REFS: Dict[str, Any] = {
    "label": "windows-x86_64-refs",
    "runner": "windows-latest",
    "build_runner": "windows-latest",
    "fs": "refs",
    "fs_label": "ReFS",
    "share": True,
    "gen": "0",
    "once": "1",
    # one scanner per shard if need be: at high the anchor alone took 35-130 min there (runners differ 2.5x on ReFS),
    # and a shard of three scanners ran past the job limit. Scaled up from mid, the estimates came out 1.7-2.8x too low
    # there (warm scans of a high ReFS tree are partly cold)
    "max_shards": "12",
    "safety": "2.5",
    "warm": "3",
    "normalize": False,  # windows-summary writes it, after the NTFS vs ReFS audit
    "python_arch": "",
}

NTFS_X64: Dict[str, Any] = {
    "label": "windows-x86_64",
    "runner": "windows-latest",
    "build_runner": "windows-latest",
    "fs": "ntfs",
    "fs_label": "NTFS",
    # built once: every shard then scans the same image (generating took 31-47 min per shard at very-high)
    "share": True,
    "gen": "4",
    "once": "1",
    "max_shards": "8",
    # runners differ: the anchor's cold scan took 243 s on one very-high shard and 423 s on the other, whose scans ran
    # 1.6-1.8x over their estimates (warm scans of a very-high tree are nearly as slow as cold ones there)
    "safety": "2.5",
    "warm": "3",
    "normalize": False,  # windows-summary writes it, with the ReFS cross-check where there is one
    "python_arch": "",
}


def targets(preset: str) -> List[Dict[str, Any]]:
    if preset in ("mid", "high"):
        return [ARM64, REFS]
    if preset in ("very-high", "before-death"):
        # one warm scan on ARM64 there (as on macOS ARM64): at high dust's warm scans already took 520-706 s against
        # 2076 s cold, and on a very-high tree they come close to the cold one, which put its shard at ~320 min. The
        # estimates scale the quicker warm scans of high, hence safety 2: still one scanner per shard (8), the
        # largest estimated at ~215 min (~150 min expected, ~220 on a slow runner) where 1.5 packed them into 5
        return [{**ARM64, "warm": "1", "safety": "2"}, NTFS_X64]
    return []


def main() -> int:
    print(f"include={json.dumps(targets(sys.argv[1]), separators=(',', ':'))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
