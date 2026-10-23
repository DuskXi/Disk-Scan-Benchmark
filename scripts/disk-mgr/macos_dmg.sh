#!/usr/bin/env bash
set -euo pipefail

# macOS Native APFS Workspace & Cold-Cache Evictor for disk-scanner-bench
# Note: On macOS 15 Sequoia virtualized runners (especially macos-15-intel),
# hdiutil .sparseimage routes all I/O through user-space diskimagesiod with severe
# IPC latency (~87 files/s) and DiskArbitration detach timeouts.
# Using a dedicated workspace directory on the runner's native APFS container
# with XNU kernel `purge` delivers true native APFS performance and reliable cold-cache eviction.
#
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

case "$CMD" in
    create)
        SIZE_GB="${1:-60}"
        MOUNT_PATH="${2:-/tmp/BenchVol}"
        echo "[macos_dmg] Preparing native APFS benchmark workspace at ${MOUNT_PATH} (logical cap: ${SIZE_GB}g)..."

        # Clean up any legacy hdiutil mount or previous directory
        if [[ -d "$MOUNT_PATH" ]]; then
            hdiutil detach "$MOUNT_PATH" -force >/dev/null 2>&1 || sudo hdiutil detach "$MOUNT_PATH" -force >/dev/null 2>&1 || true
            rm -rf "$MOUNT_PATH"
        fi
        rm -f /tmp/bench.sparseimage

        mkdir -p "$MOUNT_PATH"
        chmod 777 "$MOUNT_PATH" 2>/dev/null || sudo chmod 777 "$MOUNT_PATH" || true

        # Prevent Spotlight from indexing /private/tmp without polluting files inside $MOUNT_PATH
        PARENT_DIR="$(dirname "$MOUNT_PATH")"
        touch "${PARENT_DIR}/.metadata_never_index" 2>/dev/null || sudo touch "${PARENT_DIR}/.metadata_never_index" 2>/dev/null || true
        sudo mdutil -i off / >/dev/null 2>&1 || true

        echo "[macos_dmg] Native APFS workspace ready at ${MOUNT_PATH} (Spotlight indexing disabled)"
        ;;

    purge-cache)
        MOUNT_PATH="${1:-/tmp/BenchVol}"
        echo "[macos_dmg] Evicting XNU APFS vnode & unified buffer cache via sync + sudo purge..."
        sync
        sudo purge 2>/dev/null || purge 2>/dev/null || true
        echo "[macos_dmg] Cold cache state restored for ${MOUNT_PATH}"
        ;;

    teardown)
        MOUNT_PATH="${1:-/tmp/BenchVol}"
        echo "[macos_dmg] Removing APFS benchmark workspace at ${MOUNT_PATH}..."
        hdiutil detach "$MOUNT_PATH" -force >/dev/null 2>&1 || sudo hdiutil detach "$MOUNT_PATH" -force >/dev/null 2>&1 || true
        rm -rf "$MOUNT_PATH" /tmp/bench.sparseimage
        echo "[macos_dmg] Teardown complete."
        ;;

    *)
        echo "Unknown command: $CMD. Expected create, purge-cache, or teardown." >&2
        exit 1
        ;;
esac
