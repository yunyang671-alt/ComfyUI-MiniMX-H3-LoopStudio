"""Sampling compatibility for the pinned original MiniMax H3 Loop wrappers."""
import logging
import hashlib
import inspect
from pathlib import Path
import torch
import comfy.patcher_extension
import nodes

from .periodic_ops import close_av_streams, wrap_time
from .selflift_vendor import h3_upscaler
from .selflift_vendor.nodes import SelfLiftH3Sampler, progressive_sample


def require_loop_nodes():
    # Private pinned implementation: no separately installed Loop plugin required.
    from . import _loop_vendor
    data = Path(_loop_vendor.__file__).read_bytes().replace(b"\r\n", b"\n")
    fingerprint = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
    if fingerprint != "436156f86671cbc00bd7b2f68c8de36ac6d6e673":
        raise RuntimeError("本仓库 _loop_vendor.py 不完整或已改变，请重新安装本仓库固定版本。")
    return _loop_vendor


def trace_sampler(executor, guider, sigmas, extra_args, callback, noise, *args, **kwargs):
    options = extra_args["model_options"]
    transformer = options.get("transformer_options", {})
    if "minimax_h3_loop_pad_clips" not in transformer:
        raise RuntimeError("周期采样模型标记丢失，停止生成以避免输出普通视频。")
    wrappers = comfy.patcher_extension.get_all_wrappers(
        comfy.patcher_extension.WrappersMP.DIFFUSION_MODEL, options, is_model_options=True)
    if not wrappers:
        raise RuntimeError("周期模型前向包装丢失。")
    logging.info("[MiniMX Loop sampler] nfe=%d padding=%s views=%s zero_external_noise=%s shapes=%s",
                 len(sigmas) - 1, transformer.get("minimax_h3_loop_pad_clips"),
                 transformer.get("minimax_h3_loop_views"), bool(torch.count_nonzero(noise) == 0),
                 getattr(guider.inner_model, "latent_shapes", None))
    return executor(guider, sigmas, extra_args, callback, noise, *args, **kwargs)


class MiniMXH3LoopModel:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"model": ("MODEL",), "pad_clips": ("INT", {"default": 1, "min": 1, "max": 3}),
                             "views": ("INT", {"default": 1, "min": 1, "max": 2})}}
    RETURN_TYPES = ("MODEL",)
    FUNCTION = "patch"
    CATEGORY = "MiniMX/H3周期循环/内部"

    def patch(self, model, pad_clips, views):
        loop = require_loop_nodes()
        wrapped = loop.MiniMaxH3Loop().patch(model, pad_clips, views)[0]
        wrapped.add_wrapper_with_key(comfy.patcher_extension.WrappersMP.SAMPLER_SAMPLE,
                                     "minimxa_loop_trace", trace_sampler)
        return (wrapped,)


class MiniMXH3SelfLiftLoopSampler(SelfLiftH3Sampler):
    CATEGORY = "MiniMX/H3周期循环/内部"

    def sample(self, model, positive, negative, vae, latent_image, sampler, sigmas, seed, cfg,
               transition_step, lowres_scale, rho, w_min, w_max, upscaler_model,
               model_hires=None, highres_tiling=False, upscaler_unload=True):
        require_loop_nodes()
        if rho != 0.0:
            raise ValueError("本版周期SelfLift保持原配方rho=0；尚未实现像素VAE锚定支路的周期适配。")
        if highres_tiling:
            raise ValueError("本版周期SelfLift尚未验证高清分块包装顺序，请保持原交付设置：二采高清分块关闭。关闭循环后原分块功能保留。")
        if upscaler_model == "none":
            raise ValueError("周期SelfLift需要原配方的h3_upscaler_lms放大模型。")
        for target in (model, model_hires or model):
            if "minimax_h3_loop_pad_clips" not in target.model_options.get("transformer_options", {}):
                raise RuntimeError("SelfLift两个阶段必须使用Loop包装后的模型。")

        def lifter(z, hw):
            n = z.shape[2] - 2
            if n < 5 or n % 5:
                raise ValueError("周期放大接收到无效的H3周期时间长度。")
            # Only the clean period goes through the learned model; the two
            # context latents are rebuilt from its lifted beginning afterwards.
            body = h3_upscaler.learned_latent_lift(
                z[:, :, :n], hw, upscaler_model, force_unload=upscaler_unload, periodic=True)
            logging.info("[MiniMX Loop lift] circular_time=True period=%d tail=2 model=%s target=%s",
                         n, upscaler_model, hw)
            return wrap_time(body, 0, 2)

        return (progressive_sample(model, positive, negative, vae, latent_image, sampler, sigmas,
                                   seed, cfg, transition_step, lowres_scale, rho, w_min, w_max,
                                   "nearest", latent_lifter=lifter, highres_tiling=False,
                                   model_hires=model_hires, periodic=True),)
