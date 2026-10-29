# 平台依赖与故障定位

## 必装：一个仓库

将本仓库整体安装到 `ComfyUI/custom_nodes/ComfyUI-MiniMX-H3-LoopStudio/`。不要只复制 `__init__.py`，也不要只复制 `studio.py`。`js/`、`selflift_vendor/`、`prompt_templates/`、`_loop_vendor.py`、`nodes_manifest.json` 都是安装内容。

Python 包清单：`torch`（使用平台原有版本）、`numpy`、`safetensors`、`aiohttp`、`Pillow`、`psutil`、`opencv-python`、`imageio-ffmpeg`、与 torch 匹配的 `torchaudio`。本包不会在启动时自动执行 pip。

## ComfyUI 原生能力

需要支持 MiniMax H3 的现代 ComfyUI，并提供 `comfy.patcher_extension`、`comfy.ldm.minimax`、`comfy.nested_tensor`、`comfy_execution.graph_utils`、H3 FunControlPatch 和音视频解码接口。不能仅根据版本字符串判断平台分支是否齐全。

必须存在的原生节点见 `diagnostics.py` 的 `NATIVE_REQUIRED`。包括 H3 条件和 SigmaShift、AV latent 合并拆分、自定义采样器、模型和 VAE 加载器、图像/视频/音频 IO、注意力后端。它们来自 [ComfyUI](https://github.com/Comfy-Org/ComfyUI)，无需把原生代码再次复制到 custom_nodes。

运行服务的 `/minimxa-loop/package-diagnostics` 汇总检查；也可对已启动服务执行 `python tools/check_server.py http://127.0.0.1:8188`。后者读取标准 `/object_info`，即使本包根本导入失败也能列出缺失的 23 个节点。

## 环境已有时不重复安装

- 视频合成：[`ComfyUI-VideoHelperSuite`](https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite) 的 `VHS_VideoCombine`。它是输出端节点，不是循环算法的一部分；平台已有就无需复制。
- 可选加速/预览：[`ComfyUI-KJNodes`](https://github.com/kijai/ComfyUI-KJNodes)。`PathchSageAttentionKJ` 和 `ModelPreviewOverrideKJ` 由该包提供。上游创作台还兼容环境中的 `MiniMaxH3MemoryEfficientSageAttentionPatch`；本包不会假设平台必然有此补丁，只有相关补丁和 Python 加速库齐备时才启用。缺少 SageAttention 时创作台会发出速度提示并回退原生注意力，未安装预览时跳过预览节点。SageAttention 的 wheel 必须匹配实际 GPU、CUDA、Python、PyTorch，不能通过随包塞入任意 wheel 解决。
- `MinimaxH3LatentUpscalerNode3D`、`MiniMaxH3LatentUpscaleCombined` 仅为上游保留的兼容分支。本包已提供内置潜空间放大节点，不要求安装这两个外部插件。
- Loop 原文件包含未使用的 ControlVideo / 插帧类，但本包只使用私有循环包装和解码，不对外注册插帧节点，因此不依赖 FILM、RIFE 或 ComfyUI-Frame-Interpolation。
- 本地提示词增强可选 `llama-cpp-python` 和兼容 GGUF；云端增强可选用户自行配置的服务。均不是视频循环生成的必要依赖。本包不包含用户 API Key。

## 模型文件

循环算法没有新增独立权重。基础生成需要用户选择的 H3 diffusion model、对应文本编码器、视频 VAE、音频 VAE；使用的 LoRA 也须已存在。启用 SelfLift 时还需要兼容 `h3_upscaler_lms` 学习式放大模型，目录为 `models/latent_upscale_models/`。权重以各自发布者许可及来源为准，本仓库不代发、不替换用户已选择的权重，也不包含私人模型配方。

## 一次验收清单

1. 后端启动没有本包 `IMPORT FAILED`；Python requirements 全部可导入。
2. `/object_info` 中 `nodes_manifest.json` 的 23 个 ID 全部存在。
3. `/minimxa-loop/package-diagnostics` 中原生节点缺失列表为空，VHS 状态可用。
4. 前端网络请求能加载本包 `studio.js`、`loop_controls.js`、`seed_control.js`；节点出现完整工作台及循环开关。
5. 工作流选定的全部权重在实际模型列表中。目录数量大于零不等于某个具体文件存在。
6. 用单张自有图片做一次云端人工测试，再检查输出帧数、时长、接缝及 SelfLift 日志。

第 1—5 项用于在一次安装中排查所有已知代码和环境依赖；第 6 项才检验真实推理。平台后端版本、权限和硬件内核仍需平台确认。
