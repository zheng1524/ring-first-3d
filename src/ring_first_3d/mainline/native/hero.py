"""Exact historical HERO loader/input choices, calling external official code.

The weights and third-party full source are never bundled by this project.
All learned weights are loaded; only three resolution-dependent coordinate
buffers can be regenerated, as in the frozen adapter.
"""
from pathlib import Path
import copy
import contextlib
import importlib
import importlib.util
import json
import subprocess
import sys
import time
import numpy as np
from .io import sha256, save_json
from .geometry import native_rgb_labels, depth_mesh,validate_camera

CHECKPOINT_SHA256='00878bab903b1d384cd6bb9ea092e247a9036d429cb8bcc3d6dcbb81f67e556d'
UPSTREAM_COMMIT='5bd49bba0992aa56060e1aa3bb40b2150b04726f'

def verify_source(root, manifest):
    root=Path(root).resolve();checked=0
    for row in manifest['matched']:
        p=root/row['path']
        if sha256(p)!=row['sha256']:raise ValueError('Official code differs: '+row['path'])
        checked+=1
    return dict(files_verified=checked,upstream_commit=UPSTREAM_COMMIT,verification='per-file SHA256, not parent-directory git rev-parse')

def load_official(mvs_root, checkpoint_path, dino_root, manifest, size=(352,640)):
    import torch
    mvs_root=Path(mvs_root).resolve();dino_root=Path(dino_root).resolve()
    receipt=verify_source(mvs_root,manifest)
    dino=manifest.get('dinov2',{})
    if dino.get('different'):raise ValueError('Unresolved DINO source differences in version lock')
    for row in dino.get('matched',[]):
        if sha256(dino_root/row['path'])!=row['sha256']:raise ValueError('DINO code differs: '+row['path'])
    receipt.update(dinov2_commit=dino.get('upstream_commit'),dinov2_files_verified=len(dino.get('matched',[])))
    if sha256(checkpoint_path)!=CHECKPOINT_SHA256:raise ValueError('HERO checkpoint SHA256 mismatch')
    sys.path[:0]=[str(mvs_root/'src'),str(mvs_root)]
    import torchvision, antialiased_cnns
    from mvsanywhere.experiment_modules.sr_depth_model import DepthModel
    from torchvision import transforms as T
    spec=importlib.util.spec_from_file_location('_ring_first_official_hubconf',mvs_root/'hubconf.py')
    hub=importlib.util.module_from_spec(spec);spec.loader.exec_module(hub)
    # Only the exact verified, researcher-provided pickle is accepted.
    ck=torch.load(checkpoint_path,map_location='cpu',weights_only=False,mmap=True)
    opts=copy.deepcopy(ck['hyper_parameters']['opts']);opts.image_height,opts.image_width=size
    opts.prediction_scale=1.;opts.da_weights_path=None;opts.fast_cost_volume=False
    original_hub=torch.hub.load
    def local_dino(repo,name,*args,**kwargs):
        if repo=='facebookresearch/dinov2':return original_hub(str(dino_root),name,source='local',pretrained=False)
        return original_hub(repo,name,*args,**kwargs)
    originals={};aa_originals={};torch.hub.load=local_dino
    for key in ['resnet18','resnet34','resnet50','resnet101','resnet152']:
        orig=getattr(torchvision.models,key);originals[key]=orig
        def create(*args,_orig=orig,**kwargs):return _orig(weights=None)
        setattr(torchvision.models,key,create)
    for key in ['resnet18','resnet34','resnet50','resnet101','resnet152']:
        if not hasattr(antialiased_cnns,key):continue
        orig=getattr(antialiased_cnns,key);aa_originals[key]=orig
        def create_aa(*args,_orig=orig,**kwargs):
            kwargs.pop('pretrained',None)
            if args:args=(False,)+args[1:]
            else:kwargs['pretrained']=False
            return _orig(*args,**kwargs)
        setattr(antialiased_cnns,key,create_aa)
    try:model=DepthModel(opts)
    finally:
        torch.hub.load=original_hub
        for key,orig in originals.items():setattr(torchvision.models,key,orig)
        for key,orig in aa_originals.items():setattr(antialiased_cnns,key,orig)
    state=ck['state_dict'];expected=model.state_dict();ignored={}
    for key in list(state):
        if key in expected and state[key].shape!=expected[key].shape:
            if key in dict(model.named_parameters()) or key not in ['compute_normals.backproject.pix_coords_13N','mv_depth_loss.backproject.pix_coords_13N','cost_volume.backprojector.pix_coords_13N']:
                raise ValueError('Unsupported checkpoint shape mismatch: '+key)
            ignored[key]=list(state[key].shape);state.pop(key)
    incompatible=model.load_state_dict(state,strict=False)
    if not all(k in ignored for k in incompatible.missing_keys) or incompatible.unexpected_keys:
        raise ValueError('Checkpoint state mismatch: '+str(incompatible))
    if not set(dict(model.named_parameters()))<=set(state):raise ValueError('Missing learned parameters')
    model.cost_volume.matching_height=-1;model.cost_volume.matching_width=-1
    model.depth_decoder.set_prediction_scale(1.)
    wrapper=hub.MVSAnywhereInference.__new__(hub.MVSAnywhereInference)
    torch.nn.Module.__init__(wrapper);wrapper.model=torch.nn.DataParallel(model).to('cuda').eval()
    wrapper.normalize=T.Normalize(mean=[.485,.456,.406],std=[.229,.224,.225])
    wrapper.input_transform=T.Compose([T.ToTensor(),wrapper.normalize])
    receipt.update(checkpoint_SHA256=CHECKPOINT_SHA256,all_learned_parameters_loaded=len(dict(model.named_parameters())),learned_parameter_elements=sum(p.numel()for p in model.parameters()),regenerated_fixed_buffers=ignored,actual_source_views=3,fast_cost_volume=False,weights_updated=False)
    return wrapper,receipt

def infer(model, frames, output):
    """frames: target first, then exactly three source frames with RGB/labels/K/c2w."""
    import torch
    if len(frames)!=4:raise ValueError('Frozen adapter requires exactly one target plus three supports')
    for f in frames:
        if f['RGB'].shape!=(360,640,3) or f['labels'].shape!=(360,640):raise ValueError('Expected 640x360 work RGB and labels')
        validate_camera(f['c2w_mm'],f['K'])
    target=frames[0];supports=frames[1:];C=np.array(target['c2w_mm']);Cs=np.array([f['c2w_mm']for f in supports])
    pm=C.copy();pm[:3,3]/=1000.;ps=Cs.copy();ps[:,:3,3]/=1000.
    k=np.eye(4);k[:3,:3]=target['K'];k[:2,2]+=.5
    # Exact frozen adapter: same calibrated K in all four work frames.
    if not all(np.array_equal(f['K'],target['K'])for f in supports):raise ValueError('Frozen adapter requires common work K')
    ks=np.repeat(k[None],3,axis=0);torch.cuda.reset_peak_memory_stats();start=time.time()
    with torch.inference_mode(),torch.autocast('cuda',dtype=torch.float16):
        out=model.preprocess_and_run(cur_image=np.array(target['RGB']).copy(),src_image=[np.array(f['RGB']).copy()for f in supports],cur_pose=pm.copy(),src_pose=ps.copy(),cur_intrinsics=k.copy(),src_intrinsics=ks.copy(),depth_range=None,num_refinement_steps=1,target_image_size=[352,640],device='cuda')
    torch.cuda.synchronize();depth=np.squeeze(out['depth'].float().cpu().numpy())*1000
    if depth.shape!=(352,640) or not (np.isfinite(depth)&(depth>0)).any():raise ValueError('Invalid native HERO output')
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    rgb,labels,Kn=native_rgb_labels(target['RGB'],target['labels'],target['K'])
    np.savez_compressed(output/'HERO_native.npz',depth_mm=depth,K_index_native=Kn,reference_pose_mm=C,source_poses_mm=Cs,unit='mm',depth_definition='camera axial Z')
    mesh,uv,pix=depth_mesh(depth,labels,C,Kn,rgb)
    mesh.export(output/'Raw_open_mesh.ply')
    np.savez_compressed(output/'RAW_NATIVE_MESH.npz',V=np.asarray(mesh.vertices),F=np.asarray(mesh.faces),uv=uv,native_pixel_id=pix,original_face_id=np.arange(len(mesh.faces)),K=Kn,T=C)
    np.savez_compressed(output/'NATIVE_RGB_LABELS.npz',RGB=rgb,labels=labels)
    rec=dict(inference_executed=True,reused_historical_depth=False,optimizer_steps=0,native_shape=list(depth.shape),depth_interpolation=0,unit='mm',depth_definition='axialZ',native_pixels=len(uv),raw_faces=len(mesh.faces),seconds=time.time()-start,peak_GPU_bytes=torch.cuda.max_memory_allocated())
    save_json(output/'INFERENCE.json',rec)
    return rec
