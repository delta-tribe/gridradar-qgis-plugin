"""WMS layer builder."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlencode

from qgis.core import QgsDataSourceUri, QgsRasterLayer

from .helpers import (
    apply_proxy_headers,
    apply_proxy_uri_headers,
    apply_proxy_wms_params,
    default_wms_styles,
    proxy_service_url,
)


def build_wms_layer(
    descriptor: dict[str, Any],
    *,
    api_base: str,
    token: str,
    org_id: int | None,
) -> QgsRasterLayer | None:
    requires_proxy = bool(descriptor.get("requires_proxy"))
    proxy_path = descriptor.get("proxy_path")
    service_url = descriptor.get("service_url")

    if requires_proxy and proxy_path:
        service_url = proxy_service_url(api_base, str(proxy_path))

    if not service_url:
        return None

    uri = QgsDataSourceUri()
    uri.setParam("url", str(service_url))
    if descriptor.get("layers"):
        uri.setParam("layers", str(descriptor["layers"]))
    # QGIS rejects GeoServer WMS layers without an explicit styles param.
    uri.setParam("styles", default_wms_styles(descriptor))
    crs = descriptor.get("crs") or descriptor.get("wms_projection") or "EPSG:3857"
    uri.setParam("crs", str(crs))
    uri.setParam("format", "image/png")
    if descriptor.get("wms_version"):
        uri.setParam("version", str(descriptor["wms_version"]))
    if descriptor.get("cql_filter"):
        uri.setParam("cqlFilter", str(descriptor["cql_filter"]))
    if requires_proxy:
        apply_proxy_wms_params(uri)
        apply_proxy_uri_headers(uri, token, org_id)

    layer = QgsRasterLayer(uri.encodedUri().data().decode(), descriptor["name"], "wms")
    if requires_proxy:
        apply_proxy_headers(layer, token, org_id)
    if not layer.isValid():
        return None
    return layer
