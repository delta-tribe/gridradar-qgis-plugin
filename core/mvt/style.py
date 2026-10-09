"""Apply OpenInfraMap-style symbology and labels to QgsVectorTileLayer."""

from __future__ import annotations

from qgis.core import (
    QgsFillSymbol,
    QgsLineSymbol,
    QgsMarkerSymbol,
    QgsPalLayerSettings,
    QgsTextFormat,
    QgsVectorTileBasicLabeling,
    QgsVectorTileBasicLabelingStyle,
    QgsVectorTileBasicRenderer,
    QgsVectorTileBasicRendererStyle,
    QgsVectorTileLayer,
    QgsWkbTypes,
)
from qgis.PyQt.QtGui import QColor

from .symbology_data import (
    FALLBACK_LINE,
    FALLBACK_POINT,
    FALLBACK_POLYGON,
    LABEL_MIN_ZOOM,
    LINE_SYMBOLOGY,
    NAME_LABEL_EXPRESSION,
    POINT_SYMBOLOGY,
    POLYGON_SYMBOLOGY,
    POWER_LINE_LABEL_EXPRESSION,
    POWER_LINE_VOLTAGE_STOPS,
)


def _line_style(layer_name: str, color: str, width: float) -> QgsVectorTileBasicRendererStyle:
    style = QgsVectorTileBasicRendererStyle()
    style.setLayerName(layer_name)
    style.setGeometryType(QgsWkbTypes.LineGeometry)
    style.setSymbol(
        QgsLineSymbol.createSimple({"color": color, "width": str(width), "capstyle": "round"})
    )
    return style


def _fill_style(layer_name: str, stroke: str, fill_rgba: str) -> QgsVectorTileBasicRendererStyle:
    style = QgsVectorTileBasicRendererStyle()
    style.setLayerName(layer_name)
    style.setGeometryType(QgsWkbTypes.PolygonGeometry)
    style.setSymbol(
        QgsFillSymbol.createSimple(
            {
                "color": fill_rgba,
                "outline_color": stroke,
                "outline_width": "0.6",
            }
        )
    )
    return style


def _point_style(layer_name: str, color: str, size: float) -> QgsVectorTileBasicRendererStyle:
    style = QgsVectorTileBasicRendererStyle()
    style.setLayerName(layer_name)
    style.setGeometryType(QgsWkbTypes.PointGeometry)
    style.setSymbol(
        QgsMarkerSymbol.createSimple(
            {
                "color": color,
                "size": str(size),
                "outline_color": "white",
                "outline_width": "0.35",
            }
        )
    )
    return style


def _power_line_styles() -> list[QgsVectorTileBasicRendererStyle]:
    styles: list[QgsVectorTileBasicRendererStyle] = []
    for index, stop in enumerate(POWER_LINE_VOLTAGE_STOPS):
        style = QgsVectorTileBasicRendererStyle()
        style.setLayerName("power_line")
        style.setGeometryType(QgsWkbTypes.LineGeometry)
        if index == 0:
            expression = f'coalesce("voltage", 0) >= {stop.min_kv}'
        elif stop.min_kv == 0:
            expression = 'coalesce("voltage", 0) < 10'
        else:
            next_min = POWER_LINE_VOLTAGE_STOPS[index - 1].min_kv
            expression = (
                f'coalesce("voltage", 0) >= {stop.min_kv} '
                f'AND coalesce("voltage", 0) < {next_min}'
            )
        style.setFilterExpression(expression)
        style.setSymbol(
            QgsLineSymbol.createSimple(
                {"color": stop.color, "width": "2.5", "capstyle": "round"}
            )
        )
        styles.append(style)
    return styles


def _label_style(
    layer_name: str,
    geometry_type: QgsWkbTypes.GeometryType,
    expression: str,
    *,
    min_zoom: int = LABEL_MIN_ZOOM,
) -> QgsVectorTileBasicLabelingStyle:
    label = QgsVectorTileBasicLabelingStyle()
    label.setLayerName(layer_name)
    label.setGeometryType(geometry_type)
    label.setMinZoomLevel(min_zoom)

    settings = QgsPalLayerSettings()
    settings.fieldName = expression
    settings.isExpression = True
    text_format = QgsTextFormat()
    text_format.setColor(QColor("#202428"))
    text_format.setSize(9.0)
    text_format.buffer().setEnabled(True)
    text_format.buffer().setColor(QColor(255, 255, 255, 235))
    text_format.buffer().setSize(1.2)
    settings.setFormat(text_format)
    label.setLabelSettings(settings)
    return label


def apply_openinframap_style(
    layer: QgsVectorTileLayer,
    source_layers: list[str] | None,
) -> None:
    """Style an OpenInfraMap MVT layer with voltage colors, icons and labels."""
    active_layers = list(source_layers or [])
    renderer_styles: list[QgsVectorTileBasicRendererStyle] = []
    label_styles: list[QgsVectorTileBasicLabelingStyle] = []

    if "power_line" in active_layers:
        renderer_styles.extend(_power_line_styles())
        label_styles.append(
            _label_style("power_line", QgsWkbTypes.LineGeometry, POWER_LINE_LABEL_EXPRESSION)
        )

    for layer_name, (color, width) in LINE_SYMBOLOGY.items():
        if layer_name in active_layers and layer_name != "power_line":
            renderer_styles.append(_line_style(layer_name, color, width))

    for layer_name, (stroke, fill) in POLYGON_SYMBOLOGY.items():
        if layer_name in active_layers:
            renderer_styles.append(_fill_style(layer_name, stroke, fill))
            label_styles.append(
                _label_style(layer_name, QgsWkbTypes.PolygonGeometry, NAME_LABEL_EXPRESSION)
            )

    for layer_name, (color, size) in POINT_SYMBOLOGY.items():
        if layer_name in active_layers:
            renderer_styles.append(_point_style(layer_name, color, size))
            if layer_name not in {"power_heatmap_solar", "power_tower"}:
                label_styles.append(
                    _label_style(layer_name, QgsWkbTypes.PointGeometry, NAME_LABEL_EXPRESSION)
                )

    for layer_name in active_layers:
        if any(s.layerName() == layer_name for s in renderer_styles):
            continue
        if layer_name.endswith("_line") or layer_name.endswith("_way") or "pipeline" in layer_name:
            color, width = FALLBACK_LINE
            renderer_styles.append(_line_style(layer_name, color, width))
        elif layer_name.endswith("_point") or layer_name.endswith("_tower") or layer_name.endswith("_mast"):
            color, size = FALLBACK_POINT
            renderer_styles.append(_point_style(layer_name, color, size))
        else:
            stroke, fill = FALLBACK_POLYGON
            renderer_styles.append(_fill_style(layer_name, stroke, fill))

    if not renderer_styles:
        return

    renderer = QgsVectorTileBasicRenderer()
    renderer.setStyles(renderer_styles)
    layer.setRenderer(renderer)

    if label_styles:
        labeling = QgsVectorTileBasicLabeling()
        labeling.setStyles(label_styles)
        layer.setLabeling(labeling)
        layer.setLabelsEnabled(True)
