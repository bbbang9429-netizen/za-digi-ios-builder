from pathlib import Path

GAME_DATA = Path('src/system/game-data.ts')

def main():
    if not GAME_DATA.exists():
        raise SystemExit('ERROR: src/system/game-data.ts not found')

    s = GAME_DATA.read_text(encoding='utf-8')
    original = s

    # 1) Statically import the Capacitor plugin so Vite bundles it and Capacitor can register it reliably.
    import_line = 'import { FilePicker } from "@capawesome/capacitor-file-picker";\n'
    if import_line not in s:
        first_import = s.find('import ')
        if first_import < 0:
            raise SystemExit('ERROR: no import section found in game-data.ts')
        s = s[:first_import] + import_line + s[first_import:]

    # 2) Replace the dynamic import chain from v17.3 with a direct native call.
    start_marker = '    // iOS/Capacitor: use the native document picker.'
    end_marker = '      });'
    start = s.find(start_marker)
    if start < 0:
        raise SystemExit('ERROR: v17.3 native picker block start not found')

    # Find the end of the .catch(...) block by anchoring to the known fallback text.
    fallback = '        releaseInputs();\n      });'
    end = s.find(fallback, start)
    if end < 0:
        raise SystemExit('ERROR: v17.3 native picker block end not found')
    end += len(fallback)

    direct_block = '''    // iOS/Capacitor native document picker.
    // Do NOT call releaseInputs() before opening it: doing so moves the game cursor
    // and can break the interaction that invoked Import Data.
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

    s = s[:start] + direct_block + s[end:]

    if s == original:
        raise SystemExit('ERROR: no changes made')

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

    if 'void import("@capawesome/capacitor-file-picker")' in verify:
        raise SystemExit('ERROR: old dynamic import still present')

    print('=== iOS v17.4 native PRSV picker ===')
    print('Static FilePicker import: YES')
    print('Direct native pickFiles call: YES')
    print('No pre-picker releaseInputs: YES')
    print('DONE: v17.4 patch applied')

if __name__ == '__main__':
    main()
