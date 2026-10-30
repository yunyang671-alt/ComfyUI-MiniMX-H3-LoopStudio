# MiniMX H3 LoopStudio

**版本0.3.1 · RunningHub安装交付整理版 · 2026-10-30**

ComfyUI自定义节点包：完整H3工作台、周期采样、周期SelfLift二采和周期解码。补齐最新代码、模型文件名兼容及前端资源，保留最终稳定配方的生成核心。**本版是安装结构与可选服务隔离更新，不是新的循环算法。**

给平台技术人员：先读 **[RunningHub安装与验收](docs/RUNNINGHUB_INSTALL.md)**；添加理由在 **[提交说明](docs/RUNNINGHUB_REQUEST.md)**。

## 安装范围

| 内容 | 本包提供 | 环境需提供 |
|---|---|---|
| 工作台及内部节点 | 23个，ID与旧包一致 | 支持H3的ComfyUI原生节点 |
| 周期模型包装、采样、解码 | 完整源码 | H3主模型、编码器、两个VAE |
| SelfLift二采 | 完整vendor及周期适配 | 放大权重、所选LoRA |
| 视频合成 | 不重复打包 | VHS的VHS_VideoCombine |
| 自建批量、TXT、命名、可视化及本地保存 | 全代码随包，默认不启动 | 管理员启用、可写目录及同源接口 |
| 自动看图写词 | 自建批量的图构建代码 | 可选QwenVL节点和完整Qwen4B模型 |
| RunningHub会员网页自动补交 | **未适配** | 平台任务通道适配，不能靠装节点替代 |

本仓库只放节点源码、通用模板、工具与安装资料；不放第三方工作流、个人素材、任务记录、密钥或大模型实体。

## 标准Git安装

仓库根目录就是节点目录；不要再嵌套一层，不要只拷贝单个Python文件。

```sh
cd /path/to/ComfyUI/custom_nodes
git clone https://github.com/yunyang671-alt/ComfyUI-MiniMX-H3-LoopStudio.git
cd ComfyUI-MiniMX-H3-LoopStudio
# 使用运行ComfyUI的同一个Python/虚拟环境
python tools/verify_package.py
python -m pip install -r requirements.txt
```

重启ComfyUI，浏览器强制刷新。本包不强装、升级或降级平台的torch、CUDA、torchaudio，也不在导入时下载模型。pyproject.toml提供项目元数据，不代表已注册Comfy Registry；不需要pip install .、虚构PublisherId或额外install.py。

**更新必须完整替换目录。** 旧js/studio.js必须从活动目录移走，否则与新js/studio_ui_preview_v2.js重复初始化。旧目录如需保留，请放到custom_nodes之外。不要混装不同版本文件。

## 无推理验收

```sh
python tools/check_server.py http://127.0.0.1:8188
python -m unittest discover -s tests -p "test_*.py"
python tools/check_models.py /path/to/ComfyUI/models
# 可选：读取全部权重，比较SHA256，会有较多磁盘IO
python tools/check_models.py /path/to/ComfyUI/models --sha256
```

check_server只GET节点信息，不提交任务。默认检查23个本包节点、原生依赖、VHS和精确H3模型下拉项。通过这些检查不等于已验证平台GPU推理或画面接缝。

只读接口：/minimxa-loop/package-diagnostics、/minimxa-loop/package-features。平台若不转发自定义接口，可用标准/object_info及服务日志核对。23节点用途见[节点清单](docs/NODES.md)，模型来源/大小/SHA256见[模型说明](docs/MODELS.md)与[机器清单](manifests/models.json)。

## 自建批量服务（可选）

默认MINIMX_ENABLE_BATCH_SERVICE=0。不导入批量服务，不创建其SQLite，不启动worker，不向/prompt补交。单张周期生成和工作台正常提供。

自建ComfyUI管理员在启动服务前显式设置：

```sh
export MINIMX_ENABLE_BATCH_SERVICE=1
python main.py --listen 0.0.0.0 --port 8188
```

可选服务因目录权限等失败时，日志保留异常，基础节点保持加载；修复后重启。不能把本地队列当作RunningHub会员队列。本地保存仍需浏览器授权并保持网页打开。

批量在创建时保存参数快照；继续旧批次不会自动使用页面后来改动的秒数、分辨率和档位。周期时长按17帧对齐，24fps：3秒目标→68帧/2.8333秒，4秒→102帧/4.25秒，6秒→136帧/5.6667秒。周期约束不保证任意图片/种子/提示词均视觉无缝；文件是否重复播放由播放器控制。

## 来源与许可

参考[liaodaobin/comfyui-liao2049](https://github.com/liaodaobin/comfyui-liao2049)、[pxl-pshr/ComfyUI-MiniMaxH3-Loop](https://github.com/pxl-pshr/ComfyUI-MiniMaxH3-Loop)、[facok/comfyui-SelfLift](https://github.com/facok/comfyui-SelfLift)。固定上游、修改范围和许可状态见[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。未把组合包误标为统一MIT/GPL；上游许可待核实事项如实保留。

格式参考ComfyUI官方[Git节点安装约定](https://docs.comfy.org/custom-nodes/backend/manager)与[项目元数据说明](https://docs.comfy.org/registry/specifications)。本整理不代表RunningHub认证，接受范围及H3分支兼容以平台验收为准。

## 2026-10-30默认配方定版

一键恢复默认LoRA已按用户实测改为Ref2V 8-step v1.0 768p原版，强度1.0；其他默认值、全部生成核心不变。见[精确身份和恢复说明](docs/STABLE_DEFAULTS.md)。RunningHub会员自动排队仍需单独适配。

2026-10-30前端资源修复：公网旧模块地址仍返回4步配置，主入口改为`js/studio_ui_rh031_20261030.js`，恢复默认模块采用新版本地址。恢复后显示实际LoRA文件名和强度；模型身份、默认参数及循环核心未改变。

## RunningHub界面兼容候选

0.3.1为独立的平台兼容候选，尚未在用户RunningHub页面验收。动态模型候选、节点前端关联和界面版本标记的变更见[兼容核对说明](docs/RUNNINGHUB_UI_COMPAT.md)。云端定版和私有v1.0/v2.0备份保持不变。
