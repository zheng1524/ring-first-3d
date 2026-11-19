"""One entry point for every group/video; fail closed per instance."""
from pathlib import Path
import argparse,subprocess,sys,traceback,time
from concurrent.futures import ThreadPoolExecutor
import pipeline as p
from ring_first_3d.mainline.native.io import save_json,sha256

def legal_instances():
    result=[]
    for g in p.GROUPS:
        for video in ['004','005']:
            if p.inherited(g,video):continue
            fit=[v for v in p.instance_views(g,video) if v['meta']['role']=='FIT']
            if all((p.OUT/g/video/'camera'/v['meta']['id']/'ADMISSION.json').exists() and p.read(p.OUT/g/video/'camera'/v['meta']['id']/'ADMISSION.json')['status']=='PASS' for v in fit):result.append((g,video))
    return result

def freeze_code():
    file=p.TASK/'audit/EXECUTION_SOURCE_FREEZE.json'
    if file.exists():
        for r in p.read(file)['files']:assert sha256(r['path'])==r['sha256'],r['path']
        return
    names=['pipeline.py','inputs.py','banks.py','cameras.py','adapters.py','run.py']
    save_json(file,dict(files=[p.asset(p.TASK/'code'/n) for n in names],GT_geometry_read=False,all_camera_parameters_frozen=True))

def train_batch(group=None,video=None):
    jobs=[j for j in legal_instances() if (not group or j[0]==group) and (not video or j[1]==video)]
    def job(item):
        g,vi=item;rows=[]
        for arm in ['B1','B2']:
            dest=p.OUT/g/vi/'body'/arm
            if (dest/'TASK_PREDICTION_FROZEN.json').exists() or (dest/'FAILURE.json').exists():continue
            log=p.TASK/'logs'/f'TRAIN_{g}_{vi}_{arm}.log';start=time.monotonic()
            with log.open('w') as stream:
                try:
                    r=subprocess.run([sys.executable,str(Path(__file__)),'run','--stage','body-one','--group',g,'--video',vi,'--arm',arm],stdout=stream,stderr=subprocess.STDOUT,timeout=5400);code=r.returncode
                except subprocess.TimeoutExpired:code=-1
            if not (dest/'TASK_PREDICTION_FROZEN.json').exists():
                dest.mkdir(parents=True,exist_ok=True)
                if not (dest/'FAILURE.json').exists():save_json(dest/'FAILURE.json',dict(status='FAIL',reason='BODY_PROCESS_OR_CONTRACT_FAILED',exit_code=code,log=str(log),GT_read=False))
            row=dict(group=g,video=vi,arm=arm,exit_code=code,seconds=time.monotonic()-start,log=str(log));rows.append(row);print('BODY_TERMINAL',row,flush=True)
        return rows
    with ThreadPoolExecutor(max_workers=2) as ex:rows=[r for rr in ex.map(job,jobs) for r in rr]
    save_json(p.TASK/'logs/BODY_BATCH.json',rows)

def execute(stage,g=None,video=None,arm=None):
    if stage=='audit':
        from inputs import audit
        return audit()
    if stage=='banks':
        from banks import build
        return build(g,video)
    p.verify();freeze_code()
    if stage=='cameras':
        from cameras import solve
        return solve(g,video)
    if stage=='hero':
        from adapters import hero
        return hero()
    if stage=='body':return train_batch(g,video)
    if stage=='body-one':
        from adapters import body
        return body(g,video,arm)
    if stage=='evaluate':
        import adapters
        for gg,v in legal_instances():
            for aa in ['B1','B2']:assert (p.OUT/gg/v/'body'/aa/'TASK_PREDICTION_FROZEN.json').exists() or (p.OUT/gg/v/'body'/aa/'FAILURE.json').exists(),'Body not terminal'
        adapters.freeze_all()
        for gg,v in legal_instances():
            if (g and gg!=g) or (video and v!=video):continue
            if not all((p.OUT/gg/v/'body'/a/'TASK_PREDICTION_FROZEN.json').exists() for a in ['B1','B2']):continue
            if (p.OUT/gg/v/'GT_EVALUATION_COMPLETE.json').exists():continue
            try:adapters.evaluate(gg,v)
            except Exception:save_json(p.OUT/gg/v/'EVALUATION_FAILURE.json',dict(status='FAIL',error=traceback.format_exc()));print(traceback.format_exc(),flush=True)
        return
    if stage=='report':
        from publish import main
        return main()
    if stage=='check':
        from check_artifacts import main
        return main()
    raise ValueError(stage)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['check','run']);ap.add_argument('--stage',default='all',choices=['all','audit','banks','cameras','hero','body','body-one','evaluate','report','check']);ap.add_argument('--group',choices=p.GROUPS);ap.add_argument('--video',choices=['004','005']);ap.add_argument('--arm',choices=['B1','B2']);a=ap.parse_args()
    if a.action=='check':p.verify();freeze_code();print('INPUT_AND_SCIENTIFIC_SOURCE_CHECK_PASS');return
    stages=['audit','banks','cameras','hero','body','evaluate','report','check'] if a.stage=='all' else [a.stage]
    for s in stages:
        if s=='audit' and (p.TASK/'audit/INPUT_FREEZE.json').exists():p.verify();continue
        execute(s,a.group,a.video,a.arm)

if __name__=='__main__':main()
