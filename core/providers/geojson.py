"""GeoJSON vector layer builder."""

from __future__ import annotations

from typing import Any

from qgis.core import QgsVectorLayer

from .helpers import apply_proxy_headers, proxy_service_url


def build_geojson_layer(
    descriptor: dict[str, Any],
    *,
    api_base: str,
    token: str,
    org_id: int | None,
) -> QgsVectorLayer | None:
    service_url = descriptor.get("service_url") or descriptor.get("uri")
    if descriptor.get("requires_proxy") and descriptor.get("proxy_path"):
        service_url = proxy_service_url(api_base, str(descriptor["proxy_path"]))
    if not service_url:
        return None

    layer = QgsVectorLayer(service_url, descriptor["name"], "ogr")
    if descriptor.get("requires_proxy"):
        apply_proxy_headers(layer, token, org_id)
    if not layer.isValid():
        return None
    return layer
