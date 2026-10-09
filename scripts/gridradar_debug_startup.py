"""QGIS debugpy bootstrap (via ``qgis --code`` or profile ``startup.py``).

Active only when ``GRIDRADAR_DEBUGPY=1`` (set by ``scripts/debug-qgis.sh``).
"""

from __future__ import annotations

import os

_STARTED = False


def _boot() -> None:
    global _STARTED
    if _STARTED:
        return
    if os.environ.get("GRIDRADAR_DEBUGPY") != "1":
        return

    try:
        import debugpy
    except ImportError as exc:
        print(
            "[gridradar] debugpy not installed — run: sudo apt install python3-debugpy",
            flush=True,
        )
        print(f"[gridradar] ({exc})", flush=True)
        return

    host = os.environ.get("GRIDRADAR_DEBUGPY_HOST", "127.0.0.1")
    port = int(os.environ.get("GRIDRADAR_DEBUGPY_PORT", "5678"))

    try:
        debugpy.listen((host, port))
    except RuntimeError as exc:
        if "in use" not in str(exc).lower():
            raise
        print(f"[gridradar] debugpy already listening on {host}:{port}", flush=True)
    else:
        print(f"[gridradar] debugpy listening on {host}:{port}", flush=True)

    _STARTED = True


_boot()
