"""Resume two existing lanes and fill their idle slots; max two Body processes."""
from pathlib import Path
import subprocess,sys,time,threading,fcntl
from concurrent.futures import ThreadPoolExecutor
import pipeline as p
from ring_first_3d.mainline.native.io import save_json
PLAN=p.TASK/'audit/BODY_QUEUE.json';LOCK=PLAN.with_suffix('.lock');rows=[];guard=threading.Lock()
def update(fn):
    with LOCK.open('a') as f:
        fcntl.flock(f,fcntl.LOCK_EX);plan=p.read(PLAN);value=fn(plan);tmp=PLAN.with_suffix('.pending');save_json(tmp,plan);tmp.replace(PLAN);fcntl.flock(f,fcntl.LOCK_UN);return value
def take(worker):
    def apply(plan):
        for row in plan['items']:
            if row['state']=='PENDING':row['state']='RUNNING';row['worker']=worker;return row.copy()
        return None if plan['sealed'] else False
    return update(apply)
def active(g,vi):
    ps=subprocess.check_output(['ps','-eo','args'],text=True)
    return any(line.startswith(sys.executable) and 'run.py run --stage body-one' in line and '--group '+g in line and '--video '+vi in line for line in ps.splitlines())
def worker(lane):
    g,vi=lane['initial_group'],lane['initial_video'];base=p.OUT/g/vi/'body/B2'
    while not ((base/'TASK_PREDICTION_FROZEN.json').exists() or (base/'FAILURE.json').exists()) or active(g,vi):time.sleep(3)
    while True:
        item=take(lane['worker'])
        if item is None:return
        if item is False:time.sleep(3);continue
        g,vi=item['group'],item['video'];print('QUEUE_INSTANCE_START',g,vi,flush=True)
        for arm in ['B1','B2']:
            root=p.OUT/g/vi/'body'/arm
            if (root/'TASK_PREDICTION_FROZEN.json').exists() or (root/'FAILURE.json').exists():continue
            log=p.TASK/'logs'/f'TRAIN_{g}_{vi}_{arm}.log';start=time.monotonic()
            with log.open('w') as stream:
                try:result=subprocess.run([sys.executable,str(p.TASK/'code/run.py'),'run','--stage','body-one','--group',g,'--video',vi,'--arm',arm],stdout=stream,stderr=subprocess.STDOUT,timeout=5400);code=result.returncode
                except subprocess.TimeoutExpired:code=-1
            if not (root/'TASK_PREDICTION_FROZEN.json').exists():
                root.mkdir(parents=True,exist_ok=True)
                if not (root/'FAILURE.json').exists():save_json(root/'FAILURE.json',dict(status='FAIL',reason='BODY_PROCESS_FAILED',exit_code=code,log=str(log),GT_read=False))
            row=dict(group=g,video=vi,arm=arm,exit_code=code,seconds=time.monotonic()-start,log=str(log),prediction_status='PASS' if (root/'TASK_PREDICTION_FROZEN.json').exists() else 'FAIL')
            with guard:rows.append(row);save_json(p.TASK/'logs/BODY_BATCH_ADDITIONAL.json',rows)
            print('QUEUE_ARM_TERMINAL',row,flush=True)
        def finish(plan):
            next(r for r in plan['items'] if (r['group'],r['video'])==(g,vi))['state']='COMPLETE'
        update(finish)
def main():
    p.verify();plan=p.read(PLAN);assert len(plan['initial_lanes'])==2
    with ThreadPoolExecutor(max_workers=2) as ex:list(ex.map(worker,plan['initial_lanes']))
    print('BODY_QUEUE_COMPLETE',len(rows),'arms',flush=True)
if __name__=='__main__':main()
