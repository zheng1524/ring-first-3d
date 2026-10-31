"""E2.6 scoped CPU context; audited helpers reused, previous worktrees read-only."""
from pathlib import Path
from functools import lru_cache
import os,sys,ast,json,csv,hashlib,datetime,subprocess,importlib.util,gc
R=Path(__file__).resolve().parents[1];REPO=R.parents[1]
E0=Path('/home/liu/ring_first_3d_neural_e0/experiments/TASK-NEURAL-E0-COMPARE-001')
E1=Path('/home/liu/ring_first_3d_neural_e1/experiments/TASK-NEURAL-E1-PIPELINE-RECOVERY-001')
E2=Path('/home/liu/ring_first_3d_neural_e2/experiments/TASK-NEURAL-E2-C2A-C2B-CONTRACT-001')
E2C=Path('/home/liu/ring_first_3d_neural_e2_cpu/experiments/TASK-NEURAL-E2-C2A-C2B-CONTRACT-001')
E25=Path('/home/liu/ring_first_3d_neural_e2p5/experiments/TASK-NEURAL-E2P5-DEPTH-AND-NEURAL-WIRING-001')
GROW=Path('/home/liu/ring_first_3d_boundary_growth/experiments/TASK-BOUNDARY-GUIDED-SURFACE-GROWTH-001')
PART=Path('/home/liu/ring_first_3d_view_partition/experiments/TASK-VIEW-PARTITION-MAST3R-FUSION-001')
INC=Path('/home/liu/ring_first_3d_incremental/experiments/TASK-PHASED-INCREMENTAL-FUSION-MULTIGROUP-001')
OLD=Path('/home/liu/polyp_research/ring_anchor_3d/experiments');VENDOR=OLD/'surface_fusion_v3/vendor'
SDF=E0/'runtime/monosdf_official';MAP=E0/'runtime/map-anything'
os.environ.update(CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',
    MPLCONFIGDIR=str(R/'runtime/mpl'),TMPDIR=str(R/'runtime/tmp'),OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='2')
sys.dont_write_bytecode=True
for d in ['code','config','metrics','provenance','figures','docs','visualizations','local_results','runtime/tmp']:(R/d).mkdir(parents=True,exist_ok=True)
ACCESSED=set();REUSE=[]
t=ast.parse((E1/'code/common.py').read_text());names=['guard','sha','load','clean','save','table','stats','extract','asset','git','protected_state','ring','cad_scene']
exec(compile(ast.Module(body=[x for x in t.body if isinstance(x,ast.FunctionDef)and x.name in names],type_ignores=[]),str(E1/'code/common.py'),'exec'),globals())
_old_guard=guard
def guard(event,args):
    if event=='import' and str(args[0])=='model.network':return  # explicit E2.6 real CPU authorization
    _old_guard(event,args)
    if event=='open' and isinstance(args[0],(str,bytes)) and Path(os.fsdecode(args[0])).suffix.lower() in ['.pt','.pth','.ckpt','.safetensors']:
        raise PermissionError('E26_NO_CHECKPOINT_IO')
sys.addaudithook(guard)
import numpy as np,cv2,trimesh
from PIL import Image
sys.path.insert(0,str(REPO));from visualization import real_p0_renderer as vis
from visualization.same_camera_scene import SameCameraScene
unproject=extract(OLD/'ring_first_v1/scripts/common.py',['unproject'])['unproject']
_names=['registry','selected','e2_asset','source','grid','official_method','import_exact','freeze']
_tree=ast.parse((E25/'code/common.py').read_text())
exec(compile(ast.Module(body=[x for x in _tree.body if isinstance(x,ast.FunctionDef)and x.name in _names],type_ignores=[]),str(E25/'code/common.py'),'exec'),globals())
sys.modules['context']=sys.modules[__name__];sys.modules['continuation_context']=sys.modules[__name__]
opacity=import_exact('opacity',E2C/'code/opacity.py')
e25=import_exact('e25_cpu_reused',E25/'code/official_sdf_cpu_adapter.py')
import torch
torch.set_num_threads(2)
def cfg():return load(R/'config/PREREGISTERED.json')
def domains():return load(E2/'config/SDF_INITIALIZATION_CANDIDATE.json')['scenes']
def robust_norm(v):
    v=v.detach().double();m=float(abs(v).max()) if v.numel() else 0.
    return 0. if m==0 else float(m*torch.linalg.vector_norm(v/m))
def full_gradient(loss,model,retain=True):
    params=list(model.named_parameters());gs=torch.autograd.grad(loss,[p for _,p in params],allow_unused=True,retain_graph=retain)
    arrays=[];groups={k:[] for k in ['implicit','head','trunk','radiance','beta']};used=0
    last='implicit_network.lin'+str(model.implicit_network.num_layers-2)
    for (name,p),g in zip(params,gs):
        if g is not None:used+=1
        v=torch.zeros(p.numel(),dtype=torch.float64) if g is None else g.detach().reshape(-1).double()
        arrays.append(v)
        if name.startswith('implicit_network'):
            groups['implicit'].append(v);groups['head' if name.startswith(last+'.')else'trunk'].append(v)
        elif name.startswith('rendering_network'):groups['radiance'].append(v)
        else:groups['beta'].append(v)
    vec=torch.cat(arrays);meta=dict(full_norm=robust_norm(vec),finite=bool(torch.isfinite(vec).all()),
        parameter_N=vec.numel(),tensor_N=len(params),used_tensor_N=used,max_abs=float(abs(vec).max()))
    for name,vs in groups.items():meta[name+'_norm']=robust_norm(torch.cat(vs)) if vs else 0.
    return meta,vec
def config_model(domain,bias):
    conf=e25.model_config(domain,'B_SOURCE_ROI_PHYSICAL',cfg());conf['implicit_network']['bias']=float(bias);return conf
def build_model(domain,bias,dtype=torch.float64):
    torch.random.default_generator.manual_seed(cfg()['seed']);model,ports=e25.construct_official(config_model(domain,bias))
    if dtype==torch.float32:model=model.float()
    assert all(p.device.type=='cpu' for p in model.parameters())
    return model,ports
