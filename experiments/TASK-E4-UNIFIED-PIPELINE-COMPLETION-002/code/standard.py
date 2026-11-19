"""Standard pipeline including the mature native-reference preparation stage."""
from pathlib import Path
from types import SimpleNamespace
import argparse,shutil,sys,subprocess
import pipeline as p
import run
from ring_first_3d.mainline.native.io import save_json,sha256

def freeze():
    lock=p.TASK/'audit/STANDARD_ENTRY_SOURCE_FREEZE.json'
    if lock.exists():
        for r in p.read(lock)['files']:assert sha256(r['path'])==r['sha256']
        return
    files=[p.TASK/'PROTOCOL_REF_BUILD_REV1.yaml',p.TASK/'PROTOCOL_REF_DENSITY_REV2.yaml',p.TASK/'code/bootstrap_references.py',p.TASK/'code/complete_reference_inputs.py',p.TASK/'code/standard.py']+sorted((p.TASK/'code/frozen_calibration').glob('*'))
    save_json(lock,dict(files=[p.asset(f) for f in files],GT_HERO_or_historical_camera_for_reference_bootstrap=False,original_task_and_source_freezes_preserved=True))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['run','check']);ap.add_argument('--stage',choices=['all','audit','banks','cameras','hero','body','evaluate','report','check'],default='all');ap.add_argument('--group',choices=p.GROUPS);ap.add_argument('--video',choices=['004','005']);a=ap.parse_args()
    if not (p.TASK/'audit/INPUT_FREEZE.json').exists() and a.action=='run' and a.stage in ['audit','all']:
        from inputs import audit
        audit()
    p.verify();run.freeze_code();freeze()
    if a.action=='check':print('STANDARD_INPUT_SOURCE_AND_REFERENCE_PROTOCOL_CHECK_PASS');return
    if a.stage=='audit':print('FROZEN_INPUT_AUDIT_REUSED');return
    if not (p.TASK/'logs/TESTS.json').exists():
        with (p.TASK/'logs/TEST_RUN.log').open('w') as out:subprocess.run([sys.executable,str(p.TASK/'code/run_tests.py')],stdout=out,stderr=subprocess.STDOUT,check=True)
    assert p.read(p.TASK/'logs/TESTS.json')['status']=='PASS','TEST_GATE_FAILED'
    for stage in (['banks','cameras','hero','body','evaluate','report','check'] if a.stage=='all' else [a.stage]):
        if stage=='banks':
            from banks import build
            from bootstrap_references import build_one
            build(a.group,a.video)
            for g in p.GROUPS:
                for video in ['004','005']:
                    if a.group and a.group!=g or a.video and a.video!=video or p.inherited(g,video):continue
                    admission=p.OUT/g/video/'bank/ADMISSION.json'
                    if not admission.exists() or p.read(admission)['status']!='PASS':build_one(g,video)
        elif stage=='cameras':
            run.execute(stage,a.group,a.video)
            from complete_reference_inputs import main as complete_inputs
            complete_inputs(a.group,a.video)  # one fixed, source-bound input completion only
            run.execute(stage,a.group,a.video)
        elif stage=='hero':
            groups=[a.group] if a.group else p.GROUPS;selected=[v for v in p.views() if (not a.video or v['meta']['video']==a.video) and v['meta']['case'] in groups];pending=[]
            for g in groups:
                for vi in ['004','005']:
                    fit=[v for v in selected if v['meta']['case']==g and v['meta']['video']==vi and v['meta']['role']=='FIT']
                    for i,v in enumerate(fit):
                        supports=[fit[(i+k)%len(fit)] for k in [0,2,4,6]];ad=[p.OUT/g/vi/'camera'/q['meta']['id']/'ADMISSION.json' for q in supports]
                        if all(f.exists() and p.read(f)['status']=='PASS' for f in ad) and not (p.OUT/g/vi/'hero'/v['meta']['id']/'ADMISSION.json').exists():pending.append(v)
            if not pending:print('HERO_TERMINAL_OUTPUTS_REUSED');continue
            inv=p.TASK/'audit/HERO_INVOCATIONS';inv.mkdir(exist_ok=True);folder=inv/str(len(list(inv.iterdir()))).zfill(3);folder.mkdir()
            for name in ['HERO_TARGETS_FROZEN.json','HERO_MODEL_RECEIPT.json']:
                src=p.OUT/name
                if src.exists():shutil.copy2(src,folder/('PREVIOUS_'+name))
            save_json(folder/'SCOPE.json',dict(groups=groups,video=a.video,new_targets=[v['meta']['id'] for v in pending],scientific_parameters_changed=False))
            from adapters import load
            ns=load('hero_stage');proxy=SimpleNamespace(**{k:getattr(p,k) for k in dir(p) if not k.startswith('_')});proxy.GROUPS=groups;proxy.read=lambda f:p.read(f) if Path(f)!=p.TASK/'audit/SELECTED_VIEWS.json' else selected;ns['p']=proxy;ns['main']()
        elif stage in ['body','evaluate']:
            ready=[(g,vi) for g,vi in run.legal_instances() if all((p.OUT/g/vi/'hero'/v['meta']['id']/'ADMISSION.json').exists() and p.read(p.OUT/g/vi/'hero'/v['meta']['id']/'ADMISSION.json')['status']=='PASS' for v in p.instance_views(g,vi) if v['meta']['role']=='FIT')]
            if stage=='body':
                pending=[(g,vi) for g,vi in ready if (not a.group or a.group==g) and (not a.video or a.video==vi) and any(not (p.OUT/g/vi/'body'/arm/'TASK_PREDICTION_FROZEN.json').exists() and not (p.OUT/g/vi/'body'/arm/'FAILURE.json').exists() for arm in ['B1','B2'])]
                if not pending:print('BODY_TERMINAL_OUTPUTS_REUSED');continue
                log=p.TASK/'logs/BODY_BATCH.json'
                if log.exists():shutil.copy2(log,log.with_name('BODY_BATCH_BEFORE_RESUME_'+str(len(list(log.parent.glob('BODY_BATCH_BEFORE_RESUME_*'))))+'.json'))
            original=run.legal_instances;run.legal_instances=lambda:ready
            try:run.execute(stage,a.group,a.video)
            finally:run.legal_instances=original
        else:run.execute(stage,a.group,a.video)

if __name__=='__main__':main()
