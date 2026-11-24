#!/usr/bin/env python3
import pandas as pd,numpy as np,json,pathlib
from pathlib import Path
R=Path('runs/m2c_corrective_completion'); O=Path('runs/m2d_w0_mvs_validation'); O.mkdir(parents=True,exist_ok=True)
s=pd.read_csv(R/'HERO_SUPPORT_SELECTION.csv'); c=pd.read_csv(R/'CAMERA_ROLE_ADMISSION.csv')
cmap={(r.group_id,f'{int(r.video_id):03d}',r.view):r for _,r in c.iterrows()}
D=pd.read_csv(R/'W0_79_VIDEO_RESULTS.csv'); dmap={(r.group_id,f'{int(r.video_id):03d}'):r for _,r in D.iterrows()}
def cams(g,v):
 p=Path(dmap[(g,v)].output_path); z=np.load(p/'camera_result.npz'); return {str(i):np.asarray(x,float) for i,x in zip(z['ids'],z['c2w'])}
rows=[]; cache={}
for _,r in s.iterrows():
 g,v=str(r.group_id),f'{int(r.video_id):03d}'; target=str(r.target_view); sups=[x for x in str(r.support_views).split(';') if x]
 arm=r.arm; t=cmap.get((g,v,target)); ok=bool(t is not None and (t.s0_eligible if arm=='S0' else t.s1_eligible))
 sok=all((cmap.get((g,v,x)) is not None and (cmap[(g,v,x)].s0_eligible if arm=='S0' else cmap[(g,v,x)].s1_eligible)) for x in sups)
 rel=True; note=''
 if len(sups)!=3: rel=False; note='N_SUPPORTS_NE_3'
 if (g,v) not in cache: cache[(g,v)]=cams(g,v)
 C=cache[(g,v)]
 try:
  baselines=[float(np.linalg.norm(C[target][:3,3]-C[x][:3,3])) for x in sups]
  if min(baselines)<1.0: rel=False; note='BASELINE_LT_1MM'
 except Exception: rel=False; note='MISSING_CAMERA'
 rows.append(dict(group_id=g,video_id=v,arm=arm,target_view=target,support_views=';'.join(sups),n_supports=len(sups),target_eligible=ok,supports_eligible=sok,relative_geometry_ok=rel,ready=bool(ok and sok and rel and len(sups)==3),original_status=r.status,reason=note))
out=pd.DataFrame(rows); out.to_csv(O/'admission/HERO_SUPPORT_SELECTION.csv',index=False)
# summary
print(out.groupby(['arm','ready']).size().to_string()); print('ready',out.ready.sum(),'videos',out[out.ready].groupby(['group_id','video_id']).ngroups,'groups',out[out.ready].group_id.nunique())
# unique input tuples
u=out[out.ready].drop_duplicates(['group_id','video_id','target_view','support_views'])
print('unique tuples',len(u)); pd.DataFrame([dict(group_id=g,video_id=v,target_view=t,support_views=s,arms=';'.join(sorted(set(u[(u.group_id==g)&(u.video_id==v)&(u.target_view==t)&(u.support_views==s)].arm)))) for g,v,t,s in u[['group_id','video_id','target_view','support_views']].itertuples(index=False)]).to_csv(O/'admission/TUPLE_VALIDATION.csv',index=False)
