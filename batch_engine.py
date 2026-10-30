"""Persistent, bounded ComfyUI queue. No RunningHub OpenAPI or inference changes."""
from __future__ import annotations
import copy
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import sqlite3
import threading
import time
import urllib.error
import urllib.request
import uuid
try:
    from .batch_prompts import match_prompts
    from .batch_autoprompt import MODEL_NAME, add_nodes, append_gui, generated_text
except ImportError:  # Standalone verification outside ComfyUI.
    from batch_prompts import match_prompts
    from batch_autoprompt import MODEL_NAME, add_nodes, append_gui, generated_text

ACTIVE = ('SUBMITTING', 'QUEUED', 'RUNNING')
TERMINAL = ('COMPLETE', 'FAILED', 'SKIPPED', 'CANCELED')
IMAGE_EXT = {'.png', '.jpg', '.jpeg', '.webp', '.bmp'}

def clean_part(value):
    value = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', str(value)).strip(' .')[:150]
    if not value: value = 'image'
    if re.fullmatch(r'(?i)(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])', value): value = '_' + value
    return value

def clean_relative(value):
    parts = str(value).replace('\\', '/').split('/')
    if any(p in ('..', '.') for p in parts): raise ValueError('素材相对路径不能包含 . 或 ..')
    return '/'.join(clean_part(p) for p in parts if p)

def scrub_secrets(obj):
    if isinstance(obj, dict):
        return {k: '' if re.search(r'api.?key|password|secret|authorization|token|密码|密钥', k, re.I)
                else scrub_secrets(v) for k,v in obj.items()}
    if isinstance(obj, list): return [scrub_secrets(v) for v in obj]
    return obj

def within(root, relative):
    target = (Path(root) / relative).resolve()
    if not target.is_relative_to(Path(root).resolve()): raise ValueError('文件路径越界')
    return target

class Rejected(Exception):
    """Explicit non-acceptance; unlike a timeout, retry can be unambiguous."""
    def __init__(self, message, busy=False):
        super().__init__(message); self.busy = busy

class ComfyClient:
    def __init__(self, base): self.base = base.rstrip('/')
    def request(self, path, data=None):
        request = urllib.request.Request(self.base+path,
            data=None if data is None else json.dumps(data, ensure_ascii=False).encode(),
            headers={'Content-Type':'application/json'})
        try:
            with urllib.request.urlopen(request, timeout=30) as r: return json.load(r)
        except urllib.error.HTTPError as e:
            message=e.read().decode('utf-8', 'replace')[:3000]
            if e.code in (400, 401, 403, 404, 409, 422, 429):
                raise Rejected(message, busy=e.code==429) from e
            # 5xx can happen after acceptance. Never automatically POST again.
            raise RuntimeError('ComfyUI服务响应异常；需核对任务标识') from e
    def queue(self): return self.request('/queue')
    def history(self, pid): return self.request('/history/'+pid).get(pid)
    def submit(self, body): return self.request('/prompt', body)

class BatchEngine:
    def __init__(self, db_path, output_root, input_root, client, can_run=lambda:False, clock=time.time):
        self.db_path=Path(db_path);self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.output_root=Path(output_root).resolve();self.input_root=Path(input_root).resolve()
        self.client=client;self.can_run=can_run;self.clock=clock
        self.lock=threading.RLock();self.tick_lock=threading.Lock();self.stopping=threading.Event()
        self.db=sqlite3.connect(self.db_path, check_same_thread=False)
        self.db.row_factory=sqlite3.Row
        self.db.executescript('''
          PRAGMA journal_mode=WAL;
          CREATE TABLE IF NOT EXISTS batches(id TEXT PRIMARY KEY,created REAL,state TEXT,config TEXT,prompt TEXT,workflow TEXT,error TEXT DEFAULT '');
          CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY,batch_id TEXT,ordinal INTEGER,original TEXT,relative_path TEXT,input_name TEXT,stem TEXT,seed INTEGER,state TEXT,prompt_id TEXT,outputs TEXT DEFAULT '[]',error TEXT DEFAULT '',updated REAL,missing_since REAL DEFAULT 0,retry_after REAL DEFAULT 0);
          CREATE INDEX IF NOT EXISTS batch_jobs ON jobs(batch_id,ordinal);
        ''');self.db.commit()
        if 'job_prompt' not in {r['name'] for r in self.db.execute('PRAGMA table_info(jobs)')}:
            self.db.execute('ALTER TABLE jobs ADD COLUMN job_prompt TEXT')
            self.db.commit()

    def rows(self, sql, args=()):
        with self.lock: return [dict(r) for r in self.db.execute(sql,args).fetchall()]
    def update(self, table, id, **fields):
        assert table in ('jobs','batches')
        with self.lock, self.db:
            self.db.execute(f'UPDATE {table} SET '+','.join(k+'=?' for k in fields)+' WHERE id=?',(*fields.values(),id))

    def create(self, payload, widget_names=None):
        graph=scrub_secrets(copy.deepcopy(payload.get('prompt',{})))
        if not isinstance(graph,dict): raise ValueError('需要当前工作流的计算图')
        studio=str(payload.get('studio_id',''));saver=str(payload.get('saver_id',''))
        if graph.get(studio,{}).get('class_type')!='MiniMXH3LoopStudio': raise ValueError('未找到本项目创作台')
        if graph.get(saver,{}).get('class_type')!='VHS_VideoCombine': raise ValueError('未找到直接相连的Video Combine')
        if graph[saver]['inputs'].get('images') != [studio,0]: raise ValueError('批量版要求Video Combine图像输入直接连接当前创作台')
        cfg=graph[studio]['inputs']
        if not (cfg.get('启用周期循环') and cfg.get('图生视频')) or any(cfg.get(k) for k in ('图生连续拼接','多参考连续拼接','文生视频','首尾帧','视频编辑','数字人','双人数字人','MV数字人')):
            raise ValueError('批量版用于图生视频的周期循环：请先选择周期循环，关闭连续拼接及其他模式。')
        if cfg.get('启用提示词增强'): raise ValueError('请关闭提示词增强，确保每张图使用填写的原始提示词。')
        if not str(cfg.get('模型','')).startswith('minimax_h3_ref2va'): raise ValueError('请沿用稳定版Ref2VA主模型')
        if cfg.get('循环条件路线')!='单图参考（推荐）': raise ValueError('请选择稳定版单图参考周期路线')
        if graph[saver]['inputs'].get('format')!='video/h264-mp4': raise ValueError('本批量版请将Video Combine格式设为video/h264-mp4')
        images=payload.get('images',[])
        if not isinstance(images,list) or not 1<=len(images)<=1000: raise ValueError('每批支持1至1000张图片')
        mode=payload.get('prompt_mode') or ('txt' if payload.get('prompt_text') is not None else 'common')
        if mode not in ('auto','txt','common'):raise ValueError('未知提示词方式')
        rules=str(payload.get('prompt_rules') or '').strip()
        if mode=='auto' and not 1<=len(rules)<=12000:raise ValueError('请填写自动写词规范，最多12000字')
        per_image = match_prompts(payload.get('prompt_text'), images) if mode=='txt' else None
        if mode=='common' and not str(cfg.get('提示词','')).strip(): raise ValueError('请上传逐图提示词TXT，或填写下方通用提示词')
        limit=int(payload.get('concurrency',1))
        if limit not in (1,2): raise ValueError('队列名额只能为1或2')
        # Keep only the selected output dependency graph, not unrelated outputs.
        keep=set()
        def visit(nid):
            if nid in keep:return
            keep.add(nid)
            for value in graph[nid].get('inputs',{}).values():
                if isinstance(value,list) and len(value)==2 and isinstance(value[0],str) and value[0] in graph:visit(value[0])
        visit(saver);graph={k:v for k,v in graph.items() if k in keep}
        bid=str(uuid.uuid4());now=self.clock();reserved=set();jobs=[]
        fixed=bool(payload.get('fixed_seed',False))
        for index,image in enumerate(images):
            original=str(image.get('name',''))
            if Path(original).suffix.lower() not in IMAGE_EXT: raise ValueError('不支持的图片：'+original)
            input_name=str(image.get('filename',''))
            if not within(self.input_root,input_name).is_file(): raise ValueError('云端缺少上传图片：'+original)
            relative=clean_relative(image.get('relative_path') or original)
            folder=str(Path(relative).parent).replace('\\','/')
            if folder=='.':folder=''
            base=clean_part(Path(original).stem);stem=base;n=1
            while (folder+'/'+stem).casefold() in reserved:
                n+=1;stem=f'{base}__{n}'
            reserved.add((folder+'/'+stem).casefold())
            stem=(folder+'/' if folder else '')+stem
            seed=int(cfg.get('随机种子',0)) if fixed else secrets.randbelow(2**53)
            jobs.append((str(uuid.uuid4()),bid,index,original,relative,input_name,stem,seed,'WAITING',None,now,per_image[index] if per_image is not None else None))
        config={'studio_id':studio,'saver_id':saver,'concurrency':limit,'fixed_seed':fixed,
                'client_id':str(payload.get('client_id','')),'widget_names':widget_names or {},
                'label':str(payload.get('label') or f'{len(jobs)}张图片')[:120],
                'prompt_source':{'auto':'自动看图写词','txt':'TXT逐图匹配','common':'通用提示词'}[mode],
                'prompt_mode':mode,'autoprompt':{'rules':rules,'model_name':MODEL_NAME} if mode=='auto' else None}
        workflow=scrub_secrets(payload.get('workflow',{}))
        with self.lock,self.db:
            self.db.execute('INSERT INTO batches(id,created,state,config,prompt,workflow) VALUES(?,?,?,?,?,?)',
                (bid,now,'PAUSED',json.dumps(config,ensure_ascii=False),json.dumps(graph,ensure_ascii=False),json.dumps(workflow,ensure_ascii=False)))
            self.db.executemany('INSERT INTO jobs(id,batch_id,ordinal,original,relative_path,input_name,stem,seed,state,prompt_id,updated,job_prompt) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',jobs)
        return self.status(bid)

    def status(self,bid=None):
        batches=self.rows('SELECT * FROM batches '+('WHERE id=?' if bid else '')+' ORDER BY created DESC LIMIT 30',(bid,) if bid else ())
        data=[]
        for b in batches:
            jobs=self.rows('SELECT * FROM jobs WHERE batch_id=? ORDER BY ordinal',(b['id'],))
            for j in jobs:
                j['outputs']=json.loads(j['outputs'])
            counts={state:sum(j['state']==state for j in jobs) for state in ('WAITING',*ACTIVE,*TERMINAL,'UNKNOWN')}
            data.append({'id':b['id'],'created':b['created'],'state':b['state'],'config':json.loads(b['config']),
                'error':b['error'],'counts':counts,'total':len(jobs),'jobs':jobs})
        return data[0] if bid and data else (None if bid else data)

    def action(self,bid,action):
        with self.lock:
            if not self.rows('SELECT id FROM batches WHERE id=?',(bid,)):raise ValueError('批次不存在')
            if action=='start':
                if not self.can_run(): raise ValueError('当前是无显卡/CPU模式。批次已保存；请在GPU模式启动ComfyUI后点击继续。')
                if self.rows('SELECT id FROM jobs WHERE batch_id=? AND state="UNKNOWN"',(bid,)):raise ValueError('存在提交结果不明的任务，请先核对并跳过，避免重复生成')
                if self.rows('SELECT id FROM batches WHERE state="RUNNING" AND id<>?',(bid,)):raise ValueError('已有另一批次运行，请先暂停它')
                self.update('batches',bid,state='RUNNING',error='')
            elif action=='pause':self.update('batches',bid,state='PAUSED')
            elif action=='cancel':
                self.update('batches',bid,state='CANCELED')
                with self.db:self.db.execute('UPDATE jobs SET state="CANCELED" WHERE batch_id=? AND state="WAITING"',(bid,))
            elif action=='retry-failed':
                self.update('batches',bid,state='PAUSED')
                with self.db:self.db.execute('UPDATE jobs SET state="WAITING",prompt_id=NULL,error="",missing_since=0,retry_after=0 WHERE batch_id=? AND state="FAILED"',(bid,))
            elif action=='skip-unknown':
                with self.db:self.db.execute('UPDATE jobs SET state="SKIPPED",error="用户核对后跳过；不自动重交" WHERE batch_id=? AND state="UNKNOWN"',(bid,))
            else:raise ValueError('未知操作')
        return self.status(bid)

    def prepare(self,batch,job):
        cfg=json.loads(batch['config']);graph=json.loads(batch['prompt']);wf=json.loads(batch['workflow'])
        studio=cfg['studio_id'];saver=cfg['saver_id'];inp=graph[studio]['inputs']
        inp['图片1']=job['input_name'];inp['随机种子']=job['seed']
        if job.get('job_prompt') is not None:
            inp['提示词']=job['job_prompt']
        # A saved per-segment UI state must never replace this job's prompt.
        if '图生分段提示词' in inp:inp['图生分段提示词']='[]'
        if '仅增强提示词' in inp:inp['仅增强提示词']=False
        for i in range(2,21):
            if '图片'+str(i) in inp:inp['图片'+str(i)]='未选择'
        auto_ids=add_nodes(graph,studio,job,cfg['autoprompt'],[n.get('id') for n in wf.get('nodes',[])]) if cfg.get('prompt_mode')=='auto' else None
        prefix=f"minimx_batches/{batch['id']}/raw/{job['stem']}"
        graph[saver]['inputs']['filename_prefix']=prefix
        for node in wf.get('nodes',[]):
            nid=str(node.get('id',''));changes={}
            if nid==studio:changes={k:v for k,v in inp.items() if k in ('随机种子','提示词','图生分段提示词','仅增强提示词') or re.fullmatch('图片[0-9]+',k)}
            if nid==studio and auto_ids:changes['提示词']='自动看图写词（由连接输入提供）'
            if nid==saver:changes={'filename_prefix':prefix}
            widget_values=node.get('widgets_values')
            if isinstance(widget_values,dict):widget_values.update(changes)
            elif isinstance(widget_values,list):
                for index,name in enumerate(cfg['widget_names'].get(nid,[])):
                    if index<len(widget_values) and name in changes:widget_values[index]=changes[name]
        wf.setdefault('extra',{})['minimx_batch_job']={'batch_id':batch['id'],'job_id':job['id'],'original':job['original'],'relative_path':job['relative_path'],'seed':job['seed']}
        if auto_ids:append_gui(wf,graph,auto_ids,studio)
        return {'prompt_id':job['prompt_id'],'prompt':graph,'client_id':cfg['client_id'],
                'extra_data':{'extra_pnginfo':{'workflow':wf}}}

    def finish(self,batch,job,history):
        if json.loads(batch['config']).get('prompt_mode')=='auto':
            prepared=self.prepare(batch,job)
            text=generated_text(history,prepared['prompt'])
            if text:self.update('jobs',job['id'],job_prompt=text)
        status=history.get('status',{})
        if status.get('status_str')=='error':
            self.update('jobs',job['id'],state='FAILED',error=json.dumps(status.get('messages',[]),ensure_ascii=False)[:3000],updated=self.clock());return
        if not status.get('completed'):return
        saver=json.loads(batch['config'])['saver_id']
        output=history.get('outputs',{}).get(saver,{})
        candidates=[x for key in ('gifs','videos','images') for x in output.get(key,[]) if isinstance(x,dict) and str(x.get('filename','')).lower().endswith('.mp4') and x.get('type','output')=='output']
        candidates.sort(key=lambda x:('-audio.' in x['filename']),reverse=True)
        if not candidates:
            self.update('jobs',job['id'],state='FAILED',error='任务结束但指定合成节点未返回MP4；未重交任务',updated=self.clock());return
        item=candidates[0];source=within(self.output_root,str(Path(item.get('subfolder',''))/item['filename']))
        if not source.is_file():
            self.update('jobs',job['id'],state='FAILED',error='视频输出文件不存在；未重交任务',updated=self.clock());return
        relative=f"minimx_batches/{batch['id']}/videos/{job['stem']}.mp4"
        target=within(self.output_root,relative);target.parent.mkdir(parents=True,exist_ok=True)
        # Per-job destination is reserved at batch creation. If a crash happened
        # after copying, identical existing bytes finish reconciliation safely.
        if target.exists():
            import hashlib
            def digest(p):
                h=hashlib.sha256()
                with p.open('rb') as f:
                    for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
                return h.digest()
            if source.stat().st_size!=target.stat().st_size or digest(source)!=digest(target):
                raise ValueError('同名输出已存在且内容不同，已保护原文件：'+relative)
        else:
            try:os.link(source,target)
            except OSError:
                # Atomic replacement of our own temporary file, never clobber a
                # destination created by someone else in the meantime.
                temporary=target.with_name(target.name+'.'+job['id']+'.part')
                with source.open('rb') as src,temporary.open('wb') as dst:shutil.copyfileobj(src,dst)
                try:os.link(temporary,target)
                except OSError:
                    with target.open('xb') as dst,temporary.open('rb') as src:shutil.copyfileobj(src,dst)
                temporary.unlink(missing_ok=True)
        result={'filename':target.name,'subfolder':str(target.parent.relative_to(self.output_root)).replace('\\','/'),'type':'output',
                'relative_path':job['stem']+'.mp4','bytes':target.stat().st_size}
        self.update('jobs',job['id'],state='COMPLETE',outputs=json.dumps([result],ensure_ascii=False),error='',updated=self.clock(),missing_since=0)

    def tick(self):
        if not self.tick_lock.acquire(blocking=False):return
        try:self._tick()
        finally:self.tick_lock.release()

    def _tick(self):
        batches=self.rows('SELECT * FROM batches WHERE state="RUNNING" OR id IN (SELECT batch_id FROM jobs WHERE state IN ("SUBMITTING","QUEUED","RUNNING"))')
        if not batches:return
        queue=self.client.queue();running={str(x[1]) for x in queue.get('queue_running',[]) if len(x)>1};pending={str(x[1]) for x in queue.get('queue_pending',[]) if len(x)>1}
        for batch in batches:
            for job in self.rows('SELECT * FROM jobs WHERE batch_id=? AND state IN ("SUBMITTING","QUEUED","RUNNING")',(batch['id'],)):
                pid=job['prompt_id']
                if pid in running|pending:
                    self.update('jobs',job['id'],state='RUNNING' if pid in running else 'QUEUED',missing_since=0);continue
                history=self.client.history(pid)
                if history:
                    try:self.finish(batch,job,history)
                    except Exception as e:
                        # A copy error is retryable by reconciliation, not by
                        # rerunning paid inference. Keep the accepted job id.
                        self.update('jobs',job['id'],error='视频归档暂未完成：'+str(e)[:800])
                    continue
                since=job['missing_since'] or self.clock()
                self.update('jobs',job['id'],missing_since=since)
                if self.clock()-since>=30:
                    self.update('jobs',job['id'],state='UNKNOWN',error='任务不在队列/历史中，已暂停；请核对后跳过，不会自动重交')
                    self.update('batches',batch['id'],state='PAUSED',error='有任务状态不明，请核对')
        for batch in batches:
            jobs=self.rows('SELECT * FROM jobs WHERE batch_id=?',(batch['id'],))
            if jobs and all(j['state'] in TERMINAL for j in jobs) and batch['state']!='CANCELED':self.update('batches',batch['id'],state='COMPLETED')
        if not self.can_run():return
        current=self.rows('SELECT * FROM batches WHERE state="RUNNING" ORDER BY created LIMIT 1')
        if not current:return
        batch=current[0];limit=json.loads(batch['config'])['concurrency']
        active=self.rows('SELECT * FROM jobs WHERE state IN ("SUBMITTING","QUEUED","RUNNING")')
        busy_ids=running|pending|{j['prompt_id'] for j in active if j['prompt_id']}
        if len(busy_ids)>=limit:return
        waiting=self.rows('SELECT * FROM jobs WHERE batch_id=? AND state="WAITING" AND retry_after<=? ORDER BY ordinal LIMIT 1',(batch['id'],self.clock()))
        if not waiting:return
        job=waiting[0];pid=str(uuid.uuid4())
        with self.lock:
            if self.rows('SELECT state FROM batches WHERE id=?',(batch['id'],))[0]['state']!='RUNNING':return
            self.update('jobs',job['id'],state='SUBMITTING',prompt_id=pid,updated=self.clock(),missing_since=0)
        job.update(state='SUBMITTING',prompt_id=pid)
        try:
            reply=self.client.submit(self.prepare(batch,job))
            if reply.get('prompt_id')!=pid:raise RuntimeError('服务器未回显预先登记的任务UUID，已停止补交')
            self.update('jobs',job['id'],state='QUEUED',error='')
        except Rejected as e:
            if e.busy:self.update('jobs',job['id'],state='WAITING',prompt_id=None,error='名额已满，30秒后再检查',retry_after=self.clock()+30)
            else:self.update('jobs',job['id'],state='FAILED',error=str(e)[:3000])
        except Exception as e:
            self.update('jobs',job['id'],error='提交响应未确认；正在按任务UUID核对：'+str(e)[:800],missing_since=self.clock())
            # Retain SUBMITTING and the UUID. Subsequent GETs reconcile it.

    def start_worker(self):
        def work():
            while not self.stopping.wait(2):
                try:self.tick()
                except Exception:pass  # HTTP server can still be starting/restarting.
        thread=threading.Thread(target=work,name='MiniMX-BatchQueue',daemon=True);thread.start();return thread
