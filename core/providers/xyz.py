"""XYZ and OSM raster layer builders."""

from __future__ import annotations

from typing import Any

from urllib.parse import unquote

from qgis.core import QgsDataSourceUri, QgsRasterLayer

from .helpers import (
    apply_proxy_headers,
    apply_proxy_uri_headers,
    normalize_xyz_url_for_qgis,
    proxy_service_url,
)


def _xyz_service_url(descriptor: dict[str, Any]) -> str | None:
    service_url = descriptor.get("service_url")
    if service_url:
        return str(service_url)

    raw_uri = descriptor.get("uri") or ""
    prefix = "type=xyz&url="
    if not raw_uri.startswith(prefix):
        return None
    url_part = raw_uri[len(prefix) :].partition("&")[0]
    return unquote(url_part) if url_part else None


def build_xyz_layer(
    descriptor: dict[str, Any],
    *,
    api_base: str,
    token: str,
    org_id: int | None,
) -> QgsRasterLayer | None:
    if descriptor.get("requires_proxy") and descriptor.get("proxy_path"):
        service_url = proxy_service_url(api_base, str(descriptor["proxy_path"]))
    else:
        service_url = _xyz_service_url(descriptor)

    if not service_url:
        return None

    service_url = normalize_xyz_url_for_qgis(service_url)

    uri = QgsDataSourceUri()
    uri.setParam("type", "xyz")
    uri.setParam("url", service_url)
    zmax = descriptor.get("max_zoom")
    if zmax is not None:
        uri.setParam("zmax", str(zmax))
    crs = descriptor.get("crs") or "EPSG:3857"
    uri.setParam("crs", str(crs))
    if descriptor.get("requires_proxy"):
        apply_proxy_uri_headers(uri, token, org_id)

    layer = QgsRasterLayer(uri.encodedUri().data().decode(), descriptor["name"], "wms")
    if descriptor.get("requires_proxy"):
        apply_proxy_headers(layer, token, org_id)
    if not layer.isValid():
        return None
    return layer


def build_osm_layer(descriptor: dict[str, Any]) -> QgsRasterLayer | None:
    uri = descriptor.get("uri") or (
        "type=xyz&url=https://tile.openstreetmap.org/{z}/{x}/{y}.png"
    )
    layer = QgsRasterLayer(uri, descriptor.get("name", "OpenStreetMap"), "wms")
    return layer if layer.isValid() else None
