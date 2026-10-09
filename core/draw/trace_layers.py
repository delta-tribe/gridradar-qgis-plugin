"""Build styled QGIS vector layers from GridRadar draw traces."""

from __future__ import annotations

import json
from typing import Any

from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsFillSymbol,
    QgsLineSymbol,
    QgsMarkerSymbol,
    QgsSingleSymbolRenderer,
    QgsVectorLayer,
)
from qgis.PyQt.QtGui import QColor


def _parse_color(hex_color: str | None) -> QColor:
    color = QColor(str(hex_color or "#0d9488"))
    if not color.isValid():
        color = QColor("#0d9488")
    return color


def _geometry_type_name(geometry: dict[str, Any]) -> str:
    geom_type = str(geometry.get("type") or "").lower()
    if geom_type == "point":
        return "Point"
    if geom_type in {"linestring", "multilinestring"}:
        return "LineString"
    if geom_type in {"polygon", "multipolygon"}:
        return "Polygon"
    return "Unknown"


def build_trace_layer(trace: dict[str, Any]) -> QgsVectorLayer | None:
    """Create a QgsVectorLayer for a single draw trace."""
    geometry = trace.get("geometry")
    if not isinstance(geometry, dict) or not geometry.get("type"):
        return None

    feature = {
        "type": "Feature",
        "geometry": geometry,
        "properties": {
            "name": trace.get("name", ""),
            "comment": trace.get("comment", ""),
            "kind": trace.get("kind", ""),
            "measure_label": trace.get("measure_label") or "",
        },
    }
    collection = {
        "type": "FeatureCollection",
        "name": trace.get("name", ""),
        "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
        "features": [feature],
    }
    layer = QgsVectorLayer(
        json.dumps(collection),
        str(trace.get("name") or f"Traccia {trace.get('id')}"),
        "ogr",
    )
    if not layer.isValid():
        return None

    layer.setCrs(QgsCoordinateReferenceSystem("EPSG:4326"))
    _apply_trace_style(layer, trace)
    return layer


def _apply_trace_style(layer: QgsVectorLayer, trace: dict[str, Any]) -> None:
    color = _parse_color(trace.get("color"))
    kind = str(trace.get("kind") or "")
    geometry = trace.get("geometry") if isinstance(trace.get("geometry"), dict) else {}
    geom_name = _geometry_type_name(geometry)

    if geom_name == "Point" or kind == "point":
        symbol = QgsMarkerSymbol.createSimple(
            {
                "name": "circle",
                "color": color.name(),
                "outline_color": color.darker(120).name(),
                "outline_width": "0.4",
                "size": "4",
            }
        )
    elif geom_name == "LineString" or kind in {"line", "measure-distance"}:
        symbol = QgsLineSymbol.createSimple(
            {
                "color": color.name(),
                "width": "2.2",
                "capstyle": "round",
            }
        )
    else:
        fill = QColor(color)
        fill.setAlpha(70)
        symbol = QgsFillSymbol.createSimple(
            {
                "color": fill.name(QColor.HexArgb),
                "outline_color": color.name(),
                "outline_width": "0.8",
            }
        )

    layer.setRenderer(QgsSingleSymbolRenderer(symbol))
