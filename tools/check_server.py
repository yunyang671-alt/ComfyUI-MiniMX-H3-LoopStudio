"""Check a running ComfyUI node registry without queueing work or reading assets."""
import argparse
import json
from pathlib import Path
import urllib.request


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('url', help='ComfyUI service URL, for example http://127.0.0.1:8188')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    manifest = json.loads((root / 'nodes_manifest.json').read_text(encoding='utf-8'))
    request = urllib.request.Request(args.url.rstrip('/') + '/object_info')
    with urllib.request.urlopen(request, timeout=30) as response:
        registry = json.load(response)
    # Load only the pure constants; diagnostics itself never imports models.
    import importlib.util
    spec = importlib.util.spec_from_file_location('loop_inventory', root / 'diagnostics.py')
    inventory = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(inventory)
    result = {
        'missing_bundled_nodes': sorted(set(manifest) - set(registry)),
        'missing_native_nodes': sorted(set(inventory.NATIVE_REQUIRED) - set(registry)),
        'optional_nodes': {n: n in registry for n in inventory.OPTIONAL},
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return int(bool(result['missing_bundled_nodes'] or result['missing_native_nodes']))


if __name__ == '__main__':
    raise SystemExit(main())
