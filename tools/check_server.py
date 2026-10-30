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
        'generation_submitted': False,
        'missing_bundled_nodes': sorted(set(manifest) - set(registry)),
        'missing_native_nodes': sorted(set(inventory.NATIVE_REQUIRED) - set(registry)),
        'optional_nodes': {n: n in registry for n in inventory.OPTIONAL},
    }
    result['missing_video_output'] = [] if 'VHS_VideoCombine' in registry else ['VHS_VideoCombine']
    # Inspect exact selected names rather than model-folder counts. No model load.
    model_manifest = json.loads((root / 'manifests/models.json').read_text('utf-8'))
    cfg = registry.get('MiniMXH3LoopStudio', {}).get('input', {}).get('required', {})
    fields = {'diffusion_models': '模型', 'text_encoders': '文本编码器',
              'loras': 'LoRA1', 'latent_upscale_models': '二采放大模型'}
    checks = []
    for model in model_manifest['models']:
        if model.get('required_for') not in ('base', 'selflift'):
            continue
        field = fields.get(model['category'])
        if model['category'] == 'vae':
            field = '视频VAE' if 'video' in model['filename'] else '音频VAE'
        options = cfg.get(field, [[]])[0] if field in cfg else []
        checks.append({'file': model['id'], 'input': field,
                       'available': isinstance(options, list) and model['filename'] in options})
    result['selected_models'] = checks
    try:
        with urllib.request.urlopen(args.url.rstrip('/') + '/minimxa-loop/package-features', timeout=10) as response:
            result['features'] = json.load(response)
    except Exception as exc:
        result['features_note'] = f'Custom route unavailable ({type(exc).__name__}); inspect platform routing/logs.'
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return int(bool(result['missing_bundled_nodes'] or result['missing_native_nodes']
                    or result['missing_video_output'] or any(not x['available'] for x in checks)))


if __name__ == '__main__':
    raise SystemExit(main())
