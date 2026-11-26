"""Optional frozen017 classification + original018/MAX gap rule.

No surface rebuilding, vertex change, filling, or fusion. The original Raw
remains available. UNKNOWN is not classified as an error.
"""
from pathlib import Path
import types
import builtins
import json
import numpy as np
import trimesh
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.ndimage import distance_transform_edt
from . import _clean_kernels
from .geometry import unproject
from .io import save_json, sha256

def classify_native(output, ring_cad, *, mapped_input=None):
    import open3d as o3d
    root=Path(output)
    raw=mapped_input['raw'] if mapped_input is not None else dict(np.load(root/'RAW_NATIVE_MESH.npz'))
    native=mapped_input['native'] if mapped_input is not None else dict(np.load(root/'HERO_native.npz'))
    img=mapped_input['image_native'] if mapped_input is not None else dict(np.load(root/'NATIVE_RGB_LABELS.npz'))
    z=native['depth_mm'];K=native['K_index_native'];T=native['reference_pose_mm'];lab=img['labels'];rgb=img['RGB']
    protocol=json.loads(Path(__file__).with_name('cleaning_protocol.json').read_text());t=protocol['thresholds']
    cad=dict(np.load(ring_cad))
    ring=o3d.t.geometry.RaycastingScene(nthreads=1)
    ring.add_triangles(o3d.core.Tensor(np.asarray(cad['V'],np.float32)),o3d.core.Tensor(np.asarray(cad['F'],np.uint32)))
    def cast(s,uv,K,T):
        rays=np.c_[uv,np.ones(len(uv))]@np.linalg.inv(K).T
        rays=np.c_[np.broadcast_to(T[:3,3],rays.shape),rays@T[:3,:3].T]
        return s.cast_rays(o3d.core.Tensor(rays.astype(np.float32)))
    ns=dict(np=np,trimesh=trimesh,cKDTree=cKDTree,coo_matrix=coo_matrix,connected_components=connected_components,distance_transform_edt=distance_transform_edt,o3d=o3d,cast=cast,unproject=unproject,cfg=lambda:protocol['inherited_density'],__builtins__=vars(builtins))
    for name in ['face_components','edge_counts','features','native_grid','mapped_labels','topology','classify','analyze','patch_plane','gap_edges']:
        f=getattr(_clean_kernels,name);ns[name]=types.FunctionType(f.__code__,ns,name,f.__defaults__)
    # Historical classifier reads the Raw PLY as float32, then restores exact
    # generated float64 coordinates in retained exports. Preserve that behaviour.
    m=trimesh.load(mapped_input['original_mesh_path'] if mapped_input is not None else root/'Raw_open_mesh.ply',process=False);V=np.asarray(m.vertices);F=np.asarray(m.faces)
    if not np.array_equal(F,raw['F']):raise ValueError('Raw face ordering changed')
    if np.max(abs(V-raw['V']))>=1e-5:raise ValueError('Raw vertex identity mismatch')
    uv=raw['native_uv'] if mapped_input is not None else raw['uv'];s=dict(P=V,F=F,uv=uv,pack=dict(depth_mm=z,labels=lab,K=K,pose=T),T=T,K=K,Kn=K,nativez=z[uv[:,1],uv[:,0]],boundary_distance_native=distance_transform_edt(np.pad(lab==1,1))[1:-1,1:-1][uv[:,1],uv[:,0]],mask_ok=lab[uv[:,1],uv[:,0]]==1)
    if mapped_input is not None:
        # V6 builds the archived Mesh at 360 rows after linear native-depth resize.
        # Geometry/density uses that actual working lattice; native jump/gap evidence
        # uses the recorded 352-row nearest-pixel correspondence, never a renamed pack.
        work=mapped_input['working'];nuv=raw['native_uv'];uv=raw['uv']
        s=dict(P=V,F=F,uv=uv,pack=dict(depth_mm=work['depth_mm'],labels=work['labels'],K=work['K'],pose=T),T=T,K=work['K'],Kn=K,nativez=z[nuv[:,1],nuv[:,0]],boundary_distance_native=distance_transform_edt(np.pad(lab==1,1))[1:-1,1:-1][nuv[:,1],nuv[:,0]],mask_ok=lab[nuv[:,1],nuv[:,0]]==1)
    f,state,reason,top=ns['analyze'](s,ring,t)
    Pn,Fn,uvn,_=ns['native_grid'](z,lab,K,T)
    gaps,grows=ns['gap_edges'](z,lab,K,T,Pn,Fn,uvn,t)
    pix=raw['native_pixel_id'];confirmed=np.zeros(len(F),bool)
    for i,j in [(0,1),(1,2),(2,0)]:confirmed|=np.array([tuple(sorted(p))in gaps for p in pix[F[:,[i,j]]]])
    shape=(f['triangle_quality']<t['needle_quality'])|(f['normal_angle_deg']>t['neighbor_angle_deg'])|(f['normal_coherence']<t['normal_coherence'])
    material=f['CAD_inside_samples']>=t['ring_inside_samples_min']
    rej=confirmed&shape&((f['boundary_distance_native_px']<=t['edge_native_px'])|material)&f['native_mask_supported']&(~f['CAD_occluded']|material)&(f['native_depth_jump_mm']>t['native_depth_jump_mm'])&(f['perspective_stretch']>t['stretch_perspective'])
    state[rej]=2;reason[confirmed]|=1<<13;reason[rej]|=1<<14
    np.savez_compressed(root/'FACE_EVIDENCE.npz',state=state,reason_bits=reason,original_face_id=raw['original_face_id'],V=raw['V'],F=F,native_pixel_id=pix,**f)
    color_image=mapped_input['working']['RGB'] if mapped_input is not None else rgb
    colors=np.c_[color_image[raw['uv'][:,1],raw['uv'][:,0]],np.full(len(raw['uv']),255)]
    for name,sel in [('Trusted_visible_mesh',state==0),('Conservative_cleaned_mesh',state!=2),('Uncertain',state==1),('Rejected',state==2),('Unknown',state==3)]:
        if sel.any():trimesh.Trimesh(raw['V'],F[sel],vertex_colors=colors,process=False).export(root/(name+'.ply'))
    rec=dict(protocol_sha256=sha256(Path(__file__).with_name('cleaning_protocol.json')),raw_preserved=True,retained_vertices_unchanged=True,counts={name:int((state==i).sum())for i,name in enumerate(['TRUSTED','UNCERTAIN','REJECTED','UNKNOWN'])},confirmed_gap_edges=len(gaps),UNKNOWN_is_not_error=True,conservative_retains_unknown=True,input_contract='V6 archived 360-row original mesh + explicit 352 native mapping' if mapped_input is not None else 'native mesh')
    save_json(root/'CLEANING.json',rec)
    return rec
