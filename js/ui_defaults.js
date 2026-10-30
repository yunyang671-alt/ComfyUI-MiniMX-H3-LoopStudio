// Exact stable recipe; reset keeps the user’s prompt, uploaded media and credentials.
export const STUDIO_DEFAULTS = Object.freeze({
  "模型": "minimax_h3_ref2va_int8_convrot.safetensors",
  "文本编码器": "qwen3vl_32b_minimax_h3_int8_convrot.safetensors",
  "文本编码器类型": "minimax",
  "文本编码器设备": "default",
  "视频VAE": "minimax_h3_video_vae_fp16.safetensors",
  "音频VAE": "minimax_h3_audio_vae_fp32.safetensors",
  "模型权重精度": "default",
  "SageAttention": "auto",
  "允许编译": false,
  "画面比例": "16:9 (Widescreen)",
  "百万像素": 1,
  "尺寸倍数": 32,
  "时长秒": 6,
  "采样器": "euler",
  "调度器": "simple",
  "采样步数": 10,
  "降噪强度": 1.0,
  "参考图尺寸": "match",
  "文生视频": false,
  "图生视频": true,
  "首尾帧": false,
  "Llama模型": "",
  "Llama上下文": 8192,
  "Llama运算设备": "自动",
  "启用提示词增强": false,
  "仅增强提示词": false,
  "视频编辑": false,
  "数字人": false,
  "加速方案": "参考工作流加速",
  "视频SigmaShift": 10.0,
  "音频SigmaShift": 3.0,
  "LoRA1": "minimax_h3_ref2v_turbo_4step_v0.1_comfyui_bf16.safetensors",
  "LoRA1强度": 1.0,
  "LoRA2": "无",
  "LoRA2强度": 0.0,
  "双人数字人": false,
  "视频编辑模式": "均衡8步",
  "提示词服务": "本地 Llama",
  "云端模型": "MiniMax-M2.7",
  "增强请求序号": 1,
  "视觉识别模型": "",
  "提示词模板": "自动匹配（按生成模式）",
  "分镜数": 1,
  "自定义模型配置": true,
  "视频编辑功能": "通用编辑",
  "二采放大精修": false,
  "二采方式": "潜空间二采",
  "MV数字人": false,
  "MV图片时长": "[6.3]",
  "MV音乐开始秒": 0.0,
  "MV音乐结束秒": 0.0,
  "音频剪切配置": "{}",
  "图生连续拼接": false,
  "图生当前图片序号": "1",
  "MV当前图片序号": "1",
  "多参考连续拼接": false,
  "多参考当前分段": "1",
  "NSFW配置": false,
  "LoRA3": "无",
  "LoRA3强度": 0.6500000000000001,
  "LoRA4": "无",
  "LoRA4强度": 0.3500000000000001,
  "LoRA5": "无",
  "LoRA5强度": 0.3500000000000001,
  "LoRA6": "无",
  "LoRA6强度": 3.0000000000000004,
  "武戏配置": false,
  "武戏速度": 3.0,
  "注意力机制": "PyTorch",
  "SelfLift二采": true,
  "二采放大模型": "minimax_h3_latent_upscaler_3d_fp16.safetensors",
  "二采高清分块": false,
  "启用周期循环": true,
  "循环条件路线": "单图参考（推荐）",
  "循环正片帧数": 136,
  "循环上下文段数": 1,
  "循环视角": 1
});
export function restoreStudioDefaults(node) {
  for (const [name,value] of Object.entries(STUDIO_DEFAULTS)) {
    const target = node.widgets?.find(item => item.name === name);
    if (target) target.value = value;
  }
  node.properties ??= {};
  // A loop accepts one image. Keep extra files on disk and remember selections,
  // but deactivate extra image inputs so reset is immediately executable.
  const extras = node.widgets?.filter(item => /^图片([2-9]|1[0-9]|20)$/.test(item.name) && item.value && item.value !== "未选择") || [];
  if (extras.length) {
    node.properties.minimx_extra_images_before_reset = extras.map(item => [item.name,item.value]);
    for (const item of extras) item.value = "未选择";
  }
  node.properties.liao_fixed_seed = false;
  node.properties.wwh3StoryboardAuto = true;
  node.properties.minimx_requested_loop_seconds = 6;
  delete node.properties.liao_combat_lora_restore;
  node.__wwh3SelectedMode = "图生视频";
  node.__wwh3I2vPromptIndex = null;
  node.__wwh3MvPromptIndex = null;
  node.__wwh3MultiRefSegmentIndex = null;
  node.__wwh3PresetKey = "图生视频|均衡8步";
  node.__wwh3SeedSync?.();
}
