"""Format OpenInfraMap MVT attributes for the feature detail panel."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote

from qgis.core import QgsFeature

SOURCE_LAYER_LABELS: dict[str, str] = {
    "power_line": "Linea elettrica",
    "power_tower": "Traliccio",
    "power_portal_way": "Portale",
    "power_substation": "Sottostazione",
    "power_substation_point": "Sottostazione",
    "power_plant": "Centrale elettrica",
    "power_plant_point": "Centrale elettrica",
    "power_generator": "Generatore",
    "power_generator_area": "Generatore",
    "power_transformer": "Trasformatore",
    "power_compensator": "Compensatore",
    "power_switch": "Interruttore",
    "telecoms_communication_line": "Linea telecomunicazioni",
    "telecoms_data_center": "Data center",
    "telecoms_data_center_point": "Data center",
    "telecoms_mast": "Traliccio telecom",
    "telecoms_antenna": "Antenna",
    "telecoms_cabinet": "Armadio stradale",
    "petroleum_pipeline": "Condotta petrolifera",
    "petroleum_well": "Pozzo petrolifero",
    "petroleum_site": "Impianto petrolifero",
    "other_pipeline": "Condotta",
    "water_pipeline": "Condotta idrica",
    "pressurised_waterway": "Canale pressurizzato",
    "water_treatment_plant_polygon": "Impianto trattamento acqua",
    "water_treatment_plant_point": "Impianto trattamento acqua",
    "wastewater_plant_polygon": "Depuratore",
    "wastewater_plant_point": "Depuratore",
    "water_reservoir": "Bacino idrico",
    "water_reservoir_point": "Bacino idrico",
    "water_tower": "Torre idrica",
    "water_well": "Pozzo",
    "pumping_station_polygon": "Stazione di pompaggio",
    "pumping_station_point": "Stazione di pompaggio",
    "water_cabinet": "Armadio idrico",
}

PROPERTY_LABELS: dict[str, str] = {
    "name": "Nome",
    "name_it": "Nome (IT)",
    "ref": "Riferimento",
    "type": "Tipo",
    "line": "Linea",
    "voltage": "Tensione",
    "voltage_2": "Tensione 2",
    "voltage_3": "Tensione 3",
    "voltage_4": "Tensione 4",
    "voltage_primary": "Tensione primaria",
    "voltage_secondary": "Tensione secondaria",
    "voltage_tertiary": "Tensione terziaria",
    "frequency": "Frequenza",
    "circuits": "Circuiti",
    "operator": "Gestore",
    "output": "Potenza",
    "method": "Metodo",
    "source": "Fonte",
    "substance": "Sostanza",
    "diameter": "Diametro",
    "pressure": "Pressione",
    "material": "Materiale",
    "location": "Posizione",
    "substation": "Sottostazione",
    "rating": "Potenza nominale",
    "start_date": "Data avvio",
    "construction": "In costruzione",
    "disused": "Disuso",
    "tunnel": "Galleria",
    "usage": "Uso",
    "plant_role": "Ruolo impianto",
    "storage": "Accumulo",
    "osm_id": "OpenStreetMap",
    "url": "Scheda OSM",
    "wikidata": "Wikidata",
    "wikipedia": "Wikipedia",
    "area": "Area",
    "angle": "Angolo",
}

PROPERTY_ORDER: list[str] = [
    "name",
    "name_it",
    "ref",
    "type",
    "line",
    "voltage",
    "voltage_2",
    "voltage_3",
    "voltage_4",
    "voltage_primary",
    "voltage_secondary",
    "voltage_tertiary",
    "frequency",
    "circuits",
    "output",
    "method",
    "source",
    "substance",
    "diameter",
    "pressure",
    "material",
    "location",
    "substation",
    "operator",
    "rating",
    "usage",
    "plant_role",
    "storage",
    "construction",
    "disused",
    "tunnel",
    "start_date",
    "osm_id",
    "url",
    "wikidata",
    "wikipedia",
    "area",
    "angle",
]

SKIP_PROPERTIES = {
    "tile_layer",
    "tile_zoom",
    "layer",
    "geometry",
    "is_node",
    "ref_len",
    "mvt_id_field",
}

LOCALIZED_NAME_KEYS = tuple(f"name_{code}" for code in ("it", "en", "de", "fr", "es"))


@dataclass(frozen=True)
class FeatureDetailRow:
    label: str
    value: str
    href: str | None = None


@dataclass(frozen=True)
class FeatureDetails:
    title: str
    subtitle: str
    rows: list[FeatureDetailRow]


def get_mvt_source_layer(feature: QgsFeature) -> str | None:
    for key in ("tile_layer", "layer"):
        value = feature.attribute(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return None


def _source_layer_label(source_layer: str) -> str:
    return SOURCE_LAYER_LABELS.get(source_layer, source_layer.replace("_", " "))


def _property_label(key: str) -> str:
    return PROPERTY_LABELS.get(key, key.replace("_", " "))


def _normalize_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _format_property_value(key: str, value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return "Sì" if value else None
    if isinstance(value, float):
        if not (value == value):  # NaN
            return None
        value = int(value) if value.is_integer() else value
    if isinstance(value, int):
        if key == "voltage" or key.startswith("voltage"):
            return f"{value} kV"
        if key == "output":
            return f"{value} MW"
        if key == "area":
            if value >= 1_000_000:
                return f"{value / 1_000_000:.2f} km²"
            if value >= 10_000:
                return f"{value / 10_000:.2f} ha"
            return f"{value} m²"
        if key == "angle":
            return f"{value}°"
        if key == "frequency":
            return f"{value} Hz"
        return str(value)

    text = _normalize_text(value)
    if not text or text.lower() == "null":
        return None
    if key == "frequency" and text.isdigit():
        return f"{text} Hz"
    return text


def _osm_url(osm_id: Any, is_node: Any) -> str | None:
    try:
        numeric_id = int(osm_id)
    except (TypeError, ValueError):
        return None
    if numeric_id <= 0:
        return None
    path = "node" if is_node is True else "way"
    return f"https://www.openstreetmap.org/{path}/{numeric_id}"


def _sort_property_keys(keys: list[str]) -> list[str]:
    def sort_key(name: str) -> tuple[int, str]:
        try:
            return (PROPERTY_ORDER.index(name), name)
        except ValueError:
            return (len(PROPERTY_ORDER), name)

    return sorted(keys, key=sort_key)


def build_feature_details(
    feature: QgsFeature,
    *,
    source_layer: str | None = None,
    catalog_layer_name: str,
) -> FeatureDetails | None:
    source_layer = source_layer or get_mvt_source_layer(feature)
    if not source_layer:
        return None

    attributes = {
        field.name(): feature.attribute(field.name())
        for field in feature.fields()
        if field.name() not in SKIP_PROPERTIES
    }

    feature_type_label = _source_layer_label(source_layer)
    name = _normalize_text(attributes.get("name") or "")
    if not name:
        for key in LOCALIZED_NAME_KEYS:
            name = _normalize_text(attributes.get(key) or "")
            if name:
                break
    ref = _normalize_text(attributes.get("ref") or "")
    title = name or ref or feature_type_label

    rows: list[FeatureDetailRow] = []
    for key in _sort_property_keys(list(attributes.keys())):
        if key in SKIP_PROPERTIES or (key.startswith("name_") and key != "name_it"):
            continue
        formatted = _format_property_value(key, attributes[key])
        if not formatted:
            continue

        href: str | None = None
        if key == "osm_id":
            href = _osm_url(attributes.get("osm_id"), attributes.get("is_node"))
        elif key == "url" and formatted.startswith("http"):
            href = formatted
        elif key == "wikidata" and formatted:
            href = f"https://www.wikidata.org/wiki/{formatted}"
        elif key == "wikipedia" and ":" in formatted:
            language, article = formatted.split(":", 1)
            if language and article:
                href = f"https://{language}.wikipedia.org/wiki/{quote(article)}"

        rows.append(FeatureDetailRow(_property_label(key), formatted, href))

    if not any(row.label == _property_label("type") for row in rows):
        rows.insert(0, FeatureDetailRow("Tipo elemento", feature_type_label))

    return FeatureDetails(title=title, subtitle=catalog_layer_name, rows=rows)
