#!/usr/bin/env python3
"""
Independent tree walker used as the reference for trees that fs-mirage did not generate (e.g. a real pnpm install).

It never follows symlinks or junctions (they are counted as one item each), counts every hard link as a separate item
(scanners list each link) but allocates each file only once, which mirrors how disk-usage scanners account for them.
"""

import json
import os
import sys
from typing import Any, Dict, Set, Tuple

CLUSTER = 4096
RESIDENT_LIMIT = 700  # NTFS keeps tiny files inside the MFT record: no clusters allocated


def allocated_for(size: int) -> int:
    if size <= RESIDENT_LIMIT:
        return 0
    return ((size + CLUSTER - 1) // CLUSTER) * CLUSTER


def walk_stats(root: str) -> Dict[str, Any]:
    files = dirs = links = 0
    apparent = allocated = 0
    seen: Set[Tuple[int, int]] = set()
    stack = [root]
    while stack:
        current = stack.pop()
        try:
            it = os.scandir(current)
        except OSError:
            continue
        with it:
            for entry in it:
                try:
                    if entry.is_symlink() or entry.is_junction():
                        links += 1
                        continue
                    if entry.is_dir(follow_symlinks=False):
                        dirs += 1
                        stack.append(entry.path)
                        continue
                    # DirEntry.stat() has no st_ino/st_dev on Windows, so hard links could not be told apart
                    st = os.stat(entry.path, follow_symlinks=False)
                except OSError:
                    continue
                files += 1
                apparent += st.st_size
                key = (st.st_dev, st.st_ino)
                if key not in seen:
                    seen.add(key)
                    allocated += allocated_for(st.st_size)
    return {
        "files": files,
        "dirs": dirs,
        "reparse_points": links,
        "apparent_bytes": apparent,
        "allocated_bytes": allocated,
        "unique_files": len(seen),
    }


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: treewalk.py <dir>", file=sys.stderr)
        return 2
    print(json.dumps(walk_stats(sys.argv[1]), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
