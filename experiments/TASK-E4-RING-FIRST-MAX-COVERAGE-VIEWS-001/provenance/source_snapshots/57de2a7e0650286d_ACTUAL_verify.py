from coverage import *
from ceres_backend import *
def main():
 rows=[];C=np.eye(4);K=K0;lab=np.ones((360,640),np.uint8);V=np.array([[-2,-2,10],[2,-2,10],[0,2,10]],float);F=np.array([[0,1,2]]);ss=scene(V,F);ring=scene(V+np.array([0,0,90]),F);vis,unk=visible(np.array([[0,0,10],[4,0,10]],float),C,K,lab,ss,ring);rows.append(dict(name='selfMISS_isUNKNOWN_never_visible',PASS=vis.tolist()==[True,False]and unk.tolist()==[False,True],detail=dict(visible=vis,unknown=unk)))
 A=np.diag([1.,352/360,1.]);A[1,2]=.5*352/360-.5;Kn=A@K;p=np.array([[0,0],[300,200],[639,351]],float);z=np.array([20.,25.,40.]);X=np.c_[p,np.ones(3)]@np.linalg.inv(Kn).T*z[:,None];uv,zz=projection(X,C,Kn);rows.append(dict(name='native_depth_mm_axial_roundtrip_no_resize',PASS=bool(np.max(abs(uv-p))<1e-10 and np.max(abs(zz-z))<1e-12),unit='mm'))
 for g in GROUPS:
  conf,ss,_=None,None,None
  conf,ss=frozen_sources(g);rows.append(dict(name=g+'_FIT_only_no_evalonly_HERO_proxy',PASS=all(s['role']=='FIT'and not s['source'].get('evaluation_only',False)for s in ss),N=len(ss)))
  pool=load(camera_file(g));held={v['id']for v in pool if v['role']=='HOLDOUT'};plan=load(selpath(g,'_HERO_PLAN.json'));ok=all(r['target']['id']not in held and all(s['id']not in held and s['formal']for s in r['support_views'])and r['target']['formal']for r in plan);rows.append(dict(name=g+'_all_actual_HERO_parents_FORMAL_FIT',PASS=ok,targets=len(plan),held_N=len(held)))
  v=next(v for v in pool if v['formal']);Cc=np.array(v['C']);a=curves(Cc,K);H=np.eye(4);H[:3,:3]=Rotation.from_euler('z',.7).as_matrix();b=curves(H@Cc,K);yaw=float(abs(a['uv']-b['uv']).max());rows.append(dict(name=g+'_exact_thickTorus_original_yaw_invariance',PASS=yaw<1e-7,error_px=yaw))
  c=PoseCache(Cc,np.eye(4));rr=load(v.get('rgb_geometry_path',N/'inputs'/v['id']/'RGB_GEOMETRY.json'));m=rr['fit_pnp_inliers'][0];cost=Reprojection(c,K,m['uv'],.2);ns=dict(np=np);extract(U/'code/stage_a.py',['jac_check'],ns);jac=ns['jac_check'](cost,[np.zeros(6),np.zeros(6),np.array(m['X'])],g+'_full6RGB');rows+=jac
 table('metrics/CONTRACT_AND_GEOMETRY_TESTS.csv',rows);save('metrics/CONTRACT_AND_GEOMETRY_TESTS.json',rows);save('STAGE_D_READY.json',dict(PASS=all(r['PASS']for r in rows),tests=len(rows),new_depth_interpolations=0));assert all(r['PASS']for r in rows);print('PRE_HERO_CONTRACTS_PASS',len(rows),flush=True)
if __name__=='__main__':main()
