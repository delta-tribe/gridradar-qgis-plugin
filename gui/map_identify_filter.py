# -*- coding: utf-8 -*-
"""Detect map clicks for GridRadar MVT feature inspection."""

from __future__ import annotations

from qgis.PyQt.QtCore import QObject, QPoint, Qt, pyqtSignal
from qgis.PyQt.QtGui import QMouseEvent
from qgis.PyQt.QtWidgets import QApplication
from qgis.core import QgsPointXY
from qgis.gui import QgsMapCanvas


class MapIdentifyFilter(QObject):
    """Emit canvas map points on simple left clicks (not pans)."""

    map_clicked = pyqtSignal(QgsPointXY)

    _DRAG_THRESHOLD_PX = 6

    def __init__(self, canvas: QgsMapCanvas, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._canvas = canvas
        self._press_pos: QPoint | None = None
        self._enabled = False
        canvas.installEventFilter(self)

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = enabled
        if not enabled:
            self._press_pos = None

    def eventFilter(self, watched: QObject, event) -> bool:  # noqa: N802
        if not self._enabled or watched is not self._canvas:
            return False

        if event.type() == QMouseEvent.MouseButtonPress and event.button() == Qt.LeftButton:
            self._press_pos = event.pos()
            return False

        if event.type() == QMouseEvent.MouseButtonRelease and event.button() == Qt.LeftButton:
            if self._press_pos is None:
                return False
            if (event.pos() - self._press_pos).manhattanLength() > self._DRAG_THRESHOLD_PX:
                self._press_pos = None
                return False
            self._press_pos = None
            if QApplication.mouseButtons() & Qt.LeftButton:
                return False
            map_point = self._canvas.getCoordinateTransform().toMapCoordinates(event.pos())
            self.map_clicked.emit(map_point)
            return False

        return False
