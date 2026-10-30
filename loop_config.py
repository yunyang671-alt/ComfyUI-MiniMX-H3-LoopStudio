"""Append-only UI fields and resource checks for the independent loop studio."""
from collections import OrderedDict
import os

REFERENCE_ROUTE = "单图参考（推荐）"
ANCHOR_ROUTE = "保留首帧锚定（实验）"
STUDIO_ID = "MiniMXH3LoopStudio"
BASE_PREFIX = "MiniMXBase_"


def loop_fields():
    return OrderedDict([
        ("启用周期循环", ("BOOLEAN", {"default": False, "tooltip": "开启后接入采样、SelfLift时间放大和VAE解码的周期路径。关闭时走原版路径。"})),
        ("循环条件路线", ([REFERENCE_ROUTE, ANCHOR_ROUTE], {"default": REFERENCE_ROUTE, "tooltip": "参考路线仍只输入一张图，参考人物与画风，不固定为输出第1帧。首帧路线尚待单独验证。"})),
        ("循环正片帧数", ("INT", {"default": 204, "min": 17, "max": 306, "step": 17, "tooltip": "17的整数倍；204帧在24fps下为8.5秒。开启循环时由此决定时长，内部另加5帧上下文。"})),
        ("循环上下文段数", ("INT", {"default": 1, "min": 1, "max": 3, "tooltip": "pad_clips：每侧借用的17帧上下文段数。建议1；增加会变慢。"})),
        ("循环视角", ("INT", {"default": 1, "min": 1, "max": 2, "tooltip": "views：壁纸建议1。2额外计算旋转视角，主要改善音频接头，会增加耗时。"})),
    ])


def frame_plan(frames, pad_clips=1):
    frames = int(frames)
    pad_clips = int(pad_clips)
    if frames < 17 or frames > 306 or frames % 17:
        raise ValueError("循环正片帧数必须是17的整数倍，范围17至306；建议204（8.5秒）。")
    if not 1 <= pad_clips <= 3 or frames + 5 + 34 * pad_clips > 362:
        raise ValueError("周期上下文过长，超过H3单次362帧范围；请减少正片帧数或上下文段数。")
    return {"frames": frames, "length": frames + 5, "seconds": frames / 24,
            "video_period": frames // 17 * 5, "pad_clips": pad_clips}


def validate_request(values):
    """Fail before graph expansion; never silently fall back to text generation."""
    if not values.get("图生视频") or any(values.get(k) for k in
            ("文生视频", "首尾帧", "视频编辑", "数字人", "双人数字人", "MV数字人")):
        raise ValueError("本版周期分支用于单张图：请选择图生视频的单图模式。其他功能完整保留，请先关闭周期循环后使用。")
    if values.get("图生连续拼接") or values.get("多参考连续拼接"):
        raise ValueError("周期循环请关闭连续拼接；此版本一次只生成一张图的一整圈。")
    def chosen(v):
        return str(v or "").strip() not in {"", "未选择", "None", "null"}
    if not chosen(values.get("图片1")):
        raise ValueError("请先在创作台上传你自己的壁纸，放入图片1；周期分支不会退回文生视频。")
    if any(chosen(values.get(f"图片{i}")) for i in range(2, 21)):
        raise ValueError("周期单图模式只允许图片1，请移除图片2及之后的素材。")
    if not values.get("自定义模型配置"):
        raise ValueError("周期分支请保留自定义模型配置，防止速度预设改动原模型和六LoRA。")
    if values.get("模型配置"):
        raise ValueError("周期分支请直接在完整创作台选择模型与六LoRA，不使用外接模型配置覆盖。")
    if values.get("SelfLift二采") and values.get("二采高清分块"):
        raise ValueError("第一版周期SelfLift尚未验证高清分块，请保持二采高清分块关闭；关闭循环后原功能保留。")
    route = values.get("循环条件路线", REFERENCE_ROUTE)
    if route not in {REFERENCE_ROUTE, ANCHOR_ROUTE}:
        raise ValueError("未知循环条件路线，请重新选择参考路线或实验首帧路线。")
    if route == REFERENCE_ROUTE and "minimax_h3_fl2va" in str(values.get("模型", "")).lower():
        raise ValueError("单图参考周期路线需要 Ref2VA 模型；当前是 FL2VA。请在模型选项选择 minimax_h3_ref2va_int8_convrot.safetensors，再运行。")
    if int(values.get("循环视角", 1)) not in (1, 2):
        raise ValueError("循环视角只能为1或2。")
    plan = frame_plan(values.get("循环正片帧数", 204), values.get("循环上下文段数", 1))
    import folder_paths
    # Same-basename lookup is allowed only when unique; never choose a different model.
    resources = [("模型", "diffusion_models"), ("文本编码器", "text_encoders"),
                 ("视频VAE", "vae"), ("音频VAE", "vae")]
    resources += [(f"LoRA{i}", "loras") for i in range(1, 7)
                  if chosen(values.get(f"LoRA{i}")) and values.get(f"LoRA{i}") != "无"]
    if values.get("SelfLift二采"):
        resources.append(("二采放大模型", "latent_upscale_models"))
    resolved = {}
    for field, category in resources:
        name = str(values.get(field) or "")
        available = list(folder_paths.get_filename_list(category))
        if name in available:
            resolved[field] = name
            continue
        basename = name.replace("\\", "/").split("/")[-1]
        matches = [v for v in available if v.replace("\\", "/").split("/")[-1] == basename]
        if len(matches) != 1:
            raise ValueError(f"周期分支缺少或无法唯一定位{field}：{name}。请在云端选择原配方同一文件；不会自动换模型。")
        resolved[field] = matches[0]
    return plan, route, resolved
