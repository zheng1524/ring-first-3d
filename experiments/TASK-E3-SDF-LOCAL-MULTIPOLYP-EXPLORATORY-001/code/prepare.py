"""Freeze actual current sources and official modules; derive evidence-based normals."""
from common import *
import shutil
def main():
    assert not (R/'config/PREREGISTERED.json').exists(),'INPUT_AND_PROTOCOL_ALREADY_FROZEN'
    # Read the original immutable Git blobs; keep the historical dirty clone untouched.
    rev='12513009cd20a08b35ddc2c55a7e42da2c7baf43';official_files=[]
    paths=['code/model/network.py','code/model/ray_sampler.py','code/model/density.py','code/model/embedder.py','code/model/loss.py','code/utils/rend_util.py','code/utils/general.py','code/utils/plots.py','code/training/monosdf_train.py','code/training/exp_runner.py','code/confs/dtu_mlp_3views.conf','README.md','LICENSE']
    for rel in paths:
        b=subprocess.check_output(['git','-C',str(ORIGINAL_SDF),'show',rev+':'+rel]);dst=R/'runtime/official_exact'/rel;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(b);official_files.append(dict(relative_path=rel,original_git_blob=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest(),**asset(dst)))
    save('provenance/OFFICIAL_SOURCE_MANIFEST.json',dict(repository='https://github.com/autonomousvision/monosdf',commit=rev,files=official_files,historical_dirty_clone_not_modified=True))
    domain=load(N0/'config/EXPERIMENT_FROZEN.json')['domains'][SCENE];C=np.array(domain['O_mm'])+domain['L_mm']/2;s=domain['L_mm']/2;bound=1.0
    gate={r['source']:r for r in load(N0/'config/CAMERA_GATE_RESULTS.json')['sources']};per=[];data={};assets=[]
    for cid in SOURCES:
        n=native(cid);c=CC[cid]
        for k in ['RGB','Mask','pack','source_points','mesh','camera_file']:
            a=asset(c[k]);assert a['sha256']==c['files'][k]['sha256'];assets.append(a)
        a=asset(c['E1_actual_native']['path']);assert a['sha256']==c['E1_actual_native']['sha256'];assets.append(a);assets.append(asset(c['Ring_CAD']['path']))
        p=np.load(N0/'frozen_inputs/native'/(cid+'.npz'));cp=np.load(N0/'frozen_inputs/crops'/(cid+'.npz'));z=p['depth_mm'];valid=p['valid'];h,w=z.shape
        assert (z[~valid]==0).all()and np.array_equal(z[valid],n['depth'][valid]);v,u=np.mgrid[:h,:w];uv=np.c_[u.ravel(),v.ravel()];X=unproject(z.ravel().astype(float),n['T'],uv,n['Kn']).reshape(h,w,3)
        # Central differences only when all four real neighbouring depth observations exist.
        neighbours=np.zeros_like(valid);neighbours[1:-1,1:-1]=valid[1:-1,1:-1]&valid[1:-1,:-2]&valid[1:-1,2:]&valid[:-2,1:-1]&valid[2:,1:-1]
        dx=np.zeros_like(X);dy=dx.copy();dx[:,1:-1]=X[:,2:]-X[:,:-2];dy[1:-1]=X[2:]-X[:-2];normal=np.cross(dx,dy);norm=np.linalg.norm(normal,axis=2);normal/=np.maximum(norm[:,:,None],1e-20)
        toward=n['T'][:3,3]-X;normal[(normal*toward).sum(2)<0]*=-1
        jump=np.zeros_like(z,dtype=float)
        for dy0,dx0 in [(1,0),(-1,0),(0,1),(0,-1)]:jump=np.maximum(jump,np.abs(z-np.roll(z,(dy0,dx0),(0,1))))
        dt=cv2.distanceTransform((n['native_labels']==1).astype(np.uint8),cv2.DIST_L2,5);normal_valid=neighbours&(jump<=.75)&(dt>2)&(norm>1e-12)
        # Exact current 320x240 crop and immutable original Pixel ID mapping.
        pixel=cp['source_ids'];inside=pixel>=0;native_normals=normal@ n['T'][:3,:3];normal_crop=np.zeros((240,320,3),np.float32);nv=np.zeros((240,320),bool);normal_crop[inside]=native_normals.reshape(-1,3)[pixel[inside]];nv[inside]=normal_valid.ravel()[pixel[inside]];normal_crop[~nv]=0
        K=cp['K_crop'];T=n['T'].copy();TM=T.copy();TM[:3,3]=(T[:3,3]-C)/s;yy,xx=np.mgrid[:240,:320];uvout=np.c_[xx.ravel(),yy.ravel()];rays=vis.camera_rays(uvout,K,T);ray=rays[:,3:];length=np.linalg.norm(ray,axis=1);unit=ray/length[:,None]
        origin=(T[:3,3]-C)/s;t1=(-bound-origin)/np.where(abs(unit)>1e-15,unit,1e-15);t2=(bound-origin)/np.where(abs(unit)>1e-15,unit,1e-15);near=np.maximum(np.minimum(t1,t2).max(1),0);far=np.maximum(t1,t2).min(1)
        cad,_=cast(ringscene(SCENE),uvout,K,T);far=np.minimum(far,(cad-.05)*length/s);legal=np.isfinite(near)&np.isfinite(far)&(far>near+1e-5)
        hero=cp['valid'].ravel()&legal;dz=cp['depth_mm'].ravel();hero&=~(np.isfinite(cad)&(dz>cad+.002));hero&=(dz*length/s>=near)&(dz*length/s<=far)
        nv=nv.ravel()&hero
        xout=unproject(dz[hero].astype(float),T,uvout[hero],K);modelX=(xout-C)/s;assert ((modelX>=-1-1e-8)&(modelX<=1+1e-8)).all()
        d=dict(depth_mm=cp['depth_mm'],depth_model=cp['depth_mm']/s,RGB=cp['RGB'],valid=cp['valid'],eligible_HERO=hero.reshape(240,320),normal_camera=normal_crop,normal_valid=nv.reshape(240,320),native_pixel_ID=cp['source_ids'],K_crop=K,c2w_mm=T,c2w_model=TM,uv=uvout.astype(np.float32),near=near.reshape(240,320).astype(np.float32),far=far.reshape(240,320).astype(np.float32),CAD_first_axial_mm=cad.reshape(240,320),X_HERO_model=np.where(hero[:,None],(unproject(dz.astype(float),T,uvout,K)-C)/s,np.nan).reshape(240,320,3))
        data[cid]=d;per.append(dict(source=cid,qualification=gate[cid]['qualification'],block=gate[cid]['block'],native_retained_N=int(valid.sum()),crop_retained_N=int(cp['valid'].sum()),eligible_crop_HERO_N=int(hero.sum()),normal_eligible_N=int(nv.sum()),normal_rule='true central XYZ derivatives, 4 legal neighbours, <=.75mm axial jump, >2 native Mask px interior, oriented toward actual camera; camera coordinates',input_baseline='G01/G06 exact current N0 frozen inputs; G08 same fixed A2 method on frozen3; no output-driven cleanup',native_asset=asset(N0/'frozen_inputs/native'/(cid+'.npz')),crop_asset=asset(N0/'frozen_inputs/crops'/(cid+'.npz'))))
    # Weak source conflict proxies, never delete a source or synthesize a corrected depth.
    for cid,d in data.items():
        hero=d['eligible_HERO'].ravel();j=np.flatnonzero(hero);X=d['X_HERO_model'].reshape(-1,3)[j]*s+C;weight=np.ones(240*320,np.float32);conflict=np.zeros(240*320,bool)
        for other,t in data.items():
            if other==cid:continue
            uv,z=vis.project_camera(X,t['K_crop'],t['c2w_mm']);ok=np.isfinite(uv).all(1)&(z>0)&(uv[:,0]>=-.5)&(uv[:,0]<319.5)&(uv[:,1]>=-.5)&(uv[:,1]<239.5);kk=np.flatnonzero(ok);ij=np.floor(uv[kk]+.5).astype(int);legal=t['eligible_HERO'][ij[:,1],ij[:,0]];cad=t['CAD_first_axial_mm'][ij[:,1],ij[:,0]];legal&=~(np.isfinite(cad)&(z[kk]>cad+.002));zd=t['depth_mm'][ij[:,1],ij[:,0]];front=legal&(z[kk]<zd-.25);conflict[j[kk[front]]]=True
        weight[conflict]=.25;d['reliability_weight']=weight.reshape(240,320);d['free_space_conflict_proxy']=conflict.reshape(240,320);folder=R/'frozen_inputs';folder.mkdir(exist_ok=True);np.savez_compressed(folder/(cid+'.npz'),**d);per[next(i for i,r in enumerate(per)if r['source']==cid)]['conditional_conflict_N']=int(conflict.sum())
    plan=dict(task=R.name,phase='LOCAL_EXPLORATORY_M1_10X',seed=20261103,scene=SCENE,sources=SOURCES,stages={'three_reference':SOURCES},arms=['M0','M1'],official_commit=rev,
        geometry=dict(C_mm=C,mm_per_model_unit=s,box_model=[[-1,-1,-1],[1,1,1]],source='same N0 frozen G01 metric cube; shared single/three and M0/M1',SDF_mm='mm_per_model_unit * raw_official_SDF',camera='c2w R unchanged, translation=(C_camera_mm-C_mm)/s',depth='axial Z_mm/s; ray samples are Euclidean distance, not axial Z'),
        official_training_budget=dict(paper_iterations=200000,rays_per_update=1024,learning_rate=5e-4,sched_decay_rate=.1,official_nepoch_cli_default=2000,warning='official dataset __len__ remains full n_images even num_views3; do NOT use new1/3image epoch count to silently shorten200k',total_primary_runs=4,total_primary_updates=800000),
        sampler=dict(N_samples=64,N_samples_eval=128,N_samples_extra=32,eps=.1,beta_iters=10,max_total_iters=5,finite_bounds='true per-ray ROI cube intersection and earliest actual CAD-.05mm; official ErrorBoundSampler core unchanged',infinite_terminal_absorption=False),
        network=dict(Grid_MLP=False,dims=[256]*8,feature_vector_size=256,multires=6,skip_in=[4],rendering_dims=[256,256],multires_view=4,bias=.6,beta_init_model=.1,beta_min_model=.0001,inside_outside=False,absorbing_sphere_disabled=True),
        optimizer=dict(type='official plain MLP Adam',lr=5e-4,betas=[.9,.999],eps=1e-8,schedule='1000-step linear warmup from baseLR/1000 then official exponential0.1 over200k; identical M0/M1',gradient_clip=None),
        losses=dict(shared=dict(rgb='official L1 on fixed legal Polyp scope',eikonal_weight=.1,smooth_weight=.005,depth='official scale-and-shift invariant shape loss; actual HERO depth in model units, no Omnidata50+.5 transform',depth_weight=.1,normal_l1_weight=.05,normal_cos_weight=.05,end_step=12800,normal_validity='real derived normals only; no fake all-ones normals',prediction_crossing_gate='official depth/normal crossing gate retained; risk explicitly evaluated'),M1=dict(surface_weight=1.,surface='smooth_L1(f_mm/.25,0), all qualified HERO points independent of predicted hit',first_surface_weight=.1,first_surface='smooth_L1((first_pos_to_neg_axial_mm-HERO_mm)/.25,0), fixed HERO denominator; miss counts remain separate, no fake hit',free_space_weight=.1,free_space='weak relu(.05-f_mm)/.25 at source HERO-0.5mm along actual ray, only if inside allowed interval before CAD; no ROI entry outside assumption',positive_mask_weight=.1,positive_mask='stable finite log optical opacity target1; no Ring/background unknown negative labels',conflict='1/.25 front-violation proxy, not physical truth; all sources retained; one shared upstream family source-balanced'),
            M0_M1_difference='M1-only absolute anchors/first-depth/free-space/positive-opacity; same official backbone/sampling/renderer, seed/batch/steps'),
        checkpoint_steps=[0,200,500,1000,2000,5000,10000],mesh=dict(official_function='utils.plots.get_surface_trace',coarse_checkpoint_resolution=256,final_resolution=256,all_components_preserved=True,mesh_postprocess=False),
        recovery=dict(max_additional_runs=1,predeclared_candidate='same init/input, baseLR5e-5, same200k update budget; only if severe shrink diagnosed; not automatically selected by appearance',primary_runs_not_stopped_for_geometry=True),
        resource_benchmark=dict(warmup_updates=5,timed_updates=20,arms=['M0','M1'],batch_rays=1024,microbatch_fallback='no silent effective-batch reduction; if1024 OOM report and propose exact gradient-accumulation adaptation separately',formal_training_updates=0,disposable_parameters=True),
        evaluation=dict(native_denominator='all original valid native Polyp for CORE; raw/retained availability and CAD flags separate; identical M0/M1',agreement_mm=.25,physical_GT='NOT_EVALUABLE',image_holdout='no independent unseen frames; held pixels only monitoring, not blind view'),
        permitted='G01_004 only; no source or camera changes, no new HERO, no GT/Oracle/Dxy',sources_detail=per)
    save('config/PREREGISTERED.json',plan);save('provenance/ORIGINAL_ASSETS.json',dict(files=assets));table('metrics/INPUT_AND_NORMAL_AUDIT.csv',per);save('provenance/INPUT_FREEZE.json',dict(files=[asset(x)for x in (R/'frozen_inputs').glob('*.npz')],config=asset(R/'config/PREREGISTERED.json'),before_any_GPU_update=True))
    print('PREPARED',clean(per),'unit_mm',s,'formal training0',flush=True)
if __name__=='__main__':main()
