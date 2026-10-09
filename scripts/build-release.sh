#!/usr/bin/env bash
# Build a protected release ZIP (obfuscated .py source, portable).
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
QGIS_PYTHON="${QGIS_PYTHON:-}"

args=()
if [[ -n "${QGIS_PYTHON}" ]]; then
  args+=(--python "${QGIS_PYTHON}")
fi

exec python3 "${REPO_ROOT}/scripts/build_release.py" "${args[@]}" "$@"
