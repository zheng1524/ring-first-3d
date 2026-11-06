from common import *
from evaluate import pointcast
from scipy.ndimage import distance_transform_edt
import open3d as o3d

def main():
 results=load(R/'metrics/CASE_MODEL_RESULTS.json');bv=load(R/'metrics/BLENDER_GEOMETRY.json');pairs=[];maskrows=[];selected=[];inputs=[]
 for c in load(R/'config/CASE_LOCK.json'):
  name=c['name'];base=load(R/'inputs'/name/'BASE.json');ring=np.load(R/'inputs'/name/'RING.npz');rv=ring['V'];rs=scene(rv,ring['F']);sourcecases=[x for x in results if x['case']==name];summary={x['arm']:x for x in sourcecases}
  for arm in['A','B','C']:
   r=summary[arm];b=next(x for x in bv if x['case']==name and x['arm']==arm);r['nonadjacent_self_pair_N']=b['nonadjacent_self_pair_N'];r['CAD_triangle_pair_N']=b['Ring_intersection_pair_N'];r['finite_geometric_candidate']=bool(not r['Ring_collision']and not r['Ring_inside_body_N']and not b['nonadjacent_self_pair_N']and r['watertight']and r['components']==1)
   m=np.load(R/'inputs'/name/'INITIAL.npz'if arm=='A'else R/'local_results'/name/(arm+'_SELECTED.npz'));rt=scene(m['V'],m['F'])
   for v in c['views']:
    im=np.load(R/'inputs'/name/(v['id']+'.npz'));lab=im['labels'];polyp=lab==1;dt=distance_transform_edt(polyp);z=cast(rt,im['K'],im['T'],360,640);cz=cast(rs,im['K'],im['T'],360,640);pred=np.isfinite(z)&(z<cz)
    for region,sel in [('full',polyp),('thick_proxy',polyp&(dt>=.5*dt.max())),('thin_proxy',polyp&(dt<=.25*dt.max()))]:maskrows.append(dict(case=name,arm=arm,source=v['id'],role=v['role'],region=region,fixed_N=int(sel.sum()),hit_N=int((sel&pred).sum()),coverage=float((sel&pred).sum()/max(1,sel.sum())),posthoc_diagnostic_only=True,not_anatomical_head_stalk_GT=True,same_formula_all_types=True))
  for a,b in[('B','A'),('C','B')]:
   aa,bb=summary[a],summary[b];pairs.append(dict(case=name,type=c['morphology'],comparison=a+' minus '+b,FIT_IoU_delta=aa['FIT_IoU']-bb['FIT_IoU'],HOLDOUT_IoU_delta=aa['HOLDOUT_IoU']-bb['HOLDOUT_IoU'],HOLDOUT_coverage_delta=aa['HOLDOUT_coverage']-bb['HOLDOUT_coverage'],underground_vertex_N_A_or_B=bb['below_estimated_plane_vertex_N'],underground_vertex_N_after=aa['below_estimated_plane_vertex_N'],CAD_penetration_delta_mm=aa['Ring_max_penetration_mm']-bb['Ring_max_penetration_mm'],base_status=base['base_status'],formal_truncation=base['truncate_allowed'],GT_accuracy='NOT_EVALUABLE'))
  # This is an audit record of candidates; no new post-hoc optimizer/model choice is introduced.
  B=load(R/'local_results'/name/'B_SELECTED.json');C=load(R/'local_results'/name/'C_SELECTED.json');selected.append(dict(case=name,type=c['morphology'],physical_specimen=c['physical_specimen'],input_status='COMPLETE',old_P0_provenance=c['initialization'],base_status=base['base_status'],contact=base['contact_status'],base_truncate_allowed=base['truncate_allowed'],B_family=B['meta']['family'],B_parameter_N=len(B['p']),B_selection_status=B['selection_status'],B_geometry_valid=summary['B']['finite_geometric_candidate'],C_family=C['meta']['family'],C_parameter_N=len(C['p']),C_selection_status=C['selection_status'],C_geometry_valid=summary['C']['finite_geometric_candidate'],C_vs_B_holdout_IoU_delta=summary['C']['HOLDOUT_IoU']-summary['B']['HOLDOUT_IoU'],final_research_status='AWAITING_HUMAN_REVIEW_NOT_MAINLINE',model_ranking_using_GT=False))
  Q=np.cov((rv-rv.mean(0)).T);e,U=np.linalg.eigh(Q);n=U[:,0];rr=rv-rv.mean(0);d=np.linalg.norm(rr-(rr@n)[:,None]*n,axis=1).min()*2;nominal=float(c['ring'][1:]);assert abs(d-nominal)<.01;inputs.append(dict(case=name,type=c['morphology'],physical_specimen=c['physical_specimen'],physical_group=c['identity'],Ring_type=c['ring'],CAD_inner_diameter_mm=float(d),nominal_inner_diameter_mm=nominal,fit_views=[v['id']for v in c['views']if v['role']=='FIT'],heldout_views=[v['id']for v in c['views']if v['role']!='FIT'],source_native_depth_N=sum(v['HERO_source']is not None for v in c['views']),input_status='READABLE_FRAME_CORRECT_COORDINATE_MM_MATCHED',GT_used=False))
 save('metrics/CASE_MODEL_RESULTS_WITH_GEOMETRY.json',results);table('metrics/PAIRED_COMPARISONS.csv',pairs);table('metrics/MASK_REGION_COVERAGE.csv',maskrows);table('metrics/MODEL_SELECTION_RECORD.csv',selected);save('metrics/MODEL_SELECTION_RECORD.json',selected);table('metrics/CASE_IDENTITY_AND_SCALE.csv',inputs);save('metrics/CASE_IDENTITY_AND_SCALE.json',inputs)
 print('ADDITIONAL_METRICS_DONE')
if __name__=='__main__':main()
