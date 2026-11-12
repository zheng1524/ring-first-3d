"""Post-run self-consistency audit. Diagnostic counterfactuals are NOT new optimization arms."""
from refine import *
from ring020 import contours
from geometry021 import cpu_curve_distance
from scipy.spatial import cKDTree

def main():
 vv=load(M/'config/VIEWS.json');out=[];evidence=[]
 for group in GROUPS:
  v=next(v for v in vv if v['group']==group and v['role']=='FIT');C=canon_np(np.array(v['T']));K=np.array(v['K']);cad=RenderedCAD(v['ring_path']);used=cad.segments(C,K);aux=cad.last_audit;cc=contours(np.isfinite(cast(cad.cad,K,C,360,640)));ds={k:cKDTree(cc[k]).query(aux['UV'])[0]for k in ['inner','outer']};inner=ds['inner']<ds['outer'];raw={k:aux['edge_ids'][inner if k=='inner'else~inner]for k in ['inner','outer']};near={k:aux['edge_ids'][(inner if k=='inner'else~inner)&(aux['distance_to_rendered_boundary_px']<=1.)]for k in ['inner','outer']}
  for key in ['inner','outer']:
   for name,seg in [('ACTUAL_ACCEPTED',used[key]),('DIAGNOSTIC_RAW_FRONT_EDGES',raw[key]),('DIAGNOSTIC_RENDER_BAND_WITHOUT_PRIMITIVE_GATE',near[key])]:
    err=cpu_curve_distance(cc[key],cad.V,seg,C,K);out.append(dict(group=group,key=key,variant=name,N_render_boundary=len(cc[key]),CAD_segments_N=len(seg),distance_px=stats(err),render_boundary_fraction_farther2px=float(np.mean(err>2)),diagnostic_only_no_refit=name!='ACTUAL_ACCEPTED'))
   err=cpu_curve_distance(cc[key],cad.V,used[key],C,K);u=cc[key][np.argmax(err)];X=cad.V[raw[key]];p=projection(X.reshape(-1,3),C,K)[0].reshape(-1,2,2);a,b=p[:,0],p[:,1];d=b-a;t=np.clip(((u-a)*d).sum(1)/np.maximum((d*d).sum(1),1e-15),0,1);ee=np.linalg.norm(u-(a+t[:,None]*d),axis=1);j=int(np.argmin(ee));edge=raw[key][j];i=next(i for i,e in enumerate(aux['edge_ids'])if np.array_equal(e,edge));evidence.append(dict(group=group,view=v['id'],key=key,rendered_boundary_pixel=u,accepted_curve_gap_px=float(err.max()),nearest_original_front_edge_vertex_ids=edge,nearest_original_edge_gap_px=float(ee[j]),CAD_XYZ_mm=cad.V[edge],edge_midpoint_UV=aux['UV'][i],distance_midpoint_to_render_px=float(aux['distance_to_rendered_boundary_px'][i]),primitive_support=bool(aux['primitive_support'][i]),classification=['VISIBLE','OCCLUDED','UNKNOWN'][int(aux['states'][i])],not_evidence_of_physical_camera_error=True))
  print('CONTOUR_COMPLETENESS_AUDITED',group,flush=True)
 save('metrics/RENDER_COVERAGE_CAUSAL_AUDIT.json',out);table('metrics/RENDER_COVERAGE_CAUSAL_AUDIT.csv',out);save('metrics/RENDER_COVERAGE_GAP_LOCATIONS.json',evidence)
 old=load(M/'STAGE_GATE_DECISION.json')
 if not(M/'provenance/PRE_COMPLETENESS_VIDEO_GATE.json').exists():save('provenance/PRE_COMPLETENESS_VIDEO_GATE.json',old)
 gate=dict(status='PAUSED_FOR_HUMAN_DIAGNOSIS',stage2_completed=True,formal_four_group_comparison_completed=True,stage1_local_numeric_gate_pass=True,full_render_curve_completeness_pass=False,allow_photo_stage=False,photo_status='NOT_RUN_VIDEO_COMPLETENESS_GATE',reason='actual CAD visible-edge primitive-neighborhood association rejects necessary silhouette spans; renderer self-coverage P95 up to10px; do not promote proxy optimization or extend photos',old_stage1_not_overwritten=True,no_new_loss_or_threshold_after_evaluation=True,all_video_predictions_preserved=True)
 save('POST_VIDEO_CONTOUR_COMPLETENESS_GATE.json',gate);save('STAGE_GATE_DECISION.json',gate)
 print('PHOTO_STAGE_STOPPED_BY_REAL_SELF_CONSISTENCY_DEFECT',flush=True)
if __name__=='__main__':main()
