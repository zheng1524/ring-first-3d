"""Pre-run physical, forward, yaw, derivative and real LM gate."""
from ceres_backend import *
from analytic_visibility import torus_polynomial
import open3d as o3d

def ray_scene(path):
 a=np.load(path);s=o3d.t.geometry.RaycastingScene(nthreads=1);s.add_triangles(o3d.core.Tensor(a['V'].astype(np.float32)),o3d.core.Tensor(a['F'].astype(np.uint32)));return s,a

def curve_visible(C,K,ringpath,n=1024):
 cr=curves(C,K,n);s,rv=ray_scene(ringpath);states=[];depth=[]
 for X in cr['X']:
  dd=X-C[:3,3];ll=np.linalg.norm(dd,axis=1);dd/=ll[:,None];q=s.cast_rays(o3d.core.Tensor(np.c_[np.broadcast_to(C[:3,3],dd.shape),dd].astype(np.float32)));hit=q['t_hit'].numpy();finite=np.isfinite(hit);st=np.full(n,2);st[finite&(abs(hit-ll)<.015)]=0;st[finite&(hit<ll-.015)]=1;states.append(st);depth.extend(((X-C[:3,3])@C[:3,:3])[:,2])
 return cr,np.array(states),float(min(depth))

def jac_check(cost,params,name):
 rs=np.empty(cost.num_residuals());J=[np.empty((cost.num_residuals()*len(p),))for p in params];assert cost.Evaluate(params,rs,J);J=[j.reshape(len(rs),-1)for j in J];rows=[]
 for k,p in enumerate(params):
  for h in [1e-4,1e-5,1e-6]:
   FD=[]
   for j in range(len(p)):
    old=p[j];p[j]=old+h;rp=np.empty(len(rs));assert cost.Evaluate(params,rp,None);p[j]=old-h;rm=np.empty(len(rs));assert cost.Evaluate(params,rm,None);p[j]=old;FD.append((rp-rm)/(2*h))
   fd=np.array(FD).T;ab=float(np.max(abs(fd-J[k])));rel=float(np.linalg.norm(fd-J[k])/max(np.linalg.norm(fd),1e-12));rows.append(dict(name=name,parameter_block=k,step=h,absolute=ab,relative=rel,PASS=ab<1e-5 or rel<1e-4))
 return rows

def main():
 checkfreeze('provenance/INPUTS_FROZEN.json');vv=load(N/'config/VIEWS.json');forward=[];jac=[];physical=[];checks=[]
 for v in vv:
  C=np.array(v['T']);K=np.array(v['K']);cr,st,z=curve_visible(C,K,v['ring_path']);th=np.tile(np.arange(1024)*2*np.pi/1024,2);br=np.repeat([-1,1],1024);u=torus_uv_t(tt(C),K,th,br).numpy().reshape(2,1024,2);ferr=float(abs(u-cr['uv']).max());yaw=[]
  for angle in [-.2,.01,.2]:
   A=np.eye(4);A[:3,:3]=Rotation.from_euler('z',angle).as_matrix();yaw.append(float(abs(curves(A@C,K)['uv']-cr['uv']).max()))
  E=np.eye(4);q=np.array([.01,-.01,.005,.001,-.002,.003]);RF=np.array(v['RF_native']);H0=np.array(v['H0']);PC=pose_t(tt(np.r_[q,np.zeros(6)]),RF,H0).numpy();hier=float(abs(PC-H0@exp(q)@RF).max())
  forward.append(dict(group=v['group'],id=v['id'],role=v['role'],forward_max_px=ferr,yaw_max_px=max(yaw),inverse_error=float(abs(np.linalg.inv(C)@C-E).max()),hierarchy_error=hier,R_mm=v['R_mm'],r_mm=v['r_mm'],minimum_torus_depth_mm=z,visible_N=int((st==0).sum()),occluded_N=int((st==1).sum()),unknown_N=int((st==2).sum()),all_contour_candidates=2048))
 # All frozen realrepresentatives, no GT / held in gradient or solver.
 for g in GROUPS:
  v=next(v for v in vv if v['group']==g and v['role']=='FIT');C=np.array(v['T']);K=np.array(v['K']);ob=np.load(N/'ring_evidence'/(v['id']+'.npz'));obs={k:ob[k][np.linspace(0,len(ob[k])-1,min(32,len(ob[k])),dtype=int)]for k in ['inner','outer']};cp=correspondence(C,K,obs);cache=PoseCache(v['RF_native'],v['H0']);a=np.zeros(6);b=np.zeros(6);cost=RingCost(cache,K,cp,1.);jac+=jac_check(cost,[a,b],g+'_Torus')
  rgb=load(N/'inputs'/v['id']/'RGB_GEOMETRY.json');m=rgb['fit_pnp_inliers'][0]if rgb['fit_pnp_inliers']else rgb['matches'][0];X=np.array(m['X']);cost2=Reprojection(cache,K,m['uv'],.2);jac+=jac_check(cost2,[a,b,X],g+'_RGB');jac+=jac_check(Prior(np.zeros(6),np.ones(6)*.1),[a],g+'_prior')
  prob=ce.Problem();prob.add_residual_block(cost,None,[a,b]);prob.add_residual_block(Prior(np.zeros(6),np.ones(6)*.1),None,[a]);prob.set_parameter_block_constant(b)
  # Hold local worldaxisz for primitiveRing5DOF solve; not arbitrarycameraEuler yaw.
  sub=ce.SubsetManifold(6,[5]);prob.set_manifold(a,sub)
  for j in range(6):prob.set_parameter_lower_bound(a,j,-.25);prob.set_parameter_upper_bound(a,j,.25)
  d=solver(prob,'STAGE_A/'+g,10,False);newC=cache.get(a,b)[0];newcp=correspondence(newC,K,obs);cnew=RingCost(cache,K,newcp,1.);rn=cnew.values(a,b)[0];r0=RingCost(PoseCache(v['RF_native'],v['H0']),K,cp,1.).values(np.zeros(6),np.zeros(6))[0];old=float(r0@r0/2);new=float(rn@rn/2+.005*np.sum(a*a));physical.append(dict(group=g,view=v['id'],initial_true_cost=old,final_reassociated_cost=new,local_Ceres_cost=d['final_cost'],usable=d['usable'],actual_descent=new<=old+1e-8,q=a,pose=newC,center_change_mm=float(np.linalg.norm(newC[:3,3]-C[:3,3])),rotation_change_deg=float(np.degrees(Rotation.from_matrix(newC[:3,:3]@C[:3,:3].T).magnitude()))))
 table('metrics/TORUS_FORWARD_YAW_AND_COORDINATES.csv',forward);save('metrics/TORUS_FORWARD_YAW_AND_COORDINATES.json',forward);table('metrics/JACOBIAN_BLOCK_TESTS.csv',jac);save('metrics/JACOBIAN_BLOCK_TESTS.json',jac);save('metrics/REAL_STAGE_A_LM.json',physical)
 checks=[dict(name='originalequationsforward98',PASS=max(r['forward_max_px']for r in forward)<1e-9),dict(name='trueRingaxisymmetryyaw98',PASS=max(r['yaw_max_px']for r in forward)<1e-7),dict(name='positiveTorusdepth98',PASS=min(r['minimum_torus_depth_mm']for r in forward)>0),dict(name='inversehierarchymetric98',PASS=max(max(r['inverse_error'],r['hierarchy_error'])for r in forward)<1e-10),dict(name='allJacobianBlocks',PASS=all(r['PASS']for r in jac)),dict(name='realLMincludingreassociateddescent4',PASS=all(r['usable']and r['actual_descent']for r in physical))]
 # Tessellated CAD misses exact tangent rays. Preserve that diagnostic, but it is
 # not a visibility truth label. Check first intersections of the exact same torus.
 exact=[];render=[]
 for v in vv:
  C=np.array(v['T']);K=np.array(v['K']);cr=curves(C,K);r=torus_polynomial(C[:3,3],cr['X'].reshape(-1,3));exact.append(dict(id=v['id'],visible_N=int((r['states']==0).sum()),occluded_N=int((r['states']==1).sum()),unknown_N=int((r['states']==2).sum()),remainder=float(r['remainder'].max())))
 for g in GROUPS:
  v=next(v for v in vv if v['group']==g and v['role']=='FIT');C=np.array(v['T']);K=np.array(v['K']);cr=curves(C,K);s,_=ray_scene(v['ring_path']);y,x=np.mgrid[:360,:640];d=np.c_[x.ravel(),y.ravel(),np.ones(360*640)]@np.linalg.inv(K).T@C[:3,:3].T;hit=s.cast_rays(o3d.core.Tensor(np.c_[np.broadcast_to(C[:3,3],d.shape),d].astype(np.float32)))['t_hit'].numpy().reshape(360,640);hard=np.zeros((360,640),np.uint8);cv2.fillPoly(hard,[np.rint(cr['outer']).astype(np.int32)],1);cv2.fillPoly(hard,[np.rint(cr['inner']).astype(np.int32)],0);mask=np.isfinite(hit);cs,_=cv2.findContours(mask.astype(np.uint8),cv2.RETR_LIST,cv2.CHAIN_APPROX_NONE);bd=np.concatenate([c[:,0]for c in cs]);dd=cKDTree(cr['uv'].reshape(-1,2)).query(bd)[0];render.append(dict(group=g,CAD_vs_exact_mask_IoU=float((mask&(hard>0)).sum()/max(1,(mask|(hard>0)).sum())),CAD_boundary_to_exact_px=stats(dd)))
 save('metrics/EXACT_FIRST_INTERSECTION_VALIDATION.json',exact);save('metrics/INDEPENDENT_CAD_VS_ANALYTIC_RENDER.json',render)
 checks.append(dict(name='exactoriginaltorusvisibilityall98',PASS=all(r['occluded_N']==0 and r['unknown_N']==0 and r['remainder']<1e-12 for r in exact)))
 checks.append(dict(name='independentCADrenderquantization',PASS=all(r['CAD_boundary_to_exact_px']['p95']<2 for r in render),detail=render))
 gate=dict(PASS=all(c['PASS']for c in checks),checks=checks,backend='actualCeres2.2LM',HERO_GT_body=False,scope='98forwardviews;gradientandLM4FITonly',status='STAGE_A_PASSED'if all(c['PASS']for c in checks)else'STOP_STAGE_A_DIAGNOSE');save('STAGE_A_GATE.json',gate);print('STAGE_A_GATE',gate['PASS'],[(c['name'],c['PASS'])for c in checks],flush=True)
if __name__=='__main__':main()
