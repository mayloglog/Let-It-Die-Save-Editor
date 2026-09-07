# -*- coding: utf-8 -*-
"""
Advanced & Save Slots Tab Mixin for LET IT DIE Save Editor.
Provides an interactive 10-slot save management system with rich game metadata
(Haters, Floor, Currencies, Fighters), dedicated per-slot backups, and advanced tools.
"""

import os
import time
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

import save_io
import i18n
from i18n import t
from ui.theme import (
    BG_DARK, BG_PANEL, BG_CARD, BG_CARD_LIGHT,
    FG_TEXT, FG_MUTED, ACCENT_GOLD, ACCENT_CYAN, ACCENT_GREEN, ACCENT_RED
)
import core.save_slots as save_slots
from ui.components import ScrollableFrame
from ui.dialogs.slot_backups_dialog import SlotBackupsDialog


class AdvancedTabMixin:
    """Provides methods for constructing and handling the Save Slots & Advanced Tab."""

    def _build_advanced_tab(self):
        # Configure root advanced tab container
        self.tab_advanced.columnconfigure(0, weight=1)
        self.tab_advanced.rowconfigure(0, weight=1)

        # Create sub-notebook to separate Slots Manager and Advanced Tools cleanly
        self.adv_notebook = ttk.Notebook(self.tab_advanced)
        self.adv_notebook.grid(row=0, column=0, sticky="nsew")

        self.subtab_slots = ttk.Frame(self.adv_notebook, padding=8)
        self.subtab_tools = ttk.Frame(self.adv_notebook, padding=8)

        self.adv_notebook.add(self.subtab_slots, text=t("adv_subtab_slots"))
        self.adv_notebook.add(self.subtab_tools, text=t("adv_subtab_tools"))

        # Build Sub-Tabs
        self._build_slots_manager_subtab()
        self._build_tools_cache_subtab()

    # =========================================================================
    # 1. SAVE SLOTS MANAGER SUB-TAB
    # =========================================================================
    def _build_slots_manager_subtab(self):
        self.subtab_slots.columnconfigure(0, weight=1)
        self.subtab_slots.rowconfigure(1, weight=1)

        # Top Banner: Active Save Profile Summary
        self.slot_banner_frame = tk.Frame(
            self.subtab_slots,
            bg=BG_CARD,
            padx=12,
            pady=8,
            highlightbackground=BG_CARD_LIGHT,
            highlightthickness=1
        )
        self.slot_banner_frame.grid(row=0, column=0, sticky="ew", pady=(0, 6))

        # Banner Title & Active Status
        banner_top = tk.Frame(self.slot_banner_frame, bg=BG_CARD)
        banner_top.pack(fill="x")

        self.lbl_banner_title = tk.Label(
            banner_top,
            text=t("slot_active_banner_title"),
            font=("Segoe UI", 10, "bold"),
            fg=ACCENT_GOLD,
            bg=BG_CARD
        )
        self.lbl_banner_title.pack(side="left")

        self.lbl_banner_path = tk.Label(
            banner_top,
            text="",
            font=("Segoe UI", 8),
            fg=FG_MUTED,
            bg=BG_CARD
        )
        self.lbl_banner_path.pack(side="left", padx=(10, 0))

        ttk.Button(
            banner_top,
            text="🔄 " + t("rebind_tool_open_btn"),
            command=self._open_account_compatibility_dialog
        ).pack(side="right")

        # Banner Stats Rows (2 lines to avoid horizontal overflow)
        self.banner_stats_frame = tk.Frame(self.slot_banner_frame, bg=BG_CARD)
        self.banner_stats_frame.pack(fill="x", pady=(2, 1))

        self.lbl_banner_fighter = tk.Label(
            self.banner_stats_frame,
            text="",
            font=("Segoe UI", 9, "bold"),
            fg=FG_TEXT,
            bg=BG_CARD
        )
        self.lbl_banner_fighter.pack(side="left")

        self.banner_stats_frame2 = tk.Frame(self.slot_banner_frame, bg=BG_CARD)
        self.banner_stats_frame2.pack(fill="x", pady=(1, 2))

        self.lbl_banner_floor_hater = tk.Label(
            self.banner_stats_frame2,
            text="",
            font=("Segoe UI", 8),
            fg=ACCENT_CYAN,
            bg=BG_CARD
        )
        self.lbl_banner_floor_hater.pack(side="left", padx=(0, 16))

        self.lbl_banner_coins = tk.Label(
            self.banner_stats_frame2,
            text="",
            font=("Segoe UI", 8),
            fg=ACCENT_GOLD,
            bg=BG_CARD
        )
        self.lbl_banner_coins.pack(side="left")

        # Main Scrollable Slots Grid Container using ScrollableFrame
        self.slots_scroll = scroll = ScrollableFrame(self.subtab_slots)
        scroll.grid(row=1, column=0, sticky="nsew")
        self.slots_inner_frame = scroll.content
        self.slots_canvas = scroll.canvas
        scroll.canvas.configure(bg=BG_DARK)

        # 2 Columns grid inside inner frame
        self.slots_inner_frame.columnconfigure(0, weight=1)
        self.slots_inner_frame.columnconfigure(1, weight=1)

        self.slot_widgets = {}
        self.refresh_slots_view()

    def refresh_slots_view(self):
        """Rebuilds or refreshes all 10 slot cards and the active save banner."""
        if not hasattr(self, "slots_inner_frame"):
            return

        # 1. Update Active Save Banner
        active_meta = None
        if self.save_json and hasattr(self, "save_path") and self.save_path:
            active_meta = save_slots.extract_save_metadata(self.save_json)
            p_name = active_meta.get("player_name", "Senpai")
            f_name = active_meta.get("fighter_name", "Fighter")
            f_class = active_meta.get("fighter_class", "BAL")
            f_grade = active_meta.get("fighter_grade", 1)
            f_lvl = active_meta.get("fighter_lvl", 1)
            flr = active_meta.get("max_floor", 1)
            haters = active_meta.get("haters_killed", 0)
            kc = active_meta.get("kill_coins", 0)
            dm = active_meta.get("death_metals", 0)
            spl = active_meta.get("splithium", 0)
            bl = active_meta.get("bloodnium", 0)
            hrs = active_meta.get("playtime_hours", 0)

            self.lbl_banner_path.config(text=f"({os.path.basename(self.save_path)})")
            self.lbl_banner_fighter.config(
                text=f"👤 {p_name} • 🥋 {f_name} ({f_class} ★{f_grade} Lv.{f_lvl})"
            )
            self.lbl_banner_floor_hater.config(
                text=f"🗼 {t('slot_lbl_floor', floor=flr)}  |  ⚔️ {t('slot_lbl_haters', haters=haters)}  |  ⏱️ {hrs}h"
            )
            self.lbl_banner_coins.config(
                text=t("slot_lbl_coins", kc=kc, dm=dm, spl=spl, bl=bl)
            )
        else:
            self.lbl_banner_path.config(text="")
            self.lbl_banner_fighter.config(text=t("slot_no_active_save"))
            self.lbl_banner_floor_hater.config(text="")
            self.lbl_banner_coins.config(text="")

        # 2. Render 10 Slot Cards
        slots_data = save_slots.get_all_slots()

        # Clear existing card widgets
        for widget in self.slots_inner_frame.winfo_children():
            widget.destroy()

        for idx, s in enumerate(slots_data):
            slot_num = s["slot_num"]
            col = (slot_num - 1) % 2
            row = (slot_num - 1) // 2

            self._create_slot_card(self.slots_inner_frame, s, row, col, active_meta)

    def _create_slot_card(self, parent, slot_data, row, col, active_meta):
        slot_num = slot_data["slot_num"]
        is_empty = slot_data["is_empty"]
        meta = slot_data.get("meta", {})
        backups_cnt = slot_data.get("backups_count", 0)

        # Check if this slot matches active save
        is_active = False
        current_active = getattr(self, "get_current_active_slot_num", lambda: None)()
        if current_active is not None:
            is_active = (slot_num == current_active)
        elif not is_empty and active_meta:
            s_uid = meta.get("uid")
            s_steam = meta.get("steam_id")
            s_kc = meta.get("kill_coins")
            s_flr = meta.get("max_floor")
            if (s_steam == active_meta.get("steam_id") and
                s_kc == active_meta.get("kill_coins") and
                s_flr == active_meta.get("max_floor")):
                is_active = True

        border_color = ACCENT_GREEN if is_active else (ACCENT_GOLD if not is_empty else BG_CARD_LIGHT)
        card = tk.Frame(
            parent,
            bg=BG_CARD,
            padx=12,
            pady=8,
            highlightbackground=border_color,
            highlightthickness=2 if (is_active or not is_empty) else 1
        )
        card.grid(row=row, column=col, sticky="nsew", padx=4, pady=4)

        # Top Header: Slot Number, Custom Name & Status Badge
        hdr = tk.Frame(card, bg=BG_CARD)
        hdr.pack(fill="x")

        custom_name = slot_data.get("custom_name") or meta.get("custom_name", "")
        slot_title = t("slot_card_num", num=slot_num)
        display_title = f"🎮 {slot_title}: {custom_name}" if custom_name else f"🎮 {slot_title}"

        lbl_title = tk.Label(
            hdr,
            text=display_title,
            font=("Segoe UI", 10, "bold"),
            fg=ACCENT_GOLD if not is_empty else FG_MUTED,
            bg=BG_CARD,
            cursor="hand2"
        )
        lbl_title.pack(side="left")
        lbl_title.bind("<Double-Button-1>", lambda e, s=slot_num: self._rename_slot_action(s))

        btn_edit = tk.Label(
            hdr,
            text="✏️",
            font=("Segoe UI", 8),
            fg=FG_MUTED,
            bg=BG_CARD,
            cursor="hand2"
        )
        btn_edit.pack(side="left", padx=4)
        btn_edit.bind("<Button-1>", lambda e, s=slot_num: self._rename_slot_action(s))

        if is_active:
            badge_text = t("slot_badge_active")
            badge_color = ACCENT_GREEN
        elif not is_empty:
            badge_text = t("slot_badge_saved")
            badge_color = ACCENT_CYAN
        else:
            badge_text = t("slot_badge_empty")
            badge_color = FG_MUTED

        tk.Label(
            hdr,
            text=badge_text,
            font=("Segoe UI", 8, "bold"),
            fg=badge_color,
            bg=BG_CARD
        ).pack(side="right")

        # Content Section
        if is_empty:
            # Empty state
            body_f = tk.Frame(card, bg=BG_CARD, pady=8)
            body_f.pack(fill="x")

            tk.Label(
                body_f,
                text=t("slot_empty_desc"),
                font=("Segoe UI", 8),
                fg=FG_MUTED,
                bg=BG_CARD
            ).pack(anchor="w")

            if backups_cnt > 0:
                tk.Label(
                    body_f,
                    text=f"🛡️ {t('slot_lbl_backups_count', count=backups_cnt)}",
                    font=("Segoe UI", 7),
                    fg=ACCENT_CYAN,
                    bg=BG_CARD
                ).pack(anchor="w", pady=(2, 0))

            # Actions for empty slot
            act_f1 = tk.Frame(card, bg=BG_CARD, pady=2)
            act_f1.pack(fill="x")

            btn_save = ttk.Button(
                act_f1,
                text=t("slot_btn_save_here"),
                style="Accent.TButton",
                command=lambda s=slot_num: self._save_current_to_slot_action(s)
            )
            btn_save.pack(side="left", fill="x", expand=True, padx=(0, 3))

            btn_import = ttk.Button(
                act_f1,
                text=t("slot_btn_import_file"),
                command=lambda s=slot_num: self._import_file_to_slot_action(s)
            )
            btn_import.pack(side="left", fill="x", expand=True, padx=(3, 3))

            btn_ren = ttk.Button(
                act_f1,
                text="✏️",
                width=3,
                command=lambda s=slot_num: self._rename_slot_action(s)
            )
            btn_ren.pack(side="left")

            if backups_cnt > 0:
                act_f2 = tk.Frame(card, bg=BG_CARD, pady=2)
                act_f2.pack(fill="x")

                btn_quick_bak = ttk.Button(
                    act_f2,
                    text=t("slot_btn_use_latest_session"),
                    command=lambda s=slot_num: self._quick_use_latest_backup_action(s)
                )
                btn_quick_bak.pack(side="left", fill="x", expand=True, padx=(0, 3))

                btn_bak = ttk.Button(
                    act_f2,
                    text=t("slot_btn_view_backups", count=backups_cnt),
                    command=lambda s=slot_num: self._open_slot_backups_action(s)
                )
                btn_bak.pack(side="left", fill="x", expand=True, padx=(3, 0))

        else:
            # Occupied state with full metadata
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

            info_f = tk.Frame(card, bg=BG_CARD, pady=2)
            info_f.pack(fill="x")

            # Row 1: Player & Fighter
            tk.Label(
                info_f,
                text=f"👤 {p_name} ({s_id})",
                font=("Segoe UI", 9, "bold"),
                fg=FG_TEXT,
                bg=BG_CARD
            ).pack(anchor="w")

            tk.Label(
                info_f,
                text=f"🥋 {t('slot_lbl_fighter_info', name=f_name, clazz=f_class, grade=f_grade, lvl=f_lvl)}",
                font=("Segoe UI", 8),
                fg=ACCENT_CYAN,
                bg=BG_CARD
            ).pack(anchor="w", pady=(1, 1))

            # Row 2: Floor & Haters & Playtime
            tk.Label(
                info_f,
                text=f"🗼 {t('slot_lbl_floor', floor=flr)}   ⚔️ {t('slot_lbl_haters', haters=haters)}   ⏱️ {hrs}h",
                font=("Segoe UI", 8, "bold"),
                fg=ACCENT_GOLD,
                bg=BG_CARD
            ).pack(anchor="w", pady=(0, 1))

            # Row 3: Coins
            tk.Label(
                info_f,
                text=t("slot_lbl_coins", kc=kc, dm=dm, spl=spl, bl=bl),
                font=("Segoe UI", 8),
                fg=FG_TEXT,
                bg=BG_CARD
            ).pack(anchor="w", pady=(0, 1))

            # Row 4: Backups / Sessions info
            latest_bak = slot_data.get("latest_backup")
            latest_meta = (latest_bak.get("meta") or {}) if latest_bak else {}
            if latest_bak and not latest_meta.get("error"):
                lb_f_name = latest_meta.get("fighter_name", "Fighter")
                lb_f_lvl = latest_meta.get("fighter_lvl", 1)
                lb_flr = latest_meta.get("max_floor", 1)
                lb_date = latest_bak.get("date_str", "")
                lb_summary = f"🕒 {t('slot_lbl_latest_session_short', date=lb_date, fighter=lb_f_name, lvl=lb_f_lvl, floor=lb_flr)}"
            elif backups_cnt > 0:
                lb_summary = f"🛡️ {t('slot_lbl_backups_count', count=backups_cnt)} • {last_saved}"
            else:
                lb_summary = f"🛡️ {t('slot_lbl_backups_count', count=backups_cnt)}"

            tk.Label(
                info_f,
                text=lb_summary,
                font=("Segoe UI", 7),
                fg=ACCENT_CYAN if latest_bak else FG_MUTED,
                bg=BG_CARD
            ).pack(anchor="w", pady=(0, 3))

            # Action Buttons Rows (2 balanced rows for responsive fit)
            act_row1 = tk.Frame(card, bg=BG_CARD, pady=1)
            act_row1.pack(fill="x")

            # Load into Game button
            btn_load = ttk.Button(
                act_row1,
                text=t("slot_btn_load_active"),
                style="Accent.TButton" if not is_active else "",
                command=lambda s=slot_num: self._load_slot_action(s)
            )
            btn_load.pack(side="left", fill="x", expand=True, padx=(0, 3))

            # Quick Use Latest Session button
            if backups_cnt > 0:
                btn_quick_bak = ttk.Button(
                    act_row1,
                    text=t("slot_btn_use_latest_session"),
                    command=lambda s=slot_num: self._quick_use_latest_backup_action(s)
                )
                btn_quick_bak.pack(side="left", fill="x", expand=True, padx=(3, 0))

            act_row2 = tk.Frame(card, bg=BG_CARD, pady=2)
            act_row2.pack(fill="x")

            # Save Current into Slot button
            btn_save = ttk.Button(
                act_row2,
                text=t("slot_btn_save_here"),
                command=lambda s=slot_num: self._save_current_to_slot_action(s)
            )
            btn_save.pack(side="left", fill="x", expand=True, padx=(0, 3))

            # View Slot Backups button
            btn_bak = ttk.Button(
                act_row2,
                text=t("slot_btn_view_backups", count=backups_cnt),
                command=lambda s=slot_num: self._open_slot_backups_action(s)
            )
            btn_bak.pack(side="left", fill="x", expand=True, padx=(3, 3))

            # Rename button
            btn_ren = ttk.Button(
                act_row2,
                text="✏️",
                width=3,
                command=lambda s=slot_num: self._rename_slot_action(s)
            )
            btn_ren.pack(side="left", padx=(0, 2))

            # Clear Slot button
            btn_clear = ttk.Button(
                act_row2,
                text="🗑️",
                width=3,
                command=lambda s=slot_num: self._clear_slot_action(s)
            )
            btn_clear.pack(side="left")

    # =========================================================================
    # SLOT ACTIONS (Save, Load, Backups, Clear, Import, Rename)
    # =========================================================================
    def _rename_slot_action(self, slot_num):
        slot_info = save_slots.get_slot_info(slot_num)
        current_name = slot_info.get("custom_name", "")

        dialog = tk.Toplevel(self)
        dialog.title(t("slot_rename_dialog_title", slot=slot_num))
        dialog.geometry("400x150")
        dialog.minsize(360, 140)
        dialog.resizable(False, False)
        dialog.configure(bg=BG_DARK)
        dialog.transient(self)
        dialog.grab_set()

        dialog.update_idletasks()
        try:
            px = self.winfo_rootx() + (self.winfo_width() - 400) // 2
            py = self.winfo_rooty() + (self.winfo_height() - 150) // 2
            dialog.geometry(f"+{max(0, px)}+{max(0, py)}")
        except Exception:
            pass

        pad_f = tk.Frame(dialog, bg=BG_DARK, padx=16, pady=14)
        pad_f.pack(fill="both", expand=True)

        tk.Label(
            pad_f,
            text=t("slot_rename_dialog_prompt"),
            font=("Segoe UI", 9, "bold"),
            fg=ACCENT_GOLD,
            bg=BG_DARK
        ).pack(anchor="w", pady=(0, 6))

        entry_var = tk.StringVar(value=current_name)
        entry = ttk.Entry(pad_f, textvariable=entry_var, font=("Segoe UI", 10))
        entry.pack(fill="x", pady=(0, 12))
        entry.focus_set()
        entry.select_range(0, tk.END)

        btn_row = tk.Frame(pad_f, bg=BG_DARK)
        btn_row.pack(fill="x")

        def _do_save(event=None):
            val = entry_var.get().strip()
            save_slots.set_slot_custom_name(slot_num, val)
            dialog.destroy()
            self.refresh_slots_view()

        ttk.Button(btn_row, text=t("confirm"), style="Accent.TButton", command=_do_save).pack(side="left", padx=(0, 6))
        ttk.Button(btn_row, text=t("dialog_close_btn"), command=dialog.destroy).pack(side="left")

        entry.bind("<Return>", _do_save)
        dialog.bind("<Escape>", lambda e: dialog.destroy())

    def _save_current_to_slot_action(self, slot_num):
        if not self.save_json:
            messagebox.showwarning(t("notice"), t("mb_load_save_first"), parent=self)
            return

        slot_info = save_slots.get_slot_info(slot_num)
        if not slot_info["is_empty"]:
            if not messagebox.askyesno(
                t("confirm"),
                t("slot_confirm_save_to_slot", slot=slot_num),
                parent=self
            ):
                return

        try:
            ver = getattr(self, "version", 2)
            save_slots.save_current_to_slot(self.save_json, ver, slot_num)
            if hasattr(self, "set_current_active_slot_num"):
                self.set_current_active_slot_num(slot_num)
            self.refresh_slots_view()
            messagebox.showinfo(
                t("notice"),
                t("slot_saved_ok", slot=slot_num),
                parent=self
            )
        except Exception as e:
            messagebox.showerror(t("error"), str(e), parent=self)

    def _load_slot_action(self, slot_num):
        slot_info = save_slots.get_slot_info(slot_num)
        if slot_info["is_empty"]:
            messagebox.showwarning(t("notice"), t("slot_bak_empty"), parent=self)
            return

        if not self.save_path or not os.path.exists(self.save_path):
            messagebox.showwarning(t("notice"), t("mb_load_save_first"), parent=self)
            return

        p_name = slot_info.get("meta", {}).get("player_name", f"Slot {slot_num}")
        if not messagebox.askyesno(
            t("confirm"),
            t("slot_confirm_load", slot=slot_num, name=p_name),
            parent=self
        ):
            return

        ok, err_or_data, ver = save_slots.load_slot_to_active(slot_num, self.save_path)
        if not ok:
            messagebox.showerror(t("error"), str(err_or_data), parent=self)
            return

        if hasattr(self, "set_current_active_slot_num"):
            self.set_current_active_slot_num(slot_num)

        # Reload editor with newly active save
        self.load_save(self.save_path)
        self.refresh_slots_view()
        messagebox.showinfo(
            t("notice"),
            t("slot_loaded_ok", slot=slot_num),
            parent=self
        )

    def _quick_use_latest_backup_action(self, slot_num):
        slot_info = save_slots.get_slot_info(slot_num)
        latest = slot_info.get("latest_backup")
        if not latest:
            messagebox.showwarning(t("notice"), t("slot_bak_empty"), parent=self)
            return

        if not self.save_path or not os.path.exists(self.save_path):
            messagebox.showwarning(t("notice"), t("mb_load_save_first"), parent=self)
            return

        meta = latest.get("meta") or {}
        f_name = meta.get("fighter_name", "Fighter")
        flr = meta.get("max_floor", 1)
        d_str = latest.get("date_str", "")

        if not messagebox.askyesno(
            t("confirm"),
            t("slot_confirm_quick_restore", slot=slot_num, file=latest["filename"], fighter=f_name, floor=flr, date=d_str),
            parent=self
        ):
            return

        try:
            save_slots.restore_slot_backup(slot_num, latest["filename"], active_target_path=self.save_path)
            if hasattr(self, "set_current_active_slot_num"):
                self.set_current_active_slot_num(slot_num)
            self.load_save(self.save_path)
            self.refresh_slots_view()
            messagebox.showinfo(
                t("notice"),
                t("slot_quick_restore_ok", slot=slot_num, file=latest["filename"]),
                parent=self
            )
        except Exception as e:
            messagebox.showerror(t("error"), str(e), parent=self)

    def _open_slot_backups_action(self, slot_num):
        def on_restored(s_num, active_updated=False):
            if active_updated and self.save_path:
                self.load_save(self.save_path)
            self.refresh_slots_view()

        SlotBackupsDialog(
            self,
            slot_num=slot_num,
            active_save_path=getattr(self, "save_path", None),
            on_restored_cb=on_restored
        )

    def _clear_slot_action(self, slot_num):
        if not messagebox.askyesno(
            t("confirm"),
            t("slot_confirm_clear", slot=slot_num),
            parent=self
        ):
            return
        save_slots.clear_slot(slot_num)
        if hasattr(self, "get_current_active_slot_num") and self.get_current_active_slot_num() == slot_num:
            if hasattr(self, "set_current_active_slot_num"):
                self.set_current_active_slot_num(None)
        self.refresh_slots_view()
        messagebox.showinfo(t("notice"), t("slot_cleared_ok", slot=slot_num), parent=self)

    def _open_account_compatibility_dialog(self, initial_path=None):
        from ui.dialogs.account_compatibility_dialog import AccountCompatibilityDialog

        def on_applied(new_active_path=None, rebound_data=None):
            if new_active_path and hasattr(self, "load_save"):
                self.load_save(new_active_path)
            elif hasattr(self, "save_path") and self.save_path:
                self.load_save(self.save_path)
            self.refresh_slots_view()

        AccountCompatibilityDialog(
            self,
            active_save_path=getattr(self, "save_path", None),
            active_save_dict=getattr(self, "save_json", None),
            initial_file_path=initial_path,
            on_applied_cb=on_applied
        )

    def _import_file_to_slot_action(self, slot_num):
        fn = filedialog.askopenfilename(
            title=t("slot_btn_import_file"),
            filetypes=[("LET IT DIE Save", "*.sav"), ("All Files", "*.*")],
            parent=self
        )
        if not fn:
            return
        try:
            import core.account_rebind as account_rebind
            data, ver = save_io.decompress_save(fn)
            my_ident = account_rebind.detect_active_account_identity(
                active_save_dict=getattr(self, "save_json", None),
                active_save_path=getattr(self, "save_path", None)
            )
            my_steam = my_ident.get("steam_id", "")
            foreign_ident = account_rebind.extract_save_identity(data)
            foreign_steam = foreign_ident.get("steam_id", "")

            target_steam = None
            target_name = None

            if my_steam and foreign_steam and my_steam != "---" and foreign_steam != "---" and foreign_steam != my_steam:
                # Ask user if they want to make it compatible
                res = messagebox.askyesnocancel(
                    t("confirm"),
                    t(
                        "slot_import_foreign_confirm",
                        file=os.path.basename(fn),
                        foreign_steam=foreign_steam,
                        foreign_name=foreign_ident.get("player_name", "Senpai"),
                        my_steam=my_steam,
                        my_name=my_ident.get("player_name", "Senpai")
                    ),
                    parent=self
                )
                if res is None:  # User clicked cancel
                    return
                if res is True:  # Yes, make compatible
                    target_steam = my_steam

            save_slots.import_save_file_to_slot(fn, slot_num, target_steam_id=target_steam, target_player_name=target_name)
            self.refresh_slots_view()
            messagebox.showinfo(t("notice"), t("slot_import_success", slot=slot_num), parent=self)
        except Exception as e:
            messagebox.showerror(t("error"), str(e), parent=self)

    # =========================================================================
    # 2. TOOLS & CACHE SUB-TAB (JSON Tools, Repairs, CDN Asset Cache)
    # =========================================================================
    def _build_tools_cache_subtab(self):
        self.tools_scroll = scroll = ScrollableFrame(self.subtab_tools)
        scroll.pack(fill="both", expand=True)
        container = scroll.content

        container.columnconfigure(0, weight=1)
        container.columnconfigure(1, weight=1)

        # Left: JSON Tools & Links
        box_tools = ttk.LabelFrame(container, text=t("bak_tools_title"), padding=12)
        box_tools.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)

        ttk.Label(box_tools, text=t("bak_json_lbl"), font=("Segoe UI", 9, "bold"), foreground=ACCENT_GOLD).pack(anchor="w", pady=2)
        json_f = ttk.Frame(box_tools)
        json_f.pack(fill="x", pady=4)
        ttk.Button(json_f, text=t("bak_export_json"), command=self.export_json).pack(side="left", padx=2, fill="x", expand=True)
        ttk.Button(json_f, text=t("bak_import_json"), command=self.import_json).pack(side="left", padx=2, fill="x", expand=True)

        ttk.Separator(box_tools, orient="horizontal").pack(fill="x", pady=8)
        ttk.Label(box_tools, text="🔄 " + t("rebind_tool_section_title"), font=("Segoe UI", 9, "bold"), foreground=ACCENT_GOLD).pack(anchor="w", pady=2)
        ttk.Label(box_tools, text=t("rebind_tool_section_desc"), font=("Segoe UI", 8), foreground=FG_MUTED).pack(anchor="w", pady=2)
        ttk.Button(box_tools, text="🔄 " + t("rebind_tool_open_btn"), style="Accent.TButton", command=self._open_account_compatibility_dialog).pack(anchor="w", pady=4)

        ttk.Separator(box_tools, orient="horizontal").pack(fill="x", pady=8)
        ttk.Label(box_tools, text=t("bak_links_lbl"), font=("Segoe UI", 9, "bold"), foreground=ACCENT_GOLD).pack(anchor="w", pady=2)
        ttk.Label(box_tools, text=t("bak_links_txt"), font=("Segoe UI", 8), foreground=FG_MUTED).pack(anchor="w", pady=2)

        # Right: Optional Advanced Repairs
        box_rep = ttk.LabelFrame(container, text=t("adv_repairs_title"), padding=12)
        box_rep.grid(row=0, column=1, sticky="nsew", padx=6, pady=6)

        ttk.Label(box_rep, text=t("adv_repair_tdm_btn") + " / " + t("adv_repair_fighters_btn"), font=("Segoe UI", 9, "bold"), foreground=ACCENT_GOLD).pack(anchor="w", pady=2)
        rep_f = ttk.Frame(box_rep)
        rep_f.pack(fill="x", pady=6)
        ttk.Button(rep_f, text=t("adv_repair_tdm_btn"), command=self._repair_tdm_action).pack(side="left", padx=2, fill="x", expand=True)
        ttk.Button(rep_f, text=t("adv_repair_fighters_btn"), command=self._repair_fighters_action).pack(side="left", padx=2, fill="x", expand=True)

        # Row 1: CDN Assets & Cache Manager
        box_assets = ttk.LabelFrame(container, text=t("asset_box_title"), padding=12)
        box_assets.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=6, pady=6)

        ttk.Label(box_assets, text=t("asset_box_desc"), font=("Segoe UI", 8), foreground=FG_MUTED).pack(anchor="w", pady=2)

        self.asset_stats_lbl = ttk.Label(box_assets, text="...", font=("Segoe UI", 9, "bold"), foreground=ACCENT_GOLD)
        self.asset_stats_lbl.pack(anchor="w", pady=4)

        self.asset_pbar = ttk.Progressbar(box_assets, orient="horizontal", mode="determinate")
        self.asset_pbar.pack(fill="x", pady=4)
        self.asset_pbar_lbl = ttk.Label(box_assets, text="", font=("Segoe UI", 8), foreground=FG_MUTED)
        self.asset_pbar_lbl.pack(anchor="w", pady=1)

        btn_assets_f = ttk.Frame(box_assets)
        btn_assets_f.pack(fill="x", pady=4)
        self.asset_dl_btn = ttk.Button(btn_assets_f, text=t("asset_download_all_btn"), style="Accent.TButton", command=self._download_all_cdn_assets)
        self.asset_dl_btn.pack(side="left", padx=2)
        ttk.Button(btn_assets_f, text=t("asset_clear_cache_btn"), command=self._clear_cdn_cache).pack(side="left", padx=2)
        ttk.Button(btn_assets_f, text="🔄 " + t("reload"), command=self.update_cache_stats).pack(side="left", padx=2)

        self.update_cache_stats()

    def update_cache_stats(self):
        if hasattr(self, "asset_manager"):
            stats = self.asset_manager.get_cache_stats()
            self.asset_stats_lbl.config(text=t("asset_cache_stats", count=stats["count"], size=stats["size_mb"]))

    def _download_all_cdn_assets(self):
        if not hasattr(self, "asset_manager"):
            return

        asset_paths = set()
        if hasattr(self, "icon_map") and isinstance(self.icon_map, dict):
            for cat in self.icon_map.values():
                if isinstance(cat, dict):
                    for p in cat.values():
                        if p:
                            asset_paths.add(p)
        if hasattr(self.asset_manager, "manifest") and self.asset_manager.manifest:
            for p in self.asset_manager.manifest.values():
                if p and "/" in p:
                    asset_paths.add(p)

        if not asset_paths:
            messagebox.showinfo(t("notice"), t("asset_no_downloads"))
            return

        total = len(asset_paths)
        self.asset_dl_btn.config(state="disabled")
        self.asset_pbar.config(maximum=total, value=0)
        self.asset_pbar_lbl.config(text=t("asset_downloading", current=0, total=total))

        def on_progress(cur, tot, f):
            def _ui():
                self.asset_pbar.config(value=cur)
                self.asset_pbar_lbl.config(text=t("asset_downloading", current=cur, total=tot))
            self.after(0, _ui)

        def on_complete(downloaded, errors):
            def _ui():
                self.asset_dl_btn.config(state="normal")
                self.update_cache_stats()
                self.asset_pbar_lbl.config(text="")
                messagebox.showinfo(t("notice"), t("asset_download_done", downloaded=downloaded))
            self.after(0, _ui)

        self.asset_manager.download_all_assets_async(list(asset_paths), progress_callback=on_progress, completion_callback=on_complete)

    def _clear_cdn_cache(self):
        if not hasattr(self, "asset_manager"):
            return
        if messagebox.askyesno(t("notice"), t("asset_confirm_clear")):
            self.asset_manager.clear_cache()
            self.update_cache_stats()
            messagebox.showinfo(t("notice"), t("asset_cache_cleared"))

    def refresh_backups_list(self):
        """Called upon save reload or tab switch."""
        self.update_cache_stats()
        self.refresh_slots_view()

    def _repair_tdm_action(self):
        if not self.save_json:
            return
        if messagebox.askyesno(t("notice"), t("adv_confirm_tdm_repair")):
            import modifiers
            modifiers.repair_and_sanitize_tdm(self.save_json)
            self._auto_save()
            self.refresh_all_views()
            messagebox.showinfo(t("notice"), t("adv_tdm_repaired"))

    def _repair_fighters_action(self):
        if not self.save_json:
            return
        if messagebox.askyesno(t("notice"), t("adv_confirm_fighter_repair")):
            import modifiers
            modifiers.sanitize_fighters(self.save_json)
            self._auto_save()
            self.refresh_all_views()
            messagebox.showinfo(t("notice"), t("adv_fighters_repaired"))
