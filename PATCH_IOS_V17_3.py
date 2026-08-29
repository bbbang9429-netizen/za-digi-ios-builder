from pathlib import Path

GAME_DATA = Path('src/system/game-data.ts')
MAIN_TS = Path('src/main.ts')

def replace_once(s, old, new, label):
    if old not in s:
        raise SystemExit(f'ERROR: anchor not found: {label}')
    return s.replace(old, new, 1)

def patch_prsv_native_picker():
    if not GAME_DATA.exists():
        raise SystemExit('ERROR: src/system/game-data.ts not found')
    s = GAME_DATA.read_text(encoding='utf-8')

    s = replace_once(
        s,
        '''    saveFile.addEventListener("change", e => {\n      // Android's native file picker can steal focus before the virtual A button\n      // receives its touchend/pointerup event. Clear all held/repeating inputs\n      // before parsing the selected save so no phantom key repeats occur.\n      releaseInputs();\n      const reader = new FileReader();''',
        '''    const processSelectedFile = (selectedFile: File) => {\n      releaseInputs();\n      const reader = new FileReader();''',
        'change handler start',
    )

    s = replace_once(
        s,
        '''      reader.onload = (_ => {\n        return e => {''',
        '''      reader.onload = e => {''',
        'reader.onload wrapper start',
    )

    s = replace_once(
        s,
        '''        };\n      })((e.target as any).files[0]);\n\n      const selectedFile = (e.target as HTMLInputElement).files?.[0];\n      if (!selectedFile) {\n        cleanupFileInput();\n        return;\n      }\n''',
        '''      };\n''',
        'reader.onload wrapper end',
    )

    s = replace_once(
        s,
        '''      reader.onloadend = () => cleanupFileInput();\n      reader.readAsText(selectedFile);\n    });\n\n    saveFile.addEventListener("cancel", cleanupFileInput);''',
        '''      reader.onloadend = () => cleanupFileInput();\n      reader.readAsText(selectedFile);\n    };\n\n    saveFile.addEventListener("change", e => {\n      const selectedFile = (e.target as HTMLInputElement).files?.[0];\n      if (!selectedFile) {\n        cleanupFileInput();\n        return;\n      }\n      processSelectedFile(selectedFile);\n    });\n\n    saveFile.addEventListener("cancel", cleanupFileInput);''',
        'process function end',
    )

    old_open = '''    // Defer opening the Android document picker until the touch that selected\n    saveFile.click();\n    // "Import Data" has been fully released. This prevents a stuck virtual key.\n    releaseInputs();\n    window.setTimeout(() => saveFile.click(), 150);'''

    native_open = '''    // iOS/Capacitor: use native document picker instead of WKWebView input.click().\n    void import("@capawesome/capacitor-file-picker")\n      .then(async ({ FilePicker }) => {\n        try {\n          const result = await FilePicker.pickFiles({\n            limit: 1,\n            readData: true,\n          });\n\n          const pickedFile = result.files?.[0];\n          if (!pickedFile) {\n            cleanupFileInput();\n            return;\n          }\n\n          if (!pickedFile.name?.toLowerCase().endsWith(".prsv")) {\n            cleanupFileInput();\n            globalScene.ui.showText(\n              i18next.t("menuUiHandler:importCorrupt", {\n                dataName: i18next.t(`gameData:${toCamelCase(GameDataType[dataType])}`),\n              }),\n              null,\n              () => globalScene.ui.showText("", 0),\n              fixedInt(1500),\n            );\n            return;\n          }\n\n          if (!pickedFile.data) {\n            throw new Error("Native file picker returned no file data");\n          }\n\n          const binary = atob(pickedFile.data);\n          const bytes = new Uint8Array(binary.length);\n          for (let i = 0; i < binary.length; i++) {\n            bytes[i] = binary.charCodeAt(i);\n          }\n\n          const selectedFile = new File([bytes], pickedFile.name, {\n            type: pickedFile.mimeType || "application/octet-stream",\n          });\n\n          processSelectedFile(selectedFile);\n        } catch (error) {\n          console.warn("[ZA-IOS-PRSV] Native picker dismissed or failed", error);\n          cleanupFileInput();\n        }\n      })\n      .catch(error => {\n        console.warn("[ZA-IOS-PRSV] Native picker unavailable; falling back to web input", error);\n        saveFile.click();\n        releaseInputs();\n      });'''

    s = replace_once(s, old_open, native_open, 'v17.2 picker block')
    GAME_DATA.write_text(s, encoding='utf-8')

    verify = GAME_DATA.read_text(encoding='utf-8')
    for needle in (
        'const processSelectedFile = (selectedFile: File) => {',
        'import("@capawesome/capacitor-file-picker")',
        'FilePicker.pickFiles({',
        'readData: true',
        'endsWith(".prsv")',
        'processSelectedFile(selectedFile);',
        'reader.readAsText(selectedFile);',
    ):
        if needle not in verify:
            raise SystemExit(f'ERROR: PRSV verification failed: {needle}')

    print('=== iOS native PRSV picker ===')
    print('Native FilePicker import: YES')
    print('Base64 -> File conversion: YES')
    print('Existing AES/import parser reused: YES')

def patch_ios_webgl_memory():
    if not MAIN_TS.exists():
        raise SystemExit('ERROR: src/main.ts not found')
    s = MAIN_TS.read_text(encoding='utf-8')
    original = s
    if 'antialiasGL: false' not in s:
        anchor = '  antialias: false,'
        if anchor not in s:
            raise SystemExit('ERROR: src/main.ts antialias anchor not found')
        replacement = '  antialias: false,\n  render: {\n    antialiasGL: false,\n    preserveDrawingBuffer: false,\n    powerPreference: "low-power",\n  },'
        s = s.replace(anchor, replacement, 1)
    s = s.replace('game.sound.pauseOnBlur = false;', 'game.sound.pauseOnBlur = true;')
    if s != original:
        MAIN_TS.write_text(s, encoding='utf-8')
    verify = MAIN_TS.read_text(encoding='utf-8')
    for needle in ('antialiasGL: false', 'preserveDrawingBuffer: false', 'powerPreference: "low-power"'):
        if needle not in verify:
            raise SystemExit(f'ERROR: WebGL verification failed: {needle}')
    print('=== iOS WebGL memory mitigation ===')
    print('antialiasGL=false: YES')
    print('preserveDrawingBuffer=false: YES')
    print('powerPreference=low-power: YES')

def main():
    if not Path('src').is_dir():
        raise SystemExit('ERROR: run from cloned game directory')
    patch_prsv_native_picker()
    patch_ios_webgl_memory()
    print('DONE: ZA-DIGI Rouge iOS v17.3 patch applied.')

if __name__ == '__main__':
    main()
