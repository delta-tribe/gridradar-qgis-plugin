"""ArcGIS REST layer builders."""

from __future__ import annotations

from typing import Any

from qgis.core import QgsRasterLayer, QgsVectorLayer

from .helpers import apply_proxy_headers, proxy_service_url


def _resolved_url(descriptor: dict[str, Any], *, api_base: str) -> str | None:
    if descriptor.get("requires_proxy") and descriptor.get("proxy_path"):
        return proxy_service_url(api_base, str(descriptor["proxy_path"]))
    return descriptor.get("service_url") or descriptor.get("uri")


def build_arcgis_feature_layer(
    descriptor: dict[str, Any],
    *,
    api_base: str,
    token: str,
    org_id: int | None,
) -> QgsVectorLayer | None:
    service_url = _resolved_url(descriptor, api_base=api_base)
    if not service_url:
        return None

    uri = descriptor.get("uri") or f"url='{service_url}'"
    if service_url not in uri:
        uri = f"url='{service_url}'"

    layer = QgsVectorLayer(uri, descriptor["name"], "arcgisfeatureserver")
    if descriptor.get("requires_proxy"):
        apply_proxy_headers(layer, token, org_id)
    if not layer.isValid():
        layer = QgsVectorLayer(service_url, descriptor["name"], "arcgisfeatureserver")
        if descriptor.get("requires_proxy"):
            apply_proxy_headers(layer, token, org_id)
    if not layer.isValid():
        return None
    return layer


def build_arcgis_image_layer(
    descriptor: dict[str, Any],
    *,
    api_base: str,
    token: str,
    org_id: int | None,
) -> QgsRasterLayer | None:
    service_url = _resolved_url(descriptor, api_base=api_base)
    if not service_url:
        return None

    uri = descriptor.get("uri") or f"url='{service_url}' crs='EPSG:3857'"
    layer = QgsRasterLayer(uri, descriptor["name"], "arcgismapserver")
    if descriptor.get("requires_proxy"):
        apply_proxy_headers(layer, token, org_id)
    if not layer.isValid():
        layer = QgsRasterLayer(service_url, descriptor["name"], "arcgismapserver")
        if descriptor.get("requires_proxy"):
            apply_proxy_headers(layer, token, org_id)
    if not layer.isValid():
        return None
    return layer
