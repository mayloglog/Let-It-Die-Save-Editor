# -*- coding: utf-8 -*-
"""
Materials & R&D Tab Mixin for LET IT DIE Save Editor.
"""

import os
import sys
import json
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

import modifiers
import i18n
from i18n import t
from ui.theme import ACCENT_GOLD, ACCENT_CYAN, FG_MUTED
from ui.components import ScrollableFrame
from game_data import SPECIAL_MUSHROOMS, SPECIAL_BEASTS

if getattr(sys, "frozen", False):
    exe_dir = os.path.dirname(os.path.abspath(sys.executable))
    mei_dir = getattr(sys, "_MEIPASS", exe_dir)
    BASE_DIR = exe_dir if os.path.isdir(os.path.join(exe_dir, "icons")) else mei_dir
else:
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

ICONS_DIR = os.path.join(BASE_DIR, "icons")

CANONICAL_MATERIAL_CATEGORIES = [
    ("ALL", "mat_cat_all"),
    ("ALUMINUM", "mat_cat_aluminum"),
    ("COPPER", "mat_cat_copper"),
    ("IRON_STEEL", "mat_cat_iron_steel"),
    ("OIL", "mat_cat_oil"),
    ("WOOD", "mat_cat_wood"),
    ("CLOTH", "mat_cat_cloth"),
    ("DOD", "mat_cat_dod"),
    ("WAR", "mat_cat_war"),
    ("CW", "mat_cat_cw"),
    ("MILK", "mat_cat_milk"),
    ("BOSS", "mat_cat_boss"),
    ("JACKAL_TENGOKU", "mat_cat_jackal_tengoku"),
    ("STEROIDS", "mat_cat_steroids"),
    ("MUSHROOMS_BEASTS", "mat_cat_mushrooms_beasts"),
    ("MUSHROOMS", "mat_cat_mushrooms"),
    ("BEASTS", "mat_cat_beasts"),
]


class MaterialsTabMixin:
    """Provides methods for constructing and handling the Materials R&D Tab."""

    def _build_materials_tab(self):
        paned = ttk.PanedWindow(self.tab_materials, orient="horizontal")
        paned.pack(fill="both", expand=True)
        
        left_box = ttk.Frame(paned)
        paned.add(left_box, weight=3)
        
        # Row 1: Search, Category, Stock Filter, Rarity
        ctrl_frame = ttk.Frame(left_box)
        ctrl_frame.pack(fill="x", pady=2)
        
        ttk.Label(ctrl_frame, text=t("mat_search")).pack(side="left", padx=2)
        self.mat_search_var = tk.StringVar()
        self.mat_search_var.trace_add("write", lambda *args: self.filter_materials_list())
        ttk.Entry(ctrl_frame, textvariable=self.mat_search_var, width=11).pack(side="left", padx=2)
        
        self._mat_cat_map = {t(k): code for code, k in CANONICAL_MATERIAL_CATEGORIES}
        cats = list(self._mat_cat_map.keys())
        self.mat_cat_var = tk.StringVar(value=cats[0] if cats else t("mat_cat_all"))
        ttk.Label(ctrl_frame, text=t("mat_cat_lbl")).pack(side="left", padx=(4, 1))
        cb_cat = ttk.Combobox(ctrl_frame, textvariable=self.mat_cat_var, values=cats, state="readonly", width=16)
        cb_cat.pack(side="left", padx=2)
        cb_cat.bind("<<ComboboxSelected>>", lambda e: self.filter_materials_list())

        ttk.Label(ctrl_frame, text=t("mat_stock_lbl")).pack(side="left", padx=(4, 1))
        self._stock_filter_map = {
            t("mat_all"): "ALL",
            t("mat_in_stock"): "IN_STOCK",
            t("mat_low_stock"): "LOW_STOCK",
            t("mat_out_stock"): "OUT_OF_STOCK"
        }
        self.mat_stock_filter_var = tk.StringVar(value=t("mat_all"))
        cb_stock = ttk.Combobox(ctrl_frame, textvariable=self.mat_stock_filter_var, values=list(self._stock_filter_map.keys()), state="readonly", width=11)
        cb_stock.pack(side="left", padx=2)
        cb_stock.bind("<<ComboboxSelected>>", lambda e: self.filter_materials_list())

        ttk.Label(ctrl_frame, text=t("mat_rarity_lbl")).pack(side="left", padx=(4, 1))
        self.mat_rarity_filter_var = tk.StringVar(value=t("decal_all"))
        cb_mrarity = ttk.Combobox(ctrl_frame, textvariable=self.mat_rarity_filter_var, values=[t("decal_all"), "1★", "2★", "3★", "4★", "5★", "6★", "7★", "8★"], state="readonly", width=5)
        cb_mrarity.pack(side="left", padx=2)
        cb_mrarity.bind("<<ComboboxSelected>>", lambda e: self.filter_materials_list())

        # Row 2: Pisos de la Torre (Wiki Tower Sections Quick Bar) & Actions
        ctrl_frame_floors = ttk.Frame(left_box)
        ctrl_frame_floors.pack(fill="x", pady=2)
        
        btn_all_mat = ttk.Button(ctrl_frame_floors, text=t("mat_max_stock_btn"), style="Accent.TButton", command=self.max_all_materials_preset)
        btn_all_mat.pack(side="right", padx=1)

        btn_open_storage = ttk.Button(ctrl_frame_floors, text="📦 Coin Locker", command=self._open_storage_manager)
        btn_open_storage.pack(side="right", padx=1)

        ttk.Label(ctrl_frame_floors, text=t("mat_floors_lbl"), font=("Segoe UI", 8, "bold"), foreground=ACCENT_GOLD).pack(side="left", padx=2)
        self.mat_floor_filter = tk.StringVar(value="TODOS")
        
        floor_buttons = [
            (t("mat_floor_all"), "TODOS"),
            ("1-10F", "1_10"),
            ("11-20F", "11_20"),
            ("21-30F", "21_30"),
            ("31-40F", "31_40"),
            ("41-50F", "41_50"),
            ("51F+", "51_PLUS")
        ]
        for btn_text, mode in floor_buttons:
            ttk.Button(ctrl_frame_floors, text=btn_text, command=lambda m=mode: self._set_mat_floor_filter(m)).pack(side="left", padx=1)
        
        # Materials Treeview
        mat_tree_frame = ttk.Frame(left_box)
        mat_tree_frame.pack(fill="both", expand=True, pady=4)
        mat_scroll = ttk.Scrollbar(mat_tree_frame, orient="vertical")
        self.mat_tree = ttk.Treeview(mat_tree_frame, columns=("stock", "rarity", "category", "id"), show="tree headings", height=16, yscrollcommand=mat_scroll.set)
        mat_scroll.config(command=self.mat_tree.yview)
        self.mat_tree.heading("#0", text=t("decal_col_icon"))
        self.mat_tree.heading("stock", text=t("bp_col_storage"))
        self.mat_tree.heading("rarity", text=t("decal_col_rare"))
        self.mat_tree.heading("category", text=t("decal_col_type"))
        self.mat_tree.heading("id", text=t("wm_col_code"))
        
        self.mat_tree.column("#0", width=280)
        self.mat_tree.column("stock", width=90, anchor="center")
        self.mat_tree.column("rarity", width=70, anchor="center")
        self.mat_tree.column("category", width=130)
        self.mat_tree.column("id", width=120)
        
        mat_scroll.pack(side="right", fill="y")
        self.mat_tree.pack(side="left", fill="both", expand=True)
        self.mat_tree.bind("<<TreeviewSelect>>", self._on_mat_select)
        self.mat_tree.bind("<Double-1>", self._edit_selected_material_count)
        
        self.mat_tree.tag_configure("tag_in_stock", foreground=ACCENT_GOLD)
        self.mat_tree.tag_configure("tag_out_of_stock", foreground=FG_MUTED)
        
        # Right Material Card (Wiki Showcase)
        mat_card_container = ttk.LabelFrame(paned, text=t("mat_card_title"), padding=4)
        paned.add(mat_card_container, weight=2)
        self.materials_scroll = scroll_mat = ScrollableFrame(mat_card_container)
        scroll_mat.pack(fill="both", expand=True)
        self.mat_card = scroll_mat.content
        
        self.mat_art_lbl = ttk.Label(self.mat_card)
        self.mat_art_lbl.pack(pady=6)
        
        self.mat_title_lbl = ttk.Label(self.mat_card, text=t("mat_select_prompt"), font=("Segoe UI", 12, "bold"), foreground=ACCENT_GOLD, wraplength=260, justify="center")
        self.mat_title_lbl.pack(pady=2)
        
        self.mat_type_lbl = ttk.Label(self.mat_card, text="---", font=("Segoe UI", 9), foreground=FG_MUTED)
        self.mat_type_lbl.pack(pady=2)
        
        self.mat_stock_lbl = ttk.Label(self.mat_card, text=t("mat_none_in_storage"), font=("Segoe UI", 10, "bold"), foreground=ACCENT_CYAN)
        self.mat_stock_lbl.pack(pady=4)
        
        self.mat_desc_lbl = ttk.Label(self.mat_card, text=t("mat_desc_default"), font=("Segoe UI", 9), foreground=FG_MUTED, wraplength=260, justify="center")
        self.mat_desc_lbl.pack(pady=6)
        
        # Quantity controls
        qty_f = ttk.Frame(self.mat_card)
        qty_f.pack(pady=4)
        ttk.Label(qty_f, text=t("mat_set_qty_lbl")).pack(side="left", padx=2)
        self.mat_qty_entry_var = tk.StringVar(value="50")
        ttk.Entry(qty_f, textvariable=self.mat_qty_entry_var, width=6, justify="center").pack(side="left", padx=4)
        ttk.Button(qty_f, text=t("mat_set_btn"), style="Accent.TButton", command=self._set_selected_mat_qty).pack(side="left", padx=2)
        
        quick_m_box = ttk.Frame(self.mat_card)
        quick_m_box.pack(fill="x", pady=4)
        ttk.Button(quick_m_box, text="+10", command=lambda: self._quick_add_material_qty(10)).pack(side="left", fill="x", expand=True, padx=1)
        ttk.Button(quick_m_box, text="+50", command=lambda: self._quick_add_material_qty(50)).pack(side="left", fill="x", expand=True, padx=1)
        ttk.Button(quick_m_box, text="+100", command=lambda: self._quick_add_material_qty(100)).pack(side="left", fill="x", expand=True, padx=1)

        # Capacity expansion frame
        cap_frame = ttk.LabelFrame(self.mat_card, text=t("mat_locker_cap_title"), padding=8)
        cap_frame.pack(fill="x", pady=(10, 0))
        
        self.mat_cap_indicator_lbl = ttk.Label(cap_frame, text=t("mat_cap_initial_indicator"), font=("Segoe UI", 9, "bold"))
        self.mat_cap_indicator_lbl.pack(anchor="w", pady=2)
        
        exp_row1 = ttk.Frame(cap_frame)
        exp_row1.pack(fill="x", pady=2)
        ttk.Button(exp_row1, text=t("mat_expand_500"), command=lambda: self._expand_coin_locker_add(500)).pack(side="left", fill="x", expand=True, padx=1)
        ttk.Button(exp_row1, text=t("mat_expand_1000"), command=lambda: self._expand_coin_locker_add(1000)).pack(side="left", fill="x", expand=True, padx=1)
        
        exp_row2 = ttk.Frame(cap_frame)
        exp_row2.pack(fill="x", pady=2)
        ttk.Button(exp_row2, text=t("mat_expand_max"), command=lambda: self._expand_coin_locker(6000)).pack(side="left", fill="x", expand=True, padx=1)
        ttk.Button(exp_row2, text=t("mat_expand_custom"), style="Accent.TButton", command=self._expand_coin_locker_custom).pack(side="left", fill="x", expand=True, padx=1)

    def _get_mat_photo_key(self, itemid, name_en):
        if hasattr(self, "icon_map") and "materials_thumbs" in self.icon_map:
            thumb_rel = self.icon_map["materials_thumbs"].get(itemid)
            if thumb_rel:
                return thumb_rel
        clean_en = name_en.lower().replace(" ", "_").replace("-", "_").replace("'", "").replace(".", "")
        candidates = [
            f"thumbs/materials/mat_{itemid.lower()}.png",
            f"{clean_en}_box.png",
            f"{clean_en}_itembox.png",
            f"{clean_en}.png",
            f"{itemid.lower()}.png"
        ]
        if hasattr(self, "asset_manager") and getattr(self.asset_manager, "manifest", None):
            for c in candidates:
                c_low = c.lower()
                if c_low in self.asset_manager.manifest:
                    return self.asset_manager.manifest[c_low]
                c_base = os.path.basename(c_low)
                if c_base in self.asset_manager.manifest:
                    return self.asset_manager.manifest[c_base]

        for candidate in candidates:
            if self.get_photo(candidate, (36, 36)):
                return candidate

        if "alumi" in itemid.lower(): return "materials/aluminum_scraps.png"
        elif "copper" in itemid.lower(): return "materials/clump_of_copper_scraps.png"
        elif "iron" in itemid.lower(): return "materials/iron_scraps.png"
        elif "oil" in itemid.lower(): return "materials/waste_oil.png"
        elif "wood" in itemid.lower(): return "materials/veneer_plank.png"
        elif "fiber" in itemid.lower(): return "materials/cotton.png"
        elif "diy" in itemid.lower(): return "materials/dod_arms_purple_metal.png"
        elif "spo" in itemid.lower(): return "materials/war_ensemble_purple_metal.png"
        elif "fan" in itemid.lower(): return "materials/candle_wolf_purple_metal.png"
        elif "mil" in itemid.lower(): return "materials/m.i.l.k._purple_metal.png"
        return "materials/special_steel.png"

    def _on_mat_select(self, event):
        sel = self.mat_tree.selection()
        if not sel:
            return
        node = sel[0]
        full_title = self.mat_tree.item(node, "text").strip()
        vals = self.mat_tree.item(node, "values")
        stock_str = vals[0]
        stars = vals[1]
        cat = vals[2]
        itemid = vals[3]
        
        cnt_raw = str(stock_str).replace("pcs.", "").replace("u.", "").replace("-", "0").strip()
        cnt = int(cnt_raw) if cnt_raw.isdigit() else 0
        
        self.current_mat_selection = (itemid, full_title, cat)
        self.mat_qty_entry_var.set(str(cnt))
        self.mat_title_lbl.config(text=f"{full_title}\n({itemid}) • {stars}")
        self.mat_type_lbl.config(text=t("mat_type_info", cat=cat, count=cnt))
        
        clean_slug = full_title.split("(")[0].strip().lower().replace(" ", "_").replace("-", "_")
        name_en = full_title.split("(")[0].strip()
        
        sb_db = getattr(self, "shrooms_beasts_db", {})
        if itemid in sb_db:
            meta = sb_db[itemid]
            desc = i18n.get_item_desc(meta) or meta.get("desc_es") or meta.get("desc_en", "")
        else:
            meta = next((item for item in self.materials_db if item.get("itemid") == itemid), {})
            desc = i18n.get_item_desc(meta) or meta.get("desc", "")
            
        self.mat_desc_lbl.config(text=desc)
        
        # Check if selection is a Mushroom or Beast
        mat_art_target = None
        if itemid.startswith("MSR_") or itemid.startswith("BST_"):
            mat_art_target = sb_db.get(itemid, {}).get("icon") or f"{itemid.lower()}.png"
        else:
            card_rel = self.icon_map.get("materials_cards", {}).get(itemid) if hasattr(self, "icon_map") else None
            mat_art_target = card_rel or self._get_mat_photo_key(itemid, name_en)

        self.set_widget_image(self.mat_art_lbl, mat_art_target, size=(160, 160), preserve_aspect=True, fallback="materials/special_steel.png")

    def _set_selected_mat_qty(self):
        if not self.current_mat_selection or not self.save_json:
            return
        itemid, name, cat = self.current_mat_selection
        try:
            qty = int(self.mat_qty_entry_var.get())
        except ValueError:
            qty = 50
        modifiers.add_material_to_storage(self.save_json, itemid, count=qty)
        self._auto_save()
        self.filter_materials_list()
        self.status_var.set(t("mat_added_to_storage_status", qty=qty, name=name))

    def _quick_add_material_qty(self, delta):
        if not self.current_mat_selection or not self.save_json:
            return
        itemid, name, cat = self.current_mat_selection
        modifiers.add_material_to_storage(self.save_json, itemid, count=delta)
        self._auto_save()
        self.filter_materials_list()
        self.status_var.set(t("mat_added_to_storage_status", qty=delta, name=name))

    def _edit_selected_material_count(self, event):
        sel = self.mat_tree.selection()
        if not sel:
            return
        node = sel[0]
        vals = self.mat_tree.item(node, "values")
        itemid = vals[3]
        name = self.mat_tree.item(node, "text").strip()
        
        new_cnt = simpledialog.askinteger(
            t("mat_custom_qty_title"),
            t("mat_custom_qty_prompt", name=name, itemid=itemid),
            initialvalue=50, minvalue=1, maxvalue=500
        )
        if new_cnt is not None:
            modifiers.add_material_to_storage(self.save_json, itemid, count=new_cnt)
            self._auto_save()
            self.filter_materials_list()
            self.status_var.set(t("mat_added_to_storage_status", qty=new_cnt, name=name))

    def max_all_materials_preset(self):
        if not self.save_json:
            return
        modifiers.add_all_materials_to_storage(self.save_json, count=100)
        self._auto_save()
        self.filter_materials_list()
        self._notify("mat_notify_stocked_title", "mat_notify_stocked_msg")

    def _expand_coin_locker_add(self, amount):
        if not self.save_json:
            return
        current_cap = len(self.save_json.get("soul", {}).get("cl", []))
        self._expand_coin_locker(current_cap + amount)

    def _expand_coin_locker_custom(self):
        if not self.save_json:
            return
        cl_items = self.save_json.get("soul", {}).get("cl", [])
        current_cap = len(cl_items)
        occupied_count = len([x for x in cl_items if x.get("type", -1) != -1 or x.get("eid", "") != ""])
        prompt_txt = t("mat_locker_custom_prompt", cur=current_cap, occ=occupied_count)
        target = simpledialog.askinteger(
            "🚀 " + t("mat_locker_cap_title"),
            prompt_txt,
            initialvalue=max(occupied_count + 200, 6000),
            minvalue=max(occupied_count, 100),
            maxvalue=50000,
            parent=self
        )
        if target and target != current_cap:
            self._expand_coin_locker(target)

    def _expand_coin_locker(self, target_capacity):
        if not self.save_json:
            return
        cl_items = self.save_json.get("soul", {}).get("cl", [])
        current_cap = len(cl_items)
        occupied_count = len([x for x in cl_items if x.get("type", -1) != -1 or x.get("eid", "") != ""])
        if target_capacity < occupied_count:
            messagebox.showwarning(
                t("mat_locker_limit_title"),
                t("mat_locker_limit_msg", occ=occupied_count)
            )
            return
        if target_capacity == current_cap:
            return
        old_c, new_c = modifiers.expand_storage_capacity(self.save_json, target_capacity=target_capacity)
        self._auto_save()
        self.status_var.set(t("mat_locker_status_bar", old=old_c, new=new_c))
        self.refresh_all_views()
        messagebox.showinfo(
            t("mat_locker_updated_title"),
            t("mat_locker_updated_msg", old=old_c, new=new_c, occ=occupied_count)
        )

    def _set_mat_floor_filter(self, mode):
        self.mat_floor_filter.set(mode)
        self.filter_materials_list()

    @classmethod
    def _match_material_category(cls, cat_filter, item_cat):
        if not cat_filter or cat_filter in ("ALL", "Todos", "All", "全部", t("mat_all"), t("mat_cat_all"), t("decal_all")):
            return True
            
        # 1. Direct canonical item check if material dict is passed
        if isinstance(item_cat, dict):
            item_cid = item_cat.get("category_id")
            for code, key in CANONICAL_MATERIAL_CATEGORIES:
                if cat_filter in (code, t(key)):
                    return code == "ALL" or item_cid == code
            item_cat = item_cat.get("category", "")
            
        fl = cat_filter.lower()
        cl = item_cat.lower()
        
        # 2. Canonical mapping resolution
        filter_code = None
        for code, key in CANONICAL_MATERIAL_CATEGORIES:
            if cat_filter == code or fl == t(key).lower():
                filter_code = code
                break
                
        code_to_cl_subs = {
            "ALUMINUM": ["alumin"],
            "COPPER": ["cobre", "copper"],
            "IRON_STEEL": ["hierro", "iron", "steel", "acero"],
            "OIL": ["petr", "oil", "aceite"],
            "WOOD": ["mader", "wood"],
            "CLOTH": ["textil", "cloth", "fibra", "fiber"],
            "DOD": ["d.o.d", "dod"],
            "WAR": ["war"],
            "CW": ["candle", "cw"],
            "MILK": ["m.i.l.k", "milk"],
            "BOSS": ["boss", "jefe"],
            "JACKAL_TENGOKU": ["jackal", "tengoku"],
            "STEROIDS": ["esteroide", "steroid", "rostest"],
        }
        if filter_code and filter_code in code_to_cl_subs:
            if any(sub in cl for sub in code_to_cl_subs[filter_code]):
                return True
                
        # 3. Fallback for custom string patterns & unit tests
        if any(x in fl for x in ["steroid", "esteroide", "rostest", "类固醇"]):
            return any(x in cl for x in ["esteroide", "steroid", "rostest"])
        if any(x in fl for x in ["aluminum", "aluminio", "铝"]):
            return "alumin" in cl
        if any(x in fl for x in ["copper", "cobre", "铜"]):
            return any(x in cl for x in ["cobre", "copper"])
        if any(x in fl for x in ["iron", "hierro", "steel", "acero", "铁", "钢"]):
            return any(x in cl for x in ["hierro", "iron", "steel", "acero"])
        if any(x in fl for x in ["oil", "petr", "aceite", "油"]):
            return any(x in cl for x in ["petr", "oil", "aceite"])
        if any(x in fl for x in ["wood", "mader", "木"]):
            return any(x in cl for x in ["mader", "wood"])
        if any(x in fl for x in ["cloth", "textil", "fiber", "fibra", "布"]):
            return any(x in cl for x in ["textil", "cloth", "fibra", "fiber"])
        if any(x in fl for x in ["d.o.d", "dod"]):
            return any(x in cl for x in ["d.o.d", "dod"])
        if "war" in fl:
            return "war" in cl
        if "candle" in fl:
            return "candle" in cl
        if any(x in fl for x in ["m.i.l.k", "milk"]):
            return any(x in cl for x in ["m.i.l.k", "milk"])
        if any(x in fl for x in ["boss", "jefe"]):
            return any(x in cl for x in ["boss", "jefe"])
        if any(x in fl for x in ["jackal", "tengoku", "豺狼", "天狱"]):
            return any(x in cl for x in ["jackal", "tengoku"])
            
        c_key = cat_filter.lower().split()[0].replace("(", "").replace(")", "")
        return c_key in cl

    @staticmethod
    def _localize_material_category(cat_str):
        if not cat_str:
            return ""
        cl = cat_str.lower()
        if "esteroide" in cl or "rostest" in cl or "steroid" in cl:
            return t("mat_cat_steroids")
        if "alumin" in cl:
            return t("mat_cat_aluminum")
        if "cobre" in cl or "copper" in cl:
            return t("mat_cat_copper")
        if "hierro" in cl or "iron" in cl or "steel" in cl or "acero" in cl:
            return t("mat_cat_iron_steel")
        if "petr" in cl or "oil" in cl or "aceite" in cl:
            return t("mat_cat_oil")
        if "mader" in cl or "wood" in cl:
            return t("mat_cat_wood")
        if "textil" in cl or "cloth" in cl or "fibra" in cl or "fiber" in cl:
            return t("mat_cat_cloth")
        if "d.o.d" in cl or "dod" in cl:
            return t("mat_cat_dod")
        if "war" in cl:
            return t("mat_cat_war")
        if "candle" in cl or "cw" in cl:
            return t("mat_cat_cw")
        if "m.i.l.k" in cl or "milk" in cl:
            return t("mat_cat_milk")
        if "boss" in cl or "jefe" in cl:
            return t("mat_cat_boss")
        if "jackal" in cl or "tengoku" in cl:
            return t("mat_cat_jackal_tengoku")
        return cat_str

    @staticmethod
    def _localize_material_category_zh(cat_str):
        # Universal localization handles all languages via t()
        return MaterialsTabMixin._localize_material_category(cat_str)

    def filter_materials_list(self):
        self.mat_tree.delete(*self.mat_tree.get_children())
            
        query = self.mat_search_var.get().lower().strip() if hasattr(self, "mat_search_var") else ""
        query_tokens = query.split() if query else []
        cat_filter = self.mat_cat_var.get() if hasattr(self, "mat_cat_var") else "Todos"
        cat_map = getattr(self, "_mat_cat_map", {})
        cat_code = cat_map.get(cat_filter)
        if not cat_code:
            for code, k in CANONICAL_MATERIAL_CATEGORIES:
                if cat_filter in (code, t(k)):
                    cat_code = code
                    break
        if not cat_code:
            cat_code = "ALL"

        stock_filter = self.mat_stock_filter_var.get() if hasattr(self, "mat_stock_filter_var") else "Todo"
        stock_mode = getattr(self, "_stock_filter_map", {}).get(stock_filter)
        rarity_filter = self.mat_rarity_filter_var.get() if hasattr(self, "mat_rarity_filter_var") else "Todas"
        floor_filter = self.mat_floor_filter.get() if hasattr(self, "mat_floor_filter") else "TODOS"
        
        # Get live stock from save
        stock_map = {}
        if self.save_json:
            try:
                stock_map = modifiers.analyze_storage_stock(self.save_json).get("stock_by_id", {})
            except Exception:
                stock_map = {}
                
        first_row = None
        
        # 1. R&D Materials from masters.db
        show_rnd_materials = (cat_code not in ("MUSHROOMS", "BEASTS", "MUSHROOMS_BEASTS"))
        if show_rnd_materials and "🍄" not in cat_filter and "🐸" not in cat_filter:
            for m in self.materials_db:
                name_es = m.get("name_es", m.get("name", ""))
                name_en = m.get("name_en", "")
                cat = m.get("category", "Materiales")
                r = m.get("rarity", 1)
                stars = "★" * r
                itemid = m.get("itemid", "")
                cnt = stock_map.get(itemid, 0)
                
                # Category filter
                if cat_code != "ALL":
                    m_cid = m.get("category_id")
                    if m_cid:
                        if m_cid != cat_code:
                            continue
                    elif not self._match_material_category(cat_filter, m):
                        continue
                elif not self._match_material_category(cat_filter, m):
                    continue
                    
                # Stock filter
                if stock_mode == "IN_STOCK" and cnt <= 0:
                    continue
                elif stock_mode == "LOW_STOCK" and (cnt <= 0 or cnt >= 10):
                    continue
                elif stock_mode == "OUT_OF_STOCK" and cnt > 0:
                    continue
                elif not stock_mode:
                    if ("> 0" in stock_filter or "En Stock" in stock_filter or "In Stock" in stock_filter or "已拥有" in stock_filter or "有库存" in stock_filter) and cnt <= 0:
                        continue
                    elif ("< 10" in stock_filter or "Stock Bajo" in stock_filter or "Low Stock" in stock_filter or "低库存" in stock_filter) and (cnt <= 0 or cnt >= 10):
                        continue
                    elif ("(0)" in stock_filter or "Agotado" in stock_filter or "Out of Stock" in stock_filter or "缺货" in stock_filter or "无库存" in stock_filter) and cnt > 0:
                        continue

                # Rarity filter
                if "★" in rarity_filter:
                    try:
                        req_r = int(rarity_filter.replace("★", "").strip())
                        if r != req_r:
                            continue
                    except ValueError:
                        pass

                # Floor filter (Tower Section)
                if floor_filter != "TODOS":
                    cat_lower = cat.lower()
                    match_floor = False
                    if floor_filter == "1_10" and (r in (1, 2) or "d.o.d" in cat_lower):
                        match_floor = True
                    elif floor_filter == "11_20" and (r == 3 or "war" in cat_lower):
                        match_floor = True
                    elif floor_filter == "21_30" and (r == 4 or "candle" in cat_lower):
                        match_floor = True
                    elif floor_filter == "31_40" and (r == 5 or "m.i.l.k" in cat_lower):
                        match_floor = True
                    elif floor_filter == "41_50" and (r == 6):
                        match_floor = True
                    elif floor_filter == "51_PLUS" and (r in (7, 8) or "tengoku" in cat_lower or "jackals" in cat_lower):
                        match_floor = True
                    if not match_floor:
                        continue

                # Query search with smart multi-word matching & Tier aliases
                if query_tokens:
                    extra_names = " ".join(str(v) for k, v in m.items() if (k.startswith("name") or k.startswith("desc")) and isinstance(v, str))
                    searchable = f"{extra_names} {name_es} {name_en} {cat} {self._localize_material_category(cat)} {self._localize_material_category_zh(cat)} {itemid} t{r} tier {r} tier{r} {r}★ {r}star {name_en.replace('.', '')} {name_es.replace('.', '')}".lower()
                    if not all(token in searchable for token in query_tokens):
                        continue

                stock_str = t("inv_unit_str", qty=cnt) if cnt > 0 else "-"
                tag = "tag_in_stock" if cnt > 0 else "tag_out_of_stock"
                    
                display_title = i18n.get_entity_display_title(m)
                cat_display = self._localize_material_category(cat)
                icon_k = self._get_mat_photo_key(itemid, name_en or name_es)
                thumb = self.get_photo(icon_k, size=(36, 36), preserve_aspect=True)
                node_id = self.mat_tree.insert(
                    "",
                    "end",
                    text=f" {display_title}",
                    image=thumb or "",
                    values=(stock_str, stars, cat_display, itemid),
                    tags=(tag,)
                )
                self.tree_images[node_id] = thumb
                if not thumb and icon_k:
                    self.set_tree_item_image(self.mat_tree, node_id, icon_k, size=(36, 36), preserve_aspect=True)
                if not first_row:
                    first_row = node_id
                    
        # 2. Shrooms and Beasts (Tower Exploration)
        is_shroom_cat = (cat_code in ("MUSHROOMS", "BEASTS", "MUSHROOMS_BEASTS") or "🍄" in cat_filter or "🐸" in cat_filter)
        allow_shrooms_floors = (is_shroom_cat or floor_filter == "TODOS")
        show_shrooms = (cat_code in ("ALL", "MUSHROOMS", "BEASTS", "MUSHROOMS_BEASTS") or cat_filter in ["Todos", "All", "全部", t("mat_all"), t("decal_all")] or is_shroom_cat)

        if show_shrooms and allow_shrooms_floors:
            only_shrooms = (cat_code == "MUSHROOMS") or ("(Mushrooms)" in cat_filter or "(Setas)" in cat_filter or "🍄 蘑菇" in cat_filter or cat_filter == "🍄 Mushrooms")
            only_beasts = (cat_code == "BEASTS") or ("(Beasts)" in cat_filter or "(Criaturas)" in cat_filter or "🐸 野兽" in cat_filter or cat_filter == "🐸 Beasts")

            sb_db = getattr(self, "shrooms_beasts_db", {})
            if not sb_db:
                sb_path = os.path.join(BASE_DIR, "all_shrooms_beasts_db.json")
                if os.path.exists(sb_path):
                    try:
                        with open(sb_path, "r", encoding="utf-8") as f:
                            self.shrooms_beasts_db = json.load(f)
                            sb_db = self.shrooms_beasts_db
                    except Exception:
                        pass

            sorted_entries = sorted(
                sb_db.items(),
                key=lambda item: (0 if item[1].get("type") == "MUSHROOM" else 1, item[0])
            )

            for itemid, info in sorted_entries:
                item_type = info.get("type", "MUSHROOM")
                if only_shrooms and item_type != "MUSHROOM":
                    continue
                if only_beasts and item_type != "BEAST":
                    continue

                cnt = stock_map.get(itemid, 0)
                if stock_mode == "IN_STOCK" and cnt <= 0:
                    continue
                elif stock_mode == "LOW_STOCK" and (cnt <= 0 or cnt >= 10):
                    continue
                elif stock_mode == "OUT_OF_STOCK" and cnt > 0:
                    continue
                elif not stock_mode:
                    if ("> 0" in stock_filter or "En Stock" in stock_filter or "In Stock" in stock_filter or "已拥有" in stock_filter or "有库存" in stock_filter) and cnt <= 0:
                        continue
                    elif ("< 10" in stock_filter or "Stock Bajo" in stock_filter or "Low Stock" in stock_filter or "低库存" in stock_filter) and (cnt <= 0 or cnt >= 10):
                        continue
                    elif ("(0)" in stock_filter or "Agotado" in stock_filter or "Out of Stock" in stock_filter or "缺货" in stock_filter or "无库存" in stock_filter) and cnt > 0:
                        continue

                r = info.get("rarity", 1)
                if "★" in rarity_filter:
                    try:
                        req_r = int(rarity_filter.replace("★", "").strip())
                        if r != req_r:
                            continue
                    except ValueError:
                        pass

                name_en = info.get("name_en", "")
                name_es = info.get("name_es", "")
                cooked_en = info.get("cooked_name_en", "")
                cooked_es = info.get("cooked_name_es", "")
                cat_display = t("cat_mushroom") if item_type == "MUSHROOM" else t("cat_beast")

                if query_tokens:
                    extra_names = " ".join(str(v) for k, v in info.items() if (k.startswith("name") or k.startswith("desc") or "cooked" in k) and isinstance(v, str))
                    searchable = f"{extra_names} {name_es} {name_en} {itemid} {item_type} {cat_display} {cooked_en} {cooked_es} mushroom seta shroom beast criatura t{r} tier{r} {r}★ {r}star".lower()
                    if not all(token in searchable for token in query_tokens):
                        continue

                stock_str = t("inv_unit_str", qty=cnt) if cnt > 0 else "-"
                tag = "tag_in_stock" if cnt > 0 else "tag_out_of_stock"
                stars = "★" * r
                display_title = i18n.get_entity_display_title(info)

                icon_f = info.get("icon") or f"{itemid.lower()}.png"
                thumb = self.get_photo(icon_f, size=(36, 36), preserve_aspect=True) or self.get_photo(itemid.lower(), size=(36, 36), preserve_aspect=True)

                node_id = self.mat_tree.insert(
                    "",
                    "end",
                    text=f" {display_title}",
                    image=thumb or "",
                    values=(stock_str, stars, cat_display, itemid),
                    tags=(tag,)
                )
                self.tree_images[node_id] = thumb
                if not thumb and icon_f:
                    self.set_tree_item_image(self.mat_tree, node_id, icon_f, size=(36, 36), preserve_aspect=True)
                if not first_row:
                    first_row = node_id
                    
        if first_row:
            self.mat_tree.selection_set(first_row)
            self._on_mat_select(None)
