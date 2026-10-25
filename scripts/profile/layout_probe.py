#!/usr/bin/env python3
"""
On-disk layout probe: how "aged" a directory tree looks, measured without any disk scanner.

A tree created directory by directory has each directory's file records (NTFS MFT records / inodes) packed
together, in name order, right next to the directory's own record, and every directory index in one piece. A drive
that grew over years has them scattered and its indexes grown in pieces. This probe walks the tree once and
measures exactly that, so the generator's aging can be compared with (and calibrated against) real drives:

  density      entries / (max id - min id + 1) among one directory's children   (1.0 = one contiguous run)
  adjacency    share of consecutive entries in name order whose ids differ by at most 8
  parent_gap   |child id - directory id|, log2-binned
  extents      pieces of a directory's index (NTFS $I30 allocation via FSCTL_GET_RETRIEVAL_POINTERS, Linux FIEMAP);
               sampled on directories with at least 64 entries

Output is aggregate statistics only (no names or paths), so a real drive's result can be shared.

  python scripts/profile/layout_probe.py D:\\ --json-out layout_D.json
"""

import argparse
import ctypes
import json
import math
import os
import random
import statistics
import struct
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple

IS_WINDOWS = os.name == "nt"


# --- directory enumeration with file ids (one system call per buffer, like the fast scanners) ---

if IS_WINDOWS:
    from ctypes import wintypes

    _k32 = ctypes.WinDLL("kernel32", use_last_error=True)  # type: ignore[attr-defined]
    _k32.CreateFileW.restype = wintypes.HANDLE
    _k32.CreateFileW.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    ]
    _k32.GetFileInformationByHandleEx.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
    _k32.GetFileInformationByHandle.argtypes = [wintypes.HANDLE, ctypes.c_void_p]
    _k32.DeviceIoControl.argtypes = [
        wintypes.HANDLE,
        wintypes.DWORD,
        ctypes.c_void_p,
        wintypes.DWORD,
        ctypes.c_void_p,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
        ctypes.c_void_p,
    ]
    _k32.CloseHandle.argtypes = [wintypes.HANDLE]
    INVALID = wintypes.HANDLE(-1).value
    FILE_ID_BOTH_DIRECTORY_INFO = 10
    FILE_ID_BOTH_DIRECTORY_RESTART_INFO = 11
    FSCTL_GET_RETRIEVAL_POINTERS = 0x00090073

    def _open(path: str, access: int = 0x1) -> Optional[int]:  # FILE_LIST_DIRECTORY
        h = _k32.CreateFileW("\\\\?\\" + os.path.abspath(path), access, 0x7, None, 3, 0x02000000, None)
        return None if h in (None, INVALID) else h

    def _record(file_id: int) -> int:
        return file_id & 0x0000FFFFFFFFFFFF  # NTFS: low 48 bits = MFT record number

    def list_dir(path: str) -> Tuple[Optional[int], List[Tuple[str, int, bool]]]:
        """(directory's own id, [(name, id, is_dir)]) in enumeration (name) order."""
        h = _open(path)
        if h is None:
            return None, []
        try:

            class BHFI(ctypes.Structure):
                _fields_ = [
                    ("a", wintypes.DWORD),
                    ("t", wintypes.FILETIME * 3),
                    ("serial", wintypes.DWORD),
                    ("szh", wintypes.DWORD),
                    ("szl", wintypes.DWORD),
                    ("links", wintypes.DWORD),
                    ("idh", wintypes.DWORD),
                    ("idl", wintypes.DWORD),
                ]

            info = BHFI()
            own = None
            if _k32.GetFileInformationByHandle(h, ctypes.byref(info)):
                own = _record((info.idh << 32) | info.idl)
            buf = ctypes.create_string_buffer(256 * 1024)
            out: List[Tuple[str, int, bool]] = []
            cls = FILE_ID_BOTH_DIRECTORY_RESTART_INFO
            while _k32.GetFileInformationByHandleEx(h, cls, buf, len(buf)):
                cls = FILE_ID_BOTH_DIRECTORY_INFO
                off = 0
                while True:
                    (nxt,) = struct.unpack_from("<I", buf.raw, off)
                    attrs, name_len = struct.unpack_from("<II", buf.raw, off + 56)
                    (file_id,) = struct.unpack_from("<q", buf.raw, off + 96)
                    name = buf.raw[off + 104 : off + 104 + name_len].decode("utf-16-le", "replace")
                    if name not in (".", ".."):
                        # a directory only if it is not a reparse point: symlinks and junctions to directories also
                        # carry FILE_ATTRIBUTE_DIRECTORY, and following them loops forever on link cycles
                        is_dir = bool(attrs & 0x10) and not attrs & 0x400
                        out.append((name, _record(file_id & 0xFFFFFFFFFFFFFFFF), is_dir))
                    if not nxt:
                        break
                    off += nxt
            return own, out
        finally:
            _k32.CloseHandle(h)

    def index_extents(path: str) -> Optional[int]:
        """Pieces of the directory's $I30 index allocation (None: resident / not readable / not NTFS)."""
        h = _open(path.rstrip("\\/") + ":$I30:$INDEX_ALLOCATION", 0x80)  # FILE_READ_ATTRIBUTES
        if h is None:
            return None
        try:
            start = ctypes.c_longlong(0)
            out = ctypes.create_string_buffer(64 * 1024)
            got = wintypes.DWORD()
            extents = 0
            while True:
                ok = _k32.DeviceIoControl(
                    h, FSCTL_GET_RETRIEVAL_POINTERS, ctypes.byref(start), 8, out, len(out), ctypes.byref(got), None
                )
                err = ctypes.get_last_error()
                if not ok and err != 234:  # ERROR_MORE_DATA
                    return extents or None
                (count,) = struct.unpack_from("<I", out.raw, 0)
                extents += count
                if ok or count == 0:
                    return extents
                (start.value,) = struct.unpack_from("<q", out.raw, 16 + (count - 1) * 16)
        finally:
            _k32.CloseHandle(h)

else:
    import fcntl

    def list_dir(path: str) -> Tuple[Optional[int], List[Tuple[str, int, bool]]]:
        try:
            own = os.stat(path, follow_symlinks=False).st_ino
            with os.scandir(path) as it:
                entries = [(e.name, e.inode(), e.is_dir(follow_symlinks=False)) for e in it]
        except OSError:
            return None, []
        entries.sort(key=lambda e: e[0])  # name order, like an NTFS index
        return own, entries

    def index_extents(path: str) -> Optional[int]:
        """Extents of the directory's blocks via FIEMAP (ext4, btrfs, xfs); None where unsupported."""
        try:
            fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)  # type: ignore[attr-defined]
        except OSError:
            return None
        try:
            # struct fiemap: start, length, flags, mapped_extents, extent_count, reserved; no extent records
            req = struct.pack("=QQIIII", 0, 0xFFFFFFFFFFFFFFFF, 0, 0, 0, 0)
            res = fcntl.ioctl(fd, 0xC020660B, req)  # type: ignore[attr-defined]  # FS_IOC_FIEMAP
            return struct.unpack("=QQIIII", res)[3]
        except OSError:
            return None
        finally:
            os.close(fd)


# --- the walk ---


def walk(root: str, max_dirs: int) -> Iterator[Tuple[str, Optional[int], List[Tuple[str, int, bool]]]]:
    stack = [root]
    seen = 0
    while stack and seen < max_dirs:
        d = stack.pop()
        own, entries = list_dir(d)
        seen += 1
        yield d, own, entries
        stack.extend(os.path.join(d, name) for name, _, is_dir in entries if is_dir)


def log2_bin(n: int) -> int:
    return 0 if n <= 0 else int(math.log2(n)) + 1


def quantiles(values: List[float]) -> Dict[str, float]:
    if not values:
        return {}
    v = sorted(values)
    pick = lambda q: v[min(len(v) - 1, int(q * (len(v) - 1)))]  # noqa: E731
    return {
        "p10": pick(0.10),
        "p25": pick(0.25),
        "p50": pick(0.50),
        "p75": pick(0.75),
        "p90": pick(0.90),
        "mean": statistics.fmean(v),
    }


def probe(root: str, max_dirs: int, extent_samples: int, seed: int) -> Dict[str, Any]:
    t0 = time.monotonic()
    density: List[float] = []
    adjacency: List[float] = []
    gap_bins: Counter = Counter()
    big_dirs: List[str] = []
    n_dirs = n_entries = 0
    for d, own, entries in walk(root, max_dirs):
        n_dirs += 1
        n_entries += len(entries)
        ids = [i for _, i, _ in entries if i]
        if len(ids) >= 2:
            span = max(ids) - min(ids) + 1
            density.append(len(ids) / span)
            adjacency.append(sum(1 for a, b in zip(ids, ids[1:]) if abs(b - a) <= 8) / (len(ids) - 1))
        if own:
            for i in ids:
                gap_bins[log2_bin(abs(i - own))] += 1
        if len(entries) >= 64:
            big_dirs.append(d)
    rng = random.Random(seed)
    sample = big_dirs if len(big_dirs) <= extent_samples else rng.sample(big_dirs, extent_samples)
    # 0 = the filesystem keeps directories outside data extents (btrfs); None = no FIEMAP / not readable (zfs)
    extents = [e for e in (index_extents(d) for d in sample) if e]
    total_gaps = sum(gap_bins.values()) or 1
    return {
        "schema": "dsb-layout-1",
        "directories": n_dirs,
        "entries": n_entries,
        "seconds": round(time.monotonic() - t0, 1),
        "density": quantiles(density),
        "adjacency": quantiles(adjacency),
        "parent_gap_log2_share": {str(k): round(v / total_gaps, 4) for k, v in sorted(gap_bins.items())},
        "parent_gap_within_256": round(sum(v for k, v in gap_bins.items() if k <= 9) / total_gaps, 4),
        "index_extents": quantiles([float(e) for e in extents]),
        "index_extents_sampled": len(extents),
    }


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    ap = argparse.ArgumentParser(description="Measure how aged a tree's on-disk layout looks (aggregates only)")
    ap.add_argument("root")
    ap.add_argument("--max-dirs", type=int, default=2_000_000)
    ap.add_argument("--extent-samples", type=int, default=3000, help="Directories (>= 64 entries) probed for extents")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--json-out", default="")
    args = ap.parse_args()
    result = probe(args.root, args.max_dirs, args.extent_samples, args.seed)
    text = json.dumps(result, indent=1)
    if args.json_out:
        Path(args.json_out).write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
