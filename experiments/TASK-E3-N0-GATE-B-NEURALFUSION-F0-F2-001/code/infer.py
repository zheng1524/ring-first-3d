"""Official pretrained forward; exact official translator; no optimizer or GT."""
from common import *
import argparse,traceback
os.environ.update(CUDA_VISIBLE_DEVICES='0',TORCH_HOME=str(R/'runtime/cache/torch'),CUDA_CACHE_PATH=str(R/'runtime/cache/cuda'))
sys.path[:0]=[str(GA/'runtime/python'),str(NF),str(R/'runtime/python')]
import torch
from easydict import EasyDict
from pipeline.pipeline import FusionPipeline
from pipeline.utils import unproject as official_unproject
from evaluate import evaluate
from skimage.measure import marching_cubes
extract(R/'runtime/official_readonly/training_utils.py',['get_translation'],globals())

class Namespace(torch.nn.Module):
    def __init__(self,c):
        super().__init__();self._pipeline=FusionPipeline(c)

def main(v,stage):
    assert not (R/f'NN_{v}_{stage}_RUN.json').exists(),'DO_NOT_REPEAT_PREFIX'
    if stage!='F0':
        assert load(R/'NN_V6_F0_METRICS.json')['F0_pass'],'PRIMARY_F0_FAILED_STOP_NEW_VIEWS'
        previous='F'+str(int(stage[1:])-1)
        assert load(R/f'NN_{v}_{previous}_METRICS.json')['progression_ok'],'PREVIOUS_PREFIX_FAILED_STOP'
    protocol=cfg();checkpoint=protocol['checkpoint'];assert sha(checkpoint['path'])==checkpoint['sha256']
    torch.set_num_threads(2);torch.manual_seed(42);torch.backends.cudnn.benchmark=False
    device=torch.device('cuda:0');torch.cuda.set_device(device);torch.cuda.reset_peak_memory_stats()
    config=EasyDict(load(NF/'pretrained_models/shapenet_noise_005/version_0/config.json'))
    config.PIPELINE.device=device
    with torch.serialization.safe_globals([EasyDict]):ckpt=torch.load(checkpoint['path'],map_location='cpu',weights_only=True)
    model=Namespace(config.PIPELINE);loaded=model.load_state_dict(ckpt['state_dict'],strict=True)
    assert not loaded.missing_keys and not loaded.unexpected_keys
    model.requires_grad_(False);model.eval();model.to(device);pipe=model._pipeline
    assert not any(p.requires_grad for p in model.parameters())
    dom=protocol['domain'];L=dom['L_mm'];O=np.array(dom['O_mm']);N=128
    if stage=='F0':
        volume=torch.zeros(N,N,N,17,device=device);count=torch.zeros(N,N,N,device=device)
        assert not volume.any()and not count.any();pipe.reset()
    else:
        prior=np.load(R/'local_results'/f'NN_{v}_{previous}_latent.npz')
        volume=torch.from_numpy(prior['latent']).to(device);count=torch.from_numpy(prior['count']).to(device)
    cid=protocol['sequences'][stage][-1];c=crop(cid,v);K,T=camera(cid);TM=T.copy();TM[:3,3]=(TM[:3,3]-O)/L
    data=dict(input=torch.from_numpy(c['depth_mm'].copy()/L).unsqueeze(0).to(device),
        original_mask=torch.from_numpy(c['valid'].astype(np.float32)).unsqueeze(0).to(device),
        intrinsics=torch.from_numpy(c['K_crop'].astype(np.float32)).unsqueeze(0).to(device),
        extrinsics=torch.from_numpy(TM.astype(np.float32)).unsqueeze(0).to(device),
        origin=torch.zeros(1,1,3,device=device),resolution=1/N,volume=volume,count=count)
    files=[asset(p)for p in sorted((R/'code').glob('*.py'))]
    save(f'provenance/BEFORE_NN_{v}_{stage}.json',dict(code=files,protocol=asset(R/'config/PREREGISTERED.json'),input=asset(R/'frozen_inputs'/v/'crops'/(cid+'.npz')),checkpoint=checkpoint,parameter_updates_allowed=False))
    t0=time.monotonic()
    with torch.inference_mode():
        # Check the actual official GPU unprojection, not only an adapter formula.
        Xg=official_unproject(data['input'],data['extrinsics'],data['intrinsics'],data['origin'],1/N,device)
        actual=Xg[0].cpu().numpy().reshape(240,320,3)[c['valid']]/N*L+O
        projection_error=float(np.linalg.norm(actual-c['output_X_mm'],axis=1).max());assert projection_error<1e-4
        updated,updates,count=pipe.forward(data);torch.cuda.synchronize()
        fusion_seconds=time.monotonic()-t0
        assert torch.isfinite(updated).all()
        known=(updated.abs().sum(1)[0]>0).cpu().numpy()
        translated=get_translation(pipe,updated,config)
        field=translated[0].detach().cpu().numpy();assert np.isfinite(field).all()
        sdf=field[0].copy();sdf[~known]=config.LOSS.max_clamp
        assert (sdf<0).any()and(sdf>0).any(),'NO_ZERO_LEVEL_SET'
        verts,faces,normals,_=marching_cubes(sdf,level=0,allow_degenerate=False)
        P=verts/N*L+O
        mesh=trimesh.Trimesh(P,faces,process=False)
        # Preserve the complete official masked-SDF mesh, including uncertain caps.
        mesh.export(R/'meshes'/f'NN_{v}_{stage}_mm.ply')
        mesh.export(R/'meshes'/f'NN_{v}_{stage}_mm.glb')
        cell=np.floor(verts[faces].mean(1)).astype(int);cell=np.clip(cell,0,N-2)
        allknown=np.ones(len(faces),bool)
        for x in [0,1]:
            for y in [0,1]:
                for z in [0,1]:allknown&=known[cell[:,0]+x,cell[:,1]+y,cell[:,2]+z]
        table(f'NN_{v}_{stage}_FACE_VALIDITY.csv',[dict(original_output_face_id=int(j),all8_cell_corners_observed=bool(a),unknown_boundary_proxy=not bool(a))for j,a in enumerate(allknown)])
        latent=updated[0].permute(1,2,3,0).contiguous().cpu().numpy()
        np.savez_compressed(R/'local_results'/f'NN_{v}_{stage}_latent.npz',latent=latent,count=count.cpu().numpy())
        np.savez_compressed(R/'local_results'/f'NN_{v}_{stage}_field.npz',sdf_raw=field[0],occupancy_raw=field[1],known=known,sdf_official_unknown_positive_sentinel=sdf)
    assert all(torch.equal(value.cpu(),ckpt['state_dict'][key])for key,value in model.state_dict().items()),'MODEL_PARAMETER_CHANGED'
    assert sha(checkpoint['path'])==checkpoint['sha256']
    run=dict(method='OFFICIAL_FUSION_PIPELINE_AND_TRANSLATOR',version=v,stage=stage,sources=protocol['sequences'][stage],
        new_forward_source=cid,model_parameters=sum(p.numel()for p in model.parameters()),strict_loading=True,
        official_GPU_unprojection_error_max_mm=projection_error,fusion_seconds=fusion_seconds,total_seconds=time.monotonic()-t0,
        peak_GPU_allocated_MiB=torch.cuda.max_memory_allocated()/2**20,peak_GPU_reserved_MiB=torch.cuda.max_memory_reserved()/2**20,
        observed_voxel_N=int(known.sum()),negative_sdf_voxel_N=int((sdf<0).sum()),known_SDF_range=[float(field[0][known].min()),float(field[0][known].max())],
        complete_mesh_faces=len(faces),unknown_boundary_face_N=int((~allknown).sum()),all_mesh_faces_preserved=True,
        learned_parameters_bitwise_unchanged=True,checkpoint_SHA_unchanged=True,optimizer_steps=0,
        eval_mode=True,inference_mode=True,GT_read=False,torch=torch.__version__,GPU=torch.cuda.get_device_name())
    save(f'NN_{v}_{stage}_RUN.json',run);print('NN_FORWARD_DONE',run,flush=True)
    del data,volume,updated,model,translated;torch.cuda.empty_cache()
    evaluate('NN',v,stage)
    save(f'provenance/NN_{v}_{stage}_ACCESS.json',dict(read_files=sorted(ACCESSED),training_imported=any(k.startswith('training.')for k in sys.modules),optimizer_steps=0))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('version',choices=['V6','V2']);p.add_argument('stage',choices=['F0','F1','F2']);a=p.parse_args()
    try:main(a.version,a.stage)
    except Exception:
        save(f'NN_{a.version}_{a.stage}_EXECUTION_FAILURE.json',dict(traceback=traceback.format_exc(),stage=a.stage,version=a.version,optimizer_steps=0));raise
