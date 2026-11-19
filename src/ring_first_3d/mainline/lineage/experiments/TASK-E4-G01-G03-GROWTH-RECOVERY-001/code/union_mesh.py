"""Mature exact Boolean union with a frozen-provenance local autograd surrogate."""
from pathlib import Path
import os,json,subprocess
import numpy as np
import torch
from ring_first_3d.multisurface.geometry import scene,closest
BLENDER='/home/liu/blender/blender-5.0.1-linux-x64/blender'

class InvalidUnionCandidate(ValueError):
    """A backend result cannot be evaluated; reject it, retaining raw operands."""

def validate_boolean_result(a):
    V,F=a['V'],a['F']
    if V.ndim!=2 or V.shape[1:]!=(3,) or len(V)<4 or F.ndim!=2 or F.shape[1:]!=(3,) or len(F)<4:
        raise InvalidUnionCandidate('EMPTY_OR_MALFORMED_BOOLEAN_UNION')
    if not np.isfinite(V).all() or F.min()<0 or F.max()>=len(V):
        raise InvalidUnionCandidate('NONFINITE_OR_INVALID_BOOLEAN_UNION')

def union(original,tube,faces,folder):
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=False)
    np.savez_compressed(folder/'BODY_OPERAND.npz',V=original['V'],F=original['F_solid'])
    np.savez_compressed(folder/'SWEEP_OPERAND.npz',V=tube,F=faces)
    request=dict(body='BODY_OPERAND.npz',sweep='SWEEP_OPERAND.npz',output='UNION.npz')
    (folder/'REQUEST.json').write_text(json.dumps(request))
    command=[BLENDER,'-b','--factory-startup','--disable-autoexec','-t','2','--python',str(Path(__file__).with_name('boolean_blender.py')),'--',str(folder/'REQUEST.json')]
    with (folder/'blender_stdout.txt').open('w')as log:
        subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=60,
            env=dict(os.environ,XDG_CONFIG_HOME=str(folder/'config'),TMPDIR=str(folder)))
    a=dict(np.load(folder/'UNION.npz'));validate_boolean_result(a);F=a['F'];V=a['V']
    Q,_,fi=closest(scene(original['V'],original['F_solid']),V[F].mean(1))
    inferred=(a['face_operand']==0)&original['inferred_base_faces'][fi]&(np.linalg.norm(Q-V[F].mean(1),axis=1)<1e-4)
    # No remove_faces/fill_holes/voxel remeshing. Exact Boolean result is checked as-is.
    return dict(V=V,F=F[~inferred],F_solid=F.copy(),face_operand=a['face_operand'][~inferred],solid_face_operand=a['face_operand'],
        boundary_vertex=np.zeros(len(V),bool),inferred_base_faces=inferred)

def provenance(merged,tube,faces):
    import trimesh
    P=merged['V'];Q,_,face=closest(scene(tube,faces),P)
    bary=trimesh.triangles.points_to_barycentric(tube[faces[face]],Q)
    active=np.zeros(len(P),bool);active[np.unique(merged['F'][merged['face_operand']==1])]=True
    return dict(face=face,bary=bary,active=active,max_active_mapping_error_mm=float(np.linalg.norm(Q[active]-P[active],axis=1).max())if active.any()else 0.)

def lifted_vertices(merged,tube_tensor,faces,p):
    ids=torch.as_tensor(faces[p['face']],device=tube_tensor.device,dtype=torch.long)
    bary=torch.as_tensor(p['bary'],dtype=tube_tensor.dtype,device=tube_tensor.device)
    moving=(tube_tensor[ids]*bary[:,:,None]).sum(1);mask=torch.as_tensor(p['active'],device=tube_tensor.device)[:,None]
    const=torch.as_tensor(merged['V'],dtype=tube_tensor.dtype,device=tube_tensor.device)
    return const+torch.where(mask,moving-moving.detach(),torch.zeros_like(moving))
