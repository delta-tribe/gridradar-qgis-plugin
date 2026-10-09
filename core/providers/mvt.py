"""Vector tile (MVT) layer builder."""

from __future__ import annotations

from typing import Any

from qgis.core import QgsDataSourceUri, QgsVectorTileLayer

from ..mvt.style import apply_openinframap_style
from .helpers import apply_proxy_headers, apply_proxy_uri_headers, proxy_service_url


def build_mvt_layer(
    descriptor: dict[str, Any],
    *,
    api_base: str,
    token: str,
    org_id: int | None,
) -> QgsVectorTileLayer | None:
    service_url = descriptor.get("service_url")
    if descriptor.get("requires_proxy") and descriptor.get("proxy_path"):
        service_url = proxy_service_url(api_base, str(descriptor["proxy_path"]))
    if not service_url:
        return None

    uri = QgsDataSourceUri()
    uri.setParam("type", "xyz")
    uri.setParam("url", str(service_url))
    zmax = descriptor.get("max_zoom")
    if zmax is not None:
        uri.setParam("zmax", str(zmax))
    zmin = descriptor.get("min_zoom")
    if zmin is not None:
        uri.setParam("zmin", str(zmin))
    crs = descriptor.get("crs") or "EPSG:3857"
    uri.setParam("crs", str(crs))
    if descriptor.get("requires_proxy"):
        apply_proxy_uri_headers(uri, token, org_id)

    layer = QgsVectorTileLayer(uri.encodedUri().data().decode(), descriptor["name"])
    if descriptor.get("requires_proxy"):
        apply_proxy_headers(layer, token, org_id)
    if not layer.isValid():
        return None

    source_layers = descriptor.get("source_layers") or []
    apply_openinframap_style(layer, source_layers)
    return layer
