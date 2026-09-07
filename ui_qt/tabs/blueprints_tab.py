# -*- coding: utf-8 -*-
"""
Blueprints & Chokufunsha R&D Tab for LET IT DIE Save Editor (PySide6 Edition).
Exact layout, colors, and behavior parity with Cyberpunk Dark design.
"""

import re
import os
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QPixmap, QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QGroupBox, QLabel, QLineEdit, QPushButton, QComboBox,
    QSpinBox, QCheckBox, QSplitter, QTableWidget, QTableWidgetItem,
    QScrollArea, QFrame, QMessageBox, QHeaderView
)

import modifiers
import i18n
from i18n import t, get_item_name, get_set_name, get_entity_display_title
from ui_qt.theme import (
    get_pixmap, get_icon, find_equipment_art, resolve_icon_path,
    ACCENT_GOLD, ACCENT_CYAN, ACCENT_BLUE, ACCENT_GREEN, ACCENT_RED, ACCENT_PINK,
    FG_MUTED, FG_MAIN, BG_CARD, BG_PANEL
)
from ui_qt.dialogs.armor_set_viewer import ArmorSetViewerDialog

WP_SERIES_DAMAGE = {
    "000": "BLUNT",    # Fists
    "001": "SLASH",    # Jungle Machete
    "002": "SLASH",    # Butterfly Knife
    "003": "SLASH",    # Steel Axe
    "004": "PIERCE",   # Robber Crossbow
    "005": "BLUNT",    # Metal Bat
    "006": "SLASH",    # Buzzsaw Knuckles
    "007": "FIRE",     # FFWF Flamethrower
    "011": "BLUNT",    # Iron Hammer
    "012": "SLASH",    # Combat Pickaxe / Rake
    "013": "PIERCE",   # Knight's Lance
    "016": "SLASH",    # Masamune Blade
    "017": "PIERCE",   # Glinty Magnum
    "018": "ELECTRIC", # Stun Rod
    "019": "SLASH",    # Longsword / Dragon Buster
    "020": "POISON",   # Iron Claw / Nightmare Claw
    "021": "PIERCE",   # Pitbull Shotgun
    "023": "FIRE",     # Landmine
    "024": "BLUNT",    # Striker Flail
    "025": "PIERCE",   # DUKE Sniper Rifle
    "026": "ELECTRIC", # Cleaver Saber
    "028": "BLUNT",    # Pitching Machine
    "029": "FIRE",     # Flame Wand
    "030": "BLUNT",    # Loaded Glove / Boxing
    "031": "PIERCE",   # KAMAS Assault Rifle
    "032": "PIERCE",   # Nail Gun
    "033": "SLASH",    # Brutal Yo-Yo
    "034": "ELECTRIC", # Plasma Welding Gun
    "035": "BLUNT",    # Bowling Stomper
    "036": "PIERCE",   # Drill Arm
    "037": "FIRE",     # Red Hot Iron / Death Burner Iron
    "038": "SLASH",    # Tactical Shovel
    "039": "SLASH",    # Cyclone Shuriken
    "040": "FIRE",     # Fireball Baton
    "041": "BLUNT",    # Motor Psycho
    "042": "POISON",   # Pork Chopper / Zombie Chopper / Predator
    "043": "BLUNT",    # Apocalyptic Hockey Stick
    "044": "FIRE",     # Fireworks Launcher
    "045": "PIERCE",   # M-404 Rocket Launcher
    "046": "PIERCE",   # Hunting Bow
    "047": "ELECTRIC", # Lightning Wand / Thor's Wand
    "048": "POISON",   # Chainsaw Viper / Shark / Black Mamba
    "050": "SLASH",    # Grim Reaper Scythe
    "051": "SLASH",    # Jackal Sword
    "052": "SLASH",    # Jackal Yo-Yo
    "053": "PIERCE",   # Jackal Blaster
    "054": "BLUNT",    # Spike Crusher
    "055": "ELECTRIC", # Static Massager
    "056": "PIERCE",   # M2G-87
    "057": "ELECTRIC", # Vajra of Light / God
    "058": "POISON",   # Head of Medusa
}


class BlueprintsTab(QWidget):
    def __init__(self, main_win):
        super().__init__()
        self.main_win = main_win
        self.current_selected_bp = None
        self.filtered_blueprints = []
        self.current_collab_filter = "TODOS"
        self.armor_set_by_item_id = {}
        self._build_armor_set_index()
        self._build_ui()

    def _build_armor_set_index(self):
        self.armor_set_by_item_id = {}
        for s in getattr(self.main_win, "armor_sets", []):
            for t_item in s.get("tiers", []):
                for slot in ["head", "body", "legs"]:
                    p = t_item.get(slot)
                    if p and "id" in p:
                        self.armor_set_by_item_id[p["id"]] = (s, t_item, p)
                        self.armor_set_by_item_id[f"{p['id']}_G"] = (s, t_item, p)
                wp = t_item.get("weapon")
                if wp and "id" in wp:
                    self.armor_set_by_item_id[wp["id"]] = (s, t_item, wp)
                    self.armor_set_by_item_id[f"{wp['id']}_G"] = (s, t_item, wp)

    def _get_item_wiki_meta(self, item):
        itemid = item.get("id", "")
        raw_type = item.get("raw_type", "")
        # 1. Slot
        if raw_type == "PTTP_HEAD" or "_HEAD_" in itemid:
            slot = t("slot_head", default="Cabeza")
            slot_key = "head"
        elif raw_type == "PTTP_BODY" or "_TOPS_" in itemid:
            slot = t("slot_body", default="Torso")
            slot_key = "chest"
        elif raw_type in ("PTTP_PANTS", "PTTP_LEGS") or "_BTM_" in itemid:
            slot = t("slot_pants", default="Piernas")
            slot_key = "legs"
        else:
            slot = t("slot_weapon", default="Arma")
            slot_key = "weapon"

        # 2. Faction
        name_en_l = (item.get("name_en") or "").lower()
        name_es_l = (item.get("name_es") or "").lower()
        full_text = f"{itemid} {name_en_l} {name_es_l}".lower()

        if (
            any(k in itemid for k in ["PT_TBR", "TENGOKU", "WHITE", "NAPALM", "THUNDER", "WIND", "WP054", "WP055", "WP056", "WP057", "WP058"]) or
            any(k in full_text for k in ["white steel", "red napalm", "black thunder", "pale wind", "m2g", "spike crusher", "static massager", "vajra", "medusa"])
        ):
            faction = t("bp_fac_44ce", default="4 Forcemen & Tengoku")
            faction_key = "FORCEMEN"
        elif any(k in itemid for k in ["PT_JAC", "PT_JCL", "JACKAL", "WP051", "WP052", "WP053"]) or "jackal" in full_text:
            faction = t("bp_fac_jackals", default="Jackals")
            faction_key = "JACKAL"
        elif "PT_REC" in itemid or "_0b" in itemid.lower() or " re" in full_text:
            faction = t("bp_fac_re", default="RE (Reciclador)")
            faction_key = "RE"
        elif any(k in itemid for k in ["PT_SPE", "PT_GAS"]):
            faction = t("bp_fac_spe", default="Especial / Evento")
            faction_key = "SPE"
        elif "PT_DIY" in itemid:
            faction = t("bp_fac_dod", default="D.O.D. Arms")
            faction_key = "DOD"
        elif "PT_MIL" in itemid:
            faction = t("bp_fac_we", default="War Ensemble")
            faction_key = "MIL"
        elif "PT_FAN" in itemid:
            faction = t("bp_fac_cw", default="Candle Wolf")
            faction_key = "FAN"
        elif "PT_SPO" in itemid:
            faction = t("bp_fac_milk", default="M.I.L.K.")
            faction_key = "SPO"
        else:
            orig = item.get("faction", "")
            if "WAR" in orig:
                faction = t("bp_fac_we", default="War Ensemble")
                faction_key = "MIL"
            elif "CANDLE" in orig:
                faction = t("bp_fac_cw", default="Candle Wolf")
                faction_key = "FAN"
            elif "D.O.D" in orig:
                faction = t("bp_fac_dod", default="D.O.D. Arms")
                faction_key = "DOD"
            elif "M.I.L.K" in orig or "MILK" in orig:
                faction = t("bp_fac_milk", default="M.I.L.K.")
                faction_key = "SPO"
            else:
                faction = t("bp_fac_gen", default="General / Otras")
                faction_key = "GEN"

        # 3. Set Code
        clean_set = ""
        m = re.search(r"PT_([A-Z]+)_(?:HEAD|TOPS|BTM)_(\d+)", itemid)
        if m:
            clean_set = f"{m.group(1)}_{m.group(2)}"

        return slot, slot_key, faction, faction_key, clean_set

    def _get_weapon_damage_types(self, item):
        dt = item.get("damage_types")
        if dt:
            return set(dt) if isinstance(dt, list) else {dt}
        da = item.get("damage_attr")
        if da and isinstance(da, dict):
            return set(da.keys())

        itemid = item.get("id", "")
        m = re.search(r"WP(\d{3})", itemid, re.IGNORECASE)
        if m:
            wp_code = m.group(1)
            if wp_code in WP_SERIES_DAMAGE:
                return {WP_SERIES_DAMAGE[wp_code]}

        name_en = item.get("name_en", "").lower()
        name_es = item.get("name_es", "").lower()
        full = f"{itemid.lower()} {name_en} {name_es}"
        found = set()
        if any(k in full for k in ["poison", "veneno", "toxin", "claw", "garra", "chopper", "viper", "mamba", "medusa"]):
            found.add("POISON")
        if any(k in full for k in ["flamethrower", "fire", "fuego", "flame", "torch", "antorcha", "lanzallamas", "flare"]):
            found.add("FIRE")
        if any(k in full for k in ["electric", "electricidad", "static", "massager", "masajeador", "stun", "shock", "lightning", "rayo", "plasma", "laser"]):
            found.add("ELECTRIC")
        if any(k in full for k in ["kamas", "rifle", "sniper", "francotirador", "nail", "clavos", "magnum", "pistol", "gun", "crossbow", "ballesta", "shotgun", "escopeta", "pitching", "bow", "rocket", "harpoon"]):
            found.add("PIERCE")
        if any(k in full for k in ["machete", "sword", "espada", "katana", "cleaver", "cuchilla", "saber", "sable", "saw", "sierra", "pickaxe", "knife", "cuchillo", "scythe", "guadaña", "axe", "hacha"]):
            found.add("SLASH")
        if any(k in full for k in ["hammer", "martillo", "bat", "bate", "iron", "plancha", "club", "palo", "bowling", "flail", "boxing", "boxeo", "pipe", "puño", "sand"]):
            found.add("BLUNT")
        return found if found else {"OTHER"}

    def _build_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(8, 8, 8, 8)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        root_layout.addWidget(splitter)

        # =============================================================
        # LEFT PANEL: Search, Filters, Collabs & Blueprints Table
        # =============================================================
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 4, 0)
        left_layout.setSpacing(6)

        # Row 1: Search, Slot, Faction, and Sets Viewer Button
        r1 = QHBoxLayout()
        self.lbl_bp_search = QLabel(t("bp_search", default="🔍 Buscar:"))
        r1.addWidget(self.lbl_bp_search)
        self.search_entry = QLineEdit()
        self.search_entry.setPlaceholderText(t("search_placeholder", default="Nombre / ID..."))
        self.search_entry.textChanged.connect(self.filter_blueprints_list)
        r1.addWidget(self.search_entry)

        self.lbl_bp_slot = QLabel(t("bp_slot_lbl", default="Ranura:"))
        r1.addWidget(self.lbl_bp_slot)
        self.cat_cb = QComboBox()
        self.cat_cb.addItem(t("bp_slot_all", default="Todos"), "ALL")
        self.cat_cb.addItem(t("bp_slot_helmets", default="🪖 Cascos"), "head")
        self.cat_cb.addItem(t("bp_slot_bodies", default="👕 Pechos"), "chest")
        self.cat_cb.addItem(t("bp_slot_legs", default="👖 Piernas"), "legs")
        self.cat_cb.addItem(t("bp_slot_weapons", default="⚔️ Armas"), "weapon")
        self.cat_cb.currentIndexChanged.connect(self.filter_blueprints_list)
        r1.addWidget(self.cat_cb)

        self.lbl_bp_faction = QLabel(t("bp_faction_lbl", default="Facción:"))
        r1.addWidget(self.lbl_bp_faction)
        self.fac_cb = QComboBox()
        fac_defs = [
            ("ALL", t("bp_fac_all", default="Todas")),
            ("DOD", t("bp_fac_dod", default="🔨 D.O.D. ARMS")),
            ("MIL", t("bp_fac_we", default="🎖️ WAR ENSEMBLE")),
            ("FAN", t("bp_fac_cw", default="🕯️ CANDLE WOLF")),
            ("SPO", t("bp_fac_milk", default="🥛 M.I.L.K.")),
            ("FORCEMEN", t("bp_fac_44ce", default="⚡ 4 FORCEMEN & TENGOKU")),
            ("JACKAL", t("bp_fac_jackals", default="🕶️ JACKALS")),
            ("RE", t("bp_fac_re", default="♻️ RE (Reciclador)")),
            ("SPE", t("bp_fac_spe", default="🎭 Especial / Evento")),
            ("GEN", t("bp_fac_gen", default="⚔️ General / Otras")),
        ]
        for code, label in fac_defs:
            self.fac_cb.addItem(label, code)
        self.fac_cb.currentIndexChanged.connect(self.filter_blueprints_list)
        r1.addWidget(self.fac_cb)

        self.btn_sets_viewer = QPushButton(t("bp_view_sets_btn", default="👘 Visor de Sets por Nivel"))
        self.btn_sets_viewer.setProperty("accent", "true")
        self.btn_sets_viewer.clicked.connect(self._open_armor_set_viewer)
        r1.addWidget(self.btn_sets_viewer)
        left_layout.addLayout(r1)

        # Row 2: Possession, Damage Type, Unlock All controls, Repair
        r2 = QHBoxLayout()
        self.lbl_bp_poss = QLabel(t("bp_poss_lbl", default="Posesión:"))
        r2.addWidget(self.lbl_bp_poss)
        self.poss_cb = QComboBox()
        self.poss_cb.addItem(t("bp_poss_all", default="Todos"), "ALL")
        self.poss_cb.addItem(t("bp_poss_storage", default="📦 En Almacén (> 0)"), "STORAGE")
        self.poss_cb.addItem(t("bp_poss_shop", default="⭐ Desbloqueados en Tienda (+4)"), "SHOP")
        self.poss_cb.addItem(t("bp_poss_rnd", default="🔨 En I+D (REMODEL / MAP)"), "RND")
        self.poss_cb.addItem(t("bp_poss_locked", default="❌ Bloqueados (Faltantes)"), "LOCKED")
        self.poss_cb.currentIndexChanged.connect(self.filter_blueprints_list)
        r2.addWidget(self.poss_cb)

        self.lbl_bp_dmg = QLabel(t("bp_dmg_lbl", default="Daño:"))
        r2.addWidget(self.lbl_bp_dmg)
        self.dmg_cb = QComboBox()
        self.dmg_cb.addItem(t("bp_dmg_all", default="Todos"), "ALL")
        self.dmg_cb.addItem(t("bp_dmg_slash", default="🗡️ Corte (Slash)"), "SLASH")
        self.dmg_cb.addItem(t("bp_dmg_blunt", default="🔨 Golpe (Blunt)"), "BLUNT")
        self.dmg_cb.addItem(t("bp_dmg_pierce", default="🏹 Perforación (Pierce)"), "PIERCE")
        self.dmg_cb.addItem(t("bp_dmg_fire", default="🔥 Fuego (Burn)"), "FIRE")
        self.dmg_cb.addItem(t("bp_dmg_elec", default="⚡ Electricidad (Electric)"), "ELECTRIC")
        self.dmg_cb.addItem(t("bp_dmg_poison", default="🧪 Veneno (Poison)"), "POISON")
        self.dmg_cb.currentIndexChanged.connect(self.filter_blueprints_list)
        r2.addWidget(self.dmg_cb)

        self.lbl_bp_all_lvl = QLabel(t("bp_unlock_all_lbl", default="Nivel:"))
        r2.addWidget(self.lbl_bp_all_lvl)
        self.cb_all_lvl = QComboBox()
        for lvl_str in ["+19", "+24", "+4", "+3", "+2", "+1"]:
            self.cb_all_lvl.addItem(lvl_str, lvl_str)
        self.cb_all_lvl.setFixedWidth(65)
        r2.addWidget(self.cb_all_lvl)

        self.btn_unlock_all = QPushButton(t("bp_unlock_all_btn", default="🌟 DESBLOQUEAR TODO"))
        self.btn_unlock_all.setProperty("accent", "true")
        self.btn_unlock_all.clicked.connect(self.unlock_all_blueprints_preset)
        r2.addWidget(self.btn_unlock_all)

        self.btn_repair = QPushButton(t("bp_repair_btn", default="🔧 Reparar I+D"))
        self.btn_repair.clicked.connect(self._repair_blueprints_action)
        r2.addWidget(self.btn_repair)
        left_layout.addLayout(r2)

        # Row 3: Collabs & Quick Events Filter Bar
        r3 = QHBoxLayout()
        self.lbl_collab = QLabel(t("bp_collabs_lbl", default="🎯 Eventos:"))
        self.lbl_collab.setStyleSheet(f"color: {ACCENT_GOLD}; font-weight: bold; font-size: 8pt;")
        r3.addWidget(self.lbl_collab)

        self.btn_collab_all = QPushButton(t("bp_collab_all", default="🌐 Todos"))
        self.btn_collab_all.setFixedHeight(24)
        self.btn_collab_all.clicked.connect(lambda checked=False, m="TODOS": self._set_collab_filter(m))
        r3.addWidget(self.btn_collab_all)

        collab_buttons = [
            ("💥 WoT", "WOT"),
            ("⚔️ NMH", "NMH"),
            ("🏆 TDM", "TDM"),
            ("♻️ RE", "RE"),
            ("💀 44CE", "44CE"),
        ]
        self.btn_collab_all.setCheckable(True)
        self.btn_collab_all.setChecked(True)
        self.collab_buttons_list = [(self.btn_collab_all, "TODOS")]
        for btn_text, mode in collab_buttons:
            btn = QPushButton(btn_text)
            btn.setFixedHeight(24)
            btn.setCheckable(True)
            btn.setChecked(False)
            btn.clicked.connect(lambda checked=False, m=mode: self._set_collab_filter(m))
            r3.addWidget(btn)
            self.collab_buttons_list.append((btn, mode))

        r3.addStretch()
        left_layout.addLayout(r3)

        # Blueprints Table (5 Columns: Item, Status, Storage, Bag, ID)
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            t("bp_col_item", default="Plano / Nombre Oficial"),
            t("bp_col_status", default="Estado Forja"),
            t("bp_col_storage", default="Almacén"),
            t("bp_col_bag", default="Bolsa"),
            t("bp_col_id", default="ID Plano"),
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
        self.table.itemClicked.connect(lambda item: self._on_table_selection_changed())
        left_layout.addWidget(self.table)

        splitter.addWidget(left_widget)

        # =============================================================
        # RIGHT PANEL: Full Scrollable Workbench (Exact Tkinter Parity)
        # =============================================================
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(4, 0, 4, 0)
        right_layout.setSpacing(8)

        # Card Container
        self.box_card = QGroupBox(t("bp_card_title", default="Ficha Técnica de Plano Chokufunsha"))
        card_v = QVBoxLayout(self.box_card)
        card_v.setContentsMargins(10, 10, 10, 10)
        card_v.setSpacing(6)

        # Artwork Card (280x140)
        art_center = QHBoxLayout()
        self.bp_art_lbl = QLabel()
        self.bp_art_lbl.setFixedSize(280, 140)
        self.bp_art_lbl.setStyleSheet("border: 2px solid #252b40; border-radius: 8px; background-color: #151824;")
        self.bp_art_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        art_center.addStretch()
        art_center.addWidget(self.bp_art_lbl)
        art_center.addStretch()
        card_v.addLayout(art_center)

        # Title
        self.bp_title_lbl = QLabel(t("bp_select_prompt", default="Selecciona un equipo"))
        self.bp_title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.bp_title_lbl.setWordWrap(True)
        self.bp_title_lbl.setStyleSheet(f"color: {ACCENT_GOLD}; font-size: 11pt; font-weight: bold;")
        card_v.addWidget(self.bp_title_lbl)

        # Faction & Slot Line
        self.bp_faction_lbl = QLabel("---")
        self.bp_faction_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.bp_faction_lbl.setStyleSheet(f"color: {FG_MUTED}; font-size: 9pt;")
        card_v.addWidget(self.bp_faction_lbl)

        # Status Banner
        self.bp_status_lbl = QLabel(t("bp_status_placeholder", default="---"))
        self.bp_status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.bp_status_lbl.setWordWrap(True)
        self.bp_status_lbl.setStyleSheet(f"color: {ACCENT_CYAN}; font-size: 9.5pt; font-weight: bold;")
        card_v.addWidget(self.bp_status_lbl)

        # Stats Label
        self.bp_stats_lbl = QLabel(t("bp_stats_placeholder", default="---"))
        self.bp_stats_lbl.setWordWrap(True)
        self.bp_stats_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.bp_stats_lbl.setStyleSheet("color: #dcdde1; font-size: 8.5pt; padding: 2px;")
        card_v.addWidget(self.bp_stats_lbl)

        # View Set Button
        self.bp_set_btn = QPushButton(t("bp_view_set_btn", default="👘 Ver Conjunto en Visor de Sets"))
        self.bp_set_btn.clicked.connect(self._open_selected_piece_set)
        card_v.addWidget(self.bp_set_btn)

        # 1. Individual Actions Box
        self.indiv_box = QGroupBox(t("bp_indiv_actions_title", default="Acciones Individuales para esta Pieza"))
        indiv_v = QVBoxLayout(self.indiv_box)
        indiv_v.setContentsMargins(8, 8, 8, 8)
        indiv_v.setSpacing(6)

        act_r1 = QHBoxLayout()
        self.lbl_bp_lvl = QLabel(t("bp_lvl_lbl", default="Nivel:"))
        act_r1.addWidget(self.lbl_bp_lvl)
        self.cb_single_lvl = QComboBox()
        self.cb_single_lvl.setFixedWidth(130)
        act_r1.addWidget(self.cb_single_lvl)

        self.btn_unlock_shop = QPushButton(t("bp_unlock_shop_btn", default="⭐ Desbloquear en Tienda"))
        self.btn_unlock_shop.setProperty("accent", "true")
        self.btn_unlock_shop.clicked.connect(self._unlock_single_bp_shop)
        act_r1.addWidget(self.btn_unlock_shop)
        indiv_v.addLayout(act_r1)

        self.btn_send_rnd = QPushButton(t("bp_send_rnd_btn", default="🔨 Enviar / Mantener en I+D"))
        self.btn_send_rnd.clicked.connect(self._send_single_bp_to_rnd)
        indiv_v.addWidget(self.btn_send_rnd)

        self.btn_send_storage = QPushButton(t("bp_send_storage_btn", default="📦 Enviar 1 u. al Almacén"))
        self.btn_send_storage.clicked.connect(self._deliver_single_bp_to_storage)
        indiv_v.addWidget(self.btn_send_storage)

        self.btn_deposit_kit = QPushButton(t("bp_deposit_kit_btn", default="🛠️ Depositar Kit de Forja (+10 u.)"))
        self.btn_deposit_kit.setProperty("accent", "true")
        self.btn_deposit_kit.clicked.connect(self._deposit_crafting_kit_for_selected_bp)
        indiv_v.addWidget(self.btn_deposit_kit)

        self.bp_evolve_lbl = QLabel("")
        self.bp_evolve_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.bp_evolve_lbl.setWordWrap(True)
        self.bp_evolve_lbl.setStyleSheet(f"color: {ACCENT_CYAN}; font-size: 8.5pt; font-weight: bold;")
        indiv_v.addWidget(self.bp_evolve_lbl)

        self.btn_evolve_tier = QPushButton(t("bp_evolve_tier_btn", default="🔄 Desbloquear Sig. Tier (+4)"))
        self.btn_evolve_tier.setProperty("accent", "true")
        self.btn_evolve_tier.clicked.connect(self._evolve_selected_bp_to_next_tier)
        indiv_v.addWidget(self.btn_evolve_tier)

        card_v.addWidget(self.indiv_box)

        # 2. Endgame Sets Injector Box
        self.endgame_box = QGroupBox(t("bp_endgame_box_title", default="🛡️ Inyector de Sets Endgame"))
        endgame_v = QVBoxLayout(self.endgame_box)
        endgame_v.setContentsMargins(8, 8, 8, 8)
        endgame_v.setSpacing(6)

        endgame_defs = [
            ("white_steel", "White Steel (白钢)"),
            ("red_napalm", "Red Napalm (红凝固汽油)"),
            ("black_thunder", "Black Thunder (黑雷)"),
            ("pale_wind", "Pale Wind (苍白之风)"),
            ("jackals_gear", "Jackals V1/V2/V3 (豺狼)"),
            ("tengoku_weapons", "Tengoku Rare Arsenal (天狱)"),
        ]
        self.cb_endgame = QComboBox()
        for key, lbl in endgame_defs:
            self.cb_endgame.addItem(lbl, key)
        endgame_v.addWidget(self.cb_endgame)

        self.btn_inject_set = QPushButton(t("bp_inject_set_btn", default="🛡️ Inyectar Set Completo al Almacén"))
        self.btn_inject_set.setProperty("accent", "true")
        self.btn_inject_set.clicked.connect(self._inject_endgame_set_action)
        endgame_v.addWidget(self.btn_inject_set)
        card_v.addWidget(self.endgame_box)

        # 3. Global Equipment Modifiers Box
        self.global_gear_box = QGroupBox(t("bp_mass_actions_title", default="Modificadores y Mejoras Masivas"))
        global_v = QVBoxLayout(self.global_gear_box)
        global_v.setContentsMargins(8, 8, 8, 8)
        global_v.setSpacing(6)

        self.btn_dur = QPushButton(t("bp_inf_dur_btn", default="✨ Reparar Todo al 100% de Durabilidad (Legítimo)"))
        self.btn_dur.clicked.connect(self._set_infinite_durability_action)
        global_v.addWidget(self.btn_dur)

        self.btn_ammo = QPushButton(t("bp_inf_ammo_btn", default="🎯 Recargar Munición al Máximo (Armas de Fuego)"))
        self.btn_ammo.clicked.connect(self._set_massive_ammo_action)
        global_v.addWidget(self.btn_ammo)

        self.btn_upg19 = QPushButton(t("bp_upg_all19_btn", default="⚡ Preparar Todo a Nivel +19 en I+D (Para Fabricar)"))
        self.btn_upg19.clicked.connect(lambda: self._upgrade_all_gear_max_lvl_action(19))
        global_v.addWidget(self.btn_upg19)

        self.btn_upg24 = QPushButton(t("bp_upg_all24_btn", default="🔥 Desbloquear Todo a Nivel +19 en Tienda (Directo)"))
        self.btn_upg24.setProperty("accent", "true")
        self.btn_upg24.clicked.connect(lambda: self._upgrade_all_gear_max_lvl_action(20))
        global_v.addWidget(self.btn_upg24)
        card_v.addWidget(self.global_gear_box)

        # 4. Chokufunsha Shop Tier Suppression Mod Box
        self.shop_tiers_box = QGroupBox(t("bp_shop_tiers_mod_title", default="🏬 Mod Tienda Chokufunsha: Todos los Tiers (1 al 4)"))
        shop_v = QVBoxLayout(self.shop_tiers_box)
        shop_v.setContentsMargins(8, 8, 8, 8)
        shop_v.setSpacing(6)

        self.lbl_shop_desc = QLabel(t("bp_shop_tiers_mod_desc", default="Permite comprar cualquier tier en la tienda (Tier 1 al 4 y Destope) sin ocultar los anteriores."))
        self.lbl_shop_desc.setWordWrap(True)
        self.lbl_shop_desc.setStyleSheet(f"color: {FG_MUTED}; font-size: 8pt;")
        shop_v.addWidget(self.lbl_shop_desc)

        self.bp_shop_tiers_status_lbl = QLabel(t("bp_shop_tiers_inactive_status", default="Mod Tienda: ⏸️ Estándar (Sólo se muestra el último tier)"))
        self.bp_shop_tiers_status_lbl.setWordWrap(True)
        self.bp_shop_tiers_status_lbl.setStyleSheet(f"color: {FG_MUTED}; font-size: 8.5pt; font-weight: bold;")
        shop_v.addWidget(self.bp_shop_tiers_status_lbl)

        self.btn_shop_enable = QPushButton(t("bp_shop_tiers_enable_btn", default="🔓 Desbloquear Todos los Tiers en Tienda"))
        self.btn_shop_enable.setProperty("accent", "true")
        self.btn_shop_enable.clicked.connect(self._enable_all_shop_tiers_action)
        shop_v.addWidget(self.btn_shop_enable)

        self.btn_shop_restore = QPushButton(t("bp_shop_tiers_restore_btn", default="🔒 Restaurar Progresión Normal"))
        self.btn_shop_restore.clicked.connect(self._restore_shop_tiers_action)
        shop_v.addWidget(self.btn_shop_restore)
        card_v.addWidget(self.shop_tiers_box)

        right_layout.addWidget(self.box_card)
        right_layout.addStretch()

        scroll_area.setWidget(right_container)
        splitter.addWidget(scroll_area)
        splitter.setSizes([460, 540])

    def refresh_data(self):
        """Loads and filters the blueprints catalog."""
        self._build_armor_set_index()
        self.filter_blueprints_list()
        self._refresh_shop_tiers_status()

    def _set_collab_filter(self, mode):
        if self.current_collab_filter == mode and mode != "TODOS":
            self.current_collab_filter = "TODOS"
        else:
            self.current_collab_filter = mode

        if hasattr(self, "collab_buttons_list"):
            for btn, code in self.collab_buttons_list:
                btn.setChecked(code == self.current_collab_filter)

        self.filter_blueprints_list()

    @property
    def bp_collab_filter(self):
        class _Var:
            def __init__(self, tab): self.tab = tab
            def get(self): return self.tab.current_collab_filter
            def set(self, val): self.tab._set_collab_filter(val)
        return _Var(self)

    def filter_blueprints_list(self):
        save = self.main_win.save_json
        eq_db = getattr(self.main_win, "equipment_db", [])
        if not eq_db:
            return

        query = self.search_entry.text().strip().lower()
        cat_filter = self.cat_cb.currentData() or "ALL"
        fac_filter = self.fac_cb.currentData() or "ALL"
        poss_filter = self.poss_cb.currentData() or "ALL"
        dmg_filter = self.dmg_cb.currentData() or "ALL"
        collab_filter = self.current_collab_filter

        pr_map = modifiers.get_part_research_status(save) if save else {}
        storage_gear = modifiers.get_storage_equipment_counts(save) if save else {}
        bag_gear = modifiers.get_bag_equipment_counts(save) if save else {}

        self.filtered_blueprints = []

        for item in eq_db:
            bp_id = item.get("id", "")
            if not bp_id:
                continue

            name = get_item_name(item) or item.get("name_en", bp_id)
            name_es = item.get("name_es", "")
            name_en = item.get("name_en", "")
            slot, slot_key, faction, faction_key, set_code = self._get_item_wiki_meta(item)

            # 1. Filter by Slot
            if cat_filter != "ALL" and slot_key != cat_filter:
                continue

            # 2. Filter by Faction
            if fac_filter != "ALL" and faction_key != fac_filter:
                continue

            # 3. Forge Status
            if bp_id in pr_map:
                forge_info = pr_map[bp_id]
                forge_code = forge_info.get("status", "LOCKED")
                lvl_val = forge_info.get("lvl", 20)
                plus_lvl = lvl_val - 1 if lvl_val > 1 else lvl_val
                forge_key = f"bp_forge_{forge_code.lower()}"
                forge_status = t(
                    forge_key,
                    default=forge_info.get("label", forge_code),
                    plus_lvl=plus_lvl,
                    next_lvl=plus_lvl + 1,
                    level=forge_info.get("level", 1)
                )
            else:
                forge_status = t("bp_forge_locked", default="Bloqueado")
                forge_code = "LOCKED"

            storage_count = storage_gear.get(bp_id, 0)
            bag_count = bag_gear.get(bp_id, 0)

            # 4. Filter by Possession
            if poss_filter == "STORAGE" and storage_count <= 0:
                continue
            elif poss_filter == "SHOP" and forge_code not in ("STORE_PLUS4", "STORE_UNCAPPED", "RND_UNCAPPED", "STORE"):
                continue
            elif poss_filter == "RND" and forge_code not in ("REMODEL", "MAP", "FINISHED_LVL", "RND_UNCAPPED"):
                continue
            elif poss_filter == "LOCKED" and forge_code != "LOCKED":
                continue

            # 5. Filter by Damage Type (Weapons only)
            if dmg_filter != "ALL":
                if slot_key != "weapon":
                    continue
                w_dmgs = self._get_weapon_damage_types(item)
                if dmg_filter not in w_dmgs:
                    continue

            # 6. Collab / Event Filter
            if collab_filter != "TODOS":
                n_en = (name_en or "").lower()
                n_es = (name_es or "").lower()
                b_id = bp_id.lower()
                if collab_filter == "WOT" and "wot" not in n_en and "world of tanks" not in n_en:
                    continue
                elif collab_filter == "NMH" and "beam" not in n_en and "travis" not in n_en and "heroes" not in n_en:
                    continue
                elif collab_filter == "TDM" and "tdm" not in n_en and "_0a" not in b_id:
                    continue
                elif collab_filter == "RE" and " re" not in n_en and "_0b" not in b_id:
                    continue
                elif collab_filter == "44CE" and faction_key != "FORCEMEN":
                    continue

            # 7. Search Query
            if query:
                matched_query = (
                    query in bp_id.lower() or
                    query in set_code.lower() or
                    any(
                        query in str(v).lower()
                        for k, v in item.items()
                        if (k.startswith("name") or k.startswith("desc")) and isinstance(v, str)
                    )
                )
                if not matched_query:
                    continue

            display_title = get_entity_display_title(item)
            self.filtered_blueprints.append((item, slot, faction, forge_status, forge_code, storage_count, bag_count))

        # Populate Table
        self.table.blockSignals(True)
        self.table.clearSelection()
        self.table.setRowCount(0)
        self.table.setRowCount(len(self.filtered_blueprints))

        for row_idx, (item, slot, faction, forge_status, forge_code, storage_count, bag_count) in enumerate(self.filtered_blueprints):
            bp_id = item.get("id", "")
            title = get_entity_display_title(item)

            # Col 0: Icon + Name
            item_name = QTableWidgetItem(f" {title}")
            art_path = find_equipment_art(bp_id, as_card=False)
            ico = get_icon(art_path, (44, 44))
            if ico and not ico.isNull():
                item_name.setIcon(ico)
            self.table.setItem(row_idx, 0, item_name)

            # Col 1: Status
            item_status = QTableWidgetItem(forge_status)
            item_status.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if forge_code in ("STORE_UNCAPPED", "RND_UNCAPPED"):
                item_status.setForeground(QColor("#ff79c6"))
            elif forge_code == "STORE_PLUS4":
                item_status.setForeground(QColor(ACCENT_GOLD))
            elif forge_code in ("REMODEL", "MAP", "FINISHED_LVL"):
                item_status.setForeground(QColor(ACCENT_CYAN))
            else:
                item_status.setForeground(QColor(FG_MUTED))
            self.table.setItem(row_idx, 1, item_status)

            # Col 2: Storage Count
            s_txt = t("inv_unit_str", qty=storage_count) if storage_count > 0 else "-"
            item_stor = QTableWidgetItem(s_txt)
            item_stor.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if storage_count > 0:
                item_stor.setForeground(Qt.GlobalColor.white)
            else:
                item_stor.setForeground(Qt.GlobalColor.gray)
            self.table.setItem(row_idx, 2, item_stor)

            # Col 3: Bag Count
            b_txt = t("inv_unit_str", qty=bag_count) if bag_count > 0 else "-"
            item_bag = QTableWidgetItem(b_txt)
            item_bag.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if bag_count > 0:
                item_bag.setForeground(Qt.GlobalColor.white)
            else:
                item_bag.setForeground(Qt.GlobalColor.gray)
            self.table.setItem(row_idx, 3, item_bag)

            # Col 4: ID
            item_id_w = QTableWidgetItem(bp_id)
            item_id_w.setForeground(Qt.GlobalColor.gray)
            self.table.setItem(row_idx, 4, item_id_w)

        self.table.blockSignals(False)

        if self.filtered_blueprints:
            selected_id = self.current_selected_bp.get("id") if self.current_selected_bp else None
            row = next((i for i, entry in enumerate(self.filtered_blueprints) if entry[0].get("id") == selected_id), 0)
            self.table.selectRow(row)
            self._on_table_selection_changed()
        else:
            self.current_selected_bp = None
            self._clear_details()

    def _clear_details(self):
        self.bp_title_lbl.setText(t("bp_select_prompt", default="Selecciona un equipo"))
        self.bp_faction_lbl.setText("---")
        self.bp_status_lbl.setText(t("bp_status_info", default="Forja: - | Almacén: - | Bolsa: -", status="-", storage="-", bag="-"))
        self.bp_status_lbl.setStyleSheet(f"color: {FG_MUTED}; font-size: 9.5pt;")
        self.bp_set_btn.setText(t("bp_no_set", default="👘 No pertenece a un conjunto"))
        self.bp_set_btn.setEnabled(False)
        self.bp_stats_lbl.setText("---")
        self.bp_evolve_lbl.setText("")
        self.btn_evolve_tier.setVisible(False)
        self.bp_art_lbl.clear()

    def _on_table_selection_changed(self):
        sel_rows = self.table.selectedItems()
        if not sel_rows:
            return
        row = sel_rows[0].row()
        if 0 <= row < len(self.filtered_blueprints):
            item, slot, faction, forge_status, forge_code, storage_count, bag_count = self.filtered_blueprints[row]
            self.current_selected_bp = item
            bp_id = item.get("id", "")
            name = get_item_name(item) or item.get("name_en", bp_id)

            # 1. Update Title & Faction
            self.bp_title_lbl.setText(f"{name}\n({bp_id})")
            self.bp_faction_lbl.setText(f"{slot} • {faction}")

            # 2. Update Status Banner
            s_str = t("inv_unit_str", qty=storage_count) if storage_count > 0 else "-"
            b_str = t("inv_unit_str", qty=bag_count) if bag_count > 0 else "-"
            self.bp_status_lbl.setText(t("bp_status_info", default=f"Forja: {forge_status} | Almacén: {s_str} | Bolsa: {b_str}", status=forge_status, storage=s_str, bag=b_str))
            if "+19" in forge_status or "Destope" in forge_status or "Uncapped" in forge_status:
                self.bp_status_lbl.setStyleSheet("color: #ff79c6; font-size: 9.5pt; font-weight: bold;")
            else:
                self.bp_status_lbl.setStyleSheet(f"color: {ACCENT_CYAN}; font-size: 9.5pt; font-weight: bold;")

            # 3. Check Armor Set & Stats
            lookup_id = bp_id[:-2] if bp_id.endswith("_G") and bp_id[:-2] in self.armor_set_by_item_id else bp_id
            if lookup_id in self.armor_set_by_item_id:
                set_obj, tier_obj, piece_obj = self.armor_set_by_item_id[lookup_id]
                set_title = get_set_name(set_obj)
                self.bp_set_btn.setText(f"{t('bp_view_set_btn', default='👘 Ver Conjunto')}: {set_title}")
                self.bp_set_btn.setEnabled(True)
                if "def" in piece_obj:
                    self.bp_stats_lbl.setText(t("bp_base_def", default=f"Defensa Base: {piece_obj.get('def', '-')} (A +4: {piece_obj.get('def_plus4', '-')}) | Durabilidad: {piece_obj.get('durability', '-')}", def_b=piece_obj.get('def', '-'), def_4=piece_obj.get('def_plus4', '-'), dur=piece_obj.get('durability', '-')))
                elif "atk" in piece_obj:
                    self.bp_stats_lbl.setText(t("bp_base_atk", default=f"Ataque Base: {piece_obj.get('atk', '-')} (A +4: {piece_obj.get('atk_plus4', '-')}) | Durabilidad: {piece_obj.get('durability', '-')}", atk_b=piece_obj.get('atk', '-'), atk_4=piece_obj.get('atk_plus4', '-'), dur=piece_obj.get('durability', '-')))
                else:
                    self.bp_stats_lbl.setText(f"{set_title}")
            else:
                self.bp_set_btn.setText(t("bp_no_set", default="👘 No pertenece a un conjunto"))
                self.bp_set_btn.setEnabled(False)
                self.bp_stats_lbl.setText(t("bp_single_piece_lbl", default="Pieza individual / Sin conjunto asignado"))

            # 4. Evolution & Uncap Handling
            can_uncap = item.get("can_uncap", True)
            nextptid = item.get("nextptid", "")

            self.cb_single_lvl.blockSignals(True)
            self.cb_single_lvl.clear()
            if can_uncap:
                uncap_vals = [
                    t("bp_in_rnd_fmt", default="+19 (I+D)", lvl=19),
                    t("bp_shop_max_fmt", default="+19 (Tienda Máx)", lvl=19),
                    "+18", "+17", "+16", "+15", "+14", "+13", "+12", "+11", "+10",
                    "+9", "+8", "+7", "+6", "+5", "+4", "+3", "+2", "+1",
                    t("bp_blueprint_fmt", default="+0 (Plano)")
                ]
                for v in uncap_vals:
                    self.cb_single_lvl.addItem(v, v)
                self.bp_evolve_lbl.setText(t("bp_final_tier_ready", default="¡Tier final alcanzado! Listo para destope +19."))
                self.bp_evolve_lbl.setStyleSheet("color: #ff79c6; font-size: 8.5pt; font-weight: bold;")
                self.btn_evolve_tier.setVisible(False)
            else:
                evolve_vals = [
                    t("bp_in_rnd_fmt", default="+4 (I+D)", lvl=4),
                    t("bp_shop_max_fmt", default="+4 (Tienda Máx)", lvl=4),
                    "+3", "+2", "+1",
                    t("bp_blueprint_fmt", default="+0 (Plano)")
                ]
                for v in evolve_vals:
                    self.cb_single_lvl.addItem(v, v)

                if nextptid:
                    nxt_meta = next((it for it in getattr(self.main_win, "equipment_db", []) if it.get("id") == nextptid), None)
                    nxt_name = get_item_name(nxt_meta) if nxt_meta else nextptid
                    self.bp_evolve_lbl.setText(t("bp_evolves_to_fmt", default=f"Evoluciona a: {nxt_name}", name=nxt_name))
                    self.bp_evolve_lbl.setStyleSheet(f"color: {ACCENT_CYAN}; font-size: 8.5pt; font-weight: bold;")
                    is_nxt_uncap = nxt_meta.get("can_uncap", False) if nxt_meta else False
                    btn_txt = t("bp_evolve_to_uncapped", default=f"🔄 Evolucionar a {nxt_name} (Destope)", name=nxt_name) if is_nxt_uncap else t("bp_evolve_to_next", default=f"🔄 Evolucionar a {nxt_name}", name=nxt_name)
                    self.btn_evolve_tier.setText(btn_txt)
                    self.btn_evolve_tier.setVisible(True)
                else:
                    self.bp_evolve_lbl.setText(t("bp_max_tier_fmt", default="Tier máximo para esta serie", tier=4))
                    self.bp_evolve_lbl.setStyleSheet(f"color: {ACCENT_CYAN}; font-size: 8.5pt; font-weight: bold;")
                    self.btn_evolve_tier.setVisible(False)
            self.cb_single_lvl.blockSignals(False)

            # 5. Artwork Card (280x140)
            card_path = find_equipment_art(bp_id, as_card=True)
            card_pix = get_pixmap(card_path, (280, 140), preserve_aspect=True)
            if not card_pix or card_pix.isNull():
                thumb_path = find_equipment_art(bp_id, as_card=False)
                card_pix = get_pixmap(thumb_path, (280, 140), preserve_aspect=True)

            if card_pix and not card_pix.isNull():
                self.bp_art_lbl.setPixmap(card_pix)
            else:
                self.bp_art_lbl.clear()

    def _open_armor_set_viewer(self):
        try:
            dlg = ArmorSetViewerDialog(self, self.main_win.save_json, getattr(self.main_win, "armor_sets", []))
            dlg.exec()
            self.filter_blueprints_list()
            self.main_win.update_hud()
        except Exception as e:
            QMessageBox.warning(self, "Visor de Sets", f"Error abriendo visor: {e}")

    def _open_selected_piece_set(self):
        if not self.current_selected_bp:
            return
        bp_id = self.current_selected_bp.get("id", "")
        lookup_id = bp_id[:-2] if bp_id.endswith("_G") and bp_id[:-2] in self.armor_set_by_item_id else bp_id
        if lookup_id not in self.armor_set_by_item_id:
            return
        set_obj, tier_obj, piece_obj = self.armor_set_by_item_id[lookup_id]
        tier_num = tier_obj.get("tier_num", tier_obj.get("tier", 1))
        try:
            dlg = ArmorSetViewerDialog(self, self.main_win.save_json, getattr(self.main_win, "armor_sets", []), initial_set_id=set_obj.get("id"), initial_tier=tier_num)
            dlg.exec()
            self.filter_blueprints_list()
            self.main_win.update_hud()
        except Exception as e:
            QMessageBox.warning(self, "Visor de Sets", f"Error: {e}")

    def _parse_selected_level(self, val_str):
        val = str(val_str).strip()
        is_shop_max = ("tienda máx" in val.lower() or "tienda max" in val.lower() or "shop max" in val.lower())
        is_rnd = ("i+d" in val.lower() or "r&d" in val.lower())
        m = re.search(r"\+?(\d+)", val)
        lvl_num = int(m.group(1)) if m else 0
        return lvl_num, is_shop_max, is_rnd

    def _unlock_single_bp_shop(self):
        if not self.current_selected_bp or not self.main_win.save_json:
            return
        ptid = self.current_selected_bp.get("id")
        can_uncap = self.current_selected_bp.get("can_uncap", True)

        lvl_num, is_shop_max, is_rnd = self._parse_selected_level(self.cb_single_lvl.currentText())
        if is_shop_max or lvl_num in (20, 24, 25):
            api_lvl = 20 if can_uncap else 5
            display_lvl = 19 if can_uncap else 4
        else:
            api_lvl = lvl_num
            display_lvl = lvl_num

        next_unlocked = modifiers.unlock_single_blueprint(self.main_win.save_json, ptid, level=api_lvl, unlock_next_tier=True)
        self.main_win._auto_save()
        self.filter_blueprints_list()
        self.main_win.update_hud()

        cur_name = get_item_name(self.current_selected_bp) or ptid
        lvl_str = f"+{display_lvl} (Destope)" if display_lvl >= 19 else f"+{display_lvl}"

        if next_unlocked:
            nxt_meta = next((it for it in getattr(self.main_win, "equipment_db", []) if it.get("id") == next_unlocked), None)
            nxt_name = get_item_name(nxt_meta) if nxt_meta else next_unlocked
            self.main_win._notify("bp_notify_next_tier_title", "bp_notify_next_tier_msg", cur_name=cur_name, lvl_str=lvl_str, nxt_name=nxt_name, next_unlocked=next_unlocked)
        else:
            self.main_win._notify("bp_notify_unlocked_title", "bp_notify_unlocked_msg", cur_name=cur_name, lvl_str=lvl_str)

    def _send_single_bp_to_rnd(self):
        if not self.current_selected_bp or not self.main_win.save_json:
            return
        ptid = self.current_selected_bp.get("id")
        val = str(self.cb_single_lvl.currentText())
        lvl_num, _, _ = self._parse_selected_level(val)

        if "+0" in val or "plano" in val.lower() or lvl_num <= 0:
            target_lvl = 0
        elif lvl_num in (19, 20, 24, 25):
            target_lvl = 19
        else:
            target_lvl = lvl_num

        modifiers.send_blueprint_to_rnd(self.main_win.save_json, ptid, target_level=target_lvl)
        self.main_win._auto_save()
        self.filter_blueprints_list()
        self.main_win.update_hud()

        cur_name = get_item_name(self.current_selected_bp) or ptid
        if target_lvl == 0:
            self.main_win._notify("bp_notify_rnd_sent_title", "bp_notify_rnd_sent_msg", cur_name=cur_name, ptid=ptid)
        else:
            self.main_win._notify("bp_notify_rnd_set_title", "bp_notify_rnd_set_msg", cur_name=cur_name, ptid=ptid, prev_str="", next_str=f"+{target_lvl}")

    def _deliver_single_bp_to_storage(self):
        if not self.current_selected_bp or not self.main_win.save_json:
            return
        ptid = self.current_selected_bp.get("id")
        can_uncap = self.current_selected_bp.get("can_uncap", True)

        lvl_num, _, _ = self._parse_selected_level(self.cb_single_lvl.currentText())
        if lvl_num >= 19:
            lvl = 20 if can_uncap else 5
            plus = 19 if can_uncap else 4
        elif lvl_num <= 0:
            lvl = 1
            plus = 0
        else:
            lvl = min(20 if can_uncap else 5, lvl_num + 1)
            plus = min(19 if can_uncap else 4, lvl_num)

        modifiers.add_equipment_to_storage(self.main_win.save_json, ptid, count=1, lvl=lvl, dur=999999 if plus >= 19 else 50000)
        self.main_win._auto_save()
        self.filter_blueprints_list()
        self.main_win.update_hud()

        plus_str = f"+{plus} (Destope)" if plus >= 19 else f"+{plus}"
        self.main_win._notify("bp_notify_delivered_title", "bp_notify_delivered_msg", ptid=ptid, plus_str=plus_str)

    def _deposit_crafting_kit_for_selected_bp(self):
        if not self.current_selected_bp or not self.main_win.save_json:
            return
        ptid = self.current_selected_bp.get("id")
        name_lbl = get_item_name(self.current_selected_bp) or ptid
        raw_fac = (self.current_selected_bp.get("faction") or "").upper()

        fac_code = "DIY"
        if "WAR" in raw_fac: fac_code = "MIL"
        elif "CANDLE" in raw_fac: fac_code = "FAN"
        elif "MILK" in raw_fac or "M.I.L.K" in raw_fac: fac_code = "SPO"

        tier_num = 1
        m_tier = re.search(r"_0*(\d)$", ptid)
        if m_tier:
            tier_num = min(4, max(1, int(m_tier.group(1))))
        elif self.current_selected_bp.get("rarity"):
            tier_num = min(4, max(1, self.current_selected_bp["rarity"]))

        tier_metals = {
            1: f"ITMT_STONE_{fac_code}_1",
            2: f"ITMT_STONE_{fac_code}_2",
            3: f"ITMT_STONE_{fac_code}_3",
            4: f"ITMT_STONE_{fac_code}_4",
        }
        tier_mats = {
            1: ["ITMT_IRON_1", "ITMT_COPPER_1", "ITMT_ALUMI_1", "ITMT_OIL_1", "ITMT_WOOD_1"],
            2: ["ITMT_IRON_2", "ITMT_COPPER_2", "ITMT_ALUMI_2", "ITMT_OIL_2", "ITMT_WOOD_2"],
            3: ["ITMT_IRON_3", "ITMT_COPPER_3", "ITMT_ALUMI_3", "ITMT_OIL_3", "ITMT_WOOD_3"],
            4: ["ITMT_IRON_4", "ITMT_COPPER_4", "ITMT_ALUMI_4", "ITMT_OIL_4", "ITMT_WOOD_4"],
        }
        target_mats = [tier_metals.get(tier_num, f"ITMT_STONE_{fac_code}_1")] + tier_mats.get(tier_num, tier_mats[1])
        for mid in target_mats:
            modifiers.add_material_to_storage(self.main_win.save_json, mid, count=10)

        self.main_win._auto_save()
        self.main_win.update_hud()
        if hasattr(self.main_win, "tab_materials") and hasattr(self.main_win.tab_materials, "filter_materials_list"):
            self.main_win.tab_materials.filter_materials_list()
        self.main_win.set_status(t("mb_craft_kit_status", default=f"📦 Kit de forja T{tier_num} depositado en Coin Locker para {name_lbl}.", tier=tier_num, name=name_lbl))
        QMessageBox.information(
            self,
            t("mb_craft_kit_title", default="Kit de Forja Depositado"),
            t("mb_craft_kit_msg", default=f"Se ha añadido al Coin Locker el kit completo de forja T{tier_num} (+10 u. de cada material esencial) para {name_lbl}.", tier=tier_num, name=name_lbl)
        )

    def _evolve_selected_bp_to_next_tier(self):
        if not self.current_selected_bp or not self.main_win.save_json:
            return
        ptid = self.current_selected_bp.get("id")
        nextptid = self.current_selected_bp.get("nextptid", "")
        if not nextptid:
            return

        nxt_meta = next((it for it in getattr(self.main_win, "equipment_db", []) if it.get("id") == nextptid), None)
        is_nxt_uncap = nxt_meta.get("can_uncap", False) if nxt_meta else False

        modifiers.unlock_single_blueprint(self.main_win.save_json, ptid, level=4, unlock_next_tier=True)
        if is_nxt_uncap:
            modifiers.send_blueprint_to_rnd(self.main_win.save_json, nextptid, target_level=19)
        self.main_win._auto_save()
        self.filter_blueprints_list()
        self.main_win.update_hud()

        cur_name = get_item_name(self.current_selected_bp) or ptid
        nxt_name = get_item_name(nxt_meta) if nxt_meta else nextptid
        self.main_win._notify("bp_notify_tier_rnd_title", "bp_notify_tier_rnd_msg", cur_name=cur_name, nxt_name=nxt_name, nextptid=nextptid)

    def _inject_endgame_set_action(self):
        save = self.main_win.save_json
        if not save:
            return
        key = self.cb_endgame.currentData() or "white_steel"
        name, added = modifiers.inject_endgame_set(save, set_key=key, count=1, dur=50000, lvl=20)
        self.main_win._auto_save()
        self.filter_blueprints_list()
        self.main_win.update_hud()
        self.main_win._notify("bp_notify_endgame_injected_title", "bp_notify_endgame_injected_msg", added=added, name=name)

    def _set_infinite_durability_action(self):
        save = self.main_win.save_json
        if not save:
            return
        cnt = modifiers.set_infinite_durability_all_equipment(save, target_dur=50000)
        self.main_win._auto_save()
        self.main_win.update_hud()
        self.main_win._notify("bp_notify_durability_title", "bp_notify_durability_msg", cnt=cnt)

    def _set_massive_ammo_action(self):
        save = self.main_win.save_json
        if not save:
            return
        cnt = modifiers.set_massive_ammo_all_weapons(save, ammo=None)
        self.main_win._auto_save()
        self.main_win.update_hud()
        self.main_win._notify("bp_notify_ammo_title", "bp_notify_ammo_msg", cnt=cnt)

    def _upgrade_all_gear_max_lvl_action(self, target_lvl=19):
        save = self.main_win.save_json
        if not save:
            return
        cnt = modifiers.upgrade_all_equipment_max_level(save, target_lvl=target_lvl)
        self.main_win._auto_save()
        self.filter_blueprints_list()
        self.main_win.update_hud()
        if target_lvl == 19:
            self.main_win._notify("bp_notify_uncapped_rnd_title", "bp_notify_uncapped_rnd_msg", cnt=cnt)
        else:
            self.main_win._notify("bp_notify_uncapped_shop_title", "bp_notify_uncapped_shop_msg", cnt=cnt)

    def _refresh_shop_tiers_status(self):
        status = modifiers.get_shop_tier_mod_status()
        if status.get("active"):
            count = status.get("modified_count", 0)
            self.bp_shop_tiers_status_lbl.setText(t("bp_shop_tiers_active_status", count=count, default=f"Mod Tienda: ✅ ACTIVO ({count} tiers disponibles para compra)"))
            self.bp_shop_tiers_status_lbl.setStyleSheet(f"color: {ACCENT_GOLD}; font-size: 8.5pt; font-weight: bold;")
        else:
            self.bp_shop_tiers_status_lbl.setText(t("bp_shop_tiers_inactive_status", default="Mod Tienda: ⏸️ Estándar (Sólo se muestra el último tier)"))
            self.bp_shop_tiers_status_lbl.setStyleSheet(f"color: {FG_MUTED}; font-size: 8.5pt; font-weight: bold;")

    def _enable_all_shop_tiers_action(self):
        res = modifiers.enable_all_shop_tiers()
        self._refresh_shop_tiers_status()
        if res.get("success"):
            cnt = res.get("modified_count", 0)
            self.main_win._notify("bp_notify_shop_mod_title", "bp_notify_shop_mod_msg", cnt=cnt)
        else:
            self.main_win._notify("common_error", res.get("reason", "Unknown error"), kind="error")

    def _restore_shop_tiers_action(self):
        res = modifiers.restore_shop_tier_progression()
        self._refresh_shop_tiers_status()
        if res.get("success"):
            self.main_win._notify("bp_notify_progression_restored_title", "bp_notify_progression_restored_msg")
        else:
            self.main_win._notify("common_error", res.get("reason", "Unknown error"), kind="error")

    def unlock_all_blueprints_preset(self):
        save = self.main_win.save_json
        if not save:
            return
        lvl_str = self.cb_all_lvl.currentText()
        lvl_num, _, _ = self._parse_selected_level(lvl_str)
        lvl = 19 if lvl_num in (19, 20, 24, 25) else (lvl_num if lvl_num > 0 else 19)
        modifiers.unlock_all_blueprints(save, level=lvl, enable_shop_tiers=False)
        self._refresh_shop_tiers_status()
        self.main_win._auto_save()
        self.filter_blueprints_list()
        self.main_win.update_hud()
        self.main_win._notify("bp_notify_all_unlocked_title", "bp_notify_all_unlocked_msg", lvl=lvl)

    def _repair_blueprints_action(self):
        save = self.main_win.save_json
        if not save:
            return
        fixed = modifiers.repair_unlocked_blueprints_states(save)
        clamped_bp, clamped_st = modifiers.clamp_all_equipment_authentic_levels(save)
        self.main_win._auto_save()
        self.filter_blueprints_list()
        self.main_win.update_hud()
        self.main_win._notify("bp_notify_repaired_title", "bp_notify_repaired_msg", fixed=fixed, clamped_bp=clamped_bp, clamped_st=clamped_st)

    def refresh_translations(self):
        self.table.setHorizontalHeaderLabels([
            t("bp_col_item", default="Plano / Nombre Oficial"),
            t("bp_col_status", default="Estado Forja"),
            t("bp_col_storage", default="Almacén"),
            t("bp_col_bag", default="Bolsa"),
            t("bp_col_id", default="ID Plano"),
        ])
        if hasattr(self, 'search_entry'):
            self.search_entry.setPlaceholderText(t("search_placeholder", default="Nombre / ID..."))
        if hasattr(self, 'lbl_bp_search'):
            self.lbl_bp_search.setText(t("bp_search", default="🔍 Buscar:"))
        if hasattr(self, 'lbl_bp_slot'):
            self.lbl_bp_slot.setText(t("bp_slot_lbl", default="Ranura:"))
        if hasattr(self, 'lbl_bp_faction'):
            self.lbl_bp_faction.setText(t("bp_faction_lbl", default="Facción:"))
        if hasattr(self, 'lbl_bp_poss'):
            self.lbl_bp_poss.setText(t("bp_poss_lbl", default="Posesión:"))
        if hasattr(self, 'lbl_bp_dmg'):
            self.lbl_bp_dmg.setText(t("bp_dmg_lbl", default="Daño:"))
        if hasattr(self, 'lbl_bp_all_lvl'):
            self.lbl_bp_all_lvl.setText(t("bp_unlock_all_lbl", default="Nivel:"))
        if hasattr(self, 'lbl_collab'):
            self.lbl_collab.setText(t("bp_collabs_lbl", default="🎯 Eventos:"))
        if hasattr(self, 'btn_collab_all'):
            self.btn_collab_all.setText(t("bp_collab_all", default="🌐 Todos"))

        # Comboboxes
        if hasattr(self, 'cat_cb'):
            cur_cat = self.cat_cb.currentData()
            self.cat_cb.blockSignals(True)
            self.cat_cb.clear()
            self.cat_cb.addItem(t("bp_slot_all", default="Todos"), "ALL")
            self.cat_cb.addItem(t("bp_slot_helmets", default="🪖 Cascos"), "head")
            self.cat_cb.addItem(t("bp_slot_bodies", default="👕 Pechos"), "chest")
            self.cat_cb.addItem(t("bp_slot_legs", default="👖 Piernas"), "legs")
            self.cat_cb.addItem(t("bp_slot_weapons", default="⚔️ Armas"), "weapon")
            idx = self.cat_cb.findData(cur_cat)
            if idx >= 0:
                self.cat_cb.setCurrentIndex(idx)
            self.cat_cb.blockSignals(False)

        if hasattr(self, 'fac_cb'):
            cur_fac = self.fac_cb.currentData()
            self.fac_cb.blockSignals(True)
            self.fac_cb.clear()
            fac_defs = [
                ("ALL", t("bp_fac_all", default="Todas")),
                ("DOD", t("bp_fac_dod", default="🔨 D.O.D. ARMS")),
                ("MIL", t("bp_fac_we", default="🎖️ WAR ENSEMBLE")),
                ("FAN", t("bp_fac_cw", default="🕯️ CANDLE WOLF")),
                ("SPO", t("bp_fac_milk", default="🥛 M.I.L.K.")),
                ("FORCEMEN", t("bp_fac_44ce", default="⚡ 4 FORCEMEN & TENGOKU")),
                ("JACKAL", t("bp_fac_jackals", default="🕶️ JACKALS")),
                ("RE", t("bp_fac_re", default="♻️ RE (Reciclador)")),
                ("SPE", t("bp_fac_spe", default="🎭 Especial / Evento")),
                ("GEN", t("bp_fac_gen", default="⚔️ General / Otras")),
            ]
            for code, label in fac_defs:
                self.fac_cb.addItem(label, code)
            idx = self.fac_cb.findData(cur_fac)
            if idx >= 0:
                self.fac_cb.setCurrentIndex(idx)
            self.fac_cb.blockSignals(False)

        if hasattr(self, 'poss_cb'):
            cur_poss = self.poss_cb.currentData()
            self.poss_cb.blockSignals(True)
            self.poss_cb.clear()
            self.poss_cb.addItem(t("bp_poss_all", default="Todos"), "ALL")
            self.poss_cb.addItem(t("bp_poss_storage", default="📦 En Almacén (> 0)"), "STORAGE")
            self.poss_cb.addItem(t("bp_poss_shop", default="⭐ Desbloqueados en Tienda (+4)"), "SHOP")
            self.poss_cb.addItem(t("bp_poss_rnd", default="🔨 En I+D (REMODEL / MAP)"), "RND")
            self.poss_cb.addItem(t("bp_poss_locked", default="❌ Bloqueados (Faltantes)"), "LOCKED")
            idx = self.poss_cb.findData(cur_poss)
            if idx >= 0:
                self.poss_cb.setCurrentIndex(idx)
            self.poss_cb.blockSignals(False)

        if hasattr(self, 'dmg_cb'):
            cur_dmg = self.dmg_cb.currentData()
            self.dmg_cb.blockSignals(True)
            self.dmg_cb.clear()
            self.dmg_cb.addItem(t("bp_dmg_all", default="Todos"), "ALL")
            self.dmg_cb.addItem(t("bp_dmg_slash", default="🗡️ Corte (Slash)"), "SLASH")
            self.dmg_cb.addItem(t("bp_dmg_blunt", default="🔨 Golpe (Blunt)"), "BLUNT")
            self.dmg_cb.addItem(t("bp_dmg_pierce", default="🏹 Perforación (Pierce)"), "PIERCE")
            self.dmg_cb.addItem(t("bp_dmg_fire", default="🔥 Fuego (Burn)"), "FIRE")
            self.dmg_cb.addItem(t("bp_dmg_elec", default="⚡ Electricidad (Electric)"), "ELECTRIC")
            self.dmg_cb.addItem(t("bp_dmg_poison", default="🧪 Veneno (Poison)"), "POISON")
            idx = self.dmg_cb.findData(cur_dmg)
            if idx >= 0:
                self.dmg_cb.setCurrentIndex(idx)
            self.dmg_cb.blockSignals(False)

        # Right workbench cards & buttons
        if hasattr(self, 'box_card'):
            self.box_card.setTitle(t("bp_card_title", default="Ficha Técnica de Plano Chokufunsha"))
        if hasattr(self, 'bp_set_btn'):
            self.bp_set_btn.setText(t("bp_view_set_btn", default="👘 Ver Conjunto en Visor de Sets"))
        if hasattr(self, 'indiv_box'):
            self.indiv_box.setTitle(t("bp_indiv_actions_title", default="Acciones Individuales para esta Pieza"))
        if hasattr(self, 'lbl_bp_lvl'):
            self.lbl_bp_lvl.setText(t("bp_lvl_lbl", default="Nivel:"))
        if hasattr(self, 'btn_unlock_shop'):
            self.btn_unlock_shop.setText(t("bp_unlock_shop_btn", default="⭐ Desbloquear en Tienda"))
        if hasattr(self, 'btn_send_rnd'):
            self.btn_send_rnd.setText(t("bp_send_rnd_btn", default="🔨 Enviar / Mantener en I+D"))
        if hasattr(self, 'btn_send_storage'):
            self.btn_send_storage.setText(t("bp_send_storage_btn", default="📦 Enviar 1 u. al Almacén"))
        if hasattr(self, 'btn_deposit_kit'):
            self.btn_deposit_kit.setText(t("bp_deposit_kit_btn", default="🛠️ Depositar Kit de Forja (+10 u.)"))
        if hasattr(self, 'btn_evolve_tier'):
            self.btn_evolve_tier.setText(t("bp_evolve_tier_btn", default="🔄 Desbloquear Sig. Tier (+4)"))
        if hasattr(self, 'endgame_box'):
            self.endgame_box.setTitle(t("bp_endgame_box_title", default="🛡️ Inyector de Sets Endgame"))
        if hasattr(self, 'btn_inject_set'):
            self.btn_inject_set.setText(t("bp_inject_set_btn", default="🛡️ Inyectar Set Completo al Almacén"))
        if hasattr(self, 'global_gear_box'):
            self.global_gear_box.setTitle(t("bp_mass_actions_title", default="Modificadores y Mejoras Masivas"))
        if hasattr(self, 'btn_dur'):
            self.btn_dur.setText(t("bp_inf_dur_btn", default="✨ Reparar Todo al 100% de Durabilidad (Legítimo)"))
        if hasattr(self, 'btn_ammo'):
            self.btn_ammo.setText(t("bp_inf_ammo_btn", default="🎯 Recargar Munición al Máximo (Armas de Fuego)"))
        if hasattr(self, 'btn_upg19'):
            self.btn_upg19.setText(t("bp_upg_all19_btn", default="⚡ Preparar Todo a Nivel +19 en I+D (Para Fabricar)"))
        if hasattr(self, 'btn_upg24'):
            self.btn_upg24.setText(t("bp_upg_all24_btn", default="🔥 Desbloquear Todo a Nivel +19 en Tienda (Directo)"))
        if hasattr(self, 'shop_tiers_box'):
            self.shop_tiers_box.setTitle(t("bp_shop_tiers_mod_title", default="🏬 Mod Tienda Chokufunsha: Todos los Tiers (1 al 4)"))
        if hasattr(self, 'lbl_shop_desc'):
            self.lbl_shop_desc.setText(t("bp_shop_tiers_mod_desc", default="Permite comprar cualquier tier en la tienda (Tier 1 al 4 y Destope) sin ocultar los anteriores."))
        if hasattr(self, 'btn_shop_enable'):
            self.btn_shop_enable.setText(t("bp_shop_tiers_enable_btn", default="🔓 Desbloquear Todos los Tiers en Tienda"))
        if hasattr(self, 'btn_shop_restore'):
            self.btn_shop_restore.setText(t("bp_shop_tiers_restore_btn", default="🔒 Restaurar Progresión Normal"))

        self.btn_unlock_all.setText(t("bp_unlock_all_btn", default="🌟 DESBLOQUEAR TODO"))
        self.btn_repair.setText(t("bp_repair_btn", default="🔧 Reparar I+D"))
        self.btn_sets_viewer.setText(t("bp_view_sets_btn", default="👘 Visor de Sets por Nivel"))
        self.filter_blueprints_list()
        self._refresh_shop_tiers_status()
