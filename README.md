# MiniMX H3 LoopStudio

为 ComfyUI 的 MiniMax H3 完整创作台增加采样阶段的周期循环，以及 SelfLift 二采放大的周期时间边界处理。版本：`0.2.0-cloud-test`。

**提交给 RunningHub 的节点仓库地址：** https://github.com/yunyang671-alt/ComfyUI-MiniMX-H3-LoopStudio

## 添加原因

工作流使用自定义节点 `MiniMXH3LoopStudio`。只有工作流 JSON、或者环境中只有其他 H3 创作台节点时，无法识别此类，会出现 `has no class_type`、节点爆红、参数显示 `UNKNOWN` 等问题。需要平台安装本仓库的 Python 节点及前端扩展，并重启后端、刷新前端。

本仓库只交付节点代码、通用提示词模板、依赖清单和说明，不附带任何人的工作流 JSON、输入素材、任务记录、API Key 或模型权重。

## 安装内容与完整依赖

本仓库根目录就是一个可安装的 ComfyUI 节点包，**克隆一个仓库即可**：

```sh
cd ComfyUI/custom_nodes
git clone https://github.com/yunyang671-alt/ComfyUI-MiniMX-H3-LoopStudio.git
# 使用 ComfyUI 自己的 Python 环境执行；不要另装不同版本的 torch
python -m pip install -r ComfyUI-MiniMX-H3-LoopStudio/requirements.txt
```

随后重启 ComfyUI 后端，浏览器强制刷新。RunningHub 用户将本仓库地址交给平台技术人员添加；上传 JSON 并不能安装 Python 节点。

| 组成 | 是否包含 | 说明 |
| --- | --- | --- |
| 完整 H3 创作台 Python 和 JavaScript 界面 | 包含 | 使用独立节点 ID 和接口前缀 |
| 循环模型包装、周期解码 | 包含 | 固定版本 Loop 源码内置于 `_loop_vendor.py` |
| SelfLift 采样、放大网络、分块和辅助文件 | 包含 | 全套所需模块位于 `selflift_vendor/` |
| 周期 SelfLift 适配及控件 | 包含 | `loop_runtime.py`、`periodic_ops.py`、`loop_config.py`、`js/loop_controls.js` |
| 模板、随机种子控件、依赖诊断 | 包含 | 模板属于节点功能资源 |
| ComfyUI 原生 H3、AV latent、采样、音视频节点 | 环境提供 | 需要具有这些接口的 ComfyUI；详见 `DEPENDENCIES.md` |
| VHS 视频合成 | 环境提供 | 已有 `VHS_VideoCombine` 时无需重复安装 |
| KJ 预览和 SageAttention 加速 | 可选，环境提供 | 不作为基础循环依赖；缺少时使用原生注意力，速度可能降低 |
| 模型权重和 CUDA 二进制包 | 不包含 | 循环本身无需新增权重；SelfLift 使用环境已有的兼容放大权重 |

**不需要再单独安装 `ComfyUI-MiniMaxH3-Loop`、`comfyui-SelfLift` 或原创作台包，才能注册本包的循环节点。** 本包不会注册或替换其他包原有节点的 ID。即使平台已有 Loop/SelfLift，仍需要本包内适配过的私有代码；两者不会互相覆盖。

实际导出的全部 **23 个节点 ID** 见 [`nodes_manifest.json`](nodes_manifest.json)，其中主要节点为：

- `MiniMXH3LoopStudio`：完整创作台入口，已有使用此 ID 的工作流无需改名。
- `MiniMXH3LoopModel`：采样周期模型包装。
- `MiniMXH3SelfLiftLoopSampler`：周期 SelfLift 两阶段采样。
- `MiniMXH3LoopDecode`：周期音视频解码。
- `MiniMXBase_*`：随包提供的 19 个创作台内部节点。

## 使用范围

1. 选择单图，打开“启用周期循环”；推荐“单图参考”路线。图片提供外观参考，不强制成为第 1 帧。保留首帧锚定属于实验路线。
2. 输出帧数是 17 的整数倍。默认 204 帧，在 24 fps 下为 8.5 秒；内部额外的 5 帧仅用于 H3 上下文，周期解码会移除。循环开启时普通时长控件会禁用。
3. SelfLift 维持实际两阶段采样及学习式潜空间放大，对时间卷积使用周期边界。循环模式要求 `rho=0`、关闭高清分块。全周期放大可能增加显存占用。
4. 精确使用用户选定的模型、VAE 和 LoRA，缺少所选文件时明确报错。循环开关关闭后保留创作台的其他生成模式；目前周期功能限定单图模式。
5. 生成结果仍由提示词、模型和采样决定；不能保证所有画面都达到主观无缝效果。

## 平台一次核查

完成安装、ComfyUI 加载全部节点后，在同一服务地址打开：

```text
/minimxa-loop/package-diagnostics
```

该只读接口汇总本包 23 个节点、原生节点、可选加速节点和模型目录数量。不会下载、安装或加载模型，不返回用户素材或模型路径。请平台一次核查 `missing_bundled_nodes` 和 `missing_native_nodes` 均为空，并确认 VHS 可用；选定模型文件还需要核对实际工作流参数。原生节点缺失应升级平台 ComfyUI，不能靠重复安装本包修复。

完整接口清单、可选依赖及故障定位见 [`DEPENDENCIES.md`](DEPENDENCIES.md)。

## 来源与许可

本项目包含对以下节点代码的引用和修改，不声称其为本项目原创：

| 作者 / 仓库 | 固定提交 | 用途 |
| --- | --- | --- |
| [liaodaobin/comfyui-liao2049](https://github.com/liaodaobin/comfyui-liao2049) | `969937d331c51215d5396da03a1c5d977742c28e` | 创作台、界面、辅助节点和提示词模板 |
| [pxl-pshr/ComfyUI-MiniMaxH3-Loop](https://github.com/pxl-pshr/ComfyUI-MiniMaxH3-Loop) | `733647e41a7574a354639623d4b50e7f6152ee09` | 原始周期采样和解码算法 |
| [facok/comfyui-SelfLift](https://github.com/facok/comfyui-SelfLift) | `835c3cf7919410f71f414688f049c6ca497789d0` | SelfLift 两阶段采样和学习式放大 |

来源文件、修改范围和许可状态见 [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md)。Loop 的 GPL-3.0 正文随包保留。其余两个固定上游未提供独立 LICENSE，不能把本仓库整体解释为 MIT 或统一的开源授权；平台采用和再分发前应核实上游许可。

## 验证状态

本版用于云端人工测试。已做源码结构、图展开、合成张量的周期操作和两阶段采样检查；这些检查不等于真实 H3 模型推理。尚未确认 RunningHub 对本包的安装、显卡内核兼容性或实际生成效果，云端测试由使用者完成。
