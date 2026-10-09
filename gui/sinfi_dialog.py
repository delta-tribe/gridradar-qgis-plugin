# -*- coding: utf-8 -*-
"""SINFI connection dialog."""

from __future__ import annotations

from qgis.PyQt.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
)

from .dialog_utils import configure_plugin_dialog


class SinfiDialog(QDialog):
    """Collect SINFI credentials and target group."""

    def __init__(self, parent=None, *, theme_source=None) -> None:
        super().__init__(parent)
        configure_plugin_dialog(self, theme_source=theme_source)
        self.setWindowTitle("Integrazione SINFI")
        self.setMinimumWidth(420)

        self.username_edit = QLineEdit()
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.group_combo = QComboBox()
        self.status_label = QLabel("")

        form = QFormLayout()
        form.addRow("Utente SINFI", self.username_edit)
        form.addRow("Password", self.password_edit)
        form.addRow("Gruppo", self.group_combo)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Collega le credenziali SINFI personali per abilitare i layer WMS."))
        layout.addLayout(form)
        layout.addWidget(self.status_label)
        layout.addWidget(buttons)

    def set_status(self, message: str) -> None:
        self.status_label.setText(message)

    def set_groups(self, codes: list[str], names: list[str]) -> None:
        self.group_combo.clear()
        for code, name in zip(codes, names):
            label = f"{name} ({code})" if name else code
            self.group_combo.addItem(label, code)

    def username(self) -> str:
        return self.username_edit.text().strip()

    def password(self) -> str:
        return self.password_edit.text()

    def group_code(self) -> str:
        return str(self.group_combo.currentData() or "")

    def group_name(self) -> str:
        return self.group_combo.currentText()
