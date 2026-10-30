// Browser-only directory saving, independent of queue execution and models.
export class LocalVideoSaver {
  constructor({get,set,choose,fetchVideo,onChange=()=>{},uuid=()=>crypto.randomUUID()}) {
    Object.assign(this,{get,set,choose,fetchVideo,onChange,uuid});
    this.target=null;this.enabled=false;this.choosing=false;this.saving=false;
    this.epoch=0;this.userSelected=false;this.disposed=false;this.error='';this.lastSaved='';
  }
  state(){return {configured:Boolean(this.target&&this.enabled),name:this.target?.handle.name||'',
    choosing:this.choosing,saving:this.saving,error:this.error,lastSaved:this.lastSaved};}
  emit(){if(!this.disposed)this.onChange(this.state());}
  reset(){this.epoch++;this.userSelected=true;this.target=null;this.enabled=false;this.error='';this.lastSaved='';this.emit();}
  dispose(){this.disposed=true;this.epoch++;}
  async bind(batchId){if(this.target)await this.set('save-batch:'+batchId,this.target);}
  async restore(batchId){
    if(this.userSelected||this.disposed)return;
    const epoch=this.epoch,target=await this.get('save-batch:'+batchId);
    if(!target||this.userSelected||this.disposed||epoch!==this.epoch)return;
    const allowed=await target.handle.queryPermission({mode:'readwrite'});
    if(this.userSelected||this.disposed||epoch!==this.epoch)return;
    this.target=target;this.enabled=allowed==='granted';
    this.error=this.enabled?'':'目录写入权限未授权，请重新选择文件夹并授权。';this.emit();
  }
  async use(handle,batchId=null){
    const epoch=++this.epoch;this.userSelected=true;
    const allowed=await handle.queryPermission({mode:'readwrite'});
    if(this.disposed||epoch!==this.epoch)return false;
    if(allowed!=='granted')throw new Error('未获得文件夹写入权限，请重新选择并授权。');
    // Keep identities for all chosen destinations. Switching A -> B -> A
    // must reuse A's saved-file records rather than create duplicate __2 files.
    const registry=await this.get('save-directories')||[];
    const previous=await this.get('save-directory');
    if(previous&&!registry.some(x=>x.id===previous.id))registry.push(previous);
    if(this.target&&!registry.some(x=>x.id===this.target.id))registry.push(this.target);
    let target=null;
    for(const item of registry){
      if(await handle.isSameEntry(item.handle).catch(()=>false)){target={id:item.id,handle};break;}
    }
    target||={handle,id:this.uuid()};
    if(this.disposed||epoch!==this.epoch)return false;
    const entries=registry.filter(x=>x.id!==target.id);entries.push(target);
    await this.set('save-directories',entries);
    await this.set('save-directory',target);
    if(this.disposed||epoch!==this.epoch)return false;
    this.target=target;this.enabled=true;this.error='';this.lastSaved='';
    if(batchId)await this.bind(batchId);
    this.emit();return true;
  }
  async select(batchId=null){
    if(this.choosing||this.disposed)return false;
    this.choosing=true;this.epoch++;this.emit();
    try{
      // Always invoke a fresh picker, even when the current folder is granted.
      // Called before the first await to retain the browser's user activation.
      const handle=await this.choose();
      return await this.use(handle,batchId);
    }catch(error){
      if(error.name==='AbortError')return false;
      this.error=error.message||String(error);throw error;
    }finally{this.choosing=false;this.emit();}
  }
  async save(batch,shouldContinue=()=>true){
    if(this.saving||!batch||!this.target||!this.enabled||this.choosing||this.disposed)return;
    const target=this.target,epoch=this.epoch;
    const active=()=>!this.disposed&&epoch===this.epoch&&this.enabled&&!this.choosing&&shouldContinue();
    this.saving=true;
    try{
      if(await target.handle.queryPermission({mode:'readwrite'})!=='granted')throw new Error('目录写入权限失效，请重新选择并授权。');
      for(const job of batch.jobs){
        if(!active())return;
        if(job.state!=='COMPLETE'||!job.outputs?.length)continue;
        const key=`saved:${target.id}:${job.id}`;
        if(await this.get(key))continue;
        if(!active())return;
        const response=await this.fetchVideo(batch.id,job.id);
        if(!active())return;
        if(!response.ok)throw new Error('视频下载失败；云端原片保留。');
        const blob=await response.blob();
        const signature=new Uint8Array(await blob.slice(4,8).arrayBuffer());
        if(!active())return;
        if(String.fromCharCode(...signature)!=='ftyp')throw new Error('下载内容不是MP4。');
        const parts=job.outputs[0].relative_path.split('/');let dir=target.handle;
        for(const part of parts.slice(0,-1)){
          if(!active())return;
          dir=await dir.getDirectoryHandle(part,{create:true});
        }
        const wanted=parts.at(-1);let name=wanted,count=1;
        for(;;){
          if(!active())return;
          try{await dir.getFileHandle(name);name=wanted.replace(/\.mp4$/i,`__${++count}.mp4`);}
          catch(error){if(error.name==='NotFoundError')break;throw error;}
        }
        if(!active())return;
        const handle=await dir.getFileHandle(name,{create:true});
        if(!active())return;
        const writer=await handle.createWritable();
        try{
          if(!active()){await writer.abort();return;}
          await writer.write(blob);
          if(!active()){await writer.abort();return;}
          await writer.close();
        }catch(error){await writer.abort?.().catch(()=>{});throw error;}
        // If a completed write overlaps a directory change, record it under
        // its actual old destination, never under the newly selected folder.
        await this.set(key,{name,saved_at:Date.now()});
        if(active()){this.lastSaved=name;this.error='';this.emit();}
      }
    }catch(error){
      // A canceled/old download cannot turn the new folder's badge red.
      if(active()){this.enabled=false;this.error=error.message||String(error);this.emit();}
    }finally{this.saving=false;this.emit();}
  }
}
