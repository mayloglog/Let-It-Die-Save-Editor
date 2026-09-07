# -*- coding: utf-8 -*-
"""
Account Compatibility & Foreign Save Re-binding Dialog for LET IT DIE Save Editor.
Allows players to take saves from other users, re-bind them to their own Steam account,
clean session tokens, and activate them directly into Steam, slots, or external files.
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

import save_io
import core.save_slots as save_slots
import core.account_rebind as account_rebind
from i18n import t
from ui.theme import (
    BG_DARK, BG_PANEL, BG_CARD, FG_TEXT, FG_MUTED,
    ACCENT_GOLD, ACCENT_CYAN, ACCENT_GREEN, ACCENT_RED
)


class AccountCompatibilityDialog(tk.Toplevel):
    """Dialog to inspect and re-bind foreign save files to the user's Steam account."""

    def __init__(
        self,
        parent,
        active_save_path=None,
        active_save_dict=None,
        initial_file_path=None,
        on_applied_cb=None
    ):
        super().__init__(parent)
        self.parent = parent
        self.active_save_path = active_save_path
        self.active_save_dict = active_save_dict
        self.on_applied_cb = on_applied_cb

        self.title(t("rebind_dialog_title"))
        self.geometry("780x600")
        self.minsize(720, 530)
        self.configure(bg=BG_DARK)
        self.transient(parent)
        self.grab_set()

        # Detect user's current account identity
        self.my_ident = account_rebind.detect_active_account_identity(
            active_save_dict=self.active_save_dict,
            active_save_path=self.active_save_path
        )

        self._current_src_path = initial_file_path or ""
        self._src_data = None
        self._src_ident = None
        self._src_ver = 2

        self._build_ui()

        if self._current_src_path and os.path.exists(self._current_src_path):
            self._load_source_file(self._current_src_path)

        # Center on parent
        self.update_idletasks()
        try:
            px = parent.winfo_rootx() + (parent.winfo_width() - self.winfo_width()) // 2
            py = parent.winfo_rooty() + (parent.winfo_height() - self.winfo_height()) // 2
            self.geometry(f"+{max(0, px)}+{max(0, py)}")
        except Exception:
            pass

    def _build_ui(self):
        # Header
        hdr = tk.Frame(self, bg=BG_PANEL, padx=14, pady=10)
        hdr.pack(fill="x")

        tk.Label(
            hdr,
            text=f"🔄 {t('rebind_header_title')}",
            font=("Segoe UI", 12, "bold"),
            fg=ACCENT_GOLD,
            bg=BG_PANEL
        ).pack(anchor="w")

        tk.Label(
            hdr,
            text=t("rebind_header_subtitle"),
            font=("Segoe UI", 8),
            fg=FG_MUTED,
            bg=BG_PANEL
        ).pack(anchor="w", pady=(2, 0))

        # Main Body
        body = tk.Frame(self, bg=BG_DARK, padx=14, pady=10)
        body.pack(fill="both", expand=True)

        # Source File Picker Card
        picker_card = tk.Frame(body, bg=BG_CARD, padx=10, pady=8)
        picker_card.pack(fill="x", pady=(0, 10))

        tk.Label(
            picker_card,
            text=t("rebind_lbl_source_file"),
            font=("Segoe UI", 9, "bold"),
            fg=FG_TEXT,
            bg=BG_CARD
        ).pack(anchor="w")

        pick_row = tk.Frame(picker_card, bg=BG_CARD, pady=4)
        pick_row.pack(fill="x")

        self.src_path_var = tk.StringVar(value=self._current_src_path)
        self.entry_src_path = ttk.Entry(pick_row, textvariable=self.src_path_var, font=("Segoe UI", 8))
        self.entry_src_path.pack(side="left", fill="x", expand=True, padx=(0, 6))

        ttk.Button(
            pick_row,
            text=t("browse"),
            command=self._browse_source_action
        ).pack(side="left", padx=(0, 4))

        if self.active_save_path and os.path.exists(self.active_save_path):
            ttk.Button(
                pick_row,
                text=t("rebind_btn_use_current"),
                command=lambda: self._load_source_file(self.active_save_path)
            ).pack(side="left")

        # Side-by-Side Comparison Container
        cmp_container = tk.Frame(body, bg=BG_DARK)
        cmp_container.pack(fill="both", expand=True)

        # Left Column: Foreign / Source Save
        self.src_col = tk.Frame(cmp_container, bg=BG_CARD, padx=10, pady=8, highlightbackground=ACCENT_CYAN, highlightthickness=1)
        self.src_col.pack(side="left", fill="both", expand=True, padx=(0, 5))

        tk.Label(
            self.src_col,
            text=f"📥 {t('rebind_col_source_title')}",
            font=("Segoe UI", 10, "bold"),
            fg=ACCENT_CYAN,
            bg=BG_CARD
        ).pack(anchor="w", pady=(0, 6))

        self.lbl_src_details = tk.Label(
            self.src_col,
            text=t("rebind_src_no_file_loaded"),
            font=("Segoe UI", 8),
            fg=FG_TEXT,
            bg=BG_CARD,
            justify="left"
        )
        self.lbl_src_details.pack(anchor="w", fill="both", expand=True)

        # Right Column: Target / User Profile
        self.dst_col = tk.Frame(cmp_container, bg=BG_CARD, padx=10, pady=8, highlightbackground=ACCENT_GOLD, highlightthickness=1)
        self.dst_col.pack(side="right", fill="both", expand=True, padx=(5, 0))

        tk.Label(
            self.dst_col,
            text=f"🎯 {t('rebind_col_target_title')}",
            font=("Segoe UI", 10, "bold"),
            fg=ACCENT_GOLD,
            bg=BG_CARD
        ).pack(anchor="w", pady=(0, 6))

        # Target Steam ID
        tk.Label(
            self.dst_col,
            text=t("rebind_lbl_target_steam_id"),
            font=("Segoe UI", 8, "bold"),
            fg=FG_TEXT,
            bg=BG_CARD
        ).pack(anchor="w")

        self.target_steam_var = tk.StringVar(value=self.my_ident["steam_id"])
        self.entry_steam_id = ttk.Entry(self.dst_col, textvariable=self.target_steam_var, font=("Segoe UI", 9))
        self.entry_steam_id.pack(fill="x", pady=(2, 6))

        # Target Senpai Name
        tk.Label(
            self.dst_col,
            text=t("rebind_lbl_target_name"),
            font=("Segoe UI", 8, "bold"),
            fg=FG_TEXT,
            bg=BG_CARD
        ).pack(anchor="w")

        self.keep_orig_name_var = tk.BooleanVar(value=False)
        self.target_name_var = tk.StringVar(value=self.my_ident["player_name"])

        self.entry_player_name = ttk.Entry(self.dst_col, textvariable=self.target_name_var, font=("Segoe UI", 9))
        self.entry_player_name.pack(fill="x", pady=(2, 4))

        self.chk_keep_name = ttk.Checkbutton(
            self.dst_col,
            text=t("rebind_chk_keep_orig_name"),
            variable=self.keep_orig_name_var,
            command=self._on_toggle_keep_name
        )
        self.chk_keep_name.pack(anchor="w", pady=(0, 6))

        # Options: Clear session & Harmonize UID
        self.clear_session_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            self.dst_col,
            text=t("rebind_chk_clear_session"),
            variable=self.clear_session_var
        ).pack(anchor="w", pady=(0, 3))

        self.harmonize_uid_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            self.dst_col,
            text=t("rebind_chk_harmonize_uid"),
            variable=self.harmonize_uid_var
        ).pack(anchor="w", pady=(0, 3))

        # Status / Warning Banner
        self.status_banner = tk.Label(
            body,
            text=t("rebind_status_ready"),
            font=("Segoe UI", 8, "italic"),
            fg=FG_MUTED,
            bg=BG_DARK,
            anchor="w"
        )
        self.status_banner.pack(fill="x", pady=(8, 0))

        # Bottom Action Bar
        btn_bar = tk.Frame(self, bg=BG_PANEL, padx=14, pady=10)
        btn_bar.pack(fill="x")

        self.btn_apply_steam = ttk.Button(
            btn_bar,
            text=t("rebind_btn_apply_steam"),
            style="Accent.TButton",
            command=self._apply_to_steam_action
        )
        self.btn_apply_steam.pack(side="left", padx=(0, 4))

        self.btn_apply_slot = ttk.Button(
            btn_bar,
            text=t("rebind_btn_apply_slot"),
            command=self._apply_to_slot_action
        )
        self.btn_apply_slot.pack(side="left", padx=(0, 4))

        self.btn_export = ttk.Button(
            btn_bar,
            text=t("rebind_btn_export_file"),
            command=self._export_file_action
        )
        self.btn_export.pack(side="left", padx=(0, 4))

        ttk.Button(
            btn_bar,
            text=t("dialog_close_btn"),
            command=self.destroy
        ).pack(side="right")

    def _on_toggle_keep_name(self):
        if self.keep_orig_name_var.get() and self._src_ident:
            self.entry_player_name.config(state="disabled")
        else:
            self.entry_player_name.config(state="normal")

    def _browse_source_action(self):
        fn = filedialog.askopenfilename(
            title=t("rebind_browse_title"),
            filetypes=[("LET IT DIE Save", "*.sav"), ("All Files", "*.*")],
            parent=self
        )
        if fn:
            self._load_source_file(fn)

    def _load_source_file(self, file_path):
        if not os.path.exists(file_path):
            messagebox.showerror(t("error"), f"File not found: {file_path}", parent=self)
            return
        try:
            data, ver = save_io.decompress_save(file_path)
            self._src_data = data
            self._src_ver = ver
            self._current_src_path = file_path
            self.src_path_var.set(file_path)
            self._src_ident = account_rebind.extract_save_identity(data)

            # Update Source Details text
            fn = os.path.basename(file_path)
            sz_kb = os.path.getsize(file_path) // 1024
            meta = save_slots.extract_save_metadata(data)

            f_name = meta.get("fighter_name", "Fighter")
            f_class = meta.get("fighter_class", "BAL")
            f_grade = meta.get("fighter_grade", 1)
            f_lvl = meta.get("fighter_lvl", 1)
            flr = meta.get("max_floor", 1)
            kc = meta.get("kill_coins", 0)
            dm = meta.get("death_metals", 0)

            orig_steam = self._src_ident["steam_id"]
            orig_name = self._src_ident["player_name"]
            has_tokens = "⚠️ " + t("rebind_has_session_tokens") if self._src_ident["has_session_tokens"] else "✅ " + t("rebind_no_session_tokens")

            details_text = (
                f"📁 {fn} ({sz_kb} KB)\n\n"
                f"🆔 Steam ID: {orig_steam}\n"
                f"👤 Senpai: {orig_name} (UID: {self._src_ident['uid']})\n"
                f"🥋 {f_name} ({f_class} ★{f_grade} Lv.{f_lvl})\n"
                f"🗼 Piso: {flr}  |  🪙 {kc:,} KC  |  💎 {dm:,} DM\n\n"
                f"{has_tokens}"
            )
            self.lbl_src_details.config(text=details_text)

            # Update status banner based on compatibility
            target_steam = self.target_steam_var.get().strip()
            if orig_steam == target_steam:
                self.status_banner.config(
                    text=t("rebind_status_already_compatible"),
                    fg=ACCENT_GREEN
                )
            else:
                self.status_banner.config(
                    text=t("rebind_status_needs_rebind", foreign=orig_steam, target=target_steam),
                    fg=ACCENT_GOLD
                )

        except Exception as e:
            messagebox.showerror(t("error"), f"Failed to read save: {e}", parent=self)

    def _prepare_rebound_data(self):
        if not self._src_data:
            messagebox.showwarning(t("notice"), t("rebind_warn_no_source"), parent=self)
            return None

        target_steam = self.target_steam_var.get().strip()
        if not target_steam:
            messagebox.showwarning(t("notice"), t("rebind_warn_no_steam_id"), parent=self)
            return None

        # Determine target player name
        if self.keep_orig_name_var.get() and self._src_ident:
            target_name = self._src_ident["player_name"]
        else:
            target_name = self.target_name_var.get().strip() or self._src_ident["player_name"]

        target_uid = self.my_ident["uid"] if self.harmonize_uid_var.get() else None
        clear_tokens = self.clear_session_var.get()

        import copy
        rebound = copy.deepcopy(self._src_data)
        account_rebind.rebind_save_to_account(
            rebound,
            target_steam_id=target_steam,
            target_player_name=target_name,
            target_uid=target_uid,
            clear_session_tokens=clear_tokens
        )
        return rebound

    def _apply_to_steam_action(self):
        rebound = self._prepare_rebound_data()
        if not rebound:
            return

        target_path = self.active_save_path or save_io.get_default_save_path()
        if not target_path:
            messagebox.showerror(t("error"), t("mb_load_save_first"), parent=self)
            return

        target_steam = self.target_steam_var.get().strip()
        if not messagebox.askyesno(
            t("confirm"),
            t("rebind_confirm_apply_steam", steam=target_steam, path=target_path),
            parent=self
        ):
            return

        try:
            # Preventative backup of current active save
            if os.path.exists(target_path):
                save_io.create_backup(target_path)

            save_io.save_to_file(rebound, target_path, version=self._src_ver, make_backup=False)

            if self.on_applied_cb:
                self.on_applied_cb(target_path, rebound)

            messagebox.showinfo(
                t("notice"),
                t("rebind_success_applied_steam", steam=target_steam),
                parent=self
            )
            self.destroy()
        except Exception as e:
            messagebox.showerror(t("error"), str(e), parent=self)

    def _apply_to_slot_action(self):
        rebound = self._prepare_rebound_data()
        if not rebound:
            return

        # Pop up quick slot picker
        slot_dialog = tk.Toplevel(self)
        slot_dialog.title(t("rebind_choose_slot_title"))
        slot_dialog.geometry("360x220")
        slot_dialog.minsize(320, 200)
        slot_dialog.configure(bg=BG_DARK)
        slot_dialog.transient(self)
        slot_dialog.grab_set()

        slot_dialog.update_idletasks()
        try:
            px = self.winfo_rootx() + (self.winfo_width() - 360) // 2
            py = self.winfo_rooty() + (self.winfo_height() - 220) // 2
            slot_dialog.geometry(f"+{max(0, px)}+{max(0, py)}")
        except Exception:
            pass

        tk.Label(
            slot_dialog,
            text=t("rebind_choose_slot_prompt"),
            font=("Segoe UI", 9, "bold"),
            fg=ACCENT_GOLD,
            bg=BG_DARK
        ).pack(pady=(12, 6))

        slots = save_slots.get_all_slots()
        slot_combo_values = []
        for s in slots:
            s_num = s["slot_num"]
            c_name = s.get("custom_name")
            p_name = s.get("meta", {}).get("player_name", "Vacío") if not s["is_empty"] else t("slot_badge_empty")
            txt = f"Slot {s_num:02d}: {c_name if c_name else p_name}"
            slot_combo_values.append(txt)

        sel_slot_var = tk.StringVar(value=slot_combo_values[0])
        combo = ttk.Combobox(slot_dialog, values=slot_combo_values, textvariable=sel_slot_var, state="readonly", width=30)
        combo.pack(pady=8)

        def do_save_slot():
            idx = combo.current()
            if idx < 0:
                idx = 0
            slot_num = idx + 1
            try:
                save_slots.save_current_to_slot(rebound, self._src_ver, slot_num)
                slot_dialog.destroy()
                messagebox.showinfo(
                    t("notice"),
                    t("rebind_success_saved_slot", slot=slot_num),
                    parent=self
                )
                if self.on_applied_cb:
                    self.on_applied_cb(None, rebound)
            except Exception as e:
                messagebox.showerror(t("error"), str(e), parent=slot_dialog)

        btn_f = tk.Frame(slot_dialog, bg=BG_DARK)
        btn_f.pack(pady=10)

        ttk.Button(btn_f, text=t("save"), style="Accent.TButton", command=do_save_slot).pack(side="left", padx=4)
        ttk.Button(btn_f, text=t("cancel"), command=slot_dialog.destroy).pack(side="left", padx=4)

    def _export_file_action(self):
        rebound = self._prepare_rebound_data()
        if not rebound:
            return

        target_steam = self.target_steam_var.get().strip()
        default_fn = f"{target_steam}.sav" if target_steam and target_steam != "---" else "savedata.sav"

        fn = filedialog.asksaveasfilename(
            title=t("rebind_btn_export_file"),
            initialfile=default_fn,
            defaultextension=".sav",
            filetypes=[("LET IT DIE Save", "*.sav"), ("All Files", "*.*")],
            parent=self
        )
        if not fn:
            return

        try:
            save_io.save_to_file(rebound, fn, version=self._src_ver, make_backup=False)
            messagebox.showinfo(
                t("notice"),
                t("rebind_success_exported", path=fn),
                parent=self
            )
        except Exception as e:
            messagebox.showerror(t("error"), str(e), parent=self)
