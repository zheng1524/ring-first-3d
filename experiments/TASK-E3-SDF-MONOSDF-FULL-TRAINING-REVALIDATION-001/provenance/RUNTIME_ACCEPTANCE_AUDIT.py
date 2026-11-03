"""Read-only CPU replay; outside frozen training code, no optimization."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'code'))
from common import *
sys.path.insert(0,str(E0/'runtime/python'))
import torch
from skimage import measure
p=protocol()['geometry'];s=p['mm_per_model_unit'];C=np.array(p['C_mm'])
records=[]
for step in [0,1,10,100]:
    folder=R/'local_results'/f'single_M0_step{step:06d}'
    field=np.load(folder/f'sdf_{step}_model.npy')
    vertices,faces,_,_=measure.marching_cubes(field,level=0,spacing=(2/(field.shape[0]-1),)*3)
    vertices=(vertices-1)*s+C
    mesh=trimesh.load(folder/'raw_mm.ply',process=False)
    err=float(np.max(np.abs(mesh.vertices-vertices)))
    assert np.array_equal(faces,mesh.faces) and err<2e-6
    records.append(dict(step=step,vertices_N=len(vertices),faces_N=len(faces),mesh_inverse_max_mm=err,original_face_order_preserved=True))
a=torch.load(R/'checkpoints/single_M0/step000000.pt',map_location='cpu',weights_only=False)
b=torch.load(R/'checkpoints/single_M0/step000001.pt',map_location='cpu',weights_only=False)
changed=[k for k in a['model']if not torch.equal(a['model'][k],b['model'][k])]
assert len(changed)==len(a['model'])==37
assert a['step']==0 and b['step']==1 and b['loss_step']==1
save('metrics/OFFICIAL_RUNTIME_ACCEPTANCE.json',dict(status='PASS_EXTRACTION_AND_FIRST_REAL_UPDATE_NOT_SCIENTIFIC_CONVERGENCE',mesh_replays=records,first_update_changed_tensor_N=len(changed),changed_tensor_names=changed,step0_model_asset=asset(R/'checkpoints/single_M0/step000000.pt'),step1_model_asset=asset(R/'checkpoints/single_M0/step000001.pt'),finite_visible_sampling_guard=True,GT=False))
print('RUNTIME_ACCEPTANCE_PASS',len(records),'exact full mesh replays, real changed tensors',len(changed))
