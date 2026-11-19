"""Frozen-only independent metrics; same denominators and explicit missing Conics outputs."""
from refine import *
from geometry021 import cpu_curve_distance
from evaluate020 import contour_stats,visibility_query
from features019 import sampson
import geometry021,collections
METHODS=['P0','S0','A1','A2','A3']
FEATURE_XY={}
def feature_xy(cid):
 if cid not in FEATURE_XY:FEATURE_XY[cid]=np.load(M/'features'/(cid+'.npz'))['xy']
 return FEATURE_XY[cid]
def getpose(g,m,cid):
 r=load(M/'results'/g/m/cid/'FINAL.json');return None if r.get('pose')is None else np.array(r['pose'])

def main():
 for g in GROUPS:
  fr=load(M/'provenance'/(g+'_VIDEO_POSES_FROZEN.json'))
  for a in fr['files']:assert sha(a['path'])==a['sha256']
 save('provenance/ALL_VIDEO_CANDIDATES_FROZEN_BEFORE_EVALUATION.json',dict(epoch=time.time(),groups=[asset(M/'provenance'/(g+'_VIDEO_POSES_FROZEN.json'))for g in GROUPS],GT=False,held_optimization=False))
 vv=load(M/'config/VIEWS.json');vd={v['id']:v for v in vv};groups=load(P/'config/FOUR_GROUP_INPUTS.json');cad={g['group']:RenderedCAD(g['ring']['path'])for g in groups};bodies={g['group']:dict(np.load(g['bodies']['B2']['path']))for g in groups};body_sc={g:scene(a['V'],a['F'])for g,a in bodies.items()};rows=[]
 for v in vv:
  a=np.load(v['cache']);K=np.array(v['K']);lab=a['labels'];rgb=load(M/'inputs'/v['id']/'RGB_GEOMETRY.json');obs=np.load(M/'ring_evidence'/(v['id']+'.npz'));cc=cad[v['group']]
  for method in METHODS:
   rec=load(M/'results'/v['group']/method/v['id']/'FINAL.json');C=getpose(v['group'],method,v['id']);row=dict(group=v['group'],video=v['video'],id=v['id'],role=v['role'],method=method,status=rec['status'],C=C,new_local_pose=rec['status']=='FROZEN_NUMERIC_POSE',heldout_camera_unchanged=v['role']=='HOLDOUT',source_pixel_denominator=lab.size,center_change_mm=rec.get('center_change_mm',0. if method=='P0'or v['role']=='HOLDOUT'else None),rotation_change_deg=rec.get('rotation_change_deg',0. if method=='P0'or v['role']=='HOLDOUT'else None),initial_loss=rec.get('initial_loss'),final_loss=rec.get('final_loss'),accepted_outer=rec.get('accepted_outer'),depth_status=rec.get('depth_status','FROZEN_NATIVE_P0'))
   if C is None:
    row.update(Ring_IoU=None,inner_MAE_px=None,outer_MAE_px=None,body_IoU=None,SIFT_FIT=None,SIFT_HELD=None);rows.append(row);continue
   rd=cast(cc.cad,K,C,360,640);known=lab!=1;rp=np.isfinite(rd)&known;rt=lab==2;bd=cast(body_sc[v['group']],K,C,360,640);bp=np.isfinite(bd)&(~np.isfinite(rd)|(bd<rd-.05));pt=lab==1;ss,aux=cc.segments(canon_np(C),K,True);cur={k:stats(cpu_curve_distance(obs[k],cc.V,ss[k],canon_np(C),K))for k in ['inner','outer']}
   row.update(Ring_IoU=float((rp&rt).sum()/max(1,(rp|rt).sum())),inner_MAE_px=cur['inner']['MAE'],inner_P95_px=cur['inner']['p95'],outer_MAE_px=cur['outer']['MAE'],outer_P95_px=cur['outer']['p95'],inner_observations_N=cur['inner']['N'],outer_observations_N=cur['outer']['N'],Ring_contour_px=contour_stats(rp,rt),body_IoU=float((bp&pt).sum()/max(1,(bp|pt).sum())),body_contour_px=contour_stats(bp,pt),visibility_counts={k:int(np.sum(aux['states']==i))for i,k in enumerate(['VISIBLE','OCCLUDED','UNKNOWN'])})
   for tag,ms in [('SIFT_FIT',rgb['fit_pnp_inliers']),('SIFT_HELD',[m for m in rgb['matches']if m['role']=='FEATURE_HELD'])]:
    err=[];epi=[]
    if ms:
     uv,z=projection(np.array([m['X']for m in ms]),C,K);err=np.linalg.norm(uv-np.array([m['uv']for m in ms]),axis=1)
     for m in ms:
      ref=vd[m['descriptor_source']];Cr=getpose(ref['group'],method,ref['id'])
      if Cr is None:continue
      W=np.linalg.inv(C)@Cr;F=np.linalg.inv(K).T@skew_np(W[:3,3])@W[:3,:3]@np.linalg.inv(ref['K']);fid=m['source_feature_id'];u=feature_xy(ref['id'])[fid];epi.append(float(sampson(F,np.array([u]),np.array([m['uv']]))[0]))
    row[tag]=stats(err);row[tag+'_EPI_px']=stats(epi)
   if rec.get('data_information'):row.update(data_J_rank=rec['data_information']['rank'],condition_J=rec['data_information']['condition'])
   if v['id']==next(r['id']for r in vv if r['group']==v['group']and r['role']=='FIT'):
    d=M/'evaluation'/v['group'];d.mkdir(parents=True,exist_ok=True);np.savez_compressed(d/(method+'.npz'),RGB=a['RGB'],labels=lab,ring_pred=np.isfinite(rd),body_pred=bp)
   rows.append(row)
  if len(rows)%50==0:print('INDEPENDENT_VIDEO_METRICS',len(rows),flush=True)
 save('metrics/ALL_VIDEO_METHOD_METRICS.json',rows);table('metrics/ALL_VIDEO_METHOD_METRICS.csv',rows)
 # Counterfactual frozen-depth geometry; never claim depths were re-inferred.
 geometry021.R=P;H=np.array(load(P/'results/B3.json')['T']);ha=[];pair_rows=[];common=[]
 for group in GROUPS:
  conf,src=geometry021.group_data(group,H if group=='G01'else None);cc=cad[group]
  for method in METHODS:
   byscope={s:dict(N=0,known=0,supported=0,front=0,behind=0,cad=0,unknown=0,dz=[],common0=[],common1=[],gained=0,lost=0)for s in ['SAME_VIDEO','CROSS_VIDEO']}
   mapped={}
   for s in src:
    match=next((v for v in vv if s['id']==v['id']or s['id']in v.get('aliases',[])),None);Cnew=getpose(group,method,match['id'])if match else None
    if Cnew is None:mapped[s['id']]=None;continue
    D=Cnew@np.linalg.inv(s['C']);mapped[s['id']]=dict(C=Cnew,X=s['X']@D[:3,:3].T+D[:3,3])
   for s in src:
    for t in src:
     if s['id']==t['id']:continue
     scope='SAME_VIDEO'if s['video']==t['video']else'CROSS_VIDEO';B=byscope[scope];N=len(s['X']);B['N']+=N;r0=visibility_query(s['X'],t['C'],t['obs']['K'],t['grid'],cc.cad);a=mapped[s['id']];bb=mapped[t['id']]
     if a is None or bb is None:
      B['unknown']+=N;B['lost']+=int(r0['known'].sum());pair_rows.append(dict(group=group,method=method,scope=scope,source=s['id'],target=t['id'],fixed_N=N,known_N=0,status='MISSING_DERIVED_POSE_NO_FALLBACK'));continue
     r=visibility_query(a['X'],bb['C'],t['obs']['K'],t['grid'],cc.cad);kn=r['known'];co=kn&r0['known'];B['known']+=int(kn.sum());B['supported']+=int(r['supported'].sum());B['front']+=int(r['front'].sum());B['behind']+=int(r['behind'].sum());B['cad']+=int(r['cad_occluded'].sum());B['unknown']+=int(N-kn.sum()-r['cad_occluded'].sum());B['dz'].extend(r['dz'][kn]);B['common0'].extend(r0['dz'][co]);B['common1'].extend(r['dz'][co]);B['gained']+=int((kn&~r0['known']).sum());B['lost']+=int((~kn&r0['known']).sum());pair_rows.append(dict(group=group,method=method,scope=scope,source=s['id'],target=t['id'],fixed_N=N,known_N=int(kn.sum()),MAE_mm=stats(r['dz'][kn])['MAE'],status='POSE_CHANGED_DEPTH_NOT_REINFERRED'if method!='P0'else'FROZEN_NATIVE_P0'))
   for scope,B in byscope.items():
    if not B['N']:continue
    ha.append(dict(group=group,method=method,scope=scope,sources_N=len(src),fixed_N=B['N'],known_N=B['known'],support_fraction_fixed=B['supported']/B['N'],front_fraction_fixed=B['front']/B['N'],behind_fraction_fixed=B['behind']/B['N'],CAD_occluded_fraction_fixed=B['cad']/B['N'],unknown_fraction_fixed=B['unknown']/B['N'],known_depth_mm=stats(B['dz']),exact_common_N=len(B['common0']),common_before_mm=stats(B['common0']),common_after_mm=stats(B['common1']),gained_N=B['gained'],lost_N=B['lost'],pose_changed_depth_not_reinferred=method!='P0',not_physical_accuracy=True))
  print('COUNTERFACTUAL_HERO_DONE',group,flush=True)
 save('metrics/FROZEN_DEPTH_COUNTERFACTUAL.json',ha);table('metrics/FROZEN_DEPTH_COUNTERFACTUAL.csv',ha);save('metrics/FROZEN_DEPTH_PER_PAIR.json',pair_rows)
 summary=[]
 for g in GROUPS:
  for method in METHODS:
   for role in ['FIT','HOLDOUT']:
    allr=[r for r in rows if r['group']==g and r['method']==method and r['role']==role];rr=[r for r in allr if r.get('Ring_IoU')is not None];summary.append(dict(group=g,method=method,role=role,target_N=len(allr),numeric_N=len(rr),new_local_N=sum(r['new_local_pose']for r in rr),Ring_IoU=float(np.mean([r['Ring_IoU']for r in rr]))if rr else None,inner_MAE_px=float(np.mean([r['inner_MAE_px']for r in rr if r['inner_MAE_px']is not None]))if rr else None,outer_MAE_px=float(np.mean([r['outer_MAE_px']for r in rr if r['outer_MAE_px']is not None]))if rr else None,body_IoU=float(np.mean([r['body_IoU']for r in rr]))if rr else None,SIFT_FIT_MAE_px=float(np.mean([r['SIFT_FIT']['MAE']for r in rr if r.get('SIFT_FIT')and r['SIFT_FIT']['N']]))if rr else None,SIFT_HELD_MAE_px=float(np.mean([r['SIFT_HELD']['MAE']for r in rr if r.get('SIFT_HELD')and r['SIFT_HELD']['N']]))if rr else None,max_center_change_mm=max([r['center_change_mm']for r in rr],default=None),max_rotation_change_deg=max([r['rotation_change_deg']for r in rr],default=None),HOLDOUT_not_locally_refined=role=='HOLDOUT'))
 save('metrics/FOUR_GROUP_POSE_COMPARISON.json',summary);table('FOUR_GROUP_POSE_COMPARISON.csv',summary)
 # Same fixed method A2 was selected before observing held results.
 reasons=[]
 for g in GROUPS:
  rs=[r for r in rows if r['group']==g and r['method']=='A2'and r['role']=='FIT'];base={r['id']:r for r in rows if r['group']==g and r['method']=='P0'}
  if any(r['status']!='FROZEN_NUMERIC_POSE'for r in rs):reasons.append(g+':A2_SOLVER_MISSING')
  held=[(base[r['id']]['SIFT_HELD']['MAE'],r['SIFT_HELD']['MAE'])for r in rs if r.get('SIFT_HELD')and r['SIFT_HELD']['N']]
  if held:
   a,c=np.array(held).mean(0)
   if c-a>max(1.,.25*a):reasons.append(g+':A2_HELD_TRACK_DEGRADATION_REQUIRES_DIAGNOSIS')
  hh=[h for h in ha if h['group']==g and h['method']=='A2']
  for h in hh:
   b0=next(z for z in ha if z['group']==g and z['method']=='P0'and z['scope']==h['scope']);err0=b0['known_depth_mm']['MAE'];err=h['known_depth_mm']['MAE'];coverage0=b0['known_N']/b0['fixed_N'];coverage=h['known_N']/h['fixed_N']
   if err-err0>max(.5,.25*err0)and coverage0-coverage>.1:reasons.append(g+':A2_SEVERE_DEPTH_PROXY_CHANGE')
 gate=dict(stage2_completed=True,all_four_groups=True,selected_photo_method='A2_PREREGISTERED',allow_photo_stage=not reasons,reasons=reasons,status='VIDEO_STAGE_COMPLETE_PHOTO_AUTHORIZED'if not reasons else'PAUSED_FOR_HUMAN_DIAGNOSIS',no_HERO_reinference=True,not_strict_camera_certification=True);save('provenance/VIDEO_NUMERIC_GATE_LATEST.json',gate);save('STAGE_GATE_DECISION.json',load(M/'POST_VIDEO_CONTOUR_COMPLETENESS_GATE.json')if(M/'POST_VIDEO_CONTOUR_COMPLETENESS_GATE.json').exists()else gate);print('VIDEO_EVALUATION_GATE',gate,flush=True)
if __name__=='__main__':main()
