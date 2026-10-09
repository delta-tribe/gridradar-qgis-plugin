# -*- coding: utf-8 -*-
"""GridRadar QGIS plugin main entry."""

from __future__ import annotations

import os.path

from qgis.PyQt.QtCore import QTimer, Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QMessageBox
from qgis.core import QgsMapLayer, QgsPointXY, QgsProject

from .core.api_client import GridRadarApiClient, GridRadarApiError
from .core.auth_store import AuthStore
from .core.catalog_cache import CatalogCache
from .core.layer_manager import LayerManager
from .core.mvt.identify import identify_mvt_feature
from .core.draw.trace_layers import build_trace_layer
from .core.providers.factory import build_map_layer, insert_layer_in_group
from .core.sinfi.auth import (
    build_sinfi_wms_layer,
    fetch_capabilities,
    remove_auth_config,
    store_basic_auth,
)
from .core.sinfi.capabilities import parse_wms_capabilities
from .core.sinfi.enabled_layers import (
    build_enabled_sinfi_layers,
    group_sinfi_layers,
    sinfi_unavailable_layer_notice,
)
from .core.sinfi.session import SinfiSession
from .gui.catalog_dock import CatalogDockWidget
from .gui.feature_detail_dialog import FeatureDetailDialog
from .gui.login_dialog import LoginDialog
from .gui.map_identify_filter import MapIdentifyFilter
from .gui.sinfi_dialog import SinfiDialog


class GridRadarPlugin:
    """Main plugin orchestrator."""

    def __init__(self, iface) -> None:
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.actions: list[QAction] = []
        self.menu_name = "&GridRadar"

        self.auth_store = AuthStore()
        self.catalog_cache = CatalogCache()
        self.api_client: GridRadarApiClient | None = None
        self.layer_manager = LayerManager(on_layer_removed=self._on_catalog_layer_removed)

        self.dock: CatalogDockWidget | None = None
        self.sinfi_session: SinfiSession | None = None
        self.sinfi_auth_config_id: str | None = None
        self._map_identify_filter: MapIdentifyFilter | None = None
        self._feature_detail_dialog: FeatureDetailDialog | None = None
        self._draw_workspace: dict | None = None
        self._draw_traces_by_id: dict[int, dict] = {}
        self._layer_selections_by_id: dict[int, dict] = {}

        self._refresh_timer = QTimer()
        self._refresh_timer.setInterval(5 * 60 * 1000)
        self._refresh_timer.timeout.connect(self._refresh_session)

    def tr(self, message: str) -> str:
        return message

    def initGui(self) -> None:
        icon_path = os.path.join(self.plugin_dir, "icon.png")
        icon = QIcon(icon_path) if os.path.exists(icon_path) else QIcon()
        action = QAction(icon, self.tr("GridRadar"), self.iface.mainWindow())
        action.triggered.connect(self.run)
        action.setEnabled(True)
        self.iface.addPluginToWebMenu(self.menu_name, action)
        self.iface.addToolBarIcon(action)
        self.actions.append(action)

    def unload(self) -> None:
        for action in self.actions:
            self.iface.removePluginWebMenu(self.menu_name, action)
            self.iface.removeToolBarIcon(action)
        self._teardown_dock()

    def run(self) -> None:
        if not self._ensure_logged_in():
            return
        self._show_catalog_dock()

    @staticmethod
    def _resolve_org_id(login: dict, profile: dict) -> int | None:
        preferred_org = login.get("org_id")
        if preferred_org is not None:
            return int(preferred_org)
        organizations = profile.get("organizations") or []
        if organizations:
            return int(organizations[0]["id"])
        return None

    @staticmethod
    def _resolve_org_name(profile: dict, org_id: int | None) -> str | None:
        if org_id is None:
            return None
        for org in profile.get("organizations") or []:
            if org.get("id") == org_id:
                name = org.get("name")
                return str(name) if name else None
        return None

    def _session_user_label(self, profile: dict | None = None) -> str:
        user = self.auth_store.identifier()
        org_name = self.auth_store.org_name()
        if org_name is None and profile is not None:
            org_name = self._resolve_org_name(profile, self.auth_store.org_id())
            if org_name:
                self.auth_store.set_org_name(org_name)
        if org_name:
            return f"{user} · {org_name}"
        return user

    def _ensure_logged_in(self) -> bool:
        if self.api_client and self.auth_store.token():
            try:
                self._refresh_session()
                return True
            except GridRadarApiError:
                self.auth_store.clear_session()

        dialog = LoginDialog(theme_source=self.iface.mainWindow())
        dialog.identifier_edit.setText(self.auth_store.identifier())
        dialog.set_api_base_value(self.auth_store.api_base())

        while True:
            if dialog.exec_() != LoginDialog.Accepted:
                return False

            self.api_client = GridRadarApiClient(
                dialog.api_base(),
                token=None,
                org_id=None,
            )
            try:
                login = self.api_client.login(dialog.identifier(), dialog.password())
            except GridRadarApiError as exc:
                dialog.set_status(str(exc.message))
                continue

            self.auth_store.set_api_base(dialog.api_base())
            self.auth_store.set_identifier(dialog.identifier())
            self.auth_store.set_token(login["access_token"])
            self.api_client.set_token(login["access_token"])

            try:
                profile = self.api_client.me()
            except GridRadarApiError as exc:
                dialog.set_status(str(exc.message))
                continue

            org_id = self._resolve_org_id(login, profile)

            if org_id is None:
                dialog.set_status("Nessuna organizzazione disponibile per l'utente.")
                continue

            self.auth_store.set_org_id(int(org_id))
            self.api_client.set_org_id(int(org_id))
            org_name = self._resolve_org_name(profile, org_id)
            self.auth_store.set_org_name(org_name)
            refreshed_token = profile.get("access_token") or login["access_token"]
            self.auth_store.set_token(refreshed_token)
            self.api_client.set_token(refreshed_token)
            return True

    def _show_catalog_dock(self) -> None:
        if self.dock is None:
            self.dock = CatalogDockWidget(self.iface.mainWindow())
            self.dock.layer_toggled.connect(self._on_layer_toggled)
            self.dock.trace_toggled.connect(self._on_trace_toggled)
            self.dock.collection_toggled.connect(self._on_collection_toggled)
            self.dock.layer_selection_toggled.connect(self._on_layer_selection_toggled)
            self.dock.selection_layer_toggled.connect(self._on_selection_layer_toggled)
            self.dock.sinfi_connect_requested.connect(self._connect_sinfi)
            self.dock.refresh_requested.connect(self._load_catalog)
            self.dock.draw_refresh_requested.connect(self._load_draw_workspace)
            self.dock.layer_selections_refresh_requested.connect(self._load_layer_selections)
            self.dock.logout_requested.connect(self._logout)
            self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dock)

        self.dock.set_user_label(self._session_user_label())
        self.dock.show()
        self.dock.raise_()
        self._ensure_map_identify_filter()
        self._load_catalog()
        self._load_layer_selections()
        self._load_draw_workspace()
        self._refresh_timer.start()

    def _ensure_map_identify_filter(self) -> None:
        if self._map_identify_filter is None:
            self._map_identify_filter = MapIdentifyFilter(self.iface.mapCanvas())
            self._map_identify_filter.map_clicked.connect(self._on_map_clicked)
        self._map_identify_filter.set_enabled(True)

    def _on_map_clicked(self, point: QgsPointXY) -> None:
        if not self.layer_manager.tracked_qgis_ids():
            return

        canvas = self.iface.mapCanvas()
        hit = identify_mvt_feature(
            point,
            canvas_crs=canvas.mapSettings().destinationCrs(),
            map_scale=canvas.scale(),
            tracked_qgis_ids=self.layer_manager.tracked_qgis_ids(),
        )
        if hit is None:
            return

        _layer, details = hit
        if self._feature_detail_dialog is not None:
            self._feature_detail_dialog.close()

        dialog = FeatureDetailDialog(
            details,
            theme_source=self.iface.mainWindow(),
            parent=self.iface.mainWindow(),
        )
        self._feature_detail_dialog = dialog
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()

    def _teardown_dock(self) -> None:
        self._refresh_timer.stop()
        if self._map_identify_filter is not None:
            self._map_identify_filter.set_enabled(False)
        if self._feature_detail_dialog is not None:
            self._feature_detail_dialog.close()
            self._feature_detail_dialog = None
        if self.dock is not None:
            self.iface.removeDockWidget(self.dock)
            self.dock.deleteLater()
            self.dock = None

    def _refresh_session(self) -> None:
        if not self.api_client or not self.auth_store.token():
            return
        profile = self.api_client.me()
        token = profile.get("access_token")
        if token:
            self.auth_store.set_token(token)
            self.api_client.set_token(token)
        org_name = self._resolve_org_name(profile, self.auth_store.org_id())
        if org_name:
            self.auth_store.set_org_name(org_name)
        if self.dock:
            self.dock.set_user_label(self._session_user_label(profile))

    def _load_catalog(self) -> None:
        if not self.api_client or not self.dock:
            return
        try:
            payload = self.api_client.get_catalog()
        except GridRadarApiError as exc:
            self._show_error("Impossibile caricare il catalogo", str(exc.message))
            return

        version = payload.get("catalog_version", "")
        self.auth_store.set_catalog_version(version)
        self.catalog_cache.save(version, payload)
        self.dock.populate_catalog(payload)
        if self.sinfi_session:
            self.dock.populate_sinfi_layers(self.sinfi_session.grouped_layers)

    def _load_layer_selections(self) -> None:
        if not self.api_client or not self.dock:
            return
        org_id = self.auth_store.org_id()
        if org_id is None:
            return
        try:
            payload = self.api_client.get_layer_selections(org_id)
        except GridRadarApiError as exc:
            self._show_error("Impossibile caricare le selezioni", str(exc.message))
            return

        self._layer_selections_by_id = {
            int(selection["id"]): selection
            for selection in (payload.get("personal") or []) + (payload.get("organization") or [])
        }
        self.dock.populate_layer_selections(payload)
        for layer_id in self.layer_manager.tracked_layer_ids():
            if layer_id.startswith("draw:"):
                continue
            self.dock.set_selection_layer_checked(layer_id, True)
        self._sync_all_layer_selection_check_states()

    def _draw_trace_layer_id(self, trace_id: int) -> str:
        return f"draw:{trace_id}"

    def _load_draw_workspace(self) -> None:
        if not self.api_client or not self.dock:
            return
        org_id = self.auth_store.org_id()
        if org_id is None:
            return
        try:
            workspace = self.api_client.get_draw_workspace(org_id)
        except GridRadarApiError as exc:
            self._show_error("Impossibile caricare i disegni", str(exc.message))
            return

        self._draw_workspace = workspace
        self._draw_traces_by_id = {
            int(trace["id"]): trace for trace in workspace.get("traces") or []
        }
        self.dock.populate_draw_workspace(workspace)

        stale_ids = [
            int(layer_id.removeprefix("draw:"))
            for layer_id in self.layer_manager.tracked_layer_ids()
            if layer_id.startswith("draw:") and int(layer_id.removeprefix("draw:")) not in self._draw_traces_by_id
        ]
        for trace_id in stale_ids:
            self._remove_trace_layer(trace_id)

        for layer_id in self.layer_manager.tracked_layer_ids():
            if not layer_id.startswith("draw:"):
                continue
            trace_id = int(layer_id.removeprefix("draw:"))
            self.dock.set_trace_checked(trace_id, True)

        for trace_id, trace in self._draw_traces_by_id.items():
            if not trace.get("visible", True):
                continue
            if self.layer_manager.is_checked(self._draw_trace_layer_id(trace_id)):
                continue
            self._add_trace_layer(trace_id, notify=False)
            self.dock.set_trace_checked(trace_id, True)

        self._sync_all_collection_check_states()

    def _on_trace_toggled(self, trace_id: int, checked: bool) -> None:
        if checked:
            self._add_trace_layer(trace_id)
        else:
            self._remove_trace_layer(trace_id)
        if self.dock:
            trace = self._draw_traces_by_id.get(trace_id)
            if trace:
                self.dock.sync_collection_check_state(int(trace.get("collection_id") or 0))

    def _on_collection_toggled(self, collection_id: int, checked: bool) -> None:
        trace_ids = self._trace_ids_for_collection(collection_id)
        if not trace_ids:
            if self.dock:
                self.dock.set_collection_checked(collection_id, False)
            return

        if checked:
            added = 0
            for trace_id in trace_ids:
                if self.layer_manager.is_checked(self._draw_trace_layer_id(trace_id)):
                    continue
                self._add_trace_layer(trace_id, notify=False)
                if self.dock:
                    self.dock.set_trace_checked(trace_id, True)
                added += 1
            if added:
                self.iface.messageBar().pushSuccess(
                    "GridRadar",
                    f"Raccolta aggiunta: {self._collection_name(collection_id)} ({added} disegni)",
                )
        else:
            for trace_id in trace_ids:
                if not self.layer_manager.is_checked(self._draw_trace_layer_id(trace_id)):
                    continue
                self._remove_trace_layer(trace_id)
                if self.dock:
                    self.dock.set_trace_checked(trace_id, False)

        if self.dock:
            self.dock.sync_collection_check_state(collection_id)

    def _add_trace_layer(self, trace_id: int, *, notify: bool = True) -> None:
        if not self.dock:
            return
        trace = self._draw_traces_by_id.get(trace_id)
        if trace is None:
            self.dock.set_trace_checked(trace_id, False)
            self._show_error("Disegno non disponibile", f"Traccia {trace_id}")
            return

        layer_key = self._draw_trace_layer_id(trace_id)
        if self.layer_manager.is_checked(layer_key):
            return

        qgis_layer = build_trace_layer(trace)
        if qgis_layer is None:
            self.dock.set_trace_checked(trace_id, False)
            self._show_error("Disegno non valido", trace.get("name", str(trace_id)))
            return

        collection_name = self._collection_name_for_trace(trace)
        group_name = f"GridRadar · Disegni · {collection_name}"
        insert_layer_in_group(qgis_layer, group_name)
        self._tag_draw_trace_layer(qgis_layer, trace)
        self.layer_manager.register(layer_key, qgis_layer)
        if notify:
            self.iface.messageBar().pushSuccess(
                "GridRadar",
                f"Disegno aggiunto: {trace.get('name', trace_id)}",
            )

    def _collection_name(self, collection_id: int) -> str:
        workspace = self._draw_workspace or {}
        for collection in (workspace.get("personal") or []) + (workspace.get("organization") or []):
            if int(collection.get("id") or 0) == collection_id:
                return str(collection.get("name") or f"Raccolta {collection_id}")
        return f"Raccolta {collection_id}"

    def _collection_name_for_trace(self, trace: dict) -> str:
        return self._collection_name(int(trace.get("collection_id") or 0))

    def _trace_ids_for_collection(self, collection_id: int) -> list[int]:
        return [
            int(trace["id"])
            for trace in (self._draw_workspace or {}).get("traces") or []
            if int(trace.get("collection_id") or 0) == collection_id
        ]

    def _sync_all_collection_check_states(self) -> None:
        if not self.dock:
            return
        workspace = self._draw_workspace or {}
        collection_ids = {
            int(collection["id"])
            for collection in (workspace.get("personal") or []) + (workspace.get("organization") or [])
        }
        for collection_id in collection_ids:
            self.dock.sync_collection_check_state(collection_id)

    @staticmethod
    def _tag_draw_trace_layer(qgis_layer: QgsMapLayer, trace: dict) -> None:
        qgis_layer.setCustomProperty("gridradar_trace_id", int(trace["id"]))
        qgis_layer.setCustomProperty("gridradar_trace_name", trace.get("name", ""))
        qgis_layer.setCustomProperty("gridradar_trace_kind", trace.get("kind", ""))
        qgis_layer.setCustomProperty("gridradar_collection_id", int(trace.get("collection_id") or 0))

    def _remove_trace_layer(self, trace_id: int) -> None:
        layer_key = self._draw_trace_layer_id(trace_id)
        qgis_id = self.layer_manager.unregister(layer_key)
        if not qgis_id:
            return
        QgsProject.instance().removeMapLayer(qgis_id)

    def _on_layer_toggled(self, layer_id: str, checked: bool) -> None:
        if checked:
            self._add_layer(layer_id)
        else:
            self._remove_layer(layer_id)
        if self.dock:
            self.dock.set_selection_layer_checked(layer_id, checked)
        self._sync_layer_selections_for_layer(layer_id)

    def _selection_layer_opacity(self, selection_id: int, layer_id: str) -> float | None:
        selection = self._layer_selections_by_id.get(selection_id)
        if not selection:
            return None
        opacities = selection.get("layer_opacities") or {}
        if layer_id not in opacities:
            return None
        return float(opacities[layer_id])

    def _on_selection_layer_toggled(self, selection_id: int, layer_id: str, checked: bool) -> None:
        opacity = self._selection_layer_opacity(selection_id, layer_id)
        if checked:
            if self._add_layer(layer_id, opacity=opacity, notify=True):
                if self.dock:
                    self.dock.set_selection_layer_checked(layer_id, True)
            elif self.dock:
                self.dock.set_selection_layer_checked(layer_id, False)
        else:
            self._remove_layer(layer_id)
            if self.dock:
                self.dock.set_selection_layer_checked(layer_id, False)
        if self.dock:
            self.dock.sync_layer_selection_check_state(selection_id)
            self._sync_layer_selections_for_layer(layer_id)

    def _on_layer_selection_toggled(self, selection_id: int, checked: bool) -> None:
        selection = self._layer_selections_by_id.get(selection_id)
        if not selection or not self.dock:
            if self.dock:
                self.dock.set_layer_selection_checked(selection_id, False)
            return

        layer_ids = [str(layer_id) for layer_id in selection.get("layer_ids") or []]
        layer_opacities = {
            str(layer_id): float(opacity)
            for layer_id, opacity in (selection.get("layer_opacities") or {}).items()
        }
        if not layer_ids:
            self.dock.set_layer_selection_checked(selection_id, False)
            return

        if checked:
            added = 0
            missing = [
                layer_id
                for layer_id in layer_ids
                if not self.layer_manager.is_checked(layer_id)
            ]
            sinfi_ids = [layer_id for layer_id in missing if layer_id.startswith("sinfi_")]
            catalog_ids = [layer_id for layer_id in missing if not layer_id.startswith("sinfi_")]

            for layer_id in sinfi_ids:
                if self._add_layer(layer_id, opacity=layer_opacities.get(layer_id), notify=False):
                    self.dock.set_selection_layer_checked(layer_id, True)
                    added += 1

            for start in range(0, len(catalog_ids), 50):
                chunk = catalog_ids[start : start + 50]
                if not chunk:
                    continue
                try:
                    response = self.api_client.resolve_layers(chunk)  # type: ignore[union-attr]
                except GridRadarApiError as exc:
                    self._show_error("Impossibile risolvere la selezione", str(exc.message))
                    break
                for descriptor in response.get("layers") or []:
                    layer_id = str(descriptor.get("id"))
                    if self._add_layer_from_descriptor(
                        layer_id,
                        descriptor,
                        opacity=layer_opacities.get(layer_id),
                        notify=False,
                    ):
                        self.dock.set_selection_layer_checked(layer_id, True)
                        added += 1

            if added:
                self.iface.messageBar().pushSuccess(
                    "GridRadar",
                    f"Selezione applicata: {selection.get('name', selection_id)} ({added} layer)",
                )
            for layer_id in layer_ids:
                self.dock.set_selection_layer_checked(
                    layer_id,
                    self.layer_manager.is_checked(layer_id),
                )
                self._sync_layer_selections_for_layer(layer_id)
        else:
            for layer_id in layer_ids:
                if not self.layer_manager.is_checked(layer_id):
                    continue
                self._remove_layer(layer_id)
                self.dock.set_selection_layer_checked(layer_id, False)
                self._sync_layer_selections_for_layer(layer_id)

        self.dock.sync_layer_selection_check_state(selection_id)

    def _sync_layer_selections_for_layer(self, layer_id: str) -> None:
        if not self.dock:
            return
        for selection_id, selection in self._layer_selections_by_id.items():
            layer_ids = [str(layer_id) for layer_id in selection.get("layer_ids") or []]
            if layer_id in layer_ids:
                self.dock.sync_layer_selection_check_state(selection_id)

    def _sync_all_layer_selection_check_states(self) -> None:
        if not self.dock:
            return
        for selection_id in self._layer_selections_by_id:
            self.dock.sync_layer_selection_check_state(selection_id)

    def _add_layer(
        self,
        layer_id: str,
        *,
        opacity: float | None = None,
        notify: bool = True,
    ) -> bool:
        if not self.api_client or not self.dock:
            return False

        if layer_id.startswith("sinfi_") and self.sinfi_session:
            return self._add_sinfi_layer(layer_id, opacity=opacity, notify=notify)

        try:
            response = self.api_client.resolve_layers([layer_id])
        except GridRadarApiError as exc:
            self.dock.set_layer_checked(layer_id, False)
            if notify:
                self._show_error("Impossibile risolvere il layer", str(exc.message))
            return False

        layers = response.get("layers") or []
        if not layers:
            self.dock.set_layer_checked(layer_id, False)
            if notify:
                self._show_error("Layer non disponibile", layer_id)
            return False

        return self._add_layer_from_descriptor(
            layer_id,
            layers[0],
            opacity=opacity,
            notify=notify,
        )

    def _add_layer_from_descriptor(
        self,
        layer_id: str,
        descriptor: dict,
        *,
        opacity: float | None = None,
        notify: bool = True,
    ) -> bool:
        if not self.dock:
            return False

        qgis_layer = build_map_layer(
            descriptor,
            api_base=self.auth_store.api_base(),
            token=self.auth_store.token() or "",
            org_id=self.auth_store.org_id(),
        )
        if qgis_layer is None:
            self.dock.set_layer_checked(layer_id, False)
            if notify:
                self._show_error("Layer non valido in QGIS", descriptor.get("name", layer_id))
            return False

        group_name = descriptor.get("source_id") or "GridRadar"
        insert_layer_in_group(
            qgis_layer,
            f"GridRadar · {group_name}",
            opacity=opacity if opacity is not None else descriptor.get("opacity"),
        )
        self._tag_gridradar_layer(qgis_layer, layer_id, descriptor)
        self.layer_manager.register(layer_id, qgis_layer)
        if notify:
            self.iface.messageBar().pushSuccess(
                "GridRadar",
                f"Layer aggiunto: {descriptor.get('name', layer_id)}",
            )
        return True

    @staticmethod
    def _tag_gridradar_layer(
        qgis_layer: QgsMapLayer,
        layer_id: str,
        descriptor: dict,
    ) -> None:
        qgis_layer.setCustomProperty("gridradar_layer_id", layer_id)
        qgis_layer.setCustomProperty("gridradar_catalog_name", descriptor.get("name", layer_id))
        qgis_layer.setCustomProperty("gridradar_source_id", descriptor.get("source_id"))
        qgis_layer.setCustomProperty("gridradar_catalog_type", descriptor.get("catalog_type"))

    def _add_sinfi_layer(
        self,
        layer_id: str,
        *,
        opacity: float | None = None,
        notify: bool = True,
    ) -> bool:
        if not self.sinfi_session or not self.dock:
            return False

        match = next((layer for layer in self.sinfi_session.layers if layer["id"] == layer_id), None)
        if match is None:
            self.dock.set_layer_checked(layer_id, False)
            return False

        qgis_layer = build_sinfi_wms_layer(
            group_code=match["group_code"],
            layer_name=match["wms_layer"],
            style_name=match["style"],
            display_name=match["name"],
            username=self.sinfi_session.username,
            password=self.sinfi_session.password,
            auth_config_id=self.sinfi_session.auth_config_id,
        )
        if not qgis_layer.isValid():
            self.dock.set_layer_checked(layer_id, False)
            if notify:
                self._show_error(
                    "Layer SINFI non valido",
                    f"{match['name']}\n\nIl server SINFI potrebbe non servire questo layer "
                    f"({match['wms_layer']}). Prova Tratte o Nodi, oppure ricollega SINFI.",
                )
            return False

        insert_layer_in_group(qgis_layer, "GridRadar · SINFI", opacity=opacity if opacity is not None else 0.7)
        self.layer_manager.register(layer_id, qgis_layer)
        return True

    def _remove_layer(self, layer_id: str) -> None:
        qgis_id = self.layer_manager.unregister(layer_id)
        if not qgis_id:
            return
        QgsProject.instance().removeMapLayer(qgis_id)

    def _on_catalog_layer_removed(self, layer_id: str) -> None:
        if not self.dock:
            return
        if layer_id.startswith("draw:"):
            trace_id = int(layer_id.removeprefix("draw:"))
            self.dock.set_trace_checked(trace_id, False)
            trace = self._draw_traces_by_id.get(trace_id)
            if trace:
                self.dock.sync_collection_check_state(int(trace.get("collection_id") or 0))
            return
        self.dock.set_selection_layer_checked(layer_id, False)
        self._sync_layer_selections_for_layer(layer_id)

    def _connect_sinfi(self) -> None:
        if not self.api_client:
            return

        dialog = SinfiDialog(theme_source=self.iface.mainWindow())
        while True:
            if dialog.exec_() != SinfiDialog.Accepted:
                return

            username = dialog.username()
            password = dialog.password()
            if not username or not password:
                dialog.set_status("Inserire utente e password SINFI.")
                continue

            try:
                validated = self.api_client.validate_sinfi(username, password)
            except GridRadarApiError as exc:
                dialog.set_status(str(exc.message))
                continue

            codes = validated.get("group_codes") or []
            names = validated.get("group_names") or []
            if not codes:
                dialog.set_status("Nessun gruppo SINFI disponibile per l'utente.")
                continue

            dialog.set_groups(codes, names)
            if dialog.group_combo.count() == 1:
                dialog.group_combo.setCurrentIndex(0)
            if dialog.group_combo.currentIndex() < 0:
                dialog.set_status("Seleziona il gruppo SINFI e conferma.")
                continue

            group_code = dialog.group_code()
            try:
                capabilities_xml = fetch_capabilities(group_code, username, password)
            except Exception as exc:  # noqa: BLE001 - show user-facing network/XML errors
                dialog.set_status(f"GetCapabilities fallita: {exc}")
                continue

            capability_layers = parse_wms_capabilities(capabilities_xml)
            enabled_layers = build_enabled_sinfi_layers(capability_layers, group_code)
            if not enabled_layers:
                dialog.set_status("Nessun layer SINFI abilitato per questo gruppo.")
                continue

            if self.sinfi_auth_config_id:
                remove_auth_config(self.sinfi_auth_config_id)

            auth_config_id = store_basic_auth(username, password)
            self.sinfi_auth_config_id = auth_config_id
            grouped = group_sinfi_layers(enabled_layers)
            self.sinfi_session = SinfiSession(
                username=username,
                password=password,
                group_code=group_code,
                group_name=dialog.group_name(),
                auth_config_id=auth_config_id,
                layers=enabled_layers,
                grouped_layers=grouped,
            )
            if self.dock:
                self.dock.populate_sinfi_layers(grouped)
            unavailable_notice = sinfi_unavailable_layer_notice(capability_layers)
            if unavailable_notice:
                self.iface.messageBar().pushWarning("GridRadar", unavailable_notice)
            self.iface.messageBar().pushSuccess("GridRadar", "SINFI collegato correttamente.")
            return

    def _logout(self) -> None:
        reply = QMessageBox.question(
            self.iface.mainWindow(),
            "GridRadar",
            "Vuoi uscire e rimuovere i layer aggiunti dal plugin?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        for qgis_id in self.layer_manager.clear():
            QgsProject.instance().removeMapLayer(qgis_id)

        if self.sinfi_auth_config_id:
            remove_auth_config(self.sinfi_auth_config_id)
            self.sinfi_auth_config_id = None
        self.sinfi_session = None
        self._draw_workspace = None
        self._draw_traces_by_id = {}
        self._layer_selections_by_id = {}
        self.auth_store.clear_session()
        self.catalog_cache.clear()
        self.api_client = None
        self._teardown_dock()

    def _show_error(self, title: str, message: str) -> None:
        QMessageBox.warning(self.iface.mainWindow(), title, message)
