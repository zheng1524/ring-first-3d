from evaluation_kernels import *
def main():
 rows=[];allper=[]
 for c in load(R/'config/CASE_LOCK.json'):
  n=c['name'];rr=np.load(R/'inputs'/n/'RING.npz');rs=scene(rr['V'],rr['F']);ring=trimesh.Trimesh(rr['V'],rr['F'],process=False)
  for label,path in[('009_B',R.parent/'BODY_BASE_INIT_009/local_results'/n/'B_SELECTED.npz'),('009_C',R.parent/'BODY_BASE_INIT_009/local_results'/n/'C_SELECTED.npz'),('011_C',R/'inputs'/n/'INITIAL.npz')]:
   z=dict(np.load(path));g=geometry(c,z,rs,ring);per=view_metrics(c,z,scene(z['V'],z['F']),rs);fit=[x for x in per if x['role']=='FIT'];hold=[x for x in per if x['role']!='FIT'];rec=dict(case=n,label=label,FIT_IoU=float(np.mean([x['IoU']for x in fit])),HOLDOUT_IoU=float(np.mean([x['IoU']for x in hold])),FIT_Mask_coverage=float(np.mean([x['Mask_coverage']for x in fit])),**g);rows.append(rec);allper.extend(dict(case=n,label=label,**x)for x in per)
 save('metrics/INITIAL_COMPARISON.json',rows);table('metrics/INITIAL_COMPARISON.csv',rows);save('metrics/INITIAL_PER_VIEW.json',allper);table('metrics/INITIAL_PER_VIEW.csv',allper);print('INITIAL_EVAL_DONE')
if __name__=='__main__':main()
