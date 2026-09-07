# -*- coding: utf-8 -*-
"""
Weapon Mastery Tab for LET IT DIE Save Editor (PySide6 Edition).
Exact layout, colors, and behavior parity with Cyberpunk Dark design.
"""

from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QInputDialog, QMessageBox
)

import modifiers
import i18n
from i18n import t, get_expert_weapon_name
from game_data import WEAPON_CATEGORIES
from ui_qt.theme import get_icon, ACCENT_GOLD, ACCENT_CYAN, FG_MUTED

WEAPON_MASTERY_ICONS = {wt: img for wt, nm, img in WEAPON_CATEGORIES}


class MasteryTab(QWidget):
    def __init__(self, main_win):
        super().__init__()
        self.main_win = main_win
        self.expert_list = []
        self._build_ui()

    def _build_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(8, 8, 8, 8)
        root_layout.setSpacing(6)

        # Top Control Toolbar
        top_ctrl = QHBoxLayout()
        self.lbl_target = QLabel(t("wm_target_lvl_lbl", default="Nivel Objetivo:"))
        top_ctrl.addWidget(self.lbl_target)

        self.lvl_cb = QComboBox()
        for i in range(1, 21):
            self.lvl_cb.addItem(str(i), i)
        self.lvl_cb.setCurrentText("20")
        self.lvl_cb.setFixedWidth(60)
        top_ctrl.addWidget(self.lvl_cb)

        self.btn_max_all = QPushButton(t("wm_set_all_btn", default="Aplicar a Todas las Armas"))
        self.btn_max_all.setProperty("accent", "true")
        self.btn_max_all.clicked.connect(self.max_all_mastery)
        top_ctrl.addWidget(self.btn_max_all)
        top_ctrl.addStretch()
        root_layout.addLayout(top_ctrl)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            t("wm_col_type", default="Categoría de Arma"),
            t("wm_col_code", default="Código"),
            t("wm_col_lvl", default="Nivel"),
            t("wm_col_exp", default="Puntos ABP")
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setIconSize(QSize(44, 44))
        self.table.verticalHeader().setDefaultSectionSize(48)
        self.table.itemDoubleClicked.connect(self._on_item_double_clicked)
        root_layout.addWidget(self.table)

    def refresh_data(self):
        """Populates the mastery table."""
        save = self.main_win.save_json
        if not save:
            return

        expert_list = save.get("soul", {}).get("expert", [])
        self.expert_list = [item for item in expert_list if item.get("ptarmtp") not in ("PTARMTP_08", "PTARMTP_22")]
        self.expert_list = sorted(self.expert_list, key=lambda x: x.get("ptarmtp", ""))

        self.table.blockSignals(True)
        self.table.setRowCount(len(self.expert_list))

        for row_idx, item in enumerate(self.expert_list):
            k = item.get("ptarmtp", "PTARMTP_00")
            lvl = item.get("lvl", 1)
            pts = item.get("abp", 0)

            w_name = get_expert_weapon_name(k)
            ico_file = WEAPON_MASTERY_ICONS.get(k, "weapon")

            # Name + Icon
            item_name = QTableWidgetItem(f" {w_name}")
            ico = get_icon(ico_file, (44, 44)) or get_icon("weapon", (44, 44))
            if ico and not ico.isNull():
                item_name.setIcon(ico)
            self.table.setItem(row_idx, 0, item_name)

            # Code
            item_code = QTableWidgetItem(k)
            item_code.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row_idx, 1, item_code)

            # Level
            item_lvl = QTableWidgetItem(f"Lv.{lvl}")
            item_lvl.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if lvl >= 20:
                item_lvl.setForeground(Qt.GlobalColor.yellow)
            self.table.setItem(row_idx, 2, item_lvl)

            # Points
            item_pts = QTableWidgetItem(f"{pts:,} ABP")
            item_pts.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row_idx, 3, item_pts)

        self.table.blockSignals(False)

    def _on_item_double_clicked(self, table_item):
        row = table_item.row()
        if 0 <= row < len(self.expert_list):
            item = self.expert_list[row]
            k = item.get("ptarmtp", "PTARMTP_00")
            w_name = get_expert_weapon_name(k)
            cur_lvl = item.get("lvl", 1)

            new_lvl, ok = QInputDialog.getInt(
                self,
                t("wm_edit_title", default="Modificar Maestría"),
                t("wm_edit_prompt", arm_type=f"{w_name} ({k})", default=f"{w_name} ({k})\nNivel (1-20):"),
                cur_lvl, 1, 20
            )
            if ok:
                modifiers.set_weapon_mastery(self.main_win.save_json, k, level=new_lvl)
                self.main_win._auto_save()
                self.refresh_data()
                self.main_win._notify("wm_notify_updated_title", "wm_notify_updated_msg", arm_type=w_name, new_lvl=new_lvl)

    def max_all_mastery(self):
        save = self.main_win.save_json
        if not save:
            return
        lvl = int(self.lvl_cb.currentText())
        modifiers.max_all_weapon_mastery(save, level=lvl)
        self.main_win._auto_save()
        self.refresh_data()
        self.main_win._notify("wm_notify_maxed_title", "wm_notify_maxed_msg", count=55, lvl=lvl)

    def refresh_translations(self):
        self.lbl_target.setText(t("wm_target_lvl_lbl", default="Nivel Objetivo:"))
        self.btn_max_all.setText(t("wm_set_all_btn", default="Aplicar a Todas las Armas"))
        self.table.setHorizontalHeaderLabels([
            t("wm_col_type", default="Categoría de Arma"),
            t("wm_col_code", default="Código"),
            t("wm_col_lvl", default="Nivel"),
            t("wm_col_exp", default="Puntos ABP")
        ])
        self.refresh_data()
