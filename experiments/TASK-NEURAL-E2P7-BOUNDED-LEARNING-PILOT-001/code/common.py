"""E2.7 task-scoped GPU authorization; frozen prior assets remain read-only."""
from pathlib import Path
from functools import lru_cache
import os,sys,ast,json,csv,hashlib,datetime,subprocess,importlib.util,time,gc
R=Path(__file__).resolve().parents[1];REPO=R.parents[1]
E0=Path('/home/liu/ring_first_3d_neural_e0/experiments/TASK-NEURAL-E0-COMPARE-001')
E1=Path('/home/liu/ring_first_3d_neural_e1/experiments/TASK-NEURAL-E1-PIPELINE-RECOVERY-001')
E2=Path('/home/liu/ring_first_3d_neural_e2/experiments/TASK-NEURAL-E2-C2A-C2B-CONTRACT-001')
E2C=Path('/home/liu/ring_first_3d_neural_e2_cpu/experiments/TASK-NEURAL-E2-C2A-C2B-CONTRACT-001')
E25=Path('/home/liu/ring_first_3d_neural_e2p5/experiments/TASK-NEURAL-E2P5-DEPTH-AND-NEURAL-WIRING-001')
E26=Path('/home/liu/ring_first_3d_neural_e2p6/experiments/TASK-NEURAL-E2P6-INITIALIZATION-AND-STABLE-LOSS-001')
OLD=Path('/home/liu/polyp_research/ring_anchor_3d/experiments');VENDOR=OLD/'surface_fusion_v3/vendor'
SDF=E0/'runtime/monosdf_official';SCENE='G01_005';REFS=['G01_005_raw00057','G01_005_raw00459','G01_005_raw00745']
for d in ['code','config','metrics','provenance','figures','checkpoints/A','checkpoints/B','local_results','runtime/tmp','runtime/cache']:(R/d).mkdir(parents=True,exist_ok=True)
os.environ.update(PYTHONDONTWRITEBYTECODE='1',CUDA_VISIBLE_DEVICES='0',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',
    MPLCONFIGDIR=str(R/'runtime/mpl'),TMPDIR=str(R/'runtime/tmp'),XDG_CACHE_HOME=str(R/'runtime/cache'),
    CUDA_CACHE_PATH=str(R/'runtime/cuda_cache'),TORCH_EXTENSIONS_DIR=str(R/'runtime/extensions'),TORCHINDUCTOR_CACHE_DIR=str(R/'runtime/inductor'),
    OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='2',CUBLAS_WORKSPACE_CONFIG=':4096:8')
sys.dont_write_bytecode=True;ACCESSED=set();REUSE=[]
names=['guard','sha','load','clean','save','table','stats','extract','asset','git','protected_state','ring','cad_scene']
t=ast.parse((E1/'code/common.py').read_text());exec(compile(ast.Module(body=[n for n in t.body if isinstance(n,ast.FunctionDef)and n.name in names],type_ignores=[]),str(E1/'code/common.py'),'exec'),globals())
_old_guard=guard
def guard(event,args):
    if event=='import' and str(args[0])=='model.network':return
    _old_guard(event,args)
    if event=='open' and isinstance(args[0],(str,bytes)):
        p=Path(os.fsdecode(args[0])).resolve()
        if p.suffix.lower() in ['.pt','.pth','.ckpt','.safetensors'] and not p.is_relative_to(R/'checkpoints'):
            raise PermissionError('E27_CHECKPOINT_IO_TASK_ONLY')
sys.addaudithook(guard)
import numpy as np,cv2,trimesh
from PIL import Image
sys.path.insert(0,str(REPO));from visualization import real_p0_renderer as vis
sys.path.insert(0,str(E0/'runtime/python'))
import torch
torch.set_num_threads(2);torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
torch.backends.cudnn.benchmark=False;torch.use_deterministic_algorithms(True)
_names=['registry','e2_asset','source','grid','official_method','import_exact','freeze']
_tree=ast.parse((E25/'code/common.py').read_text());exec(compile(ast.Module(body=[n for n in _tree.body if isinstance(n,ast.FunctionDef)and n.name in _names],type_ignores=[]),str(E25/'code/common.py'),'exec'),globals())
def freeze(name,extra=None):
    save('provenance/'+name,dict(UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        code=[asset(p) for p in sorted((R/'code').glob('*.py'))],config=[asset(p) for p in sorted((R/'config').glob('*.json'))],extra=extra,
        GT_opened=False,GPU='AUTHORIZED_BOUNDED_E27',optimizer_step_N=0))
def cfg():return load(R/'config/PREREGISTERED.json')
def domain():return load(E2/'config/SDF_INITIALIZATION_CANDIDATE.json')['scenes'][SCENE]
def parameter_hash(model):
    h=hashlib.sha256()
    for name,t in model.state_dict().items():h.update(name.encode());h.update(t.detach().cpu().numpy().tobytes())
    return h.hexdigest()
def packet(ref,split):
    assert ref in REFS and split in ['small','extra']
    p=E26/f'local_results/packets/{ref}_{split}.npz';frozen=next(x for x in load(E26/'provenance/SOURCE_PROBES_FROZEN.json') if x['source']==ref and x['split']==split)
    assert sha(p)==frozen['packet']['sha256']
    with np.load(p)as z:b={k:z[k] for k in z.files}
    b['source']=str(b['source']);return b
def to_tensor(x,model):
    p=next(model.parameters());return torch.as_tensor(x,dtype=p.dtype,device=p.device)
def gradient(loss,model,retain=True):
    params=list(model.named_parameters());gs=torch.autograd.grad(loss,[p for _,p in params],retain_graph=retain,allow_unused=True)
    vec=torch.cat([torch.zeros_like(p).reshape(-1) if g is None else g.reshape(-1) for (_,p),g in zip(params,gs)]).detach()
    mask=torch.cat([torch.full((p.numel(),),name.startswith('implicit_network'),dtype=torch.bool,device=p.device) for name,p in params]);geom=vec[mask]
    def norm(v):return float(torch.linalg.vector_norm(v.double()))
    meta=dict(full_norm=norm(vec),implicit_norm=norm(geom),finite=bool(torch.isfinite(vec).all()),parameter_N=vec.numel())
    return meta,vec,geom
def check_gpu():
    if not torch.cuda.is_available():raise RuntimeError('GPU_UNAVAILABLE_NO_CPU_TRAINING_FALLBACK')
    total=torch.cuda.get_device_properties(0).total_memory;torch.cuda.set_per_process_memory_fraction(min(5*2**30/total,1.),0)
    return dict(name=torch.cuda.get_device_name(0),total_bytes=total,allocated_bytes=torch.cuda.memory_allocated(),TF32=False,AMP=False)
def memory_guard():
    n=torch.cuda.max_memory_allocated() if torch.cuda.is_initialized() else 0
    if n>5*2**30:raise RuntimeError('GPU_MEMORY_LIMIT')
    return n
