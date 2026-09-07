# -*- coding: utf-8 -*-
"""
Main Window for LET IT DIE Save Editor (PySide6 Edition).
Exact layout, colors, and behavior parity with Cyberpunk Dark design.
"""

import os
import sys
import json
import time
from PySide6.QtCore import Qt, QTimer, QSize, QObject, Signal, Slot
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QFrame, QLabel, QLineEdit, QPushButton, QComboBox,
    QTabWidget, QStatusBar, QFileDialog, QMessageBox
)

import save_io
from save_io import get_default_save_path, decompress_save, save_to_file
import modifiers
import updater
import i18n
from i18n import t
from core.asset_manager import AssetManager
import core.save_slots as save_slots
from ui_qt.theme import (
    get_pixmap, get_icon, get_fighter_class_icon, load_stylesheet,
    ACCENT_GOLD, ACCENT_CYAN, ACCENT_PINK, ACCENT_RED, ACCENT_GREEN,
    FG_MUTED, FG_MAIN, BG_DARK, BG_PANEL, BG_CARD
)
from ui_qt.tabs import (
    CurrenciesTab, FightersTab, MaterialsTab, DecalsTab,
    BlueprintsTab, MasteryTab, TowerTab, AdvancedTab
)
from ui_qt.dialogs import (
    ArmorSetViewerDialog, SmartInventoryAnalyzerDialog
)

# Paths
if getattr(sys, "frozen", False):
    exe_dir = os.path.dirname(os.path.abspath(sys.executable))
    mei_dir = getattr(sys, "_MEIPASS", exe_dir)
    BASE_DIR = exe_dir if os.path.isdir(os.path.join(exe_dir, "icons")) else mei_dir
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ICONS_DIR = os.path.join(BASE_DIR, "icons")
ICON_ICO_PATH = os.path.join(ICONS_DIR, "app_icon.ico")
ICON_PNG_PATH = os.path.join(ICONS_DIR, "app_icon.png")
ICON_MAP_PATH = os.path.join(BASE_DIR, "icon_map.json")
MATERIALS_DB_PATH = os.path.join(BASE_DIR, "all_materials_db.json")
EQUIPMENT_DB_PATH = os.path.join(BASE_DIR, "all_equipment_encyclopedia.json")
DECALS_DB_PATH = os.path.join(BASE_DIR, "all_decals_encyclopedia.json")
ARMOR_SETS_PATH = os.path.join(BASE_DIR, "armor_sets_encyclopedia.json")
SHROOMS_BEASTS_DB_PATH = os.path.join(BASE_DIR, "all_shrooms_beasts_db.json")


class _QtCallbackDispatcher(QObject):
    dispatch_signal = Signal(object)

    def __init__(self):
        super().__init__()
        self.dispatch_signal.connect(self._run)

    @Slot(object)
    def _run(self, fn):
        try:
            fn()
        except Exception as e:
            print(f"Error executing dispatched Qt callback: {e}")


class SaveEditorMainWindow(QMainWindow):
    def __init__(self, save_path=None):
        super().__init__()
        self._qt_dispatcher = _QtCallbackDispatcher()
        local_v = updater.get_local_version_info().get("version", "4.2.0")
        self.setWindowTitle(f"LET IT DIE (Offline) - Deep Save Editor Pro v{local_v} (Master Cyberpunk Edition)")
        self.resize(1240, 820)
        self.setMinimumSize(960, 600)

        # Window icon
        if os.path.exists(ICON_ICO_PATH):
            self.setWindowIcon(QIcon(ICON_ICO_PATH))
        elif os.path.exists(ICON_PNG_PATH):
            self.setWindowIcon(QIcon(ICON_PNG_PATH))

        self.setStyleSheet(load_stylesheet())

        self.asset_manager = AssetManager()
        self.save_path = save_path or get_default_save_path()
        self.save_json = None
        self._active_slot_num = None

        self._load_all_databases()
        self._build_ui()

        # Always populate catalog views immediately
        self.refresh_all_views()

        # Load save if exists
        if self.save_path and os.path.exists(self.save_path):
            self.load_save(self.save_path)
        else:
            self.set_status(t("no_save_detected", default="No se ha detectado ninguna partida."))

        # Background update check after 2 seconds
        QTimer.singleShot(2000, lambda: updater.check_updates_background(self, silent=True))

    def _load_all_databases(self):
        self.materials_db = []
        self.equipment_db = []
        self.decals_db = []
        self.decals_map = {}
        self.armor_sets = []
        self.armor_set_by_item_id = {}
        self.shrooms_beasts_db = {}
        self.icon_map = {}

        if os.path.exists(ICON_MAP_PATH):
            try:
                with open(ICON_MAP_PATH, "r", encoding="utf-8") as f:
                    self.icon_map = json.load(f)
            except Exception: pass

        if os.path.exists(MATERIALS_DB_PATH):
            try:
                with open(MATERIALS_DB_PATH, "r", encoding="utf-8") as f:
                    self.materials_db = json.load(f)
            except Exception: pass

        if os.path.exists(EQUIPMENT_DB_PATH):
            try:
                with open(EQUIPMENT_DB_PATH, "r", encoding="utf-8") as f:
                    self.equipment_db = json.load(f)
            except Exception: pass

        if os.path.exists(DECALS_DB_PATH):
            try:
                with open(DECALS_DB_PATH, "r", encoding="utf-8") as f:
                    self.decals_db = json.load(f)
                    for d in self.decals_db:
                        self.decals_map[d["id"]] = d
                    for d in self.decals_db:
                        base_id = d["id"][:-2] if d["id"].endswith("_P") else d["id"]
                        if base_id not in self.decals_map:
                            self.decals_map[base_id] = d
                        p_id = f"{base_id}_P"
                        if p_id not in self.decals_map:
                            self.decals_map[p_id] = d
            except Exception: pass

        if os.path.exists(ARMOR_SETS_PATH):
            try:
                with open(ARMOR_SETS_PATH, "r", encoding="utf-8") as f:
                    self.armor_sets = json.load(f)
                    for s in self.armor_sets:
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
            except Exception: pass

        if os.path.exists(SHROOMS_BEASTS_DB_PATH):
            try:
                with open(SHROOMS_BEASTS_DB_PATH, "r", encoding="utf-8") as f:
                    self.shrooms_beasts_db = json.load(f)
            except Exception: pass

    def _build_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 8, 10, 6)
        main_layout.setSpacing(6)

        # =============================================================
        # 1. Top Cyberpunk Save File & Action Bar
        # =============================================================
        top_frame = QFrame()
        top_frame.setObjectName("TopFrame")
        top_layout = QVBoxLayout(top_frame)
        top_layout.setContentsMargins(12, 6, 12, 6)
        top_layout.setSpacing(4)

        # Row 1: Save Path & Save Actions
        row1 = QHBoxLayout()
        self.lbl_file = QLabel(t("save_file", default="Archivo de Guardado:"))
        self.lbl_file.setObjectName("LblFile")
        row1.addWidget(self.lbl_file)

        self.path_entry = QLineEdit()
        if self.save_path:
            self.path_entry.setText(self.save_path)
        row1.addWidget(self.path_entry)

        self.browse_btn = QPushButton(t("browse", default="Examinar..."))
        self.browse_btn.clicked.connect(self.browse_save)
        row1.addWidget(self.browse_btn)

        self.reload_btn = QPushButton(t("reload", default="Recargar"))
        self.reload_btn.clicked.connect(lambda: self.load_save(self.path_entry.text()))
        row1.addWidget(self.reload_btn)

        self.backup_btn = QPushButton(t("backup", default="Crear Respaldo"))
        self.backup_btn.clicked.connect(self.create_manual_backup)
        row1.addWidget(self.backup_btn)

        self.save_btn = QPushButton(t("save_game", default="GUARDAR PARTIDA"))
        self.save_btn.setProperty("accent", "true")
        self.save_btn.clicked.connect(self.save_current)
        row1.addWidget(self.save_btn)
        top_layout.addLayout(row1)

        # Row 2: Quick Tools & Language Switcher
        row2 = QHBoxLayout()
        self.btn_sets_hud = QPushButton(t("armor_sets", default="Conjuntos de Armadura"))
        self.btn_sets_hud.setProperty("accent", "true")
        self.btn_sets_hud.clicked.connect(self._open_armor_set_viewer)
        row2.addWidget(self.btn_sets_hud)

        self.btn_rnd_hud = QPushButton(t("rnd_analyzer", default="Analizador I+D"))
        self.btn_rnd_hud.clicked.connect(self._open_smart_analyzer)
        row2.addWidget(self.btn_rnd_hud)

        self.btn_update_hud = QPushButton(t("updates", default="Actualizaciones"))
        self.btn_update_hud.clicked.connect(self._check_app_updates)
        row2.addWidget(self.btn_update_hud)

        row2.addStretch()

        self.lbl_lang = QLabel(t("lang_label", default="Idioma:"))
        self.lbl_lang.setObjectName("LblLang")
        row2.addWidget(self.lbl_lang)

        # Language Switcher (Español / English / 中文)
        installed_langs = i18n.get_installed_languages()
        self._lang_display_map = {}
        self._lang_code_to_display = {}
        for code, info in installed_langs.items():
            disp_name = info.get("native", info.get("name", code)) if isinstance(info, dict) else str(info)
            self._lang_display_map[disp_name] = code
            self._lang_code_to_display[code] = disp_name

        self.lang_cb = QComboBox()
        for name in self._lang_display_map.keys():
            self.lang_cb.addItem(name)

        cur_lang = i18n.get_language()
        cur_display = self._lang_code_to_display.get(cur_lang, "English")
        idx = self.lang_cb.findText(cur_display)
        if idx >= 0:
            self.lang_cb.setCurrentIndex(idx)
        self.lang_cb.currentIndexChanged.connect(self._on_language_changed)
        row2.addWidget(self.lang_cb)
        top_layout.addLayout(row2)

        main_layout.addWidget(top_frame)

        # =============================================================
        # 2. Player Status Cyberpunk HUD Dashboard
        # =============================================================
        self.dashboard_frame = QFrame()
        self.dashboard_frame.setObjectName("HudDashboard")
        dash_layout = QHBoxLayout(self.dashboard_frame)
        dash_layout.setContentsMargins(12, 6, 12, 6)

        # Left Avatar + Fighter Info
        self.player_avatar_lbl = QLabel()
        self.player_avatar_lbl.setFixedSize(38, 38)
        pix_av = get_pixmap("all-rounder", (38, 38))
        if pix_av:
            self.player_avatar_lbl.setPixmap(pix_av)
        dash_layout.addWidget(self.player_avatar_lbl)

        info_v = QVBoxLayout()
        info_v.setSpacing(1)
        self.player_name_lbl = QLabel(t("hud_fighter_default", default="Luchador #1 (All-Rounder G6)"))
        self.player_name_lbl.setObjectName("PlayerNameLbl")
        info_v.addWidget(self.player_name_lbl)

        self.player_meta_lbl = QLabel(t("hud_meta_default", default="Grado 6 | Nivel 145/145 | HP 10,240 | Bolsa: 30/30"))
        self.player_meta_lbl.setObjectName("PlayerMetaLbl")
        info_v.addWidget(self.player_meta_lbl)
        dash_layout.addLayout(info_v)

        dash_layout.addStretch()

        # Right: 2x3 Grid of Currency Badges
        badge_grid = QGridLayout()
        badge_grid.setSpacing(4)

        def _make_badge(icon_name, initial_text, color):
            w = QWidget()
            h = QHBoxLayout(w)
            h.setContentsMargins(4, 2, 8, 2)
            h.setSpacing(5)
            icon_lbl = QLabel()
            icon_lbl.setFixedSize(18, 18)
            icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            pix = get_pixmap(icon_name, (18, 18), preserve_aspect=True)
            if pix and not pix.isNull():
                icon_lbl.setPixmap(pix)
            h.addWidget(icon_lbl)
            text_lbl = QLabel(initial_text)
            text_lbl.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 8pt;")
            h.addWidget(text_lbl)
            return w, text_lbl

        w_dm, self.hud_dm_lbl = _make_badge("dm", "0 DM", ACCENT_PINK)
        badge_grid.addWidget(w_dm, 0, 0)

        w_kc, self.hud_kc_lbl = _make_badge("kc", "0 KC", ACCENT_GOLD)
        badge_grid.addWidget(w_kc, 0, 1)

        w_spl, self.hud_spl_lbl = _make_badge("spl", "0 SPL", ACCENT_CYAN)
        badge_grid.addWidget(w_spl, 0, 2)

        w_bl, self.hud_bl_lbl = _make_badge("bloodnium", "0 BL", ACCENT_RED)
        badge_grid.addWidget(w_bl, 1, 0)

        w_re, self.hud_re_lbl = _make_badge("re_point", "0 RE", ACCENT_GREEN)
        badge_grid.addWidget(w_re, 1, 1)

        w_bp, self.hud_bp_lbl = _make_badge("blueprint", "0/1370 (0%)", ACCENT_GOLD)
        badge_grid.addWidget(w_bp, 1, 2)

        dash_layout.addLayout(badge_grid)
        main_layout.addWidget(self.dashboard_frame)

        # =============================================================
        # 3. Main Notebook (8 Tabs with Icons & Texts)
        # =============================================================
        self.notebook = QTabWidget()
        self.notebook.setIconSize(QSize(20, 20))
        main_layout.addWidget(self.notebook)

        self.tab_currencies = CurrenciesTab(self)
        self.notebook.addTab(self.tab_currencies, get_icon("dm", (20, 20)), t("tab_currencies", default="Divisas"))

        self.tab_fighters = FightersTab(self)
        self.notebook.addTab(self.tab_fighters, get_icon("all-rounder", (20, 20)), t("tab_fighters", default="Luchadores"))

        self.tab_materials = MaterialsTab(self)
        self.notebook.addTab(self.tab_materials, get_icon("special_steel", (20, 20)), t("tab_materials", default="Materiales"))

        self.tab_decals = DecalsTab(self)
        self.notebook.addTab(self.tab_decals, get_icon("decal_p", (20, 20)), t("tab_decals", default="Calcomanías"))

        self.tab_blueprints = BlueprintsTab(self)
        self.notebook.addTab(self.tab_blueprints, get_icon("blueprint", (20, 20)), t("tab_blueprints", default="Planos"))

        self.tab_mastery = MasteryTab(self)
        self.notebook.addTab(self.tab_mastery, get_icon("weapon", (20, 20)), t("tab_mastery", default="Maestría"))

        self.tab_tower = TowerTab(self)
        self.notebook.addTab(self.tab_tower, get_icon("re_point", (20, 20)), t("tab_tower", default="Torre"))

        self.tab_advanced = AdvancedTab(self)
        self.notebook.addTab(self.tab_advanced, get_icon("reversal_metal", (20, 20)), t("tab_advanced", default="Avanzado"))

        # =============================================================
        # 4. Status Bar
        # =============================================================
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.set_status("Listo.")

    # =================================================================
    # DATA & FILE OPERATIONS
    # =================================================================
    def load_save(self, path):
        if not path or not os.path.exists(path):
            self.set_status(f"Archivo no encontrado: {path}")
            return
        try:
            self.save_json, self.version = decompress_save(path)
            self.save_path = path
            self.path_entry.setText(path)

            # Normalize empty associative arrays ({}) to lists
            modifiers.repair_save_list_structures(self.save_json)

            # Auto-sanitize currencies and facilities against C++ out-of-bounds corruption (> level 99)
            modifiers.repair_and_sanitize_currencies(self.save_json)

            self._active_slot_num = None
            self.get_current_active_slot_num()

            self.refresh_all_views()
            self.update_hud()
            self.refresh_backups_list()
            self.set_status(f"{t('mb_loaded_prefix', default='Partida cargada')}: {os.path.basename(path)}")
        except Exception as e:
            self.set_status(f"Error al cargar partida: {e}")
            self._notify("error", f"No se pudo cargar la partida:\n{e}", kind="error")

    def save_current(self):
        if not self.save_json or not self.save_path:
            self._notify("warn_no_save_title", "warn_no_save_msg", kind="warning")
            return
        try:
            # Sync currencies from entries
            if hasattr(self.tab_currencies, "apply_currencies"):
                self.tab_currencies.apply_currencies(persist=False)

            save_io.save_to_file(self.save_json, self.save_path, version=self.version)
            active_slot = self.get_current_active_slot_num()
            if active_slot:
                save_slots.record_session_backup(active_slot, self.save_json, self.version, force=True)
                self.refresh_backups_list()
                self.refresh_slots_view()

            self.update_hud()
            self.set_status(f"Partida guardada: {os.path.basename(self.save_path)}")
            self._notify("save_success_title", "save_success_msg", file=os.path.basename(self.save_path))
        except PermissionError:
            t_title = t("admin_elevation_perm_denied_title", default="Permiso Denegado")
            t_msg = t("admin_elevation_perm_denied_msg", default="¿Reiniciar como Administrador?")
            ret = QMessageBox.question(self, t_title, t_msg, QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if ret == QMessageBox.StandardButton.Yes:
                import ctypes
                try:
                    target_arg = f'"{self.save_path}"' if self.save_path else ""
                    if getattr(sys, 'frozen', False):
                        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, target_arg, None, 1)
                    else:
                        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{sys.argv[0]}" {target_arg}', None, 1)
                    self.close()
                except Exception as elev_e:
                    self._notify("error", str(elev_e), kind="error")
        except Exception as e:
            self.set_status(f"Error al guardar: {e}")
            self._notify("error", f"Error al guardar partida:\n{e}", kind="error")

    def _auto_save(self):
        if self.save_json and self.save_path:
            try:
                save_to_file(self.save_json, self.save_path, version=self.version)
                active_slot = self.get_current_active_slot_num()
                if active_slot:
                    save_slots.record_session_backup(active_slot, self.save_json, self.version, min_interval_sec=15, force=False)
                    self.refresh_slots_view()
            except Exception as exc:
                self._notify("error", str(exc), kind="error")
                raise

    def browse_save(self):
        f, _ = QFileDialog.getOpenFileName(self, t("save_file"), "", "Save Files (*.sav);;All Files (*.*)")
        if f:
            self.load_save(f)

    def create_manual_backup(self):
        if not self.save_path or not os.path.exists(self.save_path):
            self._notify("notice", "mb_no_save_backup", kind="warning")
            return
        try:
            bak_file = save_io.create_backup(self.save_path)
            self.refresh_backups_list()
            self.set_status(f"{t('mb_backup_created_title')}: {os.path.basename(bak_file)}")
            self._notify("mb_backup_created_title", "mb_backup_created_msg", file=bak_file)
        except Exception as e:
            self._notify("error", str(e), kind="error")

    def refresh_backups_list(self):
        if hasattr(self, "tab_advanced") and hasattr(self.tab_advanced, "refresh_data"):
            self.tab_advanced.refresh_data()

    def refresh_slots_view(self):
        if hasattr(self, "tab_advanced") and hasattr(self.tab_advanced, "refresh_slots_view"):
            self.tab_advanced.refresh_slots_view()
        elif hasattr(self, "tab_advanced") and hasattr(self.tab_advanced, "refresh_data"):
            self.tab_advanced.refresh_data()

    def export_json(self):
        if not self.save_json:
            self._notify("notice", "mb_load_save_first", kind="warning")
            return
        out_p = os.path.join(BASE_DIR, "save_decompressed.json")
        try:
            with open(out_p, "w", encoding="utf-8") as f:
                json.dump(self.save_json, f, indent=2, ensure_ascii=False)
            self._notify("notice", "mb_export_json_success", path=out_p)
        except Exception as e:
            self._notify("error", str(e), kind="error")

    def import_json(self):
        in_p = os.path.join(BASE_DIR, "save_decompressed.json")
        if not os.path.exists(in_p):
            self._notify("error", "mb_file_not_found", kind="error", path=in_p)
            return
        try:
            with open(in_p, "r", encoding="utf-8") as f:
                self.save_json = json.load(f)
            self.refresh_all_views()
            self.update_hud()
            self._auto_save()
            self._notify("notice", "mb_import_json_success")
        except Exception as e:
            self._notify("error", str(e), kind="error")

    def refresh_all_views(self):
        self.tab_currencies.refresh_data()
        self.tab_fighters.refresh_data()
        self.tab_materials.refresh_data()
        self.tab_decals.refresh_data()
        self.tab_blueprints.refresh_data()
        self.tab_mastery.refresh_data()
        self.tab_tower.refresh_data()
        self.tab_advanced.refresh_data()

    def update_hud(self):
        if not self.save_json:
            return

        curr = modifiers.get_player_currencies(self.save_json)
        dm = curr.get("dm", 0)
        kc = curr.get("kc", 0)
        spl = curr.get("spl", 0)
        bl = curr.get("bloodnium", 0)
        re_pt = curr.get("re_points", 0)
        self.hud_dm_lbl.setText(f"{dm:,} DM")
        self.hud_kc_lbl.setText(f"{kc:,} KC")
        self.hud_spl_lbl.setText(f"{spl:,} SPL")
        self.hud_bl_lbl.setText(f"{bl:,} BL")
        self.hud_re_lbl.setText(f"{re_pt:,} RE")

        # Blueprints count
        pr_map = modifiers.get_part_research_status(self.save_json) if self.save_json else {}
        count = sum(1 for v in pr_map.values() if v.get("status") in ("STORE_PLUS4", "REMODEL", "MAP"))
        total_bps = len(self.equipment_db) if self.equipment_db else 1370
        pct = int((count / max(1, total_bps)) * 100)
        self.hud_bp_lbl.setText(f"{count}/{total_bps} ({pct}%)")

        # Fighter
        f_list = modifiers.get_all_fighters_info(self.save_json)
        if f_list:
            cur_f = next((f for f in f_list if f.get("state") == "USE"), f_list[0])
            name = cur_f.get("name", "Principal")
            grade = cur_f.get("grade", 1)
            lvl = cur_f.get("level", 1)
            cls_code = cur_f.get("class", "BAL")
            cls_local = t(f"cls_{cls_code.lower()}", default=cur_f.get("class_name", "All-Rounder"))
            f_prefix = t("hud_fighter", default="Luchador Activo:")
            r_prefix = t("hud_rank", default="Rango")
            tdm_txt = t("hud_tdm", default="TDM")
            b_prefix = t("hud_bag", default="Bolsa:")
            s_suffix = t("hud_slots", default="casillas")
            base_up = modifiers.get_waiting_room_info(self.save_json) if hasattr(modifiers, "get_waiting_room_info") else {}
            rank_val = modifiers.calculate_player_rank(self.save_json) if hasattr(modifiers, "calculate_player_rank") else base_up.get("rank", 100)
            uid_val = self.save_json.get("soul", {}).get("uid", "---")
            bag_val = cur_f.get("bag_size", cur_f.get("bag", 20))

            self.player_name_lbl.setText(f"{f_prefix} {name} • {cls_local} (Tier {grade} ★)")
            self.player_meta_lbl.setText(f"UID: {uid_val} | {r_prefix} {rank_val} | {tdm_txt} | {b_prefix} {bag_val} {s_suffix}")

            body_val = cur_f.get("body", "BODY_FEMALE_001")
            model_art = f"all_official/{body_val.lower()}.png"
            pix = get_pixmap(model_art, (38, 38), preserve_aspect=True) or get_pixmap(get_fighter_class_icon(cls_code), (38, 38), preserve_aspect=True)
            if pix and not pix.isNull():
                self.player_avatar_lbl.setPixmap(pix)

    def get_current_active_slot_num(self):
        if self._active_slot_num:
            return self._active_slot_num
        saved = save_slots.get_active_slot()
        if saved:
            self._active_slot_num = saved
            return saved
        if self.save_json:
            matched = save_slots.find_matching_slot(self.save_json)
            if matched:
                self._active_slot_num = matched
                save_slots.set_active_slot(matched)
                return matched
        return None

    def set_current_active_slot_num(self, slot_num):
        self._active_slot_num = slot_num
        save_slots.set_active_slot(slot_num)

    def set_status(self, msg):
        self.status_bar.showMessage(str(msg))

    # =================================================================
    # DIALOGS & TOOLS
    # =================================================================
    def _open_armor_set_viewer(self):
        if not self.armor_sets:
            self._notify("notice", "mb_armor_sets_missing", kind="warning")
            return
        dlg = ArmorSetViewerDialog(self, self.save_json, self.armor_sets)
        dlg.exec()

    def _open_smart_analyzer(self):
        if not self.save_json:
            self._notify("notice", "mb_load_save_first", kind="warning")
            return
        dlg = SmartInventoryAnalyzerDialog(self, self.save_json, on_modified_cb=self.refresh_all_views)
        dlg.exec()

    def _check_app_updates(self):
        updater.check_updates_background(self, silent=False)

    # =================================================================
    # NOTIFICATIONS & STATUS
    # =================================================================
    def _notify(self, title_or_key, title_es_or_msg=None, msg_en=None, msg_es=None, kind="info", **kwargs):
        """
        Displays dialog and status updates in the user's selected language.
        Supports both modern key-based calls:
            self._notify("title_key", "msg_key", kind="info", **kwargs)
        And legacy 4-param calls:
            self._notify(title_en, title_es, msg_en, msg_es, kind="info")
        """
        lang = i18n.get_language()
        if msg_en is not None and msg_es is not None:
            if lang == "es":
                title = title_es_or_msg
                msg = msg_es
            else:
                title = title_or_key
                msg = msg_en
        elif title_es_or_msg is not None:
            title = t(title_or_key, default=title_or_key, **kwargs)
            msg = t(title_es_or_msg, default=title_es_or_msg, **kwargs)
        else:
            title = t("notice", default="Aviso")
            msg = t(title_or_key, default=title_or_key, **kwargs)

        first_line = (str(msg).splitlines() or [""])[0].replace("¡", "").replace("!", "")
        self.set_status(first_line)
        if kind == "info":
            QMessageBox.information(self, str(title), str(msg))
        elif kind == "warning":
            QMessageBox.warning(self, str(title), str(msg))
        elif kind == "error":
            QMessageBox.critical(self, str(title), str(msg))

    def after(self, ms, callback):
        """Tkinter-compatible after() method for cross-thread and legacy compatibility."""
        if ms <= 0:
            self._qt_dispatcher.dispatch_signal.emit(callback)
        else:
            QTimer.singleShot(ms, lambda: self._qt_dispatcher.dispatch_signal.emit(callback))

    # =================================================================
    # LANGUAGE
    # =================================================================
    def set_language(self, lang_code):
        if lang_code in ("es", "en", "zh"):
            i18n.set_language(lang_code)
            if hasattr(self, "_lang_code_to_display") and hasattr(self, "lang_cb"):
                disp = self._lang_code_to_display.get(lang_code)
                if disp:
                    idx = self.lang_cb.findText(disp)
                    if idx >= 0:
                        self.lang_cb.blockSignals(True)
                        self.lang_cb.setCurrentIndex(idx)
                        self.lang_cb.blockSignals(False)
            self._refresh_translations()

    change_language = set_language
    _change_language = set_language

    def _on_language_changed(self, index=None):
        val = self.lang_cb.currentText()
        new_lang = getattr(self, "_lang_display_map", {}).get(val)
        if not new_lang:
            if "中文" in val or "zh" in val.lower():
                new_lang = "zh"
            elif "Eng" in val:
                new_lang = "en"
            else:
                new_lang = "es"
        if new_lang != i18n.get_language():
            i18n.set_language(new_lang)
            self._refresh_translations()

    def _refresh_translations(self):
        self.setWindowTitle(t("app_title", default="LET IT DIE - Save Editor (Cyberpunk Edition)"))
        self.lbl_file.setText(t("save_file", default="Archivo de Guardado:"))
        self.browse_btn.setText(t("browse", default="Examinar..."))
        self.reload_btn.setText(t("reload", default="Recargar"))
        self.backup_btn.setText(t("backup", default="Crear Respaldo"))
        self.save_btn.setText(t("save_game", default="GUARDAR PARTIDA"))
        self.btn_sets_hud.setText(t("armor_sets", default="Conjuntos de Armadura"))
        self.btn_rnd_hud.setText(t("rnd_analyzer", default="Analizador I+D"))
        self.btn_update_hud.setText(t("updates", default="Actualizaciones"))
        self.lbl_lang.setText(t("lang_label", default="Idioma:"))

        active_idx = self.notebook.currentIndex()
        if active_idx < 0:
            active_idx = 0

        # Disconnect and delete previous tabs to guarantee 100% clean rebuild (matching Tkinter)
        old_tabs = [
            getattr(self, "tab_currencies", None),
            getattr(self, "tab_fighters", None),
            getattr(self, "tab_materials", None),
            getattr(self, "tab_decals", None),
            getattr(self, "tab_blueprints", None),
            getattr(self, "tab_mastery", None),
            getattr(self, "tab_tower", None),
            getattr(self, "tab_advanced", None),
        ]
        self.notebook.clear()
        for ot in old_tabs:
            if ot:
                ot.deleteLater()

        # Instantiate fresh tabs in the newly selected language
        self.tab_currencies = CurrenciesTab(self)
        self.tab_fighters = FightersTab(self)
        self.tab_materials = MaterialsTab(self)
        self.tab_decals = DecalsTab(self)
        self.tab_blueprints = BlueprintsTab(self)
        self.tab_mastery = MasteryTab(self)
        self.tab_tower = TowerTab(self)
        self.tab_advanced = AdvancedTab(self)

        self.notebook.addTab(self.tab_currencies, get_icon("dm", (20, 20)), t("tab_currencies", default="Divisas"))
        self.notebook.addTab(self.tab_fighters, get_icon("all-rounder", (20, 20)), t("tab_fighters", default="Luchadores"))
        self.notebook.addTab(self.tab_materials, get_icon("special_steel", (20, 20)), t("tab_materials", default="Materiales"))
        self.notebook.addTab(self.tab_decals, get_icon("decal_p", (20, 20)), t("tab_decals", default="Calcomanías"))
        self.notebook.addTab(self.tab_blueprints, get_icon("blueprint", (20, 20)), t("tab_blueprints", default="Planos"))
        self.notebook.addTab(self.tab_mastery, get_icon("weapon", (20, 20)), t("tab_mastery", default="Maestría"))
        self.notebook.addTab(self.tab_tower, get_icon("re_point", (20, 20)), t("tab_tower", default="Torre"))
        self.notebook.addTab(self.tab_advanced, get_icon("reversal_metal", (20, 20)), t("tab_advanced", default="Avanzado"))

        self.notebook.setCurrentIndex(active_idx)

        # Refresh all views and HUD
        self.refresh_all_views()
        self.update_hud()
        if not self.save_json:
            self.player_name_lbl.setText(t("hud_fighter_default", default="Luchador #1 (All-Rounder G6)"))
            self.player_meta_lbl.setText(t("hud_meta_default", default="Grado 6 | Nivel 145/145 | HP 10,240 | Bolsa: 30/30"))
            self.set_status(t("no_save_detected", default="Listo."))
