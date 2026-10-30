"""Same-origin UI routes for the user's self-hosted ComfyUI instance."""
from pathlib import Path
from urllib.parse import quote
from aiohttp import web
import folder_paths
from server import PromptServer
from .batch_engine import BatchEngine, ComfyClient, within
from .batch_autoprompt import MODEL_NAME
from .batch_visual import BatchVisual

def autoprompt_ready():
    import nodes
    required=('AILab_QwenVL','MiniMXBase_WenWuH3ReleaseAtStart','LoadImage','ImageScaleToTotalPixels','PreviewAny')
    missing=[name for name in required if name not in nodes.NODE_CLASS_MAPPINGS]
    model_dir=Path(folder_paths.models_dir)/'LLM/Qwen'/MODEL_NAME
    # Prefer the upstream resolver so mounted/shared model stores also work.
    if 'AILab_QwenVL' in nodes.NODE_CLASS_MAPPINGS:
        import sys
        module=sys.modules.get(nodes.NODE_CLASS_MAPPINGS['AILab_QwenVL'].__module__)
        resolver=getattr(module,'resolve_hf_model_path',None)
        if resolver:model_dir=resolver('Qwen/'+MODEL_NAME) or model_dir
    installed=False
    try:
        import json
        index=json.loads((model_dir/'model.safetensors.index.json').read_text('utf-8'))
        installed=all((model_dir/name).is_file() and (model_dir/name).stat().st_size>0 for name in set(index['weight_map'].values())) and all((model_dir/name).is_file() for name in ('config.json','tokenizer.json','tokenizer_config.json','preprocessor_config.json'))
    except (OSError,ValueError,KeyError):pass
    return {'ready':not missing and installed,'missing_nodes':missing,'model_installed':installed,'model_name':MODEL_NAME}

def gpu_ready():
    import torch
    from comfy.cli_args import args
    return bool(torch.cuda.is_available() and not args.cpu)

from comfy.cli_args import args
port=int(getattr(args,'port',8188))
engine=BatchEngine(Path(folder_paths.get_user_directory())/'default/minimx_batch/queue.sqlite3',
    folder_paths.get_output_directory(),folder_paths.get_input_directory(),
    ComfyClient(f'http://127.0.0.1:{port}'),gpu_ready)
routes=PromptServer.instance.routes
BASE='/minimx/batch/v1'
visual=BatchVisual(engine)
visual.attach(PromptServer.instance)

@routes.get(BASE+'/info')
async def info(request):
    return web.json_response({'version':'1.2-auto-prompts','visual_version':1,'can_run':gpu_ready(),
        'mode':'GPU' if gpu_ready() else 'CPU预览','runninghub_member_supported':False,'autoprompt':autoprompt_ready()})

@routes.get(BASE+'/list')
async def batch_list(request):
    return web.json_response([{k:v for k,v in x.items() if k!='jobs'} for x in engine.status()])

@routes.get(BASE+'/status/{bid}')
async def batch_status(request):
    state=visual.enrich(engine.status(request.match_info['bid']))
    return web.json_response(state) if state else web.json_response({'error':'批次不存在'},status=404)

@routes.post(BASE+'/create')
async def batch_create(request):
    try:
        data=await request.json()
        if data.get('prompt_mode')=='auto' and not autoprompt_ready()['ready']:
            raise ValueError('自动看图写词节点或Qwen3-VL-4B官方模型尚未就绪，请等待部署完成；TXT/通用方式仍可用')
        import nodes
        names={}
        for nid in (str(data.get('studio_id')),str(data.get('saver_id'))):
            node=data.get('prompt',{}).get(nid,{})
            cls=nodes.NODE_CLASS_MAPPINGS.get(node.get('class_type'))
            if cls:
                fields=[]
                for name,spec in cls.INPUT_TYPES().get('required',{}).items():
                    fields.append(name)
                    if len(spec)>1 and isinstance(spec[1],dict) and spec[1].get('control_after_generate'):fields.append('control_after_generate')
                names[nid]=fields
        return web.json_response(engine.create(data,names))
    except (ValueError,KeyError,TypeError) as e:return web.json_response({'error':str(e)},status=400)

@routes.post(BASE+'/action/{bid}/{action}')
async def batch_action(request):
    try:return web.json_response(engine.action(request.match_info['bid'],request.match_info['action']))
    except ValueError as e:return web.json_response({'error':str(e)},status=409)

@routes.post(BASE+'/validate/{bid}')
async def batch_validate(request):
    """Run ComfyUI's own input/link checks without queuing or running models."""
    import execution,uuid,json
    bid=request.match_info['bid']
    batches=engine.rows('SELECT * FROM batches WHERE id=?',(bid,))
    jobs=engine.rows('SELECT * FROM jobs WHERE batch_id=? ORDER BY ordinal LIMIT 1',(bid,))
    if not batches or not jobs:return web.json_response({'error':'队列不存在'},status=404)
    prepared=engine.prepare(batches[0],jobs[0])
    valid=await execution.validate_prompt(str(uuid.uuid4()),prepared['prompt'],None)
    return web.json_response({'valid':bool(valid[0]),'error':valid[1],'node_errors':valid[3]})

@routes.get(BASE+'/video/{bid}/{jid}')
async def batch_video(request):
    batch=engine.status(request.match_info['bid'])
    if not batch:raise web.HTTPNotFound()
    job=next((j for j in batch['jobs'] if j['id']==request.match_info['jid']),None)
    if not job or job['state']!='COMPLETE' or not job['outputs']:raise web.HTTPNotFound()
    output=job['outputs'][0]
    path=within(engine.output_root,str(Path(output['subfolder'])/output['filename']))
    return web.FileResponse(path,headers={'Content-Type':'video/mp4',
        'Content-Disposition':"attachment; filename*=UTF-8''"+quote(output['filename']),
        'Cache-Control':'no-store'})

@routes.post(BASE+'/validate-graph')
async def validate_graph_only(request):
    """No batch creation, DB changes, submission, cancellation or inference."""
    import execution,uuid
    data=await request.json();graph=data.get('prompt',{})
    allowed={'MiniMXH3LoopStudio','VHS_VideoCombine','AILab_QwenVL','MiniMXBase_WenWuH3ReleaseAtStart','LoadImage','ImageScaleToTotalPixels','PreviewAny'}
    if not isinstance(graph,dict) or not graph or any(not isinstance(n,dict) or n.get('class_type') not in allowed for n in graph.values()):
        return web.json_response({'error':'仅检查本项目的计算图'},status=400)
    valid=await execution.validate_prompt(str(uuid.uuid4()),graph,None)
    return web.json_response({'valid':bool(valid[0]),'error':valid[1],'node_errors':valid[3],'generation_submitted':False})

engine.start_worker()
