# -*- coding: utf-8 -*-
"""
Locale Integrity and Health Checker for LET IT DIE Save Editor.
Audits all locale JSON files for key parity, placeholder consistency,
and detects missing or untranslated keys.
"""

import os
import sys
import json
import re
import argparse

# Ensure standard UTF-8 console output
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCALES_DIR = os.path.join(BASE_DIR, "locales")
PLACEHOLDER_REGEX = re.compile(r"\{([a-zA-Z0-9_]+(?::[^}]*)?)\}")

def get_placeholder_names(s):
    if not isinstance(s, str):
        return set()
    matches = PLACEHOLDER_REGEX.findall(s)
    # Extract just the variable identifier before any formatting specifier (e.g. {count:,} -> count)
    return {m.split(":")[0] for m in matches}

def check_locales(locales_dir=LOCALES_DIR, ref_lang="en"):
    print("=" * 65)
    print("  LET IT DIE SAVE EDITOR - LOCALES HEALTH & INTEGRITY AUDITOR")
    print("=" * 65)

    if not os.path.isdir(locales_dir):
        print(f"[ERROR] Locales directory not found: {locales_dir}", file=sys.stderr)
        return 1

    files = {}
    for f in sorted(os.listdir(locales_dir)):
        if f.endswith(".json"):
            code = os.path.splitext(f)[0].lower()
            path = os.path.join(locales_dir, f)
            try:
                with open(path, "r", encoding="utf-8") as fp:
                    files[code] = json.load(fp)
            except Exception as e:
                print(f"[ERROR] Failed to parse {f}: {e}", file=sys.stderr)
                return 1

    if ref_lang not in files:
        print(f"[ERROR] Reference language '{ref_lang}.json' not found in {locales_dir}", file=sys.stderr)
        return 1

    ref_data = files[ref_lang]
    ref_keys = set(ref_data.keys())
    print(f"[*] Reference Language: '{ref_lang}' with {len(ref_keys)} keys.\n")

    has_errors = False

    for lang, data in files.items():
        if lang == ref_lang:
            continue

        print(f"[*] Checking '{lang}.json' ({len(data)} keys):")
        lang_keys = set(data.keys())

        missing_in_lang = ref_keys - lang_keys
        extra_in_lang = lang_keys - ref_keys

        if missing_in_lang:
            has_errors = True
            print(f"  [-] Missing {len(missing_in_lang)} keys compared to '{ref_lang}':")
            for k in sorted(missing_in_lang)[:10]:
                print(f"      - {k}")
            if len(missing_in_lang) > 10:
                print(f"      ... and {len(missing_in_lang) - 10} more")
        else:
            print("  [+] Key parity: 100% (No missing keys)")

        if extra_in_lang:
            print(f"  [!] Found {len(extra_in_lang)} extra keys not in '{ref_lang}':")
            for k in sorted(extra_in_lang)[:5]:
                print(f"      + {k}")

        # Check placeholder mismatches
        placeholder_mismatches = []
        for k in ref_keys.intersection(lang_keys):
            ph_ref = get_placeholder_names(ref_data[k])
            ph_lang = get_placeholder_names(data[k])
            if ph_ref != ph_lang:
                placeholder_mismatches.append((k, ph_ref, ph_lang))

        if placeholder_mismatches:
            has_errors = True
            print(f"  [-] {len(placeholder_mismatches)} placeholder parameter mismatch(es):")
            for k, ph_ref, ph_lang in placeholder_mismatches[:5]:
                print(f"      Key '{k}': expected {ph_ref} vs found {ph_lang}")
        else:
            print("  [+] Placeholder consistency: 100% (All variables match)")

        # Check empty values
        empty_keys = [k for k, v in data.items() if not str(v).strip()]
        if empty_keys:
            print(f"  [!] {len(empty_keys)} key(s) have empty strings:")
            for k in empty_keys[:5]:
                print(f"      - {k}")

        print()

    print("=" * 65)
    if has_errors:
        print(">>> AUDIT RESULT: FAIL - Inconsistencies detected. <<<")
        return 1
    else:
        print(">>> AUDIT RESULT: PASS - All locales are 100% healthy and in parity! <<<")
        return 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check locales integrity for LET IT DIE Save Editor")
    parser.add_argument("--ref", default="en", help="Reference language code (default: en)")
    args = parser.parse_args()
    sys.exit(check_locales(ref_lang=args.ref))
