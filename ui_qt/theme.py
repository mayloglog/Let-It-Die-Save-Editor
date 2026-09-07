# -*- coding: utf-8 -*-
"""
Theme and Styling Engine for LET IT DIE Save Editor (PySide6 Edition).
Provides color palette constants, font resolution, QSS stylesheet loading, and asset caching.
"""

import os
import sys
import json
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QPixmap, QIcon, QImage, QPainter
from PySide6.QtWidgets import QApplication

# Base paths
if getattr(sys, "frozen", False):
    exe_dir = os.path.dirname(os.path.abspath(sys.executable))
    mei_dir = getattr(sys, "_MEIPASS", exe_dir)
    BASE_DIR = exe_dir if os.path.isdir(os.path.join(exe_dir, "icons")) else mei_dir
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ICONS_DIR = os.path.join(BASE_DIR, "icons")
ICON_MAP_PATH = os.path.join(BASE_DIR, "icon_map.json")
STYLES_QSS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "styles.qss")

# Color Palette: Cyberpunk Dark
BG_DARK = "#0d0f17"        # Ultra deep dark space background
BG_PANEL = "#151824"       # Clean dark slate panel
BG_CARD = "#1c2030"        # Elevated card surface
BG_CARD_LIGHT = "#252b40"  # Highlighted card surface
BG_CARD_HOVER = "#2f3650"  # Interactive hover
FG_MAIN = "#f0f2f5"        # Crisp white text
FG_TEXT = FG_MAIN           # Compatibility alias
FG_MUTED = "#9aa0b4"       # Subtle soft secondary text
ACCENT_GOLD = "#f5b041"    # Royal gold accent
ACCENT_CYAN = "#00e5ff"    # Bright cyber cyan
ACCENT_BLUE = "#3498db"    # Clean sky blue
ACCENT_GREEN = "#2ecc71"   # Success emerald
ACCENT_RED = "#e74c3c"     # Danger crimson
ACCENT_PURPLE = "#bb86fc"  # Cyberpunk neon purple
ACCENT_PINK = "#ff4081"    # Death Metal vibrant magenta

# In-memory caches
_PIXMAP_CACHE = {}
_ICON_INDEX = {}
_ICON_MAP = None


def _index_icons():
    """Builds a fast O(1) index of all local icons."""
    global _ICON_INDEX, _ICON_MAP
    if _ICON_INDEX:
        return

    dirs_to_index = [ICONS_DIR]
    try:
        from core.asset_manager import AssetManager
        am = AssetManager()
        if getattr(am, "cache_dir", None):
            dirs_to_index.append(am.cache_dir)
    except Exception:
        pass

    for scan_dir in dirs_to_index:
        if scan_dir and os.path.isdir(scan_dir):
            for root, _, files in os.walk(scan_dir):
                for f in files:
                    if not f.endswith(".tmp"):
                        full_p = os.path.join(root, f)
                        lower_f = f.lower()
                        if lower_f not in _ICON_INDEX:
                            _ICON_INDEX[lower_f] = full_p
                        base_no_ext = os.path.splitext(lower_f)[0]
                        if base_no_ext not in _ICON_INDEX:
                            _ICON_INDEX[base_no_ext] = full_p

    if os.path.exists(ICON_MAP_PATH):
        try:
            with open(ICON_MAP_PATH, "r", encoding="utf-8") as f:
                _ICON_MAP = json.load(f)
        except Exception:
            _ICON_MAP = {}
    else:
        _ICON_MAP = {}


_MISSING_CACHE = set()


def invalidate_asset_caches():
    """Make completed downloads and cache removal visible without restarting."""
    _MISSING_CACHE.clear()
    _PIXMAP_CACHE.clear()
    _ICON_INDEX.clear()

def resolve_icon_path(rel_path):
    """Resolves a relative icon path to a local absolute file path."""
    if not rel_path:
        return None

    if rel_path in _MISSING_CACHE:
        return None

    _index_icons()
    clean_rel = str(rel_path).replace("\\", "/")

    if os.path.isabs(clean_rel) and os.path.exists(clean_rel):
        return clean_rel

    # 1. Fast O(1) lookup
    clean_base = os.path.basename(clean_rel).lower()
    clean_stem = os.path.splitext(clean_base)[0]
    found = _ICON_INDEX.get(clean_base) or _ICON_INDEX.get(clean_stem)
    if found and os.path.exists(found):
        return found

    # 2. Check icon_map.json
    if _ICON_MAP:
        for map_key in ["gear_icons", "gear_cards", "materials_cards", "materials_thumbs", "decals_icons", "equipment_thumbs"]:
            sub_map = _ICON_MAP.get(map_key, {})
            mapped = sub_map.get(clean_rel) or sub_map.get(clean_rel.upper()) or sub_map.get(clean_rel.lower())
            if mapped:
                mapped_base = os.path.basename(mapped.replace("\\", "/")).lower()
                mapped_stem = os.path.splitext(mapped_base)[0]
                found = _ICON_INDEX.get(mapped_base) or _ICON_INDEX.get(mapped_stem)
                if found and os.path.exists(found):
                    return found
                # Also check direct path
                direct = os.path.join(ICONS_DIR, mapped.replace("\\", "/"))
                if os.path.exists(direct):
                    return direct

    _MISSING_CACHE.add(rel_path)
    return None


def find_equipment_art(ptid, as_card=False):
    """Resolves official equipment art for blueprints (wide card or square icon)."""
    if not ptid:
        return "blueprint"
    _index_icons()
    ptid_str = str(ptid)
    if as_card:
        card = (
            _ICON_MAP.get("gear_cards", {}).get(ptid_str) or
            _ICON_MAP.get("gear_cards", {}).get(ptid_str.upper()) or
            _ICON_MAP.get("gear_cards", {}).get(ptid_str.lower())
        )
        if card and resolve_icon_path(card):
            return card
    ico = (
        _ICON_MAP.get("gear_icons", {}).get(ptid_str) or
        _ICON_MAP.get("gear_icons", {}).get(ptid_str.upper()) or
        _ICON_MAP.get("gear_icons", {}).get(ptid_str.lower())
    )
    if ico and resolve_icon_path(ico):
        return ico

    if as_card:
        # Fallback card to icon or vice versa
        pass
    else:
        card = (
            _ICON_MAP.get("gear_cards", {}).get(ptid_str) or
            _ICON_MAP.get("gear_cards", {}).get(ptid_str.upper()) or
            _ICON_MAP.get("gear_cards", {}).get(ptid_str.lower())
        )
        if card and resolve_icon_path(card):
            return card

    clean = ptid_str.lower().replace("pt_", "").replace("_001", "").replace("_01", "")
    candidates = [
        f"{ptid_str.lower()}.png",
        f"{ptid_str.lower()[:-2]}.png" if ptid_str.lower().endswith("_g") else None,
        f"thumb_{ptid_str.lower()}.png",
        f"{clean}.png"
    ]
    for c in candidates:
        if c and c in _ICON_INDEX:
            return _ICON_INDEX[c]
    return "weapon" if ("WP" in ptid_str or "ARM" in ptid_str) else "blueprint"


def find_material_art(itemid, name_en="", as_card=False):
    """Resolves material art (itembox card or table thumbnail) for all materials, shrooms & beasts."""
    if not itemid:
        return "materials/special_steel.png"
    _index_icons()
    item_str = str(itemid).strip()
    upper_id = item_str.upper()
    lower_id = item_str.lower()

    # Direct resolution for Mushrooms (MSR_) and Beasts (BST_)
    if upper_id.startswith("MSR_") or upper_id.startswith("BST_"):
        shroom_candidates = [
            f"all_official/{lower_id}.png",
            f"shrooms/{lower_id}.png",
            f"{lower_id}.png",
            f"all_official/{lower_id}_cooked.png",
            f"shrooms/{lower_id}_cooked.png"
        ]
        for sc in shroom_candidates:
            resolved = resolve_icon_path(sc)
            if resolved:
                return sc

    if as_card:
        card = (
            _ICON_MAP.get("materials_cards", {}).get(item_str) or
            _ICON_MAP.get("materials_cards", {}).get(upper_id) or
            _ICON_MAP.get("materials_cards", {}).get(lower_id)
        )
        if card and resolve_icon_path(card):
            return card

    thumb = (
        _ICON_MAP.get("materials_thumbs", {}).get(item_str) or
        _ICON_MAP.get("materials_thumbs", {}).get(upper_id) or
        _ICON_MAP.get("materials_thumbs", {}).get(lower_id)
    )
    if thumb and resolve_icon_path(thumb):
        return thumb

    # Cross fallback if card was requested but only thumb exists or vice versa
    if as_card:
        if thumb and resolve_icon_path(thumb):
            return thumb
    else:
        card = (
            _ICON_MAP.get("materials_cards", {}).get(item_str) or
            _ICON_MAP.get("materials_cards", {}).get(upper_id) or
            _ICON_MAP.get("materials_cards", {}).get(lower_id)
        )
        if card and resolve_icon_path(card):
            return card

    clean_en = name_en.lower().replace(" ", "_").replace("-", "_").replace("'", "").replace(".", "") if name_en else ""
    candidates = [
        f"thumbs/materials/mat_{lower_id}.png",
        f"thumbs/materials/{lower_id}.png",
        f"{clean_en}_itembox.png" if clean_en else None,
        f"{clean_en}_box.png" if clean_en else None,
        f"{clean_en}.png" if clean_en else None,
        f"{lower_id}.png"
    ]
    for c in candidates:
        if c and resolve_icon_path(c):
            return c

    ilow = lower_id
    if "alumi" in ilow: return "materials/aluminum_scraps.png"
    elif "copper" in ilow: return "materials/clump_of_copper_scraps.png"
    elif "iron" in ilow: return "materials/iron_scraps.png"
    elif "oil" in ilow: return "materials/waste_oil.png"
    elif "wood" in ilow: return "materials/veneer_plank.png"
    elif "fiber" in ilow: return "materials/cotton.png"
    elif "diy" in ilow: return "materials/dod_arms_purple_metal.png"
    elif "spo" in ilow: return "materials/war_ensemble_purple_metal.png"
    elif "fan" in ilow: return "materials/candle_wolf_purple_metal.png"
    elif "mil" in ilow: return "materials/m.i.l.k._purple_metal.png"
    return "materials/special_steel.png"


def find_decal_art(decal_id, is_premium=None):
    """Resolves official decal icon/art with premium fallback."""
    if not decal_id:
        return "all_official/decal_std.png"
    _index_icons()
    did_str = str(decal_id)
    is_p = did_str.endswith("_P") if is_premium is None else is_premium
    clean = did_str.replace("SKL_", "").replace("_P", "").lower()

    mapped = (
        _ICON_MAP.get("decals_icons", {}).get(did_str) or
        _ICON_MAP.get("decals_icons", {}).get(did_str.upper()) or
        _ICON_MAP.get("decals_icons", {}).get(did_str.lower())
    )
    if mapped:
        return mapped

    candidates = [
        f"{did_str.lower()}.png",
        f"skl_{clean}_p.png" if is_p else f"skl_{clean}.png",
        f"{clean}_p.png" if is_p else f"{clean}.png",
        f"decals/{did_str.lower()}.png"
    ]
    for c in candidates:
        if c and resolve_icon_path(c):
            return c
    return "all_official/decal_p.png" if is_p else "all_official/decal_std.png"


def get_fighter_model_art(model_str):
    """Resolves fighter character model to official face portrait."""
    import re
    if not model_str:
        return "all_official/body_female_001.png"
    m = re.search(r"BODY_(FEMALE|MALE)_(\d+)", str(model_str), re.IGNORECASE)
    if m:
        gender = m.group(1).lower()
        num = int(m.group(2))
        return f"all_official/body_{gender}_{num:03d}.png"
    m2 = re.search(r"(Female|Male)\s*(\d+)", str(model_str), re.IGNORECASE)
    if m2:
        gender = m2.group(1).lower()
        num = int(m2.group(2))
        return f"all_official/body_{gender}_{num:03d}.png"
    return "all_official/body_female_001.png"


def get_fighter_class_icon(cls_code):
    """Returns filename for fighter class icon."""
    from game_data import FIGHTER_CLASSES
    return FIGHTER_CLASSES.get(str(cls_code).upper(), ("", "all-rounder.png"))[1]


def get_qt_font(size=9, bold=False):
    """Returns a QFont configured with language-aware typography."""
    try:
        import i18n
        lang = i18n.get_language()
    except Exception:
        lang = "en"

    if lang == "zh":
        family = "Microsoft YaHei UI"
    elif lang == "ja":
        family = "Yu Gothic UI"
    elif lang == "ko":
        family = "Malgun Gothic"
    else:
        family = "Segoe UI"

    font = QFont(family, size)
    if bold:
        font.setBold(True)
    return font


def get_pixmap(rel_path, size=(28, 28), preserve_aspect=True, on_ready=None):
    """Returns a cached, smoothly-scaled QPixmap preserving natural aspect ratio."""
    if not rel_path:
        return None

    key = (str(rel_path), size[0], size[1], preserve_aspect)
    if key in _PIXMAP_CACHE:
        return _PIXMAP_CACHE[key]

    path = resolve_icon_path(rel_path)

    if path and os.path.exists(path):
        pix = QPixmap(path)
        if not pix.isNull():
            if preserve_aspect:
                scaled = pix.scaled(
                    size[0], size[1],
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
            else:
                scaled = pix.scaled(
                    size[0], size[1],
                    Qt.AspectRatioMode.IgnoreAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
            _PIXMAP_CACHE[key] = scaled
            return scaled

    return None


def get_icon(rel_path, size=(36, 36)):
    """Returns a QIcon for buttons, tables, and window tabs."""
    pix = get_pixmap(rel_path, size=size, preserve_aspect=True)
    if pix and not pix.isNull():
        return QIcon(pix)
    return QIcon()


def load_stylesheet():
    """Loads and returns the content of styles.qss."""
    if os.path.exists(STYLES_QSS_PATH):
        try:
            with open(STYLES_QSS_PATH, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            print(f"Error loading styles.qss: {e}")
    return ""
