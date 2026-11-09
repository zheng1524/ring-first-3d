"""Freeze all predictions and Ring scale BEFORE accessing any Blender geometry."""
from common import *
from audit_models import audit
from publish import link
import shutil

def main():
 assert(R/'provenance/PHASE_B_PREDICTIONS_FROZEN.json').exists();cases=load(R/'config/CASE_LOCK.json');stalk=load(R/'config/PROTOCOL.json')['phase_B']['cases'];models=[];files=[];scales=[];native=[]
 for c in cases:
  n=c['name'];ring=np.load(R/'inputs'/n/'RING.npz');inner=2*float(np.linalg.norm(ring['V'][:,:2],axis=1).min());true={'R5':5.,'R10':10.}[c['ring']];factor=true/inner;assert abs(factor-1)<1e-5,'Unexpected metric mismatch; no GT evaluation';scales.append(dict(case=n,diameter_true_mm=true,CAD_measured_inner_mm=inner,recovery_factor=factor,applied_factor=1.,already_metric=True,source=asset(R/'inputs'/n/'RING.npz')))
  for arm in ['Init-A','Init-B','Init-C']:
   for stage in ['INITIAL','FINAL']:
    path=R/'initializations'/n/(arm+'.npz')if stage=='INITIAL'else R/'arms'/arm/'local_results'/n/'FINAL.npz';label=arm+'_'+stage;models.append(dict(case=n,label=label,source=str(path)));files.append(dict(asset(path),case=n,label=label));sc=load(R/'metrics/scores'/(n+'_'+label+'.json'));native.append(dict(case=n,label=label,FIT_IoU=sc['mean']['FIT']['IoU'],HOLDOUT_IoU=sc['mean']['UPDATE_HOLDOUT']['IoU']))
  if n in stalk:
   for arm in ['Stalk-A','Stalk-B','Stalk-C']:
    path=R/'arms'/arm/'local_results'/n/'FINAL.npz'
    if not path.exists():continue
    label=arm;models.append(dict(case=n,label=label,source=str(path)));files.append(dict(asset(path),case=n,label=label));sc=load(R/'metrics/scores'/(n+'_'+label+'_FINAL.json'));native.append(dict(case=n,label=label,FIT_IoU=sc['mean']['FIT']['IoU'],HOLDOUT_IoU=sc['mean']['UPDATE_HOLDOUT']['IoU']))
 save('metrics/RING_SCALE_VALIDATION.json',scales);save('metrics/NATIVE_SUMMARY.json',native);save('config/EVAL_MODELS.json',models)
 if not(R/'provenance/ALL_PREDICTIONS_AND_SCALE_FROZEN_BEFORE_GT.json').exists():save('provenance/ALL_PREDICTIONS_AND_SCALE_FROZEN_BEFORE_GT.json',dict(epoch=time.time(),files=files,scale=asset(R/'metrics/RING_SCALE_VALIDATION.json'),selection=asset(R/'config/PHASE_A_SELECTED.json'),actual_prediction_models=len(files),target_prediction_models=81,GT_opened=False,permission='user permits per-prediction scale-fixed rigid ICP after prediction freeze',no_more_optimizer_updates=True))
 frozen=load(R/'provenance/ALL_PREDICTIONS_AND_SCALE_FROZEN_BEFORE_GT.json')
 for f in frozen['files']:assert sha(f['path'])==f['sha256']
 validity=[]
 for m in models:
  n=m['case'];link(Path(m['source']),R/'local_results/metric'/n/(m['label']+'.npz'));g=audit(n,Path(m['source']));g['label']=m['label'];validity.append(g)
 save('metrics/POST_GEOMETRY_VALIDITY.json',validity)
 # No geometry or author dimensions are accessed before the above marker.
 old=REPO/'experiments/TASK-E4-PYTORCH3D-014';sources=load(old/'evaluation_only/GT_SOURCE_LOCK.json');save('evaluation_only/GT_SOURCE_LOCK.json',sources);save('provenance/GT_FIRST_ACCESS.json',dict(epoch=time.time(),prediction_freeze=asset(R/'provenance/ALL_PREDICTIONS_AND_SCALE_FROZEN_BEFORE_GT.json'),source_lock=asset(old/'evaluation_only/GT_SOURCE_LOCK.json'),not_used_for_selection=True))
 gtvalid=[]
 for c in cases:
  n=c['name'];src=old/'evaluation_only'/n/'ORIGINAL_BLENDER_GT_MM.npz'
  if not src.exists():gtvalid.append(dict(case=n,GT_self_intersections_N=None,status='NOT_EVALUABLE_MISSING_GT'));continue
  link(src,R/'evaluation_only'/n/'ORIGINAL_BLENDER_GT_MM.npz');a=np.load(src);from safe_geometry import self_intersections
  tm=trimesh.Trimesh(a['V'],a['F'],process=False);gtvalid.append(dict(case=n,source=asset(src),GT_self_intersections_N=self_intersections(a['V'],a['F'])['intersections'],watertight=bool(tm.is_watertight),winding=bool(tm.is_winding_consistent)))
 save('metrics/GT_VALIDITY.json',gtvalid);print('EVALUATION_PREPARED',len(models),flush=True)
if __name__=='__main__':main()
