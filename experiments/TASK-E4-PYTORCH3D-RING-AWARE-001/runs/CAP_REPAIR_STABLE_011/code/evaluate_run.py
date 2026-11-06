from evaluation_kernels import *

def main():
 for a in load(R/'assets_index/PREDICTIONS_FROZEN.json')['files']:assert sha(a['path'])==a['sha256'],a['path']
 summary=[];allper=[];records=[]
 for c in load(R/'config/CASE_LOCK.json'):
  n=c['name'];rr=np.load(R/'inputs'/n/'RING.npz');rs=scene(rr['V'],rr['F']);ring=trimesh.Trimesh(rr['V'],rr['F'],process=False);init=np.load(R/'inputs'/n/'INITIAL.npz');variants=[('INITIAL',0,R/'inputs'/n/'INITIAL.npz')]+[('CHECKPOINT',i,R/'local_results'/n/('STEP_%04d.npz'%i))for i in load(R/'config/PROTOCOL.json')['checkpoints']if i>0]+[('FINAL',300,R/'local_results'/n/'FINAL.npz')]
  for label,step,path in variants:
   if not path.exists():continue
   z=dict(np.load(path));rt=scene(z['V'],z['F']);g=geometry(c,z,rs,ring);per=view_metrics(c,z,rt,rs);fit=[x for x in per if x['role']=='FIT'];held=[x for x in per if x['role']!='FIT'];rec=dict(case=n,type=c['morphology'],label=label,step=step,path=str(path),FIT_IoU=float(np.mean([x['IoU']for x in fit])),HOLDOUT_IoU=float(np.mean([x['IoU']for x in held])),FIT_coverage=float(np.mean([x['Mask_coverage']for x in fit])),HOLDOUT_coverage=float(np.mean([x['Mask_coverage']for x in held])),**g);disp=np.linalg.norm(z['V']-init['V'],axis=1);rec['material_vertex_displacement_mm']=stats(disp)
   for prefix,subset in[('FIT',fit),('HOLDOUT',held)]:
    d=[x for x in subset if x.get('fixed_depth_N',0)>0];N=sum(x['fixed_depth_N']for x in d);rec[prefix+'_fixed_depth_N']=N;rec[prefix+'_depth_hit_N']=sum(x['depth_hit_N']for x in d);rec[prefix+'_depth_coverage']=sum(x['depth_hit_N']for x in d)/N if N else None;rec[prefix+'_raw_fixed_depth_cost']=sum(x['raw_fixed_depth_cost']*x['fixed_depth_N']for x in d)/N if N else None;rec[prefix+'_contour_MAE_px']=float(np.mean([x['contour_px']['MAE']for x in subset if x['contour_px']['MAE']is not None]))
   summary.append(rec);records.append(dict(**rec,per_view=per));allper.extend(dict(case=n,label=label,step=step,**v)for v in per)
  print('EVALUATED',n,flush=True)
 save('metrics/ALL_STAGE_SUMMARY.json',summary);table('metrics/ALL_STAGE_SUMMARY.csv',summary);save('metrics/ALL_STAGE_RESULTS.json',records);save('metrics/PER_VIEW_METRICS.json',allper);table('metrics/PER_VIEW_METRICS.csv',allper)
if __name__=='__main__':main()
