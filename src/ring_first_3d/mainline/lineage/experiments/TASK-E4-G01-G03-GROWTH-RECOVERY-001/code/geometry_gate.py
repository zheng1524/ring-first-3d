"""Expected internal overlap is allowed; final external union is checked in full."""
from ring_first_3d.mainline.paths import historical_path as _mainline_path
import numpy as np
import torch
import trimesh
from io_utils import legacy
from lengths import measure
from ring_collision_gate import signed,samples
from ring_first_3d.multisurface.geometry import scene,closest
SAFE=str(_mainline_path('/home/liu/ring_first_3d_structural_update/experiments/TASK-E4-2D-CONTOUR-GUIDED-INIT-A-HERO-001/legacy015/safe_geometry.py'))

def namespace(): return legacy.legacy_geometry(SAFE)

def exterior_clearance(tube,info,configuration,original,length):
    C=info['centerline'];P=tube[:240].reshape(15,16,3)
    engine=scene(original['V'],original['F_solid'])
    center_phi=signed(engine,C.detach().cpu().numpy())
    offset=P.detach().cpu().numpy()-np.array(configuration['exit_reference'])
    near=(np.linalg.norm(offset,axis=2)<=configuration['attachment_region_radius_mm'])&((offset@np.array(configuration['direction']))<=configuration['overlap_transition_mm'])
    phase=np.linspace(0,1,16)[:15];after=phase>length['exit_parameter']
    dist=signed(engine,P.detach().cpu().numpy());bad=(dist< -1e-5)&after[:,None]&~near
    # Local differentiable SDF surrogate from actual closest original triangles.
    Q,_,_=closest(engine,P.detach().cpu().numpy().reshape(-1,3));q=torch.as_tensor(Q.reshape(15,16,3),dtype=P.dtype,device=P.device)
    direction=P.detach()-q;norm=torch.linalg.vector_norm(direction,dim=2,keepdim=True).clamp_min(1e-8)
    sign=torch.as_tensor(np.sign(dist),dtype=P.dtype,device=P.device)[:,:,None]
    normal=direction/norm*sign
    phi=torch.as_tensor(dist,dtype=P.dtype,device=P.device)+((P-P.detach())*normal).sum(2)
    active=torch.as_tensor(after[:,None]&~near,device=P.device)
    penalty=torch.relu(-phi-1e-5).square()[active].mean()if active.any()else P.sum()*0
    return penalty,dict(unexpected_exterior_inside_samples=int(bad.sum()),centerline_phi_mm=center_phi.tolist(),
        expected_internal_samples=int(((dist<0)&near).sum()),transition_region_radius_mm=configuration['attachment_region_radius_mm'])

def check(merged,tube,faces,original,initial,configuration,base,chart,ns):
    reasons=[];V=merged['V'];F=merged['F_solid'];m=trimesh.Trimesh(V,F,process=False)
    tri=V[F];normal=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);area=np.linalg.norm(normal,axis=1)*.5
    _,count=np.unique(np.sort(m.edges,axis=1),axis=0,return_counts=True)
    nonmanifold=int((count!=2).sum());duplicate=int(len(F)-len(np.unique(np.sort(F,axis=1),axis=0)))
    if not m.is_watertight:reasons.append('OPEN_UNION')
    if not m.is_winding_consistent or m.volume<=0:reasons.append('UNION_WINDING')
    if len(m.split(only_watertight=False))!=1:reasons.append('DISCONNECTED_UNION')
    if nonmanifold:reasons.append('NONMANIFOLD_UNION')
    if duplicate:reasons.append('INTERNAL_DUPLICATE_FACES')
    if area.min()<5e-9:reasons.append('DEGENERATE_TRIANGLES')
    intersections=ns['self_intersections'](V,F)['intersections']
    own=ns['self_intersections'](tube,faces)['intersections']
    if intersections:reasons.append('UNEXPECTED_UNION_SELF_INTERSECTION')
    if own:reasons.append('SWEEP_SELF_INTERSECTION')
    engine=scene(V,F);P=samples(original['V'],original['F_solid']).reshape(-1,3)
    outer=np.linalg.norm(P-np.array(configuration['exit_reference']),axis=1)>configuration['attachment_region_radius_mm']
    Q,_,_=closest(engine,P[outer]);preserved=float(np.linalg.norm(Q-P[outer],axis=1).max())if outer.any()else 0.
    if preserved>1e-5:reasons.append('FROZEN_BODY_EFFECTIVE_REGION_CHANGED')
    # Body operands are immutable; new surfaces must respect the inherited base halfspace.
    if initial['inferred_base_faces'].any():
        plane=np.asarray(base['selected_plane']);minimum=float((V@plane[:3]+plane[3]).min())
        if minimum< -1e-5:reasons.append('BASE_HALFSPACE')
        rim=original['V'][initial['boundary_vertex']];QQ,_,_=closest(engine,rim)
        if np.linalg.norm(QQ-rim,axis=1).max()>1e-5:reasons.append('BASE_BOUNDARY_CHANGED')
    else:minimum=None
    added=float(m.volume-trimesh.Trimesh(original['V'],original['F_solid'],process=False).volume)
    if added< -1e-5:reasons.append('BOOLEAN_REMOVED_BODY_VOLUME')
    return sorted(set(reasons)),dict(watertight=bool(m.is_watertight),winding_consistent=bool(m.is_winding_consistent),nonmanifold_edges=nonmanifold,
        duplicate_faces=duplicate,self_intersections=int(intersections),sweep_self_intersections=int(own),minimum_triangle_area_mm2=float(area.min()),
        preserved_original_surface_max_error_mm=preserved,base_halfspace_min_mm=minimum,volume_mm3=float(m.volume),added_volume_mm3=added,
        added_surface_area_mm2=float(m.area-trimesh.Trimesh(original['V'],original['F_solid'],process=False).area),
        new_vertices_net=int(len(V)-len(original['V'])),new_faces_net=int(len(F)-len(original['F_solid'])))
