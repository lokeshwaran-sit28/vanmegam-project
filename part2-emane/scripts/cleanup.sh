#!/usr/bin/env bash
# cleanup.sh – Safely remove EMANE processes, network namespaces, and TAP interfaces
#
# Safe to run multiple times.

set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
    echo "[ERROR] Cleanup must be run as root (sudo)." >&2
    exit 1
fi

echo "[CLEANUP] Stopping running emane processes..."
pkill -f emane || true

echo "[CLEANUP] Removing node network namespaces node-1..node-16..."
for i in $(seq 1 16); do
    NS="node-${i}"
    IFACE="emane${i}"
    
    if ip netns list | grep -qw "$NS"; then
        ip netns delete "$NS" 2>/dev/null || true
        echo "  Deleted namespace $NS"
    fi

    if ip link show "$IFACE" >/dev/null 2>&1; then
        ip link delete "$IFACE" 2>/dev/null || true
        echo "  Deleted TAP interface $IFACE"
    fi
done

echo "[CLEANUP] Done."
