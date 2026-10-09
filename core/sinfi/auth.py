"""SINFI credential storage and WMS helpers."""

from __future__ import annotations

import requests
from qgis.core import QgsApplication, QgsAuthMethodConfig, QgsDataSourceUri, QgsRasterLayer

from ..providers.helpers import apply_basic_auth_headers

SINFI_WMS_BASE = "https://sinfi.it/data/ows/{group_code}/wms"
SINFI_AUTH_URI = "sinfi.it"


def store_basic_auth(username: str, password: str) -> str:
    """Store SINFI Basic auth in the QGIS auth manager."""
    auth_mgr = QgsApplication.authManager()
    config = QgsAuthMethodConfig()
    config.setName("GridRadar SINFI")
    config.setMethod("Basic")
    config.setUri(SINFI_AUTH_URI)
    config.setConfig("username", username)
    config.setConfig("password", password)
    if not config.isValid():
        raise ValueError("Configurazione autenticazione SINFI non valida.")
    if not auth_mgr.storeAuthenticationConfig(config):
        raise RuntimeError("Impossibile salvare le credenziali SINFI in QGIS.")
    return config.id()


def remove_auth_config(auth_config_id: str | None) -> None:
    if not auth_config_id:
        return
    QgsApplication.authManager().removeAuthenticationConfig(auth_config_id)


def fetch_capabilities(group_code: str, username: str, password: str) -> str:
    """Download SINFI WMS GetCapabilities XML."""
    response = requests.get(
        SINFI_WMS_BASE.format(group_code=group_code),
        params={"service": "WMS", "request": "GetCapabilities"},
        auth=(username, password),
        timeout=60,
    )
    response.raise_for_status()
    return response.text


def build_sinfi_wms_layer(
    *,
    group_code: str,
    layer_name: str,
    style_name: str,
    display_name: str,
    username: str,
    password: str,
    auth_config_id: str,
) -> QgsRasterLayer:
    """Create an authenticated SINFI WMS raster layer."""
    uri = QgsDataSourceUri()
    uri.setParam("authcfg", auth_config_id)
    uri.setParam("layers", layer_name)
    uri.setParam("styles", style_name)
    uri.setParam("crs", "EPSG:3857")
    uri.setParam("format", "image/png")
    uri.setParam("contextualWMSLegend", "0")
    uri.setParam("dpiMode", "7")
    uri.setParam("featureCount", "10")
    uri.setParam("tilePixelRatio", "0")
    uri.setParam("url", SINFI_WMS_BASE.format(group_code=group_code))

    layer = QgsRasterLayer(uri.encodedUri().data().decode(), display_name, "wms")
    apply_basic_auth_headers(layer, username, password)
    layer.setCustomProperty("gridradar_sinfi_layer_id", f"sinfi_{group_code}_{layer_name}_{style_name}")
    return layer
