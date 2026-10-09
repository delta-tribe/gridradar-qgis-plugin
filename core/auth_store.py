"""Persist GridRadar session state in QSettings."""

from __future__ import annotations

from qgis.PyQt.QtCore import QSettings

DEFAULT_API_BASE = "https://api.gridradar.it"
LEGACY_API_BASE = "https://gridradar.it"
SETTINGS_GROUP = "gridradar_qgis_plugin"


class AuthStore:
    """Read/write plugin authentication settings."""

    def __init__(self) -> None:
        self._settings = QSettings()

    def api_base(self) -> str:
        value = self._settings.value(f"{SETTINGS_GROUP}/api_base", DEFAULT_API_BASE, type=str)
        if value.rstrip("/") == LEGACY_API_BASE:
            return DEFAULT_API_BASE
        return value.rstrip("/")

    def set_api_base(self, value: str) -> None:
        self._settings.setValue(f"{SETTINGS_GROUP}/api_base", value.rstrip("/"))

    def token(self) -> str | None:
        value = self._settings.value(f"{SETTINGS_GROUP}/token", "", type=str)
        return value or None

    def set_token(self, value: str | None) -> None:
        self._settings.setValue(f"{SETTINGS_GROUP}/token", value or "")

    def org_id(self) -> int | None:
        value = self._settings.value(f"{SETTINGS_GROUP}/org_id")
        if value in (None, ""):
            return None
        return int(value)

    def set_org_id(self, value: int | None) -> None:
        if value is None:
            self._settings.remove(f"{SETTINGS_GROUP}/org_id")
        else:
            self._settings.setValue(f"{SETTINGS_GROUP}/org_id", value)

    def org_name(self) -> str | None:
        value = self._settings.value(f"{SETTINGS_GROUP}/org_name", "", type=str)
        return value or None

    def set_org_name(self, value: str | None) -> None:
        if not value:
            self._settings.remove(f"{SETTINGS_GROUP}/org_name")
        else:
            self._settings.setValue(f"{SETTINGS_GROUP}/org_name", value)

    def identifier(self) -> str:
        return self._settings.value(f"{SETTINGS_GROUP}/identifier", "", type=str)

    def set_identifier(self, value: str) -> None:
        self._settings.setValue(f"{SETTINGS_GROUP}/identifier", value)

    def catalog_version(self) -> str | None:
        value = self._settings.value(f"{SETTINGS_GROUP}/catalog_version", "", type=str)
        return value or None

    def set_catalog_version(self, value: str | None) -> None:
        self._settings.setValue(f"{SETTINGS_GROUP}/catalog_version", value or "")

    def clear_session(self) -> None:
        self.set_token(None)
        self.set_org_id(None)
        self.set_org_name(None)
        self.set_catalog_version(None)
