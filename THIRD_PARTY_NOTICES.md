# 来源、修改与许可记录

本仓库提供节点代码，未复制或发布其他人的工作流文件。所有上游作者标记及源码内注释予以保留。以下记录截至 2026-10-29；源代码公开可读不等于获得任意再授权。

## liaodaobin / comfyui-liao2049

来源：https://github.com/liaodaobin/comfyui-liao2049/tree/969937d331c51215d5396da03a1c5d977742c28e

- `minimax_h3_unified.py` → `studio.py`：追加循环字段、单图约束、模型选择保护、循环图和解码，内部节点/路由命名空间调整，以及可选加速节点完整性检查。
- `h3_optional_sampling.py`：选择周期 SelfLift 采样器，保留上游采样配方及关闭循环路径。
- `h3_dependencies.py`：接口命名空间调整。
- `h3_latent_upscaler_embedded.py`、`h3_segmented_avatar.py`：随包辅助源码；后者未单独注册额外数字人节点。
- `js/liao_h3_ui_20260823e.js` → `js/studio.js`：独立节点 ID、接口命名空间、循环面板及导入时模型保留。
- `js/seed_control.js`、`prompt_templates/*.md`：上游功能资源。

固定上游及当前 GitHub 仓库未发现独立 LICENSE，GitHub 元数据 license 为 null。本项目不为这些代码新授 MIT/GPL 等许可；相关权利归原权利人，公开部署、再分发的许可范围需向上游核实。

## pxl-pshr / ComfyUI-MiniMaxH3-Loop

来源：https://github.com/pxl-pshr/ComfyUI-MiniMaxH3-Loop/tree/733647e41a7574a354639623d4b50e7f6152ee09

`__init__.py` 原样保存为 `_loop_vendor.py`。上游 Git blob：`436156f86671cbc00bd7b2f68c8de36ac6d6e673`。本包校验此指纹并通过私有模块调用，仅导出自身命名空间的解码 ID。

许可：GPL-3.0，完整正文在 [`licenses/Loop-GPL-3.0.txt`](licenses/Loop-GPL-3.0.txt)。上游 README / PROMPTING 随包保留于 `docs/upstream/`，没有复制其中引用的工作流 JSON 或媒体。有关本包自行编写的循环适配代码，也按 GPL-3.0 发布；这不改变其他上游代码的许可状态。

## facok / comfyui-SelfLift

来源：https://github.com/facok/comfyui-SelfLift/tree/835c3cf7919410f71f414688f049c6ca497789d0

- `selflift_vendor/nodes.py`：保留真实两阶段 SelfLift 算法，增加默认关闭的 `periodic` 分支以规范 AV 周期尾部。
- `selflift_vendor/h3_upscaler.py`：增加默认关闭的周期学习式放大路径及相应内存估计。
- `selflift.py`、`h3_tiling.py`、`h3_tst.py`、`diagnostics.py`：完整辅助模块。
- `selflift_vendor/__init__.py`：本项目私有加载入口，不覆盖原插件注册。

固定上游及当前 GitHub 仓库未发现独立 LICENSE，GitHub 元数据 license 为 null。相关权利归上游，不将其误标为本项目原创或统一 GPL 授权。平台采用及再分发前需核实其许可。

## 本项目新增

`loop_config.py`、`loop_runtime.py`、`periodic_ops.py`、`js/loop_controls.js`、根目录 `diagnostics.py`、`tools/`、清单和项目说明属于本次整理新增或组合代码。新增代码按 GPL-3.0 提供，正文见 `licenses/Loop-GPL-3.0.txt`。整个组合包由于上游授权状态不同，不设置会误导读者的统一 LICENSE。

环境依赖链接：

- ComfyUI：https://github.com/Comfy-Org/ComfyUI
- VideoHelperSuite：https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite
- KJNodes：https://github.com/kijai/ComfyUI-KJNodes
- SageAttention：https://github.com/thu-ml/SageAttention

这些环境项目未在本仓库重复打包，其许可由各项目自行提供。
