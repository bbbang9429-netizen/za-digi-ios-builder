from pathlib import Path
import re

MENU = Path("src/ui/handlers/menu-ui-handler.ts")
GAME = Path("src/system/game-data.ts")

CURSOR_MARKER = "// ZA iOS v17.5: keep Manage Data cursor state while opening the native picker"


def patch_menu_cursor():
    s = MENU.read_text(encoding="utf-8")

    if CURSOR_MARKER in s:
        print("Manage Data cursor fix: already present")
        return

    old_marker = "// ZA iOS DEV: keep the Manage Data cursor/menu state"
    if old_marker in s:
        s = s.replace(old_marker, CURSOR_MARKER, 1)
        MENU.write_text(s, encoding="utf-8")
        print("Manage Data cursor fix: finalized from DEV marker")
        return

    pat = re.compile(
        r'(?P<indent>[ \t]*)ui\.revertMode\(\);\s*'
        r'(?P<call>globalScene\.gameData\.importData\(GameDataType\.SYSTEM\);)'
    )
    m = pat.search(s)

    if m:
        indent = m.group("indent")
        replacement = indent + CURSOR_MARKER + "\n" + indent + m.group("call")
        s = s[:m.start()] + replacement + s[m.end():]
        MENU.write_text(s, encoding="utf-8")
        print("Manage Data cursor fix: APPLIED")
        return

    if "globalScene.gameData.importData(GameDataType.SYSTEM);" in s:
        print("Manage Data cursor fix: already effective")
        return

    raise SystemExit("ERROR: SYSTEM import handler not found")


def remove_dev_diagnostics():
    s = GAME.read_text(encoding="utf-8")
    changed = False

    # Robust cleanup: remove everything from the DEV diagnostic marker up to,
    # but not including, the real native picker async wrapper.
    marker = "// ZA iOS DEV diagnostic"
    marker_pos = s.find(marker)

    if marker_pos >= 0:
        line_start = s.rfind("\n", 0, marker_pos) + 1
        async_pos = s.find("void (async () => {", marker_pos)

        if async_pos < 0:
            raise SystemExit("ERROR: native picker async wrapper not found after DEV diagnostic")

        # Preserve indentation before the async wrapper itself.
        s = s[:line_start] + s[async_pos:]
        changed = True
        print("DEV FilePicker status popup: REMOVED")
    else:
        print("DEV FilePicker status popup: not present")

    # Remove any remaining DEV-only alert lines.
    lines = s.splitlines(keepends=True)
    cleaned = []
    removed_error = False

    for line in lines:
        if "[ZA-DIGI DEV] FilePicker error:" in line:
            removed_error = True
            changed = True
            continue
        cleaned.append(line)

    s = "".join(cleaned)

    if removed_error:
        print("DEV FilePicker error popup: REMOVED")
    else:
        print("DEV FilePicker error popup: not present")

    # Remove Capacitor diagnostic import if nothing else uses Capacitor.
    cap_import = 'import { Capacitor } from "@capacitor/core";'
    body_without_import = s.replace(cap_import, "", 1)

    if cap_import in s and "Capacitor." not in body_without_import:
        s = s.replace(cap_import + "\r\n", "", 1)
        s = s.replace(cap_import + "\n", "", 1)
        changed = True
        print("DEV Capacitor diagnostic import: REMOVED")
    else:
        if cap_import in s:
            print("DEV Capacitor diagnostic import: kept (still used elsewhere)")
        else:
            print("DEV Capacitor diagnostic import: not present")

    if changed:
        GAME.write_text(s, encoding="utf-8")


def verify():
    menu = MENU.read_text(encoding="utf-8")
    game = GAME.read_text(encoding="utf-8")

    required = [
        'import { FilePicker } from "@capawesome/capacitor-file-picker";',
        "const result = await FilePicker.pickFiles({",
        "readData: true",
        "processSelectedFile(selectedFile);",
    ]

    for needle in required:
        if needle not in game:
            raise SystemExit(f"ERROR: verification failed: {needle}")

    if "globalScene.gameData.importData(GameDataType.SYSTEM);" not in menu:
        raise SystemExit("ERROR: SYSTEM import handler verification failed")

    leftovers = [
        "[ZA-DIGI DEV]",
        "ZA iOS DEV diagnostic",
        "const zaNative =",
        "const zaPicker =",
    ]
    for needle in leftovers:
        if needle in game:
            raise SystemExit(f"ERROR: DEV diagnostic code still present: {needle}")

    if re.search(
        r'ui\.revertMode\(\);\s*globalScene\.gameData\.importData\(GameDataType\.SYSTEM\);',
        menu,
    ):
        raise SystemExit("ERROR: cursor-reset revertMode still precedes SYSTEM import")

    print("=== ZA-DIGI iOS v17.5 final PRSV import ===")
    print("Native FilePicker source: YES")
    print("Manage Data cursor fix: YES")
    print("DEV diagnostic popups: NO")
    print("DONE: iOS v17.5 final patch applied")


def main():
    patch_menu_cursor()
    remove_dev_diagnostics()
    verify()


if __name__ == "__main__":
    main()
