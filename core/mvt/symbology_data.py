"""OpenInfraMap MVT symbology constants (aligned with the GridRadar web app)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class VoltageStop:
    min_kv: int
    color: str
    label: str


POWER_LINE_VOLTAGE_STOPS: tuple[VoltageStop, ...] = (
    VoltageStop(400, "#ef4444", "≥ 400 kV"),
    VoltageStop(220, "#f97316", "220–399 kV"),
    VoltageStop(110, "#f59e0b", "110–219 kV"),
    VoltageStop(60, "#84cc16", "60–109 kV"),
    VoltageStop(30, "#14b8a6", "30–59 kV"),
    VoltageStop(10, "#0ea5e9", "10–29 kV"),
    VoltageStop(0, "#8b5cf6", "< 10 kV"),
)

LINE_SYMBOLOGY: dict[str, tuple[str, float]] = {
    "telecoms_communication_line": ("#38bdf8", 2.0),
    "petroleum_pipeline": ("#f59e0b", 2.5),
    "other_pipeline": ("#a78bfa", 2.0),
    "water_pipeline": ("#06b6d4", 2.5),
    "pressurised_waterway": ("#22d3ee", 2.0),
    "power_portal_way": ("#2dd4bf", 2.0),
}

POLYGON_SYMBOLOGY: dict[str, tuple[str, str]] = {
    "power_substation": ("#f97316", "255,115,22,40"),
    "power_plant": ("#facc15", "255,204,21,46"),
    "power_generator_area": ("#fde047", "253,224,71,46"),
    "telecoms_data_center": ("#38bdf8", "56,189,248,40"),
    "petroleum_site": ("#f59e0b", "245,158,11,40"),
    "water_treatment_plant_polygon": ("#06b6d4", "6,182,212,40"),
    "wastewater_plant_polygon": ("#0891b2", "8,145,178,40"),
    "water_reservoir": ("#0ea5e9", "14,165,233,46"),
    "pumping_station_polygon": ("#14b8a6", "20,184,166,40"),
}

POINT_SYMBOLOGY: dict[str, tuple[str, float]] = {
    "power_tower": ("#111827", 3.2),
    "power_substation_point": ("#f97316", 4.0),
    "power_plant_point": ("#facc15", 4.0),
    "power_generator": ("#eab308", 3.6),
    "power_transformer": ("#6366f1", 3.4),
    "power_compensator": ("#64748b", 3.4),
    "power_switch": ("#475569", 3.2),
    "power_heatmap_solar": ("#facc15", 3.0),
    "telecoms_data_center_point": ("#38bdf8", 3.6),
    "telecoms_mast": ("#0ea5e9", 3.2),
    "telecoms_antenna": ("#0284c7", 2.8),
    "telecoms_cabinet": ("#7dd3fc", 2.8),
    "petroleum_well": ("#f59e0b", 3.2),
    "water_treatment_plant_point": ("#06b6d4", 3.6),
    "wastewater_plant_point": ("#0891b2", 3.6),
    "water_reservoir_point": ("#0ea5e9", 3.2),
    "water_tower": ("#22d3ee", 3.2),
    "water_well": ("#67e8f9", 2.8),
    "pumping_station_point": ("#14b8a6", 3.2),
    "water_cabinet": ("#5eead4", 2.8),
}

FALLBACK_LINE = ("#2dd4bf", 2.0)
FALLBACK_POLYGON = ("#2dd4bf", "45,212,191,40")
FALLBACK_POINT = ("#2dd4bf", 3.2)

POWER_LINE_LABEL_EXPRESSION = (
    'coalesce("name", "ref", '
    'if(coalesce("voltage", 0) > 0, concat(to_string("voltage"), \' kV\'), NULL))'
)

NAME_LABEL_EXPRESSION = 'coalesce("name", "ref")'

LABEL_MIN_ZOOM = 13
