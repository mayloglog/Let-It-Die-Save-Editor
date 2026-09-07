# -*- coding: utf-8 -*-
"""
Visual Fighter Model Gallery Dialog for LET IT DIE Save Editor (PySide6 Edition).
Allows browsing and choosing official character models / faces with in-game portraits.
"""

import re
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QTabWidget, QWidget, QFrame
)

import i18n
from i18n import t
from ui_qt.theme import (
    get_pixmap, ACCENT_GOLD, ACCENT_CYAN, FG_MUTED, FG_MAIN, BG_CARD, BG_PANEL
)


def get_fighter_model_art(model_str):
    if not model_str:
        return "all_official/body_female_001.png"
    m = re.search(r"BODY_(FEMALE|MALE)_(\d+)", str(model_str), re.IGNORECASE)
    if m:
        gender = m.group(1).lower()
        num = int(m.group(2))
        return f"all_official/body_{gender}_{num:03d}.png"
    m2 = re.search(r"(Female|Male)\s*(\d+)", str(model_str), re.IGNORECASE)
    if m2:
        gender = m2.group(1).lower()
        num = int(m2.group(2))
        return f"all_official/body_{gender}_{num:03d}.png"
    return "all_official/body_female_001.png"


class FighterModelGalleryDialog(QDialog):
    def __init__(self, main_win, fighter_idx=0, current_model="", on_select_cb=None):
        super().__init__(main_win)
        self.main_win = main_win
        self.fighter_idx = fighter_idx
        self.current_model = str(current_model)
        self.on_select_cb = on_select_cb

        self.setWindowTitle(t("f_gallery_title", default="Galería de Modelos y Rostros Oficiales"))
        self.resize(680, 520)
        self.setFixedSize(680, 520)
        self._build_ui()

    def _build_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(12, 12, 12, 12)
        root_layout.setSpacing(8)

        # Header
        header = QFrame()
        header.setStyleSheet("background-color: #151824; border-radius: 6px; padding: 10px;")
        h_v = QVBoxLayout(header)

        lbl_title = QLabel(t("f_gallery_header", default="Selección de Modelo 3D Oficial"))
        lbl_title.setStyleSheet(f"color: {ACCENT_GOLD}; font-size: 13pt; font-weight: bold;")
        h_v.addWidget(lbl_title)

        lbl_sub = QLabel(t("f_gallery_sub", default="Elige un modelo oficial de personaje. Los 16 modelos cuentan con retrato 3D auténtico."))
        lbl_sub.setStyleSheet(f"color: {FG_MUTED}; font-size: 9pt;")
        h_v.addWidget(lbl_sub)
        root_layout.addWidget(header)

        # Tab Widget (Female / Male)
        self.tab_widget = QTabWidget()

        female_tab = QWidget()
        self._populate_grid(female_tab, "female")
        self.tab_widget.addTab(female_tab, t("f_gallery_female_tab", default="Femenino (1 - 8)"))

        male_tab = QWidget()
        self._populate_grid(male_tab, "male")
        self.tab_widget.addTab(male_tab, t("f_gallery_male_tab", default="Masculino (1 - 8)"))

        if "MALE" in self.current_model.upper():
            self.tab_widget.setCurrentIndex(1)

        root_layout.addWidget(self.tab_widget)

        # Close button
        btn_h = QHBoxLayout()
        btn_h.addStretch()
        btn_close = QPushButton(t("close", default="Cerrar"))
        btn_close.clicked.connect(self.reject)
        btn_h.addWidget(btn_close)
        root_layout.addLayout(btn_h)

    def _populate_grid(self, parent_widget, gender):
        grid = QGridLayout(parent_widget)
        grid.setSpacing(10)
        grid.setContentsMargins(8, 8, 8, 8)

        for idx in range(1, 9):
            row = (idx - 1) // 4
            col = (idx - 1) % 4

            code = f"BODY_{gender.upper()}_{idx:03d}"
            label_name = f"{gender.capitalize()} {idx}"
            full_opt = f"{label_name} ({code})"
            art_rel = f"all_official/body_{gender}_{idx:03d}.png"
            is_active = (code in self.current_model or label_name.lower() in self.current_model.lower())

            card = QFrame()
            border_col = ACCENT_GOLD if is_active else "#252b40"
            card.setStyleSheet(f"""
                QFrame {{
                    background-color: #1c2030;
                    border: 2px solid {border_col};
                    border-radius: 6px;
                    padding: 4px;
                }}
                QFrame:hover {{
                    border: 2px solid #00e5ff;
                    background-color: #252b40;
                }}
            """)
            card.setCursor(Qt.CursorShape.PointingHandCursor)
            c_v = QVBoxLayout(card)
            c_v.setSpacing(2)
            c_v.setAlignment(Qt.AlignmentFlag.AlignCenter)

            img_lbl = QLabel()
            img_lbl.setFixedSize(64, 78)
            img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            pix = get_pixmap(art_rel, (64, 78), preserve_aspect=True)
            if pix:
                img_lbl.setPixmap(pix)
            c_v.addWidget(img_lbl)

            name_lbl = QLabel(label_name)
            name_lbl.setStyleSheet(f"font-weight: bold; font-size: 8pt; color: {ACCENT_GOLD if is_active else '#ffffff'};")
            name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            c_v.addWidget(name_lbl)

            code_lbl = QLabel(f"({code})")
            code_lbl.setStyleSheet(f"font-size: 7pt; color: {ACCENT_CYAN if is_active else FG_MUTED};")
            code_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            c_v.addWidget(code_lbl)

            # Click handler
            def mouse_press(event, opt=full_opt, c=code):
                self._choose_model(opt, c)
            card.mousePressEvent = mouse_press

            grid.addWidget(card, row, col)

    def _choose_model(self, full_opt, code):
        if self.on_select_cb:
            self.on_select_cb(full_opt, code)
        else:
            save = self.main_win.save_json
            if save:
                import modifiers
                modifiers.update_fighter(save, self.fighter_idx, body_model=code)
                self.main_win._auto_save()
        self.accept()
