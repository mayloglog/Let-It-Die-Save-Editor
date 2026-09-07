"""Integration contracts between the new UI and the original save engine."""
import ast
import copy
import importlib
import inspect
import os
from pathlib import Path
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from tests import test_qt_ui as harness
import modifiers
import save_io
import core.save_slots as save_slots
from ui_qt.save_actions import set_material_quantity, inventory_counts
from ui_qt.dialogs.account_compatibility_dialog import AccountCompatibilityDialog
from ui_qt.dialogs.inventory_viewer import InventoryViewerDialog
from ui_qt.dialogs.smart_analyzer import SmartInventoryAnalyzerDialog
from ui_qt.dialogs.armor_set_viewer import ArmorSetViewerDialog


class TestQtLogic(unittest.TestCase):
    setUp = harness.TestQtUI.setUp
    tearDown = harness.TestQtUI.tearDown

    def fixture(self):
        data, version = save_io.decompress_save(os.path.join(harness.BASE_DIR, "CurrentSave", "76561198324473152.sav"))
        self.win.save_json = data
        self.win.version = version
        self.win.save_path = None
        self.win.refresh_all_views()
        return data

    def test_all_qt_backend_calls_exist_and_match_signatures(self):
        modules = {alias: importlib.import_module(name) for alias, name in (
            ("modifiers", "modifiers"), ("save_slots", "core.save_slots"),
            ("account_rebind", "core.account_rebind"), ("save_io", "save_io"),
            ("updater", "updater"))}
        for path in (Path(harness.BASE_DIR) / "ui_qt").rglob("*.py"):
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8-sig"))):
                if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                        and isinstance(node.func.value, ast.Name) and node.func.value.id in modules):
                    continue
                with self.subTest(file=str(path), line=node.lineno):
                    function = getattr(modules[node.func.value.id], node.func.attr)
                    if any(isinstance(a, ast.Starred) for a in node.args) or any(k.arg is None for k in node.keywords):
                        continue
                    inspect.signature(function).bind(*[None for _ in node.args], **{k.arg: None for k in node.keywords})

    def test_save_button_writes_once_and_roundtrips(self):
        data = self.fixture()
        self.win.save_path = os.path.join(self.temp_dir.name, "active.sav")
        with patch("save_io.save_to_file", wraps=save_io.save_to_file) as write:
            self.win.save_current()
            self.assertEqual(write.call_count, 1)
        actual, version = save_io.decompress_save(self.win.save_path)
        self.assertEqual(actual, data)
        self.assertEqual(version, self.win.version)

    def test_failed_autosave_is_reported_and_propagated(self):
        self.win.save_json = {"user": {}}
        self.win.save_path = os.path.join(self.temp_dir.name, "active.sav")
        self.win.version = 2
        with patch("ui_qt.main_window.save_to_file", side_effect=PermissionError("write denied")), patch.object(self.win, "_notify") as notify:
            with self.assertRaises(PermissionError):
                self.win._auto_save()
            notify.assert_called_once()

    def test_dialogs_save_once(self):
        data = self.fixture()
        for dialog in (SmartInventoryAnalyzerDialog(self.win, data), ArmorSetViewerDialog(self.win, data, self.win.armor_sets)):
            with self.subTest(dialog=type(dialog).__name__), patch.object(self.win, "_auto_save") as save:
                dialog._auto_save_and_sync()
                save.assert_called_once_with()
            dialog.close()

    def test_selected_fighter_edit_and_max_leave_others_unchanged(self):
        data = self.fixture()
        tab = self.win.tab_fighters
        tab.current_fighter_idx = 1
        tab.refresh_data()
        uid = modifiers.get_player_uid(data)
        other = copy.deepcopy(data["bodyuser"][uid][0])
        tab.name_entry.setText("Qt regression")
        tab.stat_spins["str"].setValue(32)
        tab._save_fighter_changes()
        info = modifiers.get_all_fighters_info(data)[1]
        self.assertEqual(info["name"], "Qt regression")
        self.assertEqual(info["str"], 32)
        self.assertEqual(data["bodyuser"][uid][0], other)
        expected = copy.deepcopy(data)
        modifiers.max_fighter_level_and_stats(expected, fighter_index=1, level=247)
        tab.max_current_fighter()
        self.assertEqual(modifiers.get_all_fighters_info(data)[1]["level"], 247)
        self.assertEqual(data["bodyuser"], expected["bodyuser"])

    def test_fighter_death_status_uses_engine_field(self):
        data = self.fixture()
        uid = modifiers.get_player_uid(data)
        data["bodyuser"][uid][0]["die"] = 1
        self.win.tab_fighters.refresh_data()
        self.assertIn("💀", self.win.tab_fighters.tree.topLevelItem(0).text(3))

    def test_material_exact_quantity_and_quick_add_are_distinct(self):
        for mid in ("IT_TEST", "MSR_TEST", "BST_TEST"):
            with self.subTest(material=mid):
                data = {"soul": {"cl": []}}
                modifiers.add_material_to_storage(data, mid, count=20)
                set_material_quantity(data, mid, 50)
                self.assertEqual(modifiers.analyze_storage_stock(data)["stock_by_id"][mid], 50)
                modifiers.add_material_to_storage(data, mid, count=10)
                self.assertEqual(modifiers.analyze_storage_stock(data)["stock_by_id"][mid], 60)
                set_material_quantity(data, mid, 3)
                self.assertEqual(modifiers.analyze_storage_stock(data)["stock_by_id"][mid], 3)
                set_material_quantity(data, mid, 0)
                self.assertEqual(modifiers.analyze_storage_stock(data)["used_slots"], 0)

    def test_material_removal_preserves_bag_and_other_stock(self):
        data = {"item": {"items": [{"eid": "bag", "itemid": "IT_TEST", "owner": "cid"}]}, "soul": {"cl": []}}
        modifiers.add_material_to_storage(data, "IT_TEST", 5)
        modifiers.add_material_to_storage(data, "IT_OTHER", 2)
        set_material_quantity(data, "IT_TEST", 0)
        self.assertIn({"eid": "bag", "itemid": "IT_TEST", "owner": "cid"}, data["item"]["items"])
        self.assertEqual(modifiers.analyze_storage_stock(data)["stock_by_id"]["IT_OTHER"], 2)

    def test_catalog_selection_survives_refresh(self):
        self.fixture()
        for tab, selection, getter in (
            (self.win.tab_materials, "current_selected_mat", lambda v: v[0]),
            (self.win.tab_blueprints, "current_selected_bp", lambda v: v["id"]),
            (self.win.tab_decals, "current_selected_decal", lambda v: v["id"]),
        ):
            with self.subTest(tab=type(tab).__name__):
                tab.table.selectRow(2)
                selected_id = getter(getattr(tab, selection))
                tab.refresh_data()
                self.assertEqual(getter(getattr(tab, selection)), selected_id)

    def test_inventory_reads_real_entities_and_filters_bag(self):
        data = self.fixture()
        dialog = InventoryViewerDialog(self.win, data)
        self.assertGreater(dialog.table.rowCount(), 0)
        counts = inventory_counts(data)
        self.assertTrue(any(key[2] == "GEAR" for key in counts))
        dialog.cat_cb.setCurrentIndex(dialog.cat_cb.findData("BAG"))
        from i18n import t
        for row in range(dialog.table.rowCount()):
            self.assertEqual(dialog.table.item(row, 4).text(), t("inv_loc_bag"))
        dialog.close()

    def test_premium_decal_keeps_selected_id_when_metadata_is_standard(self):
        self.win.save_json = {"soul": {"skl": {"psskl": []}}}
        tab = self.win.tab_decals
        # A premium inventory entry may reuse standard encyclopedia metadata.
        base_id = next(d["id"] for d in self.win.decals_db if not d["id"].endswith("_P"))
        premium_id = base_id + "_P"
        tab.filtered_decals = [(premium_id, {"id": base_id, "name": "Test"}, 5, True, 0)]
        tab.table.setRowCount(1)
        tab.table.selectRow(0)
        tab._on_table_selection_changed()
        self.assertEqual(tab.current_selected_decal["id"], premium_id)
        tab.inv_spin.setValue(7)
        entries = self.win.save_json["soul"]["skl"]["psskl"]
        self.assertTrue(any(e["sklid"] == premium_id and e["cnt"] == 7 for e in entries))
        self.assertFalse(any(e["sklid"] == base_id for e in entries))

    def test_rebind_exports_valid_save_without_mutating_source(self):
        data = self.fixture()
        dialog = AccountCompatibilityDialog(self.win)
        dialog._src_data = copy.deepcopy(data)
        original = copy.deepcopy(dialog._src_data)
        dialog._src_ver = self.win.version
        dialog.target_steam_entry.setText("76561198012345678")
        dialog.cb_dest_mode.setCurrentIndex(dialog.cb_dest_mode.findData("FILE"))
        target = os.path.join(self.temp_dir.name, "rebound.sav")
        with patch("ui_qt.dialogs.account_compatibility_dialog.QFileDialog.getSaveFileName", return_value=(target, "")):
            dialog._apply_rebind_checked()
        rebound, version = save_io.decompress_save(target)
        self.assertEqual(rebound["user"]["psnacid"], "76561198012345678")
        self.assertEqual(dialog._src_data, original)
        self.assertEqual(version, self.win.version)
        dialog.close()

    def test_invalid_rebind_source_clears_previous_file(self):
        dialog = AccountCompatibilityDialog(self.win)
        dialog._src_data = {"user": {"uid": 1}}
        dialog._load_source_file(os.path.join(self.temp_dir.name, "missing.sav"))
        self.assertIsNone(dialog._src_data)
        dialog.close()

    def test_slots_save_load_backup_restore_use_original_engine(self):
        data = self.fixture()
        original_name = data["user"]["nm"]
        target = os.path.join(self.temp_dir.name, "active.sav")
        save_io.save_to_file(data, target, version=self.win.version)
        self.win.save_path = target
        self.win.tab_advanced._save_to_slot_action(1)
        self.assertFalse(save_slots.get_slot_info(1)["is_empty"])
        self.win.save_json["user"]["nm"] = "changed"
        self.win._auto_save()
        self.win.tab_advanced._load_slot_action(1)
        # The original engine syncs the active slot on autosave.
        self.assertEqual(self.win.save_json["user"]["nm"], "changed")
        save_slots.restore_slot_backup(1, "slot_01.ORIGINAL.bak", active_target_path=target)
        self.win.load_save(target)
        self.assertEqual(self.win.save_json["user"]["nm"], original_name)

    def test_mastery_selected_category_matches_engine(self):
        data = self.fixture()
        tab = self.win.tab_mastery
        category = tab.expert_list[0]["ptarmtp"]
        expected = copy.deepcopy(data)
        modifiers.set_weapon_mastery(expected, category, level=12)
        with patch("ui_qt.tabs.mastery_tab.QInputDialog.getInt", return_value=(12, True)):
            tab._on_item_double_clicked(tab.table.item(0, 0))
        self.assertEqual(data["soul"]["expert"], expected["soul"]["expert"])

    def test_blueprint_research_matches_engine(self):
        data = self.fixture()
        tab = self.win.tab_blueprints
        blueprint = self.win.equipment_db[0]
        tab.current_selected_bp = blueprint
        index = next(i for i in range(tab.cb_single_lvl.count()) if "+4" in tab.cb_single_lvl.itemText(i))
        tab.cb_single_lvl.setCurrentIndex(index)
        expected = copy.deepcopy(data)
        with patch("time.time", return_value=1800000000):
            modifiers.send_blueprint_to_rnd(expected, blueprint["id"], target_level=4)
            tab._send_single_bp_to_rnd()
        self.assertEqual(data["soul"]["partresearch"], expected["soul"]["partresearch"])


class TestUpdateDispatch(unittest.TestCase):
    def test_update_result_is_queued_for_ui_thread(self):
        import updater
        queued = []
        root = SimpleNamespace(after=lambda ms, fn: queued.append(fn), _notify=lambda *a, **k: None)
        remote = {"version": "99.0.0"}
        with patch("updater.check_for_updates", return_value=(True, remote, None)), patch("updater.threading.Thread") as thread, patch("ui_qt.dialogs.update_dialog.QtUpdateNotificationDialog") as dialog:
            updater.check_updates_background(root)
            thread.call_args.kwargs["target"]()
            dialog.assert_not_called()
            self.assertEqual(len(queued), 1)
            queued[0]()
            dialog.assert_called_once_with(root, remote)
            dialog.return_value.exec.assert_called_once()

    def test_update_error_is_reported_without_installing(self):
        import updater
        from unittest.mock import Mock
        queued = []
        root = SimpleNamespace(after=lambda ms, fn: queued.append(fn), _notify=Mock())
        with patch("updater.check_for_updates", return_value=(False, None, "offline")), patch("updater.threading.Thread") as thread, patch("updater.perform_update_git") as install:
            updater.check_updates_background(root, silent=False)
            thread.call_args.kwargs["target"]()
            queued[0]()
            root._notify.assert_called_once_with("updates", "updater_check_err", kind="warning", error="offline")
            install.assert_not_called()
