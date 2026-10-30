// Display the exact owned job. This module never starts or requeues work.
export function currentJob(batch) {
  const jobs=batch?.jobs||[];
  return jobs.find(j=>j.state==='RUNNING')
    ||jobs.find(j=>['SUBMITTING','QUEUED'].includes(j.state))
    ||[...jobs].reverse().find(j=>['COMPLETE','FAILED','UNKNOWN'].includes(j.state))
    ||jobs.find(j=>j.state==='WAITING')||null;
}

export function jobDisplay(batch,job=currentJob(batch)) {
  if(!job)return null;
  const text=job.job_prompt??job.effective_prompt??'';
  const auto=batch.config?.prompt_mode==='auto';
  const terminal=['COMPLETE','FAILED','UNKNOWN'].includes(job.state);
  let stage=job.live?.stage||(text?'prompt_ready':'preparing');
  let label=job.live?.label||(auto&&!text?'等待 AI 看图写词':'提示词已就绪，等待执行');
  if(job.state==='WAITING'){stage='waiting';label='等待提交';}
  if(job.state==='QUEUED'&&!job.live?.stage){stage='queued';label='已提交，等待执行';}
  if(job.state==='COMPLETE'){stage='complete';label='视频已完成，已保存到云端';}
  if(job.state==='FAILED'||job.state==='UNKNOWN'){stage='error';label=job.error||'任务异常，请查看错误信息';}
  return {job,key:batch.id+':'+job.id,text,stage,label,terminal,
    percent:terminal?null:job.live?.percent??null,
    step:['complete','saving'].includes(stage)?4:['video','prompt_ready'].includes(stage)?3:stage==='writing'?2:1};
}

export function syncJobInputs(node,view,previous={}) {
  if(!view)return previous;
  const ui=node.__wwh3;
  if(!ui)return previous;
  const changed=previous.key!==view.key;
  const write=(name,value)=>{const w=node.widgets?.find(w=>w.name===name);if(w)w.value=value;};
  if(changed){
    // Clear the preceding image and all hidden extra image slots together.
    for(const w of node.widgets||[])if(/^图片\d+$/.test(w.name))w.value='未选择';
    const picture=node.widgets?.find(w=>w.name==='图片1');
    if(picture){
      if(Array.isArray(picture.options?.values)&&!picture.options.values.includes(view.job.input_name))
        picture.options.values.push(view.job.input_name);
      picture.value=view.job.input_name;
    }
    write('随机种子',view.job.seed);ui.renderMedia?.();node.__wwh3SeedSync?.();
    const image=ui.root?.querySelector?.('.wwh3-media-item img');
    if(image){image.alt=view.job.original;image.title=view.job.relative_path||view.job.original;}
    const label=ui.root?.querySelector?.('.wwh3-media-item .wwh3-media-label');
    if(label){label.textContent='@图片1 · '+view.job.original;label.title=view.job.relative_path||view.job.original;}
  }
  if(changed||previous.text!==view.text){
    // Do not dispatch the general input/change handlers: those can switch
    // profiles or rewrite per-segment state. Only synchronize image/text/seed.
    write('提示词','');write('增强源提示词','');
    if(ui.idea)ui.idea.value='';if(ui.finalPrompt)ui.finalPrompt.value='';
    write('提示词',view.text);write('增强源提示词',view.text);
    if(ui.idea)ui.idea.value=view.text;if(ui.finalPrompt)ui.finalPrompt.value=view.text;
    if(ui.idea)ui.idea.placeholder=view.text?'':view.stage==='error'?view.label:'当前图片正在看图写词；完成后会自动填入这里。';
    node.graph?.setDirtyCanvas?.(true,true);
  }
  return {key:view.key,text:view.text};
}
