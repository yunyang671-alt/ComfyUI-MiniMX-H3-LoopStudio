"""Read-only inventory; no model loading, installation, or external requests."""
import importlib.util
import json
from pathlib import Path

NATIVE_REQUIRED = (
    'UNETLoader', 'CLIPLoader', 'VAELoader', 'LoraLoaderModelOnly',
    'LoadImage', 'ImageScale', 'ImageBatch', 'MiniMaxH3ImageToVideo',
    'MiniMaxH3ReferenceToVideo', 'MiniMaxH3SigmaShift', 'BasicScheduler',
    'KSamplerSelect', 'RandomNoise', 'DisableNoise', 'BasicGuider',
    'ConditioningZeroOut', 'SplitSigmas', 'SamplerCustomAdvanced',
    'LTXVConcatAVLatent', 'LTXVSeparateAVLatent', 'VAEDecode',
    'VAEDecodeAudio', 'VAEEncode', 'VAEEncodeAudio', 'EmptyAudio',
    'LoadAudio', 'AudioConcat', 'LoadVideo', 'GetVideoComponents',
    'ModelAttentionBackend', 'BlockSparseAttention',
)
OPTIONAL = {
    'VHS_VideoCombine': '视频导出节点；现有环境已经具备时无需重复安装。',
    'PathchSageAttentionKJ': '可选 SageAttention 加速。',
    'MiniMaxH3MemoryEfficientSageAttentionPatch': '可选 H3 SageAttention 加速。',
    'ModelPreviewOverrideKJ': '可选采样预览；未安装时不添加预览节点。',
}


def report():
    import nodes
    import folder_paths
    registry = nodes.NODE_CLASS_MAPPINGS
    expected = json.loads(Path(__file__).with_name('nodes_manifest.json').read_text(encoding='utf-8'))
    missing_native = [n for n in NATIVE_REQUIRED if n not in registry]
    missing_local = [n for n in expected if n not in registry]
    models = {}
    for category in ('diffusion_models', 'text_encoders', 'vae', 'loras', 'latent_upscale_models', 'LLM', 'vae_approx'):
        try:
            models[category] = {'count': len(folder_paths.get_filename_list(category))}
        except Exception:
            models[category] = {'count': 0}
    return {
        'version': '0.3.0',
        'ready_for_loop_graph': not missing_native and not missing_local,
        'missing_bundled_nodes': missing_local,
        'missing_native_nodes': missing_native,
        'optional_nodes': {n: {'available': n in registry, 'purpose': purpose} for n, purpose in OPTIONAL.items()},
        'optional_python_packages': {n: importlib.util.find_spec(n) is not None for n in ('sageattention', 'llama_cpp')},
        'model_categories': models,
        'note': 'Counts do not verify chosen model files or CUDA kernels. No inference has been run.',
    }


try:
    from server import PromptServer
    from aiohttp import web

    @PromptServer.instance.routes.get('/minimxa-loop/package-diagnostics')
    async def package_diagnostics(request):
        return web.json_response(report())
except (ImportError, AttributeError):
    pass
