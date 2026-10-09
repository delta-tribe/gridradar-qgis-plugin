# -*- coding: utf-8 -*-
"""Feature attribute panel for GridRadar MVT layers."""

from __future__ import annotations

from qgis.PyQt.QtCore import Qt, QUrl
from qgis.PyQt.QtGui import QDesktopServices, QFont
from qgis.PyQt.QtWidgets import (
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ..core.mvt.feature_details import FeatureDetails
from .dialog_utils import configure_plugin_dialog


class FeatureDetailDialog(QDialog):
    """Show formatted OpenInfraMap feature attributes."""

    def __init__(
        self,
        details: FeatureDetails,
        *,
        theme_source=None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Dettaglio elemento")
        configure_plugin_dialog(self, theme_source=theme_source)

        title = QLabel(details.title)
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(11)
        title.setFont(title_font)
        title.setWordWrap(True)

        subtitle = QLabel(details.subtitle)
        subtitle.setStyleSheet("color: palette(mid);")
        subtitle.setWordWrap(True)

        form_host = QWidget()
        form = QFormLayout(form_host)
        form.setLabelAlignment(Qt.AlignLeft | Qt.AlignTop)
        form.setFormAlignment(Qt.AlignTop)
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(8)

        for row in details.rows:
            label = QLabel(row.label)
            label.setWordWrap(True)
            if row.href:
                value = QPushButton(row.value)
                value.setFlat(True)
                value.setCursor(Qt.PointingHandCursor)
                value.setStyleSheet("text-align: left; color: palette(link);")
                value.clicked.connect(lambda _checked=False, href=row.href: self._open_link(href))
            else:
                value = QLabel(row.value)
                value.setWordWrap(True)
                value.setTextInteractionFlags(Qt.TextSelectableByMouse)
            form.addRow(label, value)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        scroll.setWidget(form_host)

        close_button = QPushButton("Chiudi")
        close_button.clicked.connect(self.accept)
        footer = QHBoxLayout()
        footer.addStretch()
        footer.addWidget(close_button)

        layout = QVBoxLayout(self)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(scroll, stretch=1)
        layout.addLayout(footer)
        self.resize(420, 480)

    @staticmethod
    def _open_link(href: str) -> None:
        QDesktopServices.openUrl(QUrl(href))
