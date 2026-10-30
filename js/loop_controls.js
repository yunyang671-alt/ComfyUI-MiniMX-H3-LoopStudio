const widget = (node, name) => node.widgets?.find((w) => w.name === name);

export function applyLoopSamplingProfile(node, profile) {
  if (!widget(node, "启用周期循环")?.value) return false;
  const steps = profile === "极速4步" ? 4 : profile === "质量20步" ? 20 : 8;
  if (widget(node, "采样步数")) widget(node, "采样步数").value = steps;
  if (widget(node, "自定义模型配置")) widget(node, "自定义模型配置").value = true;
  return true;
}

export function installLoopControls(node, root) {
  const box = document.createElement("section");
  box.style.cssText = "border:1px solid #40bdb8;border-radius:10px;padding:12px;background:#09272d;color:#d5f3f1;display:grid;gap:9px";
  const title = document.createElement("strong");
  title.textContent = "周期循环 · 采样＋SelfLift放大＋周期解码";
  box.append(title);
  const controls = [];
  const fields = [
    ["启用周期循环", "checkbox"],
    ["循环条件路线", "select", ["单图参考（推荐）", "保留首帧锚定（实验）"]],
    ["循环正片帧数", "select", [34, 51, 68, 85, 102, 136, 153, 170, 187, 204, 255, 306]],
    ["循环上下文段数", "number"],
    ["循环视角", "number"],
  ];
  const info = document.createElement("div");
  info.style.cssText = "font-size:12px;line-height:1.7;white-space:pre-wrap";
  const refresh = () => {
    const referenceRoute = widget(node, "循环条件路线")?.value === "单图参考（推荐）";
    const incompatibleModel = referenceRoute && String(widget(node, "模型")?.value || "").includes("minimax_h3_fl2va");
    const routeError = incompatibleModel ? "参考循环请手动选择 Ref2VA 模型；切换采样档位不会替换你的模型。" : "";
    const upscaler = widget(node, "二采放大模型");
    const upscalerChoices = upscaler?.options?.values;
    if (upscaler?.value === "h3_upscaler_lms_v0.1.safetensors"
        && Array.isArray(upscalerChoices)
        && !upscalerChoices.includes(upscaler.value)
        && upscalerChoices.includes("minimax_h3_latent_upscaler_3d_fp16.safetensors")) {
      upscaler.value = "minimax_h3_latent_upscaler_3d_fp16.safetensors";
    }
    for (const [name, input, type] of controls) {
      const value = widget(node, name)?.value;
      if (type === "checkbox") input.checked = Boolean(value);
      else input.value = String(value ?? "");
    }
    const enabled = Boolean(widget(node, "启用周期循环")?.value);
    if (enabled && widget(node, "自定义模型配置")) {
      widget(node, "自定义模型配置").value = true;
    }
    const frames = Number(widget(node, "循环正片帧数")?.value || 204);
    const reference = widget(node, "循环条件路线")?.value === "单图参考（推荐）";
    info.textContent = enabled
      ? `周期采样已启用：正片${frames}帧，24fps，${(frames / 24).toFixed(4)}秒。\n当前模型：${widget(node, "模型")?.value || "未选择"}\n当前加速 LoRA：${widget(node, "LoRA1")?.value || "无"}\n${reference ? "参考路线不固定首帧，也不保证保持原图构图。" : "首帧锚定为实验路线，循环与构图效果尚需验证。"}\n${widget(node, "SelfLift二采")?.value ? "SelfLift二采：6＋4步；循环二采请关闭高清分块。" : "SelfLift二采已关闭。"}\n时长在上方帧数选项调整；画面比例和分辨率可单独修改。先固定小尺寸、模型和种子做对照。${routeError ? `\n设置错误：${routeError}` : ""}`
      : "周期循环已关闭：使用原版生成路径。所有模式及功能保留；时长恢复由原“时长（秒）”控制。";
    for (const input of root.querySelectorAll('[data-widget-name="时长秒"]')) {
      input.disabled = enabled;
      input.title = enabled ? "周期模式请在周期正片帧数中选择时长" : "";
    }
  };
  for (const [name, type, options] of fields) {
    const row = document.createElement("label");
    row.style.cssText = "display:flex;justify-content:space-between;align-items:center;gap:12px;font-size:13px";
    row.append(document.createTextNode(name));
    const input = document.createElement(type === "select" ? "select" : "input");
    input.dataset.widgetName = name;
    if (type === "select") {
      for (const value of options) {
        const option = document.createElement("option");
        option.value = String(value);
        option.textContent = name === "循环正片帧数" ? `${value}帧 · ${(Number(value) / 24).toFixed(4)}秒` : String(value);
        input.append(option);
      }
    } else input.type = type;
    if (type === "number") {
      input.min = "1"; input.max = name === "循环视角" ? "2" : "3"; input.step = "1";
    }
    input.style.cssText = "background:#071c24;color:#d5f3f1;border:1px solid #397c83;border-radius:5px;padding:4px;max-width:65%";
    input.onchange = () => {
      const item = widget(node, name);
      if (!item) return;
      item.value = type === "checkbox" ? input.checked
        : name === "循环条件路线" ? input.value : Number(input.value);
      refresh();
      node.__wwh3?.sync?.();
      node.__wwh3?.resizeForContent?.();
      node.graph?.setDirtyCanvas?.(true, true);
    };
    controls.push([name, input, type]);
    row.append(input);
    box.append(row);
  }
  box.append(info);
  root.prepend(box);
  node.__miniMXLoopRefresh = refresh;
  refresh();
  // Import/configure may update serialized fields after onNodeCreated.
  requestAnimationFrame(refresh);
  setTimeout(refresh, 100);
}
