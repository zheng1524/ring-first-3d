#!/usr/bin/env python3
"""M2C S0/S1/S2 admission and HERO target/support eligibility for all 79."""
import json,sys
from pathlib import Path
import numpy as np,pandas as pd,cv2
WS=Path('/home/liu/ring_first_3d_workspace'); OUT=WS/'runs/m2c_trajectory_admission'; A=OUT/'A_correctness'; B=OUT/'B_admission'; B.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(WS/'tools')); from m2a_c3 import pair_graph
D=pd.read_csv(A/'W0_79_VIDEO_RESULTS.csv'); POS=pd.read_csv(A/'POSITIVE_DEPTH_DIAGNOSTICS.csv')
POSMAP={(r.group_id,f'{int(r.video_id):03d}',r.view):r for _,r in POS.iterrows()}
cam=[]; srows=[]; targets=[]; supports=[]
for _,v in D.iterrows():
 g,vv=str(v.group_id),f'{int(v.video_id):03d}'; p=Path(v.output_path); adm=pd.read_csv(p/'admission.csv'); meta=json.loads((Path(p)/'PREPARED.json').read_text()) if (Path(p)/'PREPARED.json').exists() else json.loads((WS/'runs/m1_final_39/prepared'/f'{g}_{vv}'/'PREPARED.json').read_text())
 # support graph
 try: tr,edges,comps=pair_graph(OUT/'A_correctness/work_A1'/g/vv if v.method=='A1' else OUT/'A_correctness/work_recovery'/v.method/g/vv)
 except Exception: tr,edges,comps=None,[],[]
 sup={i:set() for i in range(len(adm))}
 for e in edges:
  if len(e.get('rows',[]))>=12:
   sup[int(e['i'])].add(int(e['j'])); sup[int(e['j'])].add(int(e['i']))
 adm=adm.reset_index(drop=True)
 flags=[]
 for i,r in adm.iterrows():
  pos=POSMAP.get((g,vv,str(r.view))); pdok=float(pos.positive_depth) if pos is not None and pd.notna(pos.positive_depth) else 0.0
  numerical=bool(r.pose_valid and r.cad_valid and np.isfinite(r.ring_raw_mae))
  s0=numerical and (r.ring_raw_mae<=2.0) and (r.held_n>=20) and (r.held_median<=4.0) and (r.held_p95<=8.0) and (r.big_error_fraction<=.1) and (pd.notna(r.rotation_to_previous_deg) and r.rotation_to_previous_deg<=10 or i==0) and (pd.notna(r.center_to_previous_mm) and r.center_to_previous_mm<=5 or i==0) and pdok>=.99
  s1=numerical and (r.ring_raw_mae<=3.0) and (r.held_n>=6) and (r.held_median<=6.0) and (r.held_p95<=20.0) and (r.big_error_fraction<=.25) and pdok>=.95
  s2=s1 and len(sup.get(i,set()))>=2
  cam.append(dict(group_id=g,video_id=vv,view=r.view,raw_frame=r.raw_frame,legacy_admission_status=r.admission_status,legacy_reasons=r.admission_reasons,
   numerical_validity=numerical,trajectory_quality=('T0' if pd.notna(r.rotation_to_previous_deg) and r.rotation_to_previous_deg<=30 else 'T1_OR_T2'),
   geometry_quality=('GOOD' if r.ring_raw_mae<=2 and r.held_median<=4 else 'LIMITED' if r.ring_raw_mae<=3 and r.held_median<=6 else 'POOR'),
   evidence_sufficiency=('STRONG' if r.held_n>=20 else 'LIMITED' if r.held_n>=6 else 'INSUFFICIENT'),
   positive_depth=pdok,support_count=len(sup.get(i,set())),s0_eligible=bool(s0),s1_eligible=bool(s1),s2_eligible=bool(s2),
   cross_video_matching_eligible=bool(s1),cross_video_anchor_eligible=bool(s0),hero_target_eligible=bool(s1),hero_support_eligible=bool(s2),
   body_contour_eligible=bool(s1),body_depth_eligible=False))
  flags.append((bool(s0),bool(s1),bool(s2),pos))
 # fixed 4 target identities from all cameras, independent of strategy
 order=np.argsort(adm.raw_frame.values); picks=sorted({int(order[int(round((len(order)-1)*q))]) for q in [0,.34,.67,1]})
 for tj in picks:
  raw=int(adm.raw_frame.iloc[tj]); tid=str(adm.view.iloc[tj])
  for arm in ['S0','S1','S2']:
   elig=flags[tj][{'S0':0,'S1':1,'S2':2}[arm]]
   targets.append(dict(group_id=g,video_id=vv,arm=arm,target_view=tid,target_raw_frame=raw,target_eligible=elig,selection_rule='fixed_raw_frame_quantiles',status=('ELIGIBLE' if elig else 'NOT_ELIGIBLE')))
   if not elig:
    supports.append(dict(group_id=g,video_id=vv,arm=arm,target_view=tid,support_views='',n_supports=0,status='INSUFFICIENT_SUPPORTS')); continue
   # rank other eligible cameras by graph support, then raw distance
   cands=[j for j in range(len(adm)) if j!=tj and flags[j][{'S0':0,'S1':1,'S2':2}[arm]]]
   cands.sort(key=lambda j:(-len(sup.get(tj,set())&{j}), -len(sup.get(j,set())), abs(int(adm.raw_frame.iloc[j])-raw)))
   ss=cands[:3]; supports.append(dict(group_id=g,video_id=vv,arm=arm,target_view=tid,support_views=';'.join(str(x) for x in adm.view.iloc[ss]),n_supports=len(ss),status=('READY' if len(ss)>=3 else 'INSUFFICIENT_SUPPORTS')))
pd.DataFrame(cam).to_csv(B/'CAMERA_ROLE_ADMISSION.csv',index=False)
# eligibility summary
el=pd.DataFrame(cam)[['group_id','video_id','view','raw_frame','s0_eligible','s1_eligible','s2_eligible']]
el.to_csv(B/'S0_S1_S2_ELIGIBILITY.csv',index=False)
pd.DataFrame(targets).to_csv(B/'HERO_TARGET_SELECTION.csv',index=False)
pd.DataFrame(supports).to_csv(B/'HERO_SUPPORT_SELECTION.csv',index=False)
# execution placeholders are explicit; no fake inference
pd.DataFrame([dict(group_id=g,video_id=v,arm=a,status='NOT_EXECUTED_RESOURCE',reason='HERO 4GB checkpoint + 6GB GPU shared; not executed in this run',n_targets=0) for g,v in D[['group_id','video_id']].itertuples(index=False) for a in ['S0','S1','S2']]).to_csv(B/'HERO_EXECUTION_RESULTS.csv',index=False)
pd.DataFrame([dict(group_id=g,video_id=v,arm=a,status='NOT_EXECUTED_DEPENDENCY_HERO',reason='no HERO depth available') for g,v in D[['group_id','video_id']].itertuples(index=False) for a in ['S0','S1','S2']]).to_csv(B/'BODY_EXECUTION_RESULTS.csv',index=False)
# empty metrics with explicit statuses
pd.DataFrame(columns=['group_id','video_id','arm','target_view','metric','value','status']).to_csv(B/'HERO_SURFACE_METRICS.csv',index=False)
pd.DataFrame(columns=['group_id','video_id','arm','metric','value','status']).to_csv(B/'BODY_METRICS.csv',index=False)
pd.DataFrame(columns=['group_id','video_id','arm','metric','value','status']).to_csv(B/'HOLDOUT_METRICS.csv',index=False)
pd.DataFrame(columns=['group_id','video_id','arm','metric','value','status']).to_csv(B/'GT_METRICS.csv',index=False)
summary=[]
for arm in ['S0','S1','S2']:
 sub=pd.DataFrame(cam); col=arm.lower()+'_eligible'; summary.append(dict(arm=arm,eligible_cameras=int(sub[col].sum()),videos_with_any=int(sub.groupby(['group_id','video_id'])[col].any().sum()),targets_ready=int((pd.DataFrame(targets).query('arm==@arm').status=='ELIGIBLE').sum()),supports_ready=int((pd.DataFrame(supports).query('arm==@arm').status=='READY').sum())))
pd.DataFrame(summary).to_csv(B/'ADMISSION_SUMMARY.csv',index=False)
print(pd.DataFrame(summary).to_string(index=False))
