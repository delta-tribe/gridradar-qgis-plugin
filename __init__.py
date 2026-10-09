# -*- coding: utf-8 -*-
"""GridRadar QGIS plugin entry point."""


def classFactory(iface):
    """QGIS plugin factory."""
    from .main_plugin import GridRadarPlugin

    return GridRadarPlugin(iface)
