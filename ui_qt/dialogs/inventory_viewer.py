# -*- coding: utf-8 -*-
"""
Inventory Viewer Dialog for LET IT DIE Save Editor (PySide6 Edition).
Exact layout, colors, and behavior parity with Cyberpunk Dark design.
"""

from collections import Counter
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QColor
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QComboBox, QProgressBar,
    QTableWidget, QTableWidgetItem, QFrame, QHeaderView
)

import modifiers
from ui_qt.save_actions import inventory_counts
import i18n
from i18n import t, get_item_name
from ui_qt.theme import (
    get_icon, ACCENT_GOLD, ACCENT_CYAN, FG_MUTED, FG_MAIN
)

INVENTORY_CATEGORIES = [
    ("ALL", "inv_cat_all"),
    ("MATS", "inv_cat_mats"),
    ("GEAR", "inv_cat_gear"),
    ("SHROOMS", "inv_cat_shrooms"),
    ("BAG", "inv_cat_bag")
]


class InventoryViewerDialog(QDialog):
    def __init__(self, parent, save_json, equipment_db=None, materials_db=None, shrooms_beasts_db=None):
        super().__init__(parent)
        self.parent_app = parent
        self.main_win = getattr(parent, "main_win", parent)
        self.save_json = save_json

        if equipment_db is None:
            equipment_db = getattr(self.main_win, "equipment_db", [])
        if materials_db is None:
            materials_db = getattr(self.main_win, "materials_db", [])
        if shrooms_beasts_db is None:
            shrooms_beasts_db = getattr(self.main_win, "shrooms_beasts_db", {})

        self.equipment_db = {e["id"]: e for e in equipment_db if isinstance(e, dict) and "id" in e} if isinstance(equipment_db, list) else dict(equipment_db or {})
        self.materials_db = {m.get("itemid", m.get("id")): m for m in materials_db if isinstance(m, dict) and (m.get("itemid") or m.get("id"))} if isinstance(materials_db, list) else dict(materials_db or {})
        self.shrooms_beasts_db = shrooms_beasts_db or {}

        self.setWindowTitle(t("dialog_inventory_title", default="Gestor de Almacenamiento e Inventario"))
        self.resize(960, 650)
        self._build_ui()
        self.refresh_inventory()

    def _build_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(12, 12, 12, 12)
        root_layout.setSpacing(8)

        # Header
        header = QFrame()
        header.setStyleSheet("background-color: #151824; border-radius: 6px; padding: 10px;")
        h_v = QVBoxLayout(header)

        lbl_title = QLabel(t("inv_title", default="Inventario Físico del Coin Locker y Bolsa"))
        lbl_title.setStyleSheet(f"color: {ACCENT_GOLD}; font-size: 13pt; font-weight: bold;")
        h_v.addWidget(lbl_title)

        self.lbl_cap = QLabel("...")
        self.lbl_cap.setStyleSheet("font-size: 9pt; color: #ffffff;")
        h_v.addWidget(self.lbl_cap)

        self.progress_cap = QProgressBar()
        self.progress_cap.setStyleSheet("""
            QProgressBar {
                background-color: #0d0f17;
                border: 1px solid #252b40;
                border-radius: 4px;
                height: 10px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #00e5ff;
                border-radius: 3px;
            }
        """)
        h_v.addWidget(self.progress_cap)
        root_layout.addWidget(header)

        # Filter bar
        filter_h = QHBoxLayout()
        filter_h.addWidget(QLabel(t("inv_search", default="Buscar:")))
        self.search_entry = QLineEdit()
        self.search_entry.setPlaceholderText(t("search_placeholder", default="Nombre / ID..."))
        self.search_entry.textChanged.connect(self.refresh_inventory)
        filter_h.addWidget(self.search_entry)

        filter_h.addWidget(QLabel(t("inv_cat", default="Categoría:")))
        self.cat_cb = QComboBox()
        for code, tr_key in INVENTORY_CATEGORIES:
            self.cat_cb.addItem(t(tr_key, default=code), code)
        self.cat_cb.currentIndexChanged.connect(self.refresh_inventory)
        filter_h.addWidget(self.cat_cb)
        filter_h.addStretch()
        root_layout.addLayout(filter_h)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            t("inv_col_name", default="Objeto"),
            t("inv_col_cat", default="Categoría"),
            t("inv_col_qty", default="Cantidad"),
            t("inv_col_id", default="ID Interno"),
            t("inv_col_loc", default="Ubicación")
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        root_layout.addWidget(self.table)

        # Bottom
        btn_bar = QHBoxLayout()
        btn_bar.addStretch()
        btn_close = QPushButton(t("close", default="Cerrar"))
        btn_close.clicked.connect(self.accept)
        btn_bar.addWidget(btn_close)
        root_layout.addLayout(btn_bar)

    def refresh_inventory(self):
        if not self.save_json:
            return

        slots = self.save_json.get("soul", {}).get("cl", [])
        cap = len(slots)
        counts = inventory_counts(self.save_json)
        total_used = sum(1 for s in slots if s.get("type") != -1 and s.get("eid"))
        pct = int((total_used / max(1, cap)) * 100)
        self.lbl_cap.setText(f"Ocupación: {total_used:,} / {cap:,} slots ({pct}%)")
        self.progress_cap.setValue(pct)

        search_q = self.search_entry.text().strip().lower()
        sel_cat = self.cat_cb.currentData() or "ALL"

        rows = []
        for (iid, owner, category, level, state), qty in counts.items():
            metadata = self.equipment_db.get(iid) or self.materials_db.get(iid) or self.shrooms_beasts_db.get(iid) or {"name": iid}
            if iid.startswith("MSR_") and state == 1:
                metadata = {**metadata, **{f"name_{lang}": metadata.get(f"cooked_name_{lang}") or metadata.get(f"name_{lang}", iid) + " (Grilled)" for lang in ("es", "en", "zh")}}
            name = get_item_name(metadata)
            if category == "GEAR":
                name += f" +{max(0, level - 1)}"
            cat = t({"MATS": "cat_material", "GEAR": "tab_blueprints", "SHROOMS": "cat_beast" if iid.startswith("BST_") else "cat_mushroom"}[category])

            if search_q and (search_q not in name.lower() and search_q not in iid.lower()):
                continue

            if sel_cat == "BAG" and owner == "COIN_LOCKER":
                continue
            if sel_cat not in ("ALL", "BAG") and category != sel_cat:
                continue

            rows.append((name, cat, qty, iid, owner))

        self.table.blockSignals(True)
        self.table.setRowCount(len(rows))

        for idx, (name, cat, qty, iid, owner) in enumerate(rows):
            item_name = QTableWidgetItem(f" {name}")
            ico = get_icon(iid.lower(), (22, 22))
            if ico:
                item_name.setIcon(ico)
            self.table.setItem(idx, 0, item_name)
            self.table.setItem(idx, 1, QTableWidgetItem(cat))

            item_qty = QTableWidgetItem(str(qty))
            item_qty.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(idx, 2, item_qty)

            self.table.setItem(idx, 3, QTableWidgetItem(iid))
            location = t("inv_loc_storage") if owner == "COIN_LOCKER" else t("inv_loc_bag")
            self.table.setItem(idx, 4, QTableWidgetItem(location))

        self.table.blockSignals(False)
