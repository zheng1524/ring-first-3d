"""Generate actual independent depth-grid surfaces under biased estimated poses."""
import json,hashlib
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
from ..policy.contracts import require
from ..contracts.coordinates import unproject,project,validate_c2w
from ..contracts.identities import sha256
from ..synthetic.io import save_json,outputs
from ..sim.scene import synthesize
from ..sim.geometry import error_transform
from ..dualvideo.audit import check_sources
from .geometry import depth_grid_mesh,transform,se3,distribution,sample_mesh,scene,cast,choose


def noise_vectors(conditions,views,seed):
    base={}
    for video in ['004','005']:
        n=sum(r['video']==video for r in views);z=np.random.default_rng(seed+int(video)).normal(size=(n,6));base[video]=z-z.mean(0)
    records={}
    for key,config in conditions.items():
        records[key]={}
        for video in ['004','005']:
            sr,st=config['sigma'][video];records[key][video]=base[video]*np.r_[np.full(3,sr),np.full(3,st)]
    return records


def generate(task,attempt):
    cfg=task['fusion'];assets=cfg['assets'];src=json.loads(Path(assets['source_manifest']['path']).read_text());views=src['selected'];held=src['HOLDOUT']
    for row in views+held:check_sources(row)
    gt=dict(np.load(assets['virtual_gt']['path']));ring=dict(np.load(assets['ring']['path']));V,F=gt['V'],gt['F']
    public=attempt/'public';private=attempt/'private';public.mkdir();private.mkdir();(public/'observations').mkdir();(public/'camera_meshes').mkdir()
    np.savez_compressed(private/'GT_SCENE.npz',V=V,F=F);np.savez_compressed(public/'FIXED_RING.npz',**ring)
    fits=json.loads(Path(assets['image_fits']['path']).read_text());fitby={r['id']:r for r in fits if r['domain']=='synthetic'}
    index=[];clean={};audit=[];all_truth={};global_ids=np.arange(len(V))
    for i,row in enumerate(views+held):
        cid=row['view_id'];C=np.asarray(row['Camera_to_Ring']);K=np.asarray(row['K']);obs,b,rg=synthesize(V,F,ring['V'],ring['F'],K,C)
        # Reused DXY is legal only for the exact same raw observations.
        fit=fitby[cid];identity=fit['formal']['source'];rgb_sha=hashlib.sha256(obs['RGB'].tobytes()).hexdigest();mask_sha=hashlib.sha256(obs['labels'].tobytes()).hexdigest()
        require(rgb_sha==identity['RGB_content_SHA256']and mask_sha==identity['Mask_content_SHA256'],'DXY_CACHE_IDENTITY','Frozen API pixel candidate must bind the newly generated image/mask: '+cid)
        np.savez_compressed(public/'observations'/(cid+'.npz'),RGB=obs['RGB'],labels=obs['labels'],depth_axial_mm=obs['depth_axial_mm'],K=K)
        record=dict(id=cid,source_id=row['source_id'],video=row['video'],role=row['role'],K=K.tolist(),RGB_content_sha256=rgb_sha,Mask_content_sha256=mask_sha,pose_source_sha256=row['pose_origin']['sha256'])
        if row['role']=='FIT':
            mesh,info=depth_grid_mesh(obs['depth_axial_mm'],obs['labels'],K,cfg['mesh_stride_px'],cfg['mesh_edge_limit_mm']);require(len(mesh['F'])>100,'INDEPENDENT_MESH','Insufficient actual depth-grid surface: '+cid)
            np.savez_compressed(public/'camera_meshes'/(cid+'.npz'),**mesh);Ptrue=transform(mesh['V'],C);uv=mesh['uv'].astype(int)
            # Latent identities are evaluation-only, never returned with Mesh.
            np.savez_compressed(private/(cid+'_truth.npz'),Ptrue=Ptrue,uv=uv,true_C=C,gt_face=b['face'][uv[:,1],uv[:,0]],gt_bary=b['bary'][uv[:,1],uv[:,0]])
            all_truth[cid]=dict(V=Ptrue,F=mesh['F'],C=C,K=K,labels=obs['labels'],Vcam=mesh['V']);clean[cid]=mesh;record.update(vertices=len(mesh['V']),faces=len(mesh['F']))
            audit.append(dict(id=cid,**info,unproject_material_max_mm=float(np.linalg.norm(Ptrue-b['points'][uv[:,1],uv[:,0]],axis=1).max()),GT_faces_used_to_build_mesh=False))
        else:np.savez_compressed(private/(cid+'_holdout.npz'),C=C,K=K,labels=obs['labels'])
        index.append(record)
    save_json(public/'FRAME_INDEX.json',index)
    selected=[r for r in index if r['role']=='FIT'];noise=noise_vectors(cfg['conditions'],views,cfg['seed']);injection_audit={}
    for cond in cfg['condition_order']:
        folder=public/'conditions'/cond;folder.mkdir(parents=True);cameras=[];injection_audit[cond]={}
        for video in ['004','005']:
            z=noise[cond][video];injection_audit[cond][video]=dict(requested_sigma_deg_mm=cfg['conditions'][cond]['sigma'][video],**distribution(z),units=['deg','deg','deg','mm','mm','mm'],frames=[])
            rows=[r for r in views if r['video']==video];D=error_transform(*cfg['bias_parameters'][cfg['conditions'][cond]['bias'][video]])
            for j,row in enumerate(rows):
                cid=row['view_id'];C=np.asarray(row['Camera_to_Ring']);q=z[j];local=np.r_[np.deg2rad(q[:3]),q[3:]];N=se3(local);estimated=D@C@N;validate_c2w(estimated)
                mesh=clean[cid];P=transform(mesh['V'],estimated);np.savez_compressed(folder/(cid+'.npz'),V=P,F=mesh['F'],uv=mesh['uv'])
                cameras.append(dict(id=cid,video=video,K=row['K'],estimated_C=estimated.tolist(),sigma_rotation_deg=cfg['conditions'][cond]['sigma'][video][0],sigma_translation_mm=cfg['conditions'][cond]['sigma'][video][1]))
                injection_audit[cond][video]['frames'].append(dict(id=cid,noise_vector_deg_mm=q.tolist(),FrameNoise=N.tolist(),TruePose=C.tolist(),VideoBias=D.tolist(),EstimatedPose=estimated.tolist(),actual_vertex_displacement_max_mm=float(np.linalg.norm(P-all_truth[cid]['V'],axis=1).max())))
        save_json(folder/'ESTIMATED_POSES.json',cameras)
    save_json(private/'INJECTION_TRUTH.json',injection_audit)
    # Fixed GT material targets and physical observation coverage are generated
    # once; no method-dependent GT alignment or overlap threshold is permitted.
    points,ids,bary=sample_mesh(V,F,cfg['evaluation_GT_samples'],cfg['seed']+77);visible=np.zeros(len(points),bool)
    for cid,a in all_truth.items():
        uv,z=project(points,a['K'],a['C']);pix=np.rint(uv).astype(int);inside=(pix[:,0]>=0)&(pix[:,0]<640)&(pix[:,1]>=0)&(pix[:,1]<360);ix=np.where(inside)[0]
        obs=np.load(public/'observations'/(cid+'.npz'));p=pix[ix];good=(obs['labels'][p[:,1],p[:,0]]==1)&(abs(obs['depth_axial_mm'][p[:,1],p[:,0]]-z[ix])<.15);visible[ix[good]]=True
    np.savez_compressed(private/'FIXED_GT_TARGETS.npz',points=points,face=ids,bary=bary,observed=visible)
    pairs=[];(private/'overlaps').mkdir()
    for i,a in enumerate(selected):
        cid=a['id'];A=all_truth[cid];take=np.linspace(0,len(A['V'])-1,min(cfg['overlap_evaluation_samples_per_pair'],len(A['V'])),dtype=int);P=A['V'][take]
        for b in selected[i+1:]:
            B=all_truth[b['id']];uv,z=project(P,B['K'],B['C']);pix=np.rint(uv).astype(int);inside=(pix[:,0]>=0)&(pix[:,0]<640)&(pix[:,1]>=0)&(pix[:,1]<360)
            sb=scene(B['V'],B['F']);depth,face,weights=cast(sb,uv,B['K'],B['C']);valid=inside&np.isfinite(depth)&(abs(depth-z)<.15)
            in_ix=np.where(inside)[0];valid[in_ix]&=B['labels'][pix[in_ix,1],pix[in_ix,0]]==1
            valid_ix=np.where(valid)[0];key=cid+'__'+b['id'];Qcam=np.einsum('ni,nij->nj',weights[valid],B['Vcam'][B['F'][face[valid]]])if len(valid_ix)else np.empty((0,3))
            np.savez_compressed(private/'overlaps'/(key+'.npz'),source_vertex=take[valid],target_camera_points=Qcam)
            pairs.append(dict(key=key,first=cid,second=b['id'],family='within_video'if a['video']==b['video']else'cross_video',fixed_target_N=len(valid_ix)))
    save_json(private/'OVERLAP_TARGETS.json',pairs)
    directions={v:[np.asarray(r['Camera_to_Ring'])[:3,3].tolist()for r in views if r['video']==v]for v in ['004','005']}
    save_json(attempt/'GENERATION_AUDIT.json',dict(label=cfg['label'],proxy=cfg['proxy'],independent_depth_grid=True,GT_face_union_used=False,
      mesh_audit=audit,selected_views=16,HOLDOUT_views=len(held),camera_sources_unchanged=True,source_directions=directions,physical_Ring_fixed=True,
      DXY_new_calls=0,DXY_cache_exact_RGB_Mask_verified=True,GT_target_N=len(points),observed_GT_target_N=int(visible.sum()),overlap_pairs=len(pairs)))
    return outputs(attempt,dict(status='PASS',role='generator',views=16,HOLDOUT=len(held),independent_meshes=True,GT_face_union_used=False,GT_read_by_generator=True))


def body(task,attempt):
    assets=task['fusion']['assets'];freeze=json.loads(Path(assets['body_freeze']['path']).read_text());require(freeze['GT_read_by_predictor']is False,'GT_LEAK','Initializer was GT-free')
    for arm in task['fusion']['body_arms']:
        a=np.load(assets[arm+'_initializer']['path']);np.savez_compressed(attempt/(arm+'_BODY.npz'),**dict(a))
    fits=json.loads(Path(assets['image_fits']['path']).read_text());save_json(attempt/'IMAGE_FITS.json',[r for r in fits if r['domain']=='synthetic'])
    save_json(attempt/'BODY_FREEZE.json',dict(E1_sha256=sha256(attempt/'E1_BODY.npz'),E2_sha256=sha256(attempt/'E2_BODY.npz'),GT_read_by_predictor=False,
      explicitly_reused_GT_free_2D_initializers=True,source_freeze=freeze,history_measurement_fallback=0,DXY_new_calls=0,camera_optimization=False))
    return outputs(attempt,dict(status='PASS',role='predictor',body_frozen=True,GT_read_by_predictor=False,DXY_new_calls=0))
