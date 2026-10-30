"""Read-only model inventory: no downloads, installation or GPU/model loading."""
import argparse
import hashlib
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('models_dir', type=Path)
    parser.add_argument('--autoprompt', action='store_true', help='also require the complete Qwen4B directory')
    parser.add_argument('--sha256', action='store_true', help='read full weights and compare hashes (large disk IO)')
    args = parser.parse_args()
    manifest = json.loads((Path(__file__).resolve().parents[1] / 'manifests/models.json').read_text('utf-8'))
    results = []
    for model in manifest['models']:
        if model.get('required_for') not in ('base', 'selflift') and not args.autoprompt:
            continue
        path = args.models_dir / model['id']
        result = {'file': model['id'], 'exists': path.is_file(), 'ok': False}
        if result['exists']:
            result['size_matches'] = path.stat().st_size == model['bytes']
            result['ok'] = result['size_matches']
            if args.sha256:
                digest = hashlib.sha256()
                with path.open('rb') as stream:
                    for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
                        digest.update(block)
                result['sha256_matches'] = digest.hexdigest() == model['sha256']
                result['ok'] = result['ok'] and result['sha256_matches']
        results.append(result)
    ok = all(item['ok'] for item in results) and bool(results)
    print(json.dumps({'ok': ok, 'hashes_checked': args.sha256, 'files': results}, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
