"""Runtime SINFI session state."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SinfiSession:
    """Connected SINFI session for one group."""

    username: str
    password: str
    group_code: str
    group_name: str
    auth_config_id: str
    layers: list[dict[str, Any]] = field(default_factory=list)
    grouped_layers: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
