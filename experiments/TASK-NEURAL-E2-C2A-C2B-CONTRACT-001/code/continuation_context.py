"""CPU continuation of E2; previous deliveries and source assets stay read-only."""
from context import *

BASE=Path('/home/liu/ring_first_3d_neural_e2/experiments/TASK-NEURAL-E2-C2A-C2B-CONTRACT-001')
CROOT=R/'continuation_cpu'
for d in ['config','metrics','provenance','figures','visualizations']:(CROOT/d).mkdir(parents=True,exist_ok=True)


def csave(name,value):save('continuation_cpu/'+name,value)
def ctable(name,value):table('continuation_cpu/'+name,value)


def baseline_asset(relative):
    """Verify only a requested existing artifact, never rerun previous audits."""
    manifest=load(BASE/'provenance/DELIVERY_MANIFEST.json')
    catalog={x['path']:x for x in manifest['files']+manifest['LOCAL_ONLY']}
    record=catalog[relative];p=BASE/relative
    assert sha(p)==record['sha256'],'frozen E2 input changed: '+relative
    return p


def source_packet(ref):
    b=np.load(baseline_asset('local_results/'+ref+'_batch.npz'))
    z=np.load(baseline_asset('local_results/rays/'+ref+'.npz'))
    pix=b['source_pixel'];uv=np.c_[pix%640,pix//640]
    rays=vis.camera_rays(uv,z['K'],z['c2w_mm']);factor=np.linalg.norm(rays[:,3:],axis=1)
    return dict(source=ref,origin=rays[:,:3],direction=rays[:,3:]/factor[:,None],
        cosine=1/factor,start=z['ROI_start_t_mm'][pix],end=z['ROI_end_t_mm'][pix],valid=z['ROI_valid'][pix],
        source_pixel=pix,sampling_class=b['sampling_class'],mask_weight=b['mask_weight'],mask_target=b['mask_target'],
        depth_weight=b['depth_weight'],target_Z=b['target_axial_Z_mm'],RGB=b['source_RGB'],source_K=z['K'],source_c2w_mm=z['c2w_mm'])


def official_method(path,cls,name):
    tree=ast.parse(Path(path).read_text());c=next(x for x in tree.body if isinstance(x,ast.ClassDef)and x.name==cls)
    f=next(x for x in c.body if isinstance(x,ast.FunctionDef)and x.name==name)
    return f,dict(path=str(path),class_name=cls,method=name,line=f.lineno,file_SHA256=sha(path),
        AST_SHA256=hashlib.sha256(ast.dump(f,include_attributes=False).encode()).hexdigest(),args=[a.arg for a in f.args.args])


def freeze_continuation():
    csave('provenance/AUTHORIZATION_AND_FREEZE.json',dict(task=R.name,phase='E2 CPU continuation',
        approval='user explicitly requested continuing prior task according to provided RA guidance',
        previous_delivery_commit='5d4bcbbee444d8db9a479ed256417fb7cfd9a83b',
        previous_audit_rerun=False,GPU='NOT_GRANTED',official_neural_model_forward_N=0,weight_update_N=0,
        allowed='thin adapter, analytic CPU gradient contracts, source conflict audit, official input utilities',
        source_review=asset(BASE/'inputs/RA_PHASE_E_ADAPTIVE_DESIGN_REVIEW.md'),
        code=[asset(p) for p in sorted((R/'code').glob('*continuation*.py'))]+[asset(R/'code/finite_joint_adapter.py')],
        config=[asset(p) for p in sorted((CROOT/'config').glob('*.json'))],
        source_protection=protected_state(),
        worktree_setup_incident='git worktree registered but inherited sparse info directory absent; created info only in new worktree and completed sparse checkout; no old checkout/reset'))
