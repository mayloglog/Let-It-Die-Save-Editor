# -*- coding: utf-8 -*-
"""
Account Re-binding and Compatibility Module for LET IT DIE Save Editor.
Allows converting/adapting save files downloaded from other users/accounts
so they work seamlessly with the player's active Steam account and save slots.
"""

import os
import sys
import re
import save_io
import core.save_slots as save_slots


def extract_save_identity(save_dict):
    """
    Extracts account identity and character summary from a save data dictionary.
    """
    if not isinstance(save_dict, dict):
        return {
            "steam_id": "---",
            "player_name": "Senpai",
            "uid": "0",
            "has_session_tokens": False,
            "fighter_name": "Fighter",
            "fighter_lvl": 1,
            "max_floor": 1
        }

    user = save_dict.get("user", {})
    steam_id = str(user.get("psnacid", "") or "").strip()
    player_name = str(user.get("nm", "Senpai") or "Senpai").strip()
    uid = str(user.get("uid", "0") or "0").strip()

    skey = str(user.get("skey", "") or "").strip()
    sid = str(user.get("sid", "") or "").strip()
    has_session_tokens = bool(skey or sid)

    meta = save_slots.extract_save_metadata(save_dict)
    fighter_name = meta.get("fighter_name", "Fighter")
    fighter_lvl = meta.get("fighter_lvl", 1)
    max_floor = meta.get("max_floor", 1)

    return {
        "steam_id": steam_id or "---",
        "player_name": player_name,
        "uid": uid,
        "has_session_tokens": has_session_tokens,
        "fighter_name": fighter_name,
        "fighter_lvl": fighter_lvl,
        "max_floor": max_floor
    }


def detect_active_account_identity(active_save_dict=None, active_save_path=None):
    """
    Detects the current user's active Steam ID, Senpai name, and account UID.
    Attempts:
    1. active_save_dict if passed and valid
    2. active_save_path if exists
    3. Default detected save file in Steam directory
    4. Steam registry or library paths
    """
    if active_save_dict and isinstance(active_save_dict, dict) and "user" in active_save_dict:
        ident = extract_save_identity(active_save_dict)
        if ident["steam_id"] != "---":
            return ident

    if active_save_path and os.path.exists(active_save_path):
        try:
            data, _ = save_io.decompress_save(active_save_path)
            ident = extract_save_identity(data)
            if ident["steam_id"] != "---":
                return ident
        except Exception:
            pass

    default_path = save_io.get_default_save_path()
    if default_path and os.path.exists(default_path):
        try:
            data, _ = save_io.decompress_save(default_path)
            ident = extract_save_identity(data)
            if ident["steam_id"] != "---":
                return ident
        except Exception:
            pass

    # Try detecting SteamID from Steam Savedata directory filenames
    detected_dirs = save_io.get_all_detected_steam_dirs()
    for d in detected_dirs:
        if os.path.isdir(d):
            for f in os.listdir(d):
                if f.endswith(".sav") and not f.endswith(".bak"):
                    base = os.path.splitext(f)[0]
                    if re.match(r"^7656119\d{10}$", base):
                        return {
                            "steam_id": base,
                            "player_name": "Senpai",
                            "uid": "1",
                            "has_session_tokens": False,
                            "fighter_name": "Fighter",
                            "fighter_lvl": 1,
                            "max_floor": 1
                        }

    return {
        "steam_id": "76561198000000000",
        "player_name": "Senpai",
        "uid": "1",
        "has_session_tokens": False,
        "fighter_name": "Fighter",
        "fighter_lvl": 1,
        "max_floor": 1
    }


def is_foreign_save(save_dict, my_steam_id):
    """
    Returns True if save_dict belongs to a different Steam ID than my_steam_id.
    """
    if not isinstance(save_dict, dict):
        return False
    save_steam = str(save_dict.get("user", {}).get("psnacid", "") or "").strip()
    my_steam = str(my_steam_id or "").strip()
    if not save_steam or not my_steam:
        return False
    return save_steam != my_steam


def rebind_save_to_account(
    save_dict,
    target_steam_id,
    target_player_name=None,
    target_uid=None,
    clear_session_tokens=True
):
    """
    Rebinds a save file dictionary to a target Steam account.
    - Sets user.psnacid to target_steam_id.
    - Optionally updates user.nm (player name).
    - Clears obsolete online session tokens (skey, sid, uuid, olid).
    - If target_uid is provided and differs, safely remaps internal UIDs.
    Returns the modified save_dict.
    """
    if not isinstance(save_dict, dict):
        raise ValueError("save_dict must be a valid dictionary")

    target_steam_id = str(target_steam_id or "").strip()
    if not target_steam_id:
        raise ValueError("target_steam_id cannot be empty")

    if "user" not in save_dict or not isinstance(save_dict["user"], dict):
        save_dict["user"] = {}

    old_steam_id = str(save_dict["user"].get("psnacid", ""))
    save_dict["user"]["psnacid"] = target_steam_id

    # 1. Update Player Name if provided
    if target_player_name is not None and str(target_player_name).strip():
        save_dict["user"]["nm"] = str(target_player_name).strip()

    # 2. Sanitize online session authentication cookies
    if clear_session_tokens:
        save_dict["user"]["skey"] = ""
        save_dict["user"]["sid"] = ""
        save_dict["user"]["uuid"] = ""
        save_dict["user"]["olid"] = ""

    # 3. Safe UID remapping if requested and distinct
    if target_uid is not None:
        target_uid_str = str(target_uid).strip()
        old_uid_str = str(save_dict["user"].get("uid", "0") or "0").strip()

        if target_uid_str and target_uid_str != old_uid_str:
            old_u_int = int(old_uid_str) if old_uid_str.isdigit() else old_uid_str
            new_u_int = int(target_uid_str) if target_uid_str.isdigit() else target_uid_str

            save_dict["user"]["uid"] = new_u_int

            if "soul" in save_dict and isinstance(save_dict["soul"], dict):
                save_dict["soul"]["uid"] = new_u_int

            # Remap bodyuser dictionary key
            if "bodyuser" in save_dict and isinstance(save_dict["bodyuser"], dict):
                if old_uid_str in save_dict["bodyuser"]:
                    save_dict["bodyuser"][target_uid_str] = save_dict["bodyuser"].pop(old_uid_str)

            # Remap part.pts dictionary key and item uids
            if "part" in save_dict and isinstance(save_dict["part"], dict):
                pts = save_dict["part"].get("pts")
                if isinstance(pts, dict) and old_uid_str in pts:
                    pts[target_uid_str] = pts.pop(old_uid_str)
                    if isinstance(pts[target_uid_str], list):
                        for it in pts[target_uid_str]:
                            if isinstance(it, dict) and it.get("uid") == old_u_int:
                                it["uid"] = new_u_int

            # Remap zombie sub-dictionaries
            if "zombie" in save_dict and isinstance(save_dict["zombie"], dict):
                z = save_dict["zombie"]
                for z_sec in ["pspts", "eqpts", "mstlvls", "flrzmbs", "rwds"]:
                    if z_sec in z and isinstance(z[z_sec], dict) and old_uid_str in z[z_sec]:
                        z[z_sec][target_uid_str] = z[z_sec].pop(old_uid_str)
                        val = z[z_sec][target_uid_str]
                        if isinstance(val, dict):
                            for sub_k, sub_v in val.items():
                                if isinstance(sub_v, list):
                                    for it in sub_v:
                                        if isinstance(it, dict) and it.get("uid") == old_u_int:
                                            it["uid"] = new_u_int
                        elif isinstance(val, list):
                            for it in val:
                                if isinstance(it, dict) and it.get("uid") == old_u_int:
                                    it["uid"] = new_u_int

    return save_dict


def adapt_and_save_external_file(
    src_path,
    dest_path,
    target_steam_id,
    target_player_name=None,
    target_uid=None,
    clear_session_tokens=True,
    version=2
):
    """
    Decompresses an external save file, rebinds it to the target Steam account,
    and compresses/saves it into dest_path.
    Returns (True, rebound_data, rebound_meta).
    """
    if not os.path.exists(src_path):
        raise FileNotFoundError(f"Source file not found: {src_path}")

    data, ver = save_io.decompress_save(src_path)
    save_ver = version or ver or 2

    rebind_save_to_account(
        data,
        target_steam_id=target_steam_id,
        target_player_name=target_player_name,
        target_uid=target_uid,
        clear_session_tokens=clear_session_tokens
    )

    save_io.save_to_file(data, dest_path, version=save_ver, make_backup=False)
    meta = save_slots.extract_save_metadata(data)
    return True, data, meta
