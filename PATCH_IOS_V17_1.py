from pathlib import Path
import re

GAME_DATA = Path('src/system/game-data.ts')
MAIN_TS = Path('src/main.ts')

def patch_prsv_ios_picker():
    if not GAME_DATA.exists():
        raise SystemExit('ERROR: src/system/game-data.ts not found')

    s = GAME_DATA.read_text(encoding='utf-8')
    original = s

    s, n_accept = re.subn(
        r"saveFile\.accept\s*=\s*[^;]+;",
        'saveFile.accept = ".prsv";',
        s,
        count=1,
    )
    if n_accept == 0:
        raise SystemExit('ERROR: saveFile.accept assignment not found')

    s, n_style = re.subn(
        r"saveFile\.style\.display\s*=\s*[\"\']none[\"\'];",
        'saveFile.style.position = "fixed";\n    saveFile.style.left = "-10000px";\n    saveFile.style.top = "0";\n    saveFile.style.width = "1px";\n    saveFile.style.height = "1px";\n    saveFile.style.opacity = "0";\n    saveFile.style.pointerEvents = "none";',
        s,
        count=1,
    )

    if 'document.body.appendChild(saveFile);' not in s:
        idx = s.find('saveFile.click();')
        if idx < 0:
            raise SystemExit('ERROR: saveFile.click() not found')
        line_start = s.rfind('\n', 0, idx) + 1
        indent_match = re.match(r'[ \t]*', s[line_start:idx])
        indent = indent_match.group(0) if indent_match else ''
        s = s[:line_start] + indent + 'document.body.appendChild(saveFile);\n' + s[line_start:]

    if s != original:
        GAME_DATA.write_text(s, encoding='utf-8')

    verify = GAME_DATA.read_text(encoding='utf-8')
    checks = [
        (r"saveFile\.accept\s*=\s*[\"\']\.prsv[\"\'];", 'accept .prsv'),
        (r"document\.body\.appendChild\(saveFile\);", 'DOM append'),
        (r"saveFile\.click\(\);", 'click'),
        (r"new FileReader\(\)", 'FileReader'),
        (r"reader\.readAsText\(selectedFile\);", 'readAsText'),
    ]
    for pat, label in checks:
        if not re.search(pat, verify):
            raise SystemExit(f'ERROR: verification failed: {label}')

    print('=== iOS PRSV picker fix ===')
    print('accept replacement count:', n_accept)
    print('display:none replacement count:', n_style)
    print('DOM attachment verified: YES')
    print('accept .prsv verified: YES')
    print('FileReader/readAsText verified: YES')

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
    patch_prsv_ios_picker()
    patch_ios_webgl_memory()
    print('DONE: ZA-DIGI Rouge iOS v17.1 patch applied.')

if __name__ == '__main__':
    main()
