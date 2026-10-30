# 节点添加原因与提交说明

仓库：https://github.com/yunyang671-alt/ComfyUI-MiniMX-H3-LoopStudio

请求版本：**0.3.0**，请记录commit SHA，不使用旧0.2缓存或只上传JSON。

原因：工作流调用MiniMXH3LoopStudio，平台原有H3创作台不是这个class_type，会出现缺失/UNKNOWN。仅安装其他H3工作台不能替代本包周期模型包装、周期SelfLift、周期解码。

本仓库整体是**一个节点包，包含23个注册ID**。全部Python/helper/前端齐全，不是申请23个独立仓库。原始H3、Loop、SelfLift作者与固定源码版本见THIRD_PARTY_NOTICES.md；不收录他人工作流。内置Loop/SelfLift无需重复安装；已有VHS、原生节点和精确模型文件即可复用。

旧申请后补齐最新工作台、参数保护、模型文件名识别及自建批量代码。默认关闭自建队列，避免受限平台因SQLite/worker导致整包加载失败；生成核心保持不变，23ID不变。

基础需求：完整工作台+单张周期循环+SelfLift二采+VHS输出。**RunningHub会员网页自动补交未适配，不列为已支持能力。** Qwen写词可选，已有AILab_QwenVL时核对版本和完整Qwen4B模型，无需申请另一套私有写词节点。

请按[完整安装与验收](RUNNINGHUB_INSTALL.md)一次检查代码、原生接口、模型和前端。模型官方地址、精确版本、大小及SHA256均随仓库提供；无需访问用户服务器、读取私人工作流或获取API密钥。
