#!/usr/bin/env bash
set -euo pipefail

# Linux ext4 Sparse Loop / RAMDisk (/dev/shm) Manager for disk-scanner-bench
# Usage:
#   ./linux_loop.sh create <size_gb> <mount_path> [--ramdisk] [--inodes <count>]
#   ./linux_loop.sh purge-cache <mount_path>
#   ./linux_loop.sh teardown <mount_path>

CMD="${1:-}"
if [[ -z "$CMD" ]]; then
    echo "Usage: $0 {create|purge-cache|teardown} ..." >&2
    exit 1
fi
shift

STATE_FILE="/tmp/disk_scanner_bench_linux.state"

case "$CMD" in
    create)
        SIZE_GB="${1:-60}"
        MOUNT_PATH="${2:-/mnt/bench}"
        shift 2 || true

        USE_RAMDISK=0
        INODES=4000000
        while [[ $# -gt 0 ]]; do
            case "$1" in
                --ramdisk)
                    USE_RAMDISK=1
                    shift
                    ;;
                --inodes)
                    INODES="${2:-4000000}"
                    shift 2
                    ;;
                *)
                    shift
                    ;;
            esac
        done

        if [[ "$USE_RAMDISK" -eq 1 ]]; then
            sudo mount -o remount,size="${SIZE_GB}G" /dev/shm 2>/dev/null || true
            IMG_PATH="/dev/shm/bench.ext4"
            echo "[linux_loop] Creating ${SIZE_GB}G sparse ext4 image in RAMDisk (${IMG_PATH}) with ${INODES} inodes..."
        else
            IMG_PATH="/tmp/bench.ext4"
            echo "[linux_loop] Creating ${SIZE_GB}G sparse ext4 image at ${IMG_PATH} with ${INODES} inodes..."
        fi

        if mountpoint -q "$MOUNT_PATH" 2>/dev/null; then
            sudo umount -l "$MOUNT_PATH" || true
        fi
        rm -f "$IMG_PATH"

        truncate -s "${SIZE_GB}G" "$IMG_PATH"
        mkfs.ext4 -F -N "$INODES" -b 4096 -E lazy_itable_init=0,lazy_journal_init=0 "$IMG_PATH" >/dev/null

        sudo mkdir -p "$MOUNT_PATH"
        # Direct I/O loop device: reads go to the runner's disk instead of being served (and read ahead in large
        # chunks) by the host page cache that also holds the image file. Through the cached loop a cold scan cost
        # few real reads, which hid how poorly a scanner with few threads keeps a real disk busy. tmpfs (RAMDisk)
        # has no O_DIRECT, so it falls back to a buffered loop device.
        LOOP_DEV=$(sudo losetup --find --show --direct-io=on --sector-size 4096 "$IMG_PATH" 2>/dev/null || sudo losetup --find --show "$IMG_PATH")
        sudo mount -o noatime "$LOOP_DEV" "$MOUNT_PATH"
        sudo chmod 777 "$MOUNT_PATH"

        echo "${IMG_PATH}|${MOUNT_PATH}|${USE_RAMDISK}|${LOOP_DEV}" > "$STATE_FILE"
        echo "[linux_loop] Mounted ${IMG_PATH} via ${LOOP_DEV} (direct I/O: $(cat /sys/block/${LOOP_DEV#/dev/}/loop/dio 2>/dev/null || echo ?)) at ${MOUNT_PATH}"
        ;;

    purge-cache)
        MOUNT_PATH="${1:-/mnt/bench}"
        IMG_PATH="/tmp/bench.ext4"
        LOOP_DEV=""
        if [[ -f "$STATE_FILE" ]]; then
            IFS='|' read -r SAVED_IMG SAVED_MNT _ SAVED_LOOP < "$STATE_FILE" || true
            if [[ -n "${SAVED_IMG:-}" ]]; then
                IMG_PATH="$SAVED_IMG"
            fi
            LOOP_DEV="${SAVED_LOOP:-}"
        fi

        echo "[linux_loop] Purging OS page/dentry/inode caches and remounting ${MOUNT_PATH}..."
        sync
        if mountpoint -q "$MOUNT_PATH" 2>/dev/null; then
            sudo umount "$MOUNT_PATH"
        fi
        echo 3 | sudo tee /proc/sys/vm/drop_caches >/dev/null
        # remount through the same (direct I/O) loop device when there is one
        if [[ -n "$LOOP_DEV" && -b "$LOOP_DEV" ]]; then
            sudo mount -o noatime "$LOOP_DEV" "$MOUNT_PATH"
        else
            sudo mount -o loop,noatime "$IMG_PATH" "$MOUNT_PATH"
        fi
        sudo chmod 777 "$MOUNT_PATH"
        ;;

    teardown)
        MOUNT_PATH="${1:-/mnt/bench}"
        IMG_PATH="/tmp/bench.ext4"
        LOOP_DEV=""
        if [[ -f "$STATE_FILE" ]]; then
            IFS='|' read -r SAVED_IMG _ _ SAVED_LOOP < "$STATE_FILE" || true
            if [[ -n "${SAVED_IMG:-}" ]]; then
                IMG_PATH="$SAVED_IMG"
            fi
            LOOP_DEV="${SAVED_LOOP:-}"
        fi

        echo "[linux_loop] Tearing down ${MOUNT_PATH} and removing ${IMG_PATH}..."
        if mountpoint -q "$MOUNT_PATH" 2>/dev/null; then
            sudo umount -l "$MOUNT_PATH" || true
        fi
        if [[ -n "$LOOP_DEV" ]]; then
            sudo losetup -d "$LOOP_DEV" 2>/dev/null || true
        fi
        rm -f "$IMG_PATH" "$STATE_FILE"
        ;;

    *)
        echo "Unknown command: $CMD. Expected create, purge-cache, or teardown." >&2
        exit 1
        ;;
esac
