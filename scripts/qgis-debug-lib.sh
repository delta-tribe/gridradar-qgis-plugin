#!/usr/bin/env bash
# Shared helpers for launching QGIS with debugpy (via plugin __init__.py).
set -euo pipefail

qgis_debug_env() {
  export GRIDRADAR_DEBUGPY=1
  export GRIDRADAR_DEBUGPY_HOST="${GRIDRADAR_DEBUGPY_HOST:-127.0.0.1}"
  export GRIDRADAR_DEBUGPY_PORT="${GRIDRADAR_DEBUGPY_PORT:-5678}"
  export PYDEVD_DISABLE_FILE_VALIDATION=1
}

qgis_debug_port_open() {
  local host="${GRIDRADAR_DEBUGPY_HOST:-127.0.0.1}"
  local port="${GRIDRADAR_DEBUGPY_PORT:-5678}"
  (echo >/dev/tcp/"${host}"/"${port}") 2>/dev/null
}

qgis_debug_preflight() {
  if ! /usr/bin/python3 -c "import debugpy" 2>/dev/null; then
    echo "ERROR: debugpy not installed — run: ./scripts/install-qgis-debug.sh" >&2
    return 1
  fi
}
