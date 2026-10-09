"""Pick OpenInfraMap MVT features at a map location."""

from __future__ import annotations

from qgis.core import (
    QgsGeometry,
    QgsPointXY,
    QgsProject,
    QgsSelectionContext,
    QgsVectorTileLayer,
    QgsCoordinateTransform,
    QgsCoordinateReferenceSystem,
)

from .feature_details import FeatureDetails, build_feature_details


def _gridradar_mvt_layers(layer_ids: set[str]) -> list[QgsVectorTileLayer]:
    project = QgsProject.instance()
    layers: list[QgsVectorTileLayer] = []
    for qgis_id in layer_ids:
        layer = project.mapLayer(qgis_id)
        if not isinstance(layer, QgsVectorTileLayer):
            continue
        if layer.customProperty("gridradar_catalog_type") not in {"mvt", "mvt-heatmap"}:
            continue
        layers.append(layer)
    return layers


def _search_radius(map_scale: float) -> float:
    if map_scale <= 0:
        return 250.0
    if map_scale <= 5_000:
        return 40.0
    if map_scale <= 25_000:
        return 120.0
    if map_scale <= 100_000:
        return 250.0
    return 600.0


def identify_mvt_feature(
    point: QgsPointXY,
    *,
    canvas_crs,
    map_scale: float,
    tracked_qgis_ids: set[str],
) -> tuple[QgsVectorTileLayer, FeatureDetails] | None:
    """Return the topmost GridRadar MVT feature near point, if any."""
    layers = _gridradar_mvt_layers(tracked_qgis_ids)
    if not layers:
        return None

    target_crs = QgsCoordinateReferenceSystem("EPSG:3857")
    transformed = QgsPointXY(point)
    if canvas_crs.isValid() and canvas_crs != target_crs:
        transform = QgsCoordinateTransform(canvas_crs, target_crs, QgsProject.instance())
        transformed = transform.transform(point)

    radius = _search_radius(map_scale)
    search_geom = QgsGeometry.fromPointXY(transformed).buffer(radius, 8)
    context = QgsSelectionContext()
    context.setScale(map_scale if map_scale > 0 else 50_000)

    for layer in reversed(layers):
        layer.removeSelection()
        layer.selectByGeometry(search_geom, context)
        if layer.selectedFeatureCount() <= 0:
            continue

        feature = layer.selectedFeatures()[0]
        catalog_name = str(layer.customProperty("gridradar_catalog_name") or layer.name())
        details = build_feature_details(feature, catalog_layer_name=catalog_name)
        layer.removeSelection()
        if details is None:
            continue
        return layer, details

    return None
