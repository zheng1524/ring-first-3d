"""Validate actual files, locks, Meshes, links and artifact immutability."""
from pathlib import Path
import json,re,hashlib,subprocess,html
from urllib.parse import unquote
import numpy as np,trimesh
from PIL import Image
TD=Path(__file__).resolve().parents[1];ROOT=TD.parents[1];VIS=TD/'visualization'
read=lambda p:json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):Path(p).write_text(json.dumps(x,indent=2,ensure_ascii=False,allow_nan=False)+'\n')

def main():
    counts={}
    for name in ['INPUT_MANIFEST.json','CODE_LOCK.json']:
        rows=read(TD/'inputs'/name)['files']
        for r in rows:assert Path(r['path']).is_file()and sha(r['path'])==r['sha256'],r['path']
        counts[name]=len(rows)
    assert read(TD/'evidence/FINAL_RUNNER_ACCEPTANCE.json')['accepted']
    assert read(TD/'evidence/REGRESSION_RESULT.json')['tests']==186
    for field,value in [('failures',0),('errors',0)]:assert read(TD/'evidence/REGRESSION_RESULT.json')[field]==value
    for r in read(TD/'FAILURE_REGISTRY.json')['failures']:
        for p in r['evidence']:assert (TD/p).exists(),p
    linked=0
    for href in re.findall(r'(?:href|src)="([^"]+)"',(VIS/'index.html').read_text()):
        path=(VIS/unquote(html.unescape(href))).resolve();assert path.is_file(),path;linked+=1
    for document in ['TECHNICAL_REPORT.md','RESULT_CARD.md']:
        for href in re.findall(r'\]\(([^)]+)\)',(TD/document).read_text()):
            if href!='RUN_MANIFEST.json':assert(TD/href).exists(),href
    for p in (VIS/'figures').glob('*.png'):
        with Image.open(p)as im:im.verify()
    counts['PNG']=len(list((VIS/'figures').glob('*.png')))
    faces=0
    for p in (VIS/'meshes').glob('*.glb'):
        s=trimesh.load(p,force='scene',process=False)
        assert len(s.geometry)>0,p
        for name,m in s.geometry.items():
            assert np.isfinite(m.vertices).all()and len(m.faces)>0,(p,name)
            faces+=len(m.faces)
            assert np.max(abs(m.vertices))<1.,(p,name,'GLB must use m')
        if p.name.endswith('_FULL_HERO.glb'):
            case=p.name.split('_')[0];method=p.name[len(case)+1:-len('_FULL_HERO.glb')]
            natives=list((VIS/'meshes').glob(case+'_'+method+'_'+case+'*.npz'))
            assert len(s.geometry)==len(natives)+2,(p,len(s.geometry),len(natives))
            for native in natives:
                mesh=np.load(native);view=native.stem[len(case+'_'+method+'_'):]
                assert np.array_equal(s.geometry[view].faces,mesh['F']),native
                assert np.max(abs(s.geometry[view].vertices*1000-mesh['V']))<1e-4,native
    counts.update(GLB=len(list((VIS/'meshes').glob('*.glb'))),GLB_total_actual_triangles=faces,HTML_verified_paths=linked)
    # Hash equality: reviewed public outputs did not mutate their accepted sources.
    pub=Path(read(TD/'evidence/DELIVERY_SOURCE_BINDING.json')['publication']);checked=0
    for folder in ['figures','meshes','evidence']:
        for p in (pub/folder).rglob('*'):
            if p.is_file():assert sha(p)==sha(VIS/p.relative_to(pub));checked+=1
    counts['original_publication_hashes_unchanged']=checked
    # Guard against accidental edits anywhere in pre-existing science or DXY.
    changed=subprocess.check_output(['git','diff','--name-only','418c96f87ba06458be5bb082813cad6e20127a19'],cwd=ROOT,text=True).splitlines()
    allowed_existing={'src/ring_first_3d/policy/contracts.py','src/ring_first_3d/policy/runner.py','src/ring_first_3d/policy/artifacts.py','tools/research/_policy_worker.py','tools/research/policy.py'}
    new_existing={str(p.relative_to(ROOT))for p in TD.rglob('*')if p.is_file()}
    allowed_new={'src/ring_first_3d/policy/structural_contracts.py','src/ring_first_3d/policy/structural_artifacts.py','tests/test_structural_update.py'}
    assert set(changed)<=allowed_existing|new_existing|allowed_new,set(changed)-allowed_existing-new_existing-allowed_new
    counts['preexisting_scientific_algorithms_modified']=0
    save(TD/'evidence/DELIVERY_VERIFICATION.json',dict(status='PASS',counts=counts,visualization_absolute=str(VIS),index_absolute=str(VIS/'index.html'),source_predictions_changed=False,scientific_success_claim=False))
    # Explicit selected publication: full final Meshes, all PNGs, small records,
    # and representative paired pixel/gradient evidence. Full local arrays stay.
    selected=set(subprocess.check_output(['git','ls-files',str(TD.relative_to(ROOT))],cwd=ROOT,text=True).splitlines())
    for p in TD.iterdir():
        if p.is_file()and(p.suffix in {'.md','.csv','.json','.yaml'}or p.name=='.gitignore'):selected.add(str(p.relative_to(ROOT)))
    for folder in ['evidence','review_tools']:
        for p in (TD/folder).rglob('*'):
            if p.is_file()and'__pycache__'not in p.parts:selected.add(str(p.relative_to(ROOT)))
    for p in VIS.rglob('*'):
        if not p.is_file():continue
        rel=p.relative_to(VIS)
        if rel.parts[0]in {'figures','meshes'}or len(rel.parts)==1 or p.suffix=='.json' or p.name in {'INITIAL.npz','FINAL.npz','BODY_BEFORE.npz','BODY_AFTER.npz'}or p.name.startswith('GROWTH_')or p.name.endswith('_CORRESPONDENCES.npz'):
            selected.add(str(p.relative_to(ROOT)))
    # One accepted representative source from each video at every saved step,
    # plus paired gradient. No additional source/arm/condition is selected by GT.
    for folder in [VIS/'evidence/DEFORM_ONLY',VIS/'evidence/DEFORM_GROW']+list((VIS/'evidence/REAL').glob('*/*')):
        for step in ['STEP_000','STEP_012','STEP_024','STEP_035','FINAL_CORRESPONDENCES']:
            for video in ['004','005']:
                choices=sorted(p for p in(folder/step).glob('G*.npz')if not p.name.endswith('_GRADIENT.npz')and(video in p.stem))
                if choices:
                    p=choices[0];selected.add(str(p.relative_to(ROOT)));g=p.with_name(p.stem+'_GRADIENT.npz')
                    if g.exists():selected.add(str(g.relative_to(ROOT)))
    selected.add(str((TD/'RUN_MANIFEST.json').relative_to(ROOT)))
    selected.add(str((TD/'GIT_PUBLICATION_LIST.json').relative_to(ROOT)))
    missing=[p for p in selected if not(ROOT/p).exists()and not p.endswith(('RUN_MANIFEST.json','GIT_PUBLICATION_LIST.json'))];assert not missing,missing
    save(TD/'GIT_PUBLICATION_LIST.json',dict(policy='Selected PNGs, all final complete Meshes, representative intermediate evidence; no full historical assets/videos/dependencies or raw runs',files=sorted(selected),full_local_visualization_bytes=sum(p.stat().st_size for p in VIS.rglob('*')if p.is_file())))
    files={}
    for p in sorted(TD.rglob('*')):
        if not p.is_file()or'runs'in p.relative_to(TD).parts or'__pycache__'in p.parts or p.name=='RUN_MANIFEST.json':continue
        files[p.relative_to(TD).as_posix()]=dict(sha256=sha(p),bytes=p.stat().st_size)
    save(TD/'RUN_MANIFEST.json',dict(task_id=TD.name,status='ENGINEERING_COMPLETE_SCIENTIFIC_NEGATIVES_RETAINED',scientific_acceptance='AWAITING_HUMAN_REVIEW',scientific_source_commit='6415993f4c6aa2370e80841d1803ed701b257bee',original_C0_prediction_commit='d78cacd86b095ade5c4753537e216f900a018bcd',C0_reexecuted=False,runner_manifest=str(TD/'evidence/RUNNER_RUN_MANIFEST.json'),runner_acceptance='evidence/FINAL_RUNNER_ACCEPTANCE.json',verified_visualization=str(VIS),verified_index=str(VIS/'index.html'),git_publication='GIT_PUBLICATION_LIST.json',self_hash_excluded=True,files=files))
    for document in ['TECHNICAL_REPORT.md','RESULT_CARD.md']:
        for href in re.findall(r'\]\(([^)]+)\)',(TD/document).read_text()):assert(TD/href).exists(),href
    Path('/tmp/structural-explicit-add.txt').write_text('\n'.join(sorted(selected))+'\n')
    print(json.dumps(dict(status='PASS',counts=counts,local_files=len(files),selected_git_files=len(selected),selected_existing_bytes=sum((ROOT/p).stat().st_size for p in selected)),indent=2))

if __name__=='__main__':main()
