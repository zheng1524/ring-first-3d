"""All 39 groups, independent singles and genuinely reoptimized joint configurations."""
from fit import *
from base_plane import estimate
import argparse,time,traceback,shutil
def run_configuration(g,name,videos):
 out=T/'runs/results'/g/name;out.mkdir(parents=True,exist_ok=True);key=digest(dict(config=CFG,code=code_key(),videos=[sha(T/'runs/observations'/g/v['case']/'INDEX.json')for v in videos]))
 if(out/'RESULT.json').exists()and(out/'COMPLETE.json').exists()and read(out/'RESULT.json').get('cache_key')==key:
  for item in read(out/'COMPLETE.json')['files']:asset(item['path'],item['sha256'])
  return read(out/'RESULT.json')
 assert shutil.disk_usage(T).free>=CFG['reserve_bytes']
 fs=[f for v in videos for f in v['frames']];fitframes=[f for f in fs if f['role']=='FIT'];ss=[s for v in videos for s in v['sources']];p0,init=initialize(fitframes);b=np.zeros(len(ss));base=estimate(ss);t0=time.monotonic()
 problem=Problem(fitframes,ss,p0);p,b,logs=problem.solve(p0.copy(),b,CFG['alternations'],'FULL_PARENT');parent=p.copy();parentb=b.copy();plane=np.array(base['plane'])if base.get('apply')else None
 if plane is not None:
  problem=Problem(fitframes,ss,p0,plane);p,b,more=problem.solve(p,b,CFG['clipped_alternations'],'FIXED_BASE_CLIPPED');logs+=more
 V,F=body_mesh(p);PV,PF=body_mesh(parent);np.savez_compressed(out/'PARENT.npz',V=PV,F=PF,p=parent,b=parentb)
 np.savez_compressed(out/'FINAL_UNCUT.npz',V=V,F=F,p=p,b=b)
 geometry=dict(V=V,F=F,F_solid=F,inferred_base_faces=np.zeros(len(F),bool),original_face_ID=np.arange(len(F)))
 clipping_error=None
 if plane is not None:
  try:geometry=clip(V,F,plane)
  except Exception as e:
   save(out/'CLIPPING_FAILURE.json',dict(error=repr(e),p=p,plane=plane,stages=logs))
   raise ValueError('FINAL_CLIP_FAILED_no_uncut_BODY_substitution: '+repr(e))
 np.savez_compressed(out/'BODY.npz',**geometry,p=p,b=b)
 candidate_error=None
 if base.get('candidate')and plane is None:
  try:np.savez_compressed(out/'WEAK_BASE_CANDIDATE.npz',**clip(V,F,base['plane']))
  except Exception as e:candidate_error=repr(e)
 ev=evaluate(p,b,fs,ss,plane);before=evaluate(p0,np.zeros(len(ss)),fs,ss,None);parent_ev=evaluate(parent,parentb,fs,ss,None)
 save(out/'BASE.json',base);save(out/'STAGES.json',logs);save(out/'EVALUATION.json',dict(initial=before,parent=parent_ev,final=ev))
 np.savez_compressed(out/'CORRECTED_OBSERVATIONS.npz',raw_X=np.concatenate([s['raw_X']for s in ss])if ss else np.zeros((0,3)),corrected_X=np.concatenate([corrected_points(s['rays'],s['D'],b[i])for i,s in enumerate(ss)])if ss else np.zeros((0,3)),source_index=np.concatenate([np.full(len(s['D']),i)for i,s in enumerate(ss)])if ss else np.zeros(0,int))
 fitproj=[r['IoU']for r in ev['projections']if r['role']=='FIT'];heldproj=[r['IoU']for r in ev['projections']if r['role']=='HOLDOUT'];dn=sum(r['fixed_N']for r in ev['depth']);valid=sum(r['valid_N']for r in ev['depth'])
 result=dict(group=g,configuration=name,status='NUMERIC_FAILURE_CLIP'if clipping_error else'COARSE_INIT_COMPLETE',input_kind='DXY_MASK_HERO'if ss else'DXY_MASK_2D_ONLY',coordinate_frame=videos[0]['coordinate_frame'],videos=[v['case']for v in videos],cache_key=key,p=p,initial_p=p0,initialization=init,bias=[dict(source_id=s['meta']['source_id'],b_mm=b[i],bound_mm=CFG['bias_bound_mm'],uncertainty='conservative_prior_not_absolute_depth_truth',weight=problem.w[i])for i,s in enumerate(ss)],base_status=base['status'],base_applied=plane is not None,clipping_error=clipping_error,candidate_error=candidate_error,fit_IoU_mean=np.mean(fitproj)if fitproj else None,held_IoU_mean=np.mean(heldproj)if heldproj else None,depth_fixed_N=dn,depth_valid_N=valid,depth_invalid_N=dn-valid,source_N=len(ss),seconds=time.monotonic()-t0,stages=logs,scope='9 theta plus bounded source axial bias; no high-frequency update',real_GT='NOT_EVALUABLE',source_indices=[str(T/'runs/observations'/g/v['case']/'INDEX.json')for v in videos],method_success_not_shape_validation=True)
 save(out/'RESULT.json',result);save(out/'COMPLETE.json',dict(cache_key=key,files=[asset(out/n)for n in ['RESULT.json','PARENT.npz','FINAL_UNCUT.npz','BODY.npz','BASE.json','STAGES.json','EVALUATION.json','CORRECTED_OBSERVATIONS.npz']]))
 print('INIT',g,name,result['input_kind'],base['status'],round(result['seconds'],1),'IoU',result['held_IoU_mean'],flush=True);return result
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--group');args=parser.parse_args();rows=[]
 for idx in read(M4/'GROUP_INDEX.json')['groups']:
  g=idx['group']
  if args.group and g!=args.group:continue
  audit=T/'runs/inputs'/g/'AUDIT.json'
  if not audit.exists():continue
  a=read(audit);videos=[];failures=[]
  for v in a['videos']:
   try:videos.append(prepare_video(a,v))
   except Exception as e:failures.append(dict(configuration=v['case'],status='INPUT_FAILURE',error=repr(e),traceback=traceback.format_exc()))
  configurations=[(v['case'].rsplit('_',1)[-1],[v])for v in videos]
  allcases=[x['case']for x in a['all_video_states']]
  if len(allcases)>1:
   connected=[v for v in videos if v['coordinate_frame']=='COMMON']
   if len(connected)>=2:configurations.append(('JOINT',connected))
   else:failures.append(dict(configuration='JOINT',status='NOT_EXECUTABLE_COMMON_FRAME_OR_INPUT',reason='No fabricated identity/joint copy',missing=[c for c in allcases if c not in a['transforms']]))
  results=[]
  for name,vv in configurations:
   try:results.append(run_configuration(g,name,vv))
   except Exception as e:failures.append(dict(configuration=name,status='NUMERIC_OR_INPUT_FAILURE',error=repr(e),traceback=traceback.format_exc()))
  rec=dict(group=g,results=results,failures=failures,all_video_cases=allcases,joint_excluded_cases=[c for c in allcases if c not in [v['case']for name,vv in configurations if name=='JOINT'for v in vv]],audit_sha256=sha(audit));save(T/'runs/results'/g/'GROUP_RESULT.json',rec);rows.append(rec)
 save(T/'evidence'/('SMOKE_STATUS.json'if args.group else'FULL_STATUS.json'),rows)
if __name__=='__main__':main()
