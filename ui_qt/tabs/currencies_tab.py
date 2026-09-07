# -*- coding: utf-8 -*-
"""
Currencies & VIP Tab for LET IT DIE Save Editor (PySide6 Edition).
Exact layout, colors, and behavior parity with Cyberpunk Dark design.
"""

import re
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QGroupBox, QLabel, QLineEdit, QPushButton, QComboBox,
    QScrollArea, QFrame, QMessageBox
)

import modifiers
import i18n
from i18n import t
from ui_qt.theme import get_pixmap, ACCENT_GOLD, ACCENT_PINK, ACCENT_CYAN, ACCENT_RED, ACCENT_GREEN, FG_MUTED


class CurrenciesTab(QWidget):
    def __init__(self, main_win):
        super().__init__()
        self.main_win = main_win
        self._build_ui()

    def _build_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(10, 10, 10, 10)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        root_layout.addWidget(scroll)

        container = QWidget()
        scroll.setWidget(container)

        grid = QGridLayout(container)
        grid.setSpacing(12)
        grid.setContentsMargins(8, 8, 8, 8)

        # -------------------------------------------------------------
        # Card 1 (Top-Left): Currencies
        # -------------------------------------------------------------
        self.box_curr = QGroupBox(t("curr_box_title"))
        curr_layout = QVBoxLayout(self.box_curr)
        curr_layout.setSpacing(8)

        self.curr_entries = {}
        self.curr_labels = {}
        items = [
            ("dm", t("dm_lbl"), "dm", ACCENT_PINK),
            ("kc", t("kc_lbl"), "kc", ACCENT_GOLD),
            ("spl", t("spl_lbl"), "spl", ACCENT_CYAN),
            ("bl", t("bl_lbl"), "bloodnium", ACCENT_RED),
            ("re", t("re_lbl"), "re_point", ACCENT_GREEN),
        ]

        for key, lbl_text, icon_name, color in items:
            row = QHBoxLayout()
            ico_lbl = QLabel()
            pix = get_pixmap(icon_name, (20, 20))
            if pix:
                ico_lbl.setPixmap(pix)
            row.addWidget(ico_lbl)

            lbl = QLabel(f" {lbl_text}")
            lbl.setStyleSheet(f"color: {color}; font-weight: bold;")
            row.addWidget(lbl)
            self.curr_labels[key] = lbl
            row.addStretch()

            ent = QLineEdit("0")
            ent.setFixedWidth(130)
            ent.setAlignment(Qt.AlignmentFlag.AlignRight)
            row.addWidget(ent)
            self.curr_entries[key] = ent
            curr_layout.addLayout(row)

        self.btn_max_curr = QPushButton(t("max_all_curr_btn"))
        self.btn_max_curr.setProperty("accent", "true")
        self.btn_max_curr.clicked.connect(self.max_all_currencies)
        curr_layout.addWidget(self.btn_max_curr)

        grid.addWidget(self.box_curr, 0, 0)

        # -------------------------------------------------------------
        # Card 2 (Top-Right): Waiting Room Upgrades
        # -------------------------------------------------------------
        self.box_wr = QGroupBox(t("wr_box_title"))
        wr_layout = QVBoxLayout(self.box_wr)
        wr_layout.setSpacing(8)

        upgrades = [
            ("safe", t("bank_lvl_lbl")),
            ("tank", t("tank_lvl_lbl")),
            ("rank", t("player_rank_lbl")),
        ]
        self.wr_entries = {}
        self.wr_labels = {}
        for key, lbl_t in upgrades:
            r = QHBoxLayout()
            lbl = QLabel(lbl_t)
            r.addWidget(lbl)
            self.wr_labels[key] = lbl
            r.addStretch()

            ent = QLineEdit("99" if key != "rank" else "100")
            ent.setFixedWidth(70)
            ent.setAlignment(Qt.AlignmentFlag.AlignCenter)
            r.addWidget(ent)
            self.wr_entries[key] = ent
            wr_layout.addLayout(r)

        wr_btn_f = QHBoxLayout()
        self.btn_apply_wr = QPushButton(t("apply_wr_btn"))
        self.btn_apply_wr.setProperty("accent", "true")
        self.btn_apply_wr.clicked.connect(self._apply_waiting_room_facilities)
        wr_btn_f.addWidget(self.btn_apply_wr)

        self.btn_max_wr = QPushButton(t("max_wr_btn"))
        self.btn_max_wr.clicked.connect(self._max_waiting_room_facilities)
        wr_btn_f.addWidget(self.btn_max_wr)
        wr_layout.addLayout(wr_btn_f)

        self.lbl_wr_hint = QLabel(t("wr_hint"))
        self.lbl_wr_hint.setWordWrap(True)
        self.lbl_wr_hint.setStyleSheet(f"color: {FG_MUTED}; font-size: 8pt;")
        wr_layout.addWidget(self.lbl_wr_hint)
        wr_layout.addStretch()

        grid.addWidget(self.box_wr, 0, 1)

        # -------------------------------------------------------------
        # Card 3 (Bottom-Left): VIP Royal Express
        # -------------------------------------------------------------
        self.box_vip = QGroupBox(t("vip_box_title"))
        vip_layout = QVBoxLayout(self.box_vip)
        vip_layout.setSpacing(6)

        self.vip_status_lbl = QLabel(t("vip_inactive"))
        self.vip_status_lbl.setStyleSheet(f"color: {ACCENT_RED}; font-weight: bold; font-size: 10pt;")
        vip_layout.addWidget(self.vip_status_lbl)

        self.lbl_vip_note = QLabel(t("vip_safe_note"))
        self.lbl_vip_note.setWordWrap(True)
        self.lbl_vip_note.setStyleSheet(f"color: {FG_MUTED}; font-size: 8pt;")
        vip_layout.addWidget(self.lbl_vip_note)

        vip_ctrl = QHBoxLayout()
        self.lbl_vip_days = QLabel(t("vip_days_lbl"))
        vip_ctrl.addWidget(self.lbl_vip_days)

        self.cb_vip_days = QComboBox()
        self.cb_vip_days.addItems(["90", "60", "30", "15", "7", "1"])
        self.cb_vip_days.setCurrentText("30")
        self.cb_vip_days.setFixedWidth(65)
        vip_ctrl.addWidget(self.cb_vip_days)

        self.btn_activate_vip = QPushButton(t("activate_vip_btn"))
        self.btn_activate_vip.setProperty("accent", "true")
        self.btn_activate_vip.clicked.connect(self._activate_custom_vip)
        vip_ctrl.addWidget(self.btn_activate_vip)

        self.btn_deactivate_vip = QPushButton(t("deactivate_vip_btn"))
        self.btn_deactivate_vip.clicked.connect(self._deactivate_vip_action)
        vip_ctrl.addWidget(self.btn_deactivate_vip)
        vip_layout.addLayout(vip_ctrl)

        vip_quick = QHBoxLayout()
        self.btn_vip_30 = QPushButton(t("vip_30d_btn"))
        self.btn_vip_30.setProperty("accent", "true")
        self.btn_vip_30.clicked.connect(lambda: self._set_vip_entry_and_act(30, passes=99))
        vip_quick.addWidget(self.btn_vip_30)

        self.btn_vip_1 = QPushButton(t("vip_1d_btn"))
        self.btn_vip_1.clicked.connect(lambda: self._set_vip_entry_and_act(1, passes=99))
        vip_quick.addWidget(self.btn_vip_1)
        vip_layout.addLayout(vip_quick)

        self.btn_stock_passes = QPushButton(t("vip_stock_passes"))
        self.btn_stock_passes.clicked.connect(lambda: self._set_vip_entry_and_act(30, passes=99))
        vip_layout.addWidget(self.btn_stock_passes)

        grid.addWidget(self.box_vip, 1, 0)

        # -------------------------------------------------------------
        # Card 4 (Bottom-Right): Account Perks & Death Bag Expansion
        # -------------------------------------------------------------
        self.box_perks = QGroupBox(t("account_perks_title"))
        perks_layout = QVBoxLayout(self.box_perks)
        perks_layout.setSpacing(6)

        self.lbl_bag_title = QLabel(t("tw_bag_title"))
        self.lbl_bag_title.setStyleSheet(f"color: {ACCENT_GOLD}; font-weight: bold; font-size: 9pt;")
        perks_layout.addWidget(self.lbl_bag_title)

        bag_f = QHBoxLayout()
        self.lbl_bag_cap = QLabel(t("tw_bag_cap_lbl"))
        bag_f.addWidget(self.lbl_bag_cap)
        self.cb_bag = QComboBox()
        self.cb_bag.addItems(["20", "25", "30", "35", "40", "45", "50", "60", "70"])
        self.cb_bag.setCurrentText("50")
        self.cb_bag.setFixedWidth(70)
        bag_f.addWidget(self.cb_bag)

        self.btn_expand_bag = QPushButton(t("tw_bag_btn"))
        self.btn_expand_bag.setProperty("accent", "true")
        self.btn_expand_bag.clicked.connect(self._expand_bag_action)
        bag_f.addWidget(self.btn_expand_bag)
        perks_layout.addLayout(bag_f)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        sep.setStyleSheet("background-color: #252b40; margin: 4px 0;")
        perks_layout.addWidget(sep)

        self.lbl_cont_title = QLabel(t("tw_cont_title"))
        self.lbl_cont_title.setStyleSheet(f"color: {ACCENT_GOLD}; font-weight: bold; font-size: 9pt;")
        perks_layout.addWidget(self.lbl_cont_title)

        cont_f = QHBoxLayout()
        self.lbl_cont = QLabel(t("tw_cont_lbl"))
        cont_f.addWidget(self.lbl_cont)
        self.ent_free_cont = QLineEdit("999")
        self.ent_free_cont.setFixedWidth(70)
        self.ent_free_cont.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cont_f.addWidget(self.ent_free_cont)

        self.btn_set_cont = QPushButton(t("tw_cont_btn"))
        self.btn_set_cont.setProperty("accent", "true")
        self.btn_set_cont.clicked.connect(self._set_continues_action)
        cont_f.addWidget(self.btn_set_cont)
        perks_layout.addLayout(cont_f)

        perks_layout.addStretch()
        grid.addWidget(self.box_perks, 1, 1)

        # -------------------------------------------------------------
        # Row 2 (Footer): Account Profile & Metadata
        # -------------------------------------------------------------
        self.box_acct = QGroupBox(t("account_summary_title"))
        acct_layout = QHBoxLayout(self.box_acct)
        acct_layout.setContentsMargins(10, 6, 10, 6)

        self.acct_uid_lbl = QLabel("UID: --- | Steam ID: ---")
        self.acct_uid_lbl.setStyleSheet(f"color: {ACCENT_CYAN}; font-weight: bold; font-size: 9pt;")
        acct_layout.addWidget(self.acct_uid_lbl)

        self.acct_playtime_lbl = QLabel(t("acct_hours_placeholder"))
        self.acct_playtime_lbl.setStyleSheet(f"color: {FG_MUTED}; font-size: 9pt;")
        acct_layout.addWidget(self.acct_playtime_lbl)

        self.acct_streak_lbl = QLabel(t("acct_streak_placeholder"))
        self.acct_streak_lbl.setStyleSheet(f"color: {ACCENT_GOLD}; font-size: 9pt;")
        acct_layout.addWidget(self.acct_streak_lbl)

        acct_layout.addStretch()

        self.btn_max_streak = QPushButton(t("max_streak_btn"))
        self.btn_max_streak.clicked.connect(self._max_login_streak_action)
        acct_layout.addWidget(self.btn_max_streak)

        grid.addWidget(self.box_acct, 2, 0, 1, 2)

        # Grid column weights
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)

    def refresh_data(self):
        """Refreshes all fields from the active save."""
        save = self.main_win.save_json
        if not save:
            return

        currencies = modifiers.get_player_currencies(save)
        self.curr_entries["dm"].setText(f"{currencies.get('dm', 0):,}")
        self.curr_entries["kc"].setText(f"{currencies.get('kc', 0):,}")
        self.curr_entries["spl"].setText(f"{currencies.get('spl', 0):,}")
        self.curr_entries["bl"].setText(f"{currencies.get('bloodnium', 0):,}")
        self.curr_entries["re"].setText(f"{currencies.get('re_points', 0):,}")

        # Waiting Room
        base_up = modifiers.get_waiting_room_info(save)
        self.wr_entries["safe"].setText(str(base_up.get("bank_level", 10)))
        self.wr_entries["tank"].setText(str(base_up.get("tank_level", 10)))
        self.wr_entries["rank"].setText(str(base_up.get("rank", 100)))

        # VIP status
        vip_info = modifiers.get_vip_status(save)
        is_active = vip_info.get("active", False)
        days = vip_info.get("days_left", 0)
        exp_date = vip_info.get("expires_at", "")
        if is_active:
            self.vip_status_lbl.setText(t("vip_active", days=days, date=exp_date))
            self.vip_status_lbl.setStyleSheet(f"color: {ACCENT_GREEN}; font-weight: bold; font-size: 10pt;")
        else:
            self.vip_status_lbl.setText(t("vip_inactive"))
            self.vip_status_lbl.setStyleSheet(f"color: {ACCENT_RED}; font-weight: bold; font-size: 10pt;")

        # Card 4: Account Perks
        f_list = modifiers.get_all_fighters_info(save)
        cur_f_idx = getattr(getattr(self.main_win, "tab_fighters", None), "current_fighter_idx", 0)
        if f_list and 0 <= cur_f_idx < len(f_list):
            bag_size = save.get("soul", {}).get("bag_slot", 50)
            self.cb_bag.setCurrentText(str(bag_size))

        soul_data = save.get("soul", {})
        free_cont = soul_data.get("free_continue_count", 999)
        self.ent_free_cont.setText(str(free_cont))

        # Footer Row: Account Profile & Metadata
        acct = modifiers.get_account_overview(save)
        self.acct_uid_lbl.setText(f"UID: {acct.get('uid', '---')} | Steam ID: {acct.get('steam_id', '---')}")
        self.acct_streak_lbl.setText(t("hud_streak_fmt", days=acct.get('login_streak', 1)))

        pl = modifiers.get_tower_playlog(save)
        self.acct_playtime_lbl.setText(t("hud_playtime_fmt", hours=pl.get('playtime_hours', 0.0)))

    def _parse_curr(self, text, default=0):
        if text is None:
            return default
        s = str(text).replace(",", "").replace(".", "").replace(" ", "").strip()
        try:
            return max(0, int(s))
        except ValueError:
            return default

    def apply_currencies(self, checked=False, *, persist=True):
        save = self.main_win.save_json
        if not save:
            return
        dm = self._parse_curr(self.curr_entries["dm"].text())
        kc = self._parse_curr(self.curr_entries["kc"].text())
        spl = self._parse_curr(self.curr_entries["spl"].text())
        bl = self._parse_curr(self.curr_entries["bl"].text())
        re_pt = self._parse_curr(self.curr_entries["re"].text())

        modifiers.set_currencies(save, dm=dm, kc=kc, spl=spl, bloodnium=bl, re_points=re_pt)
        if persist:
            self.main_win._auto_save()
        self.main_win.update_hud()

    def max_all_currencies(self):
        save = self.main_win.save_json
        if not save:
            return
        modifiers.max_all_currencies(save)
        self.main_win._auto_save()
        self.refresh_data()
        self.main_win.update_hud()
        self.main_win._notify("curr_notify_max_curr_title", "curr_notify_max_curr_msg")

    def _apply_waiting_room_facilities(self):
        save = self.main_win.save_json
        if not save:
            return
        try:
            safe = int(self.wr_entries["safe"].text())
            tank = int(self.wr_entries["tank"].text())
            rank = int(self.wr_entries["rank"].text())
        except ValueError:
            return
        pts = modifiers.get_rank_points_for_rank(rank)
        modifiers.upgrade_waiting_room(save, bank_level=safe, tank_level=tank)
        modifiers.set_player_rank(save, rank=rank)
        self.main_win._auto_save()
        self.main_win.update_hud()
        self.main_win._notify("curr_notify_facilities_updated_title", "curr_notify_facilities_updated_msg", b_lvl=safe, t_lvl=tank, p_rnk=rank, pts=pts)

    def _max_waiting_room_facilities(self):
        save = self.main_win.save_json
        if not save:
            return
        pts = modifiers.get_rank_points_for_rank(100)
        modifiers.upgrade_waiting_room(save, bank_level=99, tank_level=99)
        modifiers.set_player_rank(save, rank=100)
        self.main_win._auto_save()
        self.refresh_data()
        self.main_win.update_hud()
        self.main_win._notify("curr_notify_facilities_max_title", "curr_notify_facilities_max_msg", pts=pts)

    def _activate_custom_vip(self, passes=99):
        save = self.main_win.save_json
        if not save:
            return
        try:
            days = min(90, max(1, int(self.cb_vip_days.currentText())))
        except ValueError:
            days = 30
        self.cb_vip_days.setCurrentText(str(days))
        modifiers.set_vip_pass(save, days=days, passes=passes, oneday_passes=99)
        self.main_win._auto_save()
        self.main_win.refresh_all_views()
        self.main_win.update_hud()
        self.main_win._notify("curr_notify_vip_act_title", "curr_notify_vip_act_msg", days=days, passes=passes)

    def _set_vip_entry_and_act(self, days, passes=99):
        self.cb_vip_days.setCurrentText(str(days))
        self._activate_custom_vip(passes=passes)

    def _deactivate_vip_action(self):
        save = self.main_win.save_json
        if not save:
            return
        modifiers.deactivate_vip_pass(save)
        self.main_win._auto_save()
        self.main_win.refresh_all_views()
        self.main_win.update_hud()
        self.main_win._notify("curr_notify_vip_deact_title", "curr_notify_vip_deact_msg")

    def _expand_bag_action(self):
        save = self.main_win.save_json
        if not save:
            return
        try:
            slots = int(self.cb_bag.currentText())
        except ValueError:
            slots = 50
        cur_f_idx = getattr(getattr(self.main_win, "tab_fighters", None), "current_fighter_idx", 0)
        modifiers.expand_death_bag(save, slots=slots, fighter_index=cur_f_idx)
        self.main_win._auto_save()
        self.main_win.refresh_all_views()
        self.main_win.update_hud()
        self.main_win._notify("tw_notify_bag_expanded_title", "tw_notify_bag_expanded_msg", slots=slots)

    def _set_continues_action(self):
        save = self.main_win.save_json
        if not save:
            return
        try:
            cnt = int(self.ent_free_cont.text())
        except ValueError:
            cnt = 999
        modifiers.set_free_continues(save, count=cnt)
        self.main_win._auto_save()
        self.main_win.refresh_all_views()
        self.main_win._notify("tw_notify_continues_title", "tw_notify_continues_msg", cnt=cnt)

    def _max_login_streak_action(self):
        save = self.main_win.save_json
        if not save:
            return
        modifiers.max_login_streak(save, streak=365)
        self.main_win._auto_save()
        self.main_win.refresh_all_views()
        self.main_win._notify("curr_notify_streak_title", "curr_notify_streak_msg")

    def refresh_translations(self):
        self.box_curr.setTitle(t("curr_box_title"))
        self.btn_max_curr.setText(t("max_all_curr_btn"))
        curr_keys = [("dm", "dm_lbl"), ("kc", "kc_lbl"), ("spl", "spl_lbl"), ("bl", "bl_lbl"), ("re", "re_lbl")]
        for k, t_k in curr_keys:
            if k in getattr(self, "curr_labels", {}):
                self.curr_labels[k].setText(f" {t(t_k)}")

        self.box_wr.setTitle(t("wr_box_title"))
        self.btn_apply_wr.setText(t("apply_wr_btn"))
        self.btn_max_wr.setText(t("max_wr_btn"))
        self.lbl_wr_hint.setText(t("wr_hint"))
        wr_keys = [("safe", "bank_lvl_lbl"), ("tank", "tank_lvl_lbl"), ("rank", "player_rank_lbl")]
        for k, t_k in wr_keys:
            if k in getattr(self, "wr_labels", {}):
                self.wr_labels[k].setText(t(t_k))

        self.box_vip.setTitle(t("vip_box_title"))
        self.lbl_vip_note.setText(t("vip_safe_note"))
        self.lbl_vip_days.setText(t("vip_days_lbl"))
        self.btn_activate_vip.setText(t("activate_vip_btn"))
        self.btn_deactivate_vip.setText(t("deactivate_vip_btn"))
        self.btn_vip_30.setText(t("vip_30d_btn"))
        self.btn_vip_1.setText(t("vip_1d_btn"))
        self.btn_stock_passes.setText(t("vip_stock_passes"))

        self.box_perks.setTitle(t("account_perks_title"))
        self.lbl_bag_title.setText(t("tw_bag_title"))
        self.lbl_bag_cap.setText(t("tw_bag_cap_lbl"))
        self.btn_expand_bag.setText(t("tw_bag_btn"))
        self.lbl_cont_title.setText(t("tw_cont_title"))
        self.lbl_cont.setText(t("tw_cont_lbl"))
        self.btn_set_cont.setText(t("tw_cont_btn"))

        self.box_acct.setTitle(t("account_summary_title"))
        self.btn_max_streak.setText(t("max_streak_btn"))

        self.refresh_data()
