# -*- coding: utf-8 -*-
import unittest
import os
import shutil
import tempfile
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import save_io
from tests.test_save_io import REAL_SAVE_PATH
import core.account_rebind as account_rebind
import core.save_slots as save_slots

REDDIT_SAVE_PATH = r"C:\Users\sipi_\Downloads\RESPALDO_SAVE_LID\76561198658148665.sav"


class TestAccountRebind(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.save_data, self.version = save_io.decompress_save(REAL_SAVE_PATH)

    def tearDown(self):
        if os.path.exists(self.tmp_dir):
            shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_extract_save_identity(self):
        ident = account_rebind.extract_save_identity(self.save_data)
        self.assertEqual(ident["steam_id"], "76561198324473152")
        self.assertEqual(ident["player_name"], "Geus")
        self.assertEqual(ident["uid"], "1")
        self.assertFalse(ident["has_session_tokens"])
        self.assertEqual(ident["fighter_name"], "Allyson")
        self.assertEqual(ident["max_floor"], 55)

    def test_is_foreign_save(self):
        self.assertFalse(account_rebind.is_foreign_save(self.save_data, "76561198324473152"))
        self.assertTrue(account_rebind.is_foreign_save(self.save_data, "76561198658148665"))

    def test_rebind_save_to_account_steam_id_and_tokens(self):
        # Create a copy with dummy session tokens
        import copy
        mod_save = copy.deepcopy(self.save_data)
        mod_save["user"]["skey"] = "12345"
        mod_save["user"]["sid"] = "abcdef"
        mod_save["user"]["uuid"] = "uuid-test"
        mod_save["user"]["olid"] = "olid-test"

        account_rebind.rebind_save_to_account(
            mod_save,
            target_steam_id="76561198999999999",
            clear_session_tokens=True
        )

        self.assertEqual(mod_save["user"]["psnacid"], "76561198999999999")
        self.assertEqual(mod_save["user"]["skey"], "")
        self.assertEqual(mod_save["user"]["sid"], "")
        self.assertEqual(mod_save["user"]["uuid"], "")
        self.assertEqual(mod_save["user"]["olid"], "")

    def test_rebind_save_to_account_with_player_name(self):
        import copy
        mod_save = copy.deepcopy(self.save_data)

        account_rebind.rebind_save_to_account(
            mod_save,
            target_steam_id="76561198324473152",
            target_player_name="UncleDeathFan"
        )
        self.assertEqual(mod_save["user"]["nm"], "UncleDeathFan")

    def test_rebind_save_to_account_with_uid_harmonization(self):
        import copy
        mod_save = copy.deepcopy(self.save_data)
        old_uid = str(mod_save["user"]["uid"])
        new_uid = "999"

        account_rebind.rebind_save_to_account(
            mod_save,
            target_steam_id="76561198324473152",
            target_uid=new_uid
        )

        self.assertEqual(mod_save["user"]["uid"], 999)
        self.assertEqual(mod_save["soul"]["uid"], 999)
        self.assertIn("999", mod_save["bodyuser"])
        self.assertNotIn(old_uid, mod_save["bodyuser"])

    def test_adapt_and_save_external_file_roundtrip(self):
        dest_file = os.path.join(self.tmp_dir, "rebound_save.sav")
        ok, rebound_data, meta = account_rebind.adapt_and_save_external_file(
            REAL_SAVE_PATH,
            dest_file,
            target_steam_id="76561198000011111",
            target_player_name="AdaptedHero"
        )
        self.assertTrue(ok)
        self.assertTrue(os.path.exists(dest_file))
        self.assertEqual(meta["player_name"], "AdaptedHero")

        # Verify reading saved file back
        read_data, ver = save_io.decompress_save(dest_file)
        self.assertEqual(read_data["user"]["psnacid"], "76561198000011111")
        self.assertEqual(read_data["user"]["nm"], "AdaptedHero")

    def test_rebind_with_reddit_user_save(self):
        if not os.path.exists(REDDIT_SAVE_PATH):
            self.skipTest(f"Reddit save not found at {REDDIT_SAVE_PATH}")

        r_data, r_ver = save_io.decompress_save(REDDIT_SAVE_PATH)
        orig_ident = account_rebind.extract_save_identity(r_data)
        self.assertEqual(orig_ident["steam_id"], "76561198658148665")
        self.assertEqual(orig_ident["player_name"], "Braulky2")
        self.assertTrue(orig_ident["has_session_tokens"])

        # Adapt to user's Steam ID
        account_rebind.rebind_save_to_account(
            r_data,
            target_steam_id="76561198324473152",
            target_player_name="Geus",
            clear_session_tokens=True
        )

        self.assertEqual(r_data["user"]["psnacid"], "76561198324473152")
        self.assertEqual(r_data["user"]["nm"], "Geus")
        self.assertEqual(r_data["user"]["skey"], "")
        self.assertEqual(r_data["user"]["sid"], "")

        # Test importing directly into a slot with auto-rebind
        save_slots.PROJECT_SLOTS_DIR = os.path.join(self.tmp_dir, "Slots")
        save_slots.ensure_slots_directory()

        slot_info = save_slots.import_save_file_to_slot(
            REDDIT_SAVE_PATH,
            slot_num=1,
            target_steam_id="76561198324473152",
            target_player_name="Geus"
        )
        self.assertEqual(slot_info["meta"]["steam_id"], "76561198324473152")
        self.assertEqual(slot_info["meta"]["player_name"], "Geus")
        self.assertEqual(slot_info["meta"]["max_floor"], 69)


if __name__ == "__main__":
    unittest.main()
