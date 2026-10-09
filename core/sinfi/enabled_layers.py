"""SINFI enabled layer whitelist (ported from GridRadar sinfiEnabledLayers.ts)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

SINFI_CATEGORY_LABELS = {
    "infr_alloggiamento_aree": "Infrastrutture di alloggiamento · Aree",
    "infr_alloggiamento_tratte": "Infrastrutture di alloggiamento · Tratte",
    "infr_alloggiamento_nodi": "Infrastrutture di alloggiamento · Nodi",
    "cantieri": "Cantieri",
}

SINFI_CATEGORY_ORDER = [
    "infr_alloggiamento_aree",
    "infr_alloggiamento_tratte",
    "infr_alloggiamento_nodi",
    "cantieri",
]

# Listed in GetCapabilities but SINFI WMS GetMap currently returns HTTP 500.
SINFI_WMS_GETMAP_BROKEN_LAYERS = frozenset({"INFR_RT_ESTENSIONE"})


@dataclass(frozen=True)
class SinfiEnabledLayerSpec:
    category: str
    wms_layer: str
    default_style: str
    display_name: str
    style_candidates: tuple[str, ...]
    style_titles: dict[str, str]


SINFI_ENABLED_LAYER_SPECS: list[SinfiEnabledLayerSpec] = [
    SinfiEnabledLayerSpec(
        category="infr_alloggiamento_aree",
        wms_layer="INFR_RT_ESTENSIONE",
        default_style="INFR_RT_POLYGONS_ALL",
        display_name="Aree",
        style_candidates=(
            "INFR_RT_POLYGONS_ALL",
            "INFR_RT_POLYGONS_BY_STATE",
            "INFR_RT_POLY_BY_TY",
            "INFR_RT_POLYGONS_BY_TR",
            "INFR_RT_POLYGONS_BY_INFR_RT_UT",
        ),
        style_titles={
            "INFR_RT_POLYGONS_ALL": "Default",
            "INFR_RT_POLYGONS_BY_STATE": "Stato infrastruttura",
            "INFR_RT_POLY_BY_TY": "Tipo di infrastruttura",
            "INFR_RT_POLYGONS_BY_TR": "Tipo di rete alloggiata",
            "INFR_RT_POLYGONS_BY_INFR_RT_UT": "Utilizzabilità infrastruttura",
        },
    ),
    SinfiEnabledLayerSpec(
        category="infr_alloggiamento_tratte",
        wms_layer="INFR_RT_ESTENSIONE_L",
        default_style="INFR_RT_LINES_ALL",
        display_name="Tratte",
        style_candidates=(
            "INFR_RT_LINES_ALL",
            "INFR_RT_LINES_BY_STATE",
            "INFR_RT_BY_TY",
            "INFR_RT_LINES_BY_TR",
            "INFR_RT_LINES_BY_INFR_RT_UT",
        ),
        style_titles={
            "INFR_RT_LINES_ALL": "Default",
            "INFR_RT_LINES_BY_STATE": "Stato infrastruttura",
            "INFR_RT_BY_TY": "Tipo di infrastruttura",
            "INFR_RT_LINES_BY_TR": "Tipo di rete alloggiata",
            "INFR_RT_LINES_BY_INFR_RT_UT": "Utilizzabilità infrastruttura",
        },
    ),
    SinfiEnabledLayerSpec(
        category="infr_alloggiamento_nodi",
        wms_layer="INFR_RT_ESTENSIONE_P",
        default_style="INFR_RT_POINTS_ALL",
        display_name="Nodi",
        style_candidates=(
            "INFR_RT_POINTS_ALL",
            "INFR_RT_POINTS_BY_STATE",
            "INFR_RT_POINT_BY_TY",
            "INFR_RT_POINTS_BY_TR",
            "INFR_RT_POINTS_BY_INFR_RT_UT",
        ),
        style_titles={
            "INFR_RT_POINTS_ALL": "Default",
            "INFR_RT_POINTS_BY_STATE": "Stato infrastruttura",
            "INFR_RT_POINT_BY_TY": "Tipo di infrastruttura",
            "INFR_RT_POINTS_BY_TR": "Tipo di rete alloggiata",
            "INFR_RT_POINTS_BY_INFR_RT_UT": "Utilizzabilità infrastruttura",
        },
    ),
    SinfiEnabledLayerSpec(
        category="cantieri",
        wms_layer="worksites",
        default_style="WORKSITE_BY_CATEGORY",
        display_name="Cantieri e progetti",
        style_candidates=("WORKSITE_BY_CATEGORY",),
        style_titles={"WORKSITE_BY_CATEGORY": "Categoria di cantiere"},
    ),
]


def build_enabled_sinfi_layers(
    capability_layers: list[dict[str, Any]],
    group_code: str,
) -> list[dict[str, Any]]:
    """Filter GetCapabilities layers using the servizi_sinfi whitelist."""
    capability_names = {layer["name"] for layer in capability_layers}
    capability_by_name = {layer["name"]: layer for layer in capability_layers}
    enabled: list[dict[str, Any]] = []

    for spec in SINFI_ENABLED_LAYER_SPECS:
        if spec.wms_layer in SINFI_WMS_GETMAP_BROKEN_LAYERS:
            continue

        available = spec.wms_layer in capability_names or any(
            style in capability_names for style in spec.style_candidates
        )
        if not available:
            continue

        styles = [
            {
                "name": style_name,
                "title": spec.style_titles.get(style_name, style_name),
            }
            for style_name in spec.style_candidates
            if style_name in capability_names
        ]
        if not styles and spec.wms_layer in capability_by_name:
            parent = capability_by_name[spec.wms_layer]
            styles = parent.get("styles") or [
                {"name": spec.default_style, "title": spec.style_titles.get(spec.default_style, spec.default_style)}
            ]

        for style in styles:
            parent = capability_by_name.get(spec.wms_layer, {})
            enabled.append(
                {
                    "id": f"sinfi_{group_code}_{spec.wms_layer}_{style['name']}",
                    "name": style["title"],
                    "wms_layer": spec.wms_layer,
                    "style": style["name"],
                    "category": spec.category,
                    "group_code": group_code,
                    "abstract": parent.get("abstract"),
                }
            )
    return enabled


def sinfi_unavailable_layer_notice(capability_layers: list[dict[str, Any]]) -> str | None:
    """Return a user-facing note when known-broken layers are omitted from the catalog."""
    capability_names = {layer["name"] for layer in capability_layers}
    unavailable = [
        SINFI_CATEGORY_LABELS.get(spec.category, spec.wms_layer)
        for spec in SINFI_ENABLED_LAYER_SPECS
        if spec.wms_layer in SINFI_WMS_GETMAP_BROKEN_LAYERS
        and (
            spec.wms_layer in capability_names
            or any(style in capability_names for style in spec.style_candidates)
        )
    ]
    if not unavailable:
        return None
    labels = ", ".join(unavailable)
    return (
        f"Layer SINFI temporaneamente non disponibili sul server WMS: {labels}. "
        "Usa Tratte o Nodi, oppure segnala il problema a SINFI."
    )


def group_sinfi_layers(layers: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped = {category: [] for category in SINFI_CATEGORY_ORDER}
    for layer in layers:
        grouped.setdefault(layer["category"], []).append(layer)
    return grouped
