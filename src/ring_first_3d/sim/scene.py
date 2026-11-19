"""Generator: one unchanged G01 shape, a declared shared virtual deployment."""
import json,os,subprocess
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from ..policy.contracts import ROOT,require
from ..contracts.coordinates import validate_ring,validate_c2w,unproject
from ..contracts.identities import sha256
from ..dualvideo.audit import check_sources,projection_metrics
from ..synthetic.raster import ray_map,rasterize
from ..synthetic.io import save_json,outputs
from .geometry import transform,error_transform,contour,boundary_error,choose,scene


def synthesize(V,F,RV,RF,K,C):
    body=ray_map(V,F,K,C,(360,640));ring=ray_map(RV,RF,K,C,(360,640))
    b=body['valid']&(body['z']<ring['z']);r=ring['valid']&~b
    labels=np.zeros((360,640),np.uint8);labels[b]=1;labels[r]=2
    y,x=np.mgrid[:360,:640];rgb=np.zeros((360,640,3),np.uint8);rgb[:]=[104,65,61]
    texture=(4*np.sin(x/19)*np.cos(y/17)).astype(np.int16)
    rgb=np.clip(rgb.astype(np.int16)+texture[:,:,None],0,255).astype(np.uint8)
    normals=np.cross(V[F[:,1]]-V[F[:,0]],V[F[:,2]]-V[F[:,0]]);normals/=np.maximum(np.linalg.norm(normals,axis=1)[:,None],1e-12)
    light=C[:3,3]-V.mean(0);light/=np.linalg.norm(light)
    shade=.55+.45*np.abs(normals@light)
    rgb[b]=np.clip(np.array([226,135,145])[None]*shade[body['face'][b],None],0,255).astype(np.uint8)
    rgb[r]=[24,24,24];z=np.minimum(body['z'],ring['z']);z[~np.isfinite(z)]=np.nan
    return dict(RGB=rgb,labels=labels,depth_axial_mm=z),body,ring


def local_patch(V,F,face_ids):
    selected=F[np.asarray(sorted(set(face_ids)),int)];used=np.unique(selected);remap=np.full(len(V),-1,int);remap[used]=np.arange(len(used))
    return V[used],remap[selected],used


def generate(task,attempt):
    sc=task['sim'];assets=sc['assets'];manifest=json.loads(Path(assets['source_manifest']['path']).read_text());rows=manifest['rows']
    for r in rows:check_sources(r)
    public=attempt/'public';private=attempt/'private';public.mkdir();private.mkdir();(public/'initialization').mkdir()
    request=dict(blend=assets['blend'],output=str(private));save_json(attempt/'SCENE_REQUEST.json',request)
    cmd=[assets['blender_binary']['path'],'-b','--factory-startup','--disable-autoexec','-t','2','--python',str(ROOT/'tools/research/inspect_g01_scene.py'),'--',str(attempt/'SCENE_REQUEST.json')]
    with(attempt/'blender_stdout.txt').open('w')as out:subprocess.run(cmd,stdout=out,stderr=subprocess.STDOUT,check=True,timeout=90,env=dict(os.environ,XDG_CONFIG_HOME=str(attempt/'runtime/blender')))
    fresh=np.load(private/'fresh_body_mm.npz');cache=np.load(assets['gt_cache']['path']);V0,F=fresh['V'],fresh['F']
    require(np.array_equal(F,cache['F'])and np.allclose(V0,cache['V'],rtol=0,atol=1e-10),'GT_EXPORT','Original G01 exact shape')
    rr=np.load(rows[0]['ring']['path']);RV,RF=rr['V'],rr['F'];dimensions=validate_ring(RV,10.)
    np.savez_compressed(public/'canonical_ring.npz',V=RV,F=RF)
    # Select a single static translation using FIT real silhouettes only. Never
    # modify dimensions, place separately by video, or inspect registration GT.
    placement=[]
    for translation in sc['placement_candidates_mm']:
        errors=[]
        for r in rows:
            if r['role']!='FIT':continue
            K,C=np.asarray(r['K']),np.asarray(r['Camera_to_Ring']);a=np.load(r['cache']['path']);real=contour(a['labels']==1)
            b=ray_map(V0+translation,F,K,C,(360,640));rg=ray_map(RV,RF,K,C,(360,640))
            pred=contour(b['valid']&(b['z']<rg['z']))
            errors.append(boundary_error(real,pred)['MAE']if len(real)and len(pred)else 1e6)
        placement.append(dict(translation_mm=translation,FIT_boundary_MAE_px=float(np.mean(errors))))
    winner=min(range(len(placement)),key=lambda k:(placement[k]['FIT_boundary_MAE_px'],k));offset=np.array(placement[winner]['translation_mm']);V=V0+offset
    np.savez_compressed(private/'virtual_GT.npz',V=V,F=F)
    save_json(private/'PLACEMENT_AND_TRUTH.json',dict(placements=placement,selected=winner,shared_translation_mm=offset,scale=1.,rotation=np.eye(3),label=sc['label'],real_deployment_certified=False))
    public_rows=[];visible={'004':set(),'005':set()};checks=[];quality=[]
    for row in rows:
        cid=row['view_id'];K=np.asarray(row['K']);C=np.asarray(row['Camera_to_Ring']);validate_c2w(C)
        obs,b,rg=synthesize(V,F,RV,RF,K,C)
        require(int((obs['labels']==1).sum())>100,'SIM_VISIBILITY',cid)
        y,x=np.where(obs['labels']==1);idx=np.linspace(0,len(x)-1,min(200,len(x)),dtype=int);uv=np.c_[x[idx],y[idx]]
        P=unproject(uv,obs['depth_axial_mm'][y[idx],x[idx]],K,C)
        require(np.max(np.linalg.norm(P-b['points'][y[idx],x[idx]],axis=1))<.001,'AXIAL_Z','Unprojected synthetic axial depth')
        p3d=rasterize(V,F,K,C,(360,640));common=(obs['labels']==1)&p3d['valid']
        require(common.any()and np.max(abs(p3d['z'][common]-b['z'][common]))<.002,'RENDER_CONTRACT',cid)
        if row['role']=='FIT':visible[row['video']].update(b['face'][obs['labels']==1].tolist())
        native=np.load(row['cache']['path']);realmetric=projection_metrics(native['labels']==2,rg['valid'])
        quality.append(dict(source_id=row['source_id'],role=row['role'],video=row['video'],**realmetric,realism_gate='QUALITY_ONLY_NOT_BLOCKING'))
        np.savez_compressed(public/'initialization'/(cid+'.npz'),**obs,K=K,C=C,real_RGB=native['RGB'],real_labels=native['labels'])
        np.savez_compressed(private/(cid+'.npz'),true_visible=b['valid']&(b['z']<rg['z']),face=b['face'],bary=b['bary'],points=b['points'])
        public_rows.append(dict(id=cid,video=row['video'],role=row['role'],source_id=row['source_id'],K=K.tolist(),pose_sha256=row['pose_origin']['sha256'],RGB_source_sha256=row['RGB_source']['sha256']))
        checks.append(dict(id=cid,body_pixels=int((obs['labels']==1).sum()),ray_unproject_max_mm=float(np.linalg.norm(P-b['points'][y[idx],x[idx]],axis=1).max()),independent_render_z_max_mm=float(abs(p3d['z'][common]-b['z'][common]).max())))
    save_json(public/'frame_index.json',public_rows)
    clean={}
    for video in ['004','005']:
        PV,PF,ids=local_patch(V,F,visible[video]);require(len(PF)>100,'LOCAL_MESH','Full local visible triangle patch')
        clean[video]=(PV,PF);np.savez_compressed(private/(video+'_clean.npz'),V=PV,F=PF,original_vertex_ids=ids)
    injections={}
    for condition in sc['condition_order']:
        folder=public/'conditions'/condition;folder.mkdir(parents=True)
        transforms={v:error_transform(*sc['error_transforms'][sc['conditions'][condition][v]])for v in ['004','005']};injections[condition]={v:T.tolist()for v,T in transforms.items()}
        for video in ['004','005']:
            D=transforms[video];PV,PF=clean[video]
            np.savez_compressed(folder/(video+'_mesh.npz'),V=transform(PV,D),F=PF,proxy=np.array(sc['proxy']))
            RingT=np.eye(4)if sc['family_by_condition'][condition]=='camera_local'else D
            np.savez_compressed(folder/(video+'_ring.npz'),V=transform(RV,RingT),F=RF)
        cameras=[]
        for row in rows:
            cid=row['view_id'];D=transforms[row['video']];C=np.asarray(row['Camera_to_Ring']);CE=D@C
            RingT=np.eye(4)if condition=='L1'else D
            if condition!='L1':require(np.allclose(np.linalg.inv(RingT)@CE,C,atol=1e-10),'INJECTION_PROTOCOL','Camera-to-Ring must be invariant')
            require(np.allclose((D@C)[:3,:3].T@(D@C)[:3,:3],np.eye(3),atol=1e-6),'COORDINATES','Injected rigid camera')
            cameras.append(dict(id=cid,video=row['video'],role=row['role'],K=row['K'],T_estimated=CE.tolist()))
        save_json(folder/'cameras.json',cameras)
    save_json(private/'INJECTIONS.json',injections)
    # Only image observations (no clean camera matrix) are shared with registration.
    (public/'observations').mkdir()
    for row in rows:
        a=np.load(public/'initialization'/(row['view_id']+'.npz'))
        np.savez_compressed(public/'observations'/(row['view_id']+'.npz'),RGB=a['RGB'],labels=a['labels'],depth_axial_mm=a['depth_axial_mm'],K=a['K'])
    save_json(attempt/'G0_SCENE_AUDIT.json',dict(label=sc['label'],proxy=sc['proxy'],original_shape_preserved=True,scale=1.,shared_static_placement=True,
      placement=placement,selected=winner,CAD=dimensions,source_native_pose_preserved=True,realism_quality=quality,internal_checks=checks,
      local_meshes={v:dict(vertices=len(clean[v][0]),faces=len(clean[v][1]),topology='Original visible triangle union from FIT; full mesh, reindexed only')for v in clean},
      previous_G0_failures_retained=True,real_deployment_certified=False))
    return outputs(attempt,dict(status='PASS',role='generator',label=sc['label'],source_frames=len(rows),internal_checks=checks,realism_is_blocking=False,proxy=sc['proxy']))
