#!/usr/bin/env bash
# VS Code/Cursor preLaunchTask: start QGIS, wait until plugin opens debugpy, exit.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=qgis-debug-lib.sh
source "${SCRIPT_DIR}/qgis-debug-lib.sh"

QGIS_PROFILE="${QGIS_PROFILE:-default}"
HOST="${GRIDRADAR_DEBUGPY_HOST:-127.0.0.1}"
PORT="${GRIDRADAR_DEBUGPY_PORT:-5678}"
LOG_FILE="${TMPDIR:-/tmp}/gridradar-qgis-debug.log"
PID_FILE="${TMPDIR:-/tmp}/gridradar-qgis-debug.pid"

qgis_debug_env
qgis_debug_preflight

if qgis_debug_port_open; then
  echo "Stopping stale listener on ${HOST}:${PORT}"
  fuser -k "${PORT}/tcp" 2>/dev/null || true
  sleep 1
fi

if [[ -f "${PID_FILE}" ]]; then
  old_pid="$(cat "${PID_FILE}")"
  if kill -0 "${old_pid}" 2>/dev/null; then
    echo "Stopping previous debug QGIS (pid ${old_pid})"
    kill "${old_pid}" 2>/dev/null || true
    sleep 1
  fi
fi

echo "Starting QGIS (profile=${QGIS_PROFILE}, debug port=${PORT})"
echo "QGIS log: ${LOG_FILE}"

nohup qgis "$@" >>"${LOG_FILE}" 2>&1 &
QGIS_PID=$!
echo "${QGIS_PID}" >"${PID_FILE}"

for _ in $(seq 1 240); do
  if ! kill -0 "${QGIS_PID}" 2>/dev/null; then
    echo "ERROR: QGIS exited before debugpy started — see ${LOG_FILE}" >&2
    tail -40 "${LOG_FILE}" >&2 || true
    exit 1
  fi
  if qgis_debug_port_open; then
    echo "QGIS debug ready on ${HOST}:${PORT} (pid ${QGIS_PID})"
    exit 0
  fi
  sleep 0.5
done

echo "ERROR: debugpy did not open port ${PORT} within 120s — see ${LOG_FILE}" >&2
tail -40 "${LOG_FILE}" >&2 || true
kill "${QGIS_PID}" 2>/dev/null || true
exit 1
