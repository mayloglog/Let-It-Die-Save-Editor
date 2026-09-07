# -*- coding: utf-8 -*-
import unittest
import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import modifiers

class TestDecals(unittest.TestCase):
    def setUp(self):
        self.save = {
            "user": {"uid": 443455},
            "soul": {
                "uid": 443455,
                "skl": {
                    "psskl": [],
                    "eqskl": {}
                }
            }
        }

    def test_load_all_known_decals(self):
        decals = modifiers.load_all_known_decals()
        self.assertGreater(len(decals), 500)
        self.assertIn("SKL_HPUP_01", decals)

    def test_add_or_update_decals(self):
        modifiers.add_or_update_decals(self.save, ["SKL_HPUP_01", "SKL_DRAIN_01"], count=3, premium=True)
        psskl = self.save["soul"]["skl"]["psskl"]
        self.assertGreaterEqual(len(psskl), 2)
        decal_map = {d["sklid"]: d for d in psskl}
        self.assertIn("SKL_HPUP_01_P", decal_map)
        self.assertEqual(decal_map["SKL_HPUP_01_P"]["cnt"], 3)

    def test_equip_decal_preset_on_fighter(self):
        preset_name, count = modifiers.equip_decal_preset_on_fighter(self.save, "fighter_1", preset_key="tengoku_climber")
        self.assertGreaterEqual(count, 5)
        user_eq = self.save["soul"]["skl"]["eqskl"]["443455"]
        fighter_decals = [e for e in user_eq if e["cid"] == "fighter_1"]
        self.assertEqual(len(fighter_decals), count)

    def test_decals_map_preserves_standard_and_premium(self):
        """Ensure standard decals are never overwritten by premium counterparts in decals_map."""
        import json
        from core.helpers import ALL_DECALS_FILE
        self.assertTrue(os.path.exists(ALL_DECALS_FILE))
        with open(ALL_DECALS_FILE, "r", encoding="utf-8") as f:
            decals_db = json.load(f)

        # Replicate editor_gui logic
        decals_map = {}
        for d in decals_db:
            decals_map[d["id"]] = d
        for d in decals_db:
            base_id = d["id"][:-2] if d["id"].endswith("_P") else d["id"]
            if base_id not in decals_map:
                decals_map[base_id] = d
            p_id = f"{base_id}_P"
            if p_id not in decals_map:
                decals_map[p_id] = d

        std_decals = [d for d in decals_db if not d["id"].endswith("_P")]
        for d in std_decals:
            mapped = decals_map[d["id"]]
            self.assertEqual(mapped["id"], d["id"], f"{d['id']} was overwritten in decals_map")
            self.assertFalse(mapped.get("premium", False), f"{d['id']} should have premium=False")

    def test_collab_filtering_accuracy(self):
        """Ensure collaboration filters are authentic and do not leak false positives."""
        import json
        from core.helpers import ALL_DECALS_FILE
        with open(ALL_DECALS_FILE, "r", encoding="utf-8") as f:
            decals_db = json.load(f)

        from ui.tabs.decals_tab import GRAVITY_RUSH_DECAL_IDS
        k7_matches = []
        gr_matches = []
        wot_matches = []
        nmh_matches = []
        dv_matches = []

        for d in decals_db:
            did = d["id"]
            name_en = d.get("name_en", "")
            name_es = d.get("name_es", "")
            name_zh = d.get("name_zh", "")
            desc_en = d.get("desc_en", "")
            desc_es = d.get("desc_es", "")
            desc_zh = d.get("desc_zh", "")
            full_txt = f"{did} {name_en} {name_es} {name_zh} {desc_en} {desc_es} {desc_zh}".lower()

            # K7
            if "_k7" in did.lower() or any(k in full_txt for k in ["garcian", "dan smith", "kaede", "kevin", "coyote", "mask de smith", "con smith", "killer7", "harman", "iwazaru", "samantha", "queen of the wolves"]):
                k7_matches.append(did)
            # Gravity Rush (All 10 official decals: Nos. 162-172 in master_skill)
            if did in GRAVITY_RUSH_DECAL_IDS or "gravity rush" in full_txt:
                gr_matches.append(did)
            # WOT
            if "_wot" in did.lower() or "wot" in did.lower() or any(k in full_txt for k in ["world of tanks", "tiger ii", "t-34"]):
                wot_matches.append(did)
            # NMH
            if "_nmh" in did.lower() or any(k in full_txt for k in ["travis", "sylvia", "shinobu", "bad girl", "beam katana", "no more heroes"]):
                nmh_matches.append(did)
            # Deathverse
            if any(k in full_txt for k in ["deathverse", "uncle-d2", "bryan zemeckis"]):
                dv_matches.append(did)

        self.assertEqual(len(k7_matches), 22, "Killer7 must include all 22 official collab decals")
        self.assertIn("SKL_IWAZARU_K7", k7_matches)
        self.assertIn("SKL_SAMANTHA_K7", k7_matches)

        self.assertGreaterEqual(len(gr_matches), 20, "Gravity Rush must include all 10 decals (STD + PREM)")
        # Verify specific Gravity Rush decals
        self.assertIn("SKL_GRAVITY_DROPKICK_P", gr_matches, "Kat must be in Gravity Rush")
        self.assertIn("SKL_RG_STARTUP_SPDUP_P", gr_matches, "Raven must be in Gravity Rush")
        self.assertIn("SKL_NDFALL_AUSTEALTH_P", gr_matches, "Dusty must be in Gravity Rush")
        self.assertIn("SKL_DEFUP_DEATH_PROOF_P", gr_matches, "Kali Angel must be in Gravity Rush")
        self.assertIn("SKL_CRIUP_DECDUR_DOWN_P", gr_matches, "Durga Angel must be in Gravity Rush")
        self.assertIn("SKL_ATKUP_SLASHSTRIKE_P", gr_matches, "Jupiter Style must be in Gravity Rush")
        self.assertIn("SKL_STMUP_DASHDODGE_P", gr_matches, "Lunar Style must be in Gravity Rush")
        self.assertIn("SKL_HPUP_ATKUP_P", gr_matches, "Panther Mode must be in Gravity Rush")
        self.assertIn("SKL_HPCUREUP_03_P", gr_matches, "Apple must be in Gravity Rush")
        self.assertIn("SKL_MONEYUP_03_P", gr_matches, "Stasis Field must be in Gravity Rush")

        # Ensure NO Katana Addict or Hagakure leaked
        self.assertFalse(any("katana" in did.lower() for did in gr_matches), "Katana decals must not leak into Gravity Rush")

        self.assertEqual(len(wot_matches), 20, "WOT must have 20 decals (STD + PREM)")
        self.assertEqual(len(nmh_matches), 24, "NMH must have 24 decals (STD + PREM)")
        self.assertEqual(len(dv_matches), 4, "Deathverse must have 4 decals")

    def test_set_decals_filtering(self):
        """Ensure set decals filter includes all official armor synergy decals."""
        import json
        from core.helpers import ALL_DECALS_FILE
        with open(ALL_DECALS_FILE, "r", encoding="utf-8") as f:
            decals_db = json.load(f)

        set_matches = []
        for d in decals_db:
            did = d["id"]
            name_en = d.get("name_en", "")
            name_es = d.get("name_es", "")
            name_zh = d.get("name_zh", "")
            desc_en = d.get("desc_en", "")
            desc_es = d.get("desc_es", "")
            desc_zh = d.get("desc_zh", "")
            full_txt = f"{did} {name_en} {name_es} {name_zh} {desc_en} {desc_es} {desc_zh}".lower()

            is_set = (
                "_ability_up" in did.lower() or 
                "armor bonus" in desc_en.lower() or 
                "bonificación de armadura" in desc_es.lower() or 
                "套装" in desc_zh.lower() or 
                "full set" in desc_en.lower() or 
                "conjunto completo" in desc_es.lower() or 
                any(k in full_txt for k in ["cosplayer", "clay figurine", "combat diver", "happy wheeler", "trigger happy", "disparo alegre", "king of coal", "rey del carbón", "robin hood", "flashdance", "pinch hitter", "thunder road", "pro bowler", "hagakure"])
            )
            if is_set:
                set_matches.append(did)

        self.assertGreaterEqual(len(set_matches), 90, "Must detect at least 90 set synergy decals")
        self.assertIn("SKL_ASLTRFL_BULLET_UP", set_matches, "Trigger Happy must be recognized as set decal")
        self.assertIn("SKL_PECKER_ABILITY_UP", set_matches, "King of Coal must be recognized as set decal")

    def test_decal_deduplication_and_alias_sanitization(self):
        """Ensure all decal duplicate typos are cleaned and sanitized seamlessly."""
        import json
        from collections import defaultdict
        from core.helpers import ALL_DECALS_FILE
        from core.decals import DECAL_ALIASES, sanitize_save_decals

        with open(ALL_DECALS_FILE, "r", encoding="utf-8") as f:
            decals_db = json.load(f)

        # Check for zero duplicate IDs
        ids = [d["id"] for d in decals_db]
        self.assertEqual(len(ids), len(set(ids)), "Encyclopedia must not contain duplicate decal IDs")

        # Check for zero duplicate (name_en, premium)
        name_prem = [(d["name_en"], d.get("premium", False)) for d in decals_db]
        self.assertEqual(len(name_prem), len(set(name_prem)), "Encyclopedia must not contain duplicate (name, premium) entries")

        # Check that typo ID is eliminated and official ID is present
        self.assertNotIn("SKL_DEFUP_DEATHROOF_P", ids, "Legacy typo SKL_DEFUP_DEATHROOF_P must not exist in encyclopedia")
        self.assertIn("SKL_DEFUP_DEATH_PROOF_P", ids, "Official ID SKL_DEFUP_DEATH_PROOF_P must exist")

        # Verify save sanitization merges legacy typo with canonical ID
        dirty_save = {
            "user": {"uid": 999},
            "soul": {
                "uid": 999,
                "skl": {
                    "psskl": [
                        {"sklid": "SKL_DEFUP_DEATHROOF_P", "cnt": 3, "updated": 100},
                        {"sklid": "SKL_DEFUP_DEATH_PROOF_P", "cnt": 2, "updated": 200},
                        {"sklid": "SKLATROL_WOT_P", "cnt": 5, "updated": 300},
                    ],
                    "eqskl": {
                        "999": [
                            {"cid": "f_1", "sklid": "SKL_DEFUP_DEATHROOF_P", "pos": 0}
                        ]
                    }
                }
            }
        }
        sanitize_save_decals(dirty_save)
        cleaned_psskl = dirty_save["soul"]["skl"]["psskl"]
        decal_map = {d["sklid"]: d for d in cleaned_psskl}

        # Must merge into single SKL_DEFUP_DEATH_PROOF_P with max count 3
        self.assertNotIn("SKL_DEFUP_DEATHROOF_P", decal_map)
        self.assertIn("SKL_DEFUP_DEATH_PROOF_P", decal_map)
        self.assertEqual(decal_map["SKL_DEFUP_DEATH_PROOF_P"]["cnt"], 3)

        # SKLATROL_WOT_P must be converted to SKL_PATROL_WOT_P
        self.assertNotIn("SKLATROL_WOT_P", decal_map)
        self.assertIn("SKL_PATROL_WOT_P", decal_map)
        self.assertEqual(decal_map["SKL_PATROL_WOT_P"]["cnt"], 5)

        # Fighter eqskl must be updated
        self.assertEqual(dirty_save["soul"]["skl"]["eqskl"]["999"][0]["sklid"], "SKL_DEFUP_DEATH_PROOF_P")


if __name__ == "__main__":
    unittest.main()


