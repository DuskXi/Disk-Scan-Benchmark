#!/usr/bin/env python3
"""
Print the benchmark job's matrix include list as a GitHub output line (include=<json>).

  python pick_targets.py targets.json <sharded: true|false>

With sharded = true (very-high and up) the macOS targets are left out: benchmark-sharded.yml runs them in shards.
"""

import json
import sys


def main() -> int:
    targets = json.load(open(sys.argv[1], encoding="utf-8"))
    if len(sys.argv) > 2 and sys.argv[2] == "true":
        targets = [t for t in targets if t["platform"] != "macos"]
    print(f"include={json.dumps(targets, separators=(',', ':'))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
