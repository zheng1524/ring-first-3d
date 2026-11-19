"""Serial all-case execution; fixed last checkpoints; never open GT."""
from common import *
from publish import arm_case,export_A
from native_score import evaluate
import subprocess,argparse
PY='/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python'

def command(script,args,tag=None):
    name='_'.join([script.removesuffix('.py')]+args);log=R/'runtime'/(name+'.log');env=dict(os.environ)
    if tag:env['E4_RUN_DIR']=str(R/'arms'/tag)
    with log.open('a')as f:
        code=subprocess.call([PY,'-B',str(R/'code'/script)]+args,env=env,stdout=f,stderr=subprocess.STDOUT)
    if code:raise RuntimeError('Engineering interruption; retain state: '+str(log))

def main():
    cases=load(R/'config/CASE_LOCK.json');done=[]
    for c in cases:
        n=c['name'];export_A(n)
        for t in ['Init-B','Init-C']:
            for subset in [False,True]:
                p=R/'initializations'/n/(t+('_SUBSET'if subset else'')+'.npz')
                if not p.exists():
                    save('runtime/STATUS.json',dict(phase='A_INITIALIZATION',case=n,arm=t,subset=subset,completed_downstream=len(done),epoch=time.time()));command('initialize.py',[n,t]+(['--subset']if subset else[]))
        for t in ['Init-A','Init-B','Init-C']:
            initial=R/'initializations'/n/(t+'.npz');root=arm_case(t,n,initial);final=root/'local_results'/n/'FINAL.npz'
            if not final.exists():
                save('runtime/STATUS.json',dict(phase='A_DOWNSTREAM',case=n,arm=t,completed_downstream=len(done),epoch=time.time()));command('train_mesh.py',[n]+(['--resume']if list((root/'local_results'/n).glob('*.pt'))else[]),t)
            done.append(dict(case=n,arm=t,run=load(root/'metrics'/(n+'_RUN.json'))))
            for stage,path in [('INITIAL',initial),('FINAL',final)]:
                dest=R/'metrics/scores'/(n+'_'+t+'_'+stage+'.json')
                if not dest.exists():save(dest.relative_to(R),evaluate(n,path,True,t+'_'+stage))
        # Publish current-case artifacts immediately; failure of plotting cannot erase predictions.
        command('preview_case.py',[n]);save('metrics/PHASE_A_RUNS.json',done);print('PHASE_A_CASE_COMPLETE',n,len(done),flush=True)
    files=[dict(asset(R/'arms'/t/'local_results'/c['name']/'FINAL.npz'),case=c['name'],arm=t)for c in cases for t in ['Init-A','Init-B','Init-C']];save('provenance/PHASE_A_PREDICTIONS_FROZEN.json',dict(epoch=time.time(),files=files,GT_opened=False,selection_uses_FIT_only=True));save('runtime/STATUS.json',dict(phase='PHASE_A_COMPLETE',completed_downstream=len(done),epoch=time.time()));print('PHASE_A_COMPLETE',len(done),flush=True)

if __name__=='__main__':main()
