# -*- coding: utf-8 -*-
"""
Fighters Freezer Tab for LET IT DIE Save Editor (PySide6 Edition).
Exact layout, colors, and behavior parity with Cyberpunk Dark design.
"""

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QGroupBox, QLabel, QLineEdit, QPushButton, QComboBox,
    QSpinBox, QSplitter, QTreeWidget, QTreeWidgetItem,
    QScrollArea, QFrame, QMessageBox, QInputDialog, QHeaderView
)

import re
import modifiers
import i18n
from i18n import t
from ui_qt.theme import (
    get_pixmap, get_icon, get_fighter_model_art, get_fighter_class_icon,
    find_decal_art, ACCENT_GOLD, ACCENT_GREEN,
    ACCENT_CYAN, ACCENT_RED, FG_MUTED, FG_MAIN, BG_CARD
)
from game_data import FIGHTER_CLASSES


class FightersTab(QWidget):
    def __init__(self, main_win):
        super().__init__()
        self.main_win = main_win
        self.current_fighter_idx = 0
        self.fighters_data = []
        self._build_ui()

    def _build_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(8, 8, 8, 8)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        root_layout.addWidget(splitter)

        # =============================================================
        # LEFT PANEL: Fighter Freezer List & Controls
        # =============================================================
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 4, 0)
        left_layout.setSpacing(6)

        self.box_freezer = QGroupBox(t("f_freezer_title"))
        box_freezer_layout = QVBoxLayout(self.box_freezer)
        box_freezer_layout.setSpacing(6)

        # 1. Reorder Toolbar
        reorder_f = QHBoxLayout()
        self.btn_up = QPushButton(t("f_move_up"))
        self.btn_up.setProperty("accent", "true")
        self.btn_up.clicked.connect(self._move_fighter_up_action)
        reorder_f.addWidget(self.btn_up)

        self.btn_down = QPushButton(t("f_move_down"))
        self.btn_down.setProperty("accent", "true")
        self.btn_down.clicked.connect(self._move_fighter_down_action)
        reorder_f.addWidget(self.btn_down)
        box_freezer_layout.addLayout(reorder_f)

        # 2. Management Toolbar
        manage_f = QHBoxLayout()
        self.btn_create = QPushButton(t("f_create_btn"))
        self.btn_create.setProperty("success", "true")
        self.btn_create.clicked.connect(self._create_new_fighter_dialog)
        manage_f.addWidget(self.btn_create)

        self.btn_clone = QPushButton(t("f_clone_btn"))
        self.btn_clone.clicked.connect(self._clone_fighter_action)
        manage_f.addWidget(self.btn_clone)

        self.btn_delete = QPushButton(t("f_delete_btn"))
        self.btn_delete.setProperty("danger", "true")
        self.btn_delete.clicked.connect(self._delete_fighter_action)
        manage_f.addWidget(self.btn_delete)
        box_freezer_layout.addLayout(manage_f)

        # 3. Skip Tutorial Button
        self.btn_unlock_freezer = QPushButton(t("f_tut_btn", default="🎓 Desbloquear Congelador (Omitir Tutorial)"))
        self.btn_unlock_freezer.clicked.connect(self._unlock_freezer_action)
        box_freezer_layout.addWidget(self.btn_unlock_freezer)

        # 4. TreeWidget (Fighters List)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels([t("f_col_name"), t("f_col_num"), t("f_col_lvl"), t("f_col_state")])
        self.tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.tree.header().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.tree.header().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.tree.setIconSize(QSize(40, 44))
        self.tree.itemSelectionChanged.connect(self._on_tree_selection_changed)
        self.tree.itemClicked.connect(self._on_tree_item_clicked)
        box_freezer_layout.addWidget(self.tree)

        left_layout.addWidget(self.box_freezer)
        splitter.addWidget(left_widget)

        # =============================================================
        # RIGHT PANEL: Fighter Tech Sheet
        # =============================================================
        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_scroll.setFrameShape(QFrame.Shape.NoFrame)

        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(4, 0, 0, 0)
        right_layout.setSpacing(8)

        self.box_sheet = QGroupBox(t("f_tech_sheet", default="Ficha Técnica del Luchador"))
        sheet_layout = QVBoxLayout(self.box_sheet)
        sheet_layout.setSpacing(8)

        # Profile Header (Avatar + Class + Title)
        prof_f = QHBoxLayout()
        self.hero_avatar_btn = QPushButton()
        self.hero_avatar_btn.setFixedSize(58, 70)
        self.hero_avatar_btn.setStyleSheet("border: 2px solid #252b40; border-radius: 6px; background-color: #151824;")
        self.hero_avatar_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.hero_avatar_btn.clicked.connect(self._open_fighter_model_gallery)
        prof_f.addWidget(self.hero_avatar_btn)

        self.class_icon_lbl = QLabel()
        self.class_icon_lbl.setFixedSize(48, 48)
        self.class_icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        prof_f.addWidget(self.class_icon_lbl)

        title_v = QVBoxLayout()
        self.fighter_title_lbl = QLabel(t("f_select_prompt", default="Selecciona un luchador"))
        self.fighter_title_lbl.setStyleSheet(f"color: {ACCENT_GOLD}; font-size: 13pt; font-weight: bold;")
        title_v.addWidget(self.fighter_title_lbl)

        self.fighter_sub_lbl = QLabel(t("f_sub_lbl_placeholder", default="---"))
        self.fighter_sub_lbl.setStyleSheet(f"color: {FG_MUTED}; font-size: 9pt;")
        title_v.addWidget(self.fighter_sub_lbl)
        prof_f.addLayout(title_v)
        prof_f.addStretch()
        sheet_layout.addLayout(prof_f)

        # 1. Identity Config Frame
        self.box_id = QGroupBox(t("f_id_config", default="Identidad y Configuración"))
        id_layout = QGridLayout(self.box_id)
        id_layout.setSpacing(6)

        # Row 0: Name & Class
        self.lbl_name = QLabel(t("f_lbl_name", default="Nombre:"))
        id_layout.addWidget(self.lbl_name, 0, 0)
        self.name_entry = QLineEdit()
        id_layout.addWidget(self.name_entry, 0, 1)

        self.lbl_class = QLabel(t("f_lbl_class", default="Clase:"))
        id_layout.addWidget(self.lbl_class, 0, 2)
        self.class_cb = QComboBox()
        self._class_keys = ["BAL", "BRE", "DEF", "TEC", "SHT", "COL", "SKI", "LUK"]
        for k in self._class_keys:
            self.class_cb.addItem(t(f"cls_opt_{k.lower()}", default=k), k)
        id_layout.addWidget(self.class_cb, 0, 3)

        # Row 1: Grade, Level
        self.lbl_grade = QLabel(t("f_lbl_grade", default="Grado:"))
        id_layout.addWidget(self.lbl_grade, 1, 0)
        self.grade_cb = QComboBox()
        for g in range(1, 7):
            self.grade_cb.addItem(f"G{g}", g)
        id_layout.addWidget(self.grade_cb, 1, 1)

        self.lbl_lvl = QLabel(t("bp_lvl_lbl", default="Level:"))
        id_layout.addWidget(self.lbl_lvl, 1, 2)
        self.lvl_spin = QSpinBox()
        self.lvl_spin.setRange(1, 247)
        id_layout.addWidget(self.lvl_spin, 1, 3)

        # Row 2: HP Actual and MINGO Bag Bonus
        self.lbl_hp_cur = QLabel(t("f_lbl_hp_cur", default="HP Actual:"))
        id_layout.addWidget(self.lbl_hp_cur, 2, 0)
        self.hp_spin = QSpinBox()
        self.hp_spin.setRange(1, 9999999)
        id_layout.addWidget(self.hp_spin, 2, 1)

        self.lbl_mingo = QLabel(t("f_mingo_bonus_lbl", default="Bolsa MINGO:"))
        id_layout.addWidget(self.lbl_mingo, 2, 2)
        self.bag_cb = QComboBox()
        for b in ["0", "1", "2", "3"]:
            self.bag_cb.addItem(b, int(b))
        self.bag_cb.currentIndexChanged.connect(self._on_mingo_bag_ui_changed)
        id_layout.addWidget(self.bag_cb, 2, 3)

        # Row 3: Character Model / Appearance & 3D Gallery Button
        self.lbl_model = QLabel(t("f_lbl_model", default="Modelo / Apariencia:"))
        id_layout.addWidget(self.lbl_model, 3, 0)

        model_row = QHBoxLayout()
        model_row.setSpacing(6)
        self.model_cb = QComboBox()
        self.model_cb.setIconSize(QSize(24, 28))
        self._populate_model_combobox()
        self.model_cb.currentIndexChanged.connect(self._update_fighter_model_preview)
        model_row.addWidget(self.model_cb, 1)

        self.btn_gallery = QPushButton(t("f_create_gallery_btn", default="🖼️ Galería 3D"))
        self.btn_gallery.setProperty("accent", "true")
        self.btn_gallery.clicked.connect(self._open_fighter_model_gallery)
        model_row.addWidget(self.btn_gallery)
        id_layout.addLayout(model_row, 3, 1, 1, 3)

        # Row 4: Real In-Game Capacity indicator
        self.f_real_bag_lbl = QLabel(t("f_real_bag_calculating", default="🎒 Capacidad Real en Juego: Calculando..."))
        self.f_real_bag_lbl.setStyleSheet(f"color: {ACCENT_GOLD}; font-size: 8.5pt; font-weight: bold;")
        id_layout.addWidget(self.f_real_bag_lbl, 4, 0, 1, 4)

        sheet_layout.addWidget(self.box_id)

        # 2. Base Stats Grid (3 columns x 2 rows)
        self.box_stats = QGroupBox(t("f_base_stats_box", default="Atributos Base (Puntos Asignados)"))
        stats_g = QGridLayout(self.box_stats)
        stats_g.setSpacing(6)

        self._stat_keys_def = [
            ("hp", "f_hp_vit", "HP (Vitalidad)", 0, 0),
            ("stm", "f_stm_res", "STM (Resistencia)", 0, 2),
            ("str", "f_str_pow", "STR (Fuerza)", 0, 4),
            ("dex", "f_dex_agi", "DEX (Destreza)", 1, 0),
            ("vit", "f_vit_def", "VIT (Defensa)", 1, 2),
            ("luk", "f_luk_luck", "LUK (Suerte)", 1, 4),
        ]
        self.stat_labels = {}
        self.stat_spins = {}
        for key, tr_key, def_name, r, c in self._stat_keys_def:
            lbl = QLabel(t(tr_key, default=def_name))
            self.stat_labels[key] = lbl
            stats_g.addWidget(lbl, r, c)
            spin = QSpinBox()
            spin.setRange(1, 45)
            stats_g.addWidget(spin, r, c + 1)
            self.stat_spins[key] = spin

        sheet_layout.addWidget(self.box_stats)

        # 3. Equipped Decals Preview (8 slots in 4x2 grid)
        self.box_decals = QGroupBox(t("f_equipped_decals_box", default="Calcomanías Equipadas (Ranuras 1 - 8)"))
        decals_g = QGridLayout(self.box_decals)
        decals_g.setSpacing(6)
        self.decal_slots = []
        for s in range(8):
            row_layout = QHBoxLayout()
            d_icon = QLabel()
            d_icon.setFixedSize(28, 28)
            d_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            row_layout.addWidget(d_icon)
            d_name = QLabel(t("f_decal_empty", default="[ Vacío ]"))
            d_name.setStyleSheet(f"color: {FG_MUTED}; font-size: 8.5pt;")
            row_layout.addWidget(d_name)
            row_layout.addStretch()
            self.decal_slots.append((d_icon, d_name))

            r = s % 4
            c = s // 4
            decals_g.addLayout(row_layout, r, c)
        sheet_layout.addWidget(self.box_decals)

        # 4. Quick Fighter Actions Toolbar
        act_f = QHBoxLayout()
        self.btn_save_f = QPushButton(t("f_apply_btn", default="💾 Aplicar Cambios a este Luchador"))
        self.btn_save_f.setProperty("accent", "true")
        self.btn_save_f.clicked.connect(self._save_fighter_changes)
        act_f.addWidget(self.btn_save_f)

        self.btn_revive = QPushButton(t("f_revive_btn", default="❤️ Revivir / Rescatar Luchadores"))
        self.btn_revive.setProperty("success", "true")
        self.btn_revive.clicked.connect(self.revive_current_fighter)
        act_f.addWidget(self.btn_revive)

        self.btn_max_stats = QPushButton(t("f_max_stats_btn", default="⚡ Maximizar Luchador (Lvl 247)"))
        self.btn_max_stats.clicked.connect(self.max_current_fighter)
        act_f.addWidget(self.btn_max_stats)
        sheet_layout.addLayout(act_f)

        # 5. Engine Mod: Death Bag Capacity in masters.db
        self.box_db_bag = QGroupBox(t("db_mod_box_title", default="🔧 Mod del Motor: Capacidad de Bolsa en masters.db"))
        db_v = QVBoxLayout(self.box_db_bag)
        db_v.setSpacing(6)

        self.f_bag_db_status_lbl = QLabel("...")
        self.f_bag_db_status_lbl.setStyleSheet("font-size: 8.5pt;")
        db_v.addWidget(self.f_bag_db_status_lbl)

        db_btn_row = QHBoxLayout()
        self.btn_expand_bag = QPushButton(t("db_expand_btn", default="🚀 Expandir Capacidad en masters.db"))
        self.btn_expand_bag.setProperty("accent", "true")
        self.btn_expand_bag.clicked.connect(self._expand_deathbag_masters_action)
        db_btn_row.addWidget(self.btn_expand_bag)

        self.btn_restore_bag = QPushButton(t("db_restore_btn", default="🔄 Restaurar Original"))
        self.btn_restore_bag.clicked.connect(self._restore_deathbag_masters_action)
        db_btn_row.addWidget(self.btn_restore_bag)
        db_v.addLayout(db_btn_row)
        sheet_layout.addWidget(self.box_db_bag)

        # 6. Meta Decal Presets for Fighters
        self.box_presets = QGroupBox(t("f_presets_box", default="🏆 Presets Tácticos de Calcomanías"))
        preset_v = QVBoxLayout(self.box_presets)
        preset_v.setSpacing(6)

        preset_top = QHBoxLayout()
        self.lbl_preset = QLabel(t("f_preset_lbl", default="Preset:"))
        preset_top.addWidget(self.lbl_preset)

        self.decal_preset_cb = QComboBox()
        self.decal_preset_cb.addItem(t("preset_tengoku_climber", default="Tengoku God Climber (Pisos 51F - 350F+)"), "tengoku_climber")
        self.decal_preset_cb.addItem(t("preset_kamas_god", default="Tirador KAMAS Definitivo (Full Shooter Meta)"), "kamas_god")
        self.decal_preset_cb.addItem(t("preset_melee_melter", default="Destructor Melee (Mayal / Machete / Katana)"), "melee_melter")
        self.decal_preset_cb.addItem(t("preset_tdm_defense", default="Pesadilla de Defensa TDM (Invulnerable Tank)"), "tdm_defense")
        preset_top.addWidget(self.decal_preset_cb, 1)
        preset_v.addLayout(preset_top)

        preset_btns = QHBoxLayout()
        self.btn_equip_preset = QPushButton(t("f_preset_btn", default="👑 Equipar Preset al Luchador Actual"))
        self.btn_equip_preset.setProperty("accent", "true")
        self.btn_equip_preset.clicked.connect(self._equip_decal_preset_action)
        preset_btns.addWidget(self.btn_equip_preset)

        self.btn_apply_preset = QPushButton(t("f_inject_preset_btn", default="🎒 Añadir Calcomanías al Almacén"))
        self.btn_apply_preset.clicked.connect(self._apply_decal_preset_action)
        preset_btns.addWidget(self.btn_apply_preset)
        preset_v.addLayout(preset_btns)
        sheet_layout.addWidget(self.box_presets)

        sheet_layout.addStretch()
        right_layout.addWidget(self.box_sheet)
        right_scroll.setWidget(right_widget)
        splitter.addWidget(right_scroll)

        # 40% left, 60% right
        splitter.setSizes([380, 560])

    def refresh_data(self):
        """Refreshes the fighters list and current fighter details."""
        save = self.main_win.save_json
        if not save:
            return

        self.fighters_data = modifiers.get_all_fighters_info(save)
        cur_idx = self.current_fighter_idx
        self.tree.blockSignals(True)
        self.tree.clear()

        sel_item = None

        for idx, f in enumerate(self.fighters_data):
            name = f.get("name", f"Fighter #{idx+1}")
            slot_str = str(f.get("slot", idx+1))
            lvl_str = f"Lv.{f.get('level', 1)}"
            cls_code = f.get("class", "BAL")
            is_dead = bool(f.get("die", 0))
            alive_txt = t("f_state_alive", default="Vivo")
            dead_txt = t("f_state_dead", default="Muerto")
            state_str = f"💀 {dead_txt}" if is_dead else f"✔️ {alive_txt}"

            item = QTreeWidgetItem([name, slot_str, lvl_str, state_str])
            item.setData(0, Qt.ItemDataRole.UserRole, idx)

            # Icon: Fighter model art or class icon
            model_art = get_fighter_model_art(f.get("body", f.get("model", "")))
            cls_icon = get_fighter_class_icon(cls_code)
            ico = get_icon(model_art, (40, 44)) or get_icon(cls_icon, (40, 44))
            if ico and not ico.isNull():
                item.setIcon(0, ico)

            self.tree.addTopLevelItem(item)
            if idx == cur_idx:
                sel_item = item

        target_item = sel_item or (self.tree.topLevelItem(0) if self.tree.topLevelItemCount() > 0 else None)
        if target_item:
            self.tree.setCurrentItem(target_item)
            target_item.setSelected(True)
            self.tree.scrollToItem(target_item)
            idx = target_item.data(0, Qt.ItemDataRole.UserRole)
            if idx is not None and 0 <= idx < len(self.fighters_data):
                self.current_fighter_idx = idx
                self._load_fighter_details(idx)
        self.tree.blockSignals(False)

    def _on_tree_selection_changed(self):
        items = self.tree.selectedItems()
        item = items[0] if items else self.tree.currentItem()
        if not item:
            return
        idx = item.data(0, Qt.ItemDataRole.UserRole)
        if idx is not None and 0 <= idx < len(self.fighters_data):
            self.current_fighter_idx = idx
            self._load_fighter_details(idx)

    def _populate_model_combobox(self):
        self.model_cb.blockSignals(True)
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
        self.model_cb.blockSignals(False)

    def _on_tree_item_clicked(self, item, column):
        idx = item.data(0, Qt.ItemDataRole.UserRole)
        if idx is not None and 0 <= idx < len(self.fighters_data):
            self.current_fighter_idx = idx
            self._load_fighter_details(idx)

    def _load_fighter_details(self, idx):
        if idx < 0 or idx >= len(self.fighters_data):
            return
        f = self.fighters_data[idx]
        save = self.main_win.save_json

        name = f.get("name", "")
        self.name_entry.blockSignals(True)
        self.name_entry.setText(name)
        self.name_entry.blockSignals(False)

        cls_code = f.get("class", "BAL")
        self.class_cb.blockSignals(True)
        found_idx = self.class_cb.findData(cls_code)
        if found_idx >= 0:
            self.class_cb.setCurrentIndex(found_idx)
        self.class_cb.blockSignals(False)

        grade = f.get("grade", 1)
        self.grade_cb.blockSignals(True)
        found_g = self.grade_cb.findText(f"G{grade}")
        if found_g >= 0:
            self.grade_cb.setCurrentIndex(found_g)
        else:
            self.grade_cb.setCurrentText(f"G{grade}")
        self.grade_cb.blockSignals(False)

        lvl = f.get("level", 1)
        self.lvl_spin.blockSignals(True)
        self.lvl_spin.setValue(lvl)
        self.lvl_spin.blockSignals(False)

        hp_val = f.get("hp", 100)
        self.hp_spin.blockSignals(True)
        self.hp_spin.setValue(hp_val)
        self.hp_spin.blockSignals(False)

        mingo_bag = min(3, max(0, int(f.get("bag", 0))))
        self.bag_cb.blockSignals(True)
        idx_bag = self.bag_cb.findData(mingo_bag)
        if idx_bag >= 0:
            self.bag_cb.setCurrentIndex(idx_bag)
        self.bag_cb.blockSignals(False)

        # Title & Meta Subtitle
        cls_local = t(f"cls_{cls_code.lower()}", default=cls_code)
        self.fighter_title_lbl.setText(name)
        self.fighter_sub_lbl.setText(t("f_class_meta", cls=f"{cls_local} ({cls_code})", grd=grade, lvl=lvl, default=f"{cls_local} ({cls_code}) | Grd: {grade} | Lvl: {lvl}"))

        # Class icon
        cls_ico_name = get_fighter_class_icon(cls_code)
        pix_cls = get_pixmap(cls_ico_name, (48, 48), preserve_aspect=True)
        if pix_cls and not pix_cls.isNull():
            self.class_icon_lbl.setPixmap(pix_cls)
        else:
            self.class_icon_lbl.clear()

        # Character model combobox & Hero Portrait
        body_val = f.get("body", f.get("model", "BODY_FEMALE_001"))
        self.model_cb.blockSignals(True)
        found_m = False
        for i in range(self.model_cb.count()):
            d = self.model_cb.itemData(i)
            if d and d in body_val:
                self.model_cb.setCurrentIndex(i)
                found_m = True
                break
        if not found_m:
            for i in range(self.model_cb.count()):
                if body_val in self.model_cb.itemText(i):
                    self.model_cb.setCurrentIndex(i)
                    break
        self.model_cb.blockSignals(False)

        art_rel = get_fighter_model_art(body_val)
        avatar_pix = get_pixmap(art_rel, (54, 66), preserve_aspect=True)
        if avatar_pix and not avatar_pix.isNull():
            self.hero_avatar_btn.setIcon(QIcon(avatar_pix))
            self.hero_avatar_btn.setIconSize(QSize(54, 66))

        # Real in-game capacity indicator & deathbag status
        self._update_real_bag_capacity(mingo_bag)
        self._refresh_deathbag_db_status()

        # Stats allocation points (1..45)
        for key in ["hp", "stm", "str", "dex", "vit", "luk"]:
            val = f.get(f"{key}_pts") if f.get(f"{key}_pts") is not None else f.get(key, 20)
            spin = self.stat_spins.get(key)
            if spin:
                spin.blockSignals(True)
                spin.setValue(int(val))
                spin.blockSignals(False)

        # Equipped Decals from soul["skl"]["eqskl"][body_uid] matching e.get("cid") == cid
        cid = f.get("cid", "")
        decals_map = getattr(self.main_win, "decals_map", {})
        body_uid = modifiers.get_player_uid(save) if save else ""
        eq_list = save.get("soul", {}).get("skl", {}).get("eqskl", {}).get(body_uid, []) if (save and body_uid) else []
        fighter_eq = [e for e in eq_list if e.get("cid") == cid]

        for s_idx in range(8):
            d_icon_lbl, d_name_lbl = self.decal_slots[s_idx]
            matching = [e for e in fighter_eq if e.get("slot") == s_idx]
            if matching:
                did = matching[0].get("sklid", "")
                d_info = decals_map.get(did, {})
                d_name = i18n.get_entity_display_title(d_info) or i18n.get_item_name(d_info) or did
                is_p = did.endswith("_P") or d_info.get("premium", False)
                d_name_lbl.setText(t("f_slot_decal_equipped", slot=s_idx+1, name=d_name, id=did, default=f"Slot {s_idx+1}: {d_name} ({did})"))
                d_name_lbl.setStyleSheet(f"color: {ACCENT_GOLD}; font-weight: bold; font-size: 8.5pt;")
                art_rel = find_decal_art(did, is_premium=is_p)
                pix = get_pixmap(art_rel, (28, 28), preserve_aspect=True)
                if pix and not pix.isNull():
                    d_icon_lbl.setPixmap(pix)
                else:
                    d_icon_lbl.clear()
            else:
                d_name_lbl.setText(t("f_slot_decal_empty", slot=s_idx+1, default=f"Slot {s_idx+1}: [ {t('f_slot_empty', default='Vacío')} ]"))
                d_name_lbl.setStyleSheet(f"color: {FG_MUTED}; font-size: 8.5pt;")
                d_icon_lbl.clear()

    def _on_mingo_bag_ui_changed(self):
        val = self.bag_cb.currentData()
        if val is None:
            try:
                val = int(self.bag_cb.currentText())
            except ValueError:
                val = 0
        self._update_real_bag_capacity(val)

    def _update_fighter_model_preview(self):
        code = self.model_cb.currentData()
        if not code:
            txt = self.model_cb.currentText()
            m = re.search(r"BODY_(FEMALE|MALE)_\d+", txt, re.IGNORECASE)
            code = m.group(0) if m else txt
        art_rel = get_fighter_model_art(code)
        avatar_pix = get_pixmap(art_rel, (54, 66), preserve_aspect=True)
        if avatar_pix and not avatar_pix.isNull():
            self.hero_avatar_btn.setIcon(QIcon(avatar_pix))
            self.hero_avatar_btn.setIconSize(QSize(54, 66))

    def _update_real_bag_capacity(self, mingo_bag):
        save = self.main_win.save_json
        db_st = modifiers.get_deathbag_masters_status(save_path=getattr(self.main_win, "save_path", None))
        vip_active = bool(save.get("soul", {}).get("vip", {}).get("flag", 0)) if save else False
        vip_bonus = db_st.get("vip_bonus", 10) if vip_active else 0
        base_slots = db_st.get("min_bag", 20)
        total_slots = base_slots + mingo_bag + vip_bonus
        vip_txt = t("f_real_bag_vip_bonus", vip=vip_bonus, default=f" (+{vip_bonus} Pase VIP)") if vip_bonus > 0 else ""
        self.f_real_bag_lbl.setText(
            t("f_real_bag_info", total=total_slots, base=base_slots, mingo=mingo_bag, vip=vip_txt,
              default=f"🎒 Capacidad Real: {total_slots} ranuras (Base: {base_slots} + Bolsa Mingo: +{mingo_bag}{vip_txt})")
        )

    def _save_fighter_changes(self):
        save = self.main_win.save_json
        if not save or self.current_fighter_idx >= len(self.fighters_data):
            return
        idx = self.current_fighter_idx
        name = self.name_entry.text().strip()
        cls_code = self.class_cb.currentData() or "BAL"
        model_val = self.model_cb.currentData() or self.model_cb.currentText()
        try:
            grade_str = self.grade_cb.currentText().replace("G", "").strip()
            grade = int(grade_str)
            lvl = self.lvl_spin.value()
            hp_val = self.hp_spin.value()
            bag_val = int(self.bag_cb.currentText())
            php = self.stat_spins["hp"].value()
            pstm = self.stat_spins["stm"].value()
            pstr = self.stat_spins["str"].value()
            pdex = self.stat_spins["dex"].value()
            pvit = self.stat_spins["vit"].value()
            pluk = self.stat_spins["luk"].value()
        except (ValueError, KeyError):
            self.main_win._notify("error", "err_num_fields", kind="error")
            return

        modifiers.update_fighter(
            save, idx,
            name=name, clazz=cls_code, grade=grade, lvl=lvl, hp=hp_val,
            str_stat=pstr, dex=pdex, vit=pvit, stm=pstm, luk=pluk, bag=bag_val,
            param_hp=php, param_stm=pstm, param_str=pstr, param_dex=pdex, param_vit=pvit, param_luk=pluk,
            body_model=model_val
        )
        self.main_win._auto_save()
        self.refresh_data()
        self.main_win.update_hud()
        self.main_win._notify("f_notify_updated_title", "f_notify_updated_msg", name=name, num=idx+1)

    def revive_current_fighter(self):
        save = self.main_win.save_json
        if not save:
            return
        modifiers.revive_all_fighters(save)
        self.main_win._auto_save()
        self.refresh_data()
        self.main_win.update_hud()
        self.main_win._notify("f_notify_all_revived_title", "f_notify_all_revived_msg")

    def max_current_fighter(self):
        save = self.main_win.save_json
        if not save:
            return
        modifiers.max_fighter_level_and_stats(save, fighter_index=self.current_fighter_idx, level=247)
        self.main_win._auto_save()
        self.refresh_data()
        self.main_win.update_hud()
        self.main_win._notify("f_notify_maximized_title", "f_notify_maximized_msg", num=self.current_fighter_idx+1)

    def _move_fighter_up_action(self):
        save = self.main_win.save_json
        if not save or self.current_fighter_idx <= 0:
            return
        if modifiers.move_fighter_up(save, self.current_fighter_idx):
            self.current_fighter_idx -= 1
            self.main_win._auto_save()
            self.refresh_data()
            self.main_win.update_hud()

    def _move_fighter_down_action(self):
        save = self.main_win.save_json
        if not save or self.current_fighter_idx >= len(self.fighters_data) - 1:
            return
        if modifiers.move_fighter_down(save, self.current_fighter_idx):
            self.current_fighter_idx += 1
            self.main_win._auto_save()
            self.refresh_data()
            self.main_win.update_hud()

    def _create_new_fighter_dialog(self):
        from ui_qt.dialogs.create_fighter import CreateFighterDialog
        save = self.main_win.save_json
        if not save:
            return
        uid = modifiers.get_player_uid(save)
        fighters = save.get("bodyuser", {}).get(uid, [])
        if len(fighters) >= 10:
            self.main_win._notify("fighter_freezer_full", "f_freezer_full_msg", kind="warning")
            return
        dlg = CreateFighterDialog(self.main_win)
        if dlg.exec():
            total_f = len(save.get("bodyuser", {}).get(uid, []))
            self.current_fighter_idx = max(0, total_f - 1)
            self.refresh_data()
            self.main_win.update_hud()

    def _clone_fighter_action(self):
        save = self.main_win.save_json
        if not save or self.current_fighter_idx >= len(self.fighters_data):
            return
        uid = modifiers.get_player_uid(save)
        fighters = save.get("bodyuser", {}).get(uid, [])
        if len(fighters) >= 10:
            self.main_win._notify("fighter_freezer_full", "f_freezer_full_msg", kind="warning")
            return
        chr_chrs = save.get("soul", {}).get("chr", {}).get("chrs", {}).get(uid, [])
        orig_name = chr_chrs[self.current_fighter_idx].get("name", "Luchador") if self.current_fighter_idx < len(chr_chrs) else "Luchador"
        new_name, ok = QInputDialog.getText(
            self,
            t("f_clone_title", default="Clonar Luchador"),
            t("f_clone_prompt", default="Nombre para el clon:"),
            text=t("f_clone_default_fmt", name=orig_name, default=f"{orig_name} (Clon)")
        )
        if not ok or not new_name.strip():
            return
        s_ok, res = modifiers.clone_fighter(save, self.current_fighter_idx, new_name=new_name.strip())
        if not s_ok:
            self.main_win._notify("error", str(res), kind="error")
            return
        total_f = len(save.get("bodyuser", {}).get(uid, []))
        self.current_fighter_idx = max(0, total_f - 1)
        self.main_win._auto_save()
        self.refresh_data()
        self.main_win._notify("f_notify_cloned_title", "f_notify_cloned_msg", orig_name=orig_name, new_name=new_name.strip())

    def _delete_fighter_action(self):
        save = self.main_win.save_json
        if not save or len(self.fighters_data) <= 1:
            self.main_win._notify("notice", "f_delete_only_one_err", kind="warning")
            return
        uid = modifiers.get_player_uid(save)
        chr_chrs = save.get("soul", {}).get("chr", {}).get("chrs", {}).get(uid, [])
        f_name = chr_chrs[self.current_fighter_idx].get("name", "Luchador") if self.current_fighter_idx < len(chr_chrs) else "Luchador"
        if self.current_fighter_idx < len(chr_chrs) and chr_chrs[self.current_fighter_idx].get("state") == "USE":
            self.main_win._notify("notice", "f_delete_in_use_err", kind="warning")
            return
        confirm = QMessageBox.question(
            self,
            t("f_delete_btn", default="Eliminar"),
            t("f_delete_confirm", name=f_name, default=f"¿Estás seguro de que deseas eliminar permanentemente a '{f_name}'?"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        s_ok, res = modifiers.delete_fighter(save, self.current_fighter_idx)
        if not s_ok:
            self.main_win._notify("error", str(res), kind="error")
            return
        self.current_fighter_idx = max(0, self.current_fighter_idx - 1)
        self.main_win._auto_save()
        self.refresh_data()
        self.main_win._notify("f_notify_deleted_title", "f_notify_deleted_msg", name=f_name)

    def _unlock_freezer_action(self):
        save = self.main_win.save_json
        if not save:
            return
        modifiers.unlock_tutorial_and_waiting_room(save)
        self.main_win._auto_save()
        self.refresh_data()
        self.main_win._notify("f_notify_freezer_unlocked_title", "f_notify_freezer_unlocked_msg")

    def _open_fighter_model_gallery(self):
        from ui_qt.dialogs.fighter_model_gallery import FighterModelGalleryDialog
        cur_model = self.model_cb.currentText() if hasattr(self, "model_cb") else ""
        dlg = FighterModelGalleryDialog(
            self.main_win,
            fighter_idx=self.current_fighter_idx,
            current_model=cur_model,
            on_select_cb=self._on_gallery_model_selected
        )
        if dlg.exec():
            self._update_fighter_model_preview()

    def _on_gallery_model_selected(self, full_opt, code):
        if hasattr(self, "model_cb"):
            self.model_cb.blockSignals(True)
            for i in range(self.model_cb.count()):
                d = self.model_cb.itemData(i)
                if d == code or code in self.model_cb.itemText(i):
                    self.model_cb.setCurrentIndex(i)
                    break
            self.model_cb.blockSignals(False)
        self._update_fighter_model_preview()

    def _refresh_deathbag_db_status(self):
        if not hasattr(self, "f_bag_db_status_lbl"):
            return
        st = modifiers.get_deathbag_masters_status(save_path=getattr(self.main_win, "save_path", None))
        if not st.get("exists"):
            self.f_bag_db_status_lbl.setText(t("db_mod_status_missing", default="❌ Archivo masters.db no encontrado."))
            self.f_bag_db_status_lbl.setStyleSheet(f"color: {FG_MUTED};")
        elif st.get("is_modded"):
            min_b = st.get("min_bag", 60)
            vip_b = st.get("vip_bonus", 10)
            self.f_bag_db_status_lbl.setText(
                t("db_mod_status_active", base=min_b, total=min_b + vip_b, default=f"✔️ Mod Activo: Base {min_b} slots (Total con Pase: {min_b + vip_b})")
            )
            self.f_bag_db_status_lbl.setStyleSheet(f"color: {ACCENT_GREEN}; font-weight: bold;")
        else:
            self.f_bag_db_status_lbl.setText(
                t("db_mod_status_vanilla", default="⚪ Estado Vanilla (20 slots base)")
            )
            self.f_bag_db_status_lbl.setStyleSheet(f"color: {FG_MUTED};")

    def _expand_deathbag_masters_action(self):
        target, ok = QInputDialog.getInt(
            self,
            t("db_expand_title", default="Expandir Capacidad masters.db"),
            t("db_expand_prompt", default="Nueva capacidad base (30 - 100 ranuras):"),
            60,
            30,
            100
        )
        if not ok:
            return
        try:
            res = modifiers.expand_deathbag_capacity(target_capacity=target, vip_bonus=10, save_path=getattr(self.main_win, "save_path", None))
            self._refresh_deathbag_db_status()
            self._load_fighter_details(self.current_fighter_idx)
            QMessageBox.information(
                self,
                t("db_expand_success_title", default="¡Capacidad Modificada con Éxito!"),
                t("db_expand_success_msg", target=target, vip=target + 10, path=res['db_path'], default=f"Capacidad base configurada a {target} slots ({target + 10} con Pase).\nModificado en: {res['db_path']}")
            )
        except Exception as e:
            QMessageBox.critical(self, t("error", default="Error"), f"masters.db:\n{e}")

    def _restore_deathbag_masters_action(self):
        confirm = QMessageBox.question(
            self,
            t("db_restore_title", default="Restaurar masters.db"),
            t("db_restore_prompt", default="¿Deseas restaurar la capacidad original de 20 slots en masters.db?"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        try:
            res = modifiers.restore_deathbag_capacity(save_path=getattr(self.main_win, "save_path", None))
            self._refresh_deathbag_db_status()
            self._load_fighter_details(self.current_fighter_idx)
            QMessageBox.information(
                self,
                t("db_restore_success_title", default="Restaurado"),
                t("db_restore_success_msg", path=res['db_path'], default=f"masters.db restaurado a capacidad original.\nRuta: {res['db_path']}")
            )
        except Exception as e:
            QMessageBox.critical(self, t("error", default="Error"), f"masters.db:\n{e}")

    def _apply_decal_preset_action(self):
        save = self.main_win.save_json
        if not save:
            return
        key = self.decal_preset_cb.currentData()
        if not key:
            sel = self.decal_preset_cb.currentText()
            key = "tengoku_climber"
            if "KAMAS" in sel: key = "kamas_god"
            elif "Melee" in sel: key = "melee_melter"
            elif "TDM" in sel: key = "tdm_defense"

        name, count = modifiers.apply_decal_preset_to_inventory(save, preset_key=key, count=5)
        self.main_win._auto_save()
        self.refresh_data()
        self.main_win.update_hud()
        self.main_win._notify("f_notify_decal_preset_title", "f_notify_decal_preset_msg", count=count, name=name)

    def _equip_decal_preset_action(self):
        save = self.main_win.save_json
        if not save:
            return
        fighters = modifiers.get_all_fighters_info(save)
        idx = self.current_fighter_idx
        if idx >= len(fighters):
            return
        f_info = fighters[idx]
        cid = f_info.get("cid")
        key = self.decal_preset_cb.currentData()
        if not key:
            sel = self.decal_preset_cb.currentText()
            key = "tengoku_climber"
            if "KAMAS" in sel: key = "kamas_god"
            elif "Melee" in sel: key = "melee_melter"
            elif "TDM" in sel: key = "tdm_defense"

        name, count = modifiers.equip_decal_preset_on_fighter(save, cid, preset_key=key)
        self.main_win._auto_save()
        self.refresh_data()
        self.main_win.update_hud()
        self.main_win._notify("mb_preset_equipped_title", "mb_preset_equipped_msg", count=count, name=name, fighter=f_info.get('name', 'Luchador'))

    def refresh_translations(self):
        self.box_freezer.setTitle(t("f_freezer_title", default="Congelador de Luchadores"))
        self.btn_up.setText(t("f_move_up", default="Subir"))
        self.btn_down.setText(t("f_move_down", default="Bajar"))
        self.btn_create.setText(t("f_create_btn", default="Crear"))
        self.btn_clone.setText(t("f_clone_btn", default="Clonar"))
        self.btn_delete.setText(t("f_delete_btn", default="Eliminar"))
        self.btn_unlock_freezer.setText(t("f_tut_btn", default="🎓 Desbloquear Congelador (Omitir Tutorial)"))
        self.tree.setHeaderLabels([t("f_col_name", default="Nombre"), t("f_col_num", default="Ranura"), t("f_col_lvl", default="Nivel"), t("f_col_state", default="Estado")])
        self.box_sheet.setTitle(t("f_tech_sheet", default="Ficha Técnica del Luchador"))
        self.box_id.setTitle(t("f_id_config", default="Identidad y Configuración"))

        self.lbl_name.setText(t("f_lbl_name", default="Nombre:"))
        self.lbl_class.setText(t("f_lbl_class", default="Clase:"))
        self.lbl_grade.setText(t("f_lbl_grade", default="Grado:"))
        self.lbl_lvl.setText(t("bp_lvl_lbl", default="Level:"))
        self.lbl_hp_cur.setText(t("f_lbl_hp_cur", default="HP Actual:"))
        self.lbl_mingo.setText(t("f_mingo_bonus_lbl", default="Bolsa MINGO:"))
        self.lbl_model.setText(t("f_lbl_model", default="Modelo / Apariencia:"))
        self.btn_gallery.setText(t("f_create_gallery_btn", default="🖼️ Galería 3D"))

        cur_cls = self.class_cb.currentData()
        self.class_cb.blockSignals(True)
        self.class_cb.clear()
        for k in self._class_keys:
            self.class_cb.addItem(t(f"cls_opt_{k.lower()}", default=k), k)
        idx_cls = self.class_cb.findData(cur_cls)
        if idx_cls >= 0:
            self.class_cb.setCurrentIndex(idx_cls)
        self.class_cb.blockSignals(False)

        cur_model_data = self.model_cb.currentData()
        self._populate_model_combobox()
        idx_m = self.model_cb.findData(cur_model_data)
        if idx_m >= 0:
            self.model_cb.blockSignals(True)
            self.model_cb.setCurrentIndex(idx_m)
            self.model_cb.blockSignals(False)

        self.box_stats.setTitle(t("f_base_stats_box", default="Atributos Base (Puntos Asignados)"))
        for key, tr_key, def_name, _, _ in getattr(self, "_stat_keys_def", []):
            if key in self.stat_labels:
                self.stat_labels[key].setText(t(tr_key, default=def_name))

        self.box_decals.setTitle(t("f_equipped_decals_box", default="Calcomanías Equipadas (Ranuras 1 - 8)"))
        self.btn_save_f.setText(t("f_apply_btn", default="💾 Aplicar Cambios a este Luchador"))
        self.btn_revive.setText(t("f_revive_btn", default="❤️ Revivir / Rescatar Luchadores"))
        self.btn_max_stats.setText(t("f_max_stats_btn", default="⚡ Maximizar Luchador (Lvl 247)"))

        self.box_db_bag.setTitle(t("db_mod_box_title", default="🔧 Mod del Motor: Capacidad de Bolsa en masters.db"))
        self.btn_expand_bag.setText(t("db_expand_btn", default="🚀 Expandir Capacidad en masters.db"))
        self.btn_restore_bag.setText(t("db_restore_btn", default="🔄 Restaurar Original"))

        self.box_presets.setTitle(t("f_presets_box", default="🏆 Presets Tácticos de Calcomanías"))
        self.lbl_preset.setText(t("f_preset_lbl", default="Preset:"))
        self.btn_equip_preset.setText(t("f_preset_btn", default="👑 Equipar Preset al Luchador Actual"))
        self.btn_apply_preset.setText(t("f_inject_preset_btn", default="🎒 Añadir Calcomanías al Almacén"))

        cur_preset_key = self.decal_preset_cb.currentData()
        self.decal_preset_cb.blockSignals(True)
        self.decal_preset_cb.clear()
        self.decal_preset_cb.addItem(t("preset_tengoku_climber", default="Tengoku God Climber (Pisos 51F - 350F+)"), "tengoku_climber")
        self.decal_preset_cb.addItem(t("preset_kamas_god", default="Tirador KAMAS Definitivo (Full Shooter Meta)"), "kamas_god")
        self.decal_preset_cb.addItem(t("preset_melee_melter", default="Destructor Melee (Mayal / Machete / Katana)"), "melee_melter")
        self.decal_preset_cb.addItem(t("preset_tdm_defense", default="Pesadilla de Defensa TDM (Invulnerable Tank)"), "tdm_defense")
        idx_p = self.decal_preset_cb.findData(cur_preset_key)
        if idx_p >= 0:
            self.decal_preset_cb.setCurrentIndex(idx_p)
        self.decal_preset_cb.blockSignals(False)

        self.refresh_data()
