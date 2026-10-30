// ComfyUI supports array, function(widget), and object-map combo providers.
// Reference: Comfy-Org/ComfyUI_frontend src/utils/litegraphUtil.ts,
// resolveComboValues. Do not treat a platform catalog as a static array.
export function resolveWidgetChoices(widget) {
  const options = widget?.options;
  let source = options?.values ?? options?.items;
  try {
    if (typeof source === "function") source = source(widget);
    if (source && typeof source.then === "function") {
      Promise.resolve(source).catch(() => {});
      return [];
    }
    const values = Array.isArray(source) ? source
      : source && typeof source === "object" ? Object.keys(source) : [];
    return [...new Set(values.filter(value => typeof value === "string" || typeof value === "number"))];
  } catch (_) {
    // Keep the saved selection visible if a platform provider is unavailable.
    return [];
  }
}

export function isModelChoice(name) {
  return ["模型", "文本编码器", "视频VAE", "音频VAE", "二采放大模型"].includes(name)
    || /^LoRA[1-6]$/.test(name);
}

export function refreshWidgetChoices(select, widget) {
  const choices = resolveWidgetChoices(widget);
  const current = String(widget?.value ?? "");
  const names = choices.map(String);
  // Never replace a saved model with the first catalog entry during refresh.
  if (!names.includes(current)) names.unshift(current);
  const signature = JSON.stringify([names, current]);
  if (select.dataset.minimxChoicesSignature !== signature) {
    const doc = select.ownerDocument;
    select.replaceChildren(...names.map(value => {
      const option = doc.createElement("option");
      option.value = value;
      option.textContent = value || "平台未提供候选模型";
      return option;
    }));
    select.dataset.minimxChoicesSignature = signature;
  }
  select.value = current;
  select.dataset.minimxAvailableChoices = String(choices.length);
  select.title = choices.length
    ? `当前：${current}\n候选项来自本节点的实际模型列表。`
    : `当前：${current}\n平台未向此字段提供候选模型；保留当前选择。请核对原生模型选择器/字段映射。`;
  return choices.length;
}
