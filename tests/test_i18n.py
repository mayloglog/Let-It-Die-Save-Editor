# -*- coding: utf-8 -*-
import unittest
import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import i18n
from i18n import t

class TestI18n(unittest.TestCase):
    def test_key_parity_between_languages(self):
        es_keys = set(i18n.TRANSLATIONS["es"].keys())
        en_keys = set(i18n.TRANSLATIONS["en"].keys())
        zh_keys = set(i18n.TRANSLATIONS["zh"].keys())
        self.assertEqual(len(es_keys ^ en_keys), 0, f"ES/EN mismatch: {es_keys ^ en_keys}")
        self.assertEqual(len(en_keys ^ zh_keys), 0, f"EN/ZH mismatch: {en_keys ^ zh_keys}")
        self.assertGreater(len(es_keys), 400)

    def test_translation_formatting(self):
        i18n.set_language("en")
        s_en = t("inv_cap_lbl", used=10, total=100, free=90, pct=10.0)
        self.assertIn("10", s_en)
        self.assertIn("100", s_en)
        self.assertIn("Locker", s_en)
        
        i18n.set_language("es")
        s_es = t("inv_cap_lbl", used=10, total=100, free=90, pct=10.0)
        self.assertIn("10", s_es)
        self.assertIn("Almacén", s_es)

        i18n.set_language("zh")
        s_zh = t("inv_cap_lbl", used=10, total=100, free=90, pct=10.0)
        self.assertIn("10", s_zh)
        self.assertIn("仓库", s_zh)

    def test_locales_directory_loading(self):
        self.assertTrue(os.path.isdir(i18n.LOCALES_DIR))
        available = i18n.get_available_languages()
        self.assertIn("es", available)
        self.assertIn("en", available)
        self.assertIn("zh", available)

    def test_entity_helpers(self):
        fake_item = {
            "id": "TEST_ITEM_01",
            "name_en": "Super Armor",
            "name_es": "Súper Armadura",
            "desc_en": "Protects against attacks.",
            "desc_es": "Protege contra ataques."
        }
        i18n.set_language("en")
        self.assertEqual(i18n.get_item_name(fake_item), "Super Armor")
        self.assertEqual(i18n.get_item_desc(fake_item), "Protects against attacks.")

        i18n.set_language("es")
        self.assertEqual(i18n.get_item_name(fake_item), "Súper Armadura")
        self.assertEqual(i18n.get_item_desc(fake_item), "Protege contra ataques.")

        i18n.set_language("zh")
        # Falls back to en if no zh name provided
        self.assertEqual(i18n.get_item_name(fake_item), "Super Armor")

    def test_weapon_expert_localization(self):
        i18n.set_language("es")
        self.assertEqual(i18n.get_expert_weapon_name("PTARMTP_00"), "Manos Desnudas")
        i18n.set_language("en")
        self.assertEqual(i18n.get_expert_weapon_name("PTARMTP_00"), "Bare Fists")
        i18n.set_language("zh")
        self.assertEqual(i18n.get_expert_weapon_name("PTARMTP_00"), "空手")

    def test_default_language_is_en_and_persists_user_choice(self):
        self.assertEqual(i18n.DEFAULT_LANGUAGE, "en")
        
        # Test preference saving and loading
        i18n.set_language("es")
        self.assertEqual(i18n.get_language(), "es")
        self.assertEqual(i18n.load_saved_language(), "es")

        i18n.set_language("zh")
        self.assertEqual(i18n.get_language(), "zh")
        self.assertEqual(i18n.load_saved_language(), "zh")

        i18n.set_language("en")
        self.assertEqual(i18n.get_language(), "en")
        self.assertEqual(i18n.load_saved_language(), "en")

    def test_multilingual_filter_tokens(self):
        from ui.tabs.materials_tab import MaterialsTabMixin

        for lang in ("es", "en", "zh"):
            i18n.set_language(lang)
            for k in ("mat_all", "decal_all", "bp_slot_all", "bp_fac_all", "bp_poss_all", "bp_dmg_all"):
                val = t(k)
                self.assertTrue(bool(val), f"Missing translation for {k} in {lang}")
            
            # Universal 'All' filter pass-through
            all_token = t("mat_all")
            self.assertTrue(MaterialsTabMixin._match_material_category(all_token, "Aluminio (Aluminum)"))
            self.assertTrue(MaterialsTabMixin._match_material_category(all_token, "Boss Metals"))

        # Category matching with Chinese labels
        self.assertTrue(MaterialsTabMixin._match_material_category("铝 (Aluminum)", "Aluminio"))
        self.assertTrue(MaterialsTabMixin._match_material_category("铜 (Copper)", "Cobre (Copper)"))
        self.assertTrue(MaterialsTabMixin._match_material_category("铁与钢 (Iron & Steel)", "Hierro y Acero"))
        self.assertTrue(MaterialsTabMixin._match_material_category("Boss金属 (Boss Metals)", "Boss Metals"))
        self.assertTrue(MaterialsTabMixin._match_material_category("类固醇 / Rostest (Fighters)", "Esteroides / Rostest"))

    def test_get_entity_display_title(self):
        fake_gear = {
            "id": "WEAPON_TEST",
            "name_en": "Laser Saber",
            "name_es": "Sable Láser",
            "name_zh": "激光军刀"
        }
        i18n.set_language("es")
        self.assertEqual(i18n.get_entity_display_title(fake_gear), "Sable Láser")
        self.assertEqual(i18n.get_entity_display_title(fake_gear, with_en_subtitle=True), "Sable Láser (Laser Saber)")

        i18n.set_language("en")
        self.assertEqual(i18n.get_entity_display_title(fake_gear), "Laser Saber")

        i18n.set_language("zh")
        self.assertEqual(i18n.get_entity_display_title(fake_gear), "激光军刀")
        self.assertEqual(i18n.get_entity_display_title(fake_gear, with_en_subtitle=True), "激光军刀 (Laser Saber)")

    def test_canonical_material_categories_and_forge_keys(self):
        from ui.tabs.materials_tab import CANONICAL_MATERIAL_CATEGORIES

        for lang in ("es", "en", "zh"):
            i18n.set_language(lang)
            for _, cat_key in CANONICAL_MATERIAL_CATEGORIES:
                label = t(cat_key)
                self.assertTrue(bool(label) and label != cat_key, f"Missing category translation: {cat_key} in {lang}")

            for forge_code in ("store_uncapped", "rnd_uncapped", "store_plus4", "store", "finished_lvl", "remodel", "map"):
                k = f"bp_forge_{forge_code}"
                rendered = t(k, plus_lvl=4, next_lvl=5, level=4)
                self.assertTrue(bool(rendered) and rendered != k, f"Missing forge key: {k} in {lang}")

    def test_system_language_detection(self):
        detected = i18n._detect_system_language()
        self.assertIsInstance(detected, str)
        self.assertIn(detected, i18n.get_available_languages())

    def test_gui_tabs_filtering_in_all_languages(self):
        from editor_gui import CompleteSaveEditorGUI
        app = CompleteSaveEditorGUI()
        app.withdraw()
        try:
            for lang in ("es", "en", "zh"):
                i18n.set_language(lang)
                app.filter_blueprints_list()
                app.filter_materials_list()
                app.filter_decals_list()
        finally:
            app.destroy()

    def test_locales_linter_validation(self):
        from tools.validate_locales import validate_all_locales
        is_valid, errors, stats = validate_all_locales()
        self.assertTrue(is_valid, f"Locales validation failed: {errors}")
        self.assertGreater(stats.get("total_keys_by_lang", {}).get("en", 0), 800)

    def test_fighter_classes_localized(self):
        from game_data import get_fighter_class_name
        i18n.set_language("en")
        self.assertEqual(get_fighter_class_name("BAL"), "All-Rounder")
        self.assertEqual(get_fighter_class_name("BRE"), "Striker")

        i18n.set_language("es")
        self.assertEqual(get_fighter_class_name("BAL"), "Todo Terreno")
        self.assertEqual(get_fighter_class_name("BRE"), "Delantero")

        i18n.set_language("zh")
        self.assertEqual(get_fighter_class_name("BAL"), "全能战士")
        self.assertEqual(get_fighter_class_name("BRE"), "强攻手")

    def test_real_bag_calculating_localized(self):
        i18n.set_language("en")
        self.assertIn("Calculating", t("f_real_bag_calculating"))
        i18n.set_language("es")
        self.assertIn("Calculando", t("f_real_bag_calculating"))
        i18n.set_language("zh")
        self.assertIn("计算中", t("f_real_bag_calculating"))

    def test_canonical_category_id_matching(self):
        from ui.tabs.materials_tab import MaterialsTabMixin
        dummy_mat = {"itemid": "ITMT_ALUMI_1", "category_id": "ALUMINUM", "category": "Aluminio"}
        for lang in ("en", "es", "zh"):
            i18n.set_language(lang)
            # Both canonical code and translated label should match
            self.assertTrue(MaterialsTabMixin._match_material_category("ALUMINUM", dummy_mat))
            self.assertTrue(MaterialsTabMixin._match_material_category(t("mat_cat_aluminum"), dummy_mat))
            self.assertFalse(MaterialsTabMixin._match_material_category("COPPER", dummy_mat))
            self.assertFalse(MaterialsTabMixin._match_material_category(t("mat_cat_copper"), dummy_mat))

    def test_weapon_damage_type_language_agnostic(self):
        from ui.tabs.blueprints_tab import BlueprintsTabMixin
        mixin = BlueprintsTabMixin()
        # Test purely by ID (no names attached)
        self.assertEqual(mixin._get_weapon_damage_type({"id": "PT_ARM_WP001_001"}), "SLASH")
        self.assertEqual(mixin._get_weapon_damage_type({"id": "PT_ARM_WP005_001"}), "BLUNT")
        self.assertEqual(mixin._get_weapon_damage_type({"id": "PT_ARM_WP004_001"}), "PIERCE")
        self.assertEqual(mixin._get_weapon_damage_type({"id": "PT_ARM_WP007_001"}), "FIRE")
        self.assertEqual(mixin._get_weapon_damage_type({"id": "PT_ARM_WP055_001"}), "ELECTRIC")
        # Poison weapons
        self.assertEqual(mixin._get_weapon_damage_type({"id": "PT_ARM_WP020_001"}), "POISON")
        self.assertEqual(mixin._get_weapon_damage_type({"id": "PT_ARM_WP042_001"}), "POISON")
        self.assertEqual(mixin._get_weapon_damage_type({"id": "PT_ARM_WP048_001"}), "POISON")
        self.assertEqual(mixin._get_weapon_damage_type({"id": "PT_ARM_WP058_001"}), "POISON")
        # Test with Tengoku Tier 4 uncap ID (no name)
        self.assertEqual(mixin._get_weapon_damage_type({"id": "PT_ARM_WP001_0H4"}), "SLASH")
        self.assertEqual(mixin._get_weapon_damage_type({"id": "PT_ARM_WP042_0H4"}), "POISON")

    def test_weapon_multi_damage_types(self):
        """Verify hybrid weapons support multiple damage attributes simultaneously."""
        from ui.tabs.blueprints_tab import BlueprintsTabMixin
        mixin = BlueprintsTabMixin()
        
        # 1. Enriched item with damage_types list
        spiked_bat = {
            "id": "PT_ARM_WP005_002",
            "name_en": "Spiked Bat",
            "damage_types": ["BLUNT", "POISON"],
            "damage_attr": {"BLUNT": 50, "POISON": 50}
        }
        bat_types = mixin._get_weapon_damage_types(spiked_bat)
        self.assertIn("BLUNT", bat_types)
        self.assertIn("POISON", bat_types)
        self.assertNotIn("SLASH", bat_types)

        machete = {
            "id": "PT_ARM_WP001_004",
            "name_en": "Battle Machete",
            "damage_types": ["SLASH", "FIRE"],
            "damage_attr": {"SLASH": 60, "FIRE": 40}
        }
        machete_types = mixin._get_weapon_damage_types(machete)
        self.assertIn("SLASH", machete_types)
        self.assertIn("FIRE", machete_types)
        self.assertNotIn("BLUNT", machete_types)

        # 2. Verify encyclopedia items contain poison weapons
        import json
        import os
        from core.helpers import ALL_EQUIPMENT_FILE
        if os.path.exists(ALL_EQUIPMENT_FILE):
            with open(ALL_EQUIPMENT_FILE, "r", encoding="utf-8") as f:
                encyclopedia = json.load(f)
            poison_weapons = [
                item for item in encyclopedia
                if "POISON" in mixin._get_weapon_damage_types(item)
            ]
            self.assertGreaterEqual(len(poison_weapons), 10, "Poison filter must return weapons from encyclopedia")

    def test_gender_and_forcemen_keys_parity(self):
        for lang in ("en", "es", "zh"):
            i18n.set_language(lang)
            for k in ("gender_female", "gender_male", "bp_set_white_steel", "bp_set_red_napalm", "bp_set_black_thunder", "bp_set_pale_wind", "f_tut_btn"):
                val = t(k)
                self.assertTrue(bool(val) and val != k, f"Missing or unrendered key {k} in {lang}")

    def test_equipment_chinese_localization(self):
        from core.helpers import ALL_EQUIPMENT_FILE
        import json
        with open(ALL_EQUIPMENT_FILE, "r", encoding="utf-8") as f:
            items = json.load(f)
        
        machete = next((it for it in items if it.get("id") == "PT_ARM_WP001_001"), None)
        self.assertIsNotNone(machete)
        self.assertEqual(machete.get("name_zh"), "丛林大砍刀")
        
        i18n.set_language("zh")
        self.assertEqual(i18n.get_item_name(machete), "丛林大砍刀")
        
        i18n.set_language("en")
        self.assertEqual(i18n.get_item_name(machete), "Jungle Machete")
        
        i18n.set_language("es")
        self.assertEqual(i18n.get_item_name(machete), "Machete de selva")

    def test_get_ui_font(self):
        from ui.theme import get_ui_font
        i18n.set_language("zh")
        font_zh = get_ui_font()
        self.assertEqual(font_zh[0], "Microsoft YaHei UI")
        
        i18n.set_language("en")
        font_en = get_ui_font()
        self.assertEqual(font_en[0], "Segoe UI")
    def test_dynamic_font_and_search_integration(self):
        from editor_gui import CompleteSaveEditorGUI
        app = CompleteSaveEditorGUI()
        app.withdraw()
        try:
            i18n.set_language("zh")
            app._apply_dynamic_fonts()
            self.assertIn("YaHei", str(app.style.lookup(".", "font")))
            
            i18n.set_language("en")
            app._apply_dynamic_fonts()
            self.assertIn("Segoe", str(app.style.lookup(".", "font")))
        finally:
            app.destroy()


if __name__ == "__main__":
    unittest.main()

