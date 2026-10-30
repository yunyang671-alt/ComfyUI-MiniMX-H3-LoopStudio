# RunningHub 界面与模型选择兼容核对（0.3.1候选）

目标页面：https://www.runninghub.cn/workflow/2116044799827599361?source=workspace

本候选基于已发布的前端缓存修复提交 `d5b3014ef09cf927896b645819905e8be888977c`。不修改用户云端实例、v1.0或v2.0定版备份。尚未在用户的RunningHub登录页面验收，不把源码检查说成平台实测。

## 可以确认的机制

1. 工作流JSON保存节点、参数与属性，不携带已安装节点的JavaScript实现。同样23个节点ID可对应不同版本代码，因此导入新版JSON不一定触发“缺节点”，标题更新也不证明界面代码更新。
2. 本项目自定义界面此前只直接读取 `widget.options.values/items`，没有求值函数提供的候选项，也没有处理对象映射。官方ComfyUI前端 `resolveComboValues` 明确支持数组、`function(widget)`、对象键。因此存在确定的控件兼容缺口。截图里主模型与部分LoRA呈现文本框，与取不到数组时的回退路径吻合；仍须检查平台实际widget数据，才能确定本页具体原因。
3. 平台公开模型库与某个节点的当前候选列表不是同一件事。前端只修复列表读取，不自行伪造平台模型目录、下载权限或模型映射。
4. RunningHub官方“原生ComfyUI接口支持”文档说明：通过其代理接口接入的第三方客户端，可选择已收藏的模型。这是该接口场景的说明，不能推导为会员网页里的任意自定义模型字段收藏后必然可用。本候选不要求API Key，也不提交API任务。
5. RunningHub相关公开H3节点的前端注册使用 `rh: {type: "nodes", nodes: [...]}`，且在存在 `app.ensureNodesRegistered` 时显式注册目标类。本候选沿用该公开代码模式；这是源码参考，尚无证据将其称为平台对所有插件的强制规范。

## 本候选的改动

- 新入口：`js/studio_ui_rh031_20261030.js`，避免继续复用旧入口缓存；不要同时保留旧的studio.js、studio_ui_preview_v2.js或其他旧主入口。
- 三个扩展声明各自关联的节点ID，加入公开示例中的rh_config.json。
- 新增widget_choices.js：支持静态数组、同步函数和对象映射；点击/聚焦模型下拉和界面同步时重新读取实际列表。
- 模型字段即使暂时拿不到列表，也保留当前精确模型名；不擅自改成列表第一项。异步或不可用的provider暂不伪装成已支持，保留当前值并提示核对平台原生选择器。
- 界面顶部显示“工作台0.3.1”和 `data-minimx-ui-build="0.3.1-rh-20261030"`，可快速核对实际加载版本。
- 全部77项默认值与定版ui_defaults.js逐字节相同，Ref2V 8步原版、强度1.0不变；16个循环/采样/二采/解码核心指纹不变。
- 自建批量服务仍默认关闭，RunningHub会员队列仍未适配。新界面显示正确不代表会员排队已经可用。

## 平台安装及无推理验收

请平台完整替换节点包，发布完整WEB_DIRECTORY；按其维护流程重启相关后端并刷新前端资源。不要只重新导入JSON，也不要只覆盖一个旧入口文件。独立检查以下两项：

### 界面版本

- 顶部应出现“一键恢复默认设置”和“工作台0.3.1”。
- “周期循环”在图生视频子模式中，与单图模式相邻，旧的巨大循环参数面板不应继续作为主界面出现。
- 记录真实安装commit及实际加载的主入口URL；核对新helper和import没有404/重复扩展注册错误。

### 模型选择

- 对比平台原生 `LoraLoaderModelOnly` 的 `lora_name`、`UNETLoader` 的 `unet_name`、`CLIPLoader` 的 `clip_name`、`VAELoader` 的 `vae_name` 是否能打开平台模型选择器，与MiniMX同类字段作对照。这是界面检查，无需运行任何节点。
- 若原生选择器能搜到而MiniMX字段没有：请平台提供并绑定 `MiniMXH3LoopStudio` 的模型字段映射。`模型→diffusion_models`、`文本编码器→text_encoders`、`视频VAE/音频VAE→vae`、`LoRA1…LoRA6→loras`、`二采放大模型→latent_upscale_models`。这些是本包后端真实目录类别，不是擅自发明的RunningHub映射API。
- 若原生选择器同样没有：核对当前账号/实例的模型提供范围、准确文件名、共享挂载及收藏状态，而不是反复改工作流JSON。
- 若后台候选已有多个、MiniMX界面仍只有一个：记录 `widget.options.values/items` 的类型与报错，确认是否为平台专用异步选择器。本候选支持ComfyUI标准同步provider；平台专用控件仍需实际页面证据后接入。
- 不要只向下拉列表硬加文件名；提交成功还要求平台运行容器实际能解析该模型。不要自动用 `_r` 权重替换用户实测原版，两者公开完整SHA256不同。

## 原始资料

- [RunningHub官方原生ComfyUI接口与模型管理](https://www.runninghub.cn/runninghub-api-doc-cn/doc-8287337)
- [RunningHub中国站8步Ref2V模型页](https://www.runninghub.cn/model/public/2095709823726874626)
- [ComfyUI官方前端组合控件求值](https://github.com/Comfy-Org/ComfyUI_frontend/blob/4d90c430552b8928322563818930e108b3944cd3/src/utils/litegraphUtil.ts)
- [H3前端节点关联及延迟注册示例](https://github.com/RH-RunningHub/ComfyUI-RH-MiniMax-H3/blob/main/web/model_inputs_first.js)
- [H3迁移扩展的rh声明示例](https://github.com/RH-RunningHub/ComfyUI-RH-MiniMax-H3/blob/main/web/model_loader_widget_migration.js)
- [rh_config.json参考](https://github.com/RH-RunningHub/ComfyUI-RH-MiniMax-H3/blob/main/rh_config.json)

受限项：本会话Chrome技能入口文件缺失，尚未读取用户实际页面的DOM/控件/控制台；以上平台安装步骤尚未执行。没有声称管理员限制模型、篡改工作流，或声称问题已在平台解决。
