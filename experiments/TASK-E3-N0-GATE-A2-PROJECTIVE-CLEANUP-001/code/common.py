"""Bind the exact Gate A IO/geometry helpers to A2; history is read-only."""
from pathlib import Path
import os, ast
TASK_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = TASK_ROOT.parents[1]
BASE = Path('/home/liu/ring_first_3d_e3n0/experiments/TASK-E3-N0-GATE-A-COMPAT-CROP-METRIC-001')
R = Path(os.environ.get('RING_A2_OUTPUT', str(TASK_ROOT))).resolve()
assert R == TASK_ROOT or R.is_relative_to(TASK_ROOT / 'runtime'), 'TASK_LOCAL_REPLAY_ONLY'
REPO = REPO_ROOT
_tree = ast.parse((BASE / 'code/common.py').read_text())
_nodes = [n for n in _tree.body if not (isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id in ['R','REPO'] for t in n.targets))]
_hook=next(i for i,n in enumerate(_nodes) if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and ast.unparse(n.value.func)=='sys.addaudithook')
exec(compile(ast.Module(body=_nodes[:_hook], type_ignores=[]), str(BASE / 'code/common.py'), 'exec'), globals())
_inherited_guard=guard
def guard(event,args):
    # This literal historical Markdown is an isolation report, not a GT asset.
    if event=='open' and isinstance(args[0],(str,bytes)) and Path(os.fsdecode(args[0])).resolve()==BASE/'GT_ISOLATION_AUDIT.md':
        mode=args[1] if len(args)>1 and isinstance(args[1],str) else ''
        flags=args[2] if len(args)>2 and isinstance(args[2],int) else 0
        if not (any(c in mode for c in 'wax+') or flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC)):
            ACCESSED.add(str(BASE/'GT_ISOLATION_AUDIT.md')); return
    return _inherited_guard(event,args)
sys.addaudithook(guard)
exec(compile(ast.Module(body=_nodes[_hook+1:], type_ignores=[]), str(BASE / 'code/common.py'), 'exec'), globals())

# Only these previously verified derived/baseline NPZ files are additionally readable.
LINEAGE = load(BASE / 'DERIVED_INPUT_LINEAGE.json')
for row in LINEAGE['sources']:
    for key in ['derived_depth_and_valid','crop']:
        ALLOWED.add(str(Path(row[key]['path']).resolve()))
    for path in [BASE/'local_results'/(row['source']+'_native_raw_diagnostic.npz'),
                 BASE/'derived_projective_v1/local_results/crops'/(row['source']+'_identities.npz')]:
        ALLOWED.add(str(path.resolve()))

def no_neural(event, args):
    if event == 'import' and str(args[0]).startswith(('torch','tensorflow','mast3r','transformers','training','graphics')):
        raise PermissionError('A2_NO_NEURAL_OR_TRAINING_IMPORT')
    if event == 'open' and isinstance(args[0], (str,bytes)) and Path(os.fsdecode(args[0])).suffix.lower() in ['.pt','.pth','.ckpt','.safetensors']:
        raise PermissionError('A2_NO_MODEL_WEIGHTS')
sys.addaudithook(no_neural)

def config():
    return load(BASE/'config/GATE_A_PREREGISTERED.json')

extract(BASE/'code/crop.py', ['make_crop','ridge_proxy'], globals())
extract(BASE/'code/metric_domain.py', ['make_domain'], globals())
extract(BASE/'code/human_review_figures.py', ['wire_box'], globals())
RAW_NATIVE = native
native = lru_cache(None)(RAW_NATIVE)

@lru_cache(None)
def baseline(cid):
    s = native(cid)
    row = next(r for r in LINEAGE['sources'] if r['source'] == cid)
    p = np.load(row['derived_depth_and_valid']['path'])
    assert sha(row['derived_depth_and_valid']['path']) == row['derived_depth_and_valid']['sha256']
    depth, valid = p['depth_mm'], p['valid']
    v,u = np.nonzero(valid); uv = np.c_[u,v]
    X = unproject(depth[v,u].astype(float), s['T'], uv, s['Kn'])
    return dict(s, depth=depth, valid=valid, native_uv=uv, native_id=v*640+u, X=X,
                historical_excluded=p['projective_excluded'])

def archive_uv(s, uv):
    return affine_uv(np.asarray(uv), s['K'] @ np.linalg.inv(s['Kn']))

def read_csv(path):
    return list(csv.DictReader(Path(path).open()))

def neighbours(depth, valid):
    """Four connected native neighbours; never wrap rows or cross invalid pixels."""
    jump = np.zeros(depth.shape, float)
    for dy,dx in [(1,0),(-1,0),(0,1),(0,-1)]:
        n = np.roll(depth,(dy,dx),(0,1)); ok = valid & np.roll(valid,(dy,dx),(0,1))
        if dy == 1: ok[0,:] = False
        if dy == -1: ok[-1,:] = False
        if dx == 1: ok[:,0] = False
        if dx == -1: ok[:,-1] = False
        jump = np.maximum(jump, np.where(ok,abs(depth-n),0))
    return jump
