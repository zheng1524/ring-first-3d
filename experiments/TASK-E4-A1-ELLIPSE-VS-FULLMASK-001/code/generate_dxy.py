"""Exact official DXY-MID API; export pixel geometry only, never its mm result."""
from pathlib import Path
import sys,os,json,hashlib,time
R=Path(__file__).resolve().parents[1];DXY=Path('/home/liu/new-polyp-dxy');PREV=Path('/home/liu/ring_first_3d_e4_a1/experiments/TASK-E4-A1-COARSE-BODY-001')
sys.dont_write_bytecode=True
os.environ.update(CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def asset(p):return dict(path=str(p),sha256=sha(p),bytes=Path(p).stat().st_size)
def load(p):return json.loads(Path(p).read_text())
def clean(x):
    if isinstance(x,dict):return {str(k):clean(v)for k,v in x.items()}
    if isinstance(x,(list,tuple)):return [clean(v)for v in x]
    if hasattr(x,'tolist'):return clean(x.tolist())
    if isinstance(x,float)and not __import__('math').isfinite(x):return None
    return x
def save(name,x):(R/name).write_text(json.dumps(clean(x),ensure_ascii=False,indent=2)+'\n')
def guard(event,args):
    if event in ['socket.connect','socket.getaddrinfo']:raise PermissionError('OFFLINE_DXY_INPUT_GENERATION')
    if event=='import'and str(args[0]).split('.')[0]in ['torch','tensorflow']:raise PermissionError('NO_NEURAL_RUNTIME')
    if event!='open'or not isinstance(args[0],(str,bytes)):return
    p=Path(os.fsdecode(args[0])).resolve();mode=args[1]if isinstance(args[1],str)else'';flags=args[2]if len(args)>2 and isinstance(args[2],int)else 0;writing=any(k in mode for k in 'wax+')or flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC)
    if writing and str(p).startswith('/home/liu/')and not p.is_relative_to(R):raise PermissionError('WRITE_ONLY_TASK:'+str(p))
    if p.name.lower().startswith('gt_')or any(k in str(p).lower()for k in ['/gt_mapping','/private_gt/','/oracle/','/checkpoints/']):raise PermissionError('NO_GT:'+str(p))
    if any(p.is_relative_to(DXY/k)for k in ['outputs','data','validation']):raise PermissionError('NO_SAVED_DXY_PREDICTIONS:'+str(p))
sys.addaudithook(guard)
import numpy as np
CC={x['id']:x for x in load(Path('/home/liu/ring_first_3d_neural_e1/experiments/TASK-NEURAL-E1-PIPELINE-RECOVERY-001/provenance/INPUT_ELIGIBILITY.json'))['references']}
sys.path.insert(0,str(DXY/'src'))
from dxy_mid.pipeline import measure_files,VERSION
def main():
    assert load(R/'provenance/DXY_VERSION_AUDIT.json')['local_and_remote_commit_equal']
    prev=load(PREV/'config/PREREGISTERED.json');records=load(R/'provenance/DXY_GENERATED.json')if(R/'provenance/DXY_GENERATED.json').exists()else[]
    for cid in sorted({cid for x in prev['scenes'].values()for cid in x['A']+x['B']}):
        if any(x['source']==cid for x in records):continue
        c=CC[cid];rgb_sha=sha(c['RGB']);mask_sha=sha(c['Mask']);t0=time.monotonic();result=measure_files(c['RGB'],c['Mask'],inner_diameter_mm=float(c['ring'][1:]),source_id=hashlib.sha256((rgb_sha+'|'+mask_sha).encode()).hexdigest()[:24])
        keep=['version','Geometry','ring_valid','ring_reason','normal_Gate_pass','Q_conflict_recovery','strict_stable','accepted','candidate_generated','stability_review_pass','geometry_state','quality_class','reason','stability_flags','P_count','Q_count','X_count','body','branch','P_zero_occlusion_inference','coordinate_system','GT_read','history_prediction_fallback','processed_mask_sha256']
        rec=dict(source=cid,source_RGB=asset(c['RGB']),source_Mask=asset(c['Mask']),DXY_commit='75d58ca5b643fb4d8e0eb887b45ad0f056b0bb95',entrypoint='dxy_mid.pipeline.measure_files',VERSION=VERSION,image_dimensions=[640,360],input_coordinates='frozen archive 640x360, identity map to K',seconds=time.monotonic()-t0,quality={k:result.audit.get(k)for k in keep})
        candidate=result.candidate
        if candidate is not None:
            center=np.asarray(candidate.center_native);basis=np.asarray(candidate.basis_native);U,axes,V=np.linalg.svd(basis);rec.update(available=True,shape=candidate.shape,center_px=center,basis_px=basis,semiaxes_px=axes,angle_rad=float(np.arctan2(U[1,0],U[0,0])),candidate_provenance=candidate.provenance)
        else:rec.update(available=False,status='NOT_EVALUABLE_DXY_NO_SELECTED_GEOMETRY')
        assert sha(c['RGB'])==rgb_sha and sha(c['Mask'])==mask_sha;records.append(clean(rec));save('provenance/DXY_GENERATED.json',records);print('DXY',cid,'available',rec['available'],'quality',rec['quality']['quality_class'],'seconds',round(rec['seconds'],2),flush=True)
    save('provenance/DXY_RUNTIME_SOURCE_INDEX.json',[asset(p)for p in sorted((DXY/'src').rglob('*.py'))]);print('DXY_GENERATION_COMPLETE',len(records),flush=True)
if __name__=='__main__':main()
