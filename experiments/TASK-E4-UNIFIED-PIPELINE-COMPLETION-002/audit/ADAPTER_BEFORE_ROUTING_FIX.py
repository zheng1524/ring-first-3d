"""Only instance selection and output plumbing around frozen 001 drivers."""
from pathlib import Path
from types import SimpleNamespace
import sys,difflib
import pipeline as p
from ring_first_3d.mainline.native.io import save_json

def load(name,group=None,video=None):
    sys.path.insert(0,str(p.OLD/'code'))
    # Ensure old adapters import the current task IO, never overwrite task001.
    sys.modules['pipeline']=p
    source=p.OLD/'code'/(name+'.py');original=source.read_text();code=original
    if name=='body_stage':
        assert original.count("video='004'")==1
        code=code.replace("video='004'","video=VIDEO")
    elif name=='hero_stage':
        code=code.replace('assert len(targets)<=32','assert len(targets)<=48')
        code=code.replace("T/'PROTOCOL_RF_ONLY.yaml'","T/'TASK.yaml'")
        hook="            save_json(pending/'MODEL_OUTPUT_KEYS.json',keys)"
        assert hook in code
        code=code.replace(hook,"""            aux={k:a.detach().float().cpu().numpy() for k,a in capture.last.items() if hasattr(a,'detach')}
            np.savez_compressed(pending/'OFFICIAL_AUXILIARY.npz',**aux)
            modelvalid=np.isfinite(aux['depth_masked'])&(aux['depth_masked']>0)
            np.savez_compressed(pending/'MODEL_DEPTH_VALIDITY.npz',valid=modelvalid)
            native_labels=np.load(pending/'NATIVE_RGB_LABELS.npz')['labels']
            assert not ((native_labels==1)&~modelvalid).any(),'MODEL_INVALID_POLYP_DEPTH'
"""+hook)
    elif name=='evaluate_stage':
        # The evaluator's math is unchanged; route one instance at a time.
        code=code.replace("/'004/", "/'"+str(video)+"/")
        code=code.replace("/'004'", "/VIDEO").replace("=='004'", "==VIDEO").replace("!='004'", "!=VIDEO").replace("video='004'", "video=VIDEO")
        code=code.replace("name=group+'_004'", "name=group+'_'+VIDEO")
        for file in ['PREDICTIONS_FROZEN_BEFORE_GT.json','GT_FIRST_ACCESS.json','BODY_SHAPE_METRICS_PARTIAL.json','BODY_SHAPE_METRICS.json','GT_EVALUATION_COMPLETE.json']:
            code=code.replace("OUT/'"+file+"'", "OUT/GROUP/VIDEO/'"+file+"'")
        for file in ['ACTUAL_BODY_METRICS.csv','PER_VIEW_METRICS.csv','GEOMETRY_METRICS.csv','DEPTH_METRICS.csv']:
            code=code.replace("T/'metrics/"+file+"'", "T/'metrics'/GROUP/VIDEO/'"+file+"'")
    out=p.TASK/'audit/driver_adapters'/(name+(('_'+group+'_'+video) if group else ''));out.mkdir(parents=True,exist_ok=True)
    (out/'ADAPTER.diff').write_text(''.join(difflib.unified_diff(original.splitlines(True),code.splitlines(True),fromfile=str(source),tofile=name+'_instance_adapter.py')))
    (out/'driver.py').write_text(code);save_json(out/'SOURCE.json',dict(original=p.asset(source),adapted=p.asset(out/'driver.py'),scope='Instance selection/output paths/auxiliary output retention only; scientific optimizer and evaluation kernels unchanged'))
    ns=dict(__name__='completion_'+name,__file__=str(out/'driver.py'),VIDEO=video,GROUP=group)
    exec(compile(code,str(out/'driver.py'),'exec'),ns)
    if name=='evaluate_stage':
        ns['p']=SimpleNamespace(**{k:getattr(p,k) for k in ['read','check_input','table','TASK','ROOT']},cases=lambda:[c for c in p.cases() if c['case']==group])
    return ns

def body(group,video,arm):
    assert not p.inherited(group,video),'Frozen reference training forbidden'
    vv=[v for v in p.instance_views(group,video) if v['meta']['role']=='FIT'];assert len(vv)==8
    for v in vv:
        root=p.OUT/group/video;cid=v['meta']['id']
        assert p.read(root/'camera'/cid/'ADMISSION.json')['status']=='PASS'
        assert p.read(root/'hero'/cid/'ADMISSION.json')['status']=='PASS'
    load('body_stage',group,video)['main'](group,arm,'train')

def hero():return load('hero_stage')['main']()

def freeze_all():
    records=[]
    for c in p.cases():
        for video in ['004','005']:
            root=p.OUT/c['case']/video
            for arm in ['B0','B1','B2']:
                if p.inherited(c['case'],video):src=Path(c['initial']['path']) if arm=='B0' else p.inherited_file(c['case'],video,'body/'+arm+'/FINAL.npz')
                else:src=Path(c['initial']['path']) if arm=='B0' else root/'body'/arm/'FINAL.npz'
                records.append(dict(group=c['case'],video=video,arm=arm,status='PASS' if src.exists() else 'NOT_RUN',path=str(src) if src.exists() else None,sha256=p.asset(src)['sha256'] if src.exists() else None,inherited=p.inherited(c['case'],video)))
            new=any((root/'body'/a/'TASK_PREDICTION_FROZEN.json').exists() for a in ['B1','B2']) and not p.inherited(c['case'],video)
            if new:
                for arm in ['B1','B2']:assert (root/'body'/arm/'TASK_PREDICTION_FROZEN.json').exists() or (root/'body'/arm/'FAILURE.json').exists()
                save_json(root/'PREDICTIONS_FROZEN_BEFORE_GT.json',dict(all_training_complete=True,GT_read=False,records=records[-3:]))
    save_json(p.OUT/'ALL_PREDICTIONS_FROZEN_BEFORE_GT.json',dict(all_new_training_complete=True,GT_read=False,records=records))

def evaluate(group,video):
    assert p.read(p.OUT/'ALL_PREDICTIONS_FROZEN_BEFORE_GT.json')['all_new_training_complete']
    assert not p.inherited(group,video)
    return load('evaluate_stage',group,video)['evaluate']()
