"""Publish review copies only after Runner acceptance; never optimize/select."""
import collections,json,shutil,sys,hashlib
from pathlib import Path
from html.parser import HTMLParser
import numpy as np
import trimesh

TD=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(TD/'code'))
from io_utils import read,sha,body,dump,source_folder,load_inputs
from ring_gate import CurrentRingGate
from ring_collision_gate import signed
from ring_first_3d.multisurface.geometry import scene
from geometry_gate import namespace
from lengths import measure

def copy(src,dst):
    dst.parent.mkdir(parents=True,exist_ok=True)
    if dst.exists():
        assert sha(src)==sha(dst), 'Never overwrite a different publication'
    else:shutil.copyfile(src,dst)

def publish():
    run=TD/'runs/LOCAL_002';manifest=read(run/'RUN_MANIFEST.json')
    assert manifest['status']=='ACCEPTED_ENGINEERING',manifest['status']
    attempts={}
    for r in manifest['attempts']:
        p=run/r['path'];a=read(p)
        assert a['status']=='PASS' and sha(p)==r['sha256']
        attempts[a['stage']]=p.parent
    ev=read(attempts['G2_evaluate']/'EVALUATION.json')
    assert ev['GT_after_all_predictions'] and not ev['GT_selects_algorithm']
    for f in ['TECHNICAL_REPORT.md','RESULT_CARD.md','RUN_MANIFEST.json']:
        copy(run/f,TD/f)
    for p in (run/'visualization').rglob('*'):
        if p.is_file():copy(p,TD/'visualization'/p.relative_to(run/'visualization'))
    for p in (attempts['G2_evaluate']/'metrics').glob('*.csv'):copy(p,TD/'metrics'/p.name)
    for f in ['EVALUATION.json','GT_FIRST_ACCESS.json','FAILURE_REGISTRY.json']:
        copy(attempts['G2_evaluate']/f,TD/f)
    copy(run/'FREEZE.json',TD/'evidence/FINAL_RUN_FREEZE.json')
    copy(attempts['recovery_regression']/'regression_log.txt',TD/'evidence/FINAL_REGRESSION_LOG.txt')
    audit=[]
    for case in ['G01','G03']:
        a=attempts['G1_'+case];pred=read(a/'PREDICTIONS_FROZEN.json');r=pred['records'][0]
        out=a/case/'DEFORM_SWEEP_RECOVERY';u=read(out/'UPDATES.json');g=u['chosen'];geometry=body(a/r['mesh_relative']);sw=body(out/'FINAL_SWEEP_PARAMETERS.npz')
        before=body(source_folder(case)/'STEP_024/BODY.npz');_,_,ring,_,_,_=load_inputs(case,'FIT')
        assert sha(a/r['mesh_relative'])==r['mesh_sha256']
        recomputed=measure(sw['control'],before)
        for key in ['total_centerline_length_mm','embedded_length_mm','exposed_stalk_length_mm']:
            assert abs(recomputed[key]-g['length'][key])<1e-9
        assert abs(recomputed['total_centerline_length_mm']-recomputed['embedded_length_mm']-recomputed['exposed_stalk_length_mm'])<1e-10
        # Inspect full proximal ring, separately from centerline-inside evidence.
        rootphi=signed(scene(before['V'],before['F_solid']),sw['V'][:16])
        mesh=trimesh.Trimesh(geometry['V'],geometry['F_solid'],process=False)
        intersections=namespace()['self_intersections'](geometry['V'],geometry['F_solid'])['intersections']
        collision=CurrentRingGate(before,ring);ok,rg,_=collision.check(geometry)
        body_checks=[]
        for p in out.glob('trials/*/boolean/BODY_OPERAND.npz'):
            b=body(p);body_checks.append(np.array_equal(b['V'],before['V']) and np.array_equal(b['F'],before['F_solid']))
        assert body_checks and all(body_checks)
        if r['status']=='NUMERIC':
            assert not g['reasons'] and g['accepted_growth'] and mesh.is_watertight and mesh.is_winding_consistent
            assert intersections==0 and ok
        record=dict(case=case,status=r['status'],reported_stalk_length_mm=recomputed['exposed_stalk_length_mm']if r['status']=='NUMERIC'else None,
            diagnostic_lengths=recomputed,chosen_trial=g['folder'],chosen_stage=g['stage'],trials=len(u['trials']),
            reasons=dict(collections.Counter(s for z in u['trials']for s in z['reasons'])),
            selected_failure_reasons=g['reasons'],external_union_watertight=bool(mesh.is_watertight),winding_consistent=bool(mesh.is_winding_consistent),
            actual_final_self_intersections=int(intersections),Ring_nonworsening=ok,Ring_delta=rg['delta'],
            original_body_operand_bitwise_equal_trials=len(body_checks),proximal_section_SDF_min_mm=float(rootphi.min()),proximal_section_SDF_max_mm=float(rootphi.max()),
            proximal_section_all_internal=bool(rootphi.max()<0),prediction_sha256=r['mesh_sha256'],execution_origin=pred.get('execution_origin',dict(mode='COMPUTED_G01_ENGINEERING_REPLAY')))
        record['root_review_status']='PARTIAL_PROXIMAL_SECTION_EXPOSURE'if rootphi.max()>1e-5 else'PROXIMAL_SECTION_INTERNAL'
        audit.append(record)
        dest=TD/'review_assets'/case;dest.mkdir(parents=True,exist_ok=True)
        for name in ['UPDATES.json','FINAL_SWEEP_PARAMETERS.npz','LOCAL_CONFIGURATION.json','RING_INITIAL.json']:
            copy(out/name,dest/name)
        copy(a/'PREDICTIONS_FROZEN.json',dest/'PREDICTIONS_FROZEN.json')
        copy(a/case/'EXACT_RECOVERY.json',dest/'EXACT_RECOVERY.json')
        copy(a/r['mesh_relative'],dest/('FINAL.npz'if r['status']=='NUMERIC'else'FAILED_ATTEMPT.npz'))
        copy(out/g['folder']/'GATES.json',dest/'CHOSEN_GATES.json')
        for name,b in [('INITIAL',body(source_folder(case)/'INITIAL.npz')),('ITERATION_024',before),('OLD_REJECTED',body(source_folder(case)/'GROWTH_PROPOSAL_024/BODY.npz')),('RECOVERY'if r['status']=='NUMERIC'else'FAILED_ATTEMPT_DIAGNOSTIC',geometry)]:
            ply=dest/(name+'.ply')
            if not ply.exists():trimesh.Trimesh(b['V'],b['F_solid'],process=False).export(ply)
        for p in (attempts['G2_evaluate']/case).glob('*.npz'):copy(p,dest/'evaluation'/p.name)
        for p in (attempts['G2_evaluate']/case).glob('*RIGID_TRIALS.json'):copy(p,dest/'evaluation'/p.name)
        case_dir=TD/'runs'/case;case_dir.mkdir(exist_ok=True)
        link=case_dir/'DEFORM_SWEEP_RECOVERY'
        if not link.exists():link.symlink_to(out)
    dump(TD/'evidence/POST_RUN_GEOMETRY_AUDIT.json',dict(records=audit,GT_used_to_select=False,Body_retrained=False,additional_optimization=False))
    files=read(TD/'inputs/INPUT_MANIFEST.json')['files']
    assert all(sha(r['path'])==r['sha256']for r in files)
    class Links(HTMLParser):
        def __init__(self):super().__init__();self.links=[]
        def handle_starttag(self,tag,attrs):
            self.links +=[v for k,v in attrs if k in ['src','href']]
    index=TD/'visualization/index.html';parser=Links();parser.feed(index.read_text())
    for s in parser.links:
        if not s.startswith(('https:','http:','#','data:')):assert (index.parent/s).is_file(),s
    pngs=list((TD/'visualization/figures').glob('*.png'))
    assert len(pngs)>=48
    assert all(p.read_bytes()[:8]==b'\x89PNG\r\n\x1a\n'for p in pngs)
    dump(TD/'evidence/PUBLICATION_VERIFICATION.json',dict(visualization_directory=str(index.parent.resolve()),index=str(index.resolve()),figures=len(pngs),all_local_html_links_exist=True,all_png_signatures_valid=True,verified_source_assets=len(files),input_hashes_unchanged=True,canonical_run=str(run),canonical_freeze=manifest['freeze_sha256'],target_groups=2,accepted_growth=sum(r['status']=='NUMERIC'for r in audit)))
    print(json.dumps(dict(audit=audit,visualization=str(index),figures=len(pngs)),indent=2))

if __name__=='__main__':publish()
