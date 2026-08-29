from pathlib import Path

GAME_DATA = Path('src/system/game-data.ts')

def main():
    if not GAME_DATA.exists():
        raise SystemExit('ERROR: src/system/game-data.ts not found')

    s = GAME_DATA.read_text(encoding='utf-8')

    static_import = 'import { FilePicker } from "@capawesome/capacitor-file-picker";\n'
    if static_import not in s:
        first_import = s.find('import ')
        if first_import < 0:
            raise SystemExit('ERROR: import section not found')
        s = s[:first_import] + static_import + s[first_import:]

    # Find the v17.3 dynamic import directly instead of relying on its comment text.
    dyn = 'void import("@capawesome/capacitor-file-picker")'
    start = s.find(dyn)
    if start < 0:
        # allow single quotes too
        dyn = "void import('@capawesome/capacitor-file-picker')"
        start = s.find(dyn)
    if start < 0:
        raise SystemExit('ERROR: v17.3 dynamic import call not found')

    line_start = s.rfind('\n', 0, start) + 1

    # End at the known fallback chain terminator from v17.3.
    fallback_text = 'releaseInputs();\n      });'
    end = s.find(fallback_text, start)
    if end < 0:
        raise SystemExit('ERROR: v17.3 dynamic picker end not found')
    end += len(fallback_text)

    direct_block = '''    // iOS/Capacitor native document picker.
    // Keep the native call in the same user action path and avoid releaseInputs()
    // before presenting the picker, because that moves the menu cursor.
    void (async () => {
      try {
        const result = await FilePicker.pickFiles({
          limit: 1,
          readData: true,
        });

        const pickedFile = result.files?.[0];
        if (!pickedFile) {
          cleanupFileInput();
          return;
        }

        if (!pickedFile.name?.toLowerCase().endsWith(".prsv")) {
          cleanupFileInput();
          globalScene.ui.showText(
            i18next.t("menuUiHandler:importCorrupt", {
              dataName: i18next.t(`gameData:${toCamelCase(GameDataType[dataType])}`),
            }),
            null,
            () => globalScene.ui.showText("", 0),
            fixedInt(1500),
          );
          return;
        }

        if (!pickedFile.data) {
          throw new Error("Native file picker returned no file data");
        }

        const binary = atob(pickedFile.data);
        const bytes = new Uint8Array(binary.length);
        for (let i = 0; i < binary.length; i++) {
          bytes[i] = binary.charCodeAt(i);
        }

        const selectedFile = new File([bytes], pickedFile.name, {
          type: pickedFile.mimeType || "application/octet-stream",
        });

        processSelectedFile(selectedFile);
      } catch (error) {
        console.warn("[ZA-IOS-PRSV] Native picker dismissed or failed", error);
        cleanupFileInput();
      }
    })();'''

    s = s[:line_start] + direct_block + s[end:]

    GAME_DATA.write_text(s, encoding='utf-8')
    verify = GAME_DATA.read_text(encoding='utf-8')

    required = [
        'import { FilePicker } from "@capawesome/capacitor-file-picker";',
        'const result = await FilePicker.pickFiles({',
        'readData: true',
        'processSelectedFile(selectedFile);',
    ]
    for needle in required:
        if needle not in verify:
            raise SystemExit(f'ERROR: verification failed: {needle}')

    if 'void import("@capawesome/capacitor-file-picker")' in verify or "void import('@capawesome/capacitor-file-picker')" in verify:
        raise SystemExit('ERROR: old dynamic import still present')

    print('=== iOS v17.4.1 native PRSV picker ===')
    print('Static FilePicker import: YES')
    print('Dynamic import removed: YES')
    print('No pre-picker releaseInputs: YES')
    print('DONE: v17.4.1 patch applied')

if __name__ == '__main__':
    main()
