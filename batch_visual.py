"""Observe this queue's execution for the UI; never submit or alter a graph."""
import copy
import json
import logging
import threading
import time
from collections import OrderedDict


class BatchVisual:
    EVENTS = {'execution_start', 'executing', 'executed', 'execution_error',
              'execution_interrupted', 'progress', 'minimxa_loop_h3_phase'}

    def __init__(self, engine, clock=time.time):
        self.engine = engine
        self.clock = clock
        self.records = OrderedDict()
        self.lock = threading.RLock()
        self.current_pid = None

    def _record(self, pid):
        if pid in self.records:
            return self.records[pid]
        jobs = self.engine.rows('SELECT * FROM jobs WHERE prompt_id=?', (pid,))
        if not jobs:
            return None
        job = jobs[0]
        batch = self.engine.rows('SELECT * FROM batches WHERE id=?', (job['batch_id'],))[0]
        cfg = json.loads(batch['config'])
        graph = self.engine.prepare(batch, job)['prompt']
        preview = graph[cfg['studio_id']]['inputs'].get('提示词')
        record = {'job': job, 'studio': cfg['studio_id'], 'saver': cfg['saver_id'],
                  'preview': str(preview[0]) if isinstance(preview, list) else None,
                  'types': {nid: n['class_type'] for nid, n in graph.items()},
                  'live': {}, 'last_emit': 0}
        self.records[pid] = record
        while len(self.records) > 256:
            self.records.popitem(last=False)
        return record

    def observe(self, event, data):
        if event not in self.EVENTS or not isinstance(data, dict):
            return None
        with self.lock:
            pid = data.get('prompt_id')
            if event == 'execution_start':
                # Track manual prompts too so a later untagged phase cannot
                # accidentally be attributed to the preceding batch job.
                self.current_pid = pid
            if event == 'minimxa_loop_h3_phase':
                pid = self.current_pid
            if not pid:
                return None
            record = self._record(str(pid))
            if not record:
                return None
            live = record['live']
            node = str(data.get('node', ''))
            kind = record['types'].get(node)
            change = None
            if event == 'execution_start':
                change = {'stage': 'preparing', 'label': '正在准备当前参考图', 'percent': None}
            elif event == 'executing':
                if kind == 'AILab_QwenVL':
                    change = {'stage': 'writing', 'label': 'AI 正在看图写提示词', 'percent': None}
                elif node == record['studio']:
                    change = {'stage': 'video', 'label': '正在生成周期视频', 'percent': None}
                elif node == record['saver']:
                    change = {'stage': 'saving', 'label': '正在合成并保存 MP4', 'percent': None}
                elif data.get('node') is None:
                    change = {'stage': 'saving', 'label': '视频已生成，正在核对归档', 'percent': None}
            elif event == 'executed' and node == record['preview']:
                values = data.get('output', {}).get('text', [])
                if values and isinstance(values[0], str) and values[0].strip():
                    text = values[0].strip()
                    # Persist before H3 starts, including when no browser is open.
                    self.engine.update('jobs', record['job']['id'], job_prompt=text)
                    record['job']['job_prompt'] = text
                    change = {'stage': 'prompt_ready', 'label': '提示词已写好，准备生成视频', 'percent': None}
            elif event == 'minimxa_loop_h3_phase' and live.get('stage') == 'video':
                base = float(data.get('progress', 0))
                change = {'stage': 'video', 'label': str(data.get('phase') or '正在生成周期视频'),
                          'percent': max(0, min(100, base)), 'base': base, 'span': float(data.get('span', 0))}
            elif event == 'progress' and live.get('stage') == 'video' and float(data.get('max', 0)) > 0:
                # Internal sampling nodes report their own IDs, while prompt_id
                # identifies the exact owned job. Do not invent an overall ETA.
                ratio = max(0, min(1, float(data.get('value', 0)) / float(data['max'])))
                change = {'percent': max(0, min(100, live.get('base', 0) + ratio * live.get('span', 100)))}
            elif event in ('execution_error', 'execution_interrupted'):
                change = {'stage': 'error', 'label': '任务失败，请查看队列错误信息', 'percent': None}
            if change is None:
                return None
            live.update(change, updated=self.clock())
            if event == 'progress' and self.clock() - record['last_emit'] < .5:
                return None
            record['last_emit'] = self.clock()
            job = record['job']
            return {'batch_id': job['batch_id'], 'job_id': job['id'], 'prompt_id': str(pid),
                    'live': copy.deepcopy(live), 'job_prompt': job.get('job_prompt')}

    def enrich(self, batch):
        if batch:
            with self.lock:
                common = None
                if batch['config'].get('prompt_mode', 'common') == 'common':
                    saved = self.engine.rows('SELECT prompt FROM batches WHERE id=?', (batch['id'],))
                    if saved:
                        common = json.loads(saved[0]['prompt'])[batch['config']['studio_id']]['inputs'].get('提示词', '')
                for job in batch['jobs']:
                    if common is not None:
                        job['effective_prompt'] = common
                    record = self.records.get(job.get('prompt_id'))
                    if record:
                        job['live'] = copy.deepcopy(record['live'])
        return batch

    def attach(self, server):
        previous = server.send_sync
        logger = logging.getLogger(__name__)
        warned = False

        def send(event, data, sid=None):
            nonlocal warned
            result = previous(event, data, sid)
            try:
                update = self.observe(event, data)
                if update:
                    # Broadcast only to this ComfyUI's connected clients so a
                    # refreshed page can follow jobs from its old client ID.
                    previous('minimx_batch_visual', update)
            except Exception:
                if not warned:
                    logger.exception('Batch display observer failed; original execution continues')
                    warned = True
            return result

        server.send_sync = send
