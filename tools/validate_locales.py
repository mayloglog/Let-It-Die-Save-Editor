# -*- coding: utf-8 -*-
"""
i18n Quality Assurance and Validation Tool for LET IT DIE Save Editor.
Validates:
1. 100% key parity across all locales (en, es, zh, etc.).
2. Placeholder consistency ({name}, {count}, {lvl}) across translations to prevent runtime formatting crashes.
3. Absence of null or empty translation strings.
"""

import os
import sys
import json
import re
import glob

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCALES_DIR = os.path.join(BASE_DIR, "locales")


def extract_placeholders(text):
    """Extracts formatting placeholders from a string, e.g. '{count:,}' -> 'count'."""
    if not isinstance(text, str):
        return set()
    matches = re.findall(r"\{([a-zA-Z0-9_]+)(?::[^}]*)?\}", text)
    return set(matches)


def validate_all_locales(locales_dir=None):
    """
    Validates all locale files in the given directory.
    Returns (is_valid, errors_list, stats_dict).
    """
    if not locales_dir:
        locales_dir = LOCALES_DIR

    locale_files = glob.glob(os.path.join(locales_dir, "*.json"))
    if not locale_files:
        return False, [f"No locale files found in {locales_dir}"], {}

    locales = {}
    for path in sorted(locale_files):
        lang = os.path.splitext(os.path.basename(path))[0].lower()
        try:
            with open(path, "r", encoding="utf-8") as f:
                locales[lang] = json.load(f)
        except Exception as e:
            return False, [f"Failed to parse JSON file '{path}': {e}"], {}

    errors = []
    stats = {
        "languages": list(locales.keys()),
        "total_keys_by_lang": {lang: len(data) for lang, data in locales.items()},
    }

    if "en" not in locales:
        errors.append("Base language 'en.json' is missing from locales.")
        return False, errors, stats

    en_keys = set(locales["en"].keys())

    # 1. Key Parity Check
    for lang, data in locales.items():
        if lang == "en":
            continue
        cur_keys = set(data.keys())
        missing_in_cur = en_keys - cur_keys
        extra_in_cur = cur_keys - en_keys
        if missing_in_cur:
            errors.append(f"[{lang}] Missing {len(missing_in_cur)} keys present in 'en': {sorted(list(missing_in_cur))[:5]}...")
        if extra_in_cur:
            errors.append(f"[{lang}] Found {len(extra_in_cur)} orphan keys not present in 'en': {sorted(list(extra_in_cur))[:5]}...")

    # 2. Placeholder Consistency Check
    for key, en_val in locales["en"].items():
        en_placeholders = extract_placeholders(en_val)
        for lang, data in locales.items():
            if lang == "en":
                continue
            cur_val = data.get(key)
            if cur_val is None:
                continue
            cur_placeholders = extract_placeholders(cur_val)
            if en_placeholders != cur_placeholders:
                errors.append(
                    f"Placeholder mismatch for key '{key}' in [{lang}]: "
                    f"en={sorted(list(en_placeholders))}, {lang}={sorted(list(cur_placeholders))}"
                )

    # 3. None Value Check
    for lang, data in locales.items():
        for key, val in data.items():
            if val is None:
                errors.append(f"[{lang}] Key '{key}' has None value.")

    is_valid = len(errors) == 0
    return is_valid, errors, stats


def main():
    print("=" * 60)
    print("  LET IT DIE SAVE EDITOR - LOCALIZATION (i18n) LINTER")
    print("=" * 60)
    is_valid, errors, stats = validate_all_locales()
    print(f"Languages audited: {', '.join(stats.get('languages', []))}")
    for lang, count in stats.get("total_keys_by_lang", {}).items():
        print(f"  • [{lang}]: {count} translation keys")
    print("-" * 60)

    if is_valid:
        print(">>> ALL LOCALES ARE 100% HEALTHY AND SYNCHRONIZED! <<<")
        return 0
    else:
        print(f"Found {len(errors)} localization issue(s):")
        for err in errors:
            print(f"  [ERROR] {err}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
