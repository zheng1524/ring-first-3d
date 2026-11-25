"""Read the frozen 004 native format; rigidly transport a whole video."""
import json
from pathlib import Path
import numpy as np
from PIL import Image
from pilot import TASK,REPO,sha
from ring_first_3d.contracts.coordinates import validate_c2w,unproject
from ring_first_3d.sim.geometry import transform

def load_snapshot():
    root=TASK/'fixtures/snapshot004'
    for r in json.loads((TASK/'evidence/SNAPSHOT_PROTECTION.json').read_text()):
        if sha(REPO/r['retained'])!=r['sha256']:raise ValueError('SNAPSHOT_DRIFT')
    m=json.loads((root/'DATA_MANIFEST.json').read_text())
    if m['unit']!='mm':raise ValueError('Explicit mm required')
    cameras=np.stack([validate_c2w(f['c2w_mm']) for f in m['frames']])
    frames=[]
    for f in m['frames']:
        rgb=np.asarray(Image.open(root/f['rgb']).convert('RGB'));labels=np.asarray(Image.open(root/f['labels']))
        if list(labels.shape)!=m['work_hw'] or rgb.shape[:2]!=labels.shape:raise ValueError('IMAGE_SIZE')
        frames.append(dict(f,RGB=rgb,labels=labels,K=np.array(f['K'])))
    h=dict(np.load(root/'HERO_native.npz'));mesh=dict(np.load(root/'RAW_NATIVE_MESH.npz'));land=dict(np.load(root/'REFERENCE_RGB_MAP.npz'));ring=dict(np.load(root/'RING_CAD.npz'))
    if str(h['unit'])!='mm' or str(h['depth_definition'])!='camera axial Z':raise ValueError('HERO units/depth definition')
    if list(h['depth_mm'].shape)!=m['native_hw']:raise ValueError('NATIVE_SIZE')
    np.testing.assert_allclose(h['reference_pose_mm'],cameras[0],atol=1e-10,rtol=0)
    np.testing.assert_allclose(h['source_poses_mm'],cameras[1:],atol=1e-10,rtol=0)
    np.testing.assert_allclose(mesh['K'],h['K_index_native'],atol=1e-10,rtol=0)
    np.testing.assert_allclose(mesh['T'],cameras[0],atol=1e-10,rtol=0)
    uv=mesh['uv'];z=h['depth_mm'][uv[:,1],uv[:,0]]
    np.testing.assert_allclose(unproject(uv,z,mesh['K'],mesh['T']),mesh['V'],atol=1e-9,rtol=0)
    return dict(cameras=cameras,landmarks=land['X'],hero=mesh['V'],ring=ring['V'],frames=frames,faces=mesh['F'],ring_faces=ring['F'],manifest=m,hero_observation=h)

def move_video(snapshot,H):
    H=validate_c2w(H)
    result=dict(snapshot)
    result['cameras']=H@np.asarray(snapshot['cameras'])
    for k in ['landmarks','hero','ring']:result[k]=transform(snapshot[k],H)
    if 'frames' in snapshot:
        result['frames']=[dict(f,c2w_mm=result['cameras'][i].tolist()) for i,f in enumerate(snapshot['frames'])]
    if 'hero_observation' in snapshot:
        h=snapshot['hero_observation']
        result['hero_observation']=dict(h,reference_pose_mm=H@h['reference_pose_mm'],source_poses_mm=H@h['source_poses_mm'])
    # manifest remains immutable source provenance, not the transported camera contract.
    return result
