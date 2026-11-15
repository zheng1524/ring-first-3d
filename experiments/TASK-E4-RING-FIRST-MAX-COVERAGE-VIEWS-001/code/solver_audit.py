"""Frozen solution diagnostics only: gradient competition, point drift, conditional Schur info."""
from register import *
def main():
 allrows=[];infos=[];points=[]
 for g in GROUPS:
  vs=load(N/'config'/(g+'_INITIAL_CAMERAS.json'));ext='_NATIVE005'if g=='G01'else'';r=load(N/'registration'/g/('JOINT_FULL6'+ext+'_FINAL.json'))
  if g=='G01':
   for i,v in enumerate(vs):
    p=N/'registration/G01/NATIVE005_EXTENSION'/(v['id']+'_INITIAL.json')
    if p.exists():vs[i]=load(p)
  B=Bundle(g,vs,'JOINT_FULL6',r['selected']);B.restore({k:{int(a)if k=='X'else a:np.array(b)for a,b in r[k].items()}for k in ['q','H','X']});A=np.zeros((6,6));blocks=collections.defaultdict(lambda:[np.zeros((6,3)),np.zeros((3,3))]);grgb=collections.defaultdict(lambda:np.zeros(6));gring={};selected=B.sel
  for c in selected:
   pc=B.pc[c];v=B.vs[c];C=B.C(c);cp=correspondence(C,K0,{k:B.ring[c].get(k,np.empty((0,2)))for k in ['inner','outer']});co=RingCost(pc,K0,cp,1/len(selected));res,J=co.values(B.q[c],B.H[v['video']],True);gring[c]=J[:,:6].T@res
  for o in B.obs:
   c=o['cid'];v=B.vs[c];pc=B.pc[c];C,dC=pc.get(B.q[c],B.H[v['video']],True);uv,JP,JX,z=project_dC(B.X[o['k']],C,K0,dC);err=(uv-o['uv'])/3.;rw=min(1.,1/max(np.linalg.norm(err),1e-15));w=o['w']*rw;grgb[c]+=w*(JP[:,:6]/3).T@err
   JT=JP[:,6:]/3 if v['video']=='005'else np.zeros((2,6));JX=JX/3;A+=w*JT.T@JT;blocks[o['k']][0]+=w*JT.T@JX;blocks[o['k']][1]+=w*JX.T@JX
  info=A.copy()
  for XX,CC in blocks.values():info-=XX@np.linalg.pinv(CC,rcond=1e-10)@XX.T
  sv=np.linalg.svd(info,compute_uv=False);rank=int((sv>max(sv[0]*1e-8,1e-12)).sum());infos.append(dict(group=g,shared005_RGB_Schur_rank=rank,singular_values=sv,conditional_on_fixed_local_cameras=True,full6_H_local_split_has_redundant_gauge=True,canonical_anchor_output='metrics/EXACT_SOURCE_GAUGE_CANONICALIZATION.json',prior_not_counted_as_RGB_information=True,no_absolute_pose_truth=True))
  for c in selected:
   a=gring[c];b=grgb[c];cos=float(a@b/(np.linalg.norm(a)*np.linalg.norm(b)))if np.linalg.norm(a)*np.linalg.norm(b)>1e-15 else None;allrows.append(dict(group=g,id=c,Ring_grad_scaled6=a,RGB_grad_scaled6=b,Ring_gradient_norm=float(np.linalg.norm(a)),RGB_gradient_norm=float(np.linalg.norm(b)),cosine=cos,conflict=cos is not None and cos<0,scope='actual Ceres inner typedTorus + RGB; outerV5Maskacceptance separately recorded',no_held_or_HERO_tuning=True))
  for k,x in B.X.items():points.append(dict(group=g,landmark_id=k,initial_mm=B.X0[k],final_mm=x,displacement_mm=float(np.linalg.norm(x-B.X0[k])),source='actual RGB identity notXYZNN'))
 table('metrics/RING_RGB_GRADIENT_COMPETITION.csv',allrows);save('metrics/RING_RGB_GRADIENT_COMPETITION.json',allrows);save('metrics/CONDITIONAL_RGB_SCHUR_INFORMATION.json',infos);table('metrics/COMMON_LANDMARK_DRIFT.csv',points);save('metrics/COMMON_LANDMARK_DRIFT.json',points);print('SOLVER_AUDIT_DONE',len(allrows),'cameras',len(points),'landmarks',flush=True)
if __name__=='__main__':main()
