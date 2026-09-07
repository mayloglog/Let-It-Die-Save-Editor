# -*- coding: utf-8 -*-
"""
Armor Set Viewer Dialog for LET IT DIE Save Editor (PySide6 Edition).
Exact layout, logic, and behavior parity with GitHub Tkinter original.
"""

import os
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPixmap, QColor
from PySide6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout,
    QGroupBox, QLabel, QPushButton, QComboBox,
    QScrollArea, QFrame, QMessageBox
)

import modifiers
from save_io import save_to_file
import i18n
from i18n import t
from ui_qt.theme import (
    get_pixmap, find_equipment_art,
    ACCENT_GOLD, ACCENT_CYAN, ACCENT_BLUE, FG_MUTED, FG_MAIN, BG_CARD, BG_PANEL
)


class ArmorSetViewerDialog(QDialog):
    """Interactive visual dialog to inspect complete armor sets by tier like on letitdie.wiki.gg"""
    def __init__(self, parent, save_json, armor_sets, initial_set_id=None, initial_tier=1):
        super().__init__(parent)
        self.parent_app = parent
        self.main_win = getattr(parent, "main_win", parent)
        self.save_json = save_json
        self.armor_sets = armor_sets or []

        self.setWindowTitle(t("dialog_armor_viewer_title"))
        self.resize(1120, 780)
        self.setMinimumSize(1000, 680)

        self.set_index = 0
        if initial_set_id:
            for idx, s in enumerate(self.armor_sets):
                if s.get("id") == initial_set_id:
                    self.set_index = idx
                    break

        self.current_tier_num = max(1, min(initial_tier, 4))
        self.piece_cards = {}

        self._build_ui()
        self.display_current_set()

    def _build_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(10, 8, 10, 8)
        root_layout.setSpacing(6)

        # 1. Header Toolbar
        header = QFrame()
        header.setObjectName("TopFrame")
        header.setStyleSheet("background-color: #151824; border-radius: 6px; padding: 4px 10px;")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(6, 4, 6, 4)

        lbl_set = QLabel(t("dialog_armor_set_label"))
        lbl_set.setStyleSheet(f"color: {ACCENT_GOLD}; font-weight: bold; font-size: 10pt;")
        h_layout.addWidget(lbl_set)

        self.cb_sets = QComboBox()
        self.cb_sets.setMinimumWidth(380)
        for s in self.armor_sets:
            title = i18n.get_entity_display_title(s)
            faction = s.get("faction", "")
            self.cb_sets.addItem(f"{title} • {faction}")
        if self.armor_sets and 0 <= self.set_index < len(self.armor_sets):
            self.cb_sets.setCurrentIndex(self.set_index)
        self.cb_sets.currentIndexChanged.connect(self._on_set_changed)
        h_layout.addWidget(self.cb_sets)

        self.faction_lbl = QLabel("")
        self.faction_lbl.setStyleSheet(f"color: {ACCENT_CYAN}; font-weight: bold; font-size: 9.5pt; margin-left: 10px;")
        h_layout.addWidget(self.faction_lbl)
        h_layout.addStretch()

        root_layout.addWidget(header)

        # 2. Tier Selection Tabs
        tier_bar = QFrame()
        tier_bar.setStyleSheet("background-color: #1c2030; border: 1px solid #252b40; border-radius: 6px; padding: 2px 8px;")
        t_layout = QHBoxLayout(tier_bar)
        t_layout.setContentsMargins(6, 3, 6, 3)

        lbl_evo = QLabel(t("dialog_evolution_label"))
        lbl_evo.setStyleSheet(f"color: {FG_MAIN}; font-weight: bold; font-size: 9pt;")
        t_layout.addWidget(lbl_evo)

        self.tier_buttons = []
        for tnum in [1, 2, 3, 4]:
            btn = QPushButton(f"Tier {tnum}")
            btn.setFixedWidth(85)
            btn.clicked.connect(lambda checked=False, tn=tnum: self.switch_tier(tn))
            t_layout.addWidget(btn)
            self.tier_buttons.append((tnum, btn))

        t_layout.addStretch()
        root_layout.addWidget(tier_bar)

        # 3. Main Split Content Area
        content_h = QHBoxLayout()
        content_h.setSpacing(8)

        # Left Side: Character Armor Model Showcase
        left_box = QGroupBox(t("dialog_preview_title"))
        left_box.setFixedWidth(315)
        left_v = QVBoxLayout(left_box)
        left_v.setContentsMargins(6, 6, 6, 6)
        left_v.setSpacing(4)

        self.model_lbl = QLabel()
        self.model_lbl.setFixedSize(295, 450)
        self.model_lbl.setStyleSheet("background-color: #0d0f17; border: 1px solid #252b40; border-radius: 6px;")
        self.model_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.model_lbl.setWordWrap(True)
        left_v.addWidget(self.model_lbl)

        self.model_title_lbl = QLabel("")
        self.model_title_lbl.setStyleSheet(f"color: {ACCENT_GOLD}; font-size: 10.5pt; font-weight: bold;")
        self.model_title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.model_title_lbl.setWordWrap(True)
        left_v.addWidget(self.model_title_lbl)
        left_v.addStretch()

        content_h.addWidget(left_box)

        # Right Side: Piece & Weapon Stat Cards in ScrollArea
        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_scroll.setFrameShape(QFrame.Shape.NoFrame)
        right_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        right_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        right_container = QWidget()
        right_v = QVBoxLayout(right_container)
        right_v.setContentsMargins(0, 0, 2, 0)
        right_v.setSpacing(6)

        slot_defs = [
            ("head", t("asv_head"), "🪖"),
            ("body", t("asv_body"), "👕"),
            ("legs", t("asv_legs"), "👖"),
            ("weapon", t("asv_weapon"), "⚔️")
        ]

        card_qss = """
            QGroupBox {
                background-color: #1c2030;
                border: 1px solid #252b40;
                border-radius: 6px;
                margin-top: 10px;
                padding: 4px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 8px;
                padding: 0 4px;
                color: #f5b041;
                font-size: 8.5pt;
                font-weight: bold;
            }
        """

        for slot_key, slot_title, emoji in slot_defs:
            card_lf = QGroupBox(slot_title)
            card_lf.setStyleSheet(card_qss)
            card_layout = QHBoxLayout(card_lf)
            card_layout.setContentsMargins(8, 4, 8, 4)
            card_layout.setSpacing(8)

            # Icon
            icon_lbl = QLabel()
            icon_lbl.setFixedSize(54, 54)
            icon_lbl.setStyleSheet("background-color: #151824; border: 1px solid #2f3650; border-radius: 6px;")
            icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            card_layout.addWidget(icon_lbl)

            # Info Column
            info_col = QVBoxLayout()
            info_col.setSpacing(1)

            title_lbl = QLabel("---")
            title_lbl.setStyleSheet(f"color: {FG_MAIN}; font-weight: bold; font-size: 9.5pt;")
            info_col.addWidget(title_lbl)

            def_dur_lbl = QLabel("")
            def_dur_lbl.setStyleSheet(f"color: {ACCENT_CYAN}; font-weight: bold; font-size: 8.5pt;")
            info_col.addWidget(def_dur_lbl)

            res_lbl = QLabel("")
            res_lbl.setStyleSheet(f"color: {FG_MUTED}; font-size: 8pt;")
            info_col.addWidget(res_lbl)

            status_lbl = QLabel("")
            status_lbl.setStyleSheet("font-size: 8.5pt; font-weight: bold;")
            info_col.addWidget(status_lbl)

            card_layout.addLayout(info_col, stretch=1)

            # Right column: card artwork + action buttons
            action_col = QVBoxLayout()
            action_col.setSpacing(3)
            action_col.setAlignment(Qt.AlignmentFlag.AlignRight)

            card_img_lbl = QLabel()
            card_img_lbl.setFixedSize(180, 80)
            card_img_lbl.setStyleSheet("background-color: #151824; border: 1px solid #252b40; border-radius: 4px;")
            card_img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            action_col.addWidget(card_img_lbl)

            btns_row = QHBoxLayout()
            btns_row.setSpacing(4)
            btns_row.setContentsMargins(0, 0, 0, 0)

            btn_unlock = QPushButton(t("asv_btn_unlock_plus4"))
            btn_unlock.setFixedWidth(100)
            btn_unlock.setFixedHeight(26)
            btn_unlock.setStyleSheet(
                "QPushButton {"
                "   background-color: #00bcd4; color: #000000; font-weight: bold;"
                "   border: 1px solid #00acc1; border-radius: 4px; font-size: 8pt; padding: 2px;"
                "}"
                "QPushButton:hover { background-color: #26c6da; }"
            )
            btn_unlock.clicked.connect(lambda checked=False, sk=slot_key: self._on_card_unlock_clicked(sk))
            btns_row.addWidget(btn_unlock)

            btn_add = QPushButton(t("asv_btn_add_storage"))
            btn_add.setFixedWidth(76)
            btn_add.setFixedHeight(26)
            btn_add.setStyleSheet(
                "QPushButton {"
                "   background-color: #1e2538; color: #e0e0e0; font-weight: normal;"
                "   border: 1px solid #2a324b; border-radius: 4px; font-size: 8pt; padding: 2px;"
                "}"
                "QPushButton:hover { background-color: #27314a; }"
            )
            btn_add.clicked.connect(lambda checked=False, sk=slot_key: self._on_card_add_clicked(sk))
            btns_row.addWidget(btn_add)

            action_col.addLayout(btns_row)
            card_layout.addLayout(action_col)

            right_v.addWidget(card_lf)

            self.piece_cards[slot_key] = {
                "frame": card_lf,
                "icon_lbl": icon_lbl,
                "title_lbl": title_lbl,
                "def_dur_lbl": def_dur_lbl,
                "res_lbl": res_lbl,
                "status_lbl": status_lbl,
                "card_img_lbl": card_img_lbl,
                "btn_unlock": btn_unlock,
                "btn_add": btn_add,
                "current_pid": None
            }

        right_scroll.setWidget(right_container)
        content_h.addWidget(right_scroll)
        root_layout.addLayout(content_h)

        # 4. Bottom Global Actions
        bottom_bar = QFrame()
        bottom_bar.setStyleSheet("background-color: #151824; border-radius: 6px; padding: 4px 10px;")
        b_layout = QHBoxLayout(bottom_bar)
        b_layout.setContentsMargins(6, 4, 6, 4)

        lbl_lvl = QLabel(t("asv_lbl_level"))
        lbl_lvl.setStyleSheet(f"color: {ACCENT_GOLD}; font-weight: bold; font-size: 9pt;")
        b_layout.addWidget(lbl_lvl)

        self.cb_glvl = QComboBox()
        self.cb_glvl.addItems(["+19 (Uncapped)", "+24 (Max Uncapped)", "+4 (Base)"])
        self.cb_glvl.setCurrentIndex(0)
        self.cb_glvl.setFixedWidth(160)
        b_layout.addWidget(self.cb_glvl)

        self.btn_unlock_set = QPushButton(t("asv_btn_unlock_set"))
        self.btn_unlock_set.setStyleSheet(
            "QPushButton {"
            "   background-color: #00bcd4; color: #000000; font-size: 9pt; font-weight: bold;"
            "   border: 1px solid #00acc1; border-radius: 4px; padding: 5px 14px;"
            "}"
            "QPushButton:hover { background-color: #26c6da; }"
        )
        self.btn_unlock_set.clicked.connect(self.unlock_current_tier_set)
        b_layout.addWidget(self.btn_unlock_set)

        self.btn_add_set = QPushButton(t("asv_btn_add_set"))
        self.btn_add_set.setStyleSheet(
            "QPushButton {"
            "   background-color: #1e2538; color: #e0e0e0; font-size: 9pt;"
            "   border: 1px solid #2a324b; border-radius: 4px; padding: 5px 14px;"
            "}"
            "QPushButton:hover { background-color: #27314a; }"
        )
        self.btn_add_set.clicked.connect(self.add_current_tier_set_storage)
        b_layout.addWidget(self.btn_add_set)

        b_layout.addStretch()

        btn_close = QPushButton(t("btn_close"))
        btn_close.setStyleSheet(
            "QPushButton {"
            "   background-color: #1e2538; color: #e0e0e0; font-size: 9pt;"
            "   border: 1px solid #2a324b; border-radius: 4px; padding: 5px 16px;"
            "}"
            "QPushButton:hover { background-color: #27314a; }"
        )
        btn_close.clicked.connect(self.accept)
        b_layout.addWidget(btn_close)

        root_layout.addWidget(bottom_bar)

    def _get_selected_gear_level(self):
        val = self.cb_glvl.currentText()
        if "+24" in val:
            return 25, 24
        elif "+4" in val:
            return 5, 4
        return 20, 19

    def _on_set_changed(self, idx):
        if 0 <= idx < len(self.armor_sets):
            self.set_index = idx
            self.display_current_set()

    def switch_tier(self, tier_num):
        self.current_tier_num = tier_num
        self.display_current_set()

    def display_current_set(self):
        if not self.armor_sets or not (0 <= self.set_index < len(self.armor_sets)):
            return

        s_obj = self.armor_sets[self.set_index]
        s_name = i18n.get_set_name(s_obj)
        faction_val = s_obj.get("faction", "")
        self.faction_lbl.setText(t("asv_faction_fmt", faction=faction_val))

        # Check available tiers via tier_num
        tiers = s_obj.get("tiers", [])
        avail_tiers = {}
        for item in tiers:
            tnum = item.get("tier_num")
            if tnum is not None:
                avail_tiers[int(tnum)] = item

        # Highlight active tier button and enable/disable
        for tnum, btn in self.tier_buttons:
            if tnum in avail_tiers:
                btn.setEnabled(True)
                if tnum == self.current_tier_num:
                    btn.setStyleSheet(
                        "QPushButton {"
                        "   background-color: #00bcd4; color: #000000; font-weight: bold;"
                        "   border: 1px solid #00acc1; border-radius: 4px; padding: 4px 10px;"
                        "}"
                    )
                else:
                    btn.setStyleSheet(
                        "QPushButton {"
                        "   background-color: #1e2538; color: #b0bec5; font-weight: normal;"
                        "   border: 1px solid #2a324b; border-radius: 4px; padding: 4px 10px;"
                        "}"
                        "QPushButton:hover { background-color: #27314a; }"
                    )
            else:
                btn.setEnabled(False)
                btn.setStyleSheet(
                    "QPushButton {"
                    "   background-color: #121520; color: #505870;"
                    "   border: 1px solid #1a1e2a; border-radius: 4px; padding: 4px 10px;"
                    "}"
                )

        # Find current tier object
        t_obj = avail_tiers.get(self.current_tier_num)
        if not t_obj and tiers:
            t_obj = tiers[-1]
            self.current_tier_num = t_obj.get("tier_num", 1)

        if not t_obj:
            return

        # 1. Update character set model
        render_path = t_obj.get("set_render")
        if render_path:
            pix = get_pixmap(render_path, (295, 450), preserve_aspect=True)
            if pix and not pix.isNull():
                self.model_lbl.setPixmap(pix)
            else:
                self.model_lbl.clear()
                self.model_lbl.setText(t("asv_loading"))
        else:
            self.model_lbl.clear()
            self.model_lbl.setText(t("asv_render_progress"))

        t_name = self._get_tier_name(t_obj)
        self.model_title_lbl.setText(f"{s_name} ({t_name})")

        # 2. Update piece cards
        counts = modifiers.get_equipment_inventory_counts(self.save_json) if self.save_json else ({}, {})
        storage_map, bag_map = counts
        pr_list = self.save_json.get("soul", {}).get("partresearch", {}).get("user", []) if self.save_json else []
        forge_levels = {}
        for r in pr_list:
            if isinstance(r, dict) and r.get("research_type") == "FINISHED":
                ptid = r.get("ptid")
                lvl = r.get("lvl", 0)
                if lvl > forge_levels.get(ptid, 0):
                    forge_levels[ptid] = lvl

        for slot_key in ["head", "body", "legs", "weapon"]:
            p = t_obj.get(slot_key)
            card_ui = self.piece_cards[slot_key]

            if not p:
                card_ui["frame"].setVisible(False)
                continue

            card_ui["frame"].setVisible(True)
            card_ui["current_pid"] = p["id"]

            # Title
            name_str = i18n.get_entity_display_title(p)
            card_ui["title_lbl"].setText(f"{name_str}  [{p['id']}]")

            if slot_key == "weapon":
                atk_base = p.get("atk", 0)
                atk_plus4 = p.get("atk_plus4", int(atk_base * 1.5))
                dur = p.get("durability", 1400)
                card_ui["def_dur_lbl"].setText(t("dialog_atk_base", atk=atk_base, atk4=atk_plus4, dur=dur))
                card_ui["def_dur_lbl"].setStyleSheet(f"color: {ACCENT_GOLD}; font-weight: bold; font-size: 8.5pt;")
                card_ui["res_lbl"].setText(t("dialog_weapon_paired"))
                card_ui["btn_unlock"].setText(t("asv_btn_unlock_weapon"))
            else:
                def_base = p.get("def", 0)
                def_plus4 = p.get("def_plus4", 0)
                dur = p.get("durability", 0)
                card_ui["def_dur_lbl"].setText(t("dialog_def_base", def_b=def_base, def4=def_plus4, dur=dur))
                card_ui["def_dur_lbl"].setStyleSheet(f"color: {ACCENT_CYAN}; font-weight: bold; font-size: 8.5pt;")

                res = p.get("resistances", {})
                res_txt = t("asv_resistances_fmt",
                    slash=res.get('slash', 0),
                    blunt=res.get('blunt', 0),
                    pierce=res.get('pierce', 0),
                    fire=res.get('fire', 0),
                    elec=res.get('electric', 0),
                    poison=res.get('poison', 0)
                )
                card_ui["res_lbl"].setText(res_txt)
                card_ui["btn_unlock"].setText(t("asv_btn_unlock_piece"))

            # Status
            f_lvl = forge_levels.get(p["id"], 0)
            st_cnt = storage_map.get(p["id"], 0)
            bg_cnt = bag_map.get(p["id"], 0)

            if f_lvl >= 20:
                f_txt = t("asv_shop_unlocked_uncapped")
            elif f_lvl >= 5:
                f_txt = t("asv_shop_unlocked_plus4")
            elif f_lvl > 0:
                f_txt = t("asv_shop_level_fmt", lvl=f_lvl - 1)
            else:
                f_txt = t("asv_shop_locked")

            unit_str = t('inv_unit_str')
            st_txt = f"📦 {t('inv_tab_storage')}: {st_cnt} {unit_str}" if st_cnt > 0 else f"📦 {t('inv_tab_storage')}: 0 {unit_str}"
            bg_txt = f"🎒 {t('inv_tab_bag')}: {bg_cnt} {unit_str}" if bg_cnt > 0 else ""
            f_color = ACCENT_GOLD if f_lvl >= 5 else ACCENT_BLUE if f_lvl > 0 else FG_MUTED

            full_stat = f"{f_txt}  •  {st_txt}" + (f"  •  {bg_txt}" if bg_txt else "")
            card_ui["status_lbl"].setText(full_stat)
            card_ui["status_lbl"].setStyleSheet(f"color: {f_color}; font-size: 8.5pt;")

            # Icon
            icon_rel = p.get("icon")
            target_ico = icon_rel or find_equipment_art(p["id"], as_card=False)
            icon_pix = get_pixmap(target_ico, (54, 54), preserve_aspect=True)
            if icon_pix and not icon_pix.isNull():
                card_ui["icon_lbl"].setPixmap(icon_pix)
            else:
                card_ui["icon_lbl"].clear()
                card_ui["icon_lbl"].setText(t("icon_placeholder"))

            # Card image
            target_card = p.get("card") or find_equipment_art(p["id"], as_card=True)
            card_pix = get_pixmap(target_card, (180, 80), preserve_aspect=True)
            if card_pix and not card_pix.isNull():
                card_ui["card_img_lbl"].setVisible(True)
                card_ui["card_img_lbl"].setPixmap(card_pix)
            else:
                card_ui["card_img_lbl"].setVisible(False)

    def _on_card_unlock_clicked(self, slot_key):
        card = self.piece_cards.get(slot_key)
        if card and card.get("current_pid"):
            self.unlock_single_piece(card["current_pid"])

    def _on_card_add_clicked(self, slot_key):
        card = self.piece_cards.get(slot_key)
        if card and card.get("current_pid"):
            self.add_single_piece_storage(card["current_pid"])

    def _auto_save_and_sync(self):
        if self.save_json is not self.main_win.save_json:
            raise ValueError("The dialog no longer refers to the active save; reopen it.")
        self.main_win._auto_save()
        self.main_win.update_hud()
        self.main_win.refresh_all_views()

    def unlock_single_piece(self, pid):
        if not self.save_json or not pid:
            return
        int_lvl, plus_lvl = self._get_selected_gear_level()
        modifiers.unlock_single_blueprint(self.save_json, pid, level=int_lvl, unlock_next_tier=True, auto_unlock_ancestors=True)
        modifiers.add_equipment_to_storage(self.save_json, pid, count=1, lvl=int_lvl, dur=50000)
        self._auto_save_and_sync()
        self.display_current_set()

        title = t("asv_notify_unlocked_title")
        msg = t("asv_notify_unlocked_msg", pid=pid, plus_lvl=plus_lvl)
        QMessageBox.information(self, title, msg)

    def add_single_piece_storage(self, pid):
        if not self.save_json or not pid:
            return
        int_lvl, plus_lvl = self._get_selected_gear_level()
        modifiers.add_equipment_to_storage(self.save_json, pid, count=1, lvl=int_lvl, dur=50000)
        self._auto_save_and_sync()
        self.display_current_set()

        title = t("asv_notify_added_title")
        msg = t("asv_notify_added_msg", pid=pid, plus_lvl=plus_lvl)
        QMessageBox.information(self, title, msg)

    def unlock_current_tier_set(self):
        if not self.save_json or not self.armor_sets:
            return
        s_obj = self.armor_sets[self.set_index]
        t_obj = next((t for t in s_obj.get("tiers", []) if t.get("tier_num") == self.current_tier_num), None)
        if not t_obj:
            return

        int_lvl, plus_lvl = self._get_selected_gear_level()
        unlocked = []

        # 1. Unlock all preceding tiers in this armor set (Tier 1, Tier 2, Tier 3, etc.)
        for tier_item in s_obj.get("tiers", []):
            if tier_item.get("tier_num", 0) < self.current_tier_num:
                for slot in ["head", "body", "legs", "weapon"]:
                    prev_p = tier_item.get(slot)
                    if prev_p and prev_p.get("id"):
                        modifiers.unlock_single_blueprint(
                            self.save_json,
                            prev_p["id"],
                            level=4,
                            unlock_next_tier=True,
                            auto_unlock_ancestors=True
                        )

        # 2. Unlock the current tier pieces + weapon and deliver to storage
        for slot in ["head", "body", "legs", "weapon"]:
            p = t_obj.get(slot)
            if p and p.get("id"):
                pid = p["id"]
                modifiers.unlock_single_blueprint(
                    self.save_json,
                    pid,
                    level=int_lvl,
                    unlock_next_tier=True,
                    auto_unlock_ancestors=True
                )
                modifiers.add_equipment_to_storage(self.save_json, pid, count=1, lvl=int_lvl, dur=50000)
                unlocked.append(i18n.get_entity_display_title(p))

        self._auto_save_and_sync()
        self.display_current_set()

        title = t("asv_notify_set_unlocked_title")
        s_name = i18n.get_set_name(s_obj)
        t_name = self._get_tier_name(t_obj)
        header_msg = t("asv_notify_tier_unlocked_msg", set_name=s_name, tier_name=t_name, plus_lvl=plus_lvl)
        msg = header_msg + "\n\n" + "\n".join([f"• {u}" for u in unlocked])
        QMessageBox.information(self, title, msg)

    def add_current_tier_set_storage(self):
        if not self.save_json or not self.armor_sets:
            return
        s_obj = self.armor_sets[self.set_index]
        t_obj = next((t for t in s_obj.get("tiers", []) if t.get("tier_num") == self.current_tier_num), None)
        if not t_obj:
            return

        int_lvl, plus_lvl = self._get_selected_gear_level()
        added = []
        for slot in ["head", "body", "legs", "weapon"]:
            p = t_obj.get(slot)
            if p and p.get("id"):
                modifiers.add_equipment_to_storage(self.save_json, p["id"], count=1, lvl=int_lvl, dur=50000)
                added.append(i18n.get_entity_display_title(p))

        self._auto_save_and_sync()
        self.display_current_set()

        title = t("asv_notify_set_added_title")
        s_name = i18n.get_set_name(s_obj)
        t_name = self._get_tier_name(t_obj)
        header_msg = t("asv_notify_tier_added_msg", set_name=s_name, tier_name=t_name, plus_lvl=plus_lvl)
        msg = header_msg + "\n\n" + "\n".join([f"• {a}" for a in added])
        QMessageBox.information(self, title, msg)

    def _get_tier_name(self, t_obj):
        if not t_obj:
            return ""
        cur_lang = i18n.get_language()
        return t_obj.get(f'tier_name_{cur_lang}') or (t_obj.get('tier_name') if cur_lang == "es" else t_obj.get('tier_name_en', t_obj.get('tier_name', "")))
