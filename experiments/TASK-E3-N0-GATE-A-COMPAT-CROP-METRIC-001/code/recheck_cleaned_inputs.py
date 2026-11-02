"""Execute the SAME preregistered crop/domain functions on derived copies.
A bound namespace changes only data loader/output root, never parameters.
"""
from crop import *
ROOT=R;V=R/'derived_projective_v1'

def derived_native(cid):
    s=native(cid);d=np.load(ROOT/'local_results/projective_cleanup_v1'/(cid+'.npz'));depth=d['depth_mm'];valid=d['valid'];v,u=np.nonzero(valid);uv=np.c_[u,v];X=unproject(depth[v,u].astype(float),s['T'],uv,s['Kn']);return dict(s,depth=depth,valid=valid,native_uv=uv,native_id=v*640+u,X=X,original_native_N=len(s['native_id']),projective_excluded=d['projective_excluded'])

def bind_run(script):
    ns=dict(globals());ns.update(R=V,native=derived_native,save=lambda p,data:save(V/p,data),table=lambda p,rows:table(V/p,rows));extract(ROOT/'code'/script,['make_domain','main']if script=='metric_domain.py'else ['main'],ns);ns['main']()

def main():
    assert not(V/'METRIC_TRANSFORM.json').exists(),'DO_NOT_OVERWRITE_COMPLETED_DERIVED_EXPERIMENT'
    for d in ['config','local_results/crops','code']:(V/d).mkdir(parents=True,exist_ok=True)
    for name in ['GATE_A_PREREGISTERED.json','BEFORE_FORMAL_CALCULATION.json']:(V/'config'/name).write_bytes((ROOT/'config'/name).read_bytes())
    if not(V/'SOURCE_AND_CROP_MANIFEST.json').exists():bind_run('build_crops.py')
    else:assert load(V/'SOURCE_AND_CROP_MANIFEST.json')['native_valid_total']==106098,'PARTIAL_CROP_INPUT_IDENTITY_CHANGED'
    bind_run('metric_domain.py')
    original=list(csv.DictReader((ROOT/'CROP_GEOMETRY_TESTS.csv').open()));derived=list(csv.DictReader((V/'CROP_GEOMETRY_TESTS.csv').open()));comp=[]
    for old,new in zip(original,derived):
        cid=old['source'];o=native(cid);c=np.load(V/'local_results/crops'/(cid+'.npz'));represented=np.unique(c['source_ids'][c['valid']]);exc=np.load(ROOT/'local_results/projective_cleanup_v1'/(cid+'.npz'))['projective_excluded'];A0=np.load(ROOT/'local_results/crops'/(cid+'.npz'))['A']
        comp.append(dict(source=cid,original_fixed_denominator=len(o['native_id']),projective_excluded_N=int(exc.sum()),derived_legal_N=int(new['original_legal_N']),original_ID_represented_by_crop_N=int(np.isin(o['native_id'],represented).sum()),all_original_ID_retention_after_cleanup_crop=float(np.isin(o['native_id'],represented).mean()),crop_affine_unchanged=bool(np.array_equal(A0,c['A'])),old_scale=float(old['scale']),new_scale=float(new['scale']),old_analytic_max_mm=float(old['analytic_XYZ_max_mm']),new_analytic_max_mm=float(new['analytic_XYZ_max_mm']),old_thin_status=old['thin_status'],new_thin_status=new['thin_status'],source_or_camera_reselected=False))
    table('PROJECTIVE_CLEANUP_BEFORE_AFTER.csv',comp);save('config/DERIVED_EXECUTION_PROVENANCE.json',dict(variant_root=V,executed_functions=REUSE,unchanged_protocol=asset(ROOT/'config/GATE_A_PREREGISTERED.json'),variant_manifest=asset(V/'SOURCE_AND_CROP_MANIFEST.json'),old_metric=asset(ROOT/'METRIC_TRANSFORM.json'),new_metric=asset(V/'METRIC_TRANSFORM.json'),all_original_denominator_retained_in_comparison=True,crop_rule_changed=False,network_forward=0))
    print('DERIVED_RECHECK',load(V/'config/METRIC_STOP.json'),flush=True)
if __name__=='__main__':main()
