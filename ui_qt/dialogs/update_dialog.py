# -*- coding: utf-8 -*-
"""
Update Notification Dialog for LET IT DIE Save Editor (PySide6 Edition).
Displays changelog, version comparisons, and one-click GitHub/Git updates.
"""

import threading
from PySide6.QtCore import Qt, QObject, Signal
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTextEdit, QFrame, QMessageBox
)

import updater
import i18n
from i18n import t
from ui_qt.theme import ACCENT_GOLD, ACCENT_CYAN, BG_DARK, BG_CARD, BG_PANEL, FG_MUTED, FG_MAIN


class _UpdateResultDispatcher(QObject):
    sig_result = Signal(bool, str)

    def __init__(self, callback):
        super().__init__()
        self.sig_result.connect(callback)


class QtUpdateNotificationDialog(QDialog):
    """Visual dialog to notify the user about a new update and let them install it with 1 click."""

    def __init__(self, parent, remote_info, on_update_complete=None):
        super().__init__(parent)
        self.main_win = parent
        self.remote_info = remote_info or {}
        self.on_update_complete = on_update_complete

        self.setWindowTitle(t("updater_avail_title", default="⚡ Actualización Disponible - Let It Die Save Editor"))
        self.resize(560, 460)
        self.setMinimumSize(480, 380)
        self.setStyleSheet(f"background-color: {BG_DARK}; color: {FG_MAIN};")

        self._dispatcher = _UpdateResultDispatcher(self._on_update_finished)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        local_info = updater.get_local_version_info()
        loc_v = local_info.get("version", updater.CURRENT_VERSION)
        rem_v = self.remote_info.get("version", "Nueva")
        rel_date = self.remote_info.get("release_date", "")

        # Header Frame
        header = QFrame()
        header.setStyleSheet(f"background-color: {BG_PANEL}; border-radius: 6px; padding: 10px;")
        h_layout = QVBoxLayout(header)
        h_layout.setContentsMargins(10, 8, 10, 8)
        h_layout.setSpacing(4)

        lbl_header = QLabel(t("updater_avail_header", default="¡Nueva versión disponible para descargar!"))
        lbl_header.setStyleSheet(f"color: {ACCENT_GOLD}; font-size: 12pt; font-weight: bold;")
        h_layout.addWidget(lbl_header)

        sub_text = t("updater_current_vs_new", current=loc_v, remote=rem_v)
        if rel_date:
            sub_text += f"  ({rel_date})"
        lbl_sub = QLabel(sub_text)
        lbl_sub.setStyleSheet("color: #ffffff; font-size: 9pt;")
        h_layout.addWidget(lbl_sub)
        layout.addWidget(header)

        # Changelog Section
        lbl_cl = QLabel(t("updater_changelog_title", default="Registro de Cambios (Novedades):"))
        lbl_cl.setStyleSheet(f"color: {ACCENT_CYAN}; font-size: 10pt; font-weight: bold;")
        layout.addWidget(lbl_cl)

        self.txt_changelog = QTextEdit()
        self.txt_changelog.setReadOnly(True)
        self.txt_changelog.setStyleSheet(
            f"background-color: {BG_PANEL}; color: #f0f2f5; "
            "border: 1px solid #252b40; border-radius: 6px; "
            "padding: 8px; font-family: 'Segoe UI'; font-size: 9pt;"
        )

        changelog = self.remote_info.get("changelog", [])
        if changelog:
            formatted_cl = "\n\n".join(f"• {item}" for item in changelog)
        else:
            formatted_cl = t("updater_default_changelog", default="• Correcciones de estabilidad y mejoras generales del sistema.")
        self.txt_changelog.setPlainText(formatted_cl)
        layout.addWidget(self.txt_changelog, stretch=1)

        # Safe update notice / Status label
        self.status_lbl = QLabel(t("updater_safe_notice", default="La actualización preserva todas tus partidas, copias de seguridad y configuraciones."))
        self.status_lbl.setStyleSheet(f"color: {FG_MUTED}; font-size: 8.5pt;")
        self.status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_lbl.setWordWrap(True)
        layout.addWidget(self.status_lbl)

        # Buttons Bar
        btn_bar = QHBoxLayout()
        btn_bar.setSpacing(10)
        btn_bar.addStretch()

        self.btn_later = QPushButton(t("updater_btn_later", default="Más Tarde"))
        self.btn_later.setFixedWidth(110)
        self.btn_later.setFixedHeight(32)
        self.btn_later.setStyleSheet(
            "QPushButton {"
            "   background-color: #252b40; color: #ffffff; font-weight: bold;"
            "   border: 1px solid #363d59; border-radius: 4px; padding: 4px;"
            "}"
            "QPushButton:hover { background-color: #31374a; }"
        )
        self.btn_later.clicked.connect(self.reject)
        btn_bar.addWidget(self.btn_later)

        self.btn_update = QPushButton(t("updater_btn_now", default="⚡ Actualizar Ahora"))
        self.btn_update.setFixedWidth(160)
        self.btn_update.setFixedHeight(32)
        self.btn_update.setStyleSheet(
            f"QPushButton {{"
            f"   background-color: {ACCENT_GOLD}; color: #121212; font-weight: bold;"
            f"   border: 1px solid #d48810; border-radius: 4px; padding: 4px;"
            f"}}"
            f"QPushButton:hover {{ background-color: #f5b041; }}"
            f"QPushButton:disabled {{ background-color: #555555; color: #888888; }}"
        )
        self.btn_update.clicked.connect(self._start_update_action)
        btn_bar.addWidget(self.btn_update)

        layout.addLayout(btn_bar)

    def _start_update_action(self):
        self.btn_update.setEnabled(False)
        self.btn_update.setText("⏳ Actualizando...")
        self.status_lbl.setText("Descargando los últimos cambios desde GitHub...")
        self.status_lbl.setStyleSheet(f"color: {ACCENT_GOLD}; font-size: 8.5pt; font-weight: bold;")

        def run_upd():
            ok, msg = updater.perform_update_git()
            self._dispatcher.sig_result.emit(ok, msg)

        threading.Thread(target=run_upd, daemon=True).start()

    def _on_update_finished(self, ok, msg):
        if ok:
            if msg == "BROWSER_OPENED":
                info_msg = t("updater_browser_opened", default="Se ha abierto la página de descargas en tu navegador web para obtener el instalador más reciente.")
            else:
                info_msg = t("updater_success", default="¡Editor actualizado con éxito!\nPor favor reinicia la aplicación para disfrutar de los cambios.")
            
            QMessageBox.information(self, t("notice", default="Aviso"), info_msg)
            self.accept()
            if self.on_update_complete:
                self.on_update_complete()
        else:
            self.btn_update.setEnabled(True)
            self.btn_update.setText("Reintentar")
            self.status_lbl.setText("Error al actualizar. Revisa la consola o tu conexión.")
            self.status_lbl.setStyleSheet("color: #e74c3c; font-size: 8.5pt; font-weight: bold;")
            err_text = t("updater_error", default=f"No se pudo completar la actualización automática:\n\n{msg}", error=msg)
            QMessageBox.critical(self, t("error", default="Error"), err_text)
