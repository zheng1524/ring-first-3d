from refine import *
from conics_init import candidates,fit_ellipse,mid_for
from scipy.spatial import cKDTree
import types,importlib

def lookat(c):
 c=np.array(c,dtype=float);z=-c/np.linalg.norm(c);x=np.cross(z,[0,0,1]);x=x/np.linalg.norm(x)if np.linalg.norm(x)>1e-8 else np.array([1.,0,0]);C=np.eye(4);C[:3,:3]=np.c_[x,np.cross(z,x),z];C[:3,3]=c;return C

def main():
 guard_fit();vv=load(M/'config/VIEWS.json');v0=vv[0];cad=RenderedCAD(v0['ring_path']);rho=np.linalg.norm(cad.V[:,:2],axis=1);radius=(rho.min()+rho.max())/2;K=np.array(v0['K']);ttheta=np.linspace(0,2*np.pi,720,endpoint=False);X=np.c_[radius*np.cos(ttheta),radius*np.sin(ttheta),np.zeros(720)];synth=[]
 mod=types.ModuleType('dxy_mid');mod.__path__=['/home/liu/new-polyp-dxy/src/dxy_mid'];sys.modules.setdefault('dxy_mid',mod);recover=importlib.import_module('dxy_mid._engine.ring_component').recover
 for depth in [35.,50.]:
  for tilt in [10.,35.,55.,70.]:
   theta=np.deg2rad(tilt);C=lookat([depth*np.sin(theta),0,depth*np.cos(theta)]);uv=projection(X,C,K)[0];e=fit_ellipse(uv);cs=candidates(e,K,radius,C);err=[np.linalg.norm(c['C'][:3,3]-C[:3,3])for c in cs];pixel=[float(cKDTree(projection(X,c['C'],K)[0]).query(uv)[0].mean())for c in cs];z=cast(cad.cad,K,C,360,640);labels=np.where(np.isfinite(z),2,0).astype(np.uint8);rgb=np.full((360,640,3),120,np.uint8);rgb[labels==2]=15;cv2.setRNGSeed(20261112);np.random.seed(20261112);dxy,payload=recover(labels,rgb[:,:,::-1],10.);mid=dxy.get('centerline');miderr=None;centererr=None
   if mid:
    from ring020 import ellipse_points
    pm=ellipse_points(mid,ttheta);miderr=float(cKDTree(pm).query(uv)[0].mean());mc=candidates(mid,K,radius,C);centererr=min([np.linalg.norm(c['C'][:3,3]-C[:3,3])for c in mc],default=None)
   synth.append(dict(depth_mm=depth,tilt_deg=tilt,known_C=C,conics_candidate_N=len(cs),best_known_circle_center_error_mm=min(err,default=None),best_circle_projection_error_px=min(pixel,default=None),DXY_Mid_valid=mid is not None,Mid_to_true_centerline_MAE_px=miderr,Mid_Conics_center_bias_mm=centererr,Mid_is_strong_loss=False));print('SYNTHETIC_CIRCLE',depth,tilt,min(err,default=None),miderr,flush=True)
 save('metrics/CONICS_SYNTHETIC_MID_AUDIT.json',synth);table('metrics/CONICS_SYNTHETIC_MID_AUDIT.csv',synth)
 regression=[];old=load(P/'geometric_pose_optimization/metrics/CAD_VISIBILITY_SWITCH_CAUSES.json');jac=[];runs=[]
 for group in GROUPS:
  v=next(v for v in vv if v['group']==group and v['role']=='FIT');p=Problem([v],True);q=np.zeros(6)
  for part in ['inner','outer','SIFT','prior','all']:
   J=p.jac(q,part)
   for h in [.001,.0001,.00001]:
    F=np.stack([(p.fun(q+np.eye(6)[j]*h,part)-p.fun(q-np.eye(6)[j]*h,part))/(2*h)for j in range(6)],1);rel=float(np.linalg.norm(J-F)/max(np.linalg.norm(J),np.linalg.norm(F),1e-12));jac.append(dict(group=group,part=part,h=h,N=len(J),relative=rel,pass_local=rel<.001 or np.linalg.norm(J-F)<1e-5))
  hist=next(a for a in old if a['group']==group);snapshots=[]
  for sgn in [0,1,-1]:
   u=q+np.eye(6)[hist['axis']]*hist['h']*sgn;C=canon_np(p.C(tt(u),v).detach().numpy());p.cads[v['ring_path']].segments(C,np.array(v['K']));au=p.cads[v['ring_path']].last_audit;lookup={tuple(e):int(s)for e,s in zip(au['edge_ids'],au['states'])};snapshots.append({','.join(map(str,e['CAD_vertex_ids'])):lookup.get(tuple(e['CAD_vertex_ids']),2)for e in hist['changed_edges']})
  regression.append(dict(group=group,axis=hist['axis'],h=hist['h'],states_base_plus_minus=snapshots,no_MISS_automatic_visible=True,states=['VISIBLE','OCCLUDED','UNKNOWN'],repaired_old_edge_states_stable=snapshots[0]==snapshots[1]==snapshots[2]))
  for method,ring in [('S0',False),('A2',True)]:
   r=solve(Problem([v],ring),group+'/'+method+'/'+v['id'],extra=dict(Stage1_same_formal_config=True));runs.append(dict(group=group,method=method,status=r['status'],before=r.get('initial_loss'),after=r.get('final_loss'),movement_mm=r.get('center_change_mm'),accepted=r.get('accepted_outer'),physical=r.get('physical')));print('ACTUAL_STAGE1_TRF',group,method,r.get('initial_loss'),r.get('final_loss'),flush=True)
 gate=all(a['best_known_circle_center_error_mm']is not None and a['best_known_circle_center_error_mm']<.01 and a['best_circle_projection_error_px']<.001 for a in synth)and all(a['pass_local']for a in jac)and all(r['status']=='FROZEN_NUMERIC_POSE'and r['after']<=r['before']+1e-9 and r['physical'][0]for r in runs)
 save('metrics/OLD_VISIBILITY_REGRESSION.json',regression);save('metrics/FIXED_CORRESPONDENCE_JACOBIAN.json',jac);table('metrics/FIXED_CORRESPONDENCE_JACOBIAN.csv',jac);save('metrics/STAGE1_ACTUAL_TRF_RUNS.json',runs);save('STAGE1_GATE.json',dict(pass_basic_correctness=gate,Mid_supervision='INITIALIZATION_ONLY',normal_correspondence_switching_allowed=True,actual_TRF_runs=len(runs),photo_stage_not_yet_authorized_by_results=True));print('STAGE1_GATE',gate,flush=True)
if __name__=='__main__':main()
