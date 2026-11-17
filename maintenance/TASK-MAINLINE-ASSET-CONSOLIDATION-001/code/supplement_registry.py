import json,hashlib,subprocess,csv,io,datetime
from pathlib import Path
R=Path(__file__).resolve().parents[3];T=Path(__file__).resolve().parents[1];C=R/'src/ring_first_3d/mainline';BASE=Path('/home/liu/ring_first_3d_growth_recovery');v=json.loads((T/'COPY_VERIFICATION.json').read_text());rows=v['files']
tasks={
'TASK-E3-D0-OPEN3D-TSDF-BASELINE-001':['hero_tsdf_adapter.py'],
'TASK-E3-N0-NEURALFUSION-EIGHT-VIEW-001':['infer.py'],
'TASK-E3-SDF-MONOSDF-FULL-TRAINING-REVALIDATION-001':['official_adapter.py']}
for task,names in tasks.items():
 for name in names:
  rel=Path('experiments')/task/'code'/name;data=subprocess.check_output(['git','show','5636aaeb:'+str(rel)],cwd=BASE);dest=C/'lineage'/rel;dest.parent.mkdir(parents=True,exist_ok=True)
  if dest.exists():assert dest.read_bytes()==data
  else:dest.write_bytes(data)
  h=hashlib.sha256(data).hexdigest();rows.append(dict(original_path=str(rel),source_task=task,source_commit='5636aaebd61a3d53b69f528692c4c7095df46508',original_sha256=h,new_path=str(dest.relative_to(R)),new_sha256=h,status='EXACT_COPY',modified=False,reason='Deprecated exploration core retained as historical reference; not an active renderer/optimizer',path_adaptations=[]))
task='TASK-E3-SDF-RTX4090-M1-10X-MULTIPOLYP-001';old=Path('/home/liu/ring_first_3d_e3_sdf_4090/experiments')/task;dest=R/'mainline/references/historical_diagnostics/MonoSDF_INCOMPLETE_TRAINING';dest.mkdir(parents=True,exist_ok=True)
pics=sorted((old/'figures').glob('*.png'))[:3]
for p in [old/'TECHNICAL_REPORT.md',old/'FAILURE_LEDGER.md']+pics:
 if p.is_file():
  data=p.read_bytes();q=dest/p.name;q.write_bytes(data);h=hashlib.sha256(data).hexdigest();rows.append(dict(original_path=str(p),source_task=task,source_commit='5636aaebd61a3d53b69f528692c4c7095df46508',original_sha256=h,new_path=str(q.relative_to(R)),new_sha256=h,status='EXACT_COPY',modified=False,reason='Incomplete training evidence retained without calling it fully trained failure',path_adaptations=[]))
p=R/'mainline/references/HISTORICAL_RETENTION.json';hist=json.loads(p.read_text());hist.append(dict(route='MonoSDF_INCOMPLETE_TRAINING',task=task,source=str(old),retained_images=[str((dest/p.name).relative_to(R))for p in pics],scientific_state='INCOMPLETE_TRAINING_NOT_SCIENTIFIC_FAILURE'));p.write_text(json.dumps(hist,indent=2)+'\n')
v.update(files=rows,exact_copies=sum(not r['modified']for r in rows),adapted_copies=sum(r['modified']for r in rows));(T/'COPY_VERIFICATION.json').write_text(json.dumps(v,indent=2)+'\n');(R/'mainline/manifests/SOURCE_PROVENANCE.json').write_text(json.dumps(dict(files=rows,source_status='ACTIVE_RESEARCH_MAINLINE',scientific_certification=False),indent=2)+'\n')
for path in [R/'mainline/manifests/MAINLINE_ASSET_MAP.json',T/'MAINLINE_ASSET_MAP.json']:
 x=json.loads(path.read_text())
 for row in x['modules']:
  if row['id']=='E1_E2_NINE_PARAMETER':row['implementation']='src/ring_first_3d/mainline/lineage/experiments/TASK-E4-A1-COARSE-BODY-001/code/models.py; TASK-E4-BODY-GUIDED-HERO-DXY-REPAIR-001/code/fitting.py; frozen_registry T04–T09'
 for task,names in tasks.items():x['modules'].append(dict(id=task,classification='DEPRECATED_EXPLORATION',implementation='src/ring_first_3d/mainline/lineage/experiments/'+task+'/code/'+names[0],scientific_state='INCOMPLETE_TRAINING'if'MONOSDF'in task else'ORIGINAL_NEGATIVE_EVIDENCE_RETAINED',rerun=False))
 path.write_text(json.dumps(x,indent=2)+'\n')
p=R/'docs/registry/EXPERIMENT_INDEX.csv';base=subprocess.check_output(['git','show','bac3fc89:docs/registry/EXPERIMENT_INDEX.csv'],cwd=R,text=True);reader=csv.DictReader(io.StringIO(base));fields=reader.fieldnames;entries=list(reader);row={k:''for k in fields};row.update(THEME='工程维护',TASK_ID=T.name,BRANCH='maintenance/'+T.name,DATE='2026-11-18',RESEARCH_QUESTION='主线资产集中与可复现性',METHOD='SHA复制闭包/静态payload去重/固定重放',GROUPS='2物理组;8固定模块',RESULT='247回归+8/8重放;科研未认证',ENGINEERING_STATUS='VERIFIED',SCIENTIFIC_STATUS='ACTIVE_RESEARCH_MAINLINE_NOT_CERTIFIED',REUSABLE_COMPONENTS='mainline/README.md',FAILURE_EVIDENCE=str((T/'FAILURE_REGISTRY.json').relative_to(R)),REPORT_PATH=str((T/'TECHNICAL_REPORT.md').relative_to(R)),SOURCE_SNAPSHOT_NOTE='Source baseline bac3fc89; final delivery SHA supplied in handoff; not a new scientific measurement')
entries.append(row)
with p.open('w',newline='')as f:w=csv.DictWriter(f,fields,lineterminator='\n');w.writeheader();w.writerows(entries)
print('Supplemented actual MonoSDF source/evidence and kept CSV schema valid')
