"""debugpy bootstrap for GridRadar plugin development."""

from __future__ import annotations

import os


def start_debugpy_if_enabled() -> None:
    """Start debugpy when QGIS was launched with GRIDRADAR_DEBUGPY=1.

    Not used when debugging via QGIS DevTools (DevTools owns port 5678).
    """
    if os.environ.get("GRIDRADAR_DEBUGPY") != "1":
        return

    try:
        import debugpy
    except ImportError:
        print(
            "[gridradar] debugpy not installed — run: ./scripts/install-qgis-debug.sh",
            flush=True,
        )
        return

    if debugpy.is_client_connected():
        return

    host = os.environ.get("GRIDRADAR_DEBUGPY_HOST", "127.0.0.1")
    port = int(os.environ.get("GRIDRADAR_DEBUGPY_PORT", "5678"))
    endpoint = (host, port)

    try:
        debugpy.listen(endpoint)
        print(f"[gridradar] debugpy listening on {host}:{port}", flush=True)
        return
    except RuntimeError as exc:
        if "in use" not in str(exc).lower():
            print(f"[gridradar] debugpy listen failed: {exc}", flush=True)
            return

    try:
        debugpy.connect(endpoint)
        print(f"[gridradar] debugpy connected to {host}:{port}", flush=True)
    except RuntimeError as exc:
        print(f"[gridradar] debugpy connect failed: {exc}", flush=True)
