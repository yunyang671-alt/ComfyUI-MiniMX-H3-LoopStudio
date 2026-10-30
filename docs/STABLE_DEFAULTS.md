# 最终定版：Ref2V 8-step v1.0 768p

2026-10-30，按用户明确要求进行增量更新。

唯一生成配方变更：一键恢复默认设置及当前主工作流的 LoRA1 从 `minimax_h3_ref2v_turbo_4step_v0.1_comfyui_bf16.safetensors` 改为 `minimax_h3_ref2v_turbo_8step_v1.0_768p_comfyui_bf16.safetensors`；强度仍为1.0。参数仍可编辑，“固定”指确定默认配方，不是锁住控件。

其余默认值保持不变：Ref2VA INT8 ConvRot、原32B编码器、视频FP16 VAE、音频FP32 VAE、SelfLift二采6＋4、PyTorch注意力、euler/simple、视频SigmaShift10、音频SigmaShift3、1376×768、目标6秒（136帧/24fps，实际5.6667秒）、周期单图参考路线、上下文1、视角1、自动分镜、随机种子不固定、高清分块关闭。8步是LoRA名称；本次没有将SelfLift的6＋4改成8步。

依据：用户在数小时、多视频测试后反馈，配合精简提示词成功率约90%。这是用户报告，不能承诺所有图片都成功；本次部署未新增GPU推理测试。

## 精确权重

- 原作者：lightx2v/Minimax-h3-Turbo。
- 固定revision：`30f485ed874aa44c8183348ad361c5eabad318da`。
- [官方下载地址](https://huggingface.co/lightx2v/Minimax-h3-Turbo/resolve/30f485ed874aa44c8183348ad361c5eabad318da/minimax_h3_ref2v_turbo_8step_v1.0_768p_comfyui_bf16.safetensors)。
- 大小：1,956,193,000字节。
- SHA256：`6a56f41ab4229c9dd845b9501bbd475ee57e112d846cf2e819d534a1ae928c5a`。
- 放置于ComfyUI的models/loras/，或该类别对应的已配置模型目录。

RunningHub已收录同系列[模型页面](https://www.runninghub.cn/model/public/2095709823726874626)，其文件名末尾为 `_bf16_r.safetensors`，公开SHA256与本次用户实测原版不同，不能自动当作同一文件替换。平台适配另行验证；保持本次已验证原版身份。

## 增量备份范围

仅更新默认配置、主工作流LoRA、模型下载清单、相关说明和校验记录。循环/采样/SelfLift/解码Python核心逐文件保持原样；原始1.0及历史工作流保持原样；不重新复制旧模型、不重新采集历史素材/视频/队列数据库。旧4步实体保留作为历史兼容文件，不是新默认，也不删除。当前恢复模型清单仍为18项，4步项换成8步项，总字节数相同。

本地最终主工作流沿用1376×768默认参数，并保留用户云端最新已保存的精简写词规范；云端正在测试的分辨率、图片、提示词、种子和现有批次快照不被覆盖。已开始的批次继续使用创建时参数。

本版仍是自建ComfyUI队列；RunningHub会员队列适配是后续任务。不得为适配平台回改这份定版循环核心。
