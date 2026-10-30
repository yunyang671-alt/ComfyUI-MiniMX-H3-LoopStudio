# 23个内置节点及用途

这是一个仓库中的23个注册ID；不是23个独立安装包。全部放在custom_nodes/ComfyUI-MiniMX-H3-LoopStudio/，不要把每个.py分别复制到models或另一节点目录。

| 注册ID | 实现类 | 用途 |
|---|---|---|
| `MiniMXBase_LiaoH3SelfLiftResult` | `LiaoH3SelfLiftResult` | SelfLift二采结果合并 |
| `MiniMXBase_LiaoH3SelfLiftPrepare` | `LiaoH3SelfLiftPrepare` | SelfLift二采准备 |
| `MiniMXBase_WenWuH3AudioDrive` | `WenWuH3AudioDrive` | 音频驱动素材/条件 |
| `MiniMXBase_WenWuH3AudioLength` | `WenWuH3AudioLength` | 内部音频时长 |
| `MiniMXBase_WenWuH3AudioCrop` | `WenWuH3AudioCrop` | 音频裁切 |
| `MiniMXBase_WenWuH3AudioConcat` | `WenWuH3AudioConcat` | 音频拼接 |
| `MiniMXBase_WenWuH3LastFrame` | `WenWuH3LastFrame` | 取末帧供连续段 |
| `MiniMXBase_WenWuH3TrimFramesToAudio` | `WenWuH3TrimFramesToAudio` | 按音频裁切视频帧 |
| `MiniMXBase_WenWuH3ModelLoraConfig` | `WenWuH3ModelLoraConfig` | 外接模型与LoRA配置 |
| `MiniMXH3LoopStudio` | `WenWuMiniMaxH3Unified` | 完整工作台，构建H3生成和周期分支 |
| `MiniMXBase_WenWuH3ReleaseAtStart` | `WenWuH3ReleaseAtStart` | 任务开始释放模型/透传字符串 |
| `MiniMXBase_WenWuH3ReleaseBeforeConditioning` | `WenWuH3ReleaseBeforeConditioning` | 条件编码前释放模型 |
| `MiniMXBase_WenWuH3ReleaseBeforeDecode` | `WenWuH3ReleaseBeforeDecode` | VAE解码前释放模型 |
| `MiniMXBase_WenWuH3ContinuousSegmentBarrier` | `WenWuH3ContinuousSegmentBarrier` | 连续分段执行屏障 |
| `MiniMXBase_WenWuH3ProgressSampler` | `WenWuH3ProgressSampler` | 原配方采样与进度 |
| `MiniMXBase_WenWuH3PhaseMarker` | `WenWuH3PhaseMarker` | 生成阶段状态 |
| `MiniMXBase_LiaoH3EmbeddedLatentUpscaler3D` | `LiaoH3EmbeddedLatentUpscaler3D` | 内置学习式潜空间放大 |
| `MiniMXBase_WenWuH3SigmaTailRefiner` | `WenWuH3SigmaTailRefiner` | Sigma尾段细化 |
| `MiniMXBase_LiaoH3SecondPassModelBarrier` | `LiaoH3SecondPassModelBarrier` | 二采模型屏障 |
| `MiniMXBase_SelfLiftH3Sampler` | `SelfLiftH3Sampler` | 原配方SelfLift二阶段采样 |
| `MiniMXH3LoopModel` | `MiniMXH3LoopModel` | 周期模型前向包装 |
| `MiniMXH3LoopDecode` | `MiniMaxH3LoopDecode` | 带周期上下文的音视频解码 |
| `MiniMXH3SelfLiftLoopSampler` | `MiniMXH3SelfLiftLoopSampler` | 周期SelfLift二阶段采样 |

工作台内部动态构建大部分节点。类名出现在清单里不代表每次任务全部执行。切换均衡/质量改变采样步数；二采调用SelfLift；周期分支统一使用周期模型及解码。

外部VHS和可选Qwen来自各自仓库，平台已有时复用；不要把外部包塞进本包selflift_vendor或js目录。
