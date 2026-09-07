# -*- coding: utf-8 -*-
"""
Create Fighter Dialog for LET IT DIE Save Editor (PySide6 Edition).
Exact layout, colors, and behavior parity with Cyberpunk Dark design.
"""

import re
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QCheckBox,
    QFrame, QMessageBox
)

import modifiers
import i18n
from i18n import t
from ui_qt.theme import ACCENT_GOLD, FG_MUTED, FG_MAIN, get_icon, get_fighter_model_art
from ui_qt.dialogs.fighter_model_gallery import FighterModelGalleryDialog


class CreateFighterDialog(QDialog):
    def __init__(self, main_win):
        super().__init__(main_win)
        self.main_win = main_win
        self.setWindowTitle(f"🥋 {t('f_create_title', default='Crear Nuevo Luchador')}")
        self.resize(540, 470)
        self.setFixedSize(540, 470)
        self._build_ui()

    def _build_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(16, 16, 16, 16)
        root_layout.setSpacing(12)

        # Header
        header = QFrame()
        header.setStyleSheet("background-color: #151824; border-radius: 6px; padding: 10px;")
        h_v = QVBoxLayout(header)

        lbl_title = QLabel(f"🥋 {t('f_create_title', default='Crear Nuevo Luchador')}")
        lbl_title.setStyleSheet(f"color: {ACCENT_GOLD}; font-size: 13pt; font-weight: bold;")
        h_v.addWidget(lbl_title)

        lbl_desc = QLabel(t("f_create_desc", default="Configura las propiedades iniciales para agregar un nuevo luchador al Congelador."))
        lbl_desc.setStyleSheet(f"color: {FG_MUTED}; font-size: 9pt;")
        h_v.addWidget(lbl_desc)
        root_layout.addWidget(header)

        # Form
        form_frame = QFrame()
        form_frame.setStyleSheet("background-color: #1c2030; border: 1px solid #252b40; border-radius: 6px; padding: 12px;")
        grid = QGridLayout(form_frame)
        grid.setSpacing(10)

        # 1. Name
        grid.addWidget(QLabel(t("f_create_name_lbl", default="Nombre del Luchador:")), 0, 0)
        self.name_entry = QLineEdit()
        self.name_entry.setText(t("f_create_default_name", default="Luchador"))
        grid.addWidget(self.name_entry, 0, 1)

        # 2. Class
        grid.addWidget(QLabel(t("f_lbl_class", default="Clase:")), 1, 0)
        self.class_cb = QComboBox()
        self.class_options = [
            ("BAL", "cls_opt_bal", "All-Rounder"),
            ("BRE", "cls_opt_bre", "Striker"),
            ("DEF", "cls_opt_def", "Defender"),
            ("TEC", "cls_opt_tec", "Attacker"),
            ("SHT", "cls_opt_sht", "Shooter"),
            ("COL", "cls_opt_col", "Collector"),
            ("SKI", "cls_opt_ski", "Skill Master"),
            ("LUK", "cls_opt_luk", "Lucky Star"),
        ]
        for code, tr_k, def_name in self.class_options:
            self.class_cb.addItem(t(tr_k, default=def_name), code)
        grid.addWidget(self.class_cb, 1, 1)

        # 3. Grade / Tier
        grid.addWidget(QLabel(t("f_lbl_grade", default="Grado (Tier ★):")), 2, 0)
        self.grade_cb = QComboBox()
        self.grade_options = [
            (t("grd_opt_t6", default="Grado 6 (Tier 6 - 8 ★)"), 6),
            (t("grd_opt_t5", default="Grado 5 (Tier 5 ★)"), 5),
            (t("grd_opt_t4", default="Grado 4 (Tier 4 ★)"), 4),
            (t("grd_opt_t3", default="Grado 3 (Tier 3 ★)"), 3),
            (t("grd_opt_t2", default="Grado 2 (Tier 2 ★)"), 2),
            (t("grd_opt_t1", default="Grado 1 (Tier 1 ★)"), 1),
        ]
        for name, g in self.grade_options:
            self.grade_cb.addItem(name, g)
        grid.addWidget(self.grade_cb, 2, 1)

        # 4. Model / Appearance
        grid.addWidget(QLabel(t("f_lbl_model", default="Modelo / Aspecto:")), 3, 0)
        m_row = QHBoxLayout()
        m_row.setSpacing(6)
        self.model_cb = QComboBox()
        self.model_cb.setIconSize(QSize(24, 28))
        self._populate_model_options()
        m_row.addWidget(self.model_cb, 1)

        btn_gal = QPushButton(t("f_create_gallery_btn", default="🖼️ Galería 3D"))
        btn_gal.setProperty("accent", "true")
        btn_gal.clicked.connect(self._open_gallery)
        m_row.addWidget(btn_gal)
        grid.addLayout(m_row, 3, 1)

        # 5. Max stats toggle
        self.max_stats_cb = QCheckBox(t("f_create_max_stats", default="Maximizar Stats a Nivel 247 (Tier 8 Uncapped)"))
        self.max_stats_cb.setChecked(True)
        grid.addWidget(self.max_stats_cb, 4, 0, 1, 2)

        root_layout.addWidget(form_frame)

        # Buttons
        btn_bar = QHBoxLayout()
        btn_bar.addStretch()

        btn_cancel = QPushButton(t("dialog_cancel_btn", default=t("cancel", default="Cancelar")))
        btn_cancel.clicked.connect(self.reject)
        btn_bar.addWidget(btn_cancel)

        self.btn_create = QPushButton(f"✅ {t('f_create_confirm', default='Crear Luchador')}")
        self.btn_create.setProperty("success", "true")
        self.btn_create.clicked.connect(self._create_action)
        btn_bar.addWidget(self.btn_create)

        root_layout.addLayout(btn_bar)

    def _populate_model_options(self):
        self.model_cb.clear()
        for i in range(1, 9):
            code = f"BODY_FEMALE_{i:03d}"
            label = f"{t('gender_female', default='Female')} {i} ({code})"
            art = get_fighter_model_art(code)
            ico = get_icon(art, (24, 28))
            if ico and not ico.isNull():
                self.model_cb.addItem(ico, label, code)
            else:
                self.model_cb.addItem(label, code)
        for i in range(1, 9):
            code = f"BODY_MALE_{i:03d}"
            label = f"{t('gender_male', default='Male')} {i} ({code})"
            art = get_fighter_model_art(code)
            ico = get_icon(art, (24, 28))
            if ico and not ico.isNull():
                self.model_cb.addItem(ico, label, code)
            else:
                self.model_cb.addItem(label, code)

    def _open_gallery(self):
        cur_code = self.model_cb.currentData() or self.model_cb.currentText()
        def on_picked(full_opt, code):
            for i in range(self.model_cb.count()):
                d = self.model_cb.itemData(i)
                if d == code or code in self.model_cb.itemText(i):
                    self.model_cb.setCurrentIndex(i)
                    break
        dlg = FighterModelGalleryDialog(self, current_model=cur_code, on_select_cb=on_picked)
        dlg.exec()

    def _create_action(self):
        save = self.main_win.save_json
        if not save:
            return
        name = self.name_entry.text().strip()
        if not name:
            QMessageBox.warning(
                self,
                t("f_create_invalid_name_title", default="Nombre Inválido"),
                t("f_create_invalid_name_msg", default="Por favor ingresa un nombre para el nuevo luchador.")
            )
            return

        cls_code = self.class_cb.currentData() or "BAL"
        grade = self.grade_cb.currentData() or 6
        model_code = self.model_cb.currentData() or self.model_cb.currentText()
        max_stats = self.max_stats_cb.isChecked()

        ok, res = modifiers.create_new_fighter(
            save,
            name=name,
            clazz=cls_code,
            grade=grade,
            body_model=model_code,
            max_stats=max_stats
        )

        if not ok:
            QMessageBox.critical(
                self,
                t("f_create_err_title", default="Error al Crear Luchador"),
                t("f_create_err_msg", err=res, default=f"No se pudo crear el personaje:\n{res}")
            )
            return

        self.main_win._auto_save()
        self.main_win._notify("f_create_success_title", "f_create_success_msg", name=name)
        self.accept()
