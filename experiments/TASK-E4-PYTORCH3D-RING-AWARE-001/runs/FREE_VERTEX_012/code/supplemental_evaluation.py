from common import *
from evaluate import area_samples,distance

def main():
 sources={x['case']:x for x in load(R/'evaluation_only/GT_SOURCE_LOCK.json')};rows=[]
 for c in load(R/'config/CASE_LOCK.json'):
  n=c['name'];initial=np.load(R/'inputs'/n/'INITIAL.npz');final=np.load(R/'local_results'/n/'FINAL.npz');F=initial['F'];edges=np.unique(np.sort(np.r_[F[:,[0,1]],F[:,[1,2]],F[:,[2,0]]],1),axis=0);L0=np.linalg.norm(initial['V'][edges[:,0]]-initial['V'][edges[:,1]],axis=1);L1=np.linalg.norm(final['V'][edges[:,0]]-final['V'][edges[:,1]],axis=1);rat=L1/np.maximum(L0,1e-20);entry=dict(case=n,edge_length_ratio_min=float(rat.min()),edge_length_ratio_max=float(rat.max()),supplemental_not_model_selection=True)
  for tag in ['C011','FINAL011','FINAL012']:
   p=R/'local_results/aligned'/n/(tag+'.npz');gt=R/'evaluation_only'/n/'ORIGINAL_BLENDER_GT_MM.npz';base=sources[n].get('author_base')
   if not p.exists()or not gt.exists():continue
   z=np.load(p);g=np.load(gt);gr=scene(g['V'],g['F']);pr=scene(z['V'],z['F_solid']);P=area_samples(z['V'],z['F_solid'],8192);G=area_samples(g['V'],g['F'],8192);rec=dict(**entry,label=tag,whole_solid_surface_Chamfer_mm=stats(np.r_[distance(gr,P),distance(pr,G)]),whole_solid_caveat='Includes inferred closure, unlike primary observation-eligible-surface metric; not a visible-surface accuracy claim')
   if base:
    normal=np.asarray(base['normal']);h=z['V']@normal+base['offset_mm'];rec.update(minimum_author_base_height_mm=float(h.min()),maximum_author_base_height_mm=float(h.max()),model_own_Z_span_in_author_direction_mm=float(np.ptp(h)),area_uniform_whole_solid_H95_mm=float(np.quantile(P@normal+base['offset_mm'],.95)),author_base_qualification=base['qualification'],height_caveat='Positive min height means missing base/stalk despite a possible correct apex height; negative means model extends below GT author base. No deployment-base accuracy certification.')
   rows.append(rec)
 save('metrics/BASE_AND_SURFACE_DIAGNOSTICS.json',rows);table('metrics/BASE_AND_SURFACE_DIAGNOSTICS.csv',rows)
 metrics=load(R/'metrics/BLENDER_GEOMETRIC_METRICS.json');idx={(x['case'],x['label']):x for x in rows};height=[]
 for x in metrics:
  d=idx.get((x['case'],x['label']));pred=None if d is None else d.get('area_uniform_whole_solid_H95_mm');gt=x.get('H95_GT_mm');height.append(dict(case=x['case'],label=x['label'],evaluation=x['evaluation'],definition='8192 area-uniform samples on complete model entity and complete original GT, same operator; inferred closure explicitly included as a model hypothesis',H95_GT_complete_mm=gt,H95_pred_complete_mm=pred,H95_complete_AE_mm=None if pred is None or gt is None else abs(pred-gt),H95_complete_relative_error=None if pred is None or gt in [None,0]else abs(pred-gt)/abs(gt),H95_pred_observation_eligible_mm=x.get('H95_pred_mm'),inferred_bottom_present=bool(np.load(R/'local_results/metric'/x['case']/(x['label']+'.npz'))['inferred_base_faces'].any()),height_qualification=x.get('base_status'),not_visible_surface_accuracy=True))
 save('metrics/REQUESTED_HEIGHT_METRICS.json',height);table('metrics/REQUESTED_HEIGHT_METRICS.csv',height)
 # Independent measurement summaries, always with the full nine-group denominator.
 m=load(R/'metrics/BLENDER_GEOMETRIC_METRICS.json');summ=[]
 for tag in ['C011','FINAL011','FINAL012']:
  selected=[x for x in m if x['label']==tag];valid=[x for x in selected if x['Dxy_AE_mm']is not None];errors=np.array([x['Dxy_AE_mm']for x in valid]);rel=np.array([x['Dxy_relative_error']for x in valid]);summ.append(dict(label=tag,target_N=9,independent_mesh_output_N=9,matched_Dxy_evaluation_N=len(valid),Dxy_median_absolute_relative_error=float(np.median(rel))if len(rel)else None,Dxy_MAE_mm=float(errors.mean())if len(errors)else None,Dxy_p95_absolute_error_mm=float(np.quantile(errors,.95))if len(errors)else None,Dxy_max_absolute_error_mm=float(errors.max())if len(errors)else None,Dxy_relative_p95=float(np.quantile(rel,.95))if len(rel)else None,strict_solid_IoU_evaluable_N=sum(x['IoU_3D']is not None for x in selected),occupancy_proxy_only_N=sum(x['occupancy_IoU_proxy']is not None and x['IoU_3D']is None for x in selected),height_status='conditional GT-author-base after pose-free rigid alignment',historical_measurement_fallback_N=0,GT_used_to_select_prediction=False))
 a={x['case']:x for x in m if x['label']=='FINAL011'};b={x['case']:x for x in m if x['label']=='FINAL012'};common=[n for n in a if a[n]['Dxy_AE_mm']is not None and b[n]['Dxy_AE_mm']is not None];paired=[dict(case=n,Dxy_AE_delta_mm=b[n]['Dxy_AE_mm']-a[n]['Dxy_AE_mm'],Chamfer_MAE_delta_mm=b[n]['Chamfer_MAE_mm']-a[n]['Chamfer_MAE_mm'],holdout_IoU_delta=b[n]['HOLDOUT_2D_IoU_original_cameras']-a[n]['HOLDOUT_2D_IoU_original_cameras'],no_historical_fusion=True)for n in common];save('metrics/MEASUREMENT_SUMMARY.json',summ);table('metrics/MEASUREMENT_SUMMARY.csv',summ);save('metrics/PAIRED_011_012.json',dict(target_N=9,common_N=len(common),pairs=paired,baseline='011 FINAL, approved upstream initialization; not a historical fused mesh or measurement fallback'));table('metrics/PAIRED_011_012.csv',paired)

if __name__=='__main__':main()
