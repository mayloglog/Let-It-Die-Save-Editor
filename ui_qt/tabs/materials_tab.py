# -*- coding: utf-8 -*-
"""
Materials & R&D Tab for LET IT DIE Save Editor (PySide6 Edition).
Exact layout, colors, and behavior parity with Cyberpunk Dark design.
"""

import os
import json
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QGroupBox, QLabel, QLineEdit, QPushButton, QComboBox,
    QSpinBox, QSplitter, QTableWidget, QTableWidgetItem,
    QScrollArea, QFrame, QMessageBox, QHeaderView, QInputDialog
)

import modifiers
from ui_qt.save_actions import set_material_quantity
import i18n
from i18n import t, get_item_name, get_item_desc, get_entity_display_title
from ui_qt.theme import (
    get_pixmap, get_icon, find_material_art, resolve_icon_path,
    ACCENT_GOLD, ACCENT_CYAN, ACCENT_GREEN, ACCENT_RED, ACCENT_PINK,
    FG_MUTED, FG_MAIN, BG_CARD, BG_PANEL
)

CANONICAL_MATERIAL_CATEGORIES = [
    ("ALL", "mat_cat_all"),
    ("ALUMINUM", "mat_cat_aluminum"),
    ("COPPER", "mat_cat_copper"),
    ("IRON_STEEL", "mat_cat_iron_steel"),
    ("OIL", "mat_cat_oil"),
    ("WOOD", "mat_cat_wood"),
    ("CLOTH", "mat_cat_cloth"),
    ("DOD", "mat_cat_dod"),
    ("WAR", "mat_cat_war"),
    ("CW", "mat_cat_cw"),
    ("MILK", "mat_cat_milk"),
    ("BOSS", "mat_cat_boss"),
    ("JACKAL_TENGOKU", "mat_cat_jackal_tengoku"),
    ("STEROIDS", "mat_cat_steroids"),
    ("MUSHROOMS_BEASTS", "mat_cat_mushrooms_beasts"),
    ("MUSHROOMS", "mat_cat_mushrooms"),
    ("BEASTS", "mat_cat_beasts"),
]


class MaterialsTab(QWidget):
    def __init__(self, main_win):
        super().__init__()
        self.main_win = main_win
        self.current_selected_mat = None  # (itemid, title, cat, meta, is_sb)
        self.filtered_materials = []
        self.current_floor_filter = "TODOS"
        self._build_ui()

    def _build_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(8, 8, 8, 8)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        root_layout.addWidget(splitter)

        # =============================================================
        # LEFT PANEL: Search, Category, Stock & Floors Table
        # =============================================================
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 4, 0)
        left_layout.setSpacing(6)

        # Filter Controls Row 1
        ctrl_f = QHBoxLayout()
        self.lbl_search = QLabel(t("mat_search", default="🔍 Buscar:"))
        ctrl_f.addWidget(self.lbl_search)
        self.search_entry = QLineEdit()
        self.search_entry.setPlaceholderText(t("search_placeholder", default="Nombre / ID..."))
        self.search_entry.textChanged.connect(self.filter_materials_list)
        ctrl_f.addWidget(self.search_entry)

        self.lbl_cat = QLabel(t("mat_cat_lbl", default="Categoría:"))
        ctrl_f.addWidget(self.lbl_cat)
        self.cat_cb = QComboBox()
        for code, tr_key in CANONICAL_MATERIAL_CATEGORIES:
            self.cat_cb.addItem(t(tr_key, default=code), code)
        self.cat_cb.currentIndexChanged.connect(self.filter_materials_list)
        ctrl_f.addWidget(self.cat_cb)

        self.lbl_stock = QLabel(t("mat_stock_lbl", default="Almacén:"))
        ctrl_f.addWidget(self.lbl_stock)
        self.stock_cb = QComboBox()
        self.stock_cb.addItem(t("mat_all", default="Todos"), "ALL")
        self.stock_cb.addItem(t("mat_in_stock", default="📦 En Stock (> 0)"), "IN_STOCK")
        self.stock_cb.addItem(t("mat_low_stock", default="⚠️ Stock Bajo (< 10)"), "LOW_STOCK")
        self.stock_cb.addItem(t("mat_out_stock", default="❌ Agotado (0)"), "OUT_OF_STOCK")
        self.stock_cb.currentIndexChanged.connect(self.filter_materials_list)
        ctrl_f.addWidget(self.stock_cb)

        self.lbl_rarity = QLabel(t("mat_rarity_lbl", default="Rareza:"))
        ctrl_f.addWidget(self.lbl_rarity)
        self.rarity_cb = QComboBox()
        self.rarity_cb.addItem(t("decal_all", default="Todas"), "ALL")
        for stars in range(1, 9):
            self.rarity_cb.addItem(f"{stars}★", stars)
        self.rarity_cb.currentIndexChanged.connect(self.filter_materials_list)
        ctrl_f.addWidget(self.rarity_cb)

        left_layout.addLayout(ctrl_f)

        # Filter Controls Row 2: Floors quick bar & Preset Actions
        f_row2 = QHBoxLayout()
        self.lbl_floors = QLabel(t("mat_floors_lbl", default="Torre:"))
        self.lbl_floors.setStyleSheet(f"color: {ACCENT_GOLD}; font-weight: bold; font-size: 8pt;")
        f_row2.addWidget(self.lbl_floors)

        floor_buttons = [
            (t("mat_floor_all", default="TODOS"), "TODOS"),
            ("1-10F", "1_10"),
            ("11-20F", "11_20"),
            ("21-30F", "21_30"),
            ("31-40F", "31_40"),
            ("41-50F", "41_50"),
            ("51F+", "51_PLUS"),
        ]
        self.floor_btn_widgets = []
        for btn_text, mode in floor_buttons:
            btn = QPushButton(btn_text)
            btn.setFixedHeight(26)
            btn.setCheckable(True)
            btn.setChecked(mode == "TODOS")
            btn.clicked.connect(lambda checked=False, m=mode: self._set_floor_filter(m))
            f_row2.addWidget(btn)
            self.floor_btn_widgets.append((btn, mode))

        f_row2.addStretch()

        self.btn_open_storage = QPushButton("📦 Coin Locker")
        self.btn_open_storage.setFixedHeight(26)
        self.btn_open_storage.clicked.connect(self._open_storage_manager)
        f_row2.addWidget(self.btn_open_storage)

        self.btn_max_all = QPushButton(t("mat_max_stock_btn", default="⭐ Maximizar Todos (100 u.)"))
        self.btn_max_all.setFixedHeight(26)
        self.btn_max_all.setProperty("accent", "true")
        self.btn_max_all.clicked.connect(self.max_all_materials_preset)
        f_row2.addWidget(self.btn_max_all)

        left_layout.addLayout(f_row2)

        # Materials Table (4 Columns: Icon/Name, Storage, Rarity, Internal Code)
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            t("decal_col_icon", default="Icono / Nombre Oficial"),
            t("bp_col_storage", default="Almacén"),
            t("decal_col_rare", default="Rareza"),
            t("wm_col_code", default="Código Interno"),
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
        self.table.itemSelectionChanged.connect(self._on_table_selection_changed)
        self.table.itemClicked.connect(lambda item: self._on_table_selection_changed())
        self.table.itemDoubleClicked.connect(self._on_table_double_clicked)
        left_layout.addWidget(self.table)

        splitter.addWidget(left_widget)

        # =============================================================
        # RIGHT PANEL: Full Scrollable Workbench & Material Card
        # =============================================================
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(4, 0, 4, 0)
        right_layout.setSpacing(8)

        # 1. Official Material Showcase Box
        self.box_detail = QGroupBox(t("mat_card_title", default="Ficha Oficial de Material R&D"))
        detail_v = QVBoxLayout(self.box_detail)
        detail_v.setContentsMargins(10, 10, 10, 10)
        detail_v.setSpacing(6)

        # Artwork Card (260x130)
        art_center = QHBoxLayout()
        self.mat_art_lbl = QLabel()
        self.mat_art_lbl.setFixedSize(260, 130)
        self.mat_art_lbl.setStyleSheet("border: 2px solid #252b40; border-radius: 8px; background-color: #151824;")
        self.mat_art_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        art_center.addStretch()
        art_center.addWidget(self.mat_art_lbl)
        art_center.addStretch()
        detail_v.addLayout(art_center)

        # Title Label
        self.mat_title_lbl = QLabel(t("mat_select_prompt", default="Selecciona un material"))
        self.mat_title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.mat_title_lbl.setWordWrap(True)
        self.mat_title_lbl.setStyleSheet(f"color: {ACCENT_GOLD}; font-size: 11pt; font-weight: bold;")
        detail_v.addWidget(self.mat_title_lbl)

        # Type & Location Line
        self.mat_type_lbl = QLabel("---")
        self.mat_type_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.mat_type_lbl.setStyleSheet(f"color: {FG_MUTED}; font-size: 9pt;")
        detail_v.addWidget(self.mat_type_lbl)

        # Stock Status Indicator
        self.mat_stock_lbl = QLabel(t("mat_none_in_storage", default="📦 En tu Almacén: 0 u. (No tienes)"))
        self.mat_stock_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.mat_stock_lbl.setStyleSheet(f"color: {ACCENT_CYAN}; font-size: 10pt; font-weight: bold;")
        detail_v.addWidget(self.mat_stock_lbl)

        # Encyclopedia Lore Description
        self.mat_desc_lbl = QLabel(t("mat_desc_default", default="Material oficial de R&D para fabricar y mejorar armas y armaduras en Chokufunsha."))
        self.mat_desc_lbl.setWordWrap(True)
        self.mat_desc_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.mat_desc_lbl.setStyleSheet("color: #dcdde1; font-size: 8.5pt; padding: 4px;")
        detail_v.addWidget(self.mat_desc_lbl)

        # Commercial / Value Info Box (Buy/Sell or Cooked data)
        self.box_value = QGroupBox(t("mat_value_box_title", default="💰 Información Comercial & Reciclaje"))
        val_v = QVBoxLayout(self.box_value)
        val_v.setContentsMargins(8, 8, 8, 8)
        val_v.setSpacing(4)
        self.mat_price_lbl = QLabel("---")
        self.mat_price_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.mat_price_lbl.setWordWrap(True)
        self.mat_price_lbl.setStyleSheet(f"color: {ACCENT_GOLD}; font-size: 8.5pt;")
        val_v.addWidget(self.mat_price_lbl)
        detail_v.addWidget(self.box_value)

        # Quantity Adjustment Controls Box
        self.box_adjust = QGroupBox(t("mat_set_qty_lbl", default="Ajuste de Stock"))
        adj_v = QVBoxLayout(self.box_adjust)
        adj_v.setContentsMargins(8, 8, 8, 8)
        adj_v.setSpacing(6)

        cur_qty_h = QHBoxLayout()
        cur_qty_h.addWidget(QLabel(t("mat_set_qty_lbl", default="Cantidad:")))
        self.qty_spin = QSpinBox()
        self.qty_spin.setRange(0, 999)
        self.qty_spin.setValue(50)
        self.qty_spin.setFixedWidth(90)
        cur_qty_h.addWidget(self.qty_spin)

        self.btn_set_qty = QPushButton(t("mat_set_btn", default="Establecer"))
        self.btn_set_qty.setProperty("accent", "true")
        self.btn_set_qty.clicked.connect(self._set_selected_mat_qty)
        cur_qty_h.addWidget(self.btn_set_qty)
        cur_qty_h.addStretch()
        adj_v.addLayout(cur_qty_h)

        quick_btns = QHBoxLayout()
        for q_val in [10, 50, 100]:
            btn = QPushButton(f"+{q_val}")
            btn.clicked.connect(lambda checked=False, val=q_val: self._quick_add_material_qty(val))
            quick_btns.addWidget(btn)

        self.btn_max_sel = QPushButton(t("mat_btn_max_sel", default="Máx (999)"))
        self.btn_max_sel.setProperty("accent", "true")
        self.btn_max_sel.clicked.connect(lambda: self._set_qty_selected(999))
        quick_btns.addWidget(self.btn_max_sel)

        self.btn_clear_sel = QPushButton(t("mat_btn_clear_sel", default="Vaciar (0)"))
        self.btn_clear_sel.setProperty("danger", "true")
        self.btn_clear_sel.clicked.connect(lambda: self._set_qty_selected(0))
        quick_btns.addWidget(self.btn_clear_sel)
        adj_v.addLayout(quick_btns)

        detail_v.addWidget(self.box_adjust)

        # Coin Locker Capacity Expansion Box
        self.box_storage = QGroupBox(t("mat_locker_cap_title", default="Capacidad del Coin Locker"))
        stor_v = QVBoxLayout(self.box_storage)
        stor_v.setContentsMargins(8, 8, 8, 8)
        stor_v.setSpacing(6)

        self.mat_cap_indicator_lbl = QLabel(t("mat_cap_initial_indicator", default="Capacidad: 1,500 casillas"))
        self.mat_cap_indicator_lbl.setStyleSheet(f"color: {ACCENT_CYAN}; font-size: 9pt; font-weight: bold;")
        stor_v.addWidget(self.mat_cap_indicator_lbl)

        exp_row1 = QHBoxLayout()
        btn_500 = QPushButton(t("mat_expand_500", default="+500 Casillas"))
        btn_500.clicked.connect(lambda: self._expand_coin_locker_add(500))
        exp_row1.addWidget(btn_500)

        btn_1000 = QPushButton(t("mat_expand_1000", default="+1,000 Casillas"))
        btn_1000.clicked.connect(lambda: self._expand_coin_locker_add(1000))
        exp_row1.addWidget(btn_1000)
        stor_v.addLayout(exp_row1)

        exp_row2 = QHBoxLayout()
        btn_max_cap = QPushButton(t("mat_expand_max", default="⭐ 6,000 (Tope)"))
        btn_max_cap.clicked.connect(lambda: self._expand_coin_locker(6000))
        exp_row2.addWidget(btn_max_cap)

        btn_custom = QPushButton(t("mat_expand_custom", default="🚀 Personalizado..."))
        btn_custom.setProperty("accent", "true")
        btn_custom.clicked.connect(self._expand_coin_locker_custom)
        exp_row2.addWidget(btn_custom)
        stor_v.addLayout(exp_row2)

        detail_v.addWidget(self.box_storage)

        right_layout.addWidget(self.box_detail)
        right_layout.addStretch()

        scroll_area.setWidget(right_container)
        splitter.addWidget(scroll_area)
        splitter.setSizes([480, 520])

    def refresh_data(self):
        """Loads and filters the materials list."""
        self.filter_materials_list()
        self._update_storage_info()

    def _set_floor_filter(self, mode):
        if self.current_floor_filter == mode and mode != "TODOS":
            self.current_floor_filter = "TODOS"
        else:
            self.current_floor_filter = mode

        if hasattr(self, "floor_btn_widgets"):
            for btn, code in self.floor_btn_widgets:
                btn.setChecked(code == self.current_floor_filter)

        self.filter_materials_list()

    _set_mat_floor_filter = _set_floor_filter

    @property
    def mat_floor_filter(self):
        class _Var:
            def __init__(self, tab): self.tab = tab
            def get(self): return self.tab.current_floor_filter
            def set(self, val): self.tab._set_floor_filter(val)
        return _Var(self)

    @classmethod
    def _match_material_category(cls, cat_filter, item_cat):
        if not cat_filter or cat_filter in ("ALL", "Todos", "All", "全部", t("mat_all"), t("mat_cat_all"), t("decal_all")):
            return True

        # 1. Direct canonical item check if material dict is passed
        if isinstance(item_cat, dict):
            item_cid = item_cat.get("category_id")
            for code, key in CANONICAL_MATERIAL_CATEGORIES:
                if cat_filter in (code, t(key)):
                    if code == "ALL":
                        return True
                    if item_cid and item_cid == code:
                        return True
            item_cat = item_cat.get("category", "")

        fl = cat_filter.lower()
        cl = item_cat.lower()

        # 2. Canonical mapping resolution
        filter_code = None
        for code, key in CANONICAL_MATERIAL_CATEGORIES:
            if cat_filter == code or fl == t(key).lower():
                filter_code = code
                break

        code_to_cl_subs = {
            "ALUMINUM": ["alumin"],
            "COPPER": ["cobre", "copper"],
            "IRON_STEEL": ["hierro", "iron", "steel", "acero"],
            "OIL": ["petr", "oil", "aceite"],
            "WOOD": ["mader", "wood"],
            "CLOTH": ["textil", "cloth", "fibra", "fiber"],
            "DOD": ["d.o.d", "dod"],
            "WAR": ["war"],
            "CW": ["candle", "cw"],
            "MILK": ["m.i.l.k", "milk"],
            "BOSS": ["boss", "jefe"],
            "JACKAL_TENGOKU": ["jackal", "tengoku"],
            "STEROIDS": ["esteroide", "steroid", "rostest"],
        }
        if filter_code and filter_code in code_to_cl_subs:
            if any(sub in cl for sub in code_to_cl_subs[filter_code]):
                return True

        # 3. Fallback for custom string patterns & unit tests
        if any(x in fl for x in ["steroid", "esteroide", "rostest", "类固醇"]):
            return any(x in cl for x in ["esteroide", "steroid", "rostest"])
        if any(x in fl for x in ["aluminum", "aluminio", "铝"]):
            return "alumin" in cl
        if any(x in fl for x in ["copper", "cobre", "铜"]):
            return any(x in cl for x in ["cobre", "copper"])
        if any(x in fl for x in ["iron", "hierro", "steel", "acero", "铁", "钢"]):
            return any(x in cl for x in ["hierro", "iron", "steel", "acero"])
        if any(x in fl for x in ["oil", "petr", "aceite", "油"]):
            return any(x in cl for x in ["petr", "oil", "aceite"])
        if any(x in fl for x in ["wood", "mader", "木"]):
            return any(x in cl for x in ["mader", "wood"])
        if any(x in fl for x in ["cloth", "textil", "fiber", "fibra", "布"]):
            return any(x in cl for x in ["textil", "cloth", "fibra", "fiber"])
        if any(x in fl for x in ["d.o.d", "dod"]):
            return any(x in cl for x in ["d.o.d", "dod"])
        if "war" in fl:
            return "war" in cl
        if "candle" in fl:
            return "candle" in cl
        if any(x in fl for x in ["m.i.l.k", "milk"]):
            return any(x in cl for x in ["m.i.l.k", "milk"])
        if any(x in fl for x in ["boss", "jefe"]):
            return any(x in cl for x in ["boss", "jefe"])
        if any(x in fl for x in ["jackal", "tengoku", "豺狼", "天狱"]):
            return any(x in cl for x in ["jackal", "tengoku"])

        c_key = cat_filter.lower().split()[0].replace("(", "").replace(")", "")
        return c_key in cl

    @staticmethod
    def _localize_material_category(cat_str):
        if not cat_str:
            return ""
        cl = cat_str.lower()
        if "esteroide" in cl or "rostest" in cl or "steroid" in cl:
            return t("mat_cat_steroids")
        if "alumin" in cl:
            return t("mat_cat_aluminum")
        if "cobre" in cl or "copper" in cl:
            return t("mat_cat_copper")
        if "hierro" in cl or "iron" in cl or "steel" in cl or "acero" in cl:
            return t("mat_cat_iron_steel")
        if "petr" in cl or "oil" in cl or "aceite" in cl:
            return t("mat_cat_oil")
        if "mader" in cl or "wood" in cl:
            return t("mat_cat_wood")
        if "textil" in cl or "cloth" in cl or "fibra" in cl or "fiber" in cl:
            return t("mat_cat_cloth")
        if "d.o.d" in cl or "dod" in cl:
            return t("mat_cat_dod")
        if "war" in cl:
            return t("mat_cat_war")
        if "candle" in cl or "cw" in cl:
            return t("mat_cat_cw")
        if "m.i.l.k" in cl or "milk" in cl:
            return t("mat_cat_milk")
        if "boss" in cl or "jefe" in cl:
            return t("mat_cat_boss")
        if "jackal" in cl or "tengoku" in cl:
            return t("mat_cat_jackal_tengoku")
        return cat_str

    @staticmethod
    def _localize_material_category_zh(cat_str):
        return MaterialsTab._localize_material_category(cat_str)

    def _clear_details(self):
        self.mat_title_lbl.setText(t("mat_select_prompt", default="Selecciona un material"))
        self.mat_type_lbl.setText("---")
        self.mat_stock_lbl.setText(t("mat_none_in_storage", default="📦 En tu Almacén: 0 u. (No tienes)"))
        self.mat_stock_lbl.setStyleSheet(f"color: {FG_MUTED}; font-size: 9.5pt;")
        self.mat_desc_lbl.setText(t("mat_desc_default", default="Material oficial de R&D para fabricar y mejorar armas y armaduras en Chokufunsha."))
        self.mat_price_lbl.setText("---")
        self.mat_art_lbl.clear()

    def filter_materials_list(self):
        save = self.main_win.save_json
        mats_db = getattr(self.main_win, "materials_db", [])
        sb_db = getattr(self.main_win, "shrooms_beasts_db", {})

        search_q = self.search_entry.text().strip().lower()
        query_tokens = search_q.split() if search_q else []

        cat_code = self.cat_cb.currentData() or "ALL"
        stock_filter = self.stock_cb.currentData() or "ALL"
        rarity_filter = self.rarity_cb.currentData() or "ALL"
        floor_filter = self.current_floor_filter

        # Live stock counts from save
        stock_map = {}
        if save:
            stock_map = modifiers.analyze_storage_stock(save).get("stock_by_id", {})

        self.filtered_materials = []

        # 1. R&D Materials from all_materials_db.json
        show_rnd_materials = (cat_code not in ("MUSHROOMS", "BEASTS", "MUSHROOMS_BEASTS"))
        if show_rnd_materials:
            for m in mats_db:
                itemid = m.get("itemid") or m.get("id", "")
                if not itemid:
                    continue

                name_es = m.get("name_es", m.get("name", ""))
                name_en = m.get("name_en", "")
                cat = m.get("category", "Materiales")
                r = m.get("rarity", 1)
                cnt = stock_map.get(itemid, 0)

                # Category filter
                if cat_code != "ALL":
                    m_cid = m.get("category_id")
                    if m_cid:
                        if m_cid != cat_code:
                            continue
                    elif not self._match_material_category(cat_code, m):
                        continue
                elif not self._match_material_category(cat_code, m):
                    continue

                # Stock filter
                if stock_filter == "IN_STOCK" and cnt <= 0:
                    continue
                elif stock_filter == "LOW_STOCK" and (cnt <= 0 or cnt >= 10):
                    continue
                elif stock_filter == "OUT_OF_STOCK" and cnt > 0:
                    continue

                # Rarity filter
                if rarity_filter != "ALL":
                    try:
                        req_r = int(rarity_filter)
                        if r != req_r:
                            continue
                    except (ValueError, TypeError):
                        pass

                # Floor filter (Tower Section)
                if floor_filter != "TODOS":
                    cat_lower = cat.lower()
                    match_floor = False
                    if floor_filter == "1_10" and (r in (1, 2) or "d.o.d" in cat_lower):
                        match_floor = True
                    elif floor_filter == "11_20" and (r == 3 or "war" in cat_lower):
                        match_floor = True
                    elif floor_filter == "21_30" and (r == 4 or "candle" in cat_lower):
                        match_floor = True
                    elif floor_filter == "31_40" and (r == 5 or "m.i.l.k" in cat_lower):
                        match_floor = True
                    elif floor_filter == "41_50" and (r == 6):
                        match_floor = True
                    elif floor_filter == "51_PLUS" and (r in (7, 8) or "tengoku" in cat_lower or "jackals" in cat_lower):
                        match_floor = True
                    if not match_floor:
                        continue

                # Multi-token search with smart multi-word matching & Tier aliases
                if query_tokens:
                    extra_names = " ".join(str(v) for k, v in m.items() if (k.startswith("name") or k.startswith("desc")) and isinstance(v, str))
                    searchable = f"{extra_names} {name_es} {name_en} {cat} {self._localize_material_category(cat)} {self._localize_material_category_zh(cat)} {itemid} t{r} tier {r} tier{r} {r}★ {r}star {name_en.replace('.', '')} {name_es.replace('.', '')}".lower()
                    if not all(token in searchable for token in query_tokens):
                        continue

                display_title = i18n.get_entity_display_title(m)
                cat_display = self._localize_material_category(cat)
                self.filtered_materials.append((itemid, display_title, cat_display, r, cnt, m, False))

        # 2. Mushrooms & Beasts from all_shrooms_beasts_db.json
        is_shroom_cat = (cat_code in ("MUSHROOMS", "BEASTS", "MUSHROOMS_BEASTS"))
        allow_shrooms_floors = (is_shroom_cat or floor_filter == "TODOS")
        show_shrooms = (cat_code in ("ALL", "MUSHROOMS", "BEASTS", "MUSHROOMS_BEASTS"))

        if show_shrooms and allow_shrooms_floors and sb_db:
            only_shrooms = (cat_code == "MUSHROOMS")
            only_beasts = (cat_code == "BEASTS")

            sorted_entries = sorted(
                sb_db.items(),
                key=lambda it: (0 if it[1].get("type") == "MUSHROOM" else 1, it[0])
            )

            for itemid, info in sorted_entries:
                item_type = info.get("type", "MUSHROOM")
                if only_shrooms and item_type != "MUSHROOM":
                    continue
                if only_beasts and item_type != "BEAST":
                    continue

                cnt = stock_map.get(itemid, 0)
                if stock_filter == "IN_STOCK" and cnt <= 0:
                    continue
                elif stock_filter == "LOW_STOCK" and (cnt <= 0 or cnt >= 10):
                    continue
                elif stock_filter == "OUT_OF_STOCK" and cnt > 0:
                    continue

                r = info.get("rarity", 1)
                if rarity_filter != "ALL":
                    try:
                        req_r = int(rarity_filter)
                        if r != req_r:
                            continue
                    except (ValueError, TypeError):
                        pass

                name_es = info.get("name_es", "")
                name_en = info.get("name_en", "")
                cooked_en = info.get("cooked_name_en", "")
                cooked_es = info.get("cooked_name_es", "")
                cat_display = t("cat_mushroom", default="Setas") if item_type == "MUSHROOM" else t("cat_beast", default="Criaturas")

                if query_tokens:
                    extra_names = " ".join(str(v) for k, v in info.items() if (k.startswith("name") or k.startswith("desc") or "cooked" in k) and isinstance(v, str))
                    searchable = f"{extra_names} {name_es} {name_en} {itemid} {item_type} {cat_display} {cooked_en} {cooked_es} mushroom seta shroom beast criatura t{r} tier{r} {r}★ {r}star".lower()
                    if not all(token in searchable for token in query_tokens):
                        continue

                display_title = i18n.get_entity_display_title(info)
                self.filtered_materials.append((itemid, display_title, cat_display, r, cnt, info, True))

        # Populate table
        self.table.blockSignals(True)
        self.table.clearSelection()
        self.table.setRowCount(0)
        self.table.setRowCount(len(self.filtered_materials))

        for row_idx, (itemid, name, cat, r, cnt, meta, is_sb) in enumerate(self.filtered_materials):
            # Column 0: Icon + Name
            item_name = QTableWidgetItem(f" {name}")
            nen = meta.get("name_en", "")
            art_path = find_material_art(itemid, nen, as_card=False)
            ico = get_icon(art_path, (44, 44))
            if ico and not ico.isNull():
                item_name.setIcon(ico)
            self.table.setItem(row_idx, 0, item_name)

            # Column 1: Stock in Storage
            stock_txt = t("inv_unit_str", qty=cnt) if cnt > 0 else "-"
            item_stock = QTableWidgetItem(stock_txt)
            item_stock.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if cnt > 0:
                item_stock.setForeground(Qt.GlobalColor.white)
            else:
                item_stock.setForeground(Qt.GlobalColor.gray)
            self.table.setItem(row_idx, 1, item_stock)

            # Column 2: Rarity Stars
            item_stars = QTableWidgetItem("★" * r)
            item_stars.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row_idx, 2, item_stars)

            # Column 3: ID (Type removed)
            item_id_w = QTableWidgetItem(itemid)
            item_id_w.setForeground(Qt.GlobalColor.gray)
            self.table.setItem(row_idx, 3, item_id_w)

        self.table.blockSignals(False)

        if self.filtered_materials:
            selected_id = self.current_selected_mat[0] if self.current_selected_mat else None
            row = next((i for i, entry in enumerate(self.filtered_materials) if entry[0] == selected_id), 0)
            self.table.selectRow(row)
            self._on_table_selection_changed()
        else:
            self.current_selected_mat = None
            self._clear_details()

    def _on_table_selection_changed(self):
        sel_rows = self.table.selectedItems()
        if not sel_rows:
            return
        row = sel_rows[0].row()
        if 0 <= row < len(self.filtered_materials):
            itemid, name, cat, r, cnt, meta, is_sb = self.filtered_materials[row]
            self.current_selected_mat = (itemid, name, cat, meta, is_sb)

            # 1. Update Title & Meta
            stars_str = "★" * r
            self.mat_title_lbl.setText(f"{name}\n({itemid}) • {stars_str}")
            self.mat_type_lbl.setText(t("mat_cat_info", cat=cat, rare=stars_str, id=itemid, default=f"Categoría: {cat} | Código: {itemid}"))

            # 2. Stock Indicator
            if cnt > 0:
                self.mat_stock_lbl.setText(t("mat_in_storage", qty=cnt, default=f"📦 En tu Almacén: {cnt:,} u."))
                self.mat_stock_lbl.setStyleSheet(f"color: {ACCENT_CYAN}; font-size: 10pt; font-weight: bold;")
            else:
                self.mat_stock_lbl.setText(t("mat_none_in_storage", default="📦 En tu Almacén: 0 u. (No tienes)"))
                self.mat_stock_lbl.setStyleSheet(f"color: {FG_MUTED}; font-size: 9.5pt;")

            # 3. Lore Description
            desc = get_item_desc(meta)
            if not desc:
                desc = meta.get("desc_es") or meta.get("desc_en") or meta.get("desc_zh") or t("mat_desc_default")
            self.mat_desc_lbl.setText(desc)

            # 4. Commercial / Value Info
            if is_sb:
                cur_lang = i18n.get_language()
                if cur_lang == "zh":
                    cooked_name = meta.get("cooked_name_zh") or meta.get("cooked_name_en") or ""
                elif cur_lang == "en":
                    cooked_name = meta.get("cooked_name_en") or meta.get("cooked_name_es") or ""
                else:
                    cooked_name = meta.get("cooked_name_es") or meta.get("cooked_name_en") or ""
                if cooked_name:
                    self.mat_price_lbl.setText(t("mat_val_cooked", default=f"🍳 Versión Asada: {cooked_name}", name=cooked_name))
                else:
                    self.mat_price_lbl.setText(t("mat_val_exploration", default=f"🍄 Exploración: {cat}", cat=cat))
            else:
                buy_kc = meta.get("buy_kc", 0)
                buy_re = meta.get("buy_re", 0)
                buy_bl = meta.get("buy_bl", 0)
                sell_kc = meta.get("sell_kc", 0)
                parts = []
                lbl_buy = t("mat_val_buy", default="Compra:")
                lbl_rec = t("mat_val_recycle", default="Reciclador:")
                lbl_bl = t("mat_val_bloodnium", default="Bloodnium:")
                lbl_sell = t("mat_val_sell", default="Venta:")
                if buy_kc: parts.append(f"💰 {lbl_buy} {buy_kc:,} KC")
                if buy_re: parts.append(f"♻️ {lbl_rec} {buy_re:,} RE")
                if buy_bl: parts.append(f"🩸 {lbl_bl} {buy_bl:,} BL")
                if sell_kc: parts.append(f"💵 {lbl_sell} {sell_kc:,} KC")
                self.mat_price_lbl.setText(" • ".join(parts) if parts else t("mat_val_exclusive", default="Material exclusivo de torre y misiones."))

            # 5. Artwork Card (260x130)
            nen = meta.get("name_en", "")
            card_path = find_material_art(itemid, nen, as_card=True)
            card_pix = get_pixmap(card_path, (260, 130), preserve_aspect=True)
            if not card_pix or card_pix.isNull():
                thumb_path = find_material_art(itemid, nen, as_card=False)
                card_pix = get_pixmap(thumb_path, (260, 130), preserve_aspect=True)

            if card_pix and not card_pix.isNull():
                self.mat_art_lbl.setPixmap(card_pix)
            else:
                self.mat_art_lbl.clear()

            # 6. Spinbox set to current count or 50 default
            self.qty_spin.blockSignals(True)
            self.qty_spin.setValue(cnt if cnt > 0 else 50)
            self.qty_spin.blockSignals(False)

    def _set_selected_mat_qty(self):
        if not self.current_selected_mat or not self.main_win.save_json:
            return
        itemid, name, cat, meta, is_sb = self.current_selected_mat
        qty = self.qty_spin.value()
        try:
            set_material_quantity(self.main_win.save_json, itemid, qty)
        except ValueError as exc:
            self.main_win._notify("error", str(exc), kind="error")
            return
        self.main_win._auto_save()
        self.filter_materials_list()
        self.main_win.update_hud()
        self.main_win.set_status(t("mat_added_to_storage_status", default=f"Almacén: establecido x{qty} de {name}.", qty=qty, name=name))

    def _quick_add_material_qty(self, delta):
        if not self.current_selected_mat or not self.main_win.save_json:
            return
        itemid, name, cat, meta, is_sb = self.current_selected_mat
        modifiers.add_material_to_storage(self.main_win.save_json, itemid, count=delta)
        self.main_win._auto_save()
        self.filter_materials_list()
        self.main_win.update_hud()
        self.main_win.set_status(t("mat_added_to_storage_status", default=f"Almacén: añadido +{delta} u. de {name}.", qty=delta, name=name))

    def _set_qty_selected(self, target_qty):
        if not self.current_selected_mat or not self.main_win.save_json:
            return
        self.qty_spin.setValue(target_qty)
        self._set_selected_mat_qty()

    def _on_table_double_clicked(self, item):
        if not self.current_selected_mat or not self.main_win.save_json:
            return
        itemid, name, cat, meta, is_sb = self.current_selected_mat
        cur_val = self.qty_spin.value()
        val, ok = QInputDialog.getInt(
            self,
            t("mat_custom_qty_title", default="Ajustar Cantidad"),
            t("mat_custom_qty_prompt", default=f"Introduce la cantidad deseada para {name} ({itemid}):", name=name, itemid=itemid),
            cur_val, 0, 999, 1
        )
        if ok:
            self._set_qty_selected(val)

    def max_all_materials_preset(self):
        save = self.main_win.save_json
        if not save:
            return
        modifiers.add_all_materials_to_storage(save, count=100)
        self.main_win._auto_save()
        self.filter_materials_list()
        self.main_win.update_hud()
        self.main_win._notify("mat_notify_stocked_title", "mat_notify_stocked_msg")

    def _update_storage_info(self):
        save = self.main_win.save_json
        if not save:
            return
        cl_items = save.get("soul", {}).get("cl", [])
        cap = len(cl_items)
        used = len([x for x in cl_items if x.get("type", -1) != -1 or x.get("eid", "") != ""])
        free = max(0, cap - used)
        self.mat_cap_indicator_lbl.setText(f"{t('bp_col_storage', default='Almacén')}: {used:,} / {cap:,} ({free:,} {t('f_slot_empty', default='libres')})")

    def _expand_coin_locker_add(self, amount):
        save = self.main_win.save_json
        if not save:
            return
        current_cap = len(save.get("soul", {}).get("cl", []))
        self._expand_coin_locker(current_cap + amount)

    def _expand_coin_locker(self, target_capacity):
        save = self.main_win.save_json
        if not save:
            return
        cl_items = save.get("soul", {}).get("cl", [])
        current_cap = len(cl_items)
        occupied_count = len([x for x in cl_items if x.get("type", -1) != -1 or x.get("eid", "") != ""])
        if target_capacity < occupied_count:
            self.main_win._notify("mat_locker_limit_title", "mat_locker_limit_msg", kind="warning", occ=occupied_count)
            return
        if target_capacity == current_cap:
            return

        old_c, new_c = modifiers.expand_storage_capacity(save, target_capacity=target_capacity)
        self.main_win._auto_save()
        self._update_storage_info()
        self.main_win.update_hud()
        self.main_win._notify("mat_locker_updated_title", "mat_locker_updated_msg", old=old_c, new=new_c, occ=occupied_count)

    def _expand_coin_locker_custom(self):
        save = self.main_win.save_json
        if not save:
            return
        cl_items = save.get("soul", {}).get("cl", [])
        current_cap = len(cl_items)
        occupied_count = len([x for x in cl_items if x.get("type", -1) != -1 or x.get("eid", "") != ""])
        prompt_txt = t("mat_locker_custom_prompt", default=f"Capacidad actual: {current_cap:,} casillas ({occupied_count:,} objetos).\nIntroduce la capacidad deseada:", cur=current_cap, occ=occupied_count)

        target, ok = QInputDialog.getInt(
            self,
            "🚀 " + t("mat_locker_cap_title", default="Capacidad del Coin Locker"),
            prompt_txt,
            max(occupied_count + 200, 6000),
            max(occupied_count, 100),
            50000,
            100
        )
        if ok and target != current_cap:
            self._expand_coin_locker(target)

    def _open_storage_manager(self):
        try:
            from ui_qt.dialogs.inventory_viewer import InventoryViewerDialog
            dlg = InventoryViewerDialog(
                self,
                self.main_win.save_json,
                getattr(self.main_win, "equipment_db", []),
                getattr(self.main_win, "materials_db", []),
                getattr(self.main_win, "shrooms_beasts_db", {})
            )
            dlg.exec()
            self.filter_materials_list()
            self._update_storage_info()
            self.main_win.update_hud()
        except Exception:
            self._expand_coin_locker_custom()

    def refresh_translations(self):
        if hasattr(self, "lbl_search"): self.lbl_search.setText(t("mat_search", default="🔍 Buscar:"))
        if hasattr(self, "lbl_cat"): self.lbl_cat.setText(t("mat_cat_lbl", default="Categoría:"))
        if hasattr(self, "lbl_stock"): self.lbl_stock.setText(t("mat_stock_lbl", default="Almacén:"))
        if hasattr(self, "lbl_rarity"): self.lbl_rarity.setText(t("mat_rarity_lbl", default="Rareza:"))
        if hasattr(self, "lbl_floors"): self.lbl_floors.setText(t("mat_floors_lbl", default="Torre:"))
        if hasattr(self, "floor_btn_widgets") and self.floor_btn_widgets:
            self.floor_btn_widgets[0].setText(t("mat_floor_all", default="TODOS"))
        if hasattr(self, "btn_open_storage"):
            self.btn_open_storage.setText(t("mat_storage_btn", default="📦 Coin Locker"))

        cur_cat = self.cat_cb.currentData()
        self.cat_cb.blockSignals(True)
        self.cat_cb.clear()
        for code, tr_key in CANONICAL_MATERIAL_CATEGORIES:
            self.cat_cb.addItem(t(tr_key, default=code), code)
        idx_c = self.cat_cb.findData(cur_cat)
        if idx_c >= 0:
            self.cat_cb.setCurrentIndex(idx_c)
        self.cat_cb.blockSignals(False)

        cur_stock = self.stock_cb.currentData()
        self.stock_cb.blockSignals(True)
        self.stock_cb.clear()
        self.stock_cb.addItem(t("mat_all", default="Todos"), "ALL")
        self.stock_cb.addItem(t("mat_in_stock", default="📦 En Stock (> 0)"), "IN_STOCK")
        self.stock_cb.addItem(t("mat_low_stock", default="⚠️ Stock Bajo (< 10)"), "LOW_STOCK")
        self.stock_cb.addItem(t("mat_out_stock", default="❌ Agotado (0)"), "OUT_OF_STOCK")
        idx_s = self.stock_cb.findData(cur_stock)
        if idx_s >= 0:
            self.stock_cb.setCurrentIndex(idx_s)
        self.stock_cb.blockSignals(False)

        cur_rare = self.rarity_cb.currentData()
        self.rarity_cb.blockSignals(True)
        self.rarity_cb.setItemText(0, t("decal_all", default="Todas"))
        idx_r = self.rarity_cb.findData(cur_rare)
        if idx_r >= 0:
            self.rarity_cb.setCurrentIndex(idx_r)
        self.rarity_cb.blockSignals(False)

        self.table.setHorizontalHeaderLabels([
            t("decal_col_icon", default="Icono / Nombre Oficial"),
            t("bp_col_storage", default="Almacén"),
            t("decal_col_rare", default="Rareza"),
            t("wm_col_code", default="Código Interno"),
        ])
        if hasattr(self, "search_entry"):
            self.search_entry.setPlaceholderText(t("search_placeholder", default="Nombre / ID..."))
        if hasattr(self, "lbl_search"):
            self.lbl_search.setText(t("mat_search", default="🔍 Buscar:"))
        if hasattr(self, "lbl_cat"):
            self.lbl_cat.setText(t("mat_cat_lbl", default="Categoría:"))
        if hasattr(self, "lbl_stock"):
            self.lbl_stock.setText(t("mat_stock_lbl", default="Almacén:"))
        if hasattr(self, "lbl_rarity"):
            self.lbl_rarity.setText(t("mat_rarity_lbl", default="Rareza:"))
        if hasattr(self, "lbl_floors"):
            self.lbl_floors.setText(t("mat_floors_lbl", default="Torre:"))
        self.box_detail.setTitle(t("mat_card_title", default="Ficha Oficial de Material R&D"))
        if hasattr(self, "box_value"):
            self.box_value.setTitle(t("mat_value_box_title", default="💰 Información Comercial & Reciclaje"))
        self.box_adjust.setTitle(t("mat_set_qty_lbl", default="Ajuste de Stock"))
        self.box_storage.setTitle(t("mat_locker_cap_title", default="Capacidad del Coin Locker"))
        self.btn_max_all.setText(t("mat_max_stock_btn", default="⭐ Maximizar Todos (100 u.)"))
        if hasattr(self, "btn_set_qty"):
            self.btn_set_qty.setText(t("mat_set_btn", default="Establecer"))
        if hasattr(self, "btn_max_sel"):
            self.btn_max_sel.setText(t("mat_btn_max_sel", default="Máx (999)"))
        if hasattr(self, "btn_clear_sel"):
            self.btn_clear_sel.setText(t("mat_btn_clear_sel", default="Vaciar (0)"))
        self.filter_materials_list()
        self._update_storage_info()
