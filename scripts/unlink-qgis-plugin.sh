#!/usr/bin/env bash
# Remove the development symlink from the QGIS user plugins folder.
set -euo pipefail

PLUGIN_NAME="${PLUGIN_NAME:-gridradar_qgis_plugin}"
QGIS_PROFILE="${QGIS_PROFILE:-default}"

PLUGINS_DIR="${HOME}/.local/share/QGIS/QGIS3/profiles/${QGIS_PROFILE}/python/plugins"
LINK_PATH="${PLUGINS_DIR}/${PLUGIN_NAME}"

if [[ -L "${LINK_PATH}" ]]; then
  rm "${LINK_PATH}"
  echo "removed symlink: ${LINK_PATH}"
elif [[ -e "${LINK_PATH}" ]]; then
  echo "error: ${LINK_PATH} is not a symlink — not removing" >&2
  exit 1
else
  echo "nothing to remove: ${LINK_PATH}"
fi
