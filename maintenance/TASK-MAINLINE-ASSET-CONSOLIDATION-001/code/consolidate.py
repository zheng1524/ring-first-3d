"""Copy selected code closures, path-only adaptations, and curated evidence."""
import ast,hashlib,json,os,shutil,subprocess,tokenize,io
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];TASK=ROOT/'maintenance/TASK-MAINLINE-ASSET-CONSOLIDATION-001'
CAN=ROOT/'src/ring_first_3d/mainline';LINEAGE=CAN/'lineage';BASE=Path('/home/liu/ring_first_3d_growth_recovery');records=[]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')
def put(source,dest,task,commit=None,adapt=False,raw=None):
    source=Path(source);dest=Path(dest);data=source.read_bytes()if raw is None else raw;original=data
    changes=[]
    if adapt and dest.suffix=='.py':
        text=data.decode();lines=text.splitlines(keepends=True);edits=[]
        offsets=[0]
        for line in lines:offsets.append(offsets[-1]+len(line))
        for t in tokenize.generate_tokens(io.StringIO(text).readline):
            if t.type!=tokenize.STRING:continue
            try:v=ast.literal_eval(t.string)
            except(ValueError,SyntaxError):continue
            if isinstance(v,str)and v.startswith('/home/liu/ring_first_3d'):
                edits.append((offsets[t.start[0]-1]+t.start[1],offsets[t.end[0]-1]+t.end[1],'str(_mainline_path('+repr(v)+'))'));changes.append(v)
        for a,b,s in reversed(edits):text=text[:a]+s+text[b:]
        if edits:
            tree=ast.parse(text);nodes=tree.body;doc=nodes[0]if nodes and isinstance(nodes[0],ast.Expr)and isinstance(nodes[0].value,ast.Constant)and isinstance(nodes[0].value.value,str)else None
            line=doc.end_lineno if doc else 0;parts=text.splitlines(keepends=True);parts.insert(line,'from ring_first_3d.mainline.paths import historical_path as _mainline_path\n');text=''.join(parts)
        data=text.encode();ast.parse(text)
    if dest.exists():
        assert dest.read_bytes()==data, 'Conflicting version: '+str(dest)
    else:dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
    records.append(dict(original_path=str(source),source_task=task,source_commit=commit,original_sha256=hashlib.sha256(original).hexdigest(),new_path=str(dest.relative_to(ROOT)),new_sha256=sha(dest),status='ADAPTED_COPY'if data!=original else'EXACT_COPY',modified=data!=original,reason='Only hardcoded legacy workspace paths replaced by explicit canonical lineage resolver'if changes else'Byte-identical copy',path_adaptations=changes))

selected={
'TASK-E4-G01-G03-GROWTH-RECOVERY-001':('ring_first_3d_growth_recovery','bac3fc89ef95db522b63cf6bb98e6914b9382864'),
'TASK-E4-STRUCTURED-BODY-UPDATE-002':('ring_first_3d_structured_body_002','238c2da1cd842c0eba710a4ec44db5f437bff8e4'),
'TASK-E4-MULTIVIEW-STRUCTURAL-UPDATE-001':('ring_first_3d_structural_update','7c471701f38f1577ba506bc8ed1e38774f99dabe'),
'TASK-E4-2D-CONTOUR-GUIDED-INIT-A-HERO-001':('ring_first_3d_contour_guided_init_a','418c96f87ba06458be5bb082813cad6e20127a19'),
'TASK-E4-MULTIVIDEO-INIT-A-HERO-ALIGN-001':('ring_first_3d_multivideo_init_a','13a73f0422be5e5b0e221df4a41407b3b6d6d52c'),
'TASK-E4-MULTISURFACE-STRESS-AND-REAL-PILOT-001':('ring_first_3d_multisurface_stress','b1f8fb433f37677b93ac52ac5719afd902c1fa11'),
'TASK-E4-G01-MULTISURFACE-BODY-FUSION-001':('ring_first_3d_g01_multisurface','b16a6f813ecf9214958cae3b88d624725a0fa484'),
'TASK-E4-G01-DUALVIDEO-BODY-ANCHORED-REGISTRATION-001-SIM-PROTOCOL-REV1':('ring_first_3d_g01_sim_rev1','0a3fe96bb1d91e5719f8e21bcf232e0967dd233f'),
'TASK-E4-G01-DUALVIDEO-BODY-ANCHORED-REGISTRATION-001':('ring_first_3d_g01_dualvideo','009112d0ceca23e968ef7a97de33ea6989c24b15'),
'TASK-E4-SYNTHETIC-BODY-PIXEL-CORRESPONDENCE-001':('ring_first_3d_synthetic_correspondence','083ad67ab4b6a8432fb631201b8abafe7df2ee13')}
for name,(workspace,commit)in selected.items():
    old=Path('/home/liu')/workspace/'experiments'/name;new=LINEAGE/'experiments'/name
    for p in old.glob('*'):
        if p.is_file()and p.name in ['TASK.yaml','TASK_FREEZE.json','TECHNICAL_REPORT.md','RESULT_CARD.md','FAILURE_REGISTRY.json']:put(p,new/p.name,name,commit)
    for p in (old/'inputs').glob('*.json'):put(p,new/'inputs'/p.name,name,commit)
    for directory in ['code','tests']if name in list(selected)[:3]else['legacy015']if '2D-CONTOUR'in name else[]:
        for p in (old/directory).glob('*.py'):put(p,new/directory/p.name,name,commit,True)
    alias=ROOT/'experiments'/name;alias.parent.mkdir(exist_ok=True)
    if not alias.exists():alias.symlink_to(os.path.relpath(new,alias.parent))

# The 013 input and actual rejected candidate are small immutable scientific assets.
structured=LINEAGE/'experiments/TASK-E4-STRUCTURED-BODY-UPDATE-002'
old=Path('/home/liu/ring_first_3d_structured_body_002/experiments/TASK-E4-STRUCTURED-BODY-UPDATE-002')
for case in ['G01','G03']:
    for n in ['INITIAL.npz','UPDATES.json','STEP_024/BODY.npz','STEP_024/GRAPH.npz','GROWTH_PROPOSAL_024/BODY.npz','GROWTH_PROPOSAL_024/SWEEP.npz']:
        put(old/'runs'/case/'DEFORM_SWEEP'/n,structured/'runs'/case/'DEFORM_SWEEP'/n,old.name,selected[old.name][1])
growth=BASE/'experiments/TASK-E4-G01-G03-GROWTH-RECOVERY-001';ng=LINEAGE/'experiments'/growth.name
for f in ['runs/LOCAL_001/FREEZE.json','runs/LOCAL_001/attempts/0005-G1_G01-c5de4ef6/G01/DEFORM_SWEEP_RECOVERY/trials/0002_1_0_b0/boolean/UNION.npz']:
    put(growth/f,ng/f,growth.name,selected[growth.name][1])
for p in (growth/'review_assets').rglob('*'):
    if p.is_file():put(p,ROOT/'mainline/results'/p.relative_to(growth/'review_assets'),growth.name,selected[growth.name][1])
for p in (growth/'visualization').rglob('*'):
    if p.is_file():put(p,ROOT/'mainline/visualization/stalk_growth'/p.relative_to(growth/'visualization'),growth.name,selected[growth.name][1])
for f in ['TECHNICAL_REPORT.md','RESULT_CARD.md','FAILURE_REGISTRY.json','SOURCE_VERSION_TABLE.json','RUN_MANIFEST.json']:
    put(growth/f,ROOT/'mainline/results'/f,growth.name,selected[growth.name][1])
for p in (growth/'metrics').glob('*.csv'):put(p,ROOT/'mainline/results/metrics'/p.name,growth.name,selected[growth.name][1])

# Populate the existing registry's exact source closure; AST loaders need no old checkout.
lock=json.loads((ROOT/'src/ring_first_3d/source_lock.json').read_text())
for key,r in lock['sources'].items():
    raw=subprocess.check_output(['git','show',r['commit']+':'+r['path']],cwd=BASE)
    assert hashlib.sha256(raw).hexdigest()==r['sha256']
    put(Path(r['path']),CAN/'frozen_registry'/r['path'],key,r['commit'],raw=raw)

# Keep distinct historical observation models / multivideo / reprojection implementations.
historical=['TASK-E4-HERO-BODY-ADAPT-018','TASK-E4-PYTORCH3D-014','TASK-E4-RING-ANCHORED-JOINT-BA-021','TASK-VIEW-OBSERVABILITY-GT-EVAL-001','TASK-E4-RING-FIRST-MAX-COVERAGE-VIEWS-001','TASK-E4-A1-COARSE-BODY-001','TASK-E4-A1-ELLIPSE-VS-FULLMASK-001','TASK-E4-BODY-GUIDED-HERO-DXY-REPAIR-001']
commit='5636aaebd61a3d53b69f528692c4c7095df46508'
for name in historical:
    names=subprocess.check_output(['git','ls-tree','-r','--name-only',commit,'experiments/'+name],cwd=BASE,text=True).splitlines()
    for n in names:
        p=Path(n)
        if(p.suffix=='.py'and'code'in p.parts)or p.name in ['TECHNICAL_REPORT.md','RESULT_CARD.md','FAILURE_REGISTRY.json','FAILURE_LEDGER.md']:
            raw=subprocess.check_output(['git','show',commit+':'+n],cwd=BASE)
            put(p,LINEAGE/p,name,commit,adapt=p.suffix=='.py',raw=raw)

core=Path('/home/liu/ring-first-hero-core');corecommit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=core,text=True).strip()
for p in (core/'src/ring_first_hero').iterdir():
    if p.is_file()and p.suffix in ['.py','.json']:put(p,CAN/'native'/p.name,'TASK-RING-FIRST-HERO-COLLAB-RELEASE-001',corecommit)
for f in ['VERSION_LOCK.json','METHOD_AND_SOURCE_AUDIT.md','LICENSE','provenance/upstream/SOURCE_COMPARISON.json']:
    put(core/f,ROOT/'mainline/references/ring_hero'/Path(f).name,'TASK-RING-FIRST-HERO-COLLAB-RELEASE-001',corecommit)

# Byte-identical compiled/runtime modules are LOCAL_ONLY; no new environment/install.
runtime={
'pytorch3d':Path('/home/liu/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/runtime/pytorch3d/pytorch3d'),
'p3d_packages':Path('/home/liu/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/runtime/packages'),
'extra_packages':Path('/home/liu/ring_first_3d_e4_sdf_evolution/experiments/E4-SDF-EVOLUTION-001/runtime/packages'),
'fcl_packages':Path('/home/liu/ring_first_3d_e4_pmgr_r1/experiments/TASK-E4-PMGR-R1/runtime/packages')}
runtime_records=[]
for name,source in runtime.items():
    dest=ROOT/'.runtime'/('p3d/pytorch3d'if name=='pytorch3d'else name)
    shutil.copytree(source,dest,ignore=shutil.ignore_patterns('__pycache__','*.pyc'),dirs_exist_ok=True)
    for p in dest.rglob('*'):
        if p.is_file():runtime_records.append(dict(original_path=str(source/p.relative_to(dest)),new_path=str(p.relative_to(ROOT)),sha256=sha(p),bytes=p.stat().st_size,LOCAL_ONLY=True))
save(ROOT/'mainline/manifests/RUNTIME_FILES.json',runtime_records)
save(TASK/'COPY_VERIFICATION.json',dict(files=records,exact_copies=sum(not r['modified']for r in records),adapted_copies=sum(r['modified']for r in records),history_modified=False))
save(ROOT/'mainline/manifests/SOURCE_PROVENANCE.json',dict(files=records,source_status='ACTIVE_RESEARCH_MAINLINE',scientific_certification=False))
print('COPIED',len(records),'files; runtime files',len(runtime_records))
