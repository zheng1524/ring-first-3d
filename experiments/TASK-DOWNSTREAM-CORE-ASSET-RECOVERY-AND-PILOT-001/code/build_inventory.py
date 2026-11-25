"""Build reviewable source retention table from the audited IDs and exact files."""
from pathlib import Path
import csv,json,hashlib,ast
from pilot import TASK,REPO,sha
matrix=list(csv.DictReader((REPO/'docs/audits/TASK-HERO-DOWNSTREAM-AND-STORAGE-AUDIT-001/MODULE_VERSION_MATRIX.csv').open()))
ids=['SB01','SB02','SB03','SB07','T24','T30','IA01','GR03']
rows=[]
for ident in ids:
 r=next(x for x in matrix if x['module_id']==ident)
 p=Path(r['source_path']);rel=p.relative_to('/home/liu/ring_first_3d_workspace');q=REPO/rel
 rows.append(dict(asset_id=ident,source_commit=r['source_commit'],source_path=r['source_path'],source_sha256=r['source_sha256'],retained_path=str(rel),current_sha256=sha(q),entrypoint=r['symbol'],required_inputs=r['input_contract'],dependencies=r['dependencies'],historical_evidence=r['evidence'],historical_status=r['research_evidence'],recovery_status={'SB01':'NEW_PILOT_EXECUTED','SB02':'NEW_PILOT_AND_HISTORY_REPLAY','SB03':'NEW_PILOT_AND_HISTORY_REPLAY','SB07':'NEW_PILOT_3_OUTER_9_ADAM; thin budget/save adaptation','T24':'018_DEPTH_REGRESSION_EXECUTED','T30':'018_NATIVE_GRADIENT_REGRESSION_EXECUTED','IA01':'SOURCE_REVIEW_ONLY; not a raw initializer','GR03':'SOURCE_AND_G01_POSITIVE_G03_NEGATIVE_PARAMETERS_PROTECTED; not regrown'}[ident],new_data_status='Requires input identity and geometry contracts; not certified on new cameras',retain_dependencies=r['evidence']))
for i,r in enumerate(json.loads((TASK/'evidence/INITIALIZATION_SOURCE_PROTECTION.json').read_text())):
 rows.append(dict(asset_id='INIT-%02d'%i,source_commit=r['source_commit'],source_path=r['source_path'],source_sha256=r['sha256'],retained_path=r['retained'],current_sha256=sha(REPO/r['retained']),entrypoint='; '.join(n.name for n in ast.parse((REPO/r['retained']).read_text()).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))) if r['retained'].endswith('.py') else 'historical inheritance evidence table',required_inputs='Original per-stage input/config/depth/basis; chain gap explicitly documented',dependencies='numpy scipy torch trimesh PyTorch3D; stage-specific historical imports',historical_evidence='INITIALIZATION_EXPECTED_ASSETS.json; original audit commit',historical_status='ANCESTRY_NOT_NEW_REPRODUCTION',recovery_status='SOURCE_PROTECTED; INPUT_CHAIN_INCOMPLETE',new_data_status='NOT_READY',retain_dependencies='Original missing inputs listed in INITIALIZATION_EXPECTED_ASSETS.json'))
for name,p,entry in [('015','src/ring_first_3d/mainline/frozen_registry/experiments/TASK-E4-MULTIVIEW-INIT-STALK-015/code/prepare.py','main'),('015-TRAIN','src/ring_first_3d/mainline/lineage/experiments/TASK-E4-MULTIVIDEO-INIT-A-HERO-ALIGN-001/legacy015/train_mesh.py','main'),('SE3','src/ring_first_3d/sim/geometry.py','rigid_fit; transform; se3')]:
 rows.append(dict(asset_id=name,source_commit='000f5f2998ad2a29ca454e8380b587b26ba9f21c (retained source baseline)',source_path=p,source_sha256=sha(REPO/p),retained_path=p,current_sha256=sha(REPO/p),entrypoint=entry,required_inputs='015 frozen inputs / paired 3D landmarks for SE3',dependencies='existing registered modules',historical_evidence='original source and audit matrix',historical_status='candidate; no automatic promotion',recovery_status='CONTROL_EXECUTED' if name=='SE3' else 'SOURCE_REVIEWED',new_data_status='Explicit identities and coordinates required',retain_dependencies='fixtures + existing lineage'))
with (TASK/'CORE_ASSETS.csv').open('w')as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
protected=[]
for name in ['PROTECTED_INPUTS.json','SNAPSHOT_PROTECTION.json','HISTORY_PROTECTION.json','INITIALIZATION_SOURCE_PROTECTION.json']:
 for r in json.loads((TASK/'evidence'/name).read_text()):
  p=REPO/r['retained'];assert sha(p)==r['sha256'];protected.append(dict(source=r.get('source',r.get('source_path')),retained=str(p),sha256=r['sha256'],bytes=p.stat().st_size,disposition='KEEP_VERSIONED_TASK_FIXTURE_OR_SOURCE'))
# Original assets remain retain dependencies, even where a task copy is now safe.
for r in rows:
 p=REPO/r['retained_path'];protected.append(dict(source=r['source_path'],retained=str(p),sha256=sha(p),bytes=p.stat().st_size,disposition='KEEP_REGISTERED_SOURCE'))
(TASK/'evidence/RETAIN_DEPENDENCIES.json').write_text(json.dumps(dict(task='TASK-DOWNSTREAM-CORE-ASSET-RECOVERY-AND-PILOT-001',protection_scope='Local durable task copies + versioned original code; not external-media backup',files=protected,external_keep_roots=['/home/liu/ring_first_3d_workspace/assets/retained_sources/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-HERO-BODY-ADAPT-018','/home/liu/ring_first_3d_workspace/.runtime','/home/liu/polyp_research/ring_anchor_3d/.venv','/home/liu/blender/blender-5.0.1-linux-x64','/home/liu/ring-first-hero-core/.local_data/G01_demo','/home/liu/ring_first_3d_workspace/experiments/TASK-E4-UNIFIED-RING-FIRST-HERO-DEPTH-001/audit/reference_banks'],deletion_authorized=False),indent=2)+'\n')
print('asset rows',len(rows),'protected file records',len(protected))
