# -*- coding: utf-8 -*-
"""Shared QGIS dialog window configuration."""

from __future__ import annotations

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QPalette
from qgis.PyQt.QtWidgets import QApplication, QDialog, QWidget


def _theme_palette(theme_source: QWidget | None = None) -> QPalette:
    """Return the active QGIS palette (dark or light)."""
    if theme_source is not None:
        return theme_source.palette()
    app = QApplication.instance()
    if app is not None:
        return app.palette()
    return QPalette()


def configure_plugin_dialog(dialog: QDialog, *, theme_source: QWidget | None = None) -> None:
    """Render plugin dialogs opaque and readable, matching the QGIS UI theme."""
    dialog.setModal(True)
    dialog.setWindowFlags(
        Qt.Dialog | Qt.WindowStaysOnTopHint | Qt.WindowTitleHint | Qt.WindowCloseButtonHint
    )
    dialog.setAttribute(Qt.WA_TranslucentBackground, False)
    dialog.setAutoFillBackground(True)

    palette = _theme_palette(theme_source)
    dialog.setPalette(palette)

    # Only style the dialog shell; child widgets keep native themed rendering.
    window = palette.color(QPalette.Window)
    dialog.setStyleSheet(f"QDialog {{ background-color: {window.name()}; }}")
