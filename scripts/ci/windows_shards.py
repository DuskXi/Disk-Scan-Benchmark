#!/usr/bin/env python3
"""
Print the Windows platforms run in shards (benchmark-sharded.yml) for a preset, as a GitHub output line
(include=<json>), from mid up:

  python windows_shards.py <preset>

  mid, high          Windows ARM64 and ReFS (ReFS with one warm scan at high)
  very-high and up   Windows ARM64 and Windows x64 NTFS. ReFS is left out there: generating its tree took 4 h at high
                     (14x NTFS on the same runner, and growing far faster than the tree: 192 s at low, 25 min at mid),
                     and one shard of dua and one scanner took 4-5 h, so neither fits in a 6-hour job at very-high.
                     NTFS x64 took 172 min in one job at high, too close to the limit at very-high.

Every value is a benchmark-sharded.yml input ("warm" is warm_runs; "gen", "once" and "reset" are the plan's minutes
per million items of generating the tree, of what a shard does once before its scans and of what it does before each
scanner); "share" builds the volume once (on build_runner) and hands it to the shards. NTFS images are built on
Windows x64 for both architectures: on the ARM64 runners Defender's real-time scanning stays on (tamper protection),
and generating a very-high tree there took 5 h, against 31-47 min on x64.
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
    "reset": "1",  # unpacking a fresh copy of the frozen volume before each scanner (~9 GB per million items)
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
    # before its first scan a shard checks what moved, probes the volume and packs it (windows_vhd.ps1 freeze): 4.8-7.3
    # min at high
    "once": "1.3",
    # a fresh copy of the frozen volume before each scanner: 21.8 GB in 64-129 s at high (~3.9 GB per million items)
    "reset": "0.4",
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
    "reset": "1",  # unpacking a fresh copy of the frozen volume before each scanner (~9 GB per million items)
    "max_shards": "8",
    # runners differ: the anchor's cold scan took 243 s on one very-high shard and 423 s on the other, whose scans ran
    # 1.6-1.8x over their estimates (warm scans of a very-high tree are nearly as slow as cold ones there)
    "safety": "2.5",
    "warm": "3",
    "normalize": False,  # windows-summary writes it, with the ReFS cross-check where there is one
    "python_arch": "",
}


# ReFS at high: already one scanner per shard, so a shard that runs long cannot be split any further. Shard 2 of run
# 42861027855 (dua, squirreldisk) ran into the 355-minute job limit and voided the platform: dua was done after 110 min
# and squirreldisk was still scanning 238 min later, against 137 min for all its scans on 42225945135 (on a runner as
# slow on I/O; this one also had the slowest CPU of those 24 shards, 185 ms on hw-probe's test against 86-133). On the
# slow runners the warm scans re-read the disk (dua's first 10-44 min, the next two 1-14 min, squirreldisk's 15-27
# min each), so one warm scan takes 18-62 min out of such a shard. Timed that way, a scanner took up to 2.04x the
# estimate from the published high result in those two runs: safety 1.7 times the plan's 1.25 overhead covers it
# (2.1x), and the largest shard (dua, sysinternals-du) still comes out at ~340 min
REFS_HIGH: Dict[str, Any] = {**REFS, "warm": "1", "safety": "1.7"}


def targets(preset: str) -> List[Dict[str, Any]]:
    if preset == "mid":
        return [ARM64, REFS]
    if preset == "high":
        return [ARM64, REFS_HIGH]
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
