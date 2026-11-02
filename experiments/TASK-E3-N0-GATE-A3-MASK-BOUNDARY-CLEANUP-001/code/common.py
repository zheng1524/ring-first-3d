"""Exact A2/Gate-A helpers bound to new IO; only original/source inputs readable."""
from pathlib import Path
import ast,os
TASK_ROOT=Path(__file__).resolve().parents[1];REPO_ROOT=TASK_ROOT.parents[1]
R=Path(os.environ.get('RING_A3_OUTPUT',str(TASK_ROOT))).resolve();REPO=REPO_ROOT
assert R==TASK_ROOT or R.is_relative_to(TASK_ROOT/'runtime')
A2=Path('/home/liu/ring_first_3d_e3n0_a2/experiments/TASK-E3-N0-GATE-A2-PROJECTIVE-CLEANUP-001')
_a2_tree=ast.parse((A2/'code/common.py').read_text())
_a2_nodes=[n for n in _a2_tree.body if not(isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in ['TASK_ROOT','REPO_ROOT','R','REPO'] for t in n.targets))]
exec(compile(ast.Module(body=_a2_nodes,type_ignores=[]),str(A2/'code/common.py'),'exec'),globals())
from scipy import ndimage
from scipy.spatial import cKDTree
VERSIONS=['V1','V2','V3']
A2_LINEAGE=load(A2/'DERIVED_INPUT_LINEAGE.json')
for a in load(A2/'LOCAL_RESULTS_INDEX.json')['files']:ALLOWED.add(str(Path(a['path']).resolve()))

@lru_cache(None)
def v1(cid):
    s=native(cid);a=next(r['incremental'] for r in A2_LINEAGE['sources'] if r['source']==cid)
    assert sha(a['path'])==a['sha256'];p=np.load(a['path']);depth,valid=p['depth_mm'],p['valid'];v,u=np.nonzero(valid);uv=np.c_[u,v]
    return dict(s,depth=depth,valid=valid,native_uv=uv,native_id=v*640+u,X=unproject(depth[v,u].astype(float),s['T'],uv,s['Kn']),historical_excluded=p['historical_excluded'],A2_excluded=p['incremental_excluded'])

@lru_cache(None)
def cohort(cid,version):
    if version=='V1':return v1(cid)
    s=v1(cid);p=np.load(R/'local_results/inputs'/version/(cid+'.npz'));depth,valid=p['depth_mm'],p['valid'];v,u=np.nonzero(valid);uv=np.c_[u,v]
    return dict(s,depth=depth,valid=valid,native_uv=uv,native_id=v*640+u,X=unproject(depth[v,u].astype(float),s['T'],uv,s['Kn']))

@lru_cache(None)
def mask_metric(cid):
    s=native(cid);h,w=s['depth'].shape;ha,wa=s['labels'].shape;M=s['labels']==1;spacing=np.array([h/ha,w/wa])
    # Exact EDT pixel-center convention, on original archived labels, anisotropic native units.
    edt=ndimage.distance_transform_edt(np.pad(M,1),sampling=spacing)[1:-1,1:-1]
    yy,xx=np.nonzero(~np.pad(M,1));bg=np.c_[yy-1,xx-1];tree=cKDTree(bg*spacing)
    return dict(mask=M,spacing=spacing,edt=edt,tree=tree,bg=bg)

def mask_query(cid,uv):
    s=native(cid);d=mask_metric(cid);uv=np.asarray(uv,float);q=archive_uv(s,uv);h,w=d['mask'].shape
    inside=np.isfinite(q).all(1)&(q[:,0]>=-.5)&(q[:,0]<w-.5)&(q[:,1]>=-.5)&(q[:,1]<h-.5)
    pix=np.floor(q+.5).astype(int);label=np.full(len(q),-1,int);dist=np.full(len(q),np.nan);di=np.full(len(q),np.nan);bg=np.full((len(q),2),np.nan)
    j=np.flatnonzero(inside);p=pix[j];label[j]=s['labels'][p[:,1],p[:,0]];value,k=d['tree'].query(q[j,::-1]*d['spacing']);dist[j]=value;di[j]=d['edt'][p[:,1],p[:,0]];bg[j]=d['bg'][k][:,::-1]
    return dict(archive_uv=q,archive_pixel=pix,inside=inside,label=label,distance_native_px=dist,nearest_original_raster_EDT_native_px=di,nearest_BG_archive_uv=bg)

def crop_data(cid,version):return np.load(R/'local_results/crops'/version/(cid+'.npz'))

def primary_protocol():return load(R/'config/A3_PREREGISTERED.json')

def raw_distances(cid,ids):
    p=np.load(BASE/'local_results'/(cid+'_native_raw_diagnostic.npz'));m=np.full(352*640,np.nan);m[p['native_id']]=p['distance_to_own_original_raw_faces_mm'];return m[np.asarray(ids,int)]

extract(A2/'code/validate_inputs.py',['comparison'],globals())
