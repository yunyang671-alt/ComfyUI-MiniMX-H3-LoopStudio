"""Independent full H3 studio with optional cycle sampling; no shared-node overwrite."""
from . import h3_dependencies
from .studio import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS
from .selflift_vendor.nodes import SelfLiftH3Sampler
from ._loop_vendor import MiniMaxH3LoopDecode
from .loop_runtime import MiniMXH3LoopModel, MiniMXH3SelfLiftLoopSampler

NODE_CLASS_MAPPINGS = dict(NODE_CLASS_MAPPINGS)
NODE_DISPLAY_NAME_MAPPINGS = dict(NODE_DISPLAY_NAME_MAPPINGS)
NODE_CLASS_MAPPINGS.update({
    "MiniMXBase_SelfLiftH3Sampler": SelfLiftH3Sampler,
    "MiniMXH3LoopModel": MiniMXH3LoopModel,
    "MiniMXH3LoopDecode": MiniMaxH3LoopDecode,
    "MiniMXH3SelfLiftLoopSampler": MiniMXH3SelfLiftLoopSampler,
})
NODE_DISPLAY_NAME_MAPPINGS["MiniMXH3LoopStudio"] = "MiniMX H3 完整创作台 · 周期循环兼容版"
WEB_DIRECTORY = "./js"
from .platform_config import VERSION, initialize_batch_service
__version__ = VERSION
print(f"[MiniMX H3 LoopStudio] {VERSION}; original node IDs untouched")

from . import diagnostics
FEATURES = initialize_batch_service()

# Read-only capability probe: no model loads, DB writes or queue submission.
from aiohttp import web
from server import PromptServer

@PromptServer.instance.routes.get("/minimxa-loop/package-features")
async def package_features(request):
    return web.json_response(FEATURES)
