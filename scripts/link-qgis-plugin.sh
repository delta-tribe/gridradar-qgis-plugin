#!/usr/bin/env bash
# Symlink this repo into the QGIS user plugins folder for local development.
# Re-run safely: replaces a symlink that already points elsewhere.
set -euo pipefail

PLUGIN_NAME="${PLUGIN_NAME:-gridradar_qgis_plugin}"
QGIS_PROFILE="${QGIS_PROFILE:-default}"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PLUGINS_DIR="${HOME}/.local/share/QGIS/QGIS3/profiles/${QGIS_PROFILE}/python/plugins"
LINK_PATH="${PLUGINS_DIR}/${PLUGIN_NAME}"

mkdir -p "${PLUGINS_DIR}"

if [[ -e "${LINK_PATH}" && ! -L "${LINK_PATH}" ]]; then
  echo "error: ${LINK_PATH} exists and is not a symlink — move it aside manually" >&2
  exit 1
fi

if [[ -L "${LINK_PATH}" ]]; then
  current="$(readlink -f "${LINK_PATH}")"
  target="$(readlink -f "${REPO_ROOT}")"
  if [[ "${current}" == "${target}" ]]; then
    echo "already linked: ${LINK_PATH} -> ${REPO_ROOT}"
    exit 0
  fi
  rm "${LINK_PATH}"
fi

ln -s "${REPO_ROOT}" "${LINK_PATH}"

echo "linked: ${LINK_PATH} -> ${REPO_ROOT}"
echo ""
echo "Next steps:"
echo "  1. Open QGIS (profile: ${QGIS_PROFILE})"
echo "  2. Plugin → Gestione e installazione plugin → installato"
echo "  3. Enable «GridRadar»"
echo ""
echo "After editing Python files, disable and re-enable the plugin (or install Plugin Reloader)."
echo "Changes to metadata.txt usually require restarting QGIS."
