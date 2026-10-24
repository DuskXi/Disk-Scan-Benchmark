#!/usr/bin/env python3
"""
Read-only "shape profile" of a real directory tree: aggregate histograms only, never a path or a file name.

What it records (all counts / histograms):
  * directories per depth, files per depth
  * how many files and sub-directories a directory holds, per depth bucket (joint, log2-binned)
  * name lengths (stems, extensions, directory names) and coarse character classes
  * file size histogram (log2) incl. the share of empty files
  * attribute shares (hidden / system / read-only / compressed / sparse / reparse / ...)
  * a 1/200 sample of hard-link counts

The profile is later used by fs-mirage (--profile) to generate a tree with the same *style* without any of the original
content. Nothing here can be turned back into names or locations.
"""

import argparse
import json
import os
import sys
import threading
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Tuple

DEPTH_BUCKETS = [(0, 0), (1, 1), (2, 2), (3, 4), (5, 7), (8, 11), (12, 1000)]


def log2_bin(n: int) -> int:
    """0 -> 0, 1 -> 1, 2 -> 2, 3..4 -> 3, 5..8 -> 4, ... (upper bound 2^(bin-1))."""
    return 0 if n <= 0 else (n - 1).bit_length() + 1 if n > 1 else 1


def depth_bucket(d: int) -> int:
    for i, (lo, hi) in enumerate(DEPTH_BUCKETS):
        if lo <= d <= hi:
            return i
    return len(DEPTH_BUCKETS) - 1


class Stats:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.files = 0
        self.dirs = 0
        self.reparse = 0
        self.dirs_by_depth: Counter = Counter()
        self.files_by_depth: Counter = Counter()
        self.joint: Dict[int, Counter] = defaultdict(Counter)  # depth bucket -> (files_bin, subdirs_bin) -> count
        self.stem_len: Counter = Counter()
        self.ext_len: Counter = Counter()
        self.dir_name_len: Counter = Counter()
        self.size_bin_count: Counter = Counter()
        self.size_bin_bytes: Counter = Counter()
        self.zero_files = 0
        self.total_bytes = 0
        self.attrs: Counter = Counter()
        self.char: Counter = Counter()
        self.nlink_sampled = 0
        self.nlink_multi = 0
        self.max_depth = 0

    def merge(self, local: "Stats") -> None:
        with self.lock:
            self.files += local.files
            self.dirs += local.dirs
            self.reparse += local.reparse
            self.max_depth = max(self.max_depth, local.max_depth)
            for name in (
                "dirs_by_depth",
                "files_by_depth",
                "stem_len",
                "ext_len",
                "dir_name_len",
                "size_bin_count",
                "size_bin_bytes",
                "attrs",
                "char",
            ):
                getattr(self, name).update(getattr(local, name))
            for k, v in local.joint.items():
                self.joint[k].update(v)
            self.zero_files += local.zero_files
            self.total_bytes += local.total_bytes
            self.nlink_sampled += local.nlink_sampled
            self.nlink_multi += local.nlink_multi


ATTR_BITS = {
    "readonly": 0x1,
    "hidden": 0x2,
    "system": 0x4,
    "archive": 0x20,
    "temporary": 0x100,
    "sparse": 0x200,
    "compressed": 0x800,
    "offline": 0x1000,
    "encrypted": 0x4000,
}


def classify_name(name: str, c: Counter) -> None:
    if not name.isascii():
        c["non_ascii"] += 1
    if " " in name:
        c["space"] += 1
    if any(ch.isupper() for ch in name):
        c["has_upper"] += 1
    if any(ch.isdigit() for ch in name):
        c["has_digit"] += 1
    if any(ch in "-_." for ch in name):
        c["has_punct"] += 1
    if any(ch in "()[]{}" for ch in name):
        c["has_brackets"] += 1
    c["names"] += 1


def scan_dir(path: str, depth: int, stats: Stats, sample_counter: List[int]) -> List[Tuple[str, int]]:
    local = Stats()
    local.max_depth = depth
    subdirs: List[Tuple[str, int]] = []
    nfiles = 0
    try:
        it = os.scandir(path)
    except OSError:
        return []
    with it:
        for entry in it:
            try:
                is_link = entry.is_symlink() or entry.is_junction()
                if is_link:
                    local.reparse += 1
                    continue
                if entry.is_dir(follow_symlinks=False):
                    subdirs.append((entry.path, depth + 1))
                    local.dir_name_len[min(len(entry.name), 120)] += 1
                    classify_name(entry.name, local.char)
                    continue
                st = entry.stat(follow_symlinks=False)
            except OSError:
                continue
            nfiles += 1
            size = st.st_size
            name = entry.name
            stem, dot, ext = name.rpartition(".")
            if not dot or not stem:
                stem, ext = name, ""
            local.stem_len[min(len(stem), 120)] += 1
            local.ext_len[min(len(ext), 16)] += 1
            classify_name(name, local.char)
            local.total_bytes += size
            if size == 0:
                local.zero_files += 1
            else:
                b = log2_bin(size)
                local.size_bin_count[b] += 1
                local.size_bin_bytes[b] += size
            attrs = getattr(st, "st_file_attributes", 0)
            for key, bit in ATTR_BITS.items():
                if attrs & bit:
                    local.attrs[key] += 1
    local.files = nfiles
    local.dirs = 1
    local.dirs_by_depth[depth] += 1
    local.files_by_depth[depth] += nfiles
    local.joint[depth_bucket(depth)][(log2_bin(nfiles), log2_bin(len(subdirs)))] += 1
    stats.merge(local)
    return subdirs


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("root")
    ap.add_argument("--out", required=True)
    ap.add_argument("--threads", type=int, default=24)
    args = ap.parse_args()
    root = os.path.abspath(args.root)

    stats = Stats()
    dummy: List[int] = [0]
    pending: List[Tuple[str, int]] = [(root, 0)]
    with ThreadPoolExecutor(max_workers=args.threads) as pool:
        while pending:
            batch, pending = pending, []
            for sub in pool.map(lambda pd: scan_dir(pd[0], pd[1], stats, dummy), batch):
                pending.extend(sub)
            print(f"\rdirs={stats.dirs:,} files={stats.files:,}", end="", file=sys.stderr)
    print(file=sys.stderr)

    n = max(stats.files, 1)
    profile: Dict[str, Any] = {
        "schema": 1,
        "note": "aggregate histograms only; no file or directory names, no paths",
        "totals": {
            "files": stats.files,
            "dirs": stats.dirs,
            "reparse_points": stats.reparse,
            "total_bytes": stats.total_bytes,
            "zero_size_files": stats.zero_files,
            "max_depth": stats.max_depth,
            "files_per_dir": stats.files / max(stats.dirs, 1),
        },
        "depth_buckets": DEPTH_BUCKETS,
        "dirs_by_depth": {str(k): v for k, v in sorted(stats.dirs_by_depth.items())},
        "files_by_depth": {str(k): v for k, v in sorted(stats.files_by_depth.items())},
        "dir_shape": {
            str(b): [[fb, sb, c] for (fb, sb), c in sorted(cnt.items())] for b, cnt in sorted(stats.joint.items())
        },
        "stem_len": {str(k): v for k, v in sorted(stats.stem_len.items())},
        "ext_len": {str(k): v for k, v in sorted(stats.ext_len.items())},
        "dir_name_len": {str(k): v for k, v in sorted(stats.dir_name_len.items())},
        "size_bins": {
            "count": {str(k): v for k, v in sorted(stats.size_bin_count.items())},
            "bytes": {str(k): v for k, v in sorted(stats.size_bin_bytes.items())},
        },
        "attr_share": {k: stats.attrs[k] / n for k in ATTR_BITS},
        "name_char_share": {k: v / max(stats.char["names"], 1) for k, v in stats.char.items() if k != "names"},
    }
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=1)
    t = profile["totals"]
    print(
        f"profile written: files={t['files']:,} dirs={t['dirs']:,} files/dir={t['files_per_dir']:.2f} max_depth={t['max_depth']} zero={t['zero_size_files'] / n:.1%}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
