# -*- coding: utf-8 -*-
"""
Automated Test Suite for PySide6 + QSS UI.
Verifies theme, styles, main window, all 8 tabs, and dialogs.
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import unittest
import tempfile
import shutil
from unittest.mock import patch
import core.save_slots as save_slots

# Configure headless offscreen mode for automated test runner
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PySide6.QtWidgets import QApplication
from ui_qt.theme import load_stylesheet, get_qt_font, get_pixmap, get_icon, BG_DARK
from ui_qt.main_window import SaveEditorMainWindow
from ui_qt.dialogs import (
    ArmorSetViewerDialog,
    SmartInventoryAnalyzerDialog,
    InventoryViewerDialog,
    CreateFighterDialog,
    FighterModelGalleryDialog,
    SlotBackupsDialog,
    AccountCompatibilityDialog,
    QtUpdateNotificationDialog
)
import i18n
import modifiers

app = QApplication.instance()
if app is None:
    app = QApplication(sys.argv)


from PySide6.QtWidgets import QMessageBox, QInputDialog

class TestQtUI(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        for target, value in [
            ("ui_qt.main_window.get_default_save_path", lambda: None),
            ("save_io.get_default_save_path", lambda: None),
            ("save_io.get_all_detected_steam_dirs", lambda: []),
            ("updater.check_updates_background", lambda *a, **k: None),
            ("i18n.CONFIG_FILE", os.path.join(self.temp_dir.name, "config.json")),
            ("core.save_slots.PROJECT_SLOTS_DIR", os.path.join(self.temp_dir.name, "slots")),
            ("core.save_slots.ACTIVE_SLOT_FILE", os.path.join(self.temp_dir.name, "slots", "active_slot.json")),
        ]:
            p = patch(target, value)
            p.start()
            self.addCleanup(p.stop)
        self.orig_info = QMessageBox.information
        self.orig_warn = QMessageBox.warning
        self.orig_critical = QMessageBox.critical
        self.orig_quest = QMessageBox.question
        self.orig_input = QInputDialog.getInt

        QMessageBox.information = lambda *a, **k: QMessageBox.StandardButton.Ok
        QMessageBox.warning = lambda *a, **k: QMessageBox.StandardButton.Ok
        QMessageBox.critical = lambda *a, **k: QMessageBox.StandardButton.Ok
        QMessageBox.question = lambda *a, **k: QMessageBox.StandardButton.Yes
        QInputDialog.getInt = lambda *a, **k: (15, True)

        self.win = SaveEditorMainWindow()

    def tearDown(self):
        self.win.close()
        self.win.deleteLater()
        QMessageBox.information = self.orig_info
        QMessageBox.warning = self.orig_warn
        QMessageBox.critical = self.orig_critical
        QMessageBox.question = self.orig_quest
        QInputDialog.getInt = self.orig_input

    def test_theme_and_styles(self):
        qss = load_stylesheet()
        self.assertTrue(len(qss) > 100)
        self.assertIn("#TopFrame", qss)
        self.assertIn("#HudDashboard", qss)
        self.assertIn(".CurrencyBadge", qss)
        self.assertIn("QTabWidget::pane", qss)
        self.assertIn("QPushButton[accent=\"true\"]", qss)

        font = get_qt_font(9)
        self.assertIsNotNone(font)

        # Test icon resolution
        pix = get_pixmap("app_icon", (32, 32))
        # It's okay if pix is None or valid depending on asset presence
        ico = get_icon("dm", (18, 18))
        self.assertIsNotNone(ico)

    def test_main_window_structure_and_tabs(self):
        self.assertIsNotNone(self.win.tab_currencies)
        self.assertIsNotNone(self.win.tab_fighters)
        self.assertIsNotNone(self.win.tab_materials)
        self.assertIsNotNone(self.win.tab_decals)
        self.assertIsNotNone(self.win.tab_blueprints)
        self.assertIsNotNone(self.win.tab_mastery)
        self.assertIsNotNone(self.win.tab_tower)
        self.assertIsNotNone(self.win.tab_advanced)

        self.assertEqual(self.win.notebook.count(), 8)

    def test_language_switching_qt(self):
        for lang_name in ["Español", "English", "中文"]:
            idx = self.win.lang_cb.findText(lang_name)
            if idx >= 0:
                self.win.lang_cb.setCurrentIndex(idx)
                self.assertIsNotNone(self.win.lbl_file.text())

    def test_currencies_tab_actions(self):
        test_save = {
            "user": {"name": "Senpai", "playtime": 3600, "free_medal": 0, "paid_medal": 0},
            "soul": {
                "free_money": 0,
                "paid_money": 0,
                "spirit": 0,
                "bloodnium_point": 0,
                "recycle_point": 0,
                "safe_level": 1,
                "spirit_tank_level": 1,
                "rank": 1
            }
        }
        self.win.save_json = test_save
        self.win.tab_currencies.refresh_data()

        # Test max_all_currencies
        self.win.tab_currencies.max_all_currencies()
        curr = modifiers.get_player_currencies(test_save)
        self.assertEqual(curr["dm"], 9999)
        self.assertEqual(curr["kc"], 2560000)
        self.assertEqual(curr["spl"], 2560000)
        self.assertEqual(curr["bloodnium"], 999999)
        self.assertEqual(curr["re_points"], 999999)

        # Test apply_currencies with custom values
        self.win.tab_currencies.curr_entries["dm"].setText("123")
        self.win.tab_currencies.curr_entries["kc"].setText("456")
        self.win.tab_currencies.curr_entries["spl"].setText("789")
        self.win.tab_currencies.curr_entries["bl"].setText("1000")
        self.win.tab_currencies.curr_entries["re"].setText("2000")
        self.win.tab_currencies.apply_currencies()
        curr2 = modifiers.get_player_currencies(test_save)
        self.assertEqual(curr2["dm"], 123)
        self.assertEqual(curr2["kc"], 456)
        self.assertEqual(curr2["spl"], 789)
        self.assertEqual(curr2["bloodnium"], 1000)
        self.assertEqual(curr2["re_points"], 2000)

    def test_vip_pass_actions(self):
        test_save = {
            "user": {"name": "Senpai", "playtime": 3600},
            "soul": {
                "safe_level": 1,
                "spirit_tank_level": 1,
                "rank": 1,
                "vip": {"flag": 0, "pass_num": 0, "oneday_pass_num": 0, "expired_time": 0}
            }
        }
        self.win.save_json = test_save
        self.win.tab_currencies.refresh_data()

        # Check initial inactive VIP status
        vip_status = modifiers.get_vip_status(test_save)
        self.assertFalse(vip_status["active"])

        # Test activating VIP with 30 days + 99 passes
        self.win.tab_currencies._set_vip_entry_and_act(30, passes=99)
        vip_status = modifiers.get_vip_status(test_save)
        self.assertTrue(vip_status["active"])
        self.assertGreaterEqual(vip_status["days_left"], 29)
        self.assertEqual(test_save["soul"]["vip"]["pass_num"], 99)
        self.assertEqual(test_save["soul"]["vip"]["friendship"], 1)

        # Test deactivating VIP
        self.win.tab_currencies._deactivate_vip_action()
        vip_status = modifiers.get_vip_status(test_save)
        self.assertFalse(vip_status["active"])

    def test_perks_and_account_actions(self):
        test_save = {
            "user": {"name": "Senpai", "playtime": 3600, "user_id": "U12345", "steam_id": "76561198000000000"},
            "soul": {
                "login_streak": 5,
                "safe_level": 1,
                "spirit_tank_level": 1,
                "rank": 1
            },
            "fighter": [
                {"name": "Fighter 1", "bag_size": 20}
            ]
        }
        self.win.save_json = test_save
        self.win.tab_currencies.refresh_data()

        # Test expand death bag
        self.win.tab_currencies.cb_bag.setCurrentText("50")
        self.win.tab_currencies._expand_bag_action()
        self.assertEqual(test_save["soul"]["bag_slot"], 50)

        # Test free continues
        self.win.tab_currencies.ent_free_cont.setText("999")
        self.win.tab_currencies._set_continues_action()
        self.assertEqual(test_save["soul"].get("free_continue_count", 0), 999)

        # Test max login streak
        self.win.tab_currencies._max_login_streak_action()
        self.assertEqual(test_save["user"]["login_keep"], 365)

    def test_tower_tab_actions(self):
        test_save = {
            "soul": {
                "tdm_rank": "TDM_RANK_01_03",
                "tdm_point": 500,
            },
            "floor": {
                "rlg": {"user": {"stuck": True}},
                "pop": {"item": {"something": 1}}
            },
            "playlog": {
                "base": {
                    "max_floor": 10,
                    "interruption": 5,
                    "elevator_cnt": 3,
                    "escalator_cnt": 8,
                    "total_get_material_cnt": 50,
                    "total_research_cnt": 2,
                    "circle_crusher": 1,
                    "total_play_time": 7200
                }
            }
        }
        self.win.save_json = test_save
        self.win.tab_tower.refresh_data()

        # Test set max floor
        self.win.tab_tower.entry_max_floor.setText("80")
        self.win.tab_tower._set_max_floor_action()
        self.assertEqual(test_save["playlog"]["base"]["max_floor"], 80)

        # Test reset interruptions
        self.win.tab_tower._reset_interrupt_action()
        self.assertEqual(test_save["playlog"]["base"]["interruption"], 0)

        # Test rescue stuck fighter
        self.win.tab_tower._rescue_stuck_fighter_action()
        self.assertEqual(test_save["floor"]["rlg"], {"user": {}, "archive": {}})

        # Test TDM rank and points
        self.win.tab_tower.cb_tdm_rank.setCurrentIndex(0)  # Diamante I (5000)
        self.win.tab_tower._set_tdm_rank_action()
        self.assertEqual(test_save["soul"]["tdm_rank"], "TDM_RANK_05_03")
        self.assertEqual(test_save["soul"]["tdm_point"], 5000)

    def test_advanced_tab_and_cache(self):
        self.win.tab_advanced.update_cache_stats()
        self.assertIn("MB", self.win.tab_advanced.asset_stats_lbl.text())
        self.win.tab_advanced.refresh_slots_view()

    def test_real_save_loading_and_saving(self):
        real_path = os.path.join(BASE_DIR, "CurrentSave", "76561198324473152.sav")
        if os.path.exists(real_path):
            copy_path = os.path.join(self.temp_dir.name, "fixture.sav")
            shutil.copy2(real_path, copy_path)
            self.win.load_save(copy_path)
            self.assertIsNotNone(self.win.save_json)
            # Verify that list structures are lists
            self.assertIsInstance(self.win.save_json.get("soul", {}).get("cl", []), list)
            # Verify HUD updated
            self.assertIn("DM", self.win.hud_dm_lbl.text())

    def test_dialogs_instantiation(self):
        test_save = {
            "user": {"name": "Senpai", "playtime": 3600},
            "save_count": 1,
            "soul": {
                "cl": [{"slot": i, "type": -1, "eid": ""} for i in range(1500)],
                "partresearch": {"user": []}
            },
            "fighter": [],
            "storage": {"part": []},
            "item": {"items": []},
            "part": {"pts": []},
            "mushroom": {"msrs": []},
            "beast": {"bsts": []},
            "money": {"dm": 10, "kc": 50000, "spl": 25000},
        }

        from PySide6.QtWidgets import QMessageBox, QInputDialog
        orig_info = QMessageBox.information
        orig_warn = QMessageBox.warning
        orig_quest = QMessageBox.question
        orig_input = QInputDialog.getInt
        try:
            QMessageBox.information = lambda *a, **k: QMessageBox.StandardButton.Ok
            QMessageBox.warning = lambda *a, **k: QMessageBox.StandardButton.Ok
            QMessageBox.question = lambda *a, **k: QMessageBox.StandardButton.Yes
            QInputDialog.getInt = lambda *a, **k: (15, True)

            # Create Fighter Dialog
            self.win.save_json = test_save
            dlg_fighter = CreateFighterDialog(self.win)
            self.assertIsNotNone(dlg_fighter)
            dlg_fighter.close()

            # Smart Analyzer Dialog
            dlg_analyzer = SmartInventoryAnalyzerDialog(self.win, test_save)
            self.assertIsNotNone(dlg_analyzer)
            dlg_analyzer._on_supply_missing()
            dlg_analyzer.close()

            # Armor Set Viewer Dialog with real/mock tiers
            mock_sets = [{
                "id": "diy_attack",
                "name": "DIY Attack Set",
                "faction": "D.O.D. ARMS",
                "tiers": [
                    {
                        "tier_num": 1,
                        "tier_name": "Tier 1",
                        "head": {"id": "PT_DIY_HEAD_001", "name": "DIY Head", "def": 14, "def_plus4": 21, "durability": 500},
                        "body": {"id": "PT_DIY_TOPS_001", "name": "DIY Body", "def": 51, "def_plus4": 76, "durability": 875},
                        "legs": {"id": "PT_DIY_BTM_001", "name": "DIY Legs", "def": 35, "def_plus4": 52, "durability": 687},
                        "weapon": {"id": "PT_ARM_WP001_01", "name": "Machete", "atk": 25, "atk_plus4": 37, "durability": 1400}
                    },
                    {
                        "tier_num": 2,
                        "tier_name": "Tier 2",
                        "head": {"id": "PT_DIY_HEAD_002", "name": "DIY Head +", "def": 50, "def_plus4": 75, "durability": 500}
                    }
                ]
            }]
            dlg_armor = ArmorSetViewerDialog(self.win, test_save, mock_sets)
            self.assertIsNotNone(dlg_armor)
            self.assertTrue(dlg_armor.tier_buttons[0][1].isEnabled())
            self.assertTrue(dlg_armor.tier_buttons[1][1].isEnabled())
            self.assertFalse(dlg_armor.tier_buttons[2][1].isEnabled())
            dlg_armor.switch_tier(2)
            self.assertEqual(dlg_armor.current_tier_num, 2)
            dlg_armor.unlock_single_piece("PT_DIY_HEAD_002")
            dlg_armor.add_single_piece_storage("PT_DIY_HEAD_002")
            dlg_armor.close()

            # Slot Backups Dialog
            dlg_backups = SlotBackupsDialog(self.win, 1)
            self.assertIsNotNone(dlg_backups)
            dlg_backups.close()

            # Account Compatibility Dialog
            dlg_rebind = AccountCompatibilityDialog(self.win)
            self.assertIsNotNone(dlg_rebind)
            dlg_rebind.close()

            # Update Notification Dialog
            dlg_update = QtUpdateNotificationDialog(self.win, {"version": "4.3.0", "release_date": "2026-09-10", "changelog": ["Feature A", "Fix B"]})
            self.assertIsNotNone(dlg_update)
            dlg_update.close()
        finally:
            QMessageBox.information = orig_info
            QMessageBox.warning = orig_warn
            QMessageBox.question = orig_quest
            QInputDialog.getInt = orig_input


if __name__ == "__main__":
    unittest.main()
