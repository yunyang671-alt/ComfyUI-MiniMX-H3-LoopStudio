# 给RunningHub技术人员：安装与验收

## 请求范围

安装Git自定义节点包**ComfyUI-MiniMX-H3-LoopStudio 0.3.0**。根目录有__init__.py、NODE_CLASS_MAPPINGS、WEB_DIRECTORY="./js"，不是工作流JSON，不是23个独立插件。旧提交16c053ddf220d97c50a549d182f5a1edcabe0a3b是0.2旧包，请使用本次0.3提交并记录实际SHA。

基础范围：完整工作台、单张周期采样、SelfLift二采、周期解码。自建批量代码随包但默认关闭；**不请求平台把本地补交绕接会员计费或并发通道**。没有平台任务通道适配前，不承诺会员网页批量即用。

## 安装目录

```text
ComfyUI/
  custom_nodes/
    ComfyUI-MiniMX-H3-LoopStudio/
      __init__.py
      platform_config.py
      studio.py
      loop_config.py / loop_runtime.py / periodic_ops.py
      _loop_vendor.py
      selflift_vendor/          # 完整二采源码
      js/                       # 完整前端，WEB_DIRECTORY
      prompt_templates/
      requirements.txt / pyproject.toml
      nodes_manifest.json / node_list.json
      manifests/                # 精确模型/外部节点/核心指纹
      tools/ / docs/ / licenses/
  models/                       # 权重单独部署或使用平台共享挂载
```

不能再嵌套第二个同名目录。不要覆盖其他H3插件；本包23个ID以MiniMX命名，和原作者插件可以区分。

## 安装/更新步骤

1. 如已有旧版，先在平台维护窗口停对应服务；旧目录移到custom_nodes之外，再完整安装本版。不能让旧js/studio.js与新入口并存。不要仅覆盖studio.py或只增加JS。
2. 在运行ComfyUI的同一个解释器执行：

```sh
cd /path/to/ComfyUI/custom_nodes
git clone https://github.com/yunyang671-alt/ComfyUI-MiniMX-H3-LoopStudio.git
cd ComfyUI-MiniMX-H3-LoopStudio
python tools/verify_package.py
python -m pip install -r requirements.txt
```

3. 使用平台已支持H3的ComfyUI原生节点和VHS。对照[依赖](../DEPENDENCIES.md)与[模型](MODELS.md)，已有精确节点及模型不重复安装。本包不强改torch/CUDA/torchaudio，不在导入时下载模型。
4. **保持MINIMX_ENABLE_BATCH_SERVICE未设置或为0。** 基础加载不创建本包SQLite/worker。可选服务异常隔离，不阻止基础节点注册。
5. 重启后端，发布WEB_DIRECTORY并刷新前端缓存。当前主入口是js/studio_ui_preview_v2.js；studio_ui_controls.js、ui_defaults.js及其本地import目标必须全部可访问。

Windows同样使用对应Python与目录，无机器专用DLL/wheel/绝对路径。Git安装即可；不要求Comfy Registry注册，也不要运行pip install .。

## 一次性无推理检查

```sh
python tools/verify_package.py
python -m unittest discover -s tests -p "test_*.py"
python tools/check_server.py http://127.0.0.1:8188
python tools/check_models.py /path/to/ComfyUI/models
# 可选，全权重读取，有较多磁盘IO
python tools/check_models.py /path/to/ComfyUI/models --sha256
```

- 日志无本包IMPORT FAILED，版本0.3.0。
- /object_info有nodes_manifest.json全部23项、原生依赖、VHS。
- 模型下拉可接受精确Ref2VA与二采权重文件名；不能仅看目录数量。
- /minimxa-loop/package-features返回batch_enabled:false为正常默认，不是缺文件。平台不转发自定义路由时，使用标准/object_info和日志检查。
- 完整工作台可见，周期/单图、时长、比例、档位可调，未重复加载旧入口。
- 自动写词为可选项；缺少Qwen不能据此判基础循环包不完整。

## 人工推理验收（由用户执行）

自有图片，保持Ref2VA、指定VAE/LoRA，先小尺寸验证均衡/二采/质量。周期按17帧对齐，6秒目标实际136帧/24fps。日志应有MiniMX Loop plan / MiniMX Loop sampler，二采应有circular_time=True。核对帧数、构图、提示词、接缝；“节点不红”不能代替生成验收。

生成核心与用户冻结稳定版相同，见manifests/core-baseline.json。本版未加首尾冻结、倒放、淡入淡出或插帧拼接；周期算法不保证任意输入都无感衔接。

## 可选Qwen写词与批量服务

写词节点AILab_QwenVL的固定来源/字段见manifests/external-nodes.json；完整Qwen3-VL-4B约8.89GB，放models/LLM/Qwen/Qwen3-VL-4B-Instruct/。已有可复用，缺失再提供，不能拿H3的32B编码器替代。自建队列动态接入写词节点；普通平台运行按钮不会自动创建这套动态图。此安装资料不冒称已完成会员网页写词或队列适配。

自建服务须管理员启动ComfyUI前设置MINIMX_ENABLE_BATCH_SERVICE=1，使用可写user/input/output、SQLite、本机/prompt。这不是RunningHub会员提交协议；没有接口转发/存储/任务生命周期支持时不要开启。平台愿意适配时先明确接口，再单独开发验收。

## 技术反馈

请提供实际commit SHA、ComfyUI分支/版本、23节点缺失项、原生缺失项、模型缺失项、前端失败URL及首段相关异常，避免用户反复提交零散文件。

标准依据：[ComfyUI Git节点约定](https://docs.comfy.org/custom-nodes/backend/manager)、[元数据](https://docs.comfy.org/registry/specifications)。这不是平台认证。来源及未明确的上游许可状态见[THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md)，平台采用前请一并核实。
