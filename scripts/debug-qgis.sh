#!/usr/bin/env bash
# Launch QGIS with debugpy enabled (GridRadar plugin calls debugpy.listen on load).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=qgis-debug-lib.sh
source "${SCRIPT_DIR}/qgis-debug-lib.sh"

qgis_debug_env
qgis_debug_preflight

echo "Starting QGIS (debug port=${GRIDRADAR_DEBUGPY_PORT})"
echo "In Cursor: Run and Debug → «QGIS: Attach»"
exec qgis "$@"
