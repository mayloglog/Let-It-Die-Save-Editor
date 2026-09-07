# -*- coding: utf-8 -*-
"""
Tower & Master Unlocks Tab for LET IT DIE Save Editor (PySide6 Edition).
Exact layout, colors, and behavior parity with Cyberpunk Dark design.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QGroupBox, QLabel, QPushButton, QComboBox, QLineEdit,
    QScrollArea, QFrame, QMessageBox
)

import modifiers
import i18n
from i18n import t
from ui_qt.theme import ACCENT_GOLD, ACCENT_CYAN, FG_MUTED, FG_MAIN


class TowerTab(QWidget):
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
        grid.setContentsMargins(0, 0, 0, 0)

        # -------------------------------------------------------------
        # Left Panel: Tower, Elevators & Stamps
        # -------------------------------------------------------------
        self.box_left = QGroupBox(t("tw_left_title", default="Torre de Barbs y Ascensores"))
        left_v = QVBoxLayout(self.box_left)
        left_v.setSpacing(8)

        self.lbl_map_title = QLabel("🗺️ " + t("tw_elev_title", default="Ascensores y Mapa Completo"))
        self.lbl_map_title.setStyleSheet(f"color: {ACCENT_GOLD}; font-weight: bold; font-size: 10pt;")
        left_v.addWidget(self.lbl_map_title)

        self.lbl_map_sub = QLabel(t("tw_elev_sub", default="Desbloquea los 61 ascensores y revela todas las salas de la Torre."))
        self.lbl_map_sub.setStyleSheet(f"color: {FG_MUTED}; font-size: 8pt;")
        left_v.addWidget(self.lbl_map_sub)

        self.btn_unlock_elevators = QPushButton(t("tw_elev_btn", default="Desbloquear los 61 Ascensores y Mapa"))
        self.btn_unlock_elevators.setProperty("accent", "true")
        self.btn_unlock_elevators.clicked.connect(self._unlock_elevators_action)
        left_v.addWidget(self.btn_unlock_elevators)

        self.btn_unlock_tutorial = QPushButton(t("tw_tut_btn", default="Desbloquear Tutorial y Sala de Espera"))
        self.btn_unlock_tutorial.clicked.connect(self._unlock_tutorial_action)
        left_v.addWidget(self.btn_unlock_tutorial)

        # Stamps
        self.lbl_stamp_title = QLabel(t("tw_stamp_title", default="🎯 Stamp Rally (Sellos)"))
        self.lbl_stamp_title.setStyleSheet(f"color: {ACCENT_GOLD}; font-weight: bold; font-size: 10pt;")
        left_v.addWidget(self.lbl_stamp_title)

        self.lbl_stamp_sub = QLabel(t("tw_stamp_sub", default="Registra los 40 sellos de la Torre en calificación PERFECTO."))
        self.lbl_stamp_sub.setStyleSheet(f"color: {FG_MUTED}; font-size: 8pt;")
        left_v.addWidget(self.lbl_stamp_sub)

        self.btn_stamps_perfect = QPushButton(t("tw_stamp_btn", default="Completar Todos los Sellos en Perfecto (40/40)"))
        self.btn_stamps_perfect.setProperty("accent", "true")
        self.btn_stamps_perfect.clicked.connect(self._set_stamps_perfect_action)
        left_v.addWidget(self.btn_stamps_perfect)

        # Secret Shop
        self.lbl_shop_title = QLabel(t("tw_shop_title", default="🛒 Tienda Ambulante Gyaku-Funsha"))
        self.lbl_shop_title.setStyleSheet(f"color: {ACCENT_GOLD}; font-weight: bold; font-size: 10pt;")
        left_v.addWidget(self.lbl_shop_title)

        self.btn_reset_shop = QPushButton(t("tw_shop_btn", default="Reiniciar Tiempo de Espera de Tienda"))
        self.btn_reset_shop.clicked.connect(self._reset_wandering_shop_action)
        left_v.addWidget(self.btn_reset_shop)

        # Emergency Rescue / Fix Stuck Loop
        self.btn_rescue = QPushButton(t("tw_rescue_btn", default="🚨 Rescate a Sala de Espera (Fix Carga)"))
        self.btn_rescue.setProperty("danger", "true")
        self.btn_rescue.clicked.connect(self._rescue_stuck_fighter_action)
        left_v.addWidget(self.btn_rescue)

        left_v.addStretch()
        grid.addWidget(self.box_left, 0, 0)

        # -------------------------------------------------------------
        # Right Panel: TDM & Encyclopedia Books
        # -------------------------------------------------------------
        self.box_right = QGroupBox(t("tw_right_title", default="TDM Metro Front y Enciclopedias"))
        right_v = QVBoxLayout(self.box_right)
        right_v.setSpacing(8)

        self.lbl_tdm_title = QLabel(t("tw_tdm_title", default="⚔️ Rango y Puntos TDM"))
        self.lbl_tdm_title.setStyleSheet(f"color: {ACCENT_GOLD}; font-weight: bold; font-size: 10pt;")
        right_v.addWidget(self.lbl_tdm_title)

        tdm_row = QHBoxLayout()
        self.lbl_tdm_rank = QLabel(t("tw_rank_lbl", default="Rango:"))
        tdm_row.addWidget(self.lbl_tdm_rank)
        self.cb_tdm_rank = QComboBox()
        self.tdm_rank_defs = [
            ("TDM_RANK_05_03", 5000, "tdm_rank_dia_1", "Diamante I (5,000 pts)"),
            ("TDM_RANK_05_02", 3200, "tdm_rank_dia_2", "Diamante II (3,200 pts)"),
            ("TDM_RANK_05_01", 3000, "tdm_rank_dia_3", "Diamante III (3,000 pts)"),
            ("TDM_RANK_04_03", 2500, "tdm_rank_plat_1", "Platino I (2,500 pts)"),
            ("TDM_RANK_03_03", 1800, "tdm_rank_gold_1", "Oro I (1,800 pts)"),
            ("TDM_RANK_02_03", 1200, "tdm_rank_silv_1", "Plata I (1,200 pts)"),
            ("TDM_RANK_01_03", 500, "tdm_rank_bron_1", "Bronce I (500 pts)"),
        ]
        for rid, pts, k, def_lbl in self.tdm_rank_defs:
            self.cb_tdm_rank.addItem(t(k, default=def_lbl), (rid, pts))
        tdm_row.addWidget(self.cb_tdm_rank)

        self.btn_apply_tdm = QPushButton(t("tw_apply_btn", default="Aplicar Rango"))
        self.btn_apply_tdm.setProperty("accent", "true")
        self.btn_apply_tdm.clicked.connect(self._set_tdm_rank_action)
        tdm_row.addWidget(self.btn_apply_tdm)
        right_v.addLayout(tdm_row)

        # Compendiums
        self.lbl_comp_title = QLabel(t("tw_comp_title", default="📚 Enciclopedias y Desbloqueos"))
        self.lbl_comp_title.setStyleSheet(f"color: {ACCENT_GOLD}; font-weight: bold; font-size: 10pt;")
        right_v.addWidget(self.lbl_comp_title)

        self.btn_comp_mats = QPushButton(t("tw_comp_mats_btn", default="Completar Enciclopedia de Materiales y Setas"))
        self.btn_comp_mats.setProperty("accent", "true")
        self.btn_comp_mats.clicked.connect(self._complete_compendiums_action)
        right_v.addWidget(self.btn_comp_mats)

        self.btn_hub = QPushButton(t("tw_comp_room_btn", default="Desbloquear Personalización de Sala"))
        self.btn_hub.clicked.connect(self._unlock_hub_action)
        right_v.addWidget(self.btn_hub)

        self.btn_quests = QPushButton(t("tw_comp_quests_btn", default="Completar Todas las Misiones"))
        self.btn_quests.setProperty("accent", "true")
        self.btn_quests.clicked.connect(self._complete_all_quests_action)
        right_v.addWidget(self.btn_quests)

        self.btn_media = QPushButton(t("tw_comp_mags_btn", default="Desbloquear Revistas y Radio"))
        self.btn_media.clicked.connect(self._unlock_magazines_and_radio_action)
        right_v.addWidget(self.btn_media)

        right_v.addStretch()
        grid.addWidget(self.box_right, 0, 1)

        # -------------------------------------------------------------
        # Bottom Panel: Records & Playlog
        # -------------------------------------------------------------
        self.box_playlog = QGroupBox(t("tw_playlog_title", default="Registros de Exploración y Combate"))
        playlog_layout = QHBoxLayout(self.box_playlog)
        playlog_layout.setSpacing(16)

        # Left Column: Editable Records & Penalties
        rec_left_w = QWidget()
        rec_left_v = QVBoxLayout(rec_left_w)
        rec_left_v.setContentsMargins(0, 0, 0, 0)
        rec_left_v.setSpacing(8)

        # Max Floor Row
        row_fl = QHBoxLayout()
        self.lbl_max_fl_title = QLabel(t("tw_max_floor_lbl", default="Piso Récord:"))
        self.lbl_max_fl_title.setStyleSheet(f"color: {ACCENT_GOLD}; font-weight: bold;")
        row_fl.addWidget(self.lbl_max_fl_title)

        self.entry_max_floor = QLineEdit("40")
        self.entry_max_floor.setFixedWidth(70)
        self.entry_max_floor.setAlignment(Qt.AlignmentFlag.AlignCenter)
        row_fl.addWidget(self.entry_max_floor)

        self.btn_set_floor = QPushButton(t("tw_set_floor_btn", default="🏆 Guardar Piso"))
        self.btn_set_floor.setProperty("accent", "true")
        self.btn_set_floor.clicked.connect(self._set_max_floor_action)
        row_fl.addWidget(self.btn_set_floor)
        row_fl.addStretch()
        rec_left_v.addLayout(row_fl)

        # Interruption / Penalties Row
        row_int = QHBoxLayout()
        self.lbl_int_title = QLabel(t("tw_interrupt_lbl", default="Interrupciones de Torre:"))
        row_int.addWidget(self.lbl_int_title)

        self.lbl_interruptions = QLabel("0")
        self.lbl_interruptions.setStyleSheet(f"color: {ACCENT_CYAN}; font-weight: bold;")
        row_int.addWidget(self.lbl_interruptions)

        self.btn_reset_interrupt = QPushButton(t("tw_reset_interrupt_btn", default="🛡️ Limpiar Penalizaciones de Desconexión / Muerte"))
        self.btn_reset_interrupt.clicked.connect(self._reset_interrupt_action)
        row_int.addWidget(self.btn_reset_interrupt)
        row_int.addStretch()
        rec_left_v.addLayout(row_int)

        playlog_layout.addWidget(rec_left_w, 1)

        # Right Column: Exploration Stats Grid
        rec_right_w = QWidget()
        rec_right_v = QVBoxLayout(rec_right_w)
        rec_right_v.setContentsMargins(0, 0, 0, 0)
        rec_right_v.setSpacing(4)

        self.lbl_stats_title = QLabel(t("tw_stats_title", default="Estadísticas de Exploración:"))
        self.lbl_stats_title.setStyleSheet(f"color: {ACCENT_GOLD}; font-weight: bold;")
        rec_right_v.addWidget(self.lbl_stats_title)

        st_grid = QGridLayout()
        st_grid.setSpacing(6)

        self.pl_elev_lbl = QLabel(t("hud_elevators_fmt", count=0, default="Ascensores: 0"))
        st_grid.addWidget(self.pl_elev_lbl, 0, 0)

        self.pl_esc_lbl = QLabel(t("hud_escalators_fmt", count=0, default="Escaleras: 0"))
        st_grid.addWidget(self.pl_esc_lbl, 0, 1)

        self.pl_mats_lbl = QLabel(t("hud_materials_fmt", count=0, default="Materiales: 0"))
        st_grid.addWidget(self.pl_mats_lbl, 1, 0)

        self.pl_res_lbl = QLabel(t("hud_researches_fmt", count=0, default="Investigaciones: 0"))
        st_grid.addWidget(self.pl_res_lbl, 1, 1)

        self.pl_boss_lbl = QLabel(t("hud_boss_kills_fmt", count=0, default="Jefes Derrotados: 0"))
        st_grid.addWidget(self.pl_boss_lbl, 2, 0)

        self.pl_time_lbl = QLabel(t("hud_tower_time_fmt", hours="0.0", default="Tiempo: 0.0h"))
        st_grid.addWidget(self.pl_time_lbl, 2, 1)

        rec_right_v.addLayout(st_grid)
        playlog_layout.addWidget(rec_right_w, 1)

        grid.addWidget(self.box_playlog, 1, 0, 1, 2)

        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)

    def refresh_data(self):
        """Refreshes records and playlog values."""
        save = self.main_win.save_json
        if not save:
            return

        try:
            pl = modifiers.get_tower_playlog(save)
            max_floor = pl.get("max_floor", 40)
            interruptions = pl.get("interruptions", 0)
            elev = pl.get("elevators", 0)
            esc = pl.get("escalators", 0)
            mats = pl.get("materials_collected", 0)
            res = pl.get("researches", 0)
            boss = pl.get("boss_kills", 0)
            time_h = pl.get("playtime_hours", 0.0)

            if hasattr(self, "entry_max_floor") and not self.entry_max_floor.hasFocus():
                self.entry_max_floor.setText(str(max_floor))
            if hasattr(self, "lbl_interruptions"):
                self.lbl_interruptions.setText(t("hud_penalties_fmt", count=interruptions, default=f"{interruptions:,}"))
            if hasattr(self, "pl_elev_lbl"):
                self.pl_elev_lbl.setText(t("hud_elevators_fmt", count=elev, default=f"Ascensores: {elev:,}"))
            if hasattr(self, "pl_esc_lbl"):
                self.pl_esc_lbl.setText(t("hud_escalators_fmt", count=esc, default=f"Escaleras: {esc:,}"))
            if hasattr(self, "pl_mats_lbl"):
                self.pl_mats_lbl.setText(t("hud_materials_fmt", count=mats, default=f"Materiales: {mats:,}"))
            if hasattr(self, "pl_res_lbl"):
                self.pl_res_lbl.setText(t("hud_researches_fmt", count=res, default=f"Investigaciones: {res:,}"))
            if hasattr(self, "pl_boss_lbl"):
                self.pl_boss_lbl.setText(t("hud_boss_kills_fmt", count=boss, default=f"Jefes: {boss:,}"))
            if hasattr(self, "pl_time_lbl"):
                self.pl_time_lbl.setText(t("hud_tower_time_fmt", hours=time_h, default=f"Tiempo: {time_h}h"))
        except Exception:
            pass

    def _rescue_stuck_fighter_action(self):
        save = self.main_win.save_json
        if not save:
            return
        modifiers.reset_floor_to_waiting_room(save)
        self.main_win._auto_save()
        self.main_win.refresh_all_views()
        self.main_win._notify("tw_notify_rescued_title", "tw_notify_rescued_msg")

    def _set_max_floor_action(self):
        save = self.main_win.save_json
        if not save:
            return
        try:
            fl = int(self.entry_max_floor.text().strip())
        except ValueError:
            fl = 40
        modifiers.set_tower_max_floor(save, max_floor=fl)
        self.main_win._auto_save()
        self.main_win.refresh_all_views()
        self.main_win._notify("tw_notify_record_title", "tw_notify_record_msg", fl=fl)

    def _reset_interrupt_action(self):
        save = self.main_win.save_json
        if not save:
            return
        old = modifiers.reset_tower_interruptions(save)
        self.main_win._auto_save()
        self.main_win.refresh_all_views()
        self.main_win._notify("tw_notify_penalties_cleared_title", "tw_notify_penalties_cleared_msg", old=old)

    def _unlock_elevators_action(self):
        save = self.main_win.save_json
        if not save:
            return
        modifiers.unlock_all_tower_elevators(save)
        self.main_win._auto_save()
        self.main_win.refresh_all_views()
        self.main_win._notify("tw_notify_elevators_full_title", "tw_notify_elevators_full_msg")

    def _unlock_tutorial_action(self):
        save = self.main_win.save_json
        if not save:
            return
        modifiers.unlock_tutorial_and_waiting_room(save)
        self.main_win._auto_save()
        self.main_win.refresh_all_views()
        self.main_win._notify("tw_notify_tutorial_unlocked_title", "tw_notify_tutorial_unlocked_msg")

    def _set_stamps_perfect_action(self):
        save = self.main_win.save_json
        if not save:
            return
        modifiers.set_all_stamps_perfect(save)
        self.main_win._auto_save()
        self.main_win._notify("tw_notify_stamps_perfect_title", "tw_notify_stamps_perfect_msg")

    def _reset_wandering_shop_timer(self):
        self._reset_wandering_shop_action()

    def _reset_wandering_shop_action(self):
        save = self.main_win.save_json
        if not save:
            return
        modifiers.reset_wandering_shop_timer(save)
        self.main_win._auto_save()
        self.main_win._notify("tw_notify_wandering_shop_title", "tw_notify_wandering_shop_msg")

    def _set_tdm_rank_action(self):
        save = self.main_win.save_json
        if not save:
            return
        data = self.cb_tdm_rank.currentData()
        if data:
            rank_id, pts = data
            sel_text = self.cb_tdm_rank.currentText()
            modifiers.set_tdm_rank(save, rank_id=rank_id, points=pts)
            self.main_win._auto_save()
            self.main_win.refresh_all_views()
            self.main_win.update_hud()
            self.main_win._notify("tw_notify_tdm_rank_title", "tw_notify_tdm_rank_msg", sel=sel_text, points=pts)

    def _complete_compendiums_action(self):
        save = self.main_win.save_json
        if not save:
            return
        modifiers.complete_encyclopedia_books(save)
        self.main_win._auto_save()
        self.main_win._notify("tw_notify_compendiums_title", "tw_notify_compendiums_msg", m_cnt=167, b_cnt=53)

    def _unlock_hub_action(self):
        save = self.main_win.save_json
        if not save:
            return
        modifiers.unlock_all_hub_customizations(save)
        self.main_win._auto_save()
        self.main_win._notify("tw_notify_hub_title", "tw_notify_hub_msg", total=24, unlocked=24)

    def _complete_all_quests_action(self):
        save = self.main_win.save_json
        if not save:
            return
        cnt = modifiers.complete_all_quests(save)
        self.main_win._auto_save()
        self.main_win._notify("tw_notify_quests_title", "tw_notify_quests_msg", cnt=cnt)

    def _unlock_magazines_and_radio_action(self):
        save = self.main_win.save_json
        if not save:
            return
        modifiers.unlock_all_magazines(save)
        modifiers.unlock_all_radio_music(save)
        self.main_win._auto_save()
        self.main_win._notify("tw_notify_collectibles_title", "tw_notify_collectibles_msg")

    def refresh_translations(self):
        self.box_left.setTitle(t("tw_left_title", default="Torre de Barbs y Ascensores"))
        if hasattr(self, 'lbl_map_title'):
            self.lbl_map_title.setText("🗺️ " + t("tw_elev_title", default="Ascensores y Mapa Completo"))
        if hasattr(self, 'lbl_map_sub'):
            self.lbl_map_sub.setText(t("tw_elev_sub", default="Desbloquea los 61 ascensores y revela todas las salas de la Torre."))
        self.btn_unlock_elevators.setText(t("tw_elev_btn", default="Desbloquear los 61 Ascensores y Mapa"))
        self.btn_unlock_tutorial.setText(t("tw_tut_btn", default="Desbloquear Tutorial y Sala de Espera"))
        if hasattr(self, 'lbl_stamp_title'):
            self.lbl_stamp_title.setText(t("tw_stamp_title", default="🎯 Stamp Rally (Sellos)"))
        if hasattr(self, 'lbl_stamp_sub'):
            self.lbl_stamp_sub.setText(t("tw_stamp_sub", default="Registra los 40 sellos de la Torre en calificación PERFECTO."))
        self.btn_stamps_perfect.setText(t("tw_stamp_btn", default="Completar Todos los Sellos en Perfecto (40/40)"))
        if hasattr(self, 'lbl_shop_title'):
            self.lbl_shop_title.setText(t("tw_shop_title", default="🛒 Tienda Ambulante Gyaku-Funsha"))
        self.btn_reset_shop.setText(t("tw_shop_btn", default="Reiniciar Tiempo de Espera de Tienda"))
        if hasattr(self, 'btn_rescue'):
            self.btn_rescue.setText(t("tw_rescue_btn", default="🚨 Rescate a Sala de Espera (Fix Carga)"))

        self.box_right.setTitle(t("tw_right_title", default="TDM Metro Front y Enciclopedias"))
        if hasattr(self, 'lbl_tdm_title'):
            self.lbl_tdm_title.setText(t("tw_tdm_title", default="⚔️ Rango y Puntos TDM"))
        if hasattr(self, 'lbl_tdm_rank'):
            self.lbl_tdm_rank.setText(t("tw_rank_lbl", default="Rango:"))
        if hasattr(self, 'cb_tdm_rank') and hasattr(self, 'tdm_rank_defs'):
            cur_data = self.cb_tdm_rank.currentData()
            self.cb_tdm_rank.blockSignals(True)
            self.cb_tdm_rank.clear()
            for rid, pts, k, def_lbl in self.tdm_rank_defs:
                self.cb_tdm_rank.addItem(t(k, default=def_lbl), (rid, pts))
            idx = self.cb_tdm_rank.findData(cur_data)
            if idx >= 0:
                self.cb_tdm_rank.setCurrentIndex(idx)
            self.cb_tdm_rank.blockSignals(False)
        self.btn_apply_tdm.setText(t("tw_apply_btn", default="Aplicar Rango"))

        if hasattr(self, 'lbl_comp_title'):
            self.lbl_comp_title.setText(t("tw_comp_title", default="📚 Enciclopedias y Desbloqueos"))
        self.btn_comp_mats.setText(t("tw_comp_mats_btn", default="Completar Enciclopedia de Materiales y Setas"))
        self.btn_hub.setText(t("tw_comp_room_btn", default="Desbloquear Personalización de Sala"))
        self.btn_quests.setText(t("tw_comp_quests_btn", default="Completar Todas las Misiones"))
        self.btn_media.setText(t("tw_comp_mags_btn", default="Desbloquear Revistas y Radio"))

        self.box_playlog.setTitle(t("tw_playlog_title", default="Registros de Exploración y Combate"))
        if hasattr(self, 'lbl_max_fl_title'):
            self.lbl_max_fl_title.setText(t("tw_max_floor_lbl", default="Piso Récord:"))
        if hasattr(self, 'btn_set_floor'):
            self.btn_set_floor.setText(t("tw_set_floor_btn", default="🏆 Guardar Piso"))
        if hasattr(self, 'lbl_int_title'):
            self.lbl_int_title.setText(t("tw_interrupt_lbl", default="Interrupciones de Torre:"))
        if hasattr(self, 'btn_reset_interrupt'):
            self.btn_reset_interrupt.setText(t("tw_reset_interrupt_btn", default="🛡️ Limpiar Penalizaciones de Desconexión / Muerte"))
        if hasattr(self, 'lbl_stats_title'):
            self.lbl_stats_title.setText(t("tw_stats_title", default="Estadísticas de Exploración:"))
        self.refresh_data()
