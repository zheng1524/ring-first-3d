from common import *
import shutil,subprocess
from evaluate import pointcast

def main():
    parent=R.parents[1];prior=parent/'runs/VISIBILITY_ORDER_REPAIR_001'
    assert sha(R/'code/p3d.py')==sha(prior/'code/p3d.py')
    history=[]
    for p in sorted(parent.rglob('*')):
        if p.is_file()and not p.is_relative_to(R)and 'runtime'not in p.parts and '__pycache__'not in p.parts:history.append(asset(p))
    save('assets_index/HISTORY_PROTECTION.json',history)
    cfg=dict(name='PROGRESSIVE_HERO_001',seed=20261106,steps=300,global_steps=100,checkpoints=[0,25,50,75,100,150,200,250,300],arms=['B','C','D'],A_frozen_root=str(prior),optimizer=dict(name='SGD',lr=1.,momentum=.9),relative_weights=dict(edge=1.,laplacian=1.,normal=.01,unsupported=.01),depth=dict(weight=.01,sigma_mm=.5,Huber_cap_r=10.,miss_cost=9.5,min_ray_face_cosine=.001,CAD_clearance_mm=.05),stop=dict(max_gradient_norm=100.,max_candidate_step_mm=2.,volume_ratio_range=[.1,10.]),GT='virtual D ideal-depth upper bound only; no GT mesh access in optimizer')
    save('config/PROTOCOL.json',cfg)
    save('assets_index/A_FROZEN.json',dict(source_root=str(prior),sha_files=[asset(p)for name in['virtual','real']for p in sorted((prior/'local_results'/name/'RingAware').glob('*'))if p.is_file()],p3d=asset(prior/'code/p3d.py'),parent_commit=subprocess.check_output(['git','-C',str(REPO),'rev-parse','HEAD'],text=True).strip(),rerun_A=False))
    # Reuse existing source-mask/native-pixel reliability audit, do not reselect by model fit.
    e1=Path('/home/liu/ring_first_3d_neural_e1/experiments/TASK-NEURAL-E1-PIPELINE-RECOVERY-001');cc={c['id']:c for c in load(e1/'provenance/INPUT_ELIGIBILITY.json')['references']};n0=Path('/home/liu/ring_first_3d_e3n0_eight/experiments/TASK-E3-N0-NEURALFUSION-EIGHT-VIEW-001/frozen_inputs/native')
    records=[];sources=[];decisions=[]
    for v in getcase('real')['views']:
        cid=v['id'];s=cc[cid];a=np.load(R1/'inputs'/(cid+'.npz'));raw=np.load(s['E1_actual_native']['path']);cl=np.load(n0/(cid+'.npz'));d=np.load(R/'inputs/real'/(cid+'.npz'));uv=a['uv'];z=a['z'];Kn=a['Kn'];T=a['T'];pid=a['pixel_id'];shape=raw['depth_mm'].shape
        assert np.array_equal(pid,uv[:,1]*shape[1]+uv[:,0]);assert np.array_equal(z,raw['depth_mm'][uv[:,1],uv[:,0]]);assert cl['valid'][uv[:,1],uv[:,0]].all();assert np.allclose(T,d['T'],atol=1e-10)and np.allclose(a['K'],d['K'],atol=1e-10)
        X=(np.c_[uv,np.ones(len(uv))]@np.linalg.inv(Kn).T*z[:,None])@T[:3,:3].T+T[:3,3];assert abs(X-a['X']).max()<1e-8
        origuv=np.c_[uv,np.ones(len(uv))]@np.linalg.inv(Kn).T@d['K'].T;origuv=origuv[:,:2]/origuv[:,2:];px=np.clip(np.rint(origuv).astype(int),[0,0],[639,359]);labels=d['labels'][px[:,1],px[:,0]]
        r=np.load(R/'inputs/real/RING.npz');_,_,cad=pointcast(scene(r['V'],r['F']),X,Kn,T);good=(labels==1)&np.isfinite(z)&(z>0)&(z<cad-.05)
        out=R/'depth_observations'/(cid+'.npz');np.savez_compressed(out,uv=uv[good],pixel_id=pid[good],z=z[good],K=Kn,T=T,weight=np.ones(good.sum()),native_shape=shape)
        for i in range(len(z)):decisions.append(dict(source=cid,pixel_id=int(pid[i]),role=v['role'],retained=bool(good[i]),raw_exact=True,clean_valid=True,RGB_label=int(labels[i]),z_HERO_mm=float(z[i]),CAD_z_mm=float(cad[i]),reason='RELIABLE_FIXED_CACHE'if good[i]else'MASK_OR_CAD_ORDER_EXCLUDED'))
        records.append(dict(case='real',source=cid,role=v['role'],depth_kind='FROZEN_NATIVE_HERO',cache_N=len(z),eligible_N=int(good.sum()),excluded_N=int((~good).sum()),native_height=shape[0],native_width=shape[1],RGB_height=360,qualification=v['qualification'],raw_exact=True,XYZ_error_mm=float(abs(X-a['X']).max())))
        sources.extend([asset(R1/'inputs'/(cid+'.npz')),asset(s['E1_actual_native']['path']),asset(n0/(cid+'.npz'))])
    # Explicitly authorized ideal-depth upper bound: rendering observations, never passing GT mesh to optimizer.
    gtpath=OLD/'audit_only/NATIVE_CAD_GT.npz';g=np.load(gtpath);rt=scene(g['V'],g['F']);rr=np.load(R/'inputs/virtual/RING.npz');rs=scene(rr['V'],rr['F'])
    for v in getcase('virtual')['views']:
        cid=v['id'];a=np.load(R/'inputs/virtual'/(cid+'.npz'));lab=a['labels'];interior=cv2.erode((lab==1).astype(np.uint8),np.ones((3,3),np.uint8)).astype(bool);y,x=np.where(interior);ix=np.linspace(0,len(x)-1,min(512,len(x))).astype(int);uv=np.c_[x[ix],y[ix]]
        # Cast these exact native center rays; no depth interpolation or invented missing values.
        K=a['K'];T=a['T'];rays=np.c_[uv,np.ones(len(uv))]@np.linalg.inv(K).T
        import open3d as o3d
        ray=o3d.core.Tensor(np.c_[np.broadcast_to(T[:3,3],rays.shape),rays@T[:3,:3].T].astype(np.float32));z=rt.cast_rays(ray)['t_hit'].numpy().astype(float);cad=rs.cast_rays(ray)['t_hit'].numpy();ok=np.isfinite(z)&(z>0)&(z<cad-.05)
        np.savez_compressed(R/'depth_observations'/(cid+'.npz'),uv=uv[ok],pixel_id=(uv[:,1]*640+uv[:,0])[ok],z=z[ok],K=K,T=T,weight=np.ones(ok.sum()),native_shape=[360,640])
        records.append(dict(case='virtual',source=cid,role=v['role'],depth_kind='IDEAL_GT_DEPTH_UPPER_BOUND_NOT_HERO',cache_N=len(z),eligible_N=int(ok.sum()),excluded_N=int((~ok).sum()),native_height=360,native_width=640,RGB_height=360,qualification=v['qualification'],raw_exact=True,XYZ_error_mm=0.))
    table('metrics/DEPTH_INPUT_AUDIT.csv',records);table('metrics/REAL_DEPTH_DECISIONS.csv',decisions);save('assets_index/DEPTH_SOURCES.json',dict(real_sources=sources,virtual_GT_depth_source=asset(gtpath),virtual_exception='User-authorized ideal-depth upper bound only; no GT mesh during optimization',weights='Uniform frozen reliable observations, no GT/error-dependent weights'))
    save('assets_index/INPUTS.json',[asset(p)for folder in['inputs','depth_observations']for p in sorted((R/folder).rglob('*'))if p.is_file()])
    print(records,flush=True)
if __name__=='__main__':main()
