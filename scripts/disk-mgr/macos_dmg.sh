#!/usr/bin/env bash
set -euo pipefail

# macOS APFS SparseImage Manager & Cold-Cache Evictor for disk-scanner-bench
# Usage:
#   ./macos_dmg.sh create <size_gb> <mount_path>
#   ./macos_dmg.sh purge-cache <mount_path>
#   ./macos_dmg.sh teardown <mount_path>

CMD="${1:-}"
if [[ -z "$CMD" ]]; then
    echo "Usage: $0 {create|purge-cache|teardown} ..." >&2
    exit 1
fi
shift

SPARSE_IMG="/tmp/bench.sparseimage"

case "$CMD" in
    create)
        SIZE_GB="${1:-60}"
        MOUNT_PATH="${2:-/tmp/BenchVol}"
        echo "[macos_dmg] Creating ${SIZE_GB}g APFS sparseimage at ${SPARSE_IMG}..."

        if [[ -d "$MOUNT_PATH" ]]; then
            hdiutil detach "$MOUNT_PATH" -force 2>/dev/null || sudo hdiutil detach "$MOUNT_PATH" -force 2>/dev/null || true
        fi
        rm -f "$SPARSE_IMG"

        hdiutil create -size "${SIZE_GB}g" -type SPARSE -fs APFS -volname BenchVol -ov "$SPARSE_IMG" >/dev/null
        mkdir -p "$MOUNT_PATH"
        hdiutil attach "$SPARSE_IMG" -mountpoint "$MOUNT_PATH" -nobrowse >/dev/null || \
            sudo hdiutil attach "$SPARSE_IMG" -mountpoint "$MOUNT_PATH" -nobrowse >/dev/null
        chmod 777 "$MOUNT_PATH" 2>/dev/null || sudo chmod 777 "$MOUNT_PATH" || true
        # Disable Spotlight indexing and FSEvents logging on the synthetic benchmark volume
        touch "$MOUNT_PATH/.metadata_never_index" 2>/dev/null || true
        mkdir -p "$MOUNT_PATH/.fseventsd" 2>/dev/null || true
        touch "$MOUNT_PATH/.fseventsd/no_log" 2>/dev/null || true
        mdutil -i off "$MOUNT_PATH" >/dev/null 2>&1 || sudo mdutil -i off "$MOUNT_PATH" >/dev/null 2>&1 || true
        echo "[macos_dmg] Mounted ${SPARSE_IMG} at ${MOUNT_PATH} (Spotlight & FSEvents disabled)"
        ;;

    purge-cache)
        MOUNT_PATH="${1:-/tmp/BenchVol}"
        echo "[macos_dmg] Evicting macOS unified buffer cache (hdiutil detach + sudo purge + attach)..."
        sync
        hdiutil detach "$MOUNT_PATH" -force >/dev/null 2>&1 || sudo hdiutil detach "$MOUNT_PATH" -force >/dev/null
        sudo purge || true
        mkdir -p "$MOUNT_PATH"
        hdiutil attach "$SPARSE_IMG" -mountpoint "$MOUNT_PATH" -nobrowse >/dev/null || \
            sudo hdiutil attach "$SPARSE_IMG" -mountpoint "$MOUNT_PATH" -nobrowse >/dev/null
        mdutil -i off "$MOUNT_PATH" >/dev/null 2>&1 || sudo mdutil -i off "$MOUNT_PATH" >/dev/null 2>&1 || true
        echo "[macos_dmg] Cold cache state restored for ${MOUNT_PATH}"
        ;;

    teardown)
        MOUNT_PATH="${1:-/tmp/BenchVol}"
        echo "[macos_dmg] Tearing down ${MOUNT_PATH} and removing ${SPARSE_IMG}..."
        hdiutil detach "$MOUNT_PATH" -force 2>/dev/null || sudo hdiutil detach "$MOUNT_PATH" -force 2>/dev/null || true
        rm -f "$SPARSE_IMG"
        echo "[macos_dmg] Teardown complete."
        ;;

    *)
        echo "Unknown command: $CMD. Expected create, purge-cache, or teardown." >&2
        exit 1
        ;;
esac
