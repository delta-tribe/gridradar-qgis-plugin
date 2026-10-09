"""SINFI WMS GetCapabilities parser."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any

WMS_NS = {
    "wms": "http://www.opengis.net/wms",
}


def parse_wms_capabilities(xml_text: str) -> list[dict[str, Any]]:
    """Parse WMS 1.3.0 capabilities and return layer metadata."""
    root = ET.fromstring(xml_text)
    layers: list[dict[str, Any]] = []

    for layer_el in root.findall(".//wms:Layer", WMS_NS):
        name_el = layer_el.find("wms:Name", WMS_NS)
        if name_el is None or not (name_el.text or "").strip():
            continue

        title_el = layer_el.find("wms:Title", WMS_NS)
        abstract_el = layer_el.find("wms:Abstract", WMS_NS)
        queryable = layer_el.attrib.get("queryable") == "1"
        styles = []
        for style_el in layer_el.findall("wms:Style", WMS_NS):
            style_name_el = style_el.find("wms:Name", WMS_NS)
            style_title_el = style_el.find("wms:Title", WMS_NS)
            if style_name_el is None or not (style_name_el.text or "").strip():
                continue
            styles.append(
                {
                    "name": style_name_el.text.strip(),
                    "title": (style_title_el.text or style_name_el.text or "").strip(),
                }
            )

        layers.append(
            {
                "name": name_el.text.strip(),
                "title": (title_el.text or name_el.text or "").strip(),
                "abstract": (abstract_el.text or "").strip() or None,
                "queryable": queryable,
                "styles": styles,
            }
        )

    return layers
