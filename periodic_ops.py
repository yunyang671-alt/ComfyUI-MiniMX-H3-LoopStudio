"""Temporal ring operations. Spatial padding and model normalization stay unchanged."""
import torch
from torch import nn
from torch.nn import functional as F


def wrap_time(x, before, after, dim=2):
    n = x.shape[dim]
    if n < 1:
        raise ValueError("周期主体不能为空。")
    indexes = torch.arange(-before, n + after, device=x.device) % n
    return x.index_select(dim, indexes)


def close_av_streams(streams):
    """Rebuild context only; do not change a single frame of the period body."""
    video = streams[0]
    n = video.shape[2] - 2
    if n < 5 or n % 5:
        raise ValueError(f"H3周期潜变量需要5k+2时间步，实际为{video.shape[2]}。")
    result = [wrap_time(video[:, :, :n], 0, 2)]
    audio_n = round((n // 5) * 17 * 40 / 24)
    for audio in streams[1:]:
        if audio.shape[-1] < audio_n:
            raise ValueError("H3联合音频潜变量短于周期主体，不能丢弃音频时钟。")
        result.append(wrap_time(audio[..., :audio_n], 0, audio.shape[-1] - audio_n, -1))
    return result


def periodic_module(module, x):
    if isinstance(module, nn.Sequential):
        for item in module:
            x = periodic_module(item, x)
        return x
    if isinstance(module, nn.Conv3d):
        pt, ph, pw = module.padding
        if module.padding_mode != "zeros":
            raise ValueError("未知3D卷积padding模式，不能安全接入周期放大。")
        if pt:
            x = wrap_time(x, pt, pt)
        return F.conv3d(x, module.weight, module.bias, module.stride,
                        (0, ph, pw), module.dilation, module.groups)
    return module(x)


def periodic_block(block, x, emb):
    # The pinned upscaler's two residual blocks have explicit temporal convolutions.
    name = type(block).__name__
    if name == "ResBlockEmb3D":
        h = periodic_module(block.in_layers, x)
        emb_out = block.emb_layers(emb).type(h.dtype)
        while emb_out.ndim < h.ndim:
            emb_out = emb_out[..., None]
        scale, shift = torch.chunk(emb_out, 2, dim=1)
        h = block.out_norm(h) * (1 + scale) + shift
        return periodic_module(block.skip, x) + periodic_module(block.out_layers, h)
    if name == "TemporalConv":
        h = periodic_module(block.dwconv, F.silu(block.norm(x)))
        return x + periodic_module(block.pwconv, h)
    # Attention uses 1x1x1 convolutions and whole-period normalization as upstream.
    return periodic_module(block, x)


def periodic_upscaler_forward(model, x, scale, size):
    """One whole temporal period: circular time convolutions, unchanged spatial ops.

    Unlike outer context duplication, this closes every temporal convolution. Run
    all T frames together so GroupNorm sees the same ring at every phase. Temporal
    chunking is deliberately bypassed only for this cycle-specific lift.
    """
    if len(size) != 3 or int(size[0]) != x.shape[2]:
        raise ValueError("周期学习式放大只改变空间尺寸，不允许重采样时间轴。")
    if tuple(size) == tuple(x.shape[-3:]):
        return x
    emb = model.embed(torch.tensor([scale - 1 if scale is not None else 0.0],
                                  device=x.device, dtype=x.dtype).unsqueeze(0))
    x = periodic_module(model.conv_in, x)
    for block in model.in_blocks:
        x = periodic_block(block, x, emb.expand(x.shape[0], -1))
    x = F.interpolate(x, size=size, mode="trilinear", align_corners=False)
    for block in model.out_blocks:
        x = periodic_block(block, x, emb.expand(x.shape[0], -1))
    return periodic_module(model.conv_out, F.silu(model.norm_out(x)))
