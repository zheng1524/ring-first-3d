"""Complete official pretrained sequential prefixes, followed by independent reverse."""
from common import *
import argparse,traceback
os.environ.update(CUDA_VISIBLE_DEVICES='0',TORCH_HOME=str(R/'runtime/cache/torch'),CUDA_CACHE_PATH=str(R/'runtime/cache/cuda'))
sys.path[:0]=[str(GA/'runtime/python'),str(RB/'runtime/python'),str(NF)]
import torch
from easydict import EasyDict
from pipeline.pipeline import FusionPipeline
from pipeline.utils import unproject as official_unproject
from skimage.measure import marching_cubes
extract(R/'runtime/official_readonly/training_utils.py',['get_translation'],globals())
class Namespace(torch.nn.Module):
    def __init__(self,c):super().__init__();self._pipeline=FusionPipeline(c)
def instrument(pipe):
    """Wrappers call the unchanged bound methods; direct .forward calls are counted."""
    events=[]
    for name in ['_extractor','_fusion','_integrator','_translator']:
        module=getattr(pipe,name);fn=module.forward
        def wrapper(*args,_fn=fn,_name=name,**kw):
            out=_fn(*args,**kw)
            events.append(dict(module=_name,input_shapes=[list(a.shape)for a in args if torch.is_tensor(a)],output_shape=list(out.shape)if torch.is_tensor(out)else None))
            return out
        module.forward=wrapper
    return events
def run(scene,order):
    p=protocol();source_order=p['orders'][scene]if order=='forward'else p['reverse_orders'][scene];checkpoint=p['checkpoint'];assert sha(checkpoint['path'])==checkpoint['sha256']
    assert sha(R/'config/EXPERIMENT_FROZEN.json')==load(R/'provenance/BEFORE_GPU.json')['protocol']['sha256']
    for a in load(R/'provenance/BEFORE_GPU.json')['inputs']:
        old=Path(a['path']);assert sha(R/'frozen_inputs'/old.parent.name/old.name)==a['sha256']
    torch.set_num_threads(2);torch.manual_seed(42);torch.backends.cudnn.benchmark=False;device=torch.device('cuda:0');torch.cuda.set_device(device)
    config=EasyDict(load(NF/'pretrained_models/shapenet_noise_005/version_0/config.json'));config.PIPELINE.device=device
    with torch.serialization.safe_globals([EasyDict]):ckpt=torch.load(checkpoint['path'],map_location='cpu',weights_only=True)
    model=Namespace(config.PIPELINE);model.load_state_dict(ckpt['state_dict'],strict=True);model.requires_grad_(False);model.eval();model.to(device);pipe=model._pipeline;events=instrument(pipe)
    assert not any(a.requires_grad for a in model.parameters());N=128;dom=p['domains'][scene];L=dom['L_mm'];O=np.array(dom['O_mm'])
    volume=torch.zeros(N,N,N,17,device=device);count=torch.zeros(N,N,N,device=device);pipe.reset();assert not volume.any()and not count.any()
    sequence=dict(scene=scene,order=order,sources=source_order,empty_initial_latent=True,empty_initial_count=True,seed=42)
    save(f'provenance/{scene}_{order}_SEQUENCE_START.json',dict(**sequence,code=[asset(x)for x in (R/'code').glob('*.py')],protocol=asset(R/'config/EXPERIMENT_FROZEN.json'),checkpoint=checkpoint))
    for i,cid in enumerate(source_order):
        tag=f'{scene}_{order}_F{i}';assert not (R/f'metrics/{tag}_RUN.json').exists(),'DO_NOT_OVERWRITE_COMPLETED_PREFIX'
        torch.cuda.reset_peak_memory_stats();event_start=len(events);t0=time.monotonic();c=crop(cid);T=source(cid)['T'].copy();T[:3,3]=(T[:3,3]-O)/L
        data=dict(input=torch.from_numpy(c['depth_mm'].copy()/L).unsqueeze(0).to(device),original_mask=torch.from_numpy(c['valid'].astype(np.float32)).unsqueeze(0).to(device),intrinsics=torch.from_numpy(c['K_crop'].astype(np.float32)).unsqueeze(0).to(device),extrinsics=torch.from_numpy(T.astype(np.float32)).unsqueeze(0).to(device),origin=torch.zeros(1,1,3,device=device),resolution=1/N,volume=volume,count=count)
        with torch.inference_mode():
            Xg=official_unproject(data['input'],data['extrinsics'],data['intrinsics'],data['origin'],1/N,device)
            actual=Xg[0].cpu().numpy().reshape(240,320,3)[c['valid']]/N*L+O;err=float(np.linalg.norm(actual-c['output_X_mm'],axis=1).max());assert err<1e-4,'INVALID_METRIC_UNPROJECTION'
            updated,updates,count=pipe.forward(data);torch.cuda.synchronize();fusion_seconds=time.monotonic()-t0;assert torch.isfinite(updated).all()
            known=(updated.abs().sum(1)[0]>0).cpu().numpy();translated=get_translation(pipe,updated,config);field=translated[0].cpu().numpy();assert np.isfinite(field).all()
            sdf=field[0].copy();sdf[~known]=config.LOSS.max_clamp
            zero_cross=bool((sdf<0).any()and(sdf>0).any())
            if zero_cross:verts,faces,normals,_=marching_cubes(sdf,level=0,allow_degenerate=False)
            else:verts=np.empty((0,3),np.float32);faces=np.empty((0,3),np.int32);normals=np.empty((0,3),np.float32)
            P=verts/N*L+O;m=trimesh.Trimesh(P,faces,process=False)
            # All three deliverables preserve exactly the same interpolated vertices/topology.
            m.export(R/'meshes'/f'{tag}_raw_mm.ply',vertex_normal=False)
            m.export(R/'meshes'/f'{tag}_flat_mm.ply',vertex_normal=False)
            m.export(R/'meshes'/f'{tag}_smooth_normals_mm.ply',vertex_normal=True)
            model_m=trimesh.Trimesh(P*.001,faces,process=False);model_m.export(R/'meshes'/f'{tag}_SI_m.glb')
            cell=np.clip(np.floor(verts[faces].mean(1)).astype(int),0,N-2);allknown=np.ones(len(faces),bool)
            for x in [0,1]:
                for y in [0,1]:
                    for z in [0,1]:allknown&=known[cell[:,0]+x,cell[:,1]+y,cell[:,2]+z]
            latent=updated[0].permute(1,2,3,0).contiguous().cpu().numpy();np.savez_compressed(R/'local_results'/f'{tag}_latent.npz',latent=latent,count=count.cpu().numpy())
            np.savez_compressed(R/'local_results'/f'{tag}_field.npz',sdf_raw=field[0],occupancy_raw=field[1],known=known,sdf_MC_unknown_positive_sentinel=sdf)
            np.savez_compressed(R/'local_results'/f'{tag}_MC_identity.npz',vertices_index_float=verts,vertices_mm=P,faces=faces,normals_MC=normals,face_all8_corners_known=allknown)
            volume=updated[0].permute(1,2,3,0).contiguous()
        assert all(torch.equal(v.cpu(),ckpt['state_dict'][k])for k,v in model.state_dict().items()),'WEIGHT_CHANGED'
        actual_events=events[event_start:];assert [r['module']for r in actual_events]==['_extractor','_fusion','_integrator','_translator'],'OFFICIAL_CHAIN_NOT_EXECUTED'
        saved=[asset(R/'local_results'/f'{tag}_{suffix}.npz')for suffix in ['latent','field','MC_identity']]
        run=dict(tag=tag,scene=scene,order=order,stage='F'+str(i),sources=source_order[:i+1],source_added=cid,actual_official_call_events=actual_events,Translator_query_N=int(known.sum()),known_voxel_N=int(known.sum()),latent_shape=list(latent.shape),count_external_max=float(count.max()),latent_count_channel_max=float(latent[:,:,:,-1].max()),negative_known_SDF_N=int(((field[0]<0)&known).sum()),SDF_known_range=[float(field[0][known].min()),float(field[0][known].max())],zero_cross=zero_cross,vertices_N=len(P),faces_N=len(faces),unknown_boundary_face_N=int((~allknown).sum()),fractional_MC_vertices_N=int((abs(verts-np.round(verts))>1e-5).any(1).sum()),official_GPU_unprojection_max_mm=err,fusion_seconds=fusion_seconds,total_seconds=time.monotonic()-t0,peak_GPU_MiB=torch.cuda.max_memory_allocated()/2**20,weights_bitwise_unchanged=True,strict_parameter_N=sum(x.numel()for x in model.parameters()),optimizer_steps=0,GT=False,quality_stop=False,saved_states=saved,shading_geometry_identical=True)
        save(f'metrics/{tag}_RUN.json',run);print('OFFICIAL_PREFIX_DONE',tag,cid,'known',int(known.sum()),'faces',len(faces),'GPU_MiB',round(run['peak_GPU_MiB'],1),flush=True)
        del data,Xg,updates,translated,updated;torch.cuda.empty_cache()
    assert sha(checkpoint['path'])==checkpoint['sha256'];save(f'provenance/{scene}_{order}_SEQUENCE_DONE.json',dict(**sequence,completed_prefixes=len(source_order),weights_unchanged=True,optimizer_steps=0,read_files=sorted(ACCESSED),denials=DENIALS))
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('scene');parser.add_argument('order',choices=['forward','reverse']);a=parser.parse_args()
    try:run(a.scene,a.order)
    except Exception:
        save(f'metrics/{a.scene}_{a.order}_EXECUTION_FAILURE.json',dict(traceback=traceback.format_exc(),optimizer_steps=0));raise
