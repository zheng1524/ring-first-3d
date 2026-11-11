"""All98 P0 cameras, real RGB metrics and unchanged native HERO proxies; P1 remains NaN."""
from geometric import *
from geometry021 import cpu_curve_distance
from evaluate020 import contour_stats,visibility_query
import geometry021
import collections

def main():
 assert not load(M/'config/JACOBIAN_GATE.json')['pass_required_geometric_J'];vv=load(M/'config/VIEWS.json');groups=load(P/'config/FOUR_GROUP_INPUTS.json');cad={g['group']:CADCurves(g['ring']['path'])for g in groups};body={g['group']:dict(np.load(g['bodies']['B2']['path']))for g in groups};body_s={k:scene(b['V'],b['F'])for k,b in body.items()};rows=load(M/'metrics/ALL_VIDEO_P0_METRICS.json')if(M/'metrics/ALL_VIDEO_P0_METRICS.json').exists()else[]
 for v in vv:
  if any(r['id']==v['id']for r in rows):continue
  a=np.load(v['cache']);K=np.array(v['K']);C=np.array(v['T']);lab=a['labels'];cc=cad[v['group']];z=cast(cc.cad,K,C,360,640);ring=np.isfinite(z);known=lab!=1;rp=ring&known;rt=lab==2;rb=cast(body_s[v['group']],K,C,360,640);bp=np.isfinite(rb)&(~np.isfinite(z)|(rb<z-.05));polyp=lab==1;ev=np.load(M/'ring_evidence'/(v['id']+'.npz'));segs=cc.segments(canon_np(C),K);r=load(M/'inputs'/v['id']/'RGB_GEOMETRY.json');reproj={}
  for name,ms in [('SIFT_FIT',r['fit_pnp_inliers']),('SIFT_HELD',[m for m in r['matches']if m['role']=='FEATURE_HELD'])]:
   if ms:uv,zz=projection(np.array([m['X']for m in ms]),C,K);err=np.linalg.norm(uv-np.array([m['uv']for m in ms]),axis=1);reproj[name]=stats(err)
   else:reproj[name]=stats([])
  d={k:stats(cpu_curve_distance(ev[k],cc.V,segs[k],canon_np(C),K))for k in ['inner','outer']};row=dict(group=v['group'],id=v['id'],role=v['role'],capture_type='VIDEO_FRAME',P0_Ring_known_Mask_IoU=float((rp&rt).sum()/max(1,(rp|rt).sum())),P0_inner_px=d['inner'],P0_outer_px=d['outer'],P0_Ring_contour_px=contour_stats(rp,rt),P0_body_Mask_IoU=float((bp&polyp).sum()/max(1,(bp|polyp).sum())),P0_body_contour_px=contour_stats(bp,polyp),SIFT_FIT_P0_px=reproj['SIFT_FIT'],SIFT_HELD_P0_px=reproj['SIFT_HELD'],P0_rotation_orthogonality_max=float(np.max(abs(C[:3,:3].T@C[:3,:3]-np.eye(3)))),P1_status='NOT_RUN_JACOBIAN_GATE',P1_translation_mm=None,P1_rotation_deg=None,P1_Ring_IoU=None,P1_HERO_error_mm=None);rows.append(row)
  if v['id']in [next(x['id']for x in vv if x['group']==g and x['role']=='FIT')for g in GROUPS]:
   (M/'evaluation').mkdir(exist_ok=True);np.savez_compressed(M/'evaluation'/(v['id']+'.npz'),RGB=a['RGB'],labels=lab,ring_pred=ring,body_pred=bp,inner_CAD_segments=segs['inner'],outer_CAD_segments=segs['outer'])
  if len(rows)%20==0:print('P0_VIDEO_AUDIT',len(rows),flush=True)
 save('metrics/ALL_VIDEO_P0_METRICS.json',rows);table('metrics/ALL_VIDEO_P0_METRICS.csv',rows)
 geometry021.R=P;H=np.array(load(P/'results/B3.json')['T']);hero=[];pairs=[]
 for group in GROUPS:
  conf,ss=geometry021.group_data(group,H if group=='G01'else None);cc=cad[group];sourcepixels=sum(len(s['obs']['uv'])for s in ss);num=collections.Counter();dzs=[];areas=[]
  for s in ss:
   tri=s['V'][s['F']];areas.append(float(trimesh.triangles.area(tri).sum()))
   for t in ss:
    if s['id']==t['id']:continue
    r=visibility_query(s['X'],t['C'],t['obs']['K'],t['grid'],cc.cad);N=len(s['X']);num['fixed']+=N
    for key in ['known','supported','front','behind','cad_occluded','target_Ring_order_unreliable']:num[key]+=int(r[key].sum())
    num['unknown']+=int(N-r['known'].sum()-r['cad_occluded'].sum())
    dzs.extend(r['dz'][r['known']]);pairs.append(dict(group=group,source=s['id'],target=t['id'],source_video=s['video'],target_video=t['video'],N=N,known_N=int(r['known'].sum()),supported_N=int(r['supported'].sum()),front_N=int(r['front'].sum()),behind_N=int(r['behind'].sum()),cad_occluded_N=int(r['cad_occluded'].sum()),unknown_N=int(N-r['known'].sum()-r['cad_occluded'].sum()),depth_mm=stats(r['dz'][r['known']]),status='P0_UNCHANGED_NATIVE_HERO_ONLY'))
  hero.append(dict(group=group,sources_N=len(ss),native_TRUSTED_pixels_N=sourcepixels,cumulative_source_area_mm2=sum(areas),not_unique_anatomical_area=True,fixed_source_target_N=num['fixed'],known_N=num['known'],depth_mm=stats(dzs),visibility_categories=dict(num),P1='NOT_RUN_JACOBIAN_GATE',no_new_depth_inference=True));print('P0_HERO_AUDITED',group,flush=True)
 save('metrics/P0_NATIVE_HERO_PROXIES.json',hero);table('metrics/P0_NATIVE_HERO_PROXIES.csv',hero);save('metrics/P0_HERO_PER_PAIR.json',pairs);table('metrics/P0_HERO_PER_PAIR.csv',pairs)
 score=[]
 for g in GROUPS:
  rr=[r for r in rows if r['group']==g];hh=next(a for a in hero if a['group']==g);sr=dict(group=g,video_scope='004+005_shared004world'if g=='G01'else'004_only',target_video_views_N=len(rr),FIT_N=sum(r['role']=='FIT'for r in rr),HOLDOUT_N=sum(r['role']=='HOLDOUT'for r in rr),P1_actual_solver_runs=0,P1_success=0,P1_status='NOT_RUN_JACOBIAN_GATE',P1_translation_mm=None,P1_rotation_deg=None,P1_Ring_improvement_px=None,P1_SIFT_improvement_px=None,P1_HERO_improvement_mm=None)
  for role in ['FIT','HOLDOUT']:
   r0=[r for r in rr if r['role']==role];sr[role+'_P0_Ring_IoU']=float(np.mean([r['P0_Ring_known_Mask_IoU']for r in r0]));sr[role+'_P0_body_IoU']=float(np.mean([r['P0_body_Mask_IoU']for r in r0]));sr[role+'_P0_Inner_MAE_px']=float(np.mean([r['P0_inner_px']['MAE']for r in r0 if r['P0_inner_px']['N']]));sr[role+'_P0_Outer_MAE_px']=float(np.mean([r['P0_outer_px']['MAE']for r in r0 if r['P0_outer_px']['N']]))
  sr.update(P0_HERO_fixed_N=hh['fixed_source_target_N'],P0_HERO_known_N=hh['known_N'],P0_HERO_MAE_mm=hh['depth_mm']['MAE'],absolute_pose_accuracy='NOT_EVALUABLE_NO_GT');score.append(sr)
 save('metrics/FOUR_GROUP_POSE_OPTIMIZATION_SCORECARD.json',score);table('FOUR_GROUP_POSE_OPTIMIZATION_SCORECARD.csv',score);save('runtime/P0_AUDIT_COMPLETE.json',dict(epoch=time.time(),actual_views=98,HERO_sources=sum(h['sources_N']for h in hero),formal_optimization_runs=0));print('P0_AUDIT_COMPLETE',flush=True)
if __name__=='__main__':main()
