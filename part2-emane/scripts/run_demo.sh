#!/usr/bin/env bash
# run_demo.sh – Linux bash runner for Part 2 EMANE TDMA Integration Demo
#
# Steps:
#   1. Generates Part 1 TDMA schedule
#   2. Runs Schedule Adapter to convert schedule to EMANE XML
#   3. Validates configuration
#   4. Checks for EMANE binary and attempts event injection if available
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "Running TDMA Schedule Optimizer & EMANE Integration Demo..."
python3 "${SCRIPT_DIR}/run_demo.py" --file "${PROJECT_ROOT}/examples/nodes16.json"

if command -v emaneevent-tdmaschedule >/dev/null 2>&1; then
    echo "[EMANE] Injecting TDMA schedule XML into EMANE Event Service..."
    emaneevent-tdmaschedule "${PROJECT_ROOT}/part2-emane/configs/tdma-schedule.xml" -i lo
    echo "[EMANE] Schedule injected successfully!"
else
    echo "[EMANE] emaneevent-tdmaschedule not found in PATH. Skipping live event injection."
fi
