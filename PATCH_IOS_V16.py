from pathlib import Path
import re

def patch_prsv_import():
    changed = []
    candidates = []
    pattern = re.compile(r"(\baccept\s*[:=]\s*)([\"'])([^\"']*\.prsv[^\"']*)(\2)", re.I)
    for p in Path('src').rglob('*'):
        if not p.is_file() or p.suffix not in {'.ts', '.tsx', '.js', '.jsx'}:
            continue
        s = p.read_text(encoding='utf-8')
        if '.prsv' not in s.lower() or 'accept' not in s.lower():
            continue
        candidates.append(str(p))
        def repl(m):
            old = m.group(3)
            if old.strip().lower() == '.prsv':
                return m.group(0)
            return f'{m.group(1)}{m.group(2)}.prsv{m.group(2)}'
        ns, n = pattern.subn(repl, s)
        if n and ns != s:
            p.write_text(ns, encoding='utf-8')
            changed.append((str(p), n))
    print('=== iOS PRSV import fix ===')
    print('candidate files:', candidates)
    print('changed:', changed)
    found = False
    verify_pattern = re.compile(r"\baccept\s*[:=]\s*[\"']\.prsv[\"']", re.I)
    for p in Path('src').rglob('*'):
        if p.is_file() and p.suffix in {'.ts', '.tsx', '.js', '.jsx'}:
            try:
                s = p.read_text(encoding='utf-8')
            except Exception:
                continue
            if verify_pattern.search(s):
                found = True
                break
    if not found:
        raise SystemExit("ERROR: Could not verify an accept='.prsv' import picker.")

def patch_ios_webgl_memory():
    p = Path('src/main.ts')
    if not p.exists():
        raise SystemExit('ERROR: src/main.ts not found')
    s = p.read_text(encoding='utf-8')
    original = s
    if 'antialiasGL: false' not in s:
        anchor = '  antialias: false,'
        if anchor not in s:
            raise SystemExit('ERROR: main.ts antialias anchor not found')
        replacement = '''  antialias: false,
  render: {
    antialiasGL: false,
    preserveDrawingBuffer: false,
    powerPreference: "low-power",
  },'''
        s = s.replace(anchor, replacement, 1)
    s = s.replace('game.sound.pauseOnBlur = false;', 'game.sound.pauseOnBlur = true;')
    if s != original:
        p.write_text(s, encoding='utf-8')
        print('=== iOS WebGL memory mitigation applied ===')
    else:
        print('=== iOS WebGL memory mitigation already present ===')
    verify = p.read_text(encoding='utf-8')
    for needle in ('antialiasGL: false', 'preserveDrawingBuffer: false', 'powerPreference: "low-power"'):
        if needle not in verify:
            raise SystemExit(f'ERROR: failed to verify {needle}')

def main():
    if not Path('src').is_dir():
        raise SystemExit('ERROR: Run this script from the cloned game directory.')
    patch_prsv_import()
    patch_ios_webgl_memory()
    print()
    print('DONE: ZA-DIGI Rouge iOS v16 fixes applied.')

if __name__ == '__main__':
    main()
