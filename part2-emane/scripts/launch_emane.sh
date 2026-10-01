#!/usr/bin/env bash
# launch_emane.sh – Linux launcher script with Network Namespace isolation
#
# Usage:
#   sudo bash part2-emane/scripts/launch_emane.sh [num_nodes] [schedule_xml]
#   e.g.: sudo bash part2-emane/scripts/launch_emane.sh 16 part2-emane/configs/tdma-schedule.xml

set -euo pipefail

# 1. OS Check
if [ "$(uname -s)" != "Linux" ]; then
    echo "[ERROR] EMANE requires a Linux operating system with TUN/TAP & network namespace support." >&2
    exit 1
fi

# 2. Privileges Check
if [ "$(id -u)" -ne 0 ]; then
    echo "[ERROR] This script must be run as root (sudo)." >&2
    exit 1
fi

# 3. Required Commands Check
for cmd in ip emane emaneevent-tdmaschedule; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
        echo "[ERROR] Required utility '$cmd' not found in PATH." >&2
        exit 1
    fi
done

NUM_NODES="${1:-16}"
SCHEDULE_XML="${2:-part2-emane/configs/tdma-schedule.xml}"
LOG_DIR="/var/log/emane"
mkdir -p "$LOG_DIR"

echo "[EMANE] Starting ${NUM_NODES}-node TDMA emulation with Linux Network Namespace isolation"
echo "[EMANE] Schedule: ${SCHEDULE_XML}"

# 4. Create Network Namespaces and TAP Interfaces
for i in $(seq 1 "$NUM_NODES"); do
    NS="node-${i}"
    IFACE="emane${i}"

    # Clean existing namespace if present
    ip netns delete "$NS" 2>/dev/null || true

    # Create namespace
    ip netns add "$NS"

    # Create TAP interface in root namespace
    ip tuntap add dev "$IFACE" mode tap

    # Move TAP interface into node namespace (prevents host kernel routing bypass)
    ip link set "$IFACE" netns "$NS"

    # Configure IP address inside namespace
    ip netns exec "$NS" ip addr add "10.0.0.${i}/24" dev "$IFACE"
    ip netns exec "$NS" ip link set "$IFACE" up
    ip netns exec "$NS" ip link set lo up

    echo "  [NS] ${NS} -> Interface ${IFACE} (10.0.0.${i}/24) UP"
done

# 5. Enable Multicast on Loopback Interface for Event Service
ip link set dev lo multicast on || true

# 6. Launch EMANE Daemon
echo "[EMANE] Launching EMANE daemon..."
emane part2-emane/configs/platform.xml \
    --realtime \
    --logfile "${LOG_DIR}/emane.log" \
    --loglevel 3 \
    --daemonize

# 7. Inject TDMA Schedule Event
echo "[EMANE] Injecting TDMA Schedule XML..."
emaneevent-tdmaschedule "$SCHEDULE_XML" -i lo

echo "[EMANE] Simulation successfully started."
echo "[EMANE] Use 'emanesh localhost get table 1 mac scheduler.ScheduleInfoTable' to verify schedule."
