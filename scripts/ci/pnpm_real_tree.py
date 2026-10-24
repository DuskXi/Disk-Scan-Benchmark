#!/usr/bin/env python3
"""
Builds a large REAL file tree by installing heavy npm projects with pnpm onto the benchmark volume.

pnpm keeps one content-addressed store and hard-links every file into each project's node_modules, then wires the
packages together with junctions - exactly the kind of messy, hard-link- and reparse-point-rich tree real machines have
and that a synthetic generator cannot imitate. Projects are installed one by one until the apparent size reaches the
target; failed installs (network hiccups, yanked versions) are logged and skipped.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
from treewalk import walk_stats  # noqa: E402

REACT = {"react": "18.3.1", "react-dom": "18.3.1"}

# (project name, dependencies, optional post-install command)
PROJECTS: List[Tuple[str, Dict[str, str], Optional[List[str]]]] = [
    ("playwright", {"@playwright/test": "1.48.2"}, ["pnpm", "exec", "playwright", "install"]),
    ("cypress", {"cypress": "13.15.0"}, None),
    ("electron", {"electron": "33.2.0", "electron-builder": "25.1.8"}, None),
    ("puppeteer", {"puppeteer": "23.9.0"}, None),
    (
        "storybook",
        {**REACT, "storybook": "8.4.7", "@storybook/react-vite": "8.4.7", "vite": "5.4.11", "typescript": "5.6.3"},
        None,
    ),
    (
        "next",
        {
            **REACT,
            "next": "14.2.20",
            "typescript": "5.6.3",
            "eslint": "8.57.1",
            "eslint-config-next": "14.2.20",
            "tailwindcss": "3.4.16",
            "@types/react": "18.3.12",
            "@types/node": "22.10.1",
        },
        None,
    ),
    (
        "angular",
        {
            "@angular/cli": "18.2.12",
            "@angular/core": "18.2.13",
            "@angular/common": "18.2.13",
            "@angular/compiler": "18.2.13",
            "@angular/platform-browser": "18.2.13",
            "@angular/router": "18.2.13",
            "rxjs": "7.8.1",
            "zone.js": "0.14.10",
            "typescript": "5.5.4",
        },
        None,
    ),
    ("react-native", {"react": "18.3.1", "react-native": "0.76.3", "expo": "52.0.11"}, None),
    ("nuxt", {"nuxt": "3.14.1592", "vue": "3.5.13"}, None),
    ("gatsby", {**REACT, "gatsby": "5.13.7"}, None),
    ("onnx", {"onnxruntime-node": "1.20.1", "sharp": "0.33.5"}, None),
    (
        "cloud-sdks",
        {
            "aws-sdk": "2.1692.0",
            "googleapis": "144.0.0",
            "@aws-sdk/client-s3": "3.712.0",
            "@azure/storage-blob": "12.26.0",
        },
        None,
    ),
    (
        "toolchain",
        {
            "webpack": "5.97.0",
            "webpack-cli": "5.1.4",
            "jest": "29.7.0",
            "ts-jest": "29.2.5",
            "@babel/core": "7.26.0",
            "@babel/preset-env": "7.26.0",
            "babel-loader": "9.2.1",
            "eslint": "9.16.0",
            "prettier": "3.4.2",
            "typescript": "5.7.2",
            "rollup": "4.28.0",
            "terser": "5.36.0",
        },
        None,
    ),
    # Other versions ship their own binaries, so they add real, non-deduplicated data to reach the size target
    ("playwright-1-44", {"@playwright/test": "1.44.1"}, ["pnpm", "exec", "playwright", "install"]),
    ("playwright-1-40", {"@playwright/test": "1.40.1"}, ["pnpm", "exec", "playwright", "install"]),
    ("electron-32", {"electron": "32.2.6"}, None),
    ("electron-31", {"electron": "31.7.5"}, None),
    ("electron-30", {"electron": "30.5.1"}, None),
    ("electron-29", {"electron": "29.4.6"}, None),
    ("cypress-13-13", {"cypress": "13.13.0"}, None),
    ("cypress-12", {"cypress": "12.17.4"}, None),
    ("puppeteer-22", {"puppeteer": "22.15.0"}, None),
    ("puppeteer-21", {"puppeteer": "21.11.0"}, None),
    ("next-13", {**REACT, "next": "13.5.7", "typescript": "5.4.5", "@types/react": "18.2.79"}, None),
    ("nuxt-3-12", {"nuxt": "3.12.4", "vue": "3.4.38"}, None),
]


def run(cmd: List[str], cwd: Path, env: Dict[str, str], timeout: int = 1800) -> bool:
    started = time.time()
    # pnpm is a .cmd shim on Windows, so resolve it through the shell PATH lookup
    exe = shutil.which(cmd[0]) or cmd[0]
    try:
        # pnpm prints UTF-8; the Windows default (cp1252) crashed the reader thread on some package output,
        # leaving proc.stdout as None
        proc = subprocess.run(
            [exe, *cmd[1:]],
            cwd=str(cwd),
            env=env,
            timeout=timeout,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
        )
    except (subprocess.TimeoutExpired, OSError) as exc:
        print(f"  ! {' '.join(cmd)} failed to run: {exc}")
        return False
    tail = "\n".join(((proc.stdout or "") + (proc.stderr or "")).strip().splitlines()[-6:])
    print(f"  {' '.join(cmd)} -> exit {proc.returncode} in {time.time() - started:.0f}s\n{tail}")
    return proc.returncode == 0


def main() -> int:
    # Windows consoles default to cp1252; pnpm/playwright progress output contains other characters
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dest", required=True, help="Directory that will hold the projects (inside the benchmark tree)")
    ap.add_argument("--store", required=True, help="pnpm store; must be on the same volume so files are hard-linked")
    ap.add_argument("--target-gb", type=float, default=10.0, help="Stop once the apparent size reaches this many GiB")
    ap.add_argument("--stats-out", default="", help="Write the final tree statistics as JSON")
    args = ap.parse_args()

    dest = Path(args.dest)
    dest.mkdir(parents=True, exist_ok=True)
    cache = dest / "_cache"
    env = os.environ.copy()
    env.update(
        {
            "CYPRESS_CACHE_FOLDER": str(cache / "cypress"),
            "PLAYWRIGHT_BROWSERS_PATH": str(cache / "playwright"),
            "PUPPETEER_CACHE_DIR": str(cache / "puppeteer"),
            "npm_config_store_dir": args.store,
            "CI": "true",
        }
    )

    target_bytes = int(args.target_gb * 1024**3)
    installed: List[str] = []
    stats: Dict[str, Any] = {}
    for name, deps, post in PROJECTS:
        stats = walk_stats(str(dest))
        print(f"[pnpm-real] {stats['apparent_bytes'] / 1024**3:.2f} GiB so far, installing '{name}' ...")
        if stats["apparent_bytes"] >= target_bytes:
            break
        proj = dest / name
        proj.mkdir(parents=True, exist_ok=True)
        (proj / "package.json").write_text(
            json.dumps({"name": name, "version": "1.0.0", "private": True, "dependencies": deps}, indent=2),
            encoding="utf-8",
        )
        ok = run(["pnpm", "install", "--store-dir", args.store, "--reporter=append-only"], proj, env)
        if ok and post:
            run(post, proj, env)
        if ok:
            installed.append(name)

    stats = walk_stats(str(dest))
    stats["projects"] = installed
    stats["target_gib"] = args.target_gb
    print(json.dumps(stats, indent=2))
    if args.stats_out:
        Path(args.stats_out).write_text(json.dumps(stats, indent=2), encoding="utf-8")
    if stats["apparent_bytes"] < target_bytes * 0.5:
        print(f"::warning::real pnpm tree only reached {stats['apparent_bytes'] / 1024**3:.2f} GiB of {args.target_gb}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
