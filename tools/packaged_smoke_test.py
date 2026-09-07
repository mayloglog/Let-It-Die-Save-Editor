"""Check a frozen build without detecting or changing a player's save."""
import json
import os
from pathlib import Path
import tempfile


def run(output_dir):
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    output = Path(output_dir).resolve()
    output.mkdir(parents=True, exist_ok=True)
    try:
        from PySide6.QtWidgets import QApplication
        from PySide6.QtGui import QFontDatabase, QFont
        import i18n
        import save_io
        import modifiers
        import updater
        import core.save_slots as slots
        from ui_qt.main_window import SaveEditorMainWindow
        from ui_qt.theme import load_stylesheet

        with tempfile.TemporaryDirectory() as temp:
            i18n.CONFIG_FILE = os.path.join(temp, "config.json")
            slots.PROJECT_SLOTS_DIR = os.path.join(temp, "slots")
            slots.ACTIVE_SLOT_FILE = os.path.join(temp, "slots", "active_slot.json")
            save_io.PROJECT_BACKUPS_DIR = os.path.join(temp, "backups")
            updater.check_updates_background = lambda *a, **kw: None
            app = QApplication.instance() or QApplication([])
            font_path = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts" / "segoeui.ttf"
            if font_path.exists():
                QFontDatabase.addApplicationFont(str(font_path))
                app.setFont(QFont("Segoe UI", 9))
            window = SaveEditorMainWindow(save_path=os.path.join(temp, "missing.sav"))
            assert window.notebook.count() == 8
            assert window.materials_db and window.equipment_db and window.decals_db
            assert window.icon_map and load_stylesheet()
            data = {"user": {"uid": 1, "nm": "Build test"}, "soul": {"uid": 1, "cl": []}}
            modifiers.set_currencies(data, dm=123, kc=456, spl=789)
            path = os.path.join(temp, "roundtrip.sav")
            save_io.save_to_file(data, path, version=2)
            decoded, version = save_io.decompress_save(path)
            assert decoded == data and version == 2
            window.resize(1400, 900)
            window.show()
            app.processEvents()
            window.grab().save(str(output / "window.png"))
            report = {"ok": True, "version": updater.get_local_version_info()["version"],
                      "tabs": window.notebook.count(), "materials": len(window.materials_db),
                      "equipment": len(window.equipment_db), "decals": len(window.decals_db),
                      "save_roundtrip": True}
            window.close()
        (output / "result.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        return 0
    except Exception:
        import traceback
        (output / "error.txt").write_text(traceback.format_exc(), encoding="utf-8")
        return 1
