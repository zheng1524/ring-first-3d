from common import *

def cosine(a,b):
 a=np.ravel(a);b=np.ravel(b);den=np.linalg.norm(a)*np.linalg.norm(b);return float(a@b/den)if den>1e-20 else None

def main():
 rows=[];folds=[];summary=load(R/'metrics/ALL_STAGE_SUMMARY.json');qa=load(R/'metrics/BLENDER_GEOMETRY.json');qidx={(x['case'],x['route'],x['label'],x['step']):x for x in qa}
 for x in summary:
  q=qidx.get((x['case'],x['route'],x['label'],x['step']));x.update(Blender_Ring_pair_N=None if q is None else q['Ring_triangle_pair_N'],Blender_nonadjacent_self_pair_N=None if q is None else q['nonadjacent_self_pair_N'])
 save('metrics/ALL_STAGE_WITH_BLENDER.json',summary);table('metrics/ALL_STAGE_WITH_BLENDER.csv',summary)
 for c in load(R/'config/PROTOCOL.json')['cases']:
  for route in['P','S']:
   folder=R/'local_results'/c/route
   for p in sorted(folder.glob('MECHANISM_*.npz')):
    z=np.load(p);sil=z['silhouette_gradient_per_mm'];ab=z['absolute_gradient_per_mm'];rel=z['relative_gradient_per_mm'];disp=z['actual_displacement_mm'];depth=ab+rel;rows.append(dict(case=c,route=route,step=int(p.stem.split('_')[-1]),stage=str(z['stage']),silhouette_gradient_norm_per_mm=float(np.linalg.norm(sil)),absolute_gradient_norm_per_mm=float(np.linalg.norm(ab)),relative_gradient_norm_per_mm=float(np.linalg.norm(rel)),shape_gradient_norm_per_mm=float(np.linalg.norm(z['prior_gradient_per_mm'])),silhouette_vs_depth_cosine=cosine(sil,depth),actual_displacement_norm_mm=float(np.linalg.norm(disp)),actual_displacement_max_mm=float(np.linalg.norm(disp,axis=1).max()),negative_raw_total_spatial_gradient_vs_displacement_cosine=cosine(-sil-depth-z['prior_gradient_per_mm'],disp),interpretation='spatial loss gradients before global/cap Jacobian and SGD momentum; actual executed displacement recorded separately'))
   q=[x for x in qa if x['case']==c and x['route']==route and x['nonadjacent_self_pair_N']>0];folds.append(dict(case=c,route=route,first_saved_self_intersection_step=min(x['step']for x in q)if q else None,first_saved_self_label=next((x['label']for x in sorted(q,key=lambda x:x['step'])),None)))
 save('metrics/LOSS_GRADIENT_MECHANISM.json',rows);table('metrics/LOSS_GRADIENT_MECHANISM.csv',rows);save('metrics/FIRST_SAVED_SELF_INTERSECTION.json',folds)
 finals=load(R/'metrics/FINAL_300_FIXED_DENOMINATOR.json');table('metrics/FINAL_300_FIXED_DENOMINATOR.csv',[{k:('NaN'if v is None else v)for k,v in x.items()}for x in finals]);print('POST_DIAGNOSTICS_DONE',len(rows))
if __name__=='__main__':main()
