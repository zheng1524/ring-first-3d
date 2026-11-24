#!/usr/bin/env python3
"""M2C corrective: final-point depth, endpoint jump-return, S1/S2 support scores."""
import json,itertools,sys
from pathlib import Path
import numpy as np,pandas as pd
WS=Path('/home/liu/ring_first_3d_workspace'); OUT=WS/'runs/m2c_corrective_completion'; A=WS/'runs/m2c_trajectory_admission/A_correctness'
sys.path.insert(0,str(WS/'tools')); from m2a_c3 import pair_graph
D=pd.read_csv(A/'W0_79_VIDEO_RESULTS.csv')
def Rdeg(A,B): return float(np.degrees(np.arccos(np.clip((np.trace(A[:3,:3].T@B[:3,:3])-1)/2,-1,1))))
def dist(A,B): return float(np.linalg.norm(A[:3,3]-B[:3,3]))
pos=[]; traj=[]; cam=[]; tgt=[]; sup=[]; scores=[]
for _,v in D.iterrows():
 g,vv=str(v.group_id),f'{int(v.video_id):03d}'; p=Path(v.output_path); w=np.load(p/'W0.npz'); cams=np.asarray(w['c2w'],float); ids=[str(x) for x in w['ids']]; adm=pd.read_csv(p/'admission.csv').set_index('view').loc[ids].reset_index()
 work=A/'work_A1'/g/vv if v.method=='A1' else A/'work_recovery'/v.method/g/vv
 try: tr,edges,comps=pair_graph(work)
 except Exception: tr=None;edges=[]
 # final points actual observed depth
 P=np.asarray(w['points'],float); Pt=np.asarray(w['point_track_ids'],int)
 for i,cid in enumerate(ids):
  xy=tr['xy'] if tr is not None else None
  obs=np.isfinite(xy[Pt,i,0]) if xy is not None else np.zeros(len(Pt),bool)
  z=((P-cams[i][:3,3])@cams[i][:3,:3])[obs,2] if obs.any() else np.array([])
  pos.append(dict(group_id=g,video_id=vv,view=cid,raw_frame=int(adm[adm.view==cid].raw_frame.iloc[0]),positive_depth_fraction=float((z>0).mean()) if len(z) else None,observed_point_count=int(len(z)),negative_count=int((z<=0).sum()),total_points=len(P)))
 # trajectory endpoint detection
 order=np.argsort([int(adm[adm.view==x].raw_frame.iloc[0]) for x in ids]); C=cams[order]; raw=np.asarray([int(adm[adm.view==x].raw_frame.iloc[0]) for x in ids])[order]; rank={int(x):i for i,x in enumerate(order)}
 n=len(C); t2=[]; t3=[]; t1=[]
 for k in range(1,n-1):
  dp=Rdeg(C[k-1],C[k]); dn=Rdeg(C[k],C[k+1]); de=Rdeg(C[k-1],C[k+1])
  tp=dist(C[k-1],C[k]); tn=dist(C[k],C[k+1]); te=dist(C[k-1],C[k+1])
  if dp>30 and dn>30 and de<15 and tp>5 and tn>5 and te<8: t2.append(int(raw[k]))
  if dp>30 and dn>30 and de>=15: t3.append(int(raw[k]))
 for k in range(1,n):
  if raw[k]-raw[k-1] > 1.8*np.median(np.diff(raw)): t1.append(int(raw[k]))
 cls='T2_ISOLATED_BRANCH' if t2 else 'T3_CONSECUTIVE_BRANCH' if t3 else 'T4_UNRESOLVED' if (v.new_w0_poses<10 or (adm.held_n<6).any()) else 'T1_SAMPLING_GAP' if t1 else 'T0_CONTINUOUS'
 traj.append(dict(group_id=g,video_id=vv,diagnostic_class=cls,n_isolated_t2=len(t2),t2_frames=';'.join(map(str,t2)),n_consecutive=len(t3),t3_frames=';'.join(map(str,t3)),n_large_gaps=len(t1),large_gap_frames=';'.join(map(str,t1)),max_adj_rotation_deg=float(v.max_adjacent_rotation_deg or 0),max_adj_translation_mm=float(v.max_adjacent_translation_mm or 0),repair_status='BRANCH_UNRESOLVED' if t2 else 'NO_REPAIR_NEEDED' if cls in ('T0_CONTINUOUS','T1_SAMPLING_GAP') else 'BRANCH_UNRESOLVED'))
 # eligibility + target/support
 edge={(int(e['i']),int(e['j'])):len(e['rows']) for e in edges}
 def edge_n(i,j): return edge.get((i,j),edge.get((j,i),0))
 for i,cid in enumerate(ids):
  a=adm.iloc[i]; pz=pos[-len(ids)+i]['positive_depth_fraction'] or 0
  s0=bool(a.pose_valid and a.cad_valid and a.ring_raw_mae<=2 and a.held_n>=20 and a.held_median<=4 and a.held_p95<=8 and a.big_error_fraction<=.1 and pz>=.95 and (i==0 or (a.rotation_to_previous_deg<=10 and a.center_to_previous_mm<=5)))
  branch_ok=not (cls=='T2_ISOLATED_BRANCH' and any(abs(int(a.raw_frame)-f)<1 for f in t2))
  s1=bool(a.pose_valid and a.cad_valid and a.ring_raw_mae<=4 and a.held_n>=4 and a.held_median<=8 and a.held_p95<=30 and pz>=.90 and branch_ok)
  cam.append(dict(group_id=g,video_id=vv,view=cid,raw_frame=int(a.raw_frame),legacy_status=a.admission_status,s0_eligible=s0,s1_eligible=s1,positive_depth=pz,trajectory_class=cls))
 # fixed 4 targets by raw quantiles
 order=np.argsort(adm.raw_frame.values); picks=sorted({int(order[int(round((len(order)-1)*q))]) for q in [0,.34,.67,1]})
 for ti in picks:
  cid=str(ids[ti]); raw_t=int(adm.raw_frame.iloc[ti]); tgt.append(dict(group_id=g,video_id=vv,target_view=cid,target_raw_frame=raw_t))
  for arm in ['S0','S1','S2']:
   elig=[j for j in range(len(ids)) if (cam[-len(ids)+j]['s0_eligible'] if arm=='S0' else cam[-len(ids)+j]['s1_eligible']) and j!=ti]
   if arm=='S0': pool=sorted(elig,key=lambda j:(abs(int(adm.raw_frame.iloc[j])-raw_t),-edge_n(ti,j)))[:3]
   elif arm=='S1':
    # same reliable trajectory class; nearest raw / graph-neighbor
    pool=sorted([j for j in elig if cam[-len(ids)+j]['trajectory_class'] in ('T0_CONTINUOUS','T1_SAMPLING_GAP')],key=lambda j:(abs(int(adm.raw_frame.iloc[j])-raw_t),-edge_n(ti,j)))[:3]
   else:
    cand=[j for j in elig if cam[-len(ids)+j]['trajectory_class'] in ('T0_CONTINUOUS','T1_SAMPLING_GAP')]
    best=None
    for comb in itertools.combinations(cand,3):
     qrgb=float(np.mean([edge_n(ti,j) for j in comb]))/50.; qov=float(np.mean([edge_n(a,b) for a,b in itertools.combinations(comb,2)]))/50.; qb=float(np.mean([dist(cams[ti],cams[j]) for j in comb]))/50.; qr=float(np.mean([Rdeg(cams[ti],cams[j])/45.+dist(cams[ti],cams[j])/25. for j in comb]))
     score=.45*qrgb+.25*qov+.20*qb-.10*qr
     if best is None or score>best[0]: best=(score,comb,dict(qrgb=qrgb,qoverlap=qov,qbaseline=qb,qrisk=qr,score=score))
    pool=list(best[1]) if best else []; scores.append(dict(group_id=g,video_id=vv,target_view=cid,arm=arm,score=best[0] if best else None,components=json.dumps(best[2]) if best else '{}',support_views=';'.join(str(ids[j]) for j in pool) if best else ''))
    sup.append(dict(group_id=g,video_id=vv,arm=arm,target_view=cid,support_views=';'.join(str(ids[j]) for j in pool),n_supports=len(pool),status='READY' if len(pool)>=3 else 'INSUFFICIENT_SUPPORTS'))
    continue
   sup.append(dict(group_id=g,video_id=vv,arm=arm,target_view=cid,support_views=';'.join(str(ids[j]) for j in pool),n_supports=len(pool),status='READY' if len(pool)>=3 else 'INSUFFICIENT_SUPPORTS'))
# write
OUT.mkdir(parents=True,exist_ok=True)
pd.DataFrame(pos).to_csv(OUT/'POSITIVE_DEPTH_VALIDATION.csv',index=False)
pd.DataFrame(traj).to_csv(OUT/'TRAJECTORY_PER_FRAME.csv',index=False)
pd.DataFrame(traj).to_csv(OUT/'TRAJECTORY_REPAIR_RESULTS.csv',index=False)
pd.DataFrame(cam).to_csv(OUT/'CAMERA_ROLE_ADMISSION.csv',index=False)
pd.DataFrame(tgt).to_csv(OUT/'HERO_TARGET_SELECTION.csv',index=False)
pd.DataFrame(sup).to_csv(OUT/'HERO_SUPPORT_SELECTION.csv',index=False)
pd.DataFrame(scores).to_csv(OUT/'HERO_SUPPORT_SCORE_COMPONENTS.csv',index=False)
print('pos',len(pos),'traj',pd.DataFrame(traj).diagnostic_class.value_counts().to_dict(),'targets',len(tgt),'supports',len(sup),'scores',len(scores))
print('S0 targets',sum(r['status']=='READY' for r in sup if r['arm']=='S0'),'S1',sum(r['status']=='READY' for r in sup if r['arm']=='S1'),'S2',sum(r['status']=='READY' for r in sup if r['arm']=='S2'))
