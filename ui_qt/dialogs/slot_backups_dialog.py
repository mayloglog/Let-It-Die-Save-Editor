# -*- coding: utf-8 -*-
"""
Slot Backups Dialog for LET IT DIE Save Editor (PySide6 Edition).
Exact 1:1 logic and behavioral parity with Tkinter implementation.
"""

import os
import time
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem, QFrame, QMessageBox, QHeaderView
)

import i18n
from i18n import t
import core.save_slots as save_slots
from ui_qt.theme import ACCENT_GOLD, ACCENT_CYAN, ACCENT_GREEN, FG_MUTED, FG_MAIN


class SlotBackupsDialog(QDialog):
    """Interactive modal dialog displaying historical backups for a specific slot."""

    def __init__(self, parent, slot_num, active_save_path=None, on_restored_cb=None):
        super().__init__(parent)
        self.parent_win = parent
        self.slot_num = slot_num
        self.active_save_path = active_save_path
        self.on_restored_cb = on_restored_cb
        self.backups_list = []

        self.setWindowTitle(t("slot_bak_dialog_title", slot=slot_num, default=f"Historial de Copias de Seguridad - Ranura #{slot_num}"))
        self.resize(880, 560)
        self.setMinimumSize(720, 440)
        self._build_ui()
        self.refresh_backups()

    def _build_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(14, 14, 14, 14)
        root_layout.setSpacing(10)

        # Header Frame
        header = QFrame()
        header.setStyleSheet("background-color: #151824; border-radius: 6px; padding: 10px;")
        h_layout = QHBoxLayout(header)

        lbl_title = QLabel(f"🛡️ {t('slot_bak_header_title', slot=self.slot_num, default=f'Copias de Seguridad de Ranura #{self.slot_num}')}")
        lbl_title.setStyleSheet(f"color: {ACCENT_GOLD}; font-size: 12pt; font-weight: bold;")
        h_layout.addWidget(lbl_title)
        h_layout.addStretch()

        lbl_hint = QLabel(f"💡 {t('slot_bak_double_click_hint', default='Doble clic para restaurar en sesión activa')}")
        lbl_hint.setStyleSheet(f"color: {ACCENT_CYAN}; font-size: 8.5pt;")
        h_layout.addWidget(lbl_hint)
        root_layout.addWidget(header)

        # Table (6 columns matching Tkinter)
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            t("slot_bak_col_file", default="Archivo de Respaldo"),
            t("slot_bak_col_fighter", default="Luchador Principal"),
            t("slot_bak_col_floor", default="Piso Máx"),
            t("slot_bak_col_coins", default="Kill Coins"),
            t("bak_col_date", default="Fecha y Hora"),
            t("slot_bak_col_type", default="Tipo"),
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.itemSelectionChanged.connect(self._on_table_select)
        self.table.itemDoubleClicked.connect(lambda item: self._restore_to_active_action())
        root_layout.addWidget(self.table)

        # Selected Backup Preview Card (matching Tkinter)
        self.preview_frame = QFrame()
        self.preview_frame.setStyleSheet(
            "background-color: #151824; border: 1px solid #00d2d3; border-radius: 6px; padding: 10px;"
        )
        prev_layout = QVBoxLayout(self.preview_frame)
        prev_layout.setContentsMargins(10, 8, 10, 8)
        prev_layout.setSpacing(4)

        self.lbl_preview_title = QLabel(t("slot_bak_preview_lbl", default="DETALLES DE LA COPIA DE SEGURIDAD SELECCIONADA:"))
        self.lbl_preview_title.setStyleSheet(f"color: {ACCENT_GOLD}; font-size: 9pt; font-weight: bold;")
        prev_layout.addWidget(self.lbl_preview_title)

        self.lbl_preview_details = QLabel(t("slot_bak_preview_none", default="Selecciona una copia para ver información detallada."))
        self.lbl_preview_details.setWordWrap(True)
        self.lbl_preview_details.setStyleSheet("color: #dcdde1; font-size: 8.5pt;")
        prev_layout.addWidget(self.lbl_preview_details)
        root_layout.addWidget(self.preview_frame)

        # Action Buttons Frame (Exact parity with Tkinter)
        btn_bar = QHBoxLayout()
        btn_bar.setSpacing(8)

        self.btn_restore_active = QPushButton(t("slot_bak_use_session_btn", default="⚡ Usar en Sesión Activa"))
        self.btn_restore_active.setProperty("accent", "true")
        self.btn_restore_active.clicked.connect(self._restore_to_active_action)
        btn_bar.addWidget(self.btn_restore_active)

        self.btn_restore = QPushButton(t("slot_bak_restore_slot_btn", default="♻️ Restaurar en Ranura"))
        self.btn_restore.clicked.connect(self._restore_to_slot_action)
        btn_bar.addWidget(self.btn_restore)

        self.btn_new_bak = QPushButton(t("slot_bak_create_btn", default="➕ Nueva Copia"))
        self.btn_new_bak.clicked.connect(self._create_backup_action)
        btn_bar.addWidget(self.btn_new_bak)

        self.btn_del_bak = QPushButton(t("slot_bak_delete_btn", default="🗑️ Eliminar"))
        self.btn_del_bak.setProperty("danger", "true")
        self.btn_del_bak.clicked.connect(self._delete_backup_action)
        btn_bar.addWidget(self.btn_del_bak)

        btn_bar.addStretch()

        btn_close = QPushButton(t("dialog_close_btn", default="Cerrar"))
        btn_close.clicked.connect(self.accept)
        btn_bar.addWidget(btn_close)

        root_layout.addLayout(btn_bar)

    def refresh_backups(self):
        self.table.blockSignals(True)
        self.table.setRowCount(0)
        self.table.blockSignals(False)

        slot_info = save_slots.get_slot_info(self.slot_num, force_refresh=True)
        self.backups_list = slot_info.get("backups", [])

        if not self.backups_list:
            self.lbl_preview_details.setText(t("slot_bak_empty", default="No hay copias de seguridad disponibles para esta ranura."))
            self.btn_restore.setEnabled(False)
            self.btn_restore_active.setEnabled(False)
            self.btn_del_bak.setEnabled(False)
            return

        self.btn_restore.setEnabled(True)
        self.btn_restore_active.setEnabled(True)
        self.btn_del_bak.setEnabled(True)

        self.table.blockSignals(True)
        self.table.setRowCount(len(self.backups_list))

        for idx, b in enumerate(self.backups_list):
            fn = b["filename"]
            is_orig = b.get("is_original", False)
            is_session = b.get("is_session", False) or "_session_" in fn
            if is_orig:
                display_title = f"⭐ {fn}"
                type_lbl = t("slot_bak_type_orig", default="Original")
            elif is_session:
                display_title = f"🕒 {fn}"
                type_lbl = t("slot_bak_type_session", default="Sesión")
            else:
                display_title = f"📦 {fn}"
                type_lbl = t("slot_bak_type_auto", default="Automático")

            meta = b.get("meta") or {}
            if meta and not meta.get("error"):
                f_name = meta.get("fighter_name", "Fighter")
                f_lvl = meta.get("fighter_lvl", 1)
                f_grade = meta.get("fighter_grade", 1)
                fighter_str = f"🥋 {f_name} (★{f_grade} Lv.{f_lvl})"
                flr = meta.get("max_floor", 1)
                floor_str = f"🗼 P.{flr}"
                kc = meta.get("kill_coins", 0)
                coins_str = f"🪙 {kc:,}"
            else:
                fighter_str = "-"
                floor_str = "-"
                coins_str = "-"

            item_file = QTableWidgetItem(display_title)
            self.table.setItem(idx, 0, item_file)

            item_fighter = QTableWidgetItem(fighter_str)
            self.table.setItem(idx, 1, item_fighter)

            item_floor = QTableWidgetItem(floor_str)
            item_floor.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(idx, 2, item_floor)

            item_coins = QTableWidgetItem(coins_str)
            item_coins.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(idx, 3, item_coins)

            item_date = QTableWidgetItem(b.get("date_str", "-"))
            item_date.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(idx, 4, item_date)

            item_type = QTableWidgetItem(type_lbl)
            item_type.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if is_orig:
                item_type.setForeground(QColor(ACCENT_GOLD))
            elif is_session:
                item_type.setForeground(QColor(ACCENT_CYAN))
            else:
                item_type.setForeground(QColor(FG_MUTED))
            self.table.setItem(idx, 5, item_type)

        self.table.blockSignals(False)

        if self.backups_list:
            self.table.selectRow(0)
            self._on_table_select()

    def _get_selected_filename(self):
        sel_rows = self.table.selectedItems()
        if not sel_rows:
            return None
        row = sel_rows[0].row()
        if 0 <= row < len(self.backups_list):
            return self.backups_list[row].get("filename")
        return None

    def _on_table_select(self):
        fn = self._get_selected_filename()
        if not fn:
            self.lbl_preview_details.setText(t("slot_bak_preview_none", default="Selecciona una copia para ver información detallada."))
            return
        backups_dir = save_slots.get_slot_backups_dir(self.slot_num)
        bak_path = os.path.join(backups_dir, fn)
        meta = save_slots.get_backup_metadata(bak_path)
        if not meta or "error" in meta:
            sz_kb = os.path.getsize(bak_path) // 1024 if os.path.exists(bak_path) else 0
            self.lbl_preview_details.setText(f"{fn} ({sz_kb} KB)")
            return

        p_name = meta.get("player_name", "Senpai")
        f_name = meta.get("fighter_name", "Fighter")
        f_class = meta.get("fighter_class", "BAL")
        f_grade = meta.get("fighter_grade", 1)
        f_lvl = meta.get("fighter_lvl", 1)
        flr = meta.get("max_floor", 0)
        haters = meta.get("haters_killed", 0)
        kc = meta.get("kill_coins", 0)
        dm = meta.get("death_metals", 0)
        spl = meta.get("splithium", 0)
        bl = meta.get("bloodnium", 0)

        line1 = f"👤 {p_name} • 🥋 {f_name} ({f_class} ★{f_grade} Lv.{f_lvl})"
        line2 = f"🗼 {t('slot_lbl_floor', floor=flr)}  |  ⚔️ {t('slot_lbl_haters', haters=haters)}  |  🪙 {kc:,} KC  |  💎 {dm:,} DM  |  ⚡ {spl:,} SPL  |  🩸 {bl:,} BL"
        self.lbl_preview_details.setText(f"{line1}\n{line2}")

    def _restore_to_slot_action(self):
        fn = self._get_selected_filename()
        if not fn:
            QMessageBox.warning(self, t("notice"), t("slot_bak_select_first", default="Selecciona una copia de seguridad de la lista."))
            return

        ret = QMessageBox.question(
            self,
            t("confirm"),
            t("slot_bak_confirm_restore_slot", file=fn, slot=self.slot_num, default=f"¿Deseas restaurar '{fn}' en la Ranura #{self.slot_num}?"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if ret == QMessageBox.StandardButton.Yes:
            try:
                save_slots.restore_slot_backup(self.slot_num, fn, active_target_path=None)
                if self.on_restored_cb:
                    self.on_restored_cb(self.slot_num, active_updated=False)
                QMessageBox.information(
                    self,
                    t("notice"),
                    t("slot_bak_restored_slot_ok", slot=self.slot_num, default=f"Copia de seguridad restaurada en la Ranura #{self.slot_num}.")
                )
                self.refresh_backups()
            except Exception as e:
                QMessageBox.critical(self, t("error"), str(e))

    def _restore_to_active_action(self):
        fn = self._get_selected_filename()
        if not fn:
            QMessageBox.warning(self, t("notice"), t("slot_bak_select_first", default="Selecciona una copia de seguridad de la lista."))
            return

        if not self.active_save_path or not os.path.exists(self.active_save_path):
            QMessageBox.warning(self, t("notice"), t("mb_load_save_first", default="Primero abre o carga una partida."))
            return

        ret = QMessageBox.question(
            self,
            t("confirm"),
            t("slot_bak_confirm_restore_active", file=fn, slot=self.slot_num, default=f"¿Deseas aplicar '{fn}' directamente a tu partida activa?"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if ret == QMessageBox.StandardButton.Yes:
            try:
                save_slots.restore_slot_backup(self.slot_num, fn, active_target_path=self.active_save_path)
                if self.on_restored_cb:
                    self.on_restored_cb(self.slot_num, active_updated=True)
                QMessageBox.information(
                    self,
                    t("notice"),
                    t("slot_bak_restored_active_ok", slot=self.slot_num, default=f"Copia de seguridad aplicada exitosamente a la partida activa.")
                )
                self.accept()
            except Exception as e:
                QMessageBox.critical(self, t("error"), str(e))

    def _create_backup_action(self):
        try:
            res = save_slots.create_slot_backup(self.slot_num)
            if not res:
                QMessageBox.warning(self, t("notice"), t("slot_bak_no_save_to_backup", default="No hay partida en esta ranura para respaldar."))
                return
            self.refresh_backups()
            QMessageBox.information(
                self,
                t("notice"),
                t("mb_backup_created_msg", file=os.path.basename(res), default=f"Copia creada: {os.path.basename(res)}")
            )
        except Exception as e:
            QMessageBox.critical(self, t("error"), str(e))

    def _delete_backup_action(self):
        fn = self._get_selected_filename()
        if not fn:
            QMessageBox.warning(self, t("notice"), t("slot_bak_select_first", default="Selecciona una copia de seguridad de la lista."))
            return

        if "ORIGINAL" in fn:
            QMessageBox.warning(self, t("notice"), t("slot_bak_cannot_delete_original", default="No se puede eliminar la copia ORIGINAL de seguridad."))
            return

        ret = QMessageBox.question(
            self,
            t("confirm"),
            t("slot_bak_confirm_delete", file=fn, default=f"¿Estás seguro de que deseas eliminar la copia '{fn}'?"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if ret == QMessageBox.StandardButton.Yes:
            b_dir = save_slots.get_slot_backups_dir(self.slot_num)
            p = os.path.join(b_dir, fn)
            try:
                if os.path.exists(p):
                    os.remove(p)
                self.refresh_backups()
            except Exception as e:
                QMessageBox.critical(self, t("error"), str(e))
