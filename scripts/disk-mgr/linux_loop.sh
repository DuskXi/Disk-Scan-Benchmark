#!/usr/bin/env bash
set -euo pipefail

# Linux loop-device volumes (ext4, btrfs, xfs, zfs) and the optional /dev/shm RAMDisk for disk-scanner-bench
# Usage:
#   ./linux_loop.sh create <size_gb> <mount_path> [--fs ext4|btrfs|xfs|zfs] [--ramdisk] [--inodes <count>]
#   ./linux_loop.sh purge-cache <mount_path>
#   ./linux_loop.sh teardown <mount_path>
#
# Cold cache: ext4 / btrfs / xfs are unmounted, the page cache dropped and the volume mounted again; ZFS keeps its
# own cache (ARC) that drop_caches does not empty, so its pool is exported and imported instead.

CMD="${1:-}"
if [[ -z "$CMD" ]]; then
    echo "Usage: $0 {create|purge-cache|teardown} ..." >&2
    exit 1
fi
shift

STATE_FILE="/tmp/disk_scanner_bench_linux.state"
POOL="benchpool"

mount_fs() {
    # mount_fs <fs> <loop device> <mount path>
    case "$1" in
        btrfs) sudo mount -o noatime,nodiscard "$2" "$3" ;;
        zfs) sudo zpool import -d "$2" "$POOL" ;;  # mounts at the pool's mountpoint
        *) sudo mount -o noatime "$2" "$3" ;;
    esac
    sudo chmod 777 "$3"
}

unmount_fs() {
    # unmount_fs <fs> <mount path>
    if [[ "$1" == "zfs" ]]; then
        sudo zpool export "$POOL" 2>/dev/null || true
    elif mountpoint -q "$2" 2>/dev/null; then
        sudo umount "$2"
    fi
}

read_state() {
    IMG_PATH="/tmp/bench.img"
    LOOP_DEV=""
    FS="ext4"
    if [[ -f "$STATE_FILE" ]]; then
        IFS='|' read -r SAVED_IMG _ _ SAVED_LOOP SAVED_FS < "$STATE_FILE" || true
        IMG_PATH="${SAVED_IMG:-$IMG_PATH}"
        LOOP_DEV="${SAVED_LOOP:-}"
        FS="${SAVED_FS:-ext4}"
    fi
}

case "$CMD" in
    create)
        SIZE_GB="${1:-60}"
        MOUNT_PATH="${2:-/mnt/bench}"
        shift 2 || true

        USE_RAMDISK=0
        INODES=4000000
        FS="ext4"
        while [[ $# -gt 0 ]]; do
            case "$1" in
                --ramdisk) USE_RAMDISK=1; shift ;;
                --inodes) INODES="${2:-4000000}"; shift 2 ;;
                --fs) FS="${2:-ext4}"; shift 2 ;;
                *) shift ;;
            esac
        done
        case "$FS" in ext4|btrfs|xfs|zfs) ;; *) echo "[linux_loop] unknown filesystem: $FS" >&2; exit 1 ;; esac

        if [[ "$USE_RAMDISK" -eq 1 ]]; then
            sudo mount -o remount,size="${SIZE_GB}G" /dev/shm 2>/dev/null || true
            IMG_PATH="/dev/shm/bench.img"
        else
            IMG_PATH="/tmp/bench.img"
        fi
        echo "[linux_loop] Creating a ${SIZE_GB}G sparse ${FS} volume at ${IMG_PATH}..."

        if mountpoint -q "$MOUNT_PATH" 2>/dev/null; then
            sudo umount -l "$MOUNT_PATH" || true
        fi
        rm -f "$IMG_PATH"
        truncate -s "${SIZE_GB}G" "$IMG_PATH"
        if [[ "$FS" == "ext4" ]]; then
            mkfs.ext4 -F -N "$INODES" -b 4096 -E lazy_itable_init=0,lazy_journal_init=0 "$IMG_PATH" >/dev/null
        fi

        sudo mkdir -p "$MOUNT_PATH"
        # Direct I/O loop device: reads go to the runner's disk instead of being served (and read ahead in large
        # chunks) by the host page cache that also holds the image file. tmpfs (RAMDisk) has no O_DIRECT, so it falls
        # back to a buffered loop device.
        LOOP_DEV=$(sudo losetup --find --show --direct-io=on --sector-size 4096 "$IMG_PATH" 2>/dev/null || sudo losetup --find --show "$IMG_PATH")

        case "$FS" in
            btrfs) sudo mkfs.btrfs -f -q -L bench "$LOOP_DEV" ;;
            xfs) sudo mkfs.xfs -f -q -L bench "$LOOP_DEV" ;;  # sector size follows the 4 KiB loop device
            zfs)
                sudo modprobe zfs
                # A 16 GB runner would otherwise let the ARC grow to most of its memory
                echo $((4 << 30)) | sudo tee /sys/module/zfs/parameters/zfs_arc_max >/dev/null
                sudo zpool create -f -o ashift=12 -o cachefile=none \
                    -O atime=off -O compression=off -O xattr=sa -O mountpoint="$MOUNT_PATH" "$POOL" "$LOOP_DEV"
                ;;
        esac
        if [[ "$FS" != "zfs" ]]; then
            mount_fs "$FS" "$LOOP_DEV" "$MOUNT_PATH"
        else
            sudo chmod 777 "$MOUNT_PATH"
        fi

        echo "${IMG_PATH}|${MOUNT_PATH}|${USE_RAMDISK}|${LOOP_DEV}|${FS}" > "$STATE_FILE"
        echo "[linux_loop] ${FS} on ${LOOP_DEV} (direct I/O: $(cat /sys/block/${LOOP_DEV#/dev/}/loop/dio 2>/dev/null || echo ?)) mounted at ${MOUNT_PATH}"
        ;;

    purge-cache)
        MOUNT_PATH="${1:-/mnt/bench}"
        read_state
        echo "[linux_loop] Purging caches of the ${FS} volume at ${MOUNT_PATH}..."
        sync
        unmount_fs "$FS" "$MOUNT_PATH"
        echo 3 | sudo tee /proc/sys/vm/drop_caches >/dev/null
        if [[ -n "$LOOP_DEV" && -b "$LOOP_DEV" ]]; then
            mount_fs "$FS" "$LOOP_DEV" "$MOUNT_PATH"
        else
            sudo mount -o loop,noatime "$IMG_PATH" "$MOUNT_PATH"
            sudo chmod 777 "$MOUNT_PATH"
        fi
        ;;

    teardown)
        MOUNT_PATH="${1:-/mnt/bench}"
        read_state
        echo "[linux_loop] Tearing down ${MOUNT_PATH} (${FS}) and removing ${IMG_PATH}..."
        if [[ "$FS" == "zfs" ]]; then
            sudo zpool destroy -f "$POOL" 2>/dev/null || true
        elif mountpoint -q "$MOUNT_PATH" 2>/dev/null; then
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
