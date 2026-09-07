# -*- coding: utf-8 -*-
"""
Account Compatibility & Foreign Save Re-binding Dialog for LET IT DIE Save Editor (PySide6 Edition).
Exact layout, colors, and behavior parity with Cyberpunk Dark design.
"""

import os
import copy
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QGroupBox, QLabel, QLineEdit, QPushButton, QComboBox,
    QFileDialog, QFrame, QMessageBox, QCheckBox
)

import save_io
import core.save_slots as save_slots
import core.account_rebind as account_rebind
import i18n
from i18n import t
from ui_qt.theme import ACCENT_GOLD, ACCENT_CYAN, ACCENT_GREEN, ACCENT_RED, FG_MUTED, FG_MAIN


class AccountCompatibilityDialog(QDialog):
    def __init__(self, main_win):
        super().__init__(main_win)
        self.main_win = main_win
        self.active_save_dict = getattr(main_win, "save_json", None)
        self.active_save_path = getattr(main_win, "save_path", None)

        self.my_ident = account_rebind.detect_active_account_identity(
            active_save_dict=self.active_save_dict,
            active_save_path=self.active_save_path
        )
        self._src_data = None
        self._src_ident = None
        self._src_ver = 2

        self.setWindowTitle(t("rebind_dialog_title", default="Compatibilidad y Re-vinculación de Cuenta"))
        self.resize(780, 580)
        self.setMinimumSize(720, 520)
        self._build_ui()

    def _build_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(12, 12, 12, 12)
        root_layout.setSpacing(10)

        # Header
        header = QFrame()
        header.setStyleSheet("background-color: #151824; border-radius: 6px; padding: 10px;")
        h_v = QVBoxLayout(header)

        lbl_title = QLabel(f"🔄 {t('rebind_header_title', default='Herramienta de Re-vinculación y Compatibilidad de Partidas')}")
        lbl_title.setStyleSheet(f"color: {ACCENT_GOLD}; font-size: 12pt; font-weight: bold;")
        h_v.addWidget(lbl_title)

        lbl_sub = QLabel(t("rebind_header_sub", default="Permite usar partidas de otros usuarios vinculándolas automáticamente a tu cuenta de Steam."))
        lbl_sub.setStyleSheet(f"color: {FG_MUTED}; font-size: 9pt;")
        h_v.addWidget(lbl_sub)
        root_layout.addWidget(header)

        # Active User Info Frame
        box_my = QGroupBox(t("rebind_my_account_box", default="Tu Identidad de Steam Detectada"))
        my_layout = QHBoxLayout(box_my)
        steam_id = self.my_ident.get("steam_id", "No detectado")
        uid = self.my_ident.get("uid", "No detectado")
        lbl_my_info = QLabel(f"Steam ID: {steam_id}   |   UID Interno: {uid}")
        lbl_my_info.setStyleSheet(f"color: {ACCENT_CYAN}; font-weight: bold;")
        my_layout.addWidget(lbl_my_info)
        root_layout.addWidget(box_my)

        identity_form = QGridLayout()
        self.target_steam_entry = QLineEdit(self.my_ident.get("steam_id", ""))
        self.target_name_entry = QLineEdit(self.my_ident.get("player_name", ""))
        identity_form.addWidget(QLabel("Steam ID"), 0, 0)
        identity_form.addWidget(self.target_steam_entry, 0, 1)
        identity_form.addWidget(QLabel(t("rebind_target_name_lbl", default="Nombre")), 1, 0)
        identity_form.addWidget(self.target_name_entry, 1, 1)
        self.keep_name_cb = QCheckBox(t("rebind_keep_original_name", default="Conservar nombre original"))
        self.keep_name_cb.setChecked(False)
        self.harmonize_uid_cb = QCheckBox(t("rebind_harmonize_uid", default="Adaptar UID interno"))
        self.harmonize_uid_cb.setChecked(True)
        self.clear_tokens_cb = QCheckBox(t("rebind_clear_session", default="Limpiar sesión anterior"))
        self.clear_tokens_cb.setChecked(True)
        identity_form.addWidget(self.keep_name_cb, 2, 0, 1, 2)
        identity_form.addWidget(self.harmonize_uid_cb, 3, 0, 1, 2)
        identity_form.addWidget(self.clear_tokens_cb, 4, 0, 1, 2)
        root_layout.addLayout(identity_form)

        # Source File Selection Frame
        box_src = QGroupBox(t("rebind_src_file_box", default="Partida Externa a Re-vincular"))
        src_v = QVBoxLayout(box_src)
        src_row = QHBoxLayout()

        self.src_path_entry = QLineEdit()
        self.src_path_entry.setPlaceholderText("Selecciona un archivo .sav de otro usuario...")
        src_row.addWidget(self.src_path_entry)

        btn_browse = QPushButton(t("browse", default="Examinar..."))
        btn_browse.clicked.connect(self._browse_source_file)
        src_row.addWidget(btn_browse)

        btn_load = QPushButton(t("reload", default="Cargar"))
        btn_load.clicked.connect(lambda: self._load_source_file(self.src_path_entry.text()))
        src_row.addWidget(btn_load)
        src_v.addLayout(src_row)

        self.lbl_src_status = QLabel(t("rebind_no_file_loaded", default="Ningún archivo cargado."))
        self.lbl_src_status.setStyleSheet(f"color: {FG_MUTED}; font-size: 9pt;")
        src_v.addWidget(self.lbl_src_status)
        root_layout.addWidget(box_src)

        # Target Destination Frame
        box_dest = QGroupBox(t("rebind_target_box", default="Destino de la Partida Re-vinculada"))
        dest_v = QVBoxLayout(box_dest)

        dest_row = QHBoxLayout()
        dest_row.addWidget(QLabel(t("rebind_mode_lbl", default="Modo de Guardado:")))
        self.cb_dest_mode = QComboBox()
        self.cb_dest_mode.addItem(t("rebind_mode_steam", default="Aplicar directamente en Partida Activa de Steam"), "ACTIVE")
        self.cb_dest_mode.addItem(t("rebind_mode_slot", default="Guardar en una Ranura (Save Slot)"), "SLOT")
        self.cb_dest_mode.addItem(t("rebind_mode_file", default="Exportar a un Nuevo Archivo .sav"), "FILE")
        dest_row.addWidget(self.cb_dest_mode)

        self.cb_slot_num = QComboBox()
        for s in range(1, 11):
            self.cb_slot_num.addItem(f"{t('f_col_num', default='Ranura')} #{s}", s)
        dest_row.addWidget(self.cb_slot_num)
        dest_v.addLayout(dest_row)
        root_layout.addWidget(box_dest)

        # Action Buttons
        btn_bar = QHBoxLayout()
        self.btn_apply = QPushButton(t("rebind_apply_btn", default="🚀 Re-vincular y Activar Partida"))
        self.btn_apply.setProperty("accent", "true")
        self.btn_apply.clicked.connect(self._apply_rebind)
        btn_bar.addWidget(self.btn_apply)

        btn_bar.addStretch()
        btn_cancel = QPushButton(t("cancel", default="Cancelar"))
        btn_cancel.clicked.connect(self.reject)
        btn_bar.addWidget(btn_cancel)
        root_layout.addLayout(btn_bar)

    def _browse_source_file(self):
        f, _ = QFileDialog.getOpenFileName(self, t("rebind_file_dialog_title", default="Seleccionar Partida"), "", "Save Files (*.sav);;All Files (*.*)")
        if f:
            self.src_path_entry.setText(f)
            self._load_source_file(f)

    def _load_source_file(self, path):
        self._src_data = None
        self._src_ident = None
        if not path or not os.path.exists(path):
            self.lbl_src_status.setText(t("rebind_no_file_loaded", default="Ningún archivo cargado."))
            return
        try:
            data, ver = save_io.decompress_save(path)
            self._src_data = data
            self._src_ver = ver
            self._src_ident = account_rebind.extract_save_identity(data)
            s_id = self._src_ident.get("steam_id", "Desconocido")
            uid = self._src_ident.get("uid", "Desconocido")
            meta = save_slots.extract_save_metadata(data)
            f_name = meta.get("fighter_name", "Fighter")
            fl = meta.get("max_floor", 1)
            self.lbl_src_status.setText(f"Partida válida: {f_name} ({fl}F) | Steam ID Origen: {s_id} | UID: {uid}")
            self.lbl_src_status.setStyleSheet(f"color: {ACCENT_GREEN}; font-weight: bold;")
        except Exception as e:
            self._src_data = None
            self._src_ident = None
            self.lbl_src_status.setText(f"Error al leer partida: {e}")
            self.lbl_src_status.setStyleSheet(f"color: {ACCENT_RED};")

    def _apply_rebind(self):
        try:
            self._apply_rebind_checked()
        except Exception as exc:
            QMessageBox.critical(self, t("error"), str(exc))

    def _apply_rebind_checked(self):
        if not self._src_data:
            QMessageBox.warning(self, t("notice"), t("rebind_err_no_src", default="Debes cargar un archivo de partida de origen válido."))
            return

        mode = self.cb_dest_mode.currentData()
        target_steam_id = self.target_steam_entry.text().strip()
        if not target_steam_id or target_steam_id == "---":
            QMessageBox.warning(self, t("notice"), t("rebind_warn_no_steam_id"))
            return
        target_uid = self.my_ident.get("uid") if self.harmonize_uid_cb.isChecked() else None
        target_name = None if self.keep_name_cb.isChecked() else self.target_name_entry.text().strip()

        rebound_data = account_rebind.rebind_save_to_account(
            copy.deepcopy(self._src_data), target_steam_id=target_steam_id,
            target_uid=target_uid, target_player_name=target_name,
            clear_session_tokens=self.clear_tokens_cb.isChecked())

        if mode == "ACTIVE":
            if not self.active_save_path:
                QMessageBox.warning(self, t("notice"), t("mb_load_save_first"))
                return
            if self.active_save_path:
                if QMessageBox.question(self, t("confirm"), t("rebind_confirm_apply_steam", steam=target_steam_id, path=self.active_save_path), QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes:
                    return
                save_io.save_to_file(rebound_data, self.active_save_path, version=self._src_ver)
                self.main_win.load_save(self.active_save_path)
                QMessageBox.information(self, t("notice"), t("rebind_success_active", default="¡Partida re-vinculada y activada con éxito en tu directorio de Steam!"))
                self.accept()
        elif mode == "SLOT":
            slot_num = self.cb_slot_num.currentData()
            if not save_slots.get_slot_info(slot_num)["is_empty"]:
                if QMessageBox.question(self, t("confirm"), t("slot_confirm_save_to_slot", slot=slot_num), QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes:
                    return
            save_slots.save_current_to_slot(rebound_data, self._src_ver, slot_num)
            self.main_win.refresh_all_views()
            QMessageBox.information(self, t("notice"), t("rebind_success_saved_slot", slot=slot_num, default=f"¡Partida re-vinculada y guardada en la Ranura #{slot_num}!"))
            self.accept()
        elif mode == "FILE":
            out_f, _ = QFileDialog.getSaveFileName(self, t("rebind_btn_export_file", default="Guardar Partida Re-vinculada"), "rebound_save.sav", "Save Files (*.sav)")
            if out_f:
                save_io.save_to_file(rebound_data, out_f, version=self._src_ver)
                QMessageBox.information(self, t("notice"), t("rebind_success_exported", path=out_f, default=f"Partida guardada en: {out_f}"))
                self.accept()
