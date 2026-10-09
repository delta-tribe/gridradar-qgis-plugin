"""Build Qgs map layers from GridRadar connection descriptors."""

from __future__ import annotations

from typing import Any, Callable

from qgis.core import QgsMapLayer, QgsProject

from .arcgis import build_arcgis_feature_layer, build_arcgis_image_layer
from .geojson import build_geojson_layer
from .mvt import build_mvt_layer
from .wms import build_wms_layer
from .xyz import build_osm_layer, build_xyz_layer


def build_map_layer(
    descriptor: dict[str, Any],
    *,
    api_base: str,
    token: str,
    org_id: int | None,
) -> QgsMapLayer | None:
    """Create a Qgs layer from a catalog resolve descriptor."""
    provider = descriptor.get("qgis_provider")
    builders: dict[str, Callable[..., QgsMapLayer | None]] = {
        "wms": build_wms_layer,
        "arcgisfeatureserver": build_arcgis_feature_layer,
        "arcgismapserver": build_arcgis_image_layer,
        "ogr": build_geojson_layer,
        "vectortile": build_mvt_layer,
    }

    if descriptor.get("catalog_type") == "osm":
        return build_osm_layer(descriptor)

    if provider == "wms" and descriptor.get("catalog_type") == "xyz":
        return build_xyz_layer(descriptor, api_base=api_base, token=token, org_id=org_id)

    builder = builders.get(str(provider))
    if builder is None:
        return None

    return builder(
        descriptor,
        api_base=api_base,
        token=token,
        org_id=org_id,
    )

def insert_layer_in_group(
    layer: QgsMapLayer,
    group_name: str,
    *,
    opacity: float | None = None,
) -> QgsMapLayer:
    """Add a layer to the project inside a named tree group."""
    if opacity is not None:
        layer.setOpacity(float(opacity))

    root = QgsProject.instance().layerTreeRoot()
    group = root.findGroup(group_name)
    if group is None:
        group = root.addGroup(group_name)

    QgsProject.instance().addMapLayer(layer, addToLegend=False)
    group.insertLayer(0, layer)
    return layer
