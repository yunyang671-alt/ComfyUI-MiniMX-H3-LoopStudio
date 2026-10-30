import { app } from '../../../scripts/app.js';
import { api } from '../../../scripts/api.js';
import { matchPrompts, parsePrompts, decodePromptText } from './batch_prompt_parser.js';
import { jobDisplay, syncJobInputs } from './batch_display_visual_v2.js';
import { LocalVideoSaver } from './batch_local_save_v1.js';

const BASE='/minimx/batch/v1', ACCEPT=/\.(png|jpe?g|webp|bmp)$/i;
const collator=new Intl.Collator('zh-CN',{numeric:true,sensitivity:'base'});
const DEFAULT_RULES='固定镜头，保持原图构图、主体位置与姿势，用于无缝循环动态壁纸。\n根据每张图实际场景挑选合理的微动：有头发和衣物时轻微随风飘动，有烟雾、水面、树叶等元素时自然缓慢运动；不要凭空添加。\n人物可以自然眨眼和轻微呼吸，手部和身体姿势保持稳定。无人物场景不要添加人物。\n所有动态同时持续，幅度克制、符合物理规律，衔接自然，无突然变化。只输出适合当前图片的一段中文视频提示词。';
const labels={WAITING:'待提交',SUBMITTING:'核对提交',QUEUED:'已排队',RUNNING:'生成中',COMPLETE:'已完成',FAILED:'失败',UNKNOWN:'需核对',CANCELED:'已取消',SKIPPED:'已跳过',PAUSED:'已暂停',COMPLETED:'全部结束'};
const el=(tag,text,style='')=>{const e=document.createElement(tag);if(text)e.textContent=text;if(style)e.style.cssText=style;return e;};
const request=async(path,data)=>{
  const r=await api.fetchApi(BASE+path,data===undefined?{}:{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});
  let body;try{body=await r.json();}catch{throw new Error('批量服务尚未连接，请稍后刷新。');}
  if(!r.ok)throw new Error(body.error||`请求失败：${r.status}`);return body;
};
function localDb(){return new Promise((resolve,reject)=>{const r=indexedDB.open('minimx-batch-local-save-v1',1);r.onupgradeneeded=()=>r.result.createObjectStore('records');r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(r.error);});}
async function localGet(key){const db=await localDb();try{return await new Promise((resolve,reject)=>{const r=db.transaction('records').objectStore('records').get(key);r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(r.error);});}finally{db.close();}}
async function localSet(key,value){const db=await localDb();try{await new Promise((resolve,reject)=>{const t=db.transaction('records','readwrite');t.objectStore('records').put(value,key);t.oncomplete=resolve;t.onerror=()=>reject(t.error);});}finally{db.close();}}

export function installBatchPanel(node){
  if(!node.properties?.minimx_batch_ui||!node.__wwh3?.root||node.__miniMXBatchPanel?.version>=8)return;
  // Managed platforms install the generation nodes without a local queue.
  // Probe once before creating controls, timers or browser storage handles.
  if(!node.__miniMXBatchFeatures){
    if(node.__miniMXBatchFeaturePending)return;
    node.__miniMXBatchFeaturePending=true;
    (async()=>{
      let enabled=false;
      try{
        const response=await api.fetchApi('/minimxa-loop/package-features');
        const features=response.ok?await response.json():null;
        enabled=features?.batch_enabled===true;
      }catch{}
      node.__miniMXBatchFeatures={enabled};
      node.__miniMXBatchFeaturePending=false;
      if(enabled){installBatchPanel(node);return;}
      if(!node.__wwh3?.root||node.__miniMXBatchUnavailable)return;
      const notice=el('div','本环境未启用自建批量服务；可使用平台运行按钮生成单张周期视频。RunningHub会员队列尚未适配。','padding:10px;color:#a9dce3;font-size:12px');
      node.__miniMXBatchUnavailable=notice;
      node.__wwh3.root.prepend(notice);
      node.__wwh3.resizeForContent?.();
    })();
    return;
  }
  if(!node.__miniMXBatchFeatures.enabled)return;
  node.__miniMXBatchPanel?.dispose();node.__miniMXBatchPanel?.panel.remove();
  const root=node.__wwh3.root, panel=el('section',null,'padding:13px;border:1px solid #218d9d;border-radius:9px;background:#071e29;display:flex;flex-direction:column;gap:9px;color:#bfe6e9;font-size:12px');
  panel.className='minimx-batch-panel';
  panel.append(el('strong','批量自动排队','font-size:14px;color:#8de9df'));
  const status=el('div','正在连接队列服务…','color:#7ae0d5;line-height:1.6');
  const liveCard=el('div',null,'padding:10px;border:1px solid #287080;border-radius:7px;background:#08242d;line-height:1.7');
  liveCard.className='minimx-batch-current';liveCard.setAttribute('aria-live','polite');
  const liveName=el('strong','尚未开始处理图片'),livePhase=el('div','选图并开始后，当前图和提示词会同步到下方。');
  const liveSteps=el('div',null,'display:flex;gap:8px;flex-wrap:wrap;font-size:11px');
  const steps=['参考图','看图写词 / 匹配提示词','生成周期视频','合成保存'];
  const stepItems=steps.map((s,i)=>{const item=el('span',`${i+1}. ${s}`);liveSteps.append(item);return item;});
  const liveProgress=el('progress');liveProgress.max=100;liveProgress.style.cssText='width:100%;height:7px;accent-color:#26c9b8';liveProgress.hidden=true;
  liveCard.append(liveName,livePhase,liveSteps,liveProgress);
  const ideaBadge=el('div',null,'font-size:11px;color:#88e1d7;padding:4px 0;line-height:1.6');
  ideaBadge.className='minimx-batch-idea-status';root.querySelector('.wwh3-idea')?.before(ideaBadge);
  const video=el('video');video.controls=true;video.preload='metadata';video.hidden=true;
  video.style.cssText='width:100%;max-height:210px;background:#020c15;border-radius:6px';
  const videoLabel=el('div',null,'font-size:11px;color:#91d5d9');
  const errors=el('div',null,'color:#ffbe88;white-space:pre-wrap;line-height:1.5');
  const tools=el('div',null,'display:flex;gap:7px;flex-wrap:wrap');
  const button=(text,action)=>{const e=el('button',text);e.type='button';e.onclick=()=>Promise.resolve(action()).catch(err=>{errors.textContent=err.message||String(err);});return e;};
  const filesInput=el('input');filesInput.type='file';filesInput.multiple=true;filesInput.accept='image/png,image/jpeg,image/webp,image/bmp';filesInput.hidden=true;
  const folderInput=el('input');folderInput.type='file';folderInput.multiple=true;folderInput.webkitdirectory=true;folderInput.hidden=true;
  const promptInput=el('input');promptInput.type='file';promptInput.accept='.txt,text/plain';promptInput.setAttribute('aria-label','上传逐图提示词TXT');promptInput.style.cssText='width:250px;max-width:100%';
  const promptRow=el('label',null,'display:flex;flex-direction:row;align-items:center;gap:9px;flex-wrap:wrap');promptRow.append(el('span','逐图提示词 TXT'),promptInput);
  const promptInfo=el('div','未上传TXT时使用下方通用提示词；上传后按文件名逐图匹配，缺项会停止提交。','font-size:11px;color:#95c4cd;line-height:1.6');
  const modeRow=el('label',null,'display:flex;flex-direction:row;align-items:center;gap:9px');
  const mode=el('select');mode.setAttribute('aria-label','提示词方式');
  for(const [value,label] of [['auto','自动看图写提示词'],['txt','上传逐图提示词TXT'],['common','使用下方通用提示词']]){const opt=el('option',label);opt.value=value;mode.append(opt);}
  mode.value=node.properties.minimx_batch_prompt_mode||'auto';modeRow.append(el('span','提示词方式'),mode);
  const rules=el('textarea');rules.setAttribute('aria-label','提示词写作规范');rules.placeholder='用大白话说明哪些内容可以动，哪些不能动，提示词应该怎么写。';rules.value=node.properties.minimx_batch_prompt_rules||DEFAULT_RULES;rules.style.cssText='width:100%;min-height:105px;box-sizing:border-box;padding:8px;line-height:1.6;resize:vertical;background:#061923;color:#d5eef0;border:1px solid #307281;border-radius:6px';
  const selection=el('div','未选择图片。可选择文件夹、批量选图，或拖入图片。','line-height:1.6');
  const draftInfo=el('div',null,'font-size:11px;color:#a1cdd8;line-height:1.6');
  const draftErrors=el('div',null,'font-size:11px;color:#ffbe88;white-space:pre-wrap');
  const draftTable=el('div',null,'max-height:100px;overflow:auto;font-size:11px;line-height:1.6');draftTable.hidden=true;
  const drop=el('div','拖入图片 / 文件夹（最多1000张）','padding:12px;border:1px dashed #2c8396;border-radius:7px;text-align:center;color:#8db9c4');
  const table=el('div',null,'max-height:160px;overflow:auto;border-top:1px solid #245061;line-height:1.6');
  const saveRow=el('div',null,'display:flex;align-items:center;gap:9px;flex-wrap:wrap;padding:11px;border:1px solid #397a90;border-radius:8px;background:#0c2834');
  saveRow.className='minimx-local-save';
  const saveButton=button('设置本地保存文件夹',async()=>{
    try{
      const changed=await saver.select(current&&!pending?current.id:null);
      if(changed)await saveCompleted();
    }catch(error){errors.textContent=error.message||String(error);}
  });
  saveButton.style.cssText='padding:8px 12px;background:#15465c;border:1px solid #66bbd6;border-radius:6px;color:#d0f3ff;font-weight:700;cursor:pointer';
  const saveBadge=el('strong','❗未设置','color:#ff6b7c;white-space:nowrap;font-size:13px');
  saveBadge.className='minimx-save-badge';saveBadge.setAttribute('role','status');
  const savePath=el('span','请选择保存视频的文件夹。','font-size:11px;color:#a5ced9;overflow-wrap:anywhere');
  savePath.className='minimx-save-path';
  const saveInfo=el('div','视频保留在云端；本地自动保存需保持网页打开。','font-size:11px;color:#92bdc9;line-height:1.6;flex-basis:100%');
  saveRow.append(saveButton,saveBadge,savePath,saveInfo);
  let files=[],promptText=null,promptName='',current=null,pending=false,busy=false,disposed=false,pollBusy=false;
  let serviceReady=false,pauseRequested=false,cpuPreview=false;
  let displayed={},videoKey='';
  let clearing=Boolean(node.properties.minimx_batch_clearing),viewEpoch=0;
  let settingsDirty=false;
  const resize=()=>node.__wwh3.resizeForContent?.();
  const saver=new LocalVideoSaver({get:localGet,set:localSet,
    choose:()=>{
      if(!window.showDirectoryPicker)throw new Error('此浏览器不支持选择本地保存目录，请使用Chrome/Edge通过HTTPS打开。');
      return window.showDirectoryPicker({mode:'readwrite'});
    },
    fetchVideo:(batchId,jobId)=>api.fetchApi(`${BASE}/video/${batchId}/${jobId}`),
    onChange:state=>{
      saveButton.textContent=state.choosing?'正在选择文件夹…':state.configured?'更改本地保存文件夹':'设置本地保存文件夹';
      saveButton.disabled=state.choosing;
      saveBadge.textContent=state.configured?'✓ 已设置':'❗未设置';
      saveBadge.style.color=state.configured?'#9edff4':'#ff6b7c';
      savePath.textContent=state.configured?`将会保存到：${state.name}（含子目录）`:state.name?`已记住：${state.name}，请重新选择并授权。`:'请选择保存视频的文件夹。';
      saveInfo.textContent=state.error|| (state.lastSaved?`最新已保存：${state.lastSaved} · 请保持网页打开。`:'本地自动保存需保持网页打开；可随时更换目录，旧目录文件保留。');
      saveInfo.style.color=state.error?'#ffad9c':'#92bdc9';
      resize();
    },
  });
  function preview(){
    let matched=null;
    try{if(mode.value==='txt'&&files.length)matched=matchPrompts(promptText??'',files.map(x=>({name:x.file.name,relative_path:x.relative})));draftErrors.textContent='';}
    catch(e){draftErrors.textContent=e.message;}
    selection.textContent=pending?`待开始的新图片：${files.length} 张${matched?' · 提示词已全部匹配':''}；按文件名自然排序。`:current?`当前队列 ${current.total} 张图片；下方实时显示当前任务。`:`已选择 ${files.length} 张图片；按文件名自然排序。`;
    draftInfo.textContent=settingsDirty&&current?'写作设置已修改，将用于下一组新图片；当前队列继续使用启动时保存的规范，实时显示不受影响。':'';
    draftTable.hidden=!pending;
    draftTable.replaceChildren(...(pending?files:[]).map((x,i)=>{
      const row=el('div',`${x.relative} → ${x.file.name.replace(/\.[^.]+$/,'')}.mp4${matched?' · 已匹配提示词':''}`,'padding:4px 2px;border-bottom:1px solid #123641');
      if(matched)row.title=matched[i];return row;
    }));resize();
  }
  function updatePromptMode(){
    node.properties.minimx_batch_prompt_mode=mode.value;
    promptRow.style.display=mode.value==='txt'?'flex':'none';rules.style.display=mode.value==='auto'?'block':'none';
    promptInfo.textContent=mode.value==='auto'?'这里填写 AI 写作规范。每张图分别看图写词，写好后自动替换下方“原始创意”，再生成视频；旧图与旧词会同步清空替换。':mode.value==='txt'?'选择TXT，按“1.jpg:提示词”匹配；可跨行，缺项会停止提交。':'本组所有图片使用工作台下方同一段通用提示词。';
    preview();node.graph?.setDirtyCanvas?.(true,true);
  }
  mode.onchange=()=>{settingsDirty=true;updatePromptMode();};
  rules.oninput=()=>{node.properties.minimx_batch_prompt_rules=rules.value;settingsDirty=true;preview();node.graph?.setDirtyCanvas?.(true,true);};
  function setFiles(items){
    if(busy)throw new Error('正在上传，请等待完成。');
    const selected=items.filter(x=>ACCEPT.test(x.file.name)).sort((a,b)=>collator.compare(a.relative,b.relative));
    if(selected.length>1000)throw new Error('最多1000张图片，请拆分文件夹后导入。');
    files=selected;pending=true;saver.reset();
    if(!current){liveName.textContent='已选择图片，等待开始';livePhase.textContent='开始后显示当前任务图词和进度。';}
    preview();
  }
  async function walkDirectory(handle,prefix=''){
    const result=[];
    for await(const [name,child] of handle.entries()){
      if(child.kind==='directory')result.push(...await walkDirectory(child,prefix+name+'/'));
      else if(ACCEPT.test(name))result.push({file:await child.getFile(),relative:prefix+name});
      if(result.length>1000)throw new Error('最多1000张图片，请拆分文件夹后导入。');
    }return result;
  }
  tools.append(button('选择图片文件夹',async()=>{
    if(busy)return;
    if(!window.showDirectoryPicker){folderInput.click();return;}
    try{const handle=await window.showDirectoryPicker({mode:'readwrite'});setFiles(await walkDirectory(handle));await saver.use(handle);}
    catch(e){if(e.name!=='AbortError')throw e;}
  }),button('批量选图',()=>{if(!busy)filesInput.click();}));
  filesInput.onchange=()=>{try{setFiles([...filesInput.files].map(file=>({file,relative:file.name})));}catch(e){errors.textContent=e.message;}};
  folderInput.onchange=()=>{try{setFiles([...folderInput.files].map(file=>({file,relative:file.webkitRelativePath.split('/').slice(1).join('/')||file.name})));}catch(e){errors.textContent=e.message;}};
  promptInput.onchange=async()=>{
    if(busy)return;
    const file=promptInput.files[0];
    // Do not fall back to an old TXT when a replacement is invalid.
    promptText=null;promptName='';
    settingsDirty=true;
    if(!file){promptInfo.textContent='未上传TXT，请选择正确文件。';preview();return;}
    try{
      if(file.size>4*1024*1024)throw new Error('TXT不能超过4MB');
      promptText=decodePromptText(await file.arrayBuffer());const parsed=parsePrompts(promptText);promptName=file.name;
      promptInfo.textContent=`${file.name} · ${parsed.size} 段提示词；文件名后至下个文件名之前均属于该图，可跨行。`;
      preview();
    }catch(e){promptText='';errors.textContent=e.message;promptInfo.textContent='TXT未通过检查，请重新选择正确文件。';}
  };
  async function readDropEntry(entry,prefix='',includeName=true){
    if(entry.isFile){const file=await new Promise((res,rej)=>entry.file(res,rej));return [{file,relative:prefix+file.name}];}
    if(!entry.isDirectory)return [];
    const reader=entry.createReader(),all=[];
    for(;;){const entries=await new Promise((res,rej)=>reader.readEntries(res,rej));if(!entries.length)break;for(const child of entries)all.push(...await readDropEntry(child,prefix+(includeName?entry.name+'/':'')));if(all.length>1000)throw new Error('图片超过1000张');}return all;
  }
  drop.ondragover=e=>{e.preventDefault();e.stopPropagation();};
  drop.ondrop=async e=>{
    e.preventDefault();e.stopPropagation();if(busy)return;
    try{const entries=[...e.dataTransfer.items].map(x=>x.webkitGetAsEntry?.()).filter(Boolean),fallback=[...e.dataTransfer.files];
      if(entries.length){const all=[];for(const entry of entries)all.push(...await readDropEntry(entry,'',entries.length>1));setFiles(all);}
      else setFiles(fallback.map(file=>({file,relative:file.name})));
    }catch(e){errors.textContent=e.message;}
  };
  function showBatch(data){
    if(disposed)return;
    current=data;node.properties.minimx_batch_id=data.id;
    if(!pending)selection.textContent=`当前队列 ${data.total} 张图片；下方实时显示当前任务。`;
    const c=data.counts;
    const active=c.SUBMITTING+c.QUEUED+c.RUNNING;
    if(clearing&&!active){
      saveCompleted();
      resetClearedView();return;
    }
    status.textContent=`${cpuPreview?'CPU预览 · ':''}${labels[data.state]||data.state} · 完成 ${c.COMPLETE}/${data.total} · 在途 ${c.SUBMITTING+c.QUEUED+c.RUNNING} · 待提交 ${c.WAITING} · 失败 ${c.FAILED} · 需核对 ${c.UNKNOWN}`;
    if(clearing)status.textContent=`待办已清空 · ${active} 条已提交任务继续完成；完成后列表自动清空。`;
    {
      const view=jobDisplay(data);
      let syncError='';
      if(view){
        try{displayed=syncJobInputs(node,view,displayed);}catch(error){syncError='当前图词回填失败，将自动重试：'+error.message;}
        liveName.textContent=`当前图片 ${view.job.ordinal+1}/${data.total}：${view.job.relative_path}`;
        livePhase.textContent=view.label+(view.percent===null?'':` · 当前阶段 ${Math.round(view.percent)}%`);
        livePhase.style.color=view.stage==='error'?'#ffbe88':'#bfe6e9';
        ideaBadge.textContent=`${view.job.original} · ${view.text?'已同步本图提示词':view.label}`;
        stepItems.forEach((item,i)=>{item.style.color=i<view.step?'#82e8ce':'#6f929a';item.style.fontWeight=i===view.step-1?'700':'400';});
        liveProgress.hidden=view.terminal||['waiting','queued'].includes(view.stage);
        if(view.percent===null)liveProgress.removeAttribute('value');else liveProgress.value=view.percent;
      }
      const last=!clearing&&[...data.jobs].reverse().find(j=>j.state==='COMPLETE'&&j.outputs?.length);
      if(last&&last.id!==videoKey){
        videoKey=last.id;const out=last.outputs[0];
        const params=new URLSearchParams({filename:out.filename,subfolder:out.subfolder||'',type:'output'});
        video.src=api.apiURL('/view?'+params);video.hidden=false;
        videoLabel.textContent='最近完成：'+last.stem+'.mp4（与上方当前任务分别标注，避免混淆）';
        resize();
      }
      errors.textContent=[syncError,data.error,...data.jobs.filter(x=>x.error).slice(0,3).map(x=>`${x.original}：${x.error}`)].filter(Boolean).join('\n');
      const shownJobs=clearing?data.jobs.filter(j=>['SUBMITTING','QUEUED','RUNNING'].includes(j.state)):data.jobs;
      table.replaceChildren(...shownJobs.map(job=>{
        const row=el('div',null,'display:flex;gap:7px;padding:4px 2px;border-bottom:1px solid #123641');
        row.append(el('span',`${job.relative_path} → ${job.stem.split('/').at(-1)}.mp4`,'flex:1;overflow-wrap:anywhere'),el('span',job.state==='RUNNING'?(job.live?.label||'执行中'):labels[job.state]||job.state));
        if(view?.job.id===job.id)row.style.background='#103d46';
        row.title=job.job_prompt||job.effective_prompt||(data.config?.prompt_mode==='auto'?'本图尚未取得新提示词':'本图提示词尚未就绪');
        if(job.state==='COMPLETE'){const a=el('a','下载');a.href=api.apiURL(`${BASE}/video/${data.id}/${job.id}`);a.download=job.outputs[0]?.filename||'';a.style.color='#8eefff';row.append(a);}return row;
      }));
    }
    if(!pending)saveCompleted();
  }
  async function createBatch(){
    if(!files.length)throw new Error('请先选择图片。');
    const selected=[...files],selectedMode=mode.value,text=selectedMode==='txt'?promptText:null,writingRules=rules.value.trim();
    if(selectedMode==='txt')matchPrompts(text??'',selected.map(x=>({name:x.file.name,relative_path:x.relative})));
    if(selectedMode==='auto'&&!writingRules)throw new Error('请填写提示词写作规范。');
    node.__wwh3.syncModeWidgets?.();node.__wwh3.syncStoryboardCount?.();
    const snapshot=structuredClone(await app.graphToPrompt()),sid=String(node.id);
    const savers=Object.entries(snapshot.output).filter(([id,n])=>n.class_type==='VHS_VideoCombine'&&JSON.stringify(n.inputs.images)===JSON.stringify([sid,0]));
    if(savers.length!==1)throw new Error('需要一个Video Combine直接连接当前创作台图像输出。');
    if(selectedMode==='common'&&!snapshot.output[sid]?.inputs?.['提示词']?.trim())throw new Error('请填写下方通用提示词。');
    const folder='minimx_batches/'+crypto.randomUUID(),uploaded=[];
    for(let i=0;i<selected.length;i++){
      const item=selected[i];status.textContent=`上传 ${i+1}/${selected.length}：${item.relative}`;
      const form=new FormData(),name=crypto.randomUUID()+'_'+item.file.name.replace(/[\\/<>:"|?*]/g,'_').replace(/\.{2,}/g,'_');
      form.append('image',item.file,name);form.append('type','input');form.append('subfolder',folder);form.append('overwrite','false');
      const r=await api.fetchApi('/upload/image',{method:'POST',body:form});if(!r.ok)throw new Error(`上传失败：${item.relative}，HTTP ${r.status}`);
      const data=await r.json();uploaded.push({name:item.file.name,relative_path:item.relative,filename:(data.subfolder?data.subfolder+'/':'')+data.name});
    }
    const data=await request('/create',{prompt:snapshot.output,workflow:snapshot.workflow,studio_id:sid,saver_id:savers[0][0],images:uploaded,prompt_mode:selectedMode,prompt_rules:writingRules,prompt_text:text,concurrency:1,fixed_seed:node.properties.liao_fixed_seed===true,client_id:api.clientId||'',label:`${selected.length}张 · ${selected[0].file.name} · ${selectedMode}`});
    viewEpoch++;current=data;pending=false;settingsDirty=false;clearing=false;node.properties.minimx_batch_empty=false;delete node.properties.minimx_batch_clearing;node.properties.minimx_batch_id=data.id;node.graph?.setDirtyCanvas?.(true,true);
    preview();
    await saver.bind(data.id);
    showBatch(data);
  }
  async function startQueue(){
    if(busy)return;
    if(!serviceReady)throw new Error('请等待批量服务连接后再开始。');
    busy=true;pauseRequested=false;start.disabled=true;clear.disabled=true;promptInput.disabled=true;mode.disabled=true;rules.disabled=true;errors.textContent='';
    try{
      const info=await request('/info');if(!info.can_run)throw new Error('当前无显卡/CPU模式，请用GPU启动ComfyUI后再开始。');
      if(pending||!current){
        if(mode.value==='auto'&&!info.autoprompt?.ready)throw new Error('自动写词节点或生成权重尚未就绪，请等待部署完成。');
        const running=(await request('/list')).find(x=>x.state==='RUNNING');
        if(running)throw new Error('已有队列正在提交，请先暂停提交，再开始新选的图片。');
        await createBatch();
        const checked=await request(`/validate/${current.id}`,{});
        if(!checked.valid)throw new Error('参数/节点检查未通过，尚未提交任务。请更正后重新选图：'+JSON.stringify(checked.node_errors||checked.error));
      }
      if(pauseRequested){showBatch(await request(`/action/${current.id}/pause`,{}));return;}
      if(current.state==='CANCELED')throw new Error('这组任务已取消，请重新选择图片后开始。');
      if(current.state==='COMPLETED'){status.textContent='这组图片已经处理结束；请选择新图片后开始。';return;}
      showBatch(await request(`/action/${current.id}/start`,{}));
      if(pauseRequested)showBatch(await request(`/action/${current.id}/pause`,{}));
    }finally{busy=false;start.disabled=false;clear.disabled=false;promptInput.disabled=false;mode.disabled=false;rules.disabled=false;if(current&&!pending)showBatch(current);}
  }
  const start=button('开始 / 继续队列',startQueue);start.style.cssText='background:#087c81;color:white;border:1px solid #38c2b5;padding:7px 12px';
  const pause=button('暂停提交',async()=>{
    pauseRequested=true;
    if(current)showBatch(await request(`/action/${current.id}/pause`,{}));
    else status.textContent=busy?'已请求暂停；图片上传完后保留待执行，不会开始提交。':'当前没有正在提交的队列。';
  });
  function resetClearedView(){
    current=null;clearing=false;files=[];pending=false;settingsDirty=false;displayed={};draftInfo.textContent='';draftErrors.textContent='';draftTable.replaceChildren();draftTable.hidden=true;
    delete node.properties.minimx_batch_id;delete node.properties.minimx_batch_clearing;
    node.properties.minimx_batch_empty=true;
    selection.textContent='队列已清空；可重新选择图片。';table.replaceChildren();errors.textContent='';
    status.textContent=cpuPreview?'CPU预览 · 队列为空':'队列为空';
    liveName.textContent='队列已清空';livePhase.textContent='已完成视频保留在云端原目录，不会删除。';
    livePhase.style.color='#bfe6e9';liveProgress.hidden=true;ideaBadge.textContent='';
    stepItems.forEach(item=>{item.style.color='#6f929a';item.style.fontWeight='400';});
    video.pause();video.removeAttribute('src');video.hidden=true;videoLabel.textContent='';videoKey='';
    node.graph?.setDirtyCanvas?.(true,true);resize();
  }
  const clear=button('清空队列',async()=>{
    if(busy)return;
    busy=true;viewEpoch++;clear.disabled=true;start.disabled=true;pause.disabled=true;
    try{
      // Cancel only this batch's not-yet-submitted work. Never interrupt a
      // native running prompt, delete completed videos, or touch other batches.
      const result=current?await request(`/action/${current.id}/cancel`,{}):null;
      files=[];pending=false;promptText=null;promptName='';promptInput.value='';filesInput.value='';folderInput.value='';
      updatePromptMode();
      if(result){clearing=true;node.properties.minimx_batch_clearing=result.id;node.properties.minimx_batch_empty=false;showBatch(result);}
      else resetClearedView();
      node.graph?.setDirtyCanvas?.(true,true);
    }finally{busy=false;clear.disabled=false;start.disabled=false;pause.disabled=false;if(current&&!pending)showBatch(current);}
  });
  clear.title='清空未提交的图片；已提交任务继续完成，已完成视频保留。';
  clear.disabled=true; // Load the saved queue before allowing it to be cleared.
  tools.append(start,pause,clear);
  panel.append(tools,saveRow,modeRow,rules,promptRow,promptInfo,selection,draftInfo,draftErrors,drop,draftTable,status,liveCard,errors,table,videoLabel,video,filesInput,folderInput);
  panel.append(el('div','暂停只停止补交；清空取消未提交任务，已提交任务继续完成，视频保留。关网页云端继续生成，本地保存需网页打开。','font-size:11px;color:#85abb9;line-height:1.6'));
  root.querySelector('.wwh3-defaults-bar')?.after(panel);
  async function saveCompleted(){
    await saver.save(current,()=>!pending);
  }
  const beforeLeave=e=>{if(busy){e.preventDefault();e.returnValue='图片尚未上传完';}};window.addEventListener('beforeunload',beforeLeave);
  async function poll(){if(pollBusy||disposed)return;pollBusy=true;try{if(current){const id=current.id,epoch=viewEpoch;const data=await request('/status/'+id);if(!disposed&&epoch===viewEpoch&&current?.id===id)showBatch(data);}}catch(e){errors.textContent='队列连接中断，恢复后自动查询：'+e.message;}finally{pollBusy=false;}}
  const timer=setInterval(poll,3000);
  const onVisual=event=>{
    const update=event.detail;
    if(disposed||!current||update?.batch_id!==current.id)return;
    const job=current.jobs.find(j=>j.id===update.job_id&&j.prompt_id===update.prompt_id);
    if(!job)return void poll();
    job.live=update.live;if(update.job_prompt!=null)job.job_prompt=update.job_prompt;
    // A native event may precede the worker's next queue poll.
    if(!['COMPLETE','FAILED','UNKNOWN','CANCELED','SKIPPED'].includes(job.state))job.state='RUNNING';
    showBatch(current);
  };
  api.addEventListener('minimx_batch_visual',onVisual);
  node.__miniMXBatchPanel={version:8,panel,dispose(){disposed=true;saver.dispose();clearInterval(timer);window.removeEventListener('beforeunload',beforeLeave);api.removeEventListener('minimx_batch_visual',onVisual);ideaBadge.remove();}};
  (async()=>{
    if(/(^|\.)runninghub\.(cn|ai)$/i.test(location.hostname)){start.disabled=true;status.textContent='此版用于自建ComfyUI，尚未适配RunningHub会员网页。';return;}
    const info=await request('/info');
    if(info.version!=='1.2-auto-prompts')throw new Error('请重启ComfyUI以加载逐图提示词服务。');
    if(info.visual_version!==1)throw new Error('可视化服务尚未加载，请重启 ComfyUI 后刷新。');
    cpuPreview=!info.can_run;status.textContent=info.can_run?'GPU已就绪：选图片、设置写词规范，然后开始队列。':'当前为CPU预览；开启GPU并启动ComfyUI后再开始。';
    const list=await request('/list');
    const saved=node.properties.minimx_batch_clearing?list.find(x=>x.id===node.properties.minimx_batch_clearing):node.properties.minimx_batch_empty?null:list.find(x=>x.id===node.properties.minimx_batch_id)||list.find(x=>x.state!=='CANCELED');
    if(saved){const epoch=viewEpoch;const restored=await request('/status/'+saved.id);if(disposed||epoch!==viewEpoch)return;showBatch(restored);
      if(!pending){await saver.restore(saved.id);await poll();}
    }
    serviceReady=true;clear.disabled=false;
  })().catch(e=>{errors.textContent=e.message;});
  updatePromptMode();
  requestAnimationFrame(resize);
}
app.registerExtension({
  name:'minimxa.loop.h3.batch.queue.visual.v4',
  rh:{type:'nodes',nodes:['MiniMXH3LoopStudio']},
  async beforeRegisterNodeDef(nodeType,nodeData){
    if(nodeData.name!=='MiniMXH3LoopStudio')return;
    const configured=nodeType.prototype.onConfigure;
    nodeType.prototype.onConfigure=function(...args){const result=configured?.apply(this,args);setTimeout(()=>installBatchPanel(this),380);return result;};
    const removed=nodeType.prototype.onRemoved;
    nodeType.prototype.onRemoved=function(...args){this.__miniMXBatchPanel?.dispose();return removed?.apply(this,args);};
  },
});
