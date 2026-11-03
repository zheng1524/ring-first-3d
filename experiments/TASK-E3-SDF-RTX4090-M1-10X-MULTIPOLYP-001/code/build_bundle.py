"""Portable, SHA-verified selected assets only; no videos/HERO weights/GT/fusion output."""
from pathlib import Path
import ast,json,hashlib,shutil,os
R=Path(__file__).resolve().parents[1]
OLD=Path('/home/liu/ring_first_3d_e3_sdf_multi/experiments/TASK-E3-SDF-LOCAL-MULTIPOLYP-EXPLORATORY-001')
N0=Path('/home/liu/ring_first_3d_e3n0_eight/experiments/TASK-E3-N0-NEURALFUSION-EIGHT-VIEW-001')
E1=Path('/home/liu/ring_first_3d_neural_e1/experiments/TASK-NEURAL-E1-PIPELINE-RECOVERY-001')
B=R/'bundle'


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(rel,obj):
    p=B/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
def copy(source,target):
    target=B/target;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
    assert sha(source)==sha(target)
    return target
def functions(path,names):
    tree=ast.parse(Path(path).read_text());nodes=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))and n.name in names]
    assert {n.name for n in nodes}==set(names)
    return ast.unparse(ast.Module(body=nodes,type_ignores=[]))+'\n'


def main():
    assert not (B/'data/REFERENCES.json').exists(),'BUNDLE_ALREADY_BUILT'
    orders=json.loads((OLD/'config/SOURCE_SELECTION.json').read_text())['orders'];ids=sum(orders.values(),[])
    references=json.loads((E1/'provenance/INPUT_ELIGIBILITY.json').read_text())['references']
    gate=json.loads((OLD/'config/CAMERA_GATE_RESULTS.json').read_text());by={r['source']:r for r in gate['sources']}
    manifest=[];cc={}
    def asset(p):
        p=Path(p);s=sha(p);rel='data/assets/'+s+p.suffix.lower()
        if not(B/rel).exists():copy(p,rel)
        manifest.append(dict(original=str(p),relative_path=rel,sha256=s,bytes=p.stat().st_size))
        return rel
    for raw in references:
        if raw['id']not in ids:continue
        c=json.loads(json.dumps(raw))
        for k in ['RGB','Mask','pack','source_points','mesh','camera_file']:
            assert sha(c[k])==c['files'][k]['sha256'];c[k]=asset(c[k])
        c['E1_actual_native']['path']=asset(c['E1_actual_native']['path'])
        c['Ring_CAD']['path']=asset(c['Ring_CAD']['path']);c['frozen_block']=by[c['id']]['block']
        cc[c['id']]=c
    write('data/REFERENCES.json',cc);write('data/ASSET_MANIFEST.json',manifest)
    for name in ['CAMERA_GATE_RULES.json','CAMERA_GATE_RESULTS.json','SOURCE_SELECTION.json','EXPERIMENT_FROZEN.json']:
        copy(OLD/'config'/name,'config/'+name)
    for folder in ['native','crops']:
        for cid in ids:copy(OLD/'frozen_inputs'/folder/(cid+'.npz'),'frozen_inputs/'+folder+'/'+cid+'.npz')
    for scene in orders:
        for p in (OLD/'groups'/scene/'frozen_inputs').glob('*.npz'):copy(p,'groups/'+scene+'/frozen_inputs/'+p.name)
        for name in ['PREREGISTERED.json','FORMAL_STAGE_FROZEN.json']:
            copy(OLD/'groups'/scene/'config'/name,'groups/'+scene+'/config/'+name)
        copy(OLD/'groups'/scene/'provenance/BEFORE_FORMAL_TRAINING.json','lineage/'+scene+'_BEFORE_FORMAL_TRAINING.json')
    official=OLD/'groups/G01_004/runtime/official_exact'
    for p in official.rglob('*'):
        if p.is_file():copy(p,'vendor/official_exact/'+str(p.relative_to(official)))
    defs=functions(N0/'code/common.py',['sha','load','clean','save','table','rows','asset','stats','source','native','original','ringmesh','mesh_scene','ringscene','cast','distance','affine_uv'])
    defs+=functions(Path('/home/liu/ring_first_3d_e3_sdf_multi/visualization/real_p0_renderer.py'),['scaled_intrinsics','project_camera','camera_rays'])
    defs+=functions(Path('/home/liu/polyp_research/ring_anchor_3d/experiments/ring_first_v1/scripts/common.py'),['unproject'])
    (B/'code').mkdir(exist_ok=True);(B/'code/historical_helpers.py').write_text(defs)
    # Computational modules copied exactly; portability entrypoints are separate and audited.
    for name in ['official_adapter.py','geometry_monitor.py','train_full.py']:
        copy(OLD/'code'/name,'code/'+name)
    copy(OLD/'code/deliver.py','code/predecessor_deliver.py')
    for name in ['METHODS_AND_VERSION.md','FAILURE_LEDGER.md']:
        copy(OLD/name,'lineage/'+name)
    for p in Path('/home/liu/ring_first_3d_e3_sdf_multi/docs').glob('KEY_TECHNICAL_VERSION*.md'):
        copy(p,'lineage/'+p.name)
    write('config/MIGRATION_PLAN.json',dict(baseline_N=2000,primary_target_each=20000,
        exact_comparison_steps=[2000,4000,10000,20000],orders=orders,
        original_official_commit='12513009cd20a08b35ddc2c55a7e42da2c7baf43',
        local_code_commit='cfc5f2094e40f80f069da598b2e81aa9719acb32',
        allowed_wall_hours=6.5,additional_steps='choose after retained4090 pilot; same loss/schedule, no quality stopping',
        no_GT=True,only_original_HERO_and_own_M1=True))
    write('provenance/BUNDLE_INDEX.json',dict(data_files=len(manifest),unique_asset_bytes=sum(p.stat().st_size for p in (B/'data/assets').iterdir()),
        scientific_source_configuration_unchanged=True,hostname_or_credentials_not_embedded=True))
    print('PORTABLE_BUNDLE_READY',len(manifest),'asset references',sum(p.stat().st_size for p in (B/'data/assets').iterdir()),flush=True)


if __name__=='__main__':main()
