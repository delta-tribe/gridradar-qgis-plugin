# -*- coding: utf-8 -*-
"""Catalog browser dock widget."""

from __future__ import annotations

import os
from typing import Any, Callable

from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.PyQt.QtGui import QFont, QIcon, QPixmap
from qgis.PyQt.QtWidgets import (
    QDockWidget,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTabWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..core.sinfi.enabled_layers import SINFI_CATEGORY_LABELS

_PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_ICON_PATH = os.path.join(_PLUGIN_DIR, "icon.png")


def _item_key(item: QTreeWidgetItem) -> tuple[Any, ...]:
    """Identify an item across repopulation: catalog id when present, else its label."""
    payload = item.data(0, Qt.UserRole) or {}
    if payload.get("kind") and payload.get("id") is not None:
        return (payload["kind"], payload["id"])
    return ("label", item.text(0))


def _iter_items(tree: QTreeWidget):
    """Yield (path, item) for every item, path being the keys from the root."""
    stack = [((), tree.topLevelItem(i)) for i in reversed(range(tree.topLevelItemCount()))]
    while stack:
        parent_path, item = stack.pop()
        path = parent_path + (_item_key(item),)
        yield path, item
        stack.extend((path, item.child(i)) for i in reversed(range(item.childCount())))


def _expanded_keys(tree: QTreeWidget) -> set[tuple[tuple[Any, ...], ...]]:
    return {path for path, item in _iter_items(tree) if item.isExpanded()}


def _restore_expanded(tree: QTreeWidget, expanded: set[tuple[tuple[Any, ...], ...]]) -> None:
    """Groups start collapsed; reopen only those the user had open before a refresh."""
    for path, item in _iter_items(tree):
        if path in expanded:
            item.setExpanded(True)


class CatalogDockWidget(QDockWidget):
    """Browse catalog sources and toggle layers."""

    layer_toggled = pyqtSignal(str, bool)
    trace_toggled = pyqtSignal(int, bool)
    collection_toggled = pyqtSignal(int, bool)
    layer_selection_toggled = pyqtSignal(int, bool)
    selection_layer_toggled = pyqtSignal(int, str, bool)
    sinfi_connect_requested = pyqtSignal()
    refresh_requested = pyqtSignal()
    draw_refresh_requested = pyqtSignal()
    layer_selections_refresh_requested = pyqtSignal()
    logout_requested = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__("GridRadar", parent)
        self.setObjectName("GridRadarCatalogDock")
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)

        if os.path.exists(_ICON_PATH):
            self.setWindowIcon(QIcon(_ICON_PATH))

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(8)

        brand = QHBoxLayout()
        brand.setSpacing(8)
        if os.path.exists(_ICON_PATH):
            logo = QLabel()
            logo.setPixmap(
                QPixmap(_ICON_PATH).scaled(
                    28,
                    28,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation,
                )
            )
            logo.setFixedSize(32, 32)
            logo.setAlignment(Qt.AlignCenter)
            brand.addWidget(logo)
        title = QLabel("GridRadar")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(11)
        title.setFont(title_font)
        brand.addWidget(title)
        brand.addStretch()

        header = QHBoxLayout()
        self.user_label = QLabel("")
        self.logout_button = QPushButton("Esci")
        header.addWidget(self.user_label, stretch=1)
        header.addWidget(self.logout_button)

        self.tabs = QTabWidget()

        catalog_tab = QWidget()
        catalog_layout = QVBoxLayout(catalog_tab)
        catalog_layout.setContentsMargins(0, 0, 0, 0)
        catalog_layout.setSpacing(8)

        catalog_header = QHBoxLayout()
        self.refresh_button = QPushButton("Aggiorna catalogo")
        self.sinfi_button = QPushButton("Collega SINFI")
        catalog_header.addWidget(self.refresh_button)
        catalog_header.addWidget(self.sinfi_button)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Cerca layer…")

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Layer", "Tipo"])
        self.tree.setColumnWidth(0, 280)

        catalog_layout.addLayout(catalog_header)
        catalog_layout.addWidget(self.search_edit)
        catalog_layout.addWidget(self.tree)

        selections_tab = QWidget()
        selections_layout = QVBoxLayout(selections_tab)
        selections_layout.setContentsMargins(0, 0, 0, 0)
        selections_layout.setSpacing(8)

        selections_header = QHBoxLayout()
        self.selections_refresh_button = QPushButton("Aggiorna selezioni")
        selections_header.addWidget(self.selections_refresh_button)
        selections_header.addStretch()

        self.selections_search_edit = QLineEdit()
        self.selections_search_edit.setPlaceholderText("Cerca selezione…")

        self.selections_tree = QTreeWidget()
        self.selections_tree.setHeaderLabels(["Selezione", "Layer"])
        self.selections_tree.setColumnWidth(0, 280)

        selections_layout.addLayout(selections_header)
        selections_layout.addWidget(self.selections_search_edit)
        selections_layout.addWidget(self.selections_tree)

        draw_tab = QWidget()
        draw_layout = QVBoxLayout(draw_tab)
        draw_layout.setContentsMargins(0, 0, 0, 0)
        draw_layout.setSpacing(8)

        draw_header = QHBoxLayout()
        self.draw_refresh_button = QPushButton("Aggiorna disegni")
        draw_header.addWidget(self.draw_refresh_button)
        draw_header.addStretch()

        self.draw_search_edit = QLineEdit()
        self.draw_search_edit.setPlaceholderText("Cerca disegno…")

        self.draw_tree = QTreeWidget()
        self.draw_tree.setHeaderLabels(["Disegno", "Tipo"])
        self.draw_tree.setColumnWidth(0, 280)

        draw_layout.addLayout(draw_header)
        draw_layout.addWidget(self.draw_search_edit)
        draw_layout.addWidget(self.draw_tree)

        self.tabs.addTab(catalog_tab, "Catalogo")
        self.tabs.addTab(selections_tab, "Selezioni")
        self.tabs.addTab(draw_tab, "Disegni")

        layout.addLayout(brand)
        layout.addLayout(header)
        layout.addWidget(self.tabs)

        self.setWidget(container)

        self.refresh_button.clicked.connect(self.refresh_requested.emit)
        self.sinfi_button.clicked.connect(self.sinfi_connect_requested.emit)
        self.selections_refresh_button.clicked.connect(self.layer_selections_refresh_requested.emit)
        self.draw_refresh_button.clicked.connect(self.draw_refresh_requested.emit)
        self.logout_button.clicked.connect(self.logout_requested.emit)
        self.search_edit.textChanged.connect(self._apply_filter)
        self.selections_search_edit.textChanged.connect(self._apply_selections_filter)
        self.draw_search_edit.textChanged.connect(self._apply_draw_filter)
        self.tree.itemChanged.connect(self._handle_item_changed)
        self.selections_tree.itemChanged.connect(self._handle_selection_item_changed)
        self.draw_tree.itemChanged.connect(self._handle_draw_item_changed)

        self._suppress_item_changed = False
        self._suppress_draw_item_changed = False
        self._suppress_selection_item_changed = False
        self._layer_items: dict[str, QTreeWidgetItem] = {}
        self._trace_items: dict[int, QTreeWidgetItem] = {}
        self._collection_items: dict[int, QTreeWidgetItem] = {}
        self._collection_trace_ids: dict[int, list[int]] = {}
        self._layer_selection_items: dict[int, QTreeWidgetItem] = {}
        self._layer_selection_layer_ids: dict[int, list[str]] = {}
        self._selection_layer_items: dict[tuple[int, str], QTreeWidgetItem] = {}

    def set_user_label(self, text: str) -> None:
        self.user_label.setText(text)

    def populate_catalog(self, catalog: dict[str, Any]) -> None:
        self._suppress_item_changed = True
        expanded = _expanded_keys(self.tree)
        self.tree.clear()
        self._layer_items.clear()

        for source in catalog.get("sources", []):
            source_item = QTreeWidgetItem([source.get("name", source.get("id", "")), ""])
            source_item.setData(0, Qt.UserRole, {"kind": "source", "id": source.get("id")})
            source_item.setFlags(source_item.flags() & ~Qt.ItemIsUserCheckable)

            if source.get("integration_type") == "sinfi":
                hint = QTreeWidgetItem(["Collega SINFI per abilitare i layer", "sinfi"])
                hint.setFlags(hint.flags() & ~Qt.ItemIsUserCheckable)
                source_item.addChild(hint)
                self.tree.addTopLevelItem(source_item)
                continue

            for subgroup in source.get("subgroups") or []:
                subgroup_item = QTreeWidgetItem([subgroup.get("name", ""), ""])
                subgroup_item.setFlags(subgroup_item.flags() & ~Qt.ItemIsUserCheckable)
                for layer in subgroup.get("layers") or []:
                    subgroup_item.addChild(self._make_layer_item(layer))
                source_item.addChild(subgroup_item)

            for layer in source.get("layers") or []:
                source_item.addChild(self._make_layer_item(layer))

            self.tree.addTopLevelItem(source_item)

        _restore_expanded(self.tree, expanded)
        self._suppress_item_changed = False

    def populate_sinfi_layers(self, grouped_layers: dict[str, list[dict[str, Any]]]) -> None:
        sinfi_root = None
        for index in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(index)
            if item.data(0, Qt.UserRole) and item.data(0, Qt.UserRole).get("id") == "sinfi":
                sinfi_root = item
                break
        if sinfi_root is None:
            return

        expanded = _expanded_keys(self.tree)
        while sinfi_root.childCount():
            sinfi_root.removeChild(sinfi_root.child(0))

        self._suppress_item_changed = True
        for category, layers in grouped_layers.items():
            if not layers:
                continue
            subgroup_item = QTreeWidgetItem([SINFI_CATEGORY_LABELS.get(category, category), "sinfi"])
            subgroup_item.setFlags(subgroup_item.flags() & ~Qt.ItemIsUserCheckable)
            for layer in layers:
                payload = {
                    "id": layer["id"],
                    "name": layer["name"],
                    "type": "sinfi-wms",
                    "sinfi": True,
                }
                item = self._make_layer_item(payload)
                subgroup_item.addChild(item)
            sinfi_root.addChild(subgroup_item)
        _restore_expanded(self.tree, expanded)
        self._suppress_item_changed = False

    def set_layer_checked(self, layer_id: str, checked: bool) -> None:
        item = self._layer_items.get(layer_id)
        if item is None:
            return
        self._suppress_item_changed = True
        item.setCheckState(0, Qt.Checked if checked else Qt.Unchecked)
        self._suppress_item_changed = False

    def set_trace_checked(self, trace_id: int, checked: bool) -> None:
        item = self._trace_items.get(trace_id)
        if item is None:
            return
        self._suppress_draw_item_changed = True
        item.setCheckState(0, Qt.Checked if checked else Qt.Unchecked)
        self._suppress_draw_item_changed = False

    def set_collection_checked(self, collection_id: int, checked: bool) -> None:
        item = self._collection_items.get(collection_id)
        if item is None:
            return
        self._suppress_draw_item_changed = True
        item.setCheckState(0, Qt.Checked if checked else Qt.Unchecked)
        self._suppress_draw_item_changed = False

    def sync_collection_check_state(self, collection_id: int) -> None:
        item = self._collection_items.get(collection_id)
        trace_ids = self._collection_trace_ids.get(collection_id, [])
        if item is None:
            return
        self._suppress_draw_item_changed = True
        if not trace_ids:
            item.setCheckState(0, Qt.Unchecked)
        else:
            checked_count = sum(
                1
                for trace_id in trace_ids
                if self._trace_items.get(trace_id)
                and self._trace_items[trace_id].checkState(0) == Qt.Checked
            )
            if checked_count == 0:
                item.setCheckState(0, Qt.Unchecked)
            elif checked_count == len(trace_ids):
                item.setCheckState(0, Qt.Checked)
            else:
                item.setCheckState(0, Qt.PartiallyChecked)
        self._suppress_draw_item_changed = False

    def populate_draw_workspace(self, workspace: dict[str, Any]) -> None:
        """Populate the Disegni tab from a draw workspace API response."""
        self._suppress_draw_item_changed = True
        expanded = _expanded_keys(self.draw_tree)
        self.draw_tree.clear()
        self._trace_items.clear()
        self._collection_items.clear()
        self._collection_trace_ids.clear()

        traces_by_collection: dict[int, list[dict[str, Any]]] = {}
        for trace in workspace.get("traces") or []:
            collection_id = trace.get("collection_id")
            if collection_id is None:
                continue
            traces_by_collection.setdefault(int(collection_id), []).append(trace)

        sections = [
            ("Personali", workspace.get("personal") or []),
            ("Organizzazione", workspace.get("organization") or []),
        ]
        for section_label, collections in sections:
            if not collections:
                continue
            section_item = QTreeWidgetItem([section_label, ""])
            section_item.setFlags(section_item.flags() & ~Qt.ItemIsUserCheckable)
            for collection in collections:
                collection_id = int(collection["id"])
                collection_traces = traces_by_collection.get(collection_id, [])
                collection_item = QTreeWidgetItem(
                    [collection.get("name", f"Raccolta {collection_id}"), ""]
                )
                collection_item.setData(
                    0,
                    Qt.UserRole,
                    {"kind": "collection", "id": collection_id},
                )
                collection_item.setFlags(
                    collection_item.flags()
                    | Qt.ItemIsUserCheckable
                    | Qt.ItemIsEnabled
                    | Qt.ItemIsTristate
                )
                collection_item.setCheckState(0, Qt.Unchecked)
                self._collection_items[collection_id] = collection_item
                self._collection_trace_ids[collection_id] = []
                for trace in collection_traces:
                    trace_id = int(trace["id"])
                    collection_item.addChild(self._make_trace_item(trace))
                    self._collection_trace_ids[collection_id].append(trace_id)
                section_item.addChild(collection_item)
            self.draw_tree.addTopLevelItem(section_item)

        _restore_expanded(self.draw_tree, expanded)
        self._suppress_draw_item_changed = False

    def set_selection_layer_checked(self, layer_id: str, checked: bool) -> None:
        self.set_layer_checked(layer_id, checked)
        self._suppress_selection_item_changed = True
        for (sel_id, lid), item in self._selection_layer_items.items():
            if lid == layer_id:
                item.setCheckState(0, Qt.Checked if checked else Qt.Unchecked)
        self._suppress_selection_item_changed = False

    def set_layer_selection_checked(self, selection_id: int, checked: bool) -> None:
        item = self._layer_selection_items.get(selection_id)
        if item is None:
            return
        self._suppress_selection_item_changed = True
        item.setCheckState(0, Qt.Checked if checked else Qt.Unchecked)
        self._suppress_selection_item_changed = False

    def sync_layer_selection_check_state(self, selection_id: int) -> None:
        item = self._layer_selection_items.get(selection_id)
        layer_ids = self._layer_selection_layer_ids.get(selection_id, [])
        if item is None:
            return
        self._suppress_selection_item_changed = True
        if not layer_ids:
            item.setCheckState(0, Qt.Unchecked)
        else:
            checked_count = sum(
                1
                for layer_id in layer_ids
                if (selection_id, layer_id) in self._selection_layer_items
                and self._selection_layer_items[(selection_id, layer_id)].checkState(0) == Qt.Checked
            )
            if checked_count == 0:
                item.setCheckState(0, Qt.Unchecked)
            elif checked_count == len(layer_ids):
                item.setCheckState(0, Qt.Checked)
            else:
                item.setCheckState(0, Qt.PartiallyChecked)
        self._suppress_selection_item_changed = False

    def populate_layer_selections(self, payload: dict[str, Any]) -> None:
        """Populate the Selezioni tab from a layer-selections API response."""
        self._suppress_selection_item_changed = True
        expanded = _expanded_keys(self.selections_tree)
        self.selections_tree.clear()
        self._layer_selection_items.clear()
        self._layer_selection_layer_ids.clear()
        self._selection_layer_items.clear()

        sections = [
            ("Personali", payload.get("personal") or []),
            ("Organizzazione", payload.get("organization") or []),
        ]
        for section_label, selections in sections:
            if not selections:
                continue
            section_item = QTreeWidgetItem([section_label, ""])
            section_item.setFlags(section_item.flags() & ~Qt.ItemIsUserCheckable)
            for selection in selections:
                selection_id = int(selection["id"])
                layer_ids = [str(layer_id) for layer_id in selection.get("layer_ids") or []]
                layer_count = len(layer_ids)
                count_label = f"{layer_count} layer" if layer_count != 1 else "1 layer"
                selection_item = QTreeWidgetItem(
                    [selection.get("name", f"Selezione {selection_id}"), count_label]
                )
                selection_item.setData(
                    0,
                    Qt.UserRole,
                    {"kind": "layer_selection", "id": selection_id},
                )
                selection_item.setFlags(
                    selection_item.flags()
                    | Qt.ItemIsUserCheckable
                    | Qt.ItemIsEnabled
                    | Qt.ItemIsTristate
                )
                selection_item.setCheckState(0, Qt.Unchecked)
                self._layer_selection_items[selection_id] = selection_item
                self._layer_selection_layer_ids[selection_id] = layer_ids
                for layer_id in layer_ids:
                    selection_item.addChild(self._make_selection_layer_item(selection_id, layer_id))
                section_item.addChild(selection_item)
            self.selections_tree.addTopLevelItem(section_item)

        _restore_expanded(self.selections_tree, expanded)
        self._suppress_selection_item_changed = False

    def _make_selection_layer_item(self, selection_id: int, layer_id: str) -> QTreeWidgetItem:
        catalog_item = self._layer_items.get(layer_id)
        name = catalog_item.text(0) if catalog_item else layer_id
        layer_type = catalog_item.text(1) if catalog_item else ""
        item = QTreeWidgetItem([name, layer_type])
        item.setData(
            0,
            Qt.UserRole,
            {
                "kind": "selection_layer",
                "selection_id": selection_id,
                "layer_id": layer_id,
            },
        )
        item.setFlags(item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
        item.setCheckState(0, Qt.Unchecked)
        self._selection_layer_items[(selection_id, layer_id)] = item
        return item

    def _handle_selection_item_changed(self, item: QTreeWidgetItem, column: int) -> None:
        if self._suppress_selection_item_changed or column != 0:
            return
        payload = item.data(0, Qt.UserRole) or {}
        kind = payload.get("kind")
        if kind == "layer_selection":
            state = item.checkState(0)
            if state == Qt.PartiallyChecked:
                return
            selection_id = int(payload.get("id"))
            self.layer_selection_toggled.emit(selection_id, state == Qt.Checked)
            return
        if kind != "selection_layer":
            return
        selection_id = int(payload.get("selection_id"))
        layer_id = str(payload.get("layer_id"))
        checked = item.checkState(0) == Qt.Checked
        self.selection_layer_toggled.emit(selection_id, layer_id, checked)

    def _apply_selections_filter(self, text: str) -> None:
        needle = text.strip().lower()

        def visit(item: QTreeWidgetItem) -> bool:
            payload = item.data(0, Qt.UserRole) or {}
            visible = False
            if payload.get("kind") in {"layer_selection", "selection_layer"}:
                visible = not needle or needle in item.text(0).lower()
            child_visible = False
            for index in range(item.childCount()):
                if visit(item.child(index)):
                    child_visible = True
            item.setHidden(
                not visible
                and not child_visible
                and payload.get("kind") in {"layer_selection", "selection_layer"}
            )
            if needle and child_visible:
                item.setExpanded(True)
            return visible or child_visible

        for index in range(self.selections_tree.topLevelItemCount()):
            visit(self.selections_tree.topLevelItem(index))

    def _make_trace_item(self, trace: dict[str, Any]) -> QTreeWidgetItem:
        kind = str(trace.get("kind") or "")
        item = QTreeWidgetItem([trace.get("name", f"Traccia {trace.get('id')}"), kind])
        item.setData(
            0,
            Qt.UserRole,
            {"kind": "trace", "id": int(trace["id"]), "collection_id": int(trace["collection_id"])},
        )
        item.setFlags(item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
        visible = bool(trace.get("visible", True))
        item.setCheckState(0, Qt.Checked if visible else Qt.Unchecked)
        self._trace_items[int(trace["id"])] = item
        return item

    def _make_layer_item(self, layer: dict[str, Any]) -> QTreeWidgetItem:
        item = QTreeWidgetItem([layer.get("name", layer.get("id", "")), layer.get("type", "")])
        item.setData(0, Qt.UserRole, {"kind": "layer", "id": layer.get("id"), "sinfi": layer.get("sinfi", False)})
        item.setFlags(item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
        item.setCheckState(0, Qt.Unchecked)
        self._layer_items[str(layer.get("id"))] = item
        return item

    def _handle_item_changed(self, item: QTreeWidgetItem, column: int) -> None:
        if self._suppress_item_changed or column != 0:
            return
        payload = item.data(0, Qt.UserRole) or {}
        if payload.get("kind") != "layer":
            return
        layer_id = str(payload.get("id"))
        checked = item.checkState(0) == Qt.Checked
        self.layer_toggled.emit(layer_id, checked)

    def _handle_draw_item_changed(self, item: QTreeWidgetItem, column: int) -> None:
        if self._suppress_draw_item_changed or column != 0:
            return
        payload = item.data(0, Qt.UserRole) or {}
        kind = payload.get("kind")
        if kind == "collection":
            state = item.checkState(0)
            if state == Qt.PartiallyChecked:
                return
            collection_id = int(payload.get("id"))
            self.collection_toggled.emit(collection_id, state == Qt.Checked)
            return
        if kind != "trace":
            return
        trace_id = int(payload.get("id"))
        checked = item.checkState(0) == Qt.Checked
        self.trace_toggled.emit(trace_id, checked)

    def _apply_filter(self, text: str) -> None:
        needle = text.strip().lower()

        def visit(item: QTreeWidgetItem) -> bool:
            payload = item.data(0, Qt.UserRole) or {}
            visible = False
            if payload.get("kind") == "layer":
                visible = not needle or needle in item.text(0).lower()
            child_visible = False
            for index in range(item.childCount()):
                if visit(item.child(index)):
                    child_visible = True
            item.setHidden(not visible and not child_visible and payload.get("kind") == "layer")
            if needle and child_visible:
                item.setExpanded(True)
            return visible or child_visible

        for index in range(self.tree.topLevelItemCount()):
            visit(self.tree.topLevelItem(index))

    def _apply_draw_filter(self, text: str) -> None:
        needle = text.strip().lower()

        def visit(item: QTreeWidgetItem) -> bool:
            payload = item.data(0, Qt.UserRole) or {}
            visible = False
            if payload.get("kind") in {"trace", "collection"}:
                visible = not needle or needle in item.text(0).lower()
            child_visible = False
            for index in range(item.childCount()):
                if visit(item.child(index)):
                    child_visible = True
            item.setHidden(
                not visible
                and not child_visible
                and payload.get("kind") in {"trace", "collection"}
            )
            if needle and child_visible:
                item.setExpanded(True)
            return visible or child_visible

        for index in range(self.draw_tree.topLevelItemCount()):
            visit(self.draw_tree.topLevelItem(index))
