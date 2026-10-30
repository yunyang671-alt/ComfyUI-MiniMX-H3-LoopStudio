# 模型清单与目录

权重不上传GitHub；完整机器清单为[manifests/models.json](../manifests/models.json)，含固定官方revision、URL、字节数、SHA256。H3六文件约69.64GB；Qwen额外完整目录约8.89GB，仅自动写词需要。平台已有同一文件即可复用。

| 类别/位置（相对ComfyUI/models） | 用途 | 来源 |
|---|---|---|
| `diffusion_models/minimax_h3_ref2va_int8_convrot.safetensors` | 视频与音频联合生成主模型（Ref2VA INT8 ConvRot） | [Comfy-Org/MiniMax-H3](https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/77aac5182eb85bb20930536bac73e498bbe2bfd7/diffusion_models/minimax_h3_ref2va_int8_convrot.safetensors) |
| `text_encoders/qwen3vl_32b_minimax_h3_int8_convrot.safetensors` | 提示词及参考内容的多模态编码器 | [Comfy-Org/MiniMax-H3](https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/77aac5182eb85bb20930536bac73e498bbe2bfd7/text_encoders/qwen3vl_32b_minimax_h3_int8_convrot.safetensors) |
| `vae/minimax_h3_video_vae_fp16.safetensors` | 视频像素/音频波形与潜变量之间的编解码器 | [Comfy-Org/MiniMax-H3](https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/77aac5182eb85bb20930536bac73e498bbe2bfd7/vae/minimax_h3_video_vae_fp16.safetensors) |
| `vae/minimax_h3_audio_vae_fp32.safetensors` | 视频像素/音频波形与潜变量之间的编解码器 | [Comfy-Org/MiniMax-H3](https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/77aac5182eb85bb20930536bac73e498bbe2bfd7/vae/minimax_h3_audio_vae_fp32.safetensors) |
| `latent_upscale_models/minimax_h3_latent_upscaler_3d_fp16.safetensors` | SelfLift 两阶段之间的学习式潜空间放大模型 | [LBH-123-AI/Minimax_h3_latent_Upscaler](https://huggingface.co/LBH-123-AI/Minimax_h3_latent_Upscaler/resolve/13ccf95d85d120bdbc92c05b1247a6e147bf54bf/minimax_h3_latent_upscaler_3d_fp16.safetensors) |
| `loras/minimax_h3_ref2v_turbo_4step_v0.1_comfyui_bf16.safetensors` | Ref2VA 蒸馏加速 LoRA | [Comfy-Org/MiniMax-H3](https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/77aac5182eb85bb20930536bac73e498bbe2bfd7/loras/minimax_h3_ref2v_turbo_4step_v0.1_comfyui_bf16.safetensors) |

## Qwen自动写词

完整目录：`ComfyUI/models/LLM/Qwen/Qwen3-VL-4B-Instruct/`，包括2个safetensors分片、索引、config、预处理器和词表等共12文件。不能只下载一个分片，不能把所有文件丢进diffusion_models。使用平台共享模型库时须让QwenVL解析到完整目录，单靠extra_model_paths不一定能覆盖其LLM目录。

官方：[Qwen/Qwen3-VL-4B-Instruct](https://huggingface.co/Qwen/Qwen3-VL-4B-Instruct/tree/ebb281ec70b05090aa6165b016eac8ec08e71b17)。这与H3的32B专用编码器不同。12文件逐项地址见机器清单。

默认基础循环不强制下载Qwen。检查基础6文件：`python tools/check_models.py /path/to/ComfyUI/models`；含Qwen：添加`--autoprompt`。加`--sha256`可读取全文件校验；默认仅检查路径与大小，不自动下载。

主模型固定Ref2VA INT8 ConvRot；不要因档位切换换成FL2VA、pruned或另一LoRA。二采放大文件名与旧h3_upscaler_lms不同，本版已兼容精确新名。

## 2026-10-30最终默认LoRA

当前默认为`minimax_h3_ref2v_turbo_8step_v1.0_768p_comfyui_bf16.safetensors`，强度1.0。[固定官方地址](https://huggingface.co/lightx2v/Minimax-h3-Turbo/resolve/30f485ed874aa44c8183348ad361c5eabad318da/minimax_h3_ref2v_turbo_8step_v1.0_768p_comfyui_bf16.safetensors)。18项恢复清单中的原4步项已替换为8步项，旧4步仅用于历史配方。详见[定版说明](STABLE_DEFAULTS.md)。
