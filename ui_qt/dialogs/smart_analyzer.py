# -*- coding: utf-8 -*-
"""
Smart Inventory Analyzer Dialog for LET IT DIE Save Editor (PySide6 Edition).
Exact layout, logic, and behavior parity with GitHub Tkinter original.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QColor
from PySide6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout,
    QGroupBox, QLabel, QPushButton, QProgressBar,
    QTableWidget, QTableWidgetItem, QFrame, QMessageBox,
    QHeaderView, QInputDialog
)

import modifiers
from save_io import save_to_file
import i18n
from i18n import t, get_item_name
from ui_qt.theme import (
    get_icon, ACCENT_GOLD, ACCENT_CYAN, ACCENT_BLUE,
    ACCENT_GREEN, ACCENT_RED, FG_MUTED, FG_MAIN, BG_CARD, BG_PANEL
)


class SmartInventoryAnalyzerDialog(QDialog):
    """Interactive visual dialog to scan active R&D recipes, calculate deficits, and supply materials."""
    def __init__(self, parent, save_json, on_modified_cb=None):
        super().__init__(parent)
        self.parent_app = parent
        self.main_win = getattr(parent, "main_win", parent)
        self.save_json = save_json
        self.on_modified_cb = on_modified_cb

        self.setWindowTitle(t("dialog_smart_analyzer_title", default="Analizador Inteligente de I+D e Inventario"))
        self.resize(880, 640)
        self.setMinimumSize(740, 520)

        self._build_ui()
        self.refresh_analysis()

    def _build_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(14, 12, 14, 12)
        root_layout.setSpacing(8)

        # 1. Header Banner
        header = QFrame()
        header.setObjectName("TopFrame")
        header.setStyleSheet("background-color: #151824; border-radius: 6px; padding: 10px 14px;")
        h_layout = QVBoxLayout(header)
        h_layout.setContentsMargins(8, 8, 8, 8)
        h_layout.setSpacing(4)

        title_lbl = QLabel(t("dialog_smart_analyzer_title", default="Analizador Inteligente de I+D e Inventario"))
        title_lbl.setStyleSheet(f"color: {ACCENT_GOLD}; font-size: 13pt; font-weight: bold;")
        h_layout.addWidget(title_lbl)

        sub_lbl = QLabel(t("dialog_smart_analyzer_sub", default="Escanea todos los planos desbloqueados, calcula materiales requeridos y detecta déficits."))
        sub_lbl.setStyleSheet(f"color: {FG_MUTED}; font-size: 9pt;")
        h_layout.addWidget(sub_lbl)

        self.cap_lbl = QLabel(t("analyzer_calculating", default="Calculando almacenamiento..."))
        self.cap_lbl.setStyleSheet(f"font-size: 9pt; font-weight: bold; color: {FG_MAIN}; margin-top: 4px;")
        h_layout.addWidget(self.cap_lbl)

        self.cap_bar = QProgressBar()
        self.cap_bar.setStyleSheet("""
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
        h_layout.addWidget(self.cap_bar)
        root_layout.addWidget(header)

        # 2. Metrics summary row
        metrics_frame = QFrame()
        metrics_frame.setStyleSheet("background-color: transparent;")
        metrics_layout = QHBoxLayout(metrics_frame)
        metrics_layout.setContentsMargins(0, 2, 0, 4)
        metrics_layout.setSpacing(8)

        self.m_recipes_card, self.m_recipes_lbl = self._create_metric_card(t("analyzer_active_recipes", default="Recetas Activas"), "---", ACCENT_BLUE)
        self.m_needed_card, self.m_needed_lbl = self._create_metric_card(t("analyzer_needed_mats", default="Materiales Requeridos"), "---", FG_MAIN)
        self.m_deficit_card, self.m_deficit_lbl = self._create_metric_card(t("analyzer_deficit_mats", default="Materiales en Déficit"), "---", ACCENT_RED)
        self.m_units_card, self.m_units_lbl = self._create_metric_card(t("analyzer_missing_units", default="Unidades Faltantes"), "---", ACCENT_GOLD)

        metrics_layout.addWidget(self.m_recipes_card)
        metrics_layout.addWidget(self.m_needed_card)
        metrics_layout.addWidget(self.m_deficit_card)
        metrics_layout.addWidget(self.m_units_card)
        root_layout.addWidget(metrics_frame)

        # 3. Table of Materials (Exact columns: Material, ID, Necesario, Stock, Déficit, Estado)
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            t("analyzer_col_mat", default="Material"),
            t("inv_col_id", default="ID Interno"),
            t("analyzer_col_needed", default="Necesario"),
            t("analyzer_col_stock", default="Stock"),
            t("analyzer_col_deficit", default="Déficit"),
            t("analyzer_col_status", default="Estado")
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.verticalHeader().setDefaultSectionSize(32)
        root_layout.addWidget(self.table)

        # 4. Bottom Actions Bar (Exact parity with GitHub Tkinter)
        action_bar = QFrame()
        action_bar.setStyleSheet("background-color: #151824; border-radius: 6px; padding: 6px 10px;")
        a_layout = QHBoxLayout(action_bar)
        a_layout.setContentsMargins(8, 6, 8, 6)
        a_layout.setSpacing(6)

        btn_supply_needed = QPushButton(t("analyzer_btn_supply_needed", default="⚡ Suministrar Materiales Faltantes"))
        btn_supply_needed.setProperty("accent", "true")
        btn_supply_needed.clicked.connect(self._on_supply_missing)
        a_layout.addWidget(btn_supply_needed)

        btn_top_up = QPushButton(t("analyzer_btn_top_up", default="✨ Top-Up Inteligente (Mínimo)"))
        btn_top_up.clicked.connect(self._on_smart_top_up)
        a_layout.addWidget(btn_top_up)

        btn_refresh = QPushButton(t("inv_refresh", default="🔄 Actualizar"))
        btn_refresh.clicked.connect(self.refresh_analysis)
        a_layout.addWidget(btn_refresh)

        btn_expand_storage = QPushButton(t("analyzer_btn_expand_storage", default="📦 Ampliar Coin Locker"))
        btn_expand_storage.clicked.connect(self._on_expand_storage)
        a_layout.addWidget(btn_expand_storage)

        a_layout.addStretch()

        btn_close = QPushButton(t("dialog_close_btn", default="Cerrar"))
        btn_close.clicked.connect(self.accept)
        a_layout.addWidget(btn_close)

        root_layout.addWidget(action_bar)

    def _create_metric_card(self, title, initial_val, color):
        card = QFrame()
        card.setStyleSheet("background-color: #1c2030; border: 1px solid #252b40; border-radius: 6px; padding: 6px;")
        v = QVBoxLayout(card)
        v.setContentsMargins(8, 6, 8, 6)
        v.setSpacing(2)

        t_lbl = QLabel(title)
        t_lbl.setStyleSheet(f"color: {FG_MUTED}; font-size: 8pt;")
        v.addWidget(t_lbl)

        v_lbl = QLabel(initial_val)
        v_lbl.setStyleSheet(f"color: {color}; font-size: 13pt; font-weight: bold;")
        v.addWidget(v_lbl)
        return card, v_lbl

    def refresh_analysis(self):
        if not self.save_json:
            return

        res = modifiers.analyze_active_recipes_materials(self.save_json)

        # Storage capacity bar
        used = res["storage_used"]
        tot = res["storage_total"]
        free = res["storage_free"]
        pct = (used / tot * 100) if tot > 0 else 0
        self.cap_lbl.setText(t("inv_cap_lbl", default=f"Almacén: {used:,} / {tot:,} ({free:,} libres) - {pct:.1f}% ocupado", used=used, total=tot, free=free, pct=pct))
        self.cap_bar.setMaximum(tot if tot > 0 else 1)
        self.cap_bar.setValue(used)

        # Metrics
        deficit_items = [m for m in res["materials"] if m["deficit"] > 0]
        total_deficit_units = sum(m["deficit"] for m in deficit_items)

        self.m_recipes_lbl.setText(str(res["total_active_recipes"]))
        self.m_needed_lbl.setText(t("analyzer_types_fmt", default=f"{res['total_materials_needed']} tipos", count=res['total_materials_needed']))
        self.m_deficit_lbl.setText(t("analyzer_types_fmt", default=f"{len(deficit_items)} tipos", count=len(deficit_items)))
        self.m_units_lbl.setText(t("analyzer_units_fmt", default=f"{total_deficit_units:,} u.", count=total_deficit_units))

        # Populate table
        mats = res.get("materials", [])
        self.table.blockSignals(True)
        self.table.setRowCount(len(mats))

        for row_idx, m in enumerate(mats):
            name_str = m.get("name", m.get("itemid", ""))
            raw_id = m.get("itemid", "")
            needed = m.get("needed", 0)
            stock = m.get("stock", 0)
            deficit = m.get("deficit", 0)

            # Name + icon
            it_name = QTableWidgetItem(f" {name_str}")
            ico = get_icon(raw_id.lower(), (20, 20))
            if ico and not ico.isNull():
                it_name.setIcon(ico)
            self.table.setItem(row_idx, 0, it_name)

            # ID
            self.table.setItem(row_idx, 1, QTableWidgetItem(raw_id))

            # Needed
            it_needed = QTableWidgetItem(str(needed))
            it_needed.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row_idx, 2, it_needed)

            # Stock
            it_stock = QTableWidgetItem(str(stock))
            it_stock.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row_idx, 3, it_stock)

            # Deficit
            it_deficit = QTableWidgetItem(str(deficit))
            it_deficit.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if deficit > 0:
                it_deficit.setForeground(QColor(ACCENT_RED))
            self.table.setItem(row_idx, 4, it_deficit)

            # Status
            if deficit > 0:
                status_text = t("analyzer_status_deficit", default=f"Faltan {deficit}", count=deficit)
                it_status = QTableWidgetItem(status_text)
                it_status.setForeground(QColor(ACCENT_RED))
            else:
                status_text = t("analyzer_status_ok", default="OK (Suficiente)")
                it_status = QTableWidgetItem(status_text)
                it_status.setForeground(QColor(ACCENT_GREEN))
            it_status.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row_idx, 5, it_status)

        self.table.blockSignals(False)

    def _auto_save_and_sync(self):
        if self.save_json is not self.main_win.save_json:
            raise ValueError("The dialog no longer refers to the active save; reopen it.")
        self.main_win._auto_save()
        self.main_win.update_hud()
        self.main_win.refresh_all_views()

    def _on_supply_missing(self):
        if not self.save_json:
            return
        analysis = modifiers.analyze_active_recipes_materials(self.save_json)
        deficit_items = [m for m in analysis["materials"] if m["deficit"] > 0]
        if not deficit_items:
            QMessageBox.information(
                self,
                t("analyzer_full_stock_title", default="Stock Completo"),
                t("analyzer_full_stock_msg", default="¡No hay déficit de materiales! Tienes suficiente stock para todas las recetas activas.")
            )
            return

        tot_units = sum(m["deficit"] for m in deficit_items)
        if analysis["storage_free"] < tot_units:
            reply = QMessageBox.question(
                self,
                t("analyzer_limited_space_title", default="Espacio Insuficiente en Coin Locker"),
                t("analyzer_limited_space_msg",
                  default=f"Solo tienes {analysis['storage_free']} casillas libres en el Coin Locker, pero necesitas {tot_units} unidades.\n\n¿Deseas suministrar hasta donde quepa en el almacén?",
                  free=analysis['storage_free'], req=tot_units),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        added_types, added_units = modifiers.smart_supply_missing_materials(self.save_json)
        self._auto_save_and_sync()
        self.refresh_analysis()
        if self.on_modified_cb:
            try:
                self.on_modified_cb(t("analyzer_supply_status_fmt", default=f"Suministradas {added_units} unidades ({added_types} tipos).", units=added_units, types=added_types))
            except Exception:
                self.on_modified_cb()

        QMessageBox.information(
            self,
            t("analyzer_supplied_title", default="Materiales Suministrados"),
            t("analyzer_supplied_msg", default=f"Se han depositado con éxito {added_units} unidades ({added_types} tipos de materiales) en tu Coin Locker.", units=added_units, types=added_types)
        )

    def _on_smart_top_up(self):
        if not self.save_json:
            return
        target, ok = QInputDialog.getInt(
            self,
            t("analyzer_topup_title", default="Top-Up Inteligente de Materiales"),
            t("analyzer_topup_prompt", default="Introduce la cantidad objetivo para cada material esencial (1-99):"),
            15, 1, 99, 1
        )
        if not ok:
            return

        added_types, added_units = modifiers.smart_top_up_materials(self.save_json, target_qty=target)
        self._auto_save_and_sync()
        self.refresh_analysis()
        if self.on_modified_cb:
            try:
                self.on_modified_cb(t("smart_topup_cb_msg", default=f"Top-Up completado: {added_units} unidades ({added_types} tipos).", added_types=added_types, target=target, added_units=added_units))
            except Exception:
                self.on_modified_cb()

        QMessageBox.information(
            self,
            t("analyzer_topup_done_title", default="Top-Up Completado"),
            t("analyzer_topup_done_msg", default=f"Se han rellenado {added_types} tipos de materiales hasta alcanzar {target} unidades.\nTotal depositado: {added_units} unidades.", target=target, types=added_types, units=added_units)
        )

    def _on_expand_storage(self):
        if not self.save_json:
            return
        current_cap = len(self.save_json.get("soul", {}).get("cl", []))
        target, ok = QInputDialog.getInt(
            self,
            t("analyzer_expand_title", default="Ampliar Capacidad del Coin Locker"),
            t("analyzer_expand_prompt", default=f"Capacidad actual: {current_cap} casillas.\nIntroduce la nueva capacidad deseada:", cap=current_cap),
            max(current_cap, 6000), current_cap, 20000, 100
        )
        if not ok or target <= current_cap:
            return

        old_c, new_c = modifiers.expand_storage_capacity(self.save_json, target_capacity=target)
        self._auto_save_and_sync()
        self.refresh_analysis()
        if self.on_modified_cb:
            try:
                self.on_modified_cb(t("smart_locker_cb_msg", default=f"Capacidad ampliada a {new_c} casillas.", old=old_c, new=new_c))
            except Exception:
                self.on_modified_cb()

        QMessageBox.information(
            self,
            t("analyzer_expand_done_title", default="Capacidad Ampliada"),
            t("analyzer_expand_done_msg", default=f"¡Capacidad del Coin Locker ampliada con éxito!\nAnterior: {old_c:,} casillas\nNueva: {new_c:,} casillas", old_cap=old_c, new_cap=new_c)
        )
