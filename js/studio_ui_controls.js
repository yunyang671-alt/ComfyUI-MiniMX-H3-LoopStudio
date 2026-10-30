import { restoreStudioDefaults } from "./ui_defaults.js?v=ui-preview-2";

const widget = (node, name) => node.widgets?.find(item => item.name === name);
const set = (node, name, value) => { const target = widget(node, name); if (target) target.value = value; };

// Stable sampling/decoding needs complete groups of 17 frames at 24 fps.
export function loopFramesForSeconds(seconds) {
  const numeric = Number(seconds);
  if (!Number.isFinite(numeric) || numeric <= 0) return 136;
  return Math.max(34, Math.min(306, Math.round(numeric * 24 / 17) * 17));
}

export function applyLoopSamplingProfile(node, profile) {
  if (!widget(node, "启用周期循环")?.value) return false;
  set(node, "采样步数", profile === "极速4步" ? 4 : profile === "质量20步" ? 20 : 8);
  set(node, "自定义模型配置", true);
  return true;
}

export function installLoopControls(node, root) {
  const header = document.createElement("section");
  header.className = "wwh3-defaults-bar";
  header.style.cssText = "display:flex;gap:12px;align-items:center;flex-wrap:wrap;padding:10px 12px;border:1px solid #247b88;border-radius:10px;background:#09232e";
  const reset = document.createElement("button");
  reset.type = "button";
  reset.textContent = "↺ 一键恢复默认设置";
  reset.title = "恢复已验证配方；保留当前上传素材和提示词。模型不会随采样档位自动切换。";
  const message = document.createElement("span");
  message.style.cssText = "flex:1;min-width:180px;color:#a9dce3;font-size:11px;line-height:1.6";
  message.textContent = "二采 · 周期循环 · 1376×768 · 目标6秒 · 随机种子";
  header.append(reset, message);
  root.prepend(header);

  const duration = root.querySelector('[data-widget-name="时长秒"]');
  const hint = document.createElement("small");
  hint.className = "wwh3-loop-duration";
  hint.style.cssText = "display:block;line-height:1.5;color:#8ddfe3;font-size:10px;margin-top:5px;white-space:normal";
  hint.style.gridColumn = "1 / -1";
  (duration?.closest(".wwh3-core-grid") || duration?.parentElement)?.append(hint);

  const refresh = () => {
    const enabled = Boolean(widget(node, "启用周期循环")?.value);
    if (duration) {
      duration.disabled = false;
      duration.min = enabled ? "1.4167" : "1";
      duration.max = enabled ? "12.75" : "15";
      duration.step = "any";
      duration.title = enabled ? "输入目标秒数，自动对齐至17帧整数倍；实际时长显示在下方。" : "视频目标时长";
    }
    hint.hidden = !enabled;
    if (enabled) {
      const frames = Number(widget(node, "循环正片帧数")?.value || 136);
      const model = String(widget(node, "模型")?.value || "");
      hint.textContent = `循环实际 ${(frames / 24).toFixed(4)}秒 · ${frames}帧 / 24fps`;
      if (!model.toLowerCase().includes("ref2va")) hint.textContent += "；请选择稳定版 Ref2VA 模型";
    }
  };
  const commitDuration = () => {
    if (!widget(node, "启用周期循环")?.value) { refresh(); return; }
    const requested = Number(duration?.value);
    if (!Number.isFinite(requested) || requested <= 0) return;
    node.properties ??= {};
    node.properties.minimx_requested_loop_seconds = requested;
    set(node, "循环正片帧数", loopFramesForSeconds(requested));
    refresh();
    node.graph?.setDirtyCanvas?.(true, true);
  };
  duration?.addEventListener("input", commitDuration);
  duration?.addEventListener("change", commitDuration);
  reset.onclick = () => {
    restoreStudioDefaults(node);
    node.__wwh3?.sync();
    refresh();
    message.textContent = "已恢复默认设置；当前素材和提示词已保留。";
    node.__wwh3?.resizeForContent?.();
    node.graph?.setDirtyCanvas?.(true, true);
  };
  node.__miniMXLoopRefresh = refresh;
  node.__miniMXLoopDurationCommit = commitDuration;
  refresh();
}
