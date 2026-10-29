# 可直接提交给 RunningHub 的添加申请

仓库地址：https://github.com/yunyang671-alt/ComfyUI-MiniMX-H3-LoopStudio

添加原因：工作流使用 `MiniMXH3LoopStudio`，平台未注册该节点时会显示 UNKNOWN 参数，并提示 `has no class_type`。需要安装此完整节点包和前端扩展，重启后端后刷新前端。

节点说明：为 H3 完整创作台提供单图采样阶段周期循环，以及 SelfLift 二采的周期边界适配。仓库内包含创作台、固定 Loop 算法、SelfLift 全部必要模块和前端，根目录可直接作为 custom_nodes 包安装，合计 23 个节点。无需另外补装 Loop 或 SelfLift 仓库。

请一次核查：

1. 使用 ComfyUI 的 Python 安装 `requirements.txt`，保留原有 torch 及与其匹配的 torchaudio。
2. 重启后检查 `nodes_manifest.json` 中全部 23 个 ID，确认没有导入失败。
3. 打开同一 ComfyUI 服务的 `/minimxa-loop/package-diagnostics`，原生节点和随包节点缺失清单均应为空。
4. 如环境已有 `VHS_VideoCombine`，无需重复添加。SageAttention / KJ 预览属于可选能力。
5. 模型使用实际任务选定的已有权重；循环本身不增加权重。启用 SelfLift 时需要兼容的 H3 学习式放大权重。

代码引用、作者地址、固定版本和许可状态已写在 README 与 THIRD_PARTY_NOTICES.md。仓库不包含任何第三方工作流 JSON 或用户素材。当前为云端人工测试版本；请先确认平台安装及接口兼容，实际云端生成由用户测试。
