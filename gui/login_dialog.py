# -*- coding: utf-8 -*-
"""GridRadar login dialog."""

from __future__ import annotations

from qgis.PyQt.QtCore import pyqtSignal
from qgis.PyQt.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from ..core.auth_store import DEFAULT_API_BASE
from .dialog_utils import configure_plugin_dialog


class LoginDialog(QDialog):
    """Collect GridRadar credentials; API base URL is optional advanced setting."""

    login_accepted = pyqtSignal()

    def __init__(self, parent=None, *, theme_source=None) -> None:
        super().__init__(parent)
        configure_plugin_dialog(self, theme_source=theme_source)
        self.setWindowTitle("Accesso GridRadar")
        self.setMinimumWidth(420)

        self.api_base_edit = QLineEdit(DEFAULT_API_BASE)
        self.identifier_edit = QLineEdit()
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.status_label = QLabel("")

        form = QFormLayout()
        form.addRow("Utente o email", self.identifier_edit)
        form.addRow("Password", self.password_edit)

        self._advanced_container = QWidget()
        advanced_form = QFormLayout(self._advanced_container)
        advanced_form.setContentsMargins(0, 0, 0, 0)
        advanced_form.addRow("URL API", self.api_base_edit)
        self._advanced_container.setVisible(False)

        self._advanced_toggle = QLabel(
            '<a href="toggle">Impostazioni avanzate</a>'
        )
        self._advanced_toggle.setOpenExternalLinks(False)
        self._advanced_toggle.linkActivated.connect(self._toggle_advanced)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self._advanced_container)
        layout.addWidget(self._advanced_toggle)
        layout.addWidget(self.status_label)
        layout.addWidget(buttons)

    def _toggle_advanced(self, _link: str = "") -> None:
        self._set_advanced_visible(not self._advanced_container.isVisible())

    def _set_advanced_visible(self, visible: bool) -> None:
        self._advanced_container.setVisible(visible)
        label = "Nascondi impostazioni avanzate" if visible else "Impostazioni avanzate"
        self._advanced_toggle.setText(f'<a href="toggle">{label}</a>')

    def set_api_base_value(self, value: str) -> None:
        self.api_base_edit.setText(value)
        if value.rstrip("/") != DEFAULT_API_BASE:
            self._set_advanced_visible(True)

    def set_status(self, message: str) -> None:
        self.status_label.setText(message)

    def api_base(self) -> str:
        return self.api_base_edit.text().strip().rstrip("/") or DEFAULT_API_BASE

    def identifier(self) -> str:
        return self.identifier_edit.text().strip()

    def password(self) -> str:
        return self.password_edit.text()
