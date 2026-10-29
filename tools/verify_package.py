"""Verify distributed files and relative imports, without ComfyUI or a GPU."""
import ast
import hashlib
import json
from pathlib import Path
import re


def main():
    root = Path(__file__).resolve().parents[1]
    expected = json.loads((root / 'SHA256SUMS.json').read_text(encoding='utf-8'))
    for name, digest in expected.items():
        assert hashlib.sha256((root / name).read_bytes()).hexdigest() == digest, name
    for path in root.rglob('*.py'):
        tree = ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.level:
                folder = path.parent
                for _ in range(node.level - 1):
                    folder = folder.parent
                if node.module:
                    base = folder.joinpath(*node.module.split('.'))
                    assert base.with_suffix('.py').is_file() or (base / '__init__.py').is_file(), (path, node.module)
                else:
                    for alias in node.names:
                        assert (folder / (alias.name + '.py')).is_file() or (folder / alias.name / '__init__.py').is_file(), (path, alias.name)
    for path in (root / 'js').glob('*.js'):
        for name in re.findall(r'from\s+[\'"]([^\'"]+)[\'"]', path.read_text(encoding='utf-8')):
            if name.startswith('./'):
                assert (path.parent / name).is_file(), (path, name)
    vendor = (root / '_loop_vendor.py').read_bytes().replace(b'\r\n', b'\n')
    assert hashlib.sha1(b'blob ' + str(len(vendor)).encode() + b'\0' + vendor).hexdigest() == '436156f86671cbc00bd7b2f68c8de36ac6d6e673'
    assert len(json.loads((root / 'nodes_manifest.json').read_text(encoding='utf-8'))) == 23
    print(f'PASS: {len(expected)} checksums, Python syntax, local imports, JS local imports, pinned Loop source, 23 node IDs.')


if __name__ == '__main__':
    main()
