#!/usr/bin/env python3
"""
Print the benchmark jobs' matrix include lists as GitHub output lines: include=<json> (Linux) and macos=<json>.

  python pick_targets.py targets.json <sharded: true|false>

macOS gets its own job (benchmark-macos), so the leaderboard can be published before the macOS runners (five per
account, scans an order of magnitude slower) are through their queue. With sharded = true (mid and up) the macOS list
is empty: benchmark-sharded.yml runs them in shards.
"""

import json
import sys


def main() -> int:
    targets = json.load(open(sys.argv[1], encoding="utf-8"))
    sharded = len(sys.argv) > 2 and sys.argv[2] == "true"
    others = [t for t in targets if t["platform"] != "macos"]
    macos = [] if sharded else [t for t in targets if t["platform"] == "macos"]
    print(f"include={json.dumps(others, separators=(',', ':'))}")
    print(f"macos={json.dumps(macos, separators=(',', ':'))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
