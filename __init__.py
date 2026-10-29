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
__version__ = "0.2.0-cloud-test"
print("[MiniMX H3 LoopStudio] 0.2.0-cloud-test; original node IDs untouched")

from . import diagnostics
