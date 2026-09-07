# -*- coding: utf-8 -*-
"""
Decals Tab for LET IT DIE Save Editor (PySide6 Edition).
Exact layout, colors, and behavior parity with Cyberpunk Dark design.
"""

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QPixmap, QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QGroupBox, QLabel, QLineEdit, QPushButton, QComboBox,
    QSpinBox, QSplitter, QTableWidget, QTableWidgetItem,
    QScrollArea, QFrame, QMessageBox, QHeaderView, QInputDialog
)

import modifiers
import i18n
from i18n import t, get_item_name, get_item_desc
from core.decals import DECAL_ALIASES
from ui_qt.theme import (
    get_pixmap, get_icon, find_decal_art, ACCENT_GOLD, ACCENT_CYAN,
    ACCENT_GREEN, ACCENT_RED, FG_MUTED, FG_MAIN, BG_CARD
)

# Official Gravity Rush Collaboration Decals (Nos. 162-172 in master_skill)
GRAVITY_RUSH_DECAL_IDS = {
    "SKL_GRAVITY_DROPKICK", "SKL_GRAVITY_DROPKICK_P",
    "SKL_RG_STARTUP_SPDUP", "SKL_RG_STARTUP_SPDUP_P",
    "SKL_NDFALL_AUSTEALTH", "SKL_NDFALL_AUSTEALTH_P",
    "SKL_DEFUP_DEATH_PROOF", "SKL_DEFUP_DEATH_PROOF_P",
    "SKL_CRIUP_DECDUR_DOWN", "SKL_CRIUP_DECDUR_DOWN_P",
    "SKL_ATKUP_SLASHSTRIKE", "SKL_ATKUP_SLASHSTRIKE_P",
    "SKL_STMUP_DASHDODGE", "SKL_STMUP_DASHDODGE_P",
    "SKL_HPUP_ATKUP", "SKL_HPUP_ATKUP_P",
    "SKL_HPCUREUP_03", "SKL_HPCUREUP_03_P",
    "SKL_MONEYUP_03", "SKL_MONEYUP_03_P",
}


class DecalsTab(QWidget):
    def __init__(self, main_win):
        super().__init__()
        self.main_win = main_win
        self.current_selected_decal = None
        self.filtered_decals = []
        self.current_event_filter = "TODOS"
        self.current_style_filter = "TODOS"
        self._build_ui()

    def _build_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(8, 8, 8, 8)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        root_layout.addWidget(splitter)

        # =============================================================
        # LEFT PANEL: Search, Filters & Decals Table
        # =============================================================
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 4, 0)
        left_layout.setSpacing(6)

        # Filter Controls Row 1
        ctrl_f = QHBoxLayout()
        self.lbl_decal_search = QLabel(t("decal_search", default="🔍 Buscar:"))
        ctrl_f.addWidget(self.lbl_decal_search)
        self.search_entry = QLineEdit()
        self.search_entry.setPlaceholderText(t("search_placeholder", default="Nombre / ID..."))
        self.search_entry.textChanged.connect(self.filter_decals_list)
        ctrl_f.addWidget(self.search_entry)

        self.lbl_decal_rare = QLabel(t("decal_rare_lbl", default="Rareza:"))
        ctrl_f.addWidget(self.lbl_decal_rare)
        self.rarity_cb = QComboBox()
        self.rarity_cb.addItem(t("decal_all", default="Todas"), "ALL")
        for stars in range(1, 6):
            self.rarity_cb.addItem(f"{stars}★", stars)
        ctrl_f.addWidget(self.rarity_cb)

        self.lbl_decal_type = QLabel(t("decal_type_lbl", default="Tipo:"))
        ctrl_f.addWidget(self.lbl_decal_type)
        self.type_cb = QComboBox()
        self.type_cb.addItem(t("decal_all", default="Todas"), "ALL")
        self.type_cb.addItem(t("decal_premium", default="Premium (_P)"), "PREMIUM")
        self.type_cb.addItem(t("decal_standard", default="Estándar"), "STANDARD")
        ctrl_f.addWidget(self.type_cb)

        self.lbl_decal_poss = QLabel(t("decal_poss_lbl", default="Posesión:"))
        ctrl_f.addWidget(self.lbl_decal_poss)
        self.poss_cb = QComboBox()
        self.poss_cb.addItem(t("decal_all", default="Todas"), "ALL")
        self.poss_cb.addItem(t("decal_owned", default="📦 Poseídas (> 0)"), "IN_STOCK")
        self.poss_cb.addItem(t("decal_missing", default="❌ Faltantes (0)"), "MISSING")
        ctrl_f.addWidget(self.poss_cb)

        self.rarity_cb.currentIndexChanged.connect(self.filter_decals_list)
        self.type_cb.currentIndexChanged.connect(self.filter_decals_list)
        self.poss_cb.currentIndexChanged.connect(self.filter_decals_list)
        left_layout.addLayout(ctrl_f)

        # Row 2: Eventos / Colaboraciones Quick Buttons Bar
        events_row = QHBoxLayout()
        self.lbl_events = QLabel(t("decal_events_lbl", default="Eventos:"))
        self.lbl_events.setStyleSheet(f"color: {ACCENT_GOLD}; font-weight: bold; font-size: 8.5pt;")
        events_row.addWidget(self.lbl_events)

        self.event_buttons = []
        event_defs = [
            (t("decal_event_all", default="Todos"), "TODOS"),
            ("💥 WoT", "WOT"),
            ("⚔️ NMH", "NMH"),
            ("🎯 K7", "KILLER7"),
            ("🌀 GR", "GRAVITY_RUSH"),
            ("💀 DV", "DEATHVERSE"),
            ("👑 Tengoku", "TENGOKU_META"),
        ]
        for label, code in event_defs:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setChecked(code == "TODOS")
            btn.clicked.connect(lambda chk=False, m=code: self._set_decal_event_filter(m))
            events_row.addWidget(btn)
            self.event_buttons.append((btn, code))

        events_row.addStretch()
        left_layout.addLayout(events_row)

        # Row 3: Estilos de Juego Tácticos Quick Buttons Bar
        styles_row = QHBoxLayout()
        self.lbl_styles = QLabel(t("decal_styles_lbl", default="Estilos:"))
        self.lbl_styles.setStyleSheet(f"color: {ACCENT_CYAN}; font-weight: bold; font-size: 8.5pt;")
        styles_row.addWidget(self.lbl_styles)

        self.style_buttons = []
        style_defs = [
            (t("decal_style_all", default="Todos"), "TODOS"),
            (t("decal_style_addicts", default="Adictos"), "ADDICTS"),
            (t("decal_style_crit", default="Críticos"), "CRIT_DMG"),
            (t("decal_style_tank", default="Tanque"), "TANK_DEF"),
            (t("decal_style_vamp", default="Vampiro"), "VAMP_SURV"),
            (t("decal_style_farm", default="Farm"), "FARM_QOL"),
            (t("decal_style_sets", default="Sets"), "SETS"),
        ]
        for label, code in style_defs:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setChecked(code == "TODOS")
            btn.clicked.connect(lambda chk=False, m=code: self._set_decal_style_filter(m))
            styles_row.addWidget(btn)
            self.style_buttons.append((btn, code))

        styles_row.addStretch()
        left_layout.addLayout(styles_row)

        # Bulk Actions Row 4
        act_f = QHBoxLayout()
        self.btn_meta = QPushButton(t("decal_pack_meta", default="🏆 Pack Meta"))
        self.btn_meta.clicked.connect(self.add_meta_decals_preset)
        act_f.addWidget(self.btn_meta)

        act_f.addStretch()
        self.lbl_decal_copies = QLabel(t("decal_copies_lbl", default="Copias:"))
        act_f.addWidget(self.lbl_decal_copies)
        self.copies_spin = QSpinBox()
        self.copies_spin.setRange(1, 99)
        self.copies_spin.setValue(3)
        self.copies_spin.setFixedWidth(50)
        act_f.addWidget(self.copies_spin)
        self.btn_unlock_all = QPushButton(t("decal_unlock_all", default="✨ Desbloquear Todas"))
        self.btn_unlock_all.setProperty("accent", "true")
        self.btn_unlock_all.clicked.connect(self.unlock_all_decals_preset)
        act_f.addWidget(self.btn_unlock_all)
        left_layout.addLayout(act_f)

        # Table (5 Columns matching Tkinter: Icon+Name, Stars, ID, Type, Qty)
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            t("decal_col_icon", default="Calcomanía"),
            t("decal_col_rare", default="Rareza"),
            t("decal_col_id", default="ID"),
            t("decal_col_type", default="Tipo"),
            t("decal_col_qty", default="Copias")
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setIconSize(QSize(44, 44))
        self.table.verticalHeader().setDefaultSectionSize(48)
        self.table.itemSelectionChanged.connect(self._on_table_selection_changed)
        self.table.itemClicked.connect(lambda item=None: self._on_table_selection_changed())
        self.table.itemDoubleClicked.connect(self._on_table_double_clicked)
        left_layout.addWidget(self.table)

        splitter.addWidget(left_widget)

        # =============================================================
        # RIGHT PANEL: Selected Decal Card & Effect Viewer (Scrollable)
        # =============================================================
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(4, 0, 4, 0)
        right_layout.setSpacing(8)

        self.box_detail = QGroupBox(t("decal_card_title", default="Ficha Técnica de la Calcomanía"))
        detail_v = QVBoxLayout(self.box_detail)
        detail_v.setContentsMargins(10, 10, 10, 10)
        detail_v.setSpacing(8)

        # Large Decal Art (160x160 Showcase)
        art_center = QHBoxLayout()
        self.decal_art_lbl = QLabel()
        self.decal_art_lbl.setFixedSize(160, 160)
        self.decal_art_lbl.setStyleSheet("border: 2px solid #252b40; border-radius: 8px; background-color: #151824;")
        self.decal_art_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        art_center.addStretch()
        art_center.addWidget(self.decal_art_lbl)
        art_center.addStretch()
        detail_v.addLayout(art_center)

        self.decal_name_lbl = QLabel(t("decal_select_prompt", default="Selecciona una calcomanía"))
        self.decal_name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.decal_name_lbl.setWordWrap(True)
        self.decal_name_lbl.setStyleSheet(f"color: {ACCENT_GOLD}; font-size: 11pt; font-weight: bold;")
        detail_v.addWidget(self.decal_name_lbl)

        self.decal_meta_lbl = QLabel("---")
        self.decal_meta_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.decal_meta_lbl.setStyleSheet(f"color: {FG_MUTED}; font-size: 9pt;")
        detail_v.addWidget(self.decal_meta_lbl)

        # Effect Description Box
        self.box_effect = QGroupBox(t("decal_effect_box_title", default="📜 Efecto Oficial Chokufunsha"))
        eff_v = QVBoxLayout(self.box_effect)
        eff_v.setContentsMargins(8, 8, 8, 8)
        self.decal_effect_lbl = QLabel(t("decal_select_prompt", default="Selecciona una calcomanía para ver sus efectos."))
        self.decal_effect_lbl.setWordWrap(True)
        self.decal_effect_lbl.setStyleSheet("font-size: 9pt; color: #ffffff; line-height: 1.3;")
        eff_v.addWidget(self.decal_effect_lbl)
        detail_v.addWidget(self.box_effect)

        # Inventory Adjustment Box
        self.box_inv = QGroupBox(t("decal_copies_edit_lbl", default="Copias en Bolsa / Almacén"))
        inv_v = QVBoxLayout(self.box_inv)
        inv_v.setContentsMargins(8, 8, 8, 8)
        inv_v.setSpacing(6)

        qty_h = QHBoxLayout()
        qty_h.addWidget(QLabel("Copias:"))
        self.inv_spin = QSpinBox()
        self.inv_spin.setRange(0, 99)
        self.inv_spin.setFixedWidth(80)
        self.inv_spin.valueChanged.connect(self._on_inv_spin_changed)
        qty_h.addWidget(self.inv_spin)
        qty_h.addStretch()
        inv_v.addLayout(qty_h)

        quick_btns = QHBoxLayout()
        for q_val in [1, 3, 5, 10]:
            btn = QPushButton(f"+{q_val}")
            btn.clicked.connect(lambda checked=False, val=q_val: self._add_copies(val))
            quick_btns.addWidget(btn)

        self.btn_zero = QPushButton(t("decal_zero", default="Agotar (0)"))
        self.btn_zero.setProperty("danger", "true")
        self.btn_zero.clicked.connect(lambda: self.inv_spin.setValue(0))
        quick_btns.addWidget(self.btn_zero)
        inv_v.addLayout(quick_btns)

        detail_v.addWidget(self.box_inv)

        right_layout.addWidget(self.box_detail)
        right_layout.addStretch()

        scroll_area.setWidget(right_container)
        splitter.addWidget(scroll_area)
        splitter.setSizes([620, 360])

    def _set_decal_event_filter(self, mode):
        if self.current_event_filter == mode and mode != "TODOS":
            self.current_event_filter = "TODOS"
        else:
            self.current_event_filter = mode

        for btn, code in getattr(self, "event_buttons", []):
            btn.setChecked(code == self.current_event_filter)

        self.filter_decals_list()

    def _set_decal_style_filter(self, mode):
        if self.current_style_filter == mode and mode != "TODOS":
            self.current_style_filter = "TODOS"
        else:
            self.current_style_filter = mode

        for btn, code in getattr(self, "style_buttons", []):
            btn.setChecked(code == self.current_style_filter)

        self.filter_decals_list()

    @property
    def decal_event_filter(self):
        class _Var:
            def __init__(self, tab): self.tab = tab
            def get(self): return self.tab.current_event_filter
            def set(self, val): self.tab._set_decal_event_filter(val)
        return _Var(self)

    @property
    def decal_style_filter(self):
        class _Var:
            def __init__(self, tab): self.tab = tab
            def get(self): return self.tab.current_style_filter
            def set(self, val): self.tab._set_decal_style_filter(val)
        return _Var(self)

    def refresh_data(self):
        """Loads and filters the decals catalog."""
        self.filter_decals_list()

    def _clear_details(self):
        self.current_selected_decal = None
        self.decal_name_lbl.setText(t("decal_select_prompt", default="Selecciona una calcomanía"))
        self.decal_meta_lbl.setText("---")
        self.decal_effect_lbl.setText(t("decal_select_prompt", default="Selecciona una calcomanía para ver sus efectos."))
        self.decal_art_lbl.clear()
        self.inv_spin.blockSignals(True)
        self.inv_spin.setValue(0)
        self.inv_spin.blockSignals(False)

    def filter_decals_list(self):
        save = self.main_win.save_json
        decals_db = getattr(self.main_win, "decals_db", [])
        decals_map = getattr(self.main_win, "decals_map", {})

        query = self.search_entry.text().lower().strip()
        rarity_filter = self.rarity_cb.currentText()
        selected_rarity = self.rarity_cb.currentData() or "ALL"
        type_code = self.type_cb.currentData() or "ALL"
        poss_code = self.poss_cb.currentData() or "ALL"
        event_filter = self.current_event_filter
        style_filter = self.current_style_filter

        psskl_counts = {}
        if save:
            psskl_list = save.get("soul", {}).get("skl", {}).get("psskl", [])
            for item in psskl_list:
                raw_id = item.get("sklid", "")
                if not raw_id:
                    continue
                canonical = DECAL_ALIASES.get(raw_id, raw_id)
                psskl_counts[canonical] = max(psskl_counts.get(canonical, 0), item.get("cnt", 0))

        all_ids = set([d["id"] for d in decals_db if d.get("id") not in DECAL_ALIASES]) | set(psskl_counts.keys())

        self.filtered_decals = []
        for did in sorted(all_ids):
            if did in DECAL_ALIASES:
                continue
            is_p = did.endswith("_P")
            cnt = psskl_counts.get(did, 0)
            base_id = did[:-2] if is_p else did
            info = decals_map.get(did) or decals_map.get(base_id) or {}
            if not info:
                info = {"id": did, "name": did}

            # 1. Type filter
            if type_code == "PREMIUM" and not is_p:
                continue
            elif type_code == "STANDARD" and is_p:
                continue

            # 2. Possession filter
            if poss_code in ("IN_STOCK", "OWNED") and cnt <= 0:
                continue
            elif poss_code == "MISSING" and cnt > 0:
                continue

            # 3. Rarity filter
            d_rarity = info.get("rarity", 1 if not is_p else 3)
            if selected_rarity != "ALL":
                try:
                    if int(d_rarity) != int(selected_rarity):
                        continue
                except (ValueError, TypeError):
                    pass

            name_es = info.get("name_es", did.replace("SKL_", "").replace("_", " "))
            name_en = info.get("name_en", "")
            name_zh = info.get("name_zh", "")
            desc_es = info.get("desc_es", "")
            desc_en = info.get("desc_en", "")
            desc_zh = info.get("desc_zh", "")
            extra_lang_texts = " ".join(str(v) for k, v in info.items() if (k.startswith("name") or k.startswith("desc")) and isinstance(v, str))
            full_txt = f"{did} {name_en} {name_es} {desc_en} {desc_es} {desc_zh} {extra_lang_texts}".lower()

            # 4. Event / Collab filter
            if event_filter != "TODOS":
                if event_filter == "WOT":
                    if not ("_wot" in did.lower() or "wot" in did.lower() or any(k in full_txt for k in ["world of tanks", "tiger ii", "t-34"])):
                        continue
                elif event_filter == "NMH":
                    if not ("_nmh" in did.lower() or any(k in full_txt for k in ["travis", "sylvia", "shinobu", "bad girl", "beam katana", "no more heroes"])):
                        continue
                elif event_filter == "KILLER7":
                    if not ("_k7" in did.lower() or any(k in full_txt for k in ["garcian", "dan smith", "kaede", "kevin", "coyote", "mask de smith", "con smith", "killer7", "harman", "iwazaru", "samantha", "queen of the wolves"])):
                        continue
                elif event_filter == "GRAVITY_RUSH":
                    if did not in GRAVITY_RUSH_DECAL_IDS and "gravity rush" not in full_txt:
                        continue
                elif event_filter == "DEATHVERSE":
                    if not any(k in full_txt for k in ["deathverse", "uncle-d2", "bryan zemeckis"]):
                        continue
                elif event_filter == "TENGOKU_META":
                    meta_keys = ["ultimate fighter", "golden gym", "serial killer", "joker", "super heavy tank", "king of the wolves", "tengoku", "professional cosplayer", "special unit captain", "critical attack", "below the belt", "spy", "rich man"]
                    if not any(k in full_txt for k in meta_keys):
                        continue

            # 5. Playstyle filter
            if style_filter != "TODOS":
                if style_filter == "ADDICTS":
                    if not ("_atkup_" in did.lower() or "addict" in full_txt or "fanático" in full_txt or "fan de la" in full_txt or "狂热" in full_txt):
                        continue
                elif style_filter == "CRIT_DMG":
                    if not any(k in full_txt for k in ["one shot one kill", "un disparo", "critical", "crítico", "bull", "toro", "barbarian", "bárbaro", "clover", "trébol", "five-leaf", "暴击", "一击必杀"]):
                        continue
                elif style_filter == "TANK_DEF":
                    if not any(k in full_txt for k in ["tank", "tanque", "diamond", "diamante", "poison eater", "comeveneno", "defender", "defensor", "iron wall", "muro de hierro", "gourmand", "glotón", "heavy tank", "super heavy tank", "防御", "坦克"]):
                        continue
                elif style_filter == "VAMP_SURV":
                    if not any(k in full_txt for k in ["vampire", "vampiro", "super long tail", "cola super larga", "mosquito", "golden heart", "corazón de oro", "drain", "drenaje", "吸血", "回血", "survivor", "superviviente"]):
                        continue
                elif style_filter == "FARM_QOL":
                    if not any(k in full_txt for k in ["treasure hunter", "cazatesoros", "marathon", "maratón", "rich man", "ricachón", "express pass", "lucky shot", "tiro afortunado", "oriental medicine", "medicina oriental", "golden lucky", "寻宝", "跑图", "qol"]):
                        continue
                elif style_filter == "SETS":
                    is_set = (
                        "_ability_up" in did.lower() or 
                        "armor bonus" in desc_en.lower() or 
                        "bonificación de armadura" in desc_es.lower() or 
                        "套装" in desc_zh.lower() or 
                        "full set" in desc_en.lower() or 
                        "conjunto completo" in desc_es.lower() or 
                        any(k in full_txt for k in ["cosplayer", "clay figurine", "combat diver", "happy wheeler", "trigger happy", "disparo alegre", "king of coal", "rey del carbón", "robin hood", "flashdance", "pinch hitter", "thunder road", "pro bowler", "hagakure"])
                    )
                    if not is_set:
                        continue

            # 6. Search query (supports multi-token)
            if query:
                tokens = query.split()
                if not all(tok in full_txt for tok in tokens):
                    continue

            self.filtered_decals.append((did, info, d_rarity, is_p, cnt))

        # Populate table
        self.table.blockSignals(True)
        self.table.clearSelection()
        self.table.setRowCount(0)
        self.table.setRowCount(len(self.filtered_decals))

        for row_idx, (did, info, stars, is_p, cnt) in enumerate(self.filtered_decals):
            display_name = i18n.get_entity_display_title(info) or i18n.get_item_name(info) or did
            std_txt = t("decal_badge_std", default="Estándar")
            prem_txt = t("decal_badge_prem", default="Premium (_P)")

            # Column 0: Name + Icon
            item_name = QTableWidgetItem(f" {display_name}")
            d_art = find_decal_art(did, is_premium=is_p)
            ico = get_icon(d_art, (44, 44))
            if ico and not ico.isNull():
                item_name.setIcon(ico)
            self.table.setItem(row_idx, 0, item_name)

            # Column 1: Stars
            item_stars = QTableWidgetItem(f"{stars}★")
            item_stars.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row_idx, 1, item_stars)

            # Column 2: ID
            item_id = QTableWidgetItem(did)
            item_id.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
            item_id.setForeground(QColor(FG_MUTED))
            self.table.setItem(row_idx, 2, item_id)

            # Column 3: Type
            item_type = QTableWidgetItem(prem_txt if is_p else std_txt)
            item_type.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if is_p:
                item_type.setForeground(QColor(ACCENT_GOLD))
            else:
                item_type.setForeground(QColor(FG_MUTED))
            self.table.setItem(row_idx, 3, item_type)

            # Column 4: Qty
            item_qty = QTableWidgetItem(f"x{cnt}" if cnt > 0 else "-")
            item_qty.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if cnt > 0:
                item_qty.setForeground(Qt.GlobalColor.white)
            else:
                item_qty.setForeground(Qt.GlobalColor.gray)
            self.table.setItem(row_idx, 4, item_qty)

        self.table.blockSignals(False)

        if self.filtered_decals:
            selected_id = self.current_selected_decal.get("id") if self.current_selected_decal else None
            row = next((i for i, entry in enumerate(self.filtered_decals) if entry[0] == selected_id), 0)
            self.table.selectRow(row)
            self._on_table_selection_changed()
        else:
            self._clear_details()

    def _on_table_selection_changed(self, *args):
        sel_rows = self.table.selectedItems()
        if not sel_rows:
            return
        row = sel_rows[0].row()
        if 0 <= row < len(self.filtered_decals):
            did, info, stars, is_p, cnt = self.filtered_decals[row]
            self.current_selected_decal = {**info, "id": did}

            display_name = i18n.get_entity_display_title(info) or i18n.get_item_name(info) or did
            std_txt = t("decal_badge_std", default="Estándar")
            prem_txt = t("decal_badge_prem", default="Premium (_P)")
            type_str = prem_txt if is_p else std_txt

            self.decal_name_lbl.setText(f"{display_name}\n({did}) • {stars}★")
            self.decal_meta_lbl.setText(t("decal_type_and_owned", type=type_str, cnt=cnt, default=f"Tipo: {type_str} | Copias: {cnt}"))

            desc = i18n.get_item_desc(info) or t("decal_default_desc", default="Sin descripción disponible.")
            self.decal_effect_lbl.setText(desc)

            d_art = find_decal_art(did, is_premium=is_p)
            pix = get_pixmap(d_art, (160, 160), preserve_aspect=True)
            if pix and not pix.isNull():
                self.decal_art_lbl.setPixmap(pix)
            else:
                self.decal_art_lbl.clear()

            self.inv_spin.blockSignals(True)
            self.inv_spin.setValue(cnt)
            self.inv_spin.blockSignals(False)

    def _on_table_double_clicked(self, item):
        if not self.current_selected_decal or not self.main_win.save_json:
            return
        did = self.current_selected_decal.get("id")
        curr_cnt = self.inv_spin.value()
        new_cnt, ok = QInputDialog.getInt(
            self,
            t("decal_dialog_title", default="Modificar Calcomanía"),
            t("decal_dialog_prompt", did=did, default=f"Copias para '{did}':"),
            curr_cnt,
            0,
            99
        )
        if ok:
            self.inv_spin.setValue(new_cnt)

    def _on_inv_spin_changed(self, val):
        if not self.current_selected_decal or not self.main_win.save_json:
            return
        did = self.current_selected_decal.get("id")
        is_p = did.endswith("_P")
        modifiers.add_or_update_decals(self.main_win.save_json, [did], count=val, premium=is_p)
        self.main_win._auto_save()
        self.main_win.update_hud()
        sel = self.table.currentRow()
        if sel >= 0 and sel < len(self.filtered_decals):
            did_cur, info, stars, is_p_cur, _ = self.filtered_decals[sel]
            self.filtered_decals[sel] = (did_cur, info, stars, is_p_cur, val)
            item_qty = self.table.item(sel, 4)
            if item_qty:
                item_qty.setText(f"x{val}" if val > 0 else "-")
                item_qty.setForeground(Qt.GlobalColor.white if val > 0 else Qt.GlobalColor.gray)
            std_txt = t("decal_badge_prem", default="Premium (_P)") if is_p else t("decal_badge_std", default="Estándar")
            self.decal_meta_lbl.setText(t("decal_type_and_owned", type=std_txt, cnt=val, default=f"Tipo: {std_txt} | Copias: {val}"))

    def _add_copies(self, amount):
        cur = self.inv_spin.value()
        self.inv_spin.setValue(min(99, cur + amount))

    def add_meta_decals_preset(self):
        save = self.main_win.save_json
        if not save:
            return
        count = self.copies_spin.value()
        modifiers.add_top_meta_decals(save, count=count)
        self.main_win._auto_save()
        self.filter_decals_list()
        self.main_win.update_hud()
        self.main_win._notify("mb_meta_decals_title", "mb_meta_decals_msg")

    def unlock_all_decals_preset(self):
        save = self.main_win.save_json
        if not save:
            return
        count = self.copies_spin.value()
        modifiers.unlock_all_decals(save, count=count, premium=True)
        self.main_win._auto_save()
        self.filter_decals_list()
        self.main_win.update_hud()
        self.main_win._notify("mb_all_decals_title", "mb_all_decals_msg", qty=count)

    def refresh_translations(self):
        self.table.setHorizontalHeaderLabels([
            t("decal_col_icon", default="Calcomanía"),
            t("decal_col_rare", default="Rareza"),
            t("decal_col_id", default="ID"),
            t("decal_col_type", default="Tipo"),
            t("decal_col_qty", default="Copias")
        ])
        if hasattr(self, 'search_entry'):
            self.search_entry.setPlaceholderText(t("search_placeholder", default="Nombre / ID..."))
        if hasattr(self, 'lbl_decal_search'):
            self.lbl_decal_search.setText(t("decal_search", default="🔍 Buscar:"))
        if hasattr(self, 'lbl_decal_rare'):
            self.lbl_decal_rare.setText(t("decal_rare_lbl", default="Rareza:"))
        if hasattr(self, 'lbl_decal_type'):
            self.lbl_decal_type.setText(t("decal_type_lbl", default="Tipo:"))
        if hasattr(self, 'lbl_decal_poss'):
            self.lbl_decal_poss.setText(t("decal_poss_lbl", default="Posesión:"))
        if hasattr(self, 'lbl_events'):
            self.lbl_events.setText(t("decal_events_lbl", default="Eventos:"))
        if hasattr(self, 'lbl_styles'):
            self.lbl_styles.setText(t("decal_styles_lbl", default="Estilos:"))
        if hasattr(self, 'lbl_decal_copies'):
            self.lbl_decal_copies.setText(t("decal_copies_lbl", default="Copias:"))

        if hasattr(self, 'rarity_cb'):
            cur_r = self.rarity_cb.currentData()
            self.rarity_cb.blockSignals(True)
            self.rarity_cb.clear()
            self.rarity_cb.addItem(t("decal_all", default="Todas"), "ALL")
            for stars in range(1, 6):
                self.rarity_cb.addItem(f"{stars}★", stars)
            idx = self.rarity_cb.findData(cur_r)
            if idx >= 0:
                self.rarity_cb.setCurrentIndex(idx)
            self.rarity_cb.blockSignals(False)

        if hasattr(self, 'type_cb'):
            cur_t = self.type_cb.currentData()
            self.type_cb.blockSignals(True)
            self.type_cb.clear()
            self.type_cb.addItem(t("decal_all", default="Todas"), "ALL")
            self.type_cb.addItem(t("decal_premium", default="Premium (_P)"), "PREMIUM")
            self.type_cb.addItem(t("decal_standard", default="Estándar"), "STANDARD")
            idx = self.type_cb.findData(cur_t)
            if idx >= 0:
                self.type_cb.setCurrentIndex(idx)
            self.type_cb.blockSignals(False)

        if hasattr(self, 'poss_cb'):
            cur_p = self.poss_cb.currentData()
            self.poss_cb.blockSignals(True)
            self.poss_cb.clear()
            self.poss_cb.addItem(t("decal_all", default="Todas"), "ALL")
            self.poss_cb.addItem(t("decal_owned", default="📦 Poseídas (> 0)"), "IN_STOCK")
            self.poss_cb.addItem(t("decal_missing", default="❌ Faltantes (0)"), "MISSING")
            idx = self.poss_cb.findData(cur_p)
            if idx >= 0:
                self.poss_cb.setCurrentIndex(idx)
            self.poss_cb.blockSignals(False)

        self.box_detail.setTitle(t("decal_card_title", default="Ficha Técnica de la Calcomanía"))
        self.box_inv.setTitle(t("decal_copies_edit_lbl", default="Copias en Bolsa / Almacén"))
        if hasattr(self, 'btn_zero'):
            self.btn_zero.setText(t("decal_zero", default="Agotar (0)"))
        self.btn_meta.setText(t("decal_pack_meta", default="🏆 Pack Meta"))
        self.btn_unlock_all.setText(t("decal_unlock_all", default="✨ Desbloquear Todas"))
        self.filter_decals_list()

