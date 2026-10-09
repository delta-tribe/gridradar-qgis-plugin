"""Shared provider helpers."""

from __future__ import annotations

import base64
import re

from qgis.core import QgsDataSourceUri, QgsHttpHeaders, QgsMapLayer

_OPENLAYERS_SUBDOMAIN_RE = re.compile(r"\{[a-z]-[a-z]\}")
_QGIS_SUBDOMAIN_PLACEHOLDER = "{s}"


def apply_basic_auth_headers(layer: QgsMapLayer, username: str, password: str) -> None:
    """Attach HTTP Basic auth headers for authenticated raster/vector sources."""
    token = base64.b64encode(f"{username}:{password}".encode()).decode("ascii")
    headers = QgsHttpHeaders()
    _set_http_header(headers, "authorization", f"Basic {token}")
    provider = layer.dataProvider()
    if hasattr(provider, "setHttpHeaders"):
        provider.setHttpHeaders(headers)


def build_proxy_http_headers(token: str, org_id: int | None) -> QgsHttpHeaders:
    """Build Bearer auth headers for proxied GridRadar sources."""
    headers = QgsHttpHeaders()
    _set_http_header(headers, "authorization", f"Bearer {token}")
    if org_id is not None:
        _set_http_header(headers, "x-org-id", str(org_id))
    return headers


def apply_proxy_uri_headers(uri: QgsDataSourceUri, token: str, org_id: int | None) -> None:
    """Attach Bearer auth to a data source URI before layer construction.

    WMS GetCapabilities runs during QgsRasterLayer creation; headers must be
    embedded in the URI (http-header:...) rather than set on the provider later.
    """
    if hasattr(uri, "setHttpHeaders"):
        uri.setHttpHeaders(build_proxy_http_headers(token, org_id))


def apply_proxy_wms_params(uri: QgsDataSourceUri) -> None:
    """Keep proxied WMS requests on the configured URL, not upstream paths from capabilities."""
    uri.setParam("IgnoreGetMapUrl", "1")
    uri.setParam("IgnoreGetFeatureInfoUrl", "1")


def apply_proxy_headers(layer: QgsMapLayer, token: str, org_id: int | None) -> None:
    """Attach Bearer auth headers on the layer provider (GetMap and follow-up requests)."""
    provider = layer.dataProvider()
    if hasattr(provider, "setHttpHeaders"):
        provider.setHttpHeaders(build_proxy_http_headers(token, org_id))


def proxy_service_url(api_base: str, proxy_path: str) -> str:
    return f"{api_base.rstrip('/')}{proxy_path}"


def normalize_xyz_url_for_qgis(url: str) -> str:
    """Replace unsupported subdomain placeholders with a fixed Carto host."""
    url = _OPENLAYERS_SUBDOMAIN_RE.sub("a", url)
    return url.replace(_QGIS_SUBDOMAIN_PLACEHOLDER, "a")


def _set_http_header(headers: QgsHttpHeaders, key: str, value: str) -> None:
    """Set a header on QgsHttpHeaders across QGIS API versions."""
    if hasattr(headers, "setHeader"):
        headers.setHeader(key, value)
    else:
        headers.insert(key, value)


_ARCGIS_WMS_PROXY_PREFIXES = (
    "/proxy/abruzzo-",
    "/proxy/molise-arcgis",
    "/proxy/puglia-sit-arcgis",
)


def default_wms_styles(descriptor: dict) -> str:
    """Return the WMS STYLES value QGIS needs for GetCapabilities validation."""
    styles = descriptor.get("styles")
    if styles is not None and str(styles):
        return str(styles)

    proxy_path = str(descriptor.get("proxy_path") or "")
    if any(proxy_path.startswith(prefix) for prefix in _ARCGIS_WMS_PROXY_PREFIXES):
        return "default"
    return ""
