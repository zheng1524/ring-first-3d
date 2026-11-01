"""Read-only evaluation of initial and rejected step1 fields; no continuation."""
from common import *
from gpu_model_adapter import load_checkpoint
from fixed_renderer import render,raw,array_pred
from evaluate import penetration
from skimage.measure import marching_cubes

MODELS={'Initial':'checkpoints/A/step000.pt','A_STOP1':'checkpoints/A/STOP_UNSAFE_step001.pt','B_STOP1':'checkpoints/B/STOP_UNSAFE_step001.pt'}
def dense_packet(ref):
    c,p,r=source(ref);stride=cfg()['geometry_probe']['render_stride'];u,v=np.meshgrid(np.arange(0,640,stride),np.arange(0,360,stride));pix=(v*640+u).ravel();uv=np.c_[u.ravel(),v.ravel()]
    ray=vis.camera_rays(uv,r['K'],r['c2w_mm']);factor=np.linalg.norm(ray[:,3:],axis=1);rel=np.load(e2_asset('local_results/'+ref+'_depth_reliability.npz'))
    return dict(source=ref,source_pixel=pix,origin=ray[:,:3],direction=ray[:,3:]/factor[:,None],cosine=1/factor,
        start=r['ROI_start_t_mm'][pix],end=r['ROI_end_t_mm'][pix],valid=r['ROI_valid'][pix],sampling_class=r['sampling_class'][pix],
        mask_target=r['mask_target'][pix],mask_weight=r['mask_weight'][pix],depth_weight=rel['pixel_weight'][pix],target_Z=r['native_axial_Z_mm'][pix],
        RGB=np.asarray(Image.open(c['RGB']).convert('RGB'))[v.ravel(),u.ravel()]/255.,Ring_t_mm=r['ring_first_t_mm'][pix],K=r['K'],c2w_mm=r['c2w_mm'],shape=np.array(u.shape))

def dense_predict(model,b):
    n=len(b['source_pixel']);out=dict(opacity=np.zeros(n),RGB=np.zeros((n,3)),depth_mm=np.full(n,np.nan),front_t_mm=np.full(n,np.nan),render_hit=np.zeros(n,bool))
    for start in range(0,n,64):
        end=min(start+64,n);ids=np.arange(start,end)
        if not b['valid'][ids].any():continue
        bb={k:v[ids] if isinstance(v,np.ndarray)and v.ndim and len(v)==n else v for k,v in b.items()}
        p=render(model,bb,load(R/'config/SELECTED_SAMPLING.json')['cells'],REFS.index(b['source']),create_graph=False)
        for key,value in array_pred(p).items():out[key][ids]=value
        del p
    return out

def surface(model,key):
    rad=domain()['ROI_radius_mm'];N=cfg()['geometry_probe']['surface_grid_final_N'];q=np.linspace(-rad,rad,N);x,y,z=np.meshgrid(q,q,q,indexing='ij');P=np.c_[x.ravel(),y.ravel(),z.ravel()]+domain()['world_origin_mm'];vals=[]
    with torch.no_grad():
        for i in range(0,len(P),4096):vals.append(raw(model,P[i:i+4096])[0].cpu().numpy())
    f=np.concatenate(vals).reshape(x.shape);vertices,faces,normals,values=marching_cubes(f,level=0,spacing=(q[1]-q[0],)*3)
    vertices=vertices-rad+np.asarray(domain()['world_origin_mm']);mesh=trimesh.Trimesh(vertices,faces,process=False)
    cls=np.zeros(len(vertices),np.uint8);support=np.zeros((3,len(vertices)),bool);conflict=support.copy();visible=support.copy()
    sys.path.insert(0,str(VENDOR));import open3d as o3d
    scene=o3d.t.geometry.RaycastingScene(nthreads=2);scene.add_triangles(o3d.core.Tensor(np.asarray(vertices,np.float32)),o3d.core.Tensor(np.asarray(faces,np.uint32)))
    for j,ref in enumerate(REFS):
        c,p,r=source(ref);uv,Z=vis.project_camera(vertices,r['K'],r['c2w_mm']);ij=np.rint(uv).astype(int);ok=(Z>0)&(ij[:,0]>=0)&(ij[:,0]<640)&(ij[:,1]>=0)&(ij[:,1]<360)
        ids=np.flatnonzero(ok);pix=ij[ids,1]*640+ij[ids,0];ray=vis.camera_rays(uv[ids],r['K'],r['c2w_mm']).astype(np.float32)
        first=scene.cast_rays(o3d.core.Tensor(ray))['t_hit'].numpy();own_front=np.isfinite(first)&(Z[ids]<=first+.05)
        t=np.linalg.norm(vertices[ids]-r['c2w_mm'][:3,3],axis=1);scope=own_front&r['ROI_valid'][pix]&(t>=r['ROI_start_t_mm'][pix])&(t<=r['ROI_end_t_mm'][pix])
        visible[j,ids]=scope;rel=np.load(e2_asset('local_results/'+ref+'_depth_reliability.npz'))['pixel_weight'][pix]
        eligible=scope&(r['labels'][pix]==1)&(rel>0)&np.isfinite(r['native_axial_Z_mm'][pix]);delta=abs(Z[ids]-r['native_axial_Z_mm'][pix])
        support[j,ids]=eligible&(delta<=cfg()['geometry_probe']['HERO_support_tolerance_mm']);conflict[j,ids]=eligible&(delta>cfg()['geometry_probe']['HERO_support_tolerance_mm'])
    cls[support.any(0)]=1;cls[conflict.any(0)]=2
    facecls=np.zeros(len(faces),np.uint8);facecls[(cls[faces]==1).all(1)]=1;facecls[(cls[faces]==2).any(1)]=2
    inside=(np.linalg.norm(vertices-domain()['world_origin_mm'],axis=1)<=rad+1e-6);facecls[~inside[faces].all(1)]=0
    # Only observed-front supported/conflict faces are exported. No closure.
    shown=trimesh.Trimesh(vertices,faces[facecls>0],process=False);shown.visual.face_colors=np.array([[160,160,160,100],[35,160,90,255],[235,135,35,255]],np.uint8)[facecls[facecls>0]]
    (R/'figures/surfaces').mkdir(exist_ok=True);shown.export(R/f'figures/surfaces/{key}_visible.ply')
    components=mesh.split(only_watertight=False);reg=load(R/'config/RUN_EXECUTION_PROTOCOL.json');substantial=[m for m in components if len(m.faces)>=reg['substantial_component_min_faces']and m.area>=reg['substantial_component_fraction']*mesh.area]
    insidegrid=(x*x+y*y+z*z)<=rad*rad;vol=float(((f<0)&insidegrid).sum()*(q[1]-q[0])**3)
    cad=penetration(vertices[cls==1])
    cad['CAD_status']='EVALUABLE' if cad['CAD_supported_N'] else 'NOT_EVALUABLE_NO_SUPPORTED_POINTS'
    if not cad['CAD_supported_N']:cad['CAD_penetration_fraction']=None
    stats=dict(model=key,raw_vertex_N=len(vertices),raw_face_N=len(faces),visible_face_N=int((facecls>0).sum()),
        supported_vertex_N=int((cls==1).sum()),conflict_vertex_N=int((cls==2).sum()),unknown_vertex_N=int((cls==0).sum()),
        raw_component_N=len(components),substantial_raw_component_N=len(substantial),negative_ROI_volume_mm3=vol,
        raw_prior_area_mm2=float(mesh.area),supported_visible_area_mm2=float(mesh.area_faces[facecls==1].sum()),conflict_visible_area_mm2=float(mesh.area_faces[facecls==2].sum()),
        raw_bounds_mm=mesh.bounds.tolist(),visible_mesh_watertight=bool(shown.is_watertight),backside_closed=False,**cad)
    folder=R/'local_results/surfaces';folder.mkdir(exist_ok=True);np.savez_compressed(folder/f'{key}.npz',vertices=vertices,faces=faces,vertex_class=cls,face_class=facecls,
        visible_by_source=visible,support_by_source=support,conflict_by_source=conflict,SDF_mm=f,coordinate_mm=q)
    return stats

def warp(modelkey,A,B):
    folder=R/'local_results/dense';a=np.load(folder/f'{modelkey}_{A}.npz');b=dense_packet(B);c,_,r=source(B);s=cfg()['geometry_probe']['render_stride'];h,w=b['shape']
    ia=np.flatnonzero(a['render_hit']&(a['mask_target']>0));X=a['origin'][ia]+a['direction'][ia]*a['front_t_mm'][ia,None]
    uv,Z=vis.project_camera(X,r['K'],r['c2w_mm']);xy=np.rint(uv/s).astype(int);native=np.rint(uv).astype(int)
    ok=(Z>0)&(xy[:,0]>=0)&(xy[:,0]<w)&(xy[:,1]>=0)&(xy[:,1]<h)&(native[:,0]>=0)&(native[:,0]<640)&(native[:,1]>=0)&(native[:,1]<360)
    q=np.flatnonzero(ok);pix=native[q,1]*640+native[q,0];t=np.linalg.norm(X[q]-r['c2w_mm'][:3,3],axis=1)
    visible=r['ROI_valid'][pix]&(t>=r['ROI_start_t_mm'][pix])&(t<=r['ROI_end_t_mm'][pix]);q=q[visible]
    target=(xy[q,1]*w+xy[q,0]);order=np.argsort(Z[q],kind='stable');target=target[order];q=q[order];_,first=np.unique(target,return_index=True);q=q[first];target=target[first]
    rgb=np.full((h*w,3),np.nan);zz=np.full(h*w,np.nan);rgb[target]=a['source_RGB'][ia[q]];zz[target]=Z[q]
    observed=(b['mask_target']>0)&(b['depth_weight']>0);received=np.isfinite(zz)&observed;diff=np.full(h*w,np.nan);depth=np.full(h*w,np.nan)
    diff[received]=abs(rgb[received]-b['RGB'][received]).mean(1);depth[received]=zz[received]-b['target_Z'][received]
    out=R/'local_results/warps';out.mkdir(exist_ok=True);np.savez_compressed(out/f'{modelkey}_{A}_to_{B}.npz',RGB=rgb.reshape(h,w,3),RGB_error=diff.reshape(h,w),Depth_residual_mm=depth.reshape(h,w),received=received.reshape(h,w))
    return dict(model=modelkey,A=A,B=B,target_qualified_grid_N=int(observed.sum()),explained_N=int(received.sum()),coverage=float(received.sum()/observed.sum()),
        RGB_MAE=None if not received.any()else float(np.nanmean(diff)),Depth_MAE_mm=None if not received.any()else float(np.nanmean(abs(depth))),
        coloring='SOURCE_A_RGB_ONLY; B image used only for residual; no B-texture reassignment',independent_view_test=False)

def main():
    check_gpu();freeze('BEFORE_POSTSTOP_DENSE_EVALUATION.json',dict(optimizer_step_N_added=0,checkpoints_rejected_for_training=True))
    surfaces=[];dense=[];regions=[]
    for key,path in MODELS.items():
        model=load_checkpoint(path);before=parameter_hash(model);surfaces.append(surface(model,key))
        for ref in REFS:
            b=dense_packet(ref);p=dense_predict(model,b);obs=b['depth_weight']>0;good=obs&p['render_hit'];v=b['valid']&(b['mask_weight']>0);target=b['mask_target']>0;pred=p['opacity']>=.5
            iou=float((v&target&pred).sum()/(v&(target|pred)).sum());rv=(b['sampling_class']==0)&p['render_hit'];depth=p['depth_mm'][good]-b['target_Z'][good]
            dense.append(dict(model=key,source=ref,stride=4,known_mask_N=int(v.sum()),qualified_HERO_N=int(obs.sum()),front_hit_N=int(good.sum()),coverage=float(good.sum()/obs.sum()),Mask_IoU=iou,
                RGB_MAE=None if not rv.any()else float(abs(p['RGB'][rv]-b['RGB'][rv]).mean()),Depth_MAE_mm=None if not good.any()else float(abs(depth).mean()),
                prediction_spill_N=int((v&pred&~target).sum()),high_opacity_no_front_N=int((obs&(p['opacity']>.98)&~p['render_hit']).sum()),all_source_image_diagnostic=True))
            q=R/'local_results/dense';q.mkdir(exist_ok=True);np.savez_compressed(q/f'{key}_{ref}.npz',**p,source_pixel=b['source_pixel'],mask_target=b['mask_target'],source_RGB=b['RGB'],
                target_Z=b['target_Z'],shape=b['shape'],origin=b['origin'],direction=b['direction'],observed=obs)
            # Source-defined world-Z proxies are fixed, not anatomical GT.
            tt=b['target_Z'][obs]/b['cosine'][obs];z=(b['origin'][obs]+b['direction'][obs]*tt[:,None])[:,2];cuts=load(R/'config/RUN_EXECUTION_PROTOCOL.json')['region_world_Z_tertiles_mm'];ids=np.flatnonzero(obs)
            for j,name in enumerate(['LOW_Z_BASE_PROXY','MID_Z_LOWER_PROXY','HIGH_Z_HEAD_PROXY']):
                use=ids[np.digitize(z,cuts)==j];H=int(p['render_hit'][use].sum());regions.append(dict(model=key,source=ref,region=name,qualified_N=len(use),front_hit_N=H,coverage=None if not len(use)else H/len(use),
                    region_definition='frozen native train-HERO world-Z tertiles; anatomical identity not certified'))
            print('POSTSTOP_DENSE',key,ref,'hits',int(good.sum()),'/',int(obs.sum()),flush=True)
        assert parameter_hash(model)==before;del model;gc.collect();torch.cuda.empty_cache()
    warps=[]
    for key in MODELS:
        for A in REFS:
            for B in REFS:
                if A!=B:warps.append(warp(key,A,B))
    table('metrics/DENSE_SOURCE_DIAGNOSTICS.csv',dense);table('metrics/REGIONAL_COVERAGE.csv',regions);table('metrics/MULTIVIEW_WARPS.csv',warps);save('metrics/SURFACE_DIAGNOSTICS.json',surfaces)
    save('metrics/POSTPROCESS_STATUS.json',dict(status='COMPLETE_REJECTED_STEP1_DIAGNOSTICS',models=list(MODELS),safe_final_models_identical_to_initial=True,
        scheduled_steps_25_50_75_100='NOT_RUN_STOPPED_AT1',no_additional_optimizer_steps=True,postprocess_peak_allocated_bytes=memory_guard()))
    print('POSTSTOP_EVALUATION_COMPLETE; actual step1 failure models, never called successful reconstruction')
if __name__=='__main__':main()
