#!/usr/bin/env bash
# Builds the benchmark tree on Btrfs with the Linux kernel driver and packs the disk as a dynamic VHDX for WinBtrfs.
#
#   ./btrfs_image.sh <size_gb> <out.vhdx> <manifest_out> [fs-mirage args...]
#
# Creating files through WinBtrfs slows down far faster than the tree grows (100k files: 15 s, 400k: 13 min, 1M: over
# 100 min), while Linux builds the same aged tree in seconds. Reading a disk that Linux wrote is also what WinBtrfs is
# for (dual boot), so the Windows job gets this image instead of generating the tree itself:
#   - a GPT disk with one partition of the Windows "basic data" type, so Windows brings the volume up and WinBtrfs
#     claims it; 512-byte sectors (the VHDX's own) so the partition table reads the same on both sides;
#   - mounted like the Linux Btrfs benchmark volume (noatime, nodiscard), the tree generated with the same arguments,
#     then remounted and its allocation recounted (Btrfs settles block counts only after the data is flushed);
#   - converted with qemu-img to a dynamic VHDX with 1 MB blocks: unwritten space (holes, preallocated extents) is not
#     stored, so the image is about as large as the metadata and the few hundred MB of written data.
set -euo pipefail

SIZE_GB="$1"
OUT_VHDX="$2"
MANIFEST="$3"
shift 3

WORK="${RUNNER_TEMP:-/tmp}/btrfs_image"
MNT="/mnt/btrfs_image"
IMG="$WORK/bench.img"
FS_MIRAGE="${FS_MIRAGE:-./target/release/fs-mirage}"

mkdir -p "$WORK" "$(dirname "$OUT_VHDX")" "$(dirname "$MANIFEST")"
sudo mkdir -p "$MNT"
rm -f "$IMG"
truncate -s "${SIZE_GB}G" "$IMG"
sgdisk --clear --new 1:2048:0 --typecode 1:0700 --change-name 1:BenchVol "$IMG" > /dev/null

LOOP=$(sudo losetup --find --show --partscan "$IMG")
PART="${LOOP}p1"
cleanup() {
    mountpoint -q "$MNT" && sudo umount "$MNT" || true
    sudo losetup -d "$LOOP" 2> /dev/null || true
}
trap cleanup EXIT
for _ in $(seq 1 50); do
    [ -b "$PART" ] && break
    sleep 0.2
done
[ -b "$PART" ] || { echo "[btrfs_image] partition $PART did not appear" >&2; exit 1; }

sudo mkfs.btrfs -f -q -L BenchVol "$PART"
sudo mount -o noatime,nodiscard "$PART" "$MNT"
sudo chmod 777 "$MNT"
mkdir -p "$MNT/bench"
echo "[btrfs_image] $(sudo btrfs --version | head -1); features: $(sudo btrfs inspect-internal dump-super "$PART" | grep -E '^(incompat_flags|compat_ro_flags)' | tr -s ' ' | tr '\n' ' ')"

GEN_ARGS=(--root "$MNT/bench" --manifest-out "$MANIFEST" "$@")
"$FS_MIRAGE" "${GEN_ARGS[@]}"
sync
sudo umount "$MNT"
echo 3 | sudo tee /proc/sys/vm/drop_caches > /dev/null
sudo mount -o noatime,nodiscard "$PART" "$MNT"
"$FS_MIRAGE" "${GEN_ARGS[@]}" --recount-alloc
# WinBtrfs maps the POSIX mode bits to Windows permissions: let the Windows job write its probe files into the tree
sudo chmod 777 "$MNT" "$MNT/bench"
echo "[btrfs_image] volume after generation: $(df -h --output=used,size "$MNT" | tail -1)"
sudo umount "$MNT"
sudo losetup -d "$LOOP"
trap - EXIT

qemu-img convert -p -f raw -O vhdx -o subformat=dynamic,block_size=1M "$IMG" "$OUT_VHDX"
rm -f "$IMG"
echo "[btrfs_image] $OUT_VHDX: $(du -h "$OUT_VHDX" | cut -f1) on disk for a ${SIZE_GB} GiB volume"
