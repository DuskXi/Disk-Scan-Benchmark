#!/usr/bin/env bash
# Access-time write audit (untimed, after the timed scans): the data a scan writes because it updates the access times
# of the files and folders it touches, with the platform's daily-use access-time setting.
#
#   scripts/ci/atime_audit.sh <platform> <fs> <mount path> <results dir> [scanner ids]
#
# A fixed tree (the very-lite preset, 100k items) is generated next to the benchmark tree on the same volume, the
# daily-use setting is turned on (Linux relatime, the default of every distribution; ZFS atime + relatime; Windows NTFS
# last-access updates; ReFS and macOS keep what they ship with), and every scanner scans it once: run_cli_scanners.py
# --reset-atime sets all access times two days back before each scanner, so each one meets the same stale times, and
# flushes the volume before reading its write counter. It also probes whether access times update at all here; where
# they do not (ReFS, or a setting that would need a reboot) report_gen.py leaves the audit out.
# Writes <results dir>/atime_audit.json and atime_audit_gt.json, which report_gen.py picks up.
set -euo pipefail

PLATFORM="$1"
FS="$2"
MOUNT="$3"
OUT="$4"
SCANNERS="${5:-}"

case "$PLATFORM" in
    macos) AUDIT="/tmp/BenchAudit" ;;           # the benchmark tree is a folder on the system volume too
    windows) AUDIT="${MOUNT:0:2}/atime_audit" ;; # X:/bench -> X:/atime_audit
    *) AUDIT="${MOUNT%/}/_atime_audit" ;;       # the benchmark volume is mounted at MOUNT itself
esac

mkdir -p "$OUT"
./target/release/fs-mirage --root "$AUDIT" --preset very-lite --seed 42 --max-physical-mb 100 \
    --manifest-out "$OUT/atime_audit_gt.json" > /dev/null

case "$PLATFORM" in
    linux)
        export BENCH_ATIME=relatime  # linux_loop.sh remounts with it before every cold scan
        if [[ "$FS" == "zfs" ]]; then sudo zfs set atime=on relatime=on benchpool; fi
        ;;
    windows)
        # applies when the volume is mounted again, which purge-cache does before every cold scan
        if [[ "$FS" == "ntfs" ]]; then fsutil behavior set disablelastaccess 0 > /dev/null || true; fi
        ;;
esac

EXTRA=()
if [[ -n "$SCANNERS" ]]; then EXTRA=(--scanners "$SCANNERS"); fi
# in a folder of its own: the runner saves each scanner's output next to its results file
python ./scripts/wrappers/run_cli_scanners.py \
    --path "$AUDIT" \
    --ground-truth "$OUT/atime_audit_gt.json" \
    --out "$OUT/atime_audit/raw_results.json" \
    --bin-dir ./bin \
    --warm-runs 1 \
    --reset-atime \
    ${EXTRA[@]+"${EXTRA[@]}"}  # bash 3.2 (macOS) treats an empty array as unset under set -u
cp "$OUT/atime_audit/raw_results.json" "$OUT/atime_audit.json"
