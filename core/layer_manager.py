"""Synchronize catalog checkboxes with QgsProject layers."""

from __future__ import annotations

from typing import Any, Callable

from qgis.core import QgsMapLayer, QgsProject


class LayerManager:
    """Track plugin-added layers and keep UI state in sync."""

    def __init__(self, on_layer_removed: Callable[[str], None] | None = None) -> None:
        self._state: dict[str, tuple[bool, str]] = {}
        self._on_layer_removed = on_layer_removed
        QgsProject.instance().layerRemoved.connect(self._handle_layer_removed)

    def is_checked(self, layer_id: str) -> bool:
        return self._state.get(layer_id, (False, ""))[0]

    def qgis_layer_id(self, layer_id: str) -> str | None:
        value = self._state.get(layer_id)
        return value[1] if value else None

    def register(self, layer_id: str, qgis_layer: QgsMapLayer) -> None:
        self._state[layer_id] = (True, qgis_layer.id())

    def unregister(self, layer_id: str) -> str | None:
        entry = self._state.pop(layer_id, None)
        return entry[1] if entry else None

    def clear(self) -> list[str]:
        removed_ids = [qgis_id for _, qgis_id in self._state.values() if qgis_id]
        self._state.clear()
        return removed_ids

    def tracked_qgis_ids(self) -> set[str]:
        return {qgis_id for _, qgis_id in self._state.values() if qgis_id}

    def tracked_layer_ids(self) -> list[str]:
        return list(self._state.keys())

    def _handle_layer_removed(self, qgis_layer_id: str) -> None:
        for catalog_id, (checked, tracked_id) in list(self._state.items()):
            if tracked_id != qgis_layer_id:
                continue
            self._state[catalog_id] = (False, "")
            if self._on_layer_removed:
                self._on_layer_removed(catalog_id)
