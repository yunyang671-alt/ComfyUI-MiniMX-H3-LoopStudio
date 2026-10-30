# 依赖分层（0.3.0）

## 必需节点源码与宿主

整个仓库安装一次，包含23个ID，见nodes_manifest.json。Loop、SelfLift及helper源码内置，不要求再装另一套Loop、SelfLift或T8插件。js/与prompt_templates/同样是运行资源。

使用ComfyUI的Python。来源环境为Python3.12、ComfyUI0.43.0、前端1.57.6、PyTorch2.13/cu132；这是来源记录，不是全平台强锁。原生接口缺失应升级平台H3分支，不是再复制一套comfy到custom_nodes。

requirements.txt仅声明numpy、safetensors、aiohttp、Pillow、psutil、opencv-python、imageio-ffmpeg。torch/torchaudio由宿主保持匹配，不把另一环境pip freeze强行安装到平台。

原生节点详见diagnostics.py:NATIVE_REQUIRED；关键接口包括comfy.ldm.minimax、comfy.nested_tensor、comfy.patcher_extension、comfy_execution.graph_utils及H3 FunControlPatch。类名相同但接口不同仍可能失败。

## 外部节点（环境已有即复用）

| 功能 | 插件/节点 | 要求 |
|---|---|---|
| MP4输出 | [VHS](https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite)，VHS_VideoCombine | 必需 |
| Qwen看图写词 | [QwenVL](https://github.com/1038lab/ComfyUI-QwenVL)，AILab_QwenVL | 仅自动写词；版本和字段见manifests/external-nodes.json |
| 写词图缩放/显示 | LoadImage、ImageScaleToTotalPixels、PreviewAny | ComfyUI原生；自动写词需要 |
| 预览/可选Sage补丁 | [KJNodes](https://github.com/kijai/ComfyUI-KJNodes)，ModelPreviewOverrideKJ、PathchSageAttentionKJ | 可选 |
| 注意力加速 | SageAttention及匹配H3补丁 | 可选；按实际GPU/Python/torch选wheel，不随包硬装 |
| 旧Llama/GGUF增强 | llama-cpp-python及GGUF | 可选，与Qwen自动写词不同 |

QwenVL上游自行声明transformers、accelerate、bitsandbytes等依赖，由平台核对后安装在兼容环境。仅循环生成不强制新增这些库。H3的32B编码器不是完整聊天模型。

## 模型与服务

六份H3配方权重及可选完整Qwen4B目录见manifests/models.json；精确现有权重优先复用。二采权重为minimax_h3_latent_upscaler_3d_fp16.safetensors。主模型保留Ref2VA，不因切换均衡/二采/质量换成FL2VA。

批量的sqlite3/threading等为标准库，不是新增一套插件。默认关闭，不创建队列数据库/worker。显式启用需可写user/default/minimx_batch/、input/、output/及同源API。RunningHub会员自动补交未适配，平台不启用此服务也可安装基础节点。
