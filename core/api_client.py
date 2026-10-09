"""HTTP client for the GridRadar FastAPI backend."""

from __future__ import annotations

from typing import Any

import requests


class GridRadarApiError(RuntimeError):
    """Raised when the GridRadar API returns an error response."""

    def __init__(self, status_code: int, message: str, payload: Any | None = None) -> None:
        super().__init__(f"GridRadar API HTTP {status_code}: {message}")
        self.status_code = status_code
        self.payload = payload
        self.message = message


class GridRadarApiClient:
    """Small synchronous client for GridRadar auth and GIS catalog endpoints."""

    def __init__(
        self,
        api_base: str,
        *,
        token: str | None = None,
        org_id: int | None = None,
        timeout: float = 60.0,
    ) -> None:
        self.api_base = api_base.rstrip("/")
        self.token = token
        self.org_id = org_id
        self.timeout = timeout
        self._session = requests.Session()
        self._session.headers.update({"Accept": "application/json"})

    def set_token(self, token: str | None) -> None:
        self.token = token

    def set_org_id(self, org_id: int | None) -> None:
        self.org_id = org_id

    def _headers(self) -> dict[str, str]:
        headers: dict[str, str] = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        if self.org_id is not None:
            headers["X-Org-Id"] = str(self.org_id)
        return headers

    def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        response = self._session.request(
            method,
            f"{self.api_base}{path}",
            headers=self._headers(),
            json=json,
            params=params,
            timeout=self.timeout,
        )
        if response.status_code >= 400:
            payload: Any
            try:
                payload = response.json()
            except ValueError:
                payload = response.text
            message = payload.get("detail") if isinstance(payload, dict) else str(payload)
            raise GridRadarApiError(response.status_code, str(message), payload)
        if response.status_code == 204:
            return None
        if not response.content:
            return None
        return response.json()

    def login(self, identifier: str, password: str) -> dict[str, Any]:
        return self._request(
            "POST",
            "/auth/login",
            json={"identifier": identifier, "password": password},
        )

    def me(self) -> dict[str, Any]:
        return self._request("GET", "/auth/me")

    def get_catalog(self) -> dict[str, Any]:
        return self._request("GET", "/gis/catalog")

    def get_catalog_version(self) -> dict[str, Any]:
        return self._request("GET", "/gis/catalog/version")

    def resolve_layers(self, layer_ids: list[str]) -> dict[str, Any]:
        return self._request(
            "POST",
            "/gis/catalog/resolve",
            json={"layer_ids": layer_ids},
        )

    def validate_sinfi(self, username: str, password: str) -> dict[str, Any]:
        return self._request(
            "POST",
            "/me/integrations/sinfi/validate",
            json={"username": username, "password": password},
        )

    def get_draw_workspace(self, org_id: int) -> dict[str, Any]:
        """Fetch personal/org collections and traces for the draw workspace."""
        return self._request("GET", f"/orgs/{org_id}/map-drawings")

    def get_layer_selections(self, org_id: int) -> dict[str, Any]:
        """Fetch saved personal/org layer visibility presets."""
        return self._request("GET", f"/orgs/{org_id}/layer-selections")
