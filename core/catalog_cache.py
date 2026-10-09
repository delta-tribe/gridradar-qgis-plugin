"""Local catalog metadata cache."""

from __future__ import annotations

import json
from typing import Any

from qgis.PyQt.QtCore import QSettings

SETTINGS_GROUP = "gridradar_qgis_plugin"


class CatalogCache:
    """Cache catalog tree JSON keyed by version."""

    def __init__(self) -> None:
        self._settings = QSettings()

    def load(self, version: str) -> dict[str, Any] | None:
        cached_version = self._settings.value(f"{SETTINGS_GROUP}/catalog_cache_version", "", type=str)
        if cached_version != version:
            return None
        raw = self._settings.value(f"{SETTINGS_GROUP}/catalog_cache_payload", "", type=str)
        if not raw:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return None

    def save(self, version: str, payload: dict[str, Any]) -> None:
        self._settings.setValue(f"{SETTINGS_GROUP}/catalog_cache_version", version)
        self._settings.setValue(f"{SETTINGS_GROUP}/catalog_cache_payload", json.dumps(payload))

    def clear(self) -> None:
        self._settings.remove(f"{SETTINGS_GROUP}/catalog_cache_version")
        self._settings.remove(f"{SETTINGS_GROUP}/catalog_cache_payload")
