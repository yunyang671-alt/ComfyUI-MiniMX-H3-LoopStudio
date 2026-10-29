const widget = (node, name) => node.widgets?.find((w) => w.name === name);

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
    ["循环正片帧数", "select", [102, 136, 153, 170, 187, 204, 255, 306]],
    ["循环上下文段数", "number"],
    ["循环视角", "number"],
  ];
  const info = document.createElement("div");
  info.style.cssText = "font-size:12px;line-height:1.7;white-space:pre-wrap";
  const refresh = () => {
    for (const [name, input, type] of controls) {
      const value = widget(node, name)?.value;
      if (type === "checkbox") input.checked = Boolean(value);
      else input.value = String(value ?? "");
    }
    const enabled = Boolean(widget(node, "启用周期循环")?.value);
    const frames = Number(widget(node, "循环正片帧数")?.value || 204);
    info.textContent = enabled
      ? `已启用：内部length=${frames + 5} → 正片${frames}帧，24fps，${(frames / 24).toFixed(4)}秒。\n循环时长由上方“循环正片帧数”决定。参考路线仍只使用图片1，但不将其固定为输出首帧。\n保留当前模型、六LoRA和SelfLift 6＋4步。上下文建议1，视角建议1。高清分块请保持关闭。\n上传图片1，并将原提示词改为适合壁纸的持续运动；本包保留了原提示词。云端效果由你手动测试。`
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
