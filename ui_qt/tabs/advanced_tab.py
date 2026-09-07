# -*- coding: utf-8 -*-
"""
Advanced & Save Slots Tab for LET IT DIE Save Editor (PySide6 Edition).
Exact 1:1 logic and behavioral parity with Tkinter implementation.
"""

import os
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QGroupBox, QLabel, QPushButton, QLineEdit, QProgressBar,
    QTabWidget, QScrollArea, QFrame, QMessageBox, QFileDialog
)

import save_io
import modifiers
import i18n
from i18n import t
import core.save_slots as save_slots
from ui_qt.theme import (
    ACCENT_GOLD, ACCENT_CYAN, ACCENT_GREEN, ACCENT_RED,
    FG_MUTED, FG_MAIN, BG_CARD, BG_PANEL
)


class AdvancedTab(QWidget):
    def __init__(self, main_win):
        super().__init__()
        self.main_win = main_win
        self.slot_cards = []
        self._build_ui()

    def _build_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(8, 8, 8, 8)

        self.sub_notebook = QTabWidget()
        root_layout.addWidget(self.sub_notebook)

        # -------------------------------------------------------------
        # Sub-tab 1: Save Slots Manager
        # -------------------------------------------------------------
        self.tab_slots = QWidget()
        self._build_slots_subtab()
        self.sub_notebook.addTab(self.tab_slots, t("adv_subtab_slots", default="Gestor de 10 Ranuras de Guardado"))

        # -------------------------------------------------------------
        # Sub-tab 2: Advanced Tools & Diagnostics
        # -------------------------------------------------------------
        self.tab_tools = QWidget()
        self._build_tools_subtab()
        self.sub_notebook.addTab(self.tab_tools, t("adv_subtab_tools", default="Herramientas Avanzadas y Diagnóstico"))

    def _build_slots_subtab(self):
        v = QVBoxLayout(self.tab_slots)
        v.setContentsMargins(6, 6, 6, 6)
        v.setSpacing(8)

        # Top Banner: Active Save Profile Summary
        self.banner_frame = QFrame()
        self.banner_frame.setObjectName("HudDashboard")
        self.banner_frame.setStyleSheet("background-color: #1c2030; border: 1px solid #252b40; border-radius: 6px; padding: 8px;")
        banner_v = QVBoxLayout(self.banner_frame)

        top_b = QHBoxLayout()
        self.lbl_banner_title = QLabel(t("slot_active_banner_title", default="PERFIL ACTIVO EN EDICIÓN"))
        self.lbl_banner_title.setStyleSheet(f"color: {ACCENT_GOLD}; font-weight: bold; font-size: 10pt;")
        top_b.addWidget(self.lbl_banner_title)

        self.lbl_banner_path = QLabel("")
        self.lbl_banner_path.setStyleSheet(f"color: {FG_MUTED}; font-size: 8pt;")
        top_b.addWidget(self.lbl_banner_path)
        top_b.addStretch()

        self.btn_rebind = QPushButton("🔄 " + t("rebind_tool_open_btn", default="Re-vincular Cuenta Steam"))
        self.btn_rebind.clicked.connect(self._open_account_rebind)
        top_b.addWidget(self.btn_rebind)
        banner_v.addLayout(top_b)

        self.lbl_banner_info = QLabel(t("slot_loading_profile", default="Cargando perfil..."))
        self.lbl_banner_info.setStyleSheet("font-size: 9pt; color: #ffffff;")
        banner_v.addWidget(self.lbl_banner_info)
        v.addWidget(self.banner_frame)

        # Scroll Area for the 10 Slot Cards (2 columns x 5 rows)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        v.addWidget(scroll)

        slot_container = QWidget()
        scroll.setWidget(slot_container)

        self.slot_grid = QGridLayout(slot_container)
        self.slot_grid.setSpacing(10)

        for slot_num in range(1, 11):
            card = self._create_slot_card(slot_num)
            row = (slot_num - 1) // 2
            col = (slot_num - 1) % 2
            self.slot_grid.addWidget(card, row, col)

    def _create_slot_card(self, slot_num):
        box = QGroupBox(f"Slot {slot_num}")
        card_v = QVBoxLayout(box)
        card_v.setSpacing(5)
        card_v.setContentsMargins(8, 8, 8, 8)

        # Header with custom name edit
        h_row = QHBoxLayout()
        lbl_name = QLabel(t("slot_name_lbl", default="Nombre:"))
        lbl_name.setStyleSheet(f"color: {FG_MUTED}; font-size: 8pt;")
        h_row.addWidget(lbl_name)

        name_entry = QLineEdit()
        name_entry.setPlaceholderText(f"Ranura {slot_num}")
        name_entry.editingFinished.connect(lambda s=slot_num, e=name_entry: self._on_slot_renamed(s, e.text()))
        h_row.addWidget(name_entry)
        card_v.addLayout(h_row)

        # Labels for detailed slot metadata
        lbl_player = QLabel("")
        lbl_player.setStyleSheet(f"font-size: 8.5pt; font-weight: bold; color: {FG_MAIN};")
        card_v.addWidget(lbl_player)

        lbl_fighter = QLabel("")
        lbl_fighter.setStyleSheet(f"font-size: 8pt; color: {ACCENT_CYAN};")
        card_v.addWidget(lbl_fighter)

        lbl_stats = QLabel("")
        lbl_stats.setStyleSheet(f"font-size: 8pt; font-weight: bold; color: {ACCENT_GOLD};")
        card_v.addWidget(lbl_stats)

        lbl_coins = QLabel("")
        lbl_coins.setStyleSheet("font-size: 7.5pt; color: #dcdde1;")
        card_v.addWidget(lbl_coins)

        lbl_session = QLabel(t("slot_empty_lbl", default="[ Ranura Vacía ]"))
        lbl_session.setStyleSheet(f"font-size: 7.5pt; color: {FG_MUTED};")
        card_v.addWidget(lbl_session)

        # Row 1 Buttons: Load & Quick Use Latest Session
        act_row1 = QHBoxLayout()
        btn_load = QPushButton(t("slot_btn_load_active", default="⚡ Cargar en Juego"))
        btn_load.clicked.connect(lambda checked=False, s=slot_num: self._load_slot_action(s))
        act_row1.addWidget(btn_load)

        btn_quick_bak = QPushButton(t("slot_btn_use_latest_session", default="🕒 Restaurar Sesión"))
        btn_quick_bak.setProperty("accent", "true")
        btn_quick_bak.clicked.connect(lambda checked=False, s=slot_num: self._quick_use_latest_backup_action(s))
        act_row1.addWidget(btn_quick_bak)
        card_v.addLayout(act_row1)

        # Row 2 Buttons: Save Here, Backups Dialog, Import .sav, Clear
        act_row2 = QHBoxLayout()
        btn_save = QPushButton(t("slot_btn_save_here", default="💾 Guardar Aquí"))
        btn_save.clicked.connect(lambda checked=False, s=slot_num: self._save_to_slot_action(s))
        act_row2.addWidget(btn_save)

        btn_backups = QPushButton("🛡️ " + t("slot_backups_btn", default="Backups"))
        btn_backups.clicked.connect(lambda checked=False, s=slot_num: self._open_slot_backups(s))
        act_row2.addWidget(btn_backups)

        btn_import = QPushButton("📥")
        btn_import.setToolTip(t("slot_btn_import_file", default="Importar archivo .sav a esta Ranura"))
        btn_import.setFixedWidth(30)
        btn_import.clicked.connect(lambda checked=False, s=slot_num: self._import_file_to_slot_action(s))
        act_row2.addWidget(btn_import)

        btn_clear = QPushButton("🗑️")
        btn_clear.setProperty("danger", "true")
        btn_clear.setFixedWidth(30)
        btn_clear.clicked.connect(lambda checked=False, s=slot_num: self._clear_slot_action(s))
        act_row2.addWidget(btn_clear)
        card_v.addLayout(act_row2)

        self.slot_cards.append({
            "slot": slot_num,
            "box": box,
            "lbl_name": lbl_name,
            "name_entry": name_entry,
            "lbl_player": lbl_player,
            "lbl_fighter": lbl_fighter,
            "lbl_stats": lbl_stats,
            "lbl_coins": lbl_coins,
            "lbl_session": lbl_session,
            "btn_load": btn_load,
            "btn_quick_bak": btn_quick_bak,
            "btn_save": btn_save,
            "btn_backups": btn_backups,
            "btn_import": btn_import,
            "btn_clear": btn_clear,
        })
        return box

    def _build_tools_subtab(self):
        v = QVBoxLayout(self.tab_tools)
        v.setContentsMargins(10, 10, 10, 10)
        v.setSpacing(12)

        # Box 1: Save Sanitization & Engine Fixes
        self.box_fix = QGroupBox(t("adv_repairs_title", default="Reparaciones del Motor y Partida"))
        fix_v = QVBoxLayout(self.box_fix)
        fix_v.setSpacing(8)

        self.btn_fix_tdm = QPushButton(t("adv_repair_tdm_btn", default="🛠️ Reparar Cargas Infinitas TDM y Estructuras Corruptas"))
        self.btn_fix_tdm.setProperty("accent", "true")
        self.btn_fix_tdm.clicked.connect(self._fix_tdm_structures_action)
        fix_v.addWidget(self.btn_fix_tdm)

        self.btn_sanitize_freezer = QPushButton(t("adv_repair_fighters_btn", default="❄️ Reparar Congelador y Desincronizaciones Mingo Head"))
        self.btn_sanitize_freezer.clicked.connect(self._sanitize_freezer_action)
        fix_v.addWidget(self.btn_sanitize_freezer)
        v.addWidget(self.box_fix)

        # Box 2: JSON Direct Export/Import
        self.box_json = QGroupBox(t("bak_tools_title", default="Herramientas de Desarrollador (JSON)"))
        json_v = QVBoxLayout(self.box_json)
        json_v.setSpacing(8)

        json_btns = QHBoxLayout()
        self.btn_export_json = QPushButton(t("bak_export_json", default="📤 Exportar save_decompressed.json"))
        self.btn_export_json.clicked.connect(self.main_win.export_json)
        json_btns.addWidget(self.btn_export_json)

        self.btn_import_json = QPushButton(t("bak_import_json", default="📥 Importar save_decompressed.json"))
        self.btn_import_json.setProperty("danger", "true")
        self.btn_import_json.clicked.connect(self.main_win.import_json)
        json_btns.addWidget(self.btn_import_json)
        json_v.addLayout(json_btns)
        v.addWidget(self.box_json)

        # Box 3: CDN Assets & Cache Manager
        self.box_assets = QGroupBox(t("asset_box_title", default="🌐 Gestor de Recursos CDN y Caché Local"))
        asset_v = QVBoxLayout(self.box_assets)
        asset_v.setSpacing(6)

        self.lbl_asset_desc = QLabel(t("asset_box_desc", default="Descarga bajo demanda de iconos, calcomanías y cartas 2D mediante jsDelivr CDN sin congelar la interfaz."))
        self.lbl_asset_desc.setStyleSheet(f"color: {FG_MUTED}; font-size: 8pt;")
        self.lbl_asset_desc.setWordWrap(True)
        asset_v.addWidget(self.lbl_asset_desc)

        self.asset_stats_lbl = QLabel("...")
        self.asset_stats_lbl.setStyleSheet(f"color: {ACCENT_GOLD}; font-weight: bold; font-size: 9pt;")
        asset_v.addWidget(self.asset_stats_lbl)

        self.asset_pbar = QProgressBar()
        self.asset_pbar.setTextVisible(True)
        self.asset_pbar.setFixedHeight(16)
        self.asset_pbar.setValue(0)
        asset_v.addWidget(self.asset_pbar)

        self.asset_pbar_lbl = QLabel("")
        self.asset_pbar_lbl.setStyleSheet(f"color: {FG_MUTED}; font-size: 8pt;")
        asset_v.addWidget(self.asset_pbar_lbl)

        btn_assets_f = QHBoxLayout()
        self.asset_dl_btn = QPushButton(t("asset_download_all_btn", default="📥 Descargar Catálogo Completo HD (Offline)"))
        self.asset_dl_btn.setProperty("accent", "true")
        self.asset_dl_btn.clicked.connect(self._download_all_cdn_assets)
        btn_assets_f.addWidget(self.asset_dl_btn)

        self.asset_clear_btn = QPushButton(t("asset_clear_cache_btn", default="🗑️ Limpiar Caché"))
        self.asset_clear_btn.clicked.connect(self._clear_cdn_cache)
        btn_assets_f.addWidget(self.asset_clear_btn)

        self.asset_reload_btn = QPushButton("🔄 " + t("reload", default="Recargar"))
        self.asset_reload_btn.clicked.connect(self.update_cache_stats)
        btn_assets_f.addWidget(self.asset_reload_btn)

        asset_v.addLayout(btn_assets_f)
        v.addWidget(self.box_assets)

        self.update_cache_stats()

        v.addStretch()

    def refresh_data(self):
        """Updates slot banner and 10 slot cards matching Tkinter logic."""
        save = self.main_win.save_json
        cur_slot = self.main_win.get_current_active_slot_num()

        if save:
            meta = save_slots.extract_save_metadata(save)
            f_name = meta.get("fighter_name", "Fighter")
            f_class = meta.get("fighter_class", "BAL")
            f_grade = meta.get("fighter_grade", 1)
            f_lvl = meta.get("fighter_lvl", 1)
            dm = meta.get("death_metals", meta.get("dm", 0))
            kc = meta.get("kill_coins", meta.get("kc", 0))
            spl = meta.get("splithium", meta.get("spl", 0))
            bl = meta.get("bloodnium", meta.get("bl", 0))
            flr = meta.get("max_floor", 1)
            f_info = t("slot_lbl_fighter_info", name=f_name, clazz=f_class, grade=f_grade, lvl=f_lvl)
            flr_info = t("slot_lbl_floor", floor=flr)
            coins_info = t("slot_lbl_coins", kc=kc, dm=dm, spl=spl, bl=bl)
            self.lbl_banner_info.setText(
                f"🥋 {f_info} | 🗼 {flr_info} | {coins_info}"
            )
            self.lbl_banner_path.setText(f"[Ranura Activa: #{cur_slot}]" if cur_slot else "")
        else:
            self.lbl_banner_info.setText(t("no_save_detected", default="No se ha detectado ninguna partida."))
            self.lbl_banner_path.setText("")

        # Refresh all 10 slots
        all_info = save_slots.get_all_slots(force_refresh=True)
        slots_by_num = {s.get("slot_num"): s for s in all_info} if isinstance(all_info, list) else (all_info or {})

        for c in self.slot_cards:
            s_num = c["slot"]
            slot_data = slots_by_num.get(s_num, {})
            c_name = slot_data.get("custom_name") or ""

            c["name_entry"].blockSignals(True)
            c["name_entry"].setText(c_name if c_name else "")
            c["name_entry"].blockSignals(False)

            is_empty = slot_data.get("is_empty", True)
            meta = slot_data.get("meta", {})
            backups_cnt = slot_data.get("backups_count", 0)
            is_active = (cur_slot == s_num)

            if is_empty:
                c["lbl_player"].setText("")
                c["lbl_fighter"].setText("")
                c["lbl_stats"].setText("")
                c["lbl_coins"].setText("")
                c["lbl_session"].setText(t("slot_empty_desc", default="Ranura vacía. Guarda tu partida aquí para crear un perfil nuevo."))
                c["lbl_session"].setStyleSheet(f"font-size: 8pt; color: {FG_MUTED};")
                c["btn_load"].setEnabled(False)
                c["btn_quick_bak"].setVisible(False)
                c["btn_backups"].setText(t("slot_btn_view_backups", count=0, default="🛡️ Backups (0)"))
                c["btn_clear"].setEnabled(False)
            else:
                p_name = meta.get("player_name", "Senpai")
                s_id = meta.get("steam_id", "---")
                f_name = meta.get("fighter_name", "Fighter")
                f_class = meta.get("fighter_class", "BAL")
                f_grade = meta.get("fighter_grade", 1)
                f_lvl = meta.get("fighter_lvl", 1)
                flr = meta.get("max_floor", 1)
                haters = meta.get("haters_killed", 0)
                kc = meta.get("kill_coins", 0)
                dm = meta.get("death_metals", 0)
                spl = meta.get("splithium", 0)
                bl = meta.get("bloodnium", 0)
                hrs = meta.get("playtime_hours", 0)
                last_saved = meta.get("last_saved", "")

                c["lbl_player"].setText(f"👤 {p_name} ({s_id})")
                c["lbl_fighter"].setText(f"🥋 {t('slot_lbl_fighter_info', name=f_name, clazz=f_class, grade=f_grade, lvl=f_lvl)}")
                c["lbl_stats"].setText(f"🗼 {t('slot_lbl_floor', floor=flr)}   ⚔️ {t('slot_lbl_haters', haters=haters)}   ⏱️ {hrs}h")
                c["lbl_coins"].setText(t("slot_lbl_coins", kc=kc, dm=dm, spl=spl, bl=bl))

                latest_bak = slot_data.get("latest_backup")
                latest_meta = (latest_bak.get("meta") or {}) if latest_bak else {}
                if latest_bak and not latest_meta.get("error"):
                    lb_f_name = latest_meta.get("fighter_name", "Fighter")
                    lb_f_lvl = latest_meta.get("fighter_lvl", 1)
                    lb_flr = latest_meta.get("max_floor", 1)
                    lb_date = latest_bak.get("date_str", "")
                    c["lbl_session"].setText(f"🕒 {t('slot_lbl_latest_session_short', date=lb_date, fighter=lb_f_name, lvl=lb_f_lvl, floor=lb_flr)}")
                    c["lbl_session"].setStyleSheet(f"font-size: 7.5pt; color: {ACCENT_CYAN};")
                elif backups_cnt > 0:
                    c["lbl_session"].setText(f"🛡️ {t('slot_lbl_backups_count', count=backups_cnt)} • {last_saved}")
                    c["lbl_session"].setStyleSheet(f"font-size: 7.5pt; color: {FG_MUTED};")
                else:
                    c["lbl_session"].setText(f"🛡️ {t('slot_lbl_backups_count', count=0)}")
                    c["lbl_session"].setStyleSheet(f"font-size: 7.5pt; color: {FG_MUTED};")

                c["btn_load"].setEnabled(True)
                c["btn_quick_bak"].setVisible(backups_cnt > 0)
                c["btn_backups"].setText(t("slot_btn_view_backups", count=backups_cnt, default=f"🛡️ Backups ({backups_cnt})"))
                c["btn_clear"].setEnabled(True)

            if is_active:
                c["box"].setStyleSheet("QGroupBox { border: 2px solid #00d2d3; }")
            else:
                c["box"].setStyleSheet("")

    def _on_slot_renamed(self, slot_num, new_name):
        save_slots.set_slot_custom_name(slot_num, new_name)

    def _load_slot_action(self, slot_num):
        slot_info = save_slots.get_slot_info(slot_num)
        if slot_info.get("is_empty", True):
            self.main_win._notify("notice", "slot_bak_empty", kind="warning")
            return

        if not self.main_win.save_path or not os.path.exists(self.main_win.save_path):
            self.main_win._notify("notice", "mb_load_save_first", kind="warning")
            return

        p_name = slot_info.get("meta", {}).get("player_name", f"Slot {slot_num}")
        ret = QMessageBox.question(
            self,
            t("confirm"),
            t("slot_confirm_load", slot=slot_num, name=p_name, default=f"¿Cargar partida de la Ranura #{slot_num} ({p_name}) a la partida activa del juego?"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if ret != QMessageBox.StandardButton.Yes:
            return

        ok, err_or_data, ver = save_slots.load_slot_to_active(slot_num, self.main_win.save_path)
        if not ok:
            self.main_win._notify("error", str(err_or_data), kind="error")
            return

        self.main_win.set_current_active_slot_num(slot_num)
        self.main_win.load_save(self.main_win.save_path)
        self.refresh_data()
        self.main_win._notify("notice", "slot_loaded_ok", slot=slot_num)

    def _save_to_slot_action(self, slot_num):
        if not self.main_win.save_json:
            self.main_win._notify("notice", "mb_load_save_first", kind="warning")
            return

        slot_info = save_slots.get_slot_info(slot_num)
        if not slot_info.get("is_empty", True):
            ret = QMessageBox.question(
                self,
                t("confirm"),
                t("slot_confirm_save_to_slot", slot=slot_num, default=f"¿Sobrescribir la Ranura #{slot_num} con la partida activa actual?"),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if ret != QMessageBox.StandardButton.Yes:
                return

        try:
            ver = getattr(self.main_win, "version", 2)
            save_slots.save_current_to_slot(self.main_win.save_json, ver, slot_num)
            self.main_win.set_current_active_slot_num(slot_num)
            self.refresh_data()
            self.main_win._notify("notice", "slot_saved_ok", slot=slot_num)
        except Exception as e:
            self.main_win._notify("error", str(e), kind="error")

    def _quick_use_latest_backup_action(self, slot_num):
        slot_info = save_slots.get_slot_info(slot_num)
        latest = slot_info.get("latest_backup")
        if not latest:
            self.main_win._notify("notice", "slot_bak_empty", kind="warning")
            return

        if not self.main_win.save_path or not os.path.exists(self.main_win.save_path):
            self.main_win._notify("notice", "mb_load_save_first", kind="warning")
            return

        meta = latest.get("meta") or {}
        f_name = meta.get("fighter_name", "Fighter")
        flr = meta.get("max_floor", 1)
        d_str = latest.get("date_str", "")

        ret = QMessageBox.question(
            self,
            t("confirm"),
            t("slot_confirm_quick_restore", slot=slot_num, file=latest["filename"], fighter=f_name, floor=flr, date=d_str,
              default=f"¿Restaurar copia rápida '{latest['filename']}' de la Ranura #{slot_num} en la partida activa?"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if ret != QMessageBox.StandardButton.Yes:
            return

        try:
            save_slots.restore_slot_backup(slot_num, latest["filename"], active_target_path=self.main_win.save_path)
            self.main_win.set_current_active_slot_num(slot_num)
            self.main_win.load_save(self.main_win.save_path)
            self.refresh_data()
            self.main_win._notify("notice", "slot_quick_restore_ok", slot=slot_num, file=latest["filename"])
        except Exception as e:
            self.main_win._notify("error", str(e), kind="error")

    def _open_slot_backups(self, slot_num):
        from ui_qt.dialogs.slot_backups_dialog import SlotBackupsDialog

        def on_restored(s_num, active_updated=False):
            if active_updated and self.main_win.save_path:
                self.main_win.set_current_active_slot_num(s_num)
                self.main_win.load_save(self.main_win.save_path)
            self.refresh_data()

        dlg = SlotBackupsDialog(
            self.main_win,
            slot_num=slot_num,
            active_save_path=getattr(self.main_win, "save_path", None),
            on_restored_cb=on_restored
        )
        dlg.exec()

    def _clear_slot_action(self, slot_num):
        ret = QMessageBox.question(
            self,
            t("confirm"),
            t("slot_confirm_clear", slot=slot_num, default=f"¿Estás seguro de que deseas vaciar la Ranura #{slot_num}?"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if ret == QMessageBox.StandardButton.Yes:
            save_slots.clear_slot(slot_num)
            if self.main_win.get_current_active_slot_num() == slot_num:
                self.main_win.set_current_active_slot_num(None)
            self.refresh_data()
            self.main_win._notify("notice", "slot_cleared_ok", slot=slot_num)

    def _import_file_to_slot_action(self, slot_num):
        fn, _ = QFileDialog.getOpenFileName(
            self,
            t("slot_btn_import_file", default="Importar archivo .sav a esta Ranura"),
            "",
            "LET IT DIE Save (*.sav);;All Files (*.*)"
        )
        if not fn:
            return
        try:
            import core.account_rebind as account_rebind
            data, ver = save_io.decompress_save(fn)
            my_ident = account_rebind.detect_active_account_identity(
                active_save_dict=getattr(self.main_win, "save_json", None),
                active_save_path=getattr(self.main_win, "save_path", None)
            )
            my_steam = my_ident.get("steam_id", "")
            foreign_ident = account_rebind.extract_save_identity(data)
            foreign_steam = foreign_ident.get("steam_id", "")

            target_steam = None
            target_name = None

            if my_steam and foreign_steam and my_steam != "---" and foreign_steam != "---" and foreign_steam != my_steam:
                res = QMessageBox.question(
                    self,
                    t("confirm"),
                    t(
                        "slot_import_foreign_confirm",
                        file=os.path.basename(fn),
                        foreign_steam=foreign_steam,
                        foreign_name=foreign_ident.get("player_name", "Senpai"),
                        my_steam=my_steam,
                        my_name=my_ident.get("player_name", "Senpai"),
                        default=f"El archivo pertenece a otra cuenta de Steam ({foreign_steam}). ¿Deseas revincularlo a tu Steam ID ({my_steam})?"
                    ),
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
                )
                if res == QMessageBox.StandardButton.Cancel:
                    return
                if res == QMessageBox.StandardButton.Yes:
                    target_steam = my_steam

            save_slots.import_save_file_to_slot(fn, slot_num, target_steam_id=target_steam, target_player_name=target_name)
            self.refresh_data()
            self.main_win._notify("notice", "slot_import_success", slot=slot_num)
        except Exception as e:
            self.main_win._notify("error", str(e), kind="error")

    def _open_account_rebind(self):
        from ui_qt.dialogs.account_compatibility_dialog import AccountCompatibilityDialog
        dlg = AccountCompatibilityDialog(self.main_win)
        dlg.exec()

    def _fix_tdm_structures_action(self):
        save = self.main_win.save_json
        if not save:
            return
        modifiers.repair_and_sanitize_tdm(save)
        self.main_win._auto_save()
        self.main_win.refresh_all_views()
        self.main_win.set_status(t("adv_tdm_repaired_status", default="Estructuras TDM y defensas sanitizadas con éxito."))
        self.main_win._notify("notice", "adv_tdm_repaired")

    def _sanitize_freezer_action(self):
        save = self.main_win.save_json
        if not save:
            return
        modifiers.sanitize_fighters(save)
        self.main_win._auto_save()
        self.main_win.refresh_all_views()
        self.main_win.set_status(t("adv_freezer_sanitized_status", default="Congelador de luchadores sanitizado con éxito."))
        self.main_win._notify("notice", "adv_fighters_repaired")

    def update_cache_stats(self):
        if hasattr(self.main_win, "asset_manager") and self.main_win.asset_manager:
            stats = self.main_win.asset_manager.get_cache_stats()
            if hasattr(self, "asset_stats_lbl"):
                self.asset_stats_lbl.setText(
                    t("asset_cache_stats", count=stats["count"], size=stats["size_mb"],
                      default=f"📦 Estado del Caché Local: {stats['count']} imágenes ({stats['size_mb']} MB)")
                )

    def _download_all_cdn_assets(self):
        if not hasattr(self.main_win, "asset_manager") or not self.main_win.asset_manager:
            return

        asset_paths = set()
        if hasattr(self.main_win, "icon_map") and isinstance(self.main_win.icon_map, dict):
            for cat in self.main_win.icon_map.values():
                if isinstance(cat, dict):
                    for p in cat.values():
                        if p:
                            asset_paths.add(p)
        if hasattr(self.main_win.asset_manager, "manifest") and self.main_win.asset_manager.manifest:
            for p in self.main_win.asset_manager.manifest.values():
                if p and "/" in p:
                    asset_paths.add(p)

        if not asset_paths:
            self.main_win._notify("notice", "asset_no_downloads")
            return

        total = len(asset_paths)
        self.asset_dl_btn.setEnabled(False)
        self.asset_pbar.setMaximum(total)
        self.asset_pbar.setValue(0)
        self.asset_pbar_lbl.setText(t("asset_downloading", current=0, total=total, default=f"Descargando (0/{total})"))

        def on_progress(cur, tot, f):
            self.main_win._qt_dispatcher.dispatch_signal.emit(
                lambda: self.main_win.tab_advanced._on_asset_progress(cur, tot)
            )

        def on_complete(downloaded, errors):
            self.main_win._qt_dispatcher.dispatch_signal.emit(
                lambda: self.main_win.tab_advanced._on_asset_complete(downloaded, errors)
            )

        self.main_win.asset_manager.download_all_assets_async(
            list(asset_paths),
            progress_callback=on_progress,
            completion_callback=on_complete
        )

    def _on_asset_progress(self, cur, tot):
        if hasattr(self, "asset_pbar"):
            self.asset_pbar.setValue(cur)
        if hasattr(self, "asset_pbar_lbl"):
            self.asset_pbar_lbl.setText(t("asset_downloading", current=cur, total=tot, default=f"Descargando ({cur}/{tot})"))

    def _on_asset_complete(self, downloaded, errors):
        from ui_qt.theme import invalidate_asset_caches
        invalidate_asset_caches()
        if hasattr(self, "asset_dl_btn"):
            self.asset_dl_btn.setEnabled(True)
        self.update_cache_stats()
        if hasattr(self, "asset_pbar_lbl"):
            self.asset_pbar_lbl.setText("")
        self.main_win._notify("notice", "asset_download_done", downloaded=downloaded)

    def _clear_cdn_cache(self):
        if not hasattr(self.main_win, "asset_manager") or not self.main_win.asset_manager:
            return
        ret = QMessageBox.question(
            self,
            t("notice", default="Aviso"),
            t("asset_confirm_clear", default="¿Estás seguro de que deseas vaciar el caché local de imágenes?"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if ret == QMessageBox.StandardButton.Yes:
            self.main_win.asset_manager.clear_cache()
            from ui_qt.theme import invalidate_asset_caches
            invalidate_asset_caches()
            self.update_cache_stats()
            self.main_win._notify("notice", "asset_cache_cleared")

    def refresh_slots_view(self):
        self.refresh_data()

    def refresh_translations(self):
        self.sub_notebook.setTabText(0, t("adv_subtab_slots", default="Gestor de 10 Ranuras de Guardado"))
        self.sub_notebook.setTabText(1, t("adv_subtab_tools", default="Herramientas Avanzadas y Diagnóstico"))
        self.lbl_banner_title.setText(t("slot_active_banner_title", default="PERFIL ACTIVO EN EDICIÓN"))
        self.btn_rebind.setText("🔄 " + t("rebind_tool_open_btn", default="Re-vincular Cuenta Steam"))
        for c in self.slot_cards:
            s_num = c["slot"]
            c["box"].setTitle(f"Slot {s_num}")
            if "lbl_name" in c:
                c["lbl_name"].setText(t("slot_name_lbl", default="Nombre:"))
            if "btn_load" in c:
                c["btn_load"].setText(t("slot_btn_load_active", default="⚡ Cargar en Juego"))
            if "btn_quick_bak" in c:
                c["btn_quick_bak"].setText(t("slot_btn_use_latest_session", default="🕒 Restaurar Sesión"))
            if "btn_save" in c:
                c["btn_save"].setText(t("slot_btn_save_here", default="💾 Guardar Aquí"))

        if hasattr(self, 'box_fix'):
            self.box_fix.setTitle(t("adv_repairs_title", default="Reparaciones del Motor y Partida"))
        self.btn_fix_tdm.setText(t("adv_repair_tdm_btn", default="🛠️ Reparar Cargas Infinitas TDM y Estructuras Corruptas"))
        self.btn_sanitize_freezer.setText(t("adv_repair_fighters_btn", default="❄️ Reparar Congelador y Desincronizaciones Mingo Head"))
        if hasattr(self, 'box_json'):
            self.box_json.setTitle(t("bak_tools_title", default="Herramientas de Desarrollador (JSON)"))
        self.btn_export_json.setText(t("bak_export_json", default="📤 Exportar save_decompressed.json"))
        self.btn_import_json.setText(t("bak_import_json", default="📥 Importar save_decompressed.json"))
        if hasattr(self, 'box_assets'):
            self.box_assets.setTitle(t("asset_box_title", default="🌐 Gestor de Recursos CDN y Caché Local"))
        if hasattr(self, 'lbl_asset_desc'):
            self.lbl_asset_desc.setText(t("asset_box_desc", default="Descarga bajo demanda de iconos, calcomanías y cartas 2D mediante jsDelivr CDN sin congelar la interfaz."))
        if hasattr(self, 'asset_dl_btn'):
            self.asset_dl_btn.setText(t("asset_download_all_btn", default="📥 Descargar Catálogo Completo HD (Offline)"))
        if hasattr(self, 'asset_clear_btn'):
            self.asset_clear_btn.setText(t("asset_clear_cache_btn", default="🗑️ Limpiar Caché"))
        self.update_cache_stats()
        self.refresh_data()
