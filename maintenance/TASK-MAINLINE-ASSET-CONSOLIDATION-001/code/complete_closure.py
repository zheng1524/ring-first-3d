import json,hashlib,os,subprocess,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[3];T=Path(__file__).resolve().parents[1];BASE=Path('/home/liu/ring_first_3d_growth_recovery');C=R/'src/ring_first_3d/mainline/lineage'
v=json.loads((T/'COPY_VERIFICATION.json').read_text());rows=v['files']
def add(p,q,task,commit):
    data=p.read_bytes();q.parent.mkdir(parents=True,exist_ok=True)
    if q.exists():assert q.read_bytes()==data
    else:q.write_bytes(data)
    h=hashlib.sha256(data).hexdigest();rows.append(dict(original_path=str(p),source_task=task,source_commit=commit,original_sha256=h,new_path=str(q.relative_to(R)),new_sha256=h,status='EXACT_COPY',modified=False,reason='Required by the unchanged existing regression/Failure Registry',path_adaptations=[]))
name='TASK-E4-G01-DUALVIDEO-BODY-ANCHORED-REGISTRATION-001-SIM-PROTOCOL-REV1';s=Path('/home/liu/ring_first_3d_g01_sim_rev1/experiments')/name;d=C/'experiments'/name
for p in s.glob('*'):
    if p.is_file()and p.name in ['TASK.yaml','TASK_FREEZE.json','TECHNICAL_REPORT.md','RESULT_CARD.md','FAILURE_REGISTRY.json']:add(p,d/p.name,name,'0a3fe96bb1d91e5719f8e21bcf232e0967dd233f')
for p in(s/'inputs').glob('*.json'):add(p,d/'inputs'/p.name,name,'0a3fe96bb1d91e5719f8e21bcf232e0967dd233f')
alias=R/'experiments'/name
if not alias.exists():alias.symlink_to(os.path.relpath(d,alias.parent))
wrong=R/'experiments/TASK-E4-G01-DUALVIDEO-SIM-PROTOCOL-REV1'
if wrong.is_symlink()and not wrong.exists():wrong.unlink()
memory=json.loads((R/'docs/registry/FAILURE_REGISTRY.json').read_text())
for entry in memory['failures']:
    for x in entry['evidence']:
        if isinstance(x,dict):
            p=BASE/x['path'];assert hashlib.sha256(p.read_bytes()).hexdigest()==x['sha256'];add(p,R/x['path'],'FAILURE_MEMORY','bac3fc89ef95db522b63cf6bb98e6914b9382864')
v.update(files=rows,exact_copies=sum(not r['modified']for r in rows),adapted_copies=sum(r['modified']for r in rows));(T/'COPY_VERIFICATION.json').write_text(json.dumps(v,indent=2)+'\n')
(R/'mainline/manifests/SOURCE_PROVENANCE.json').write_text(json.dumps(dict(files=rows,source_status='ACTIVE_RESEARCH_MAINLINE',scientific_certification=False),indent=2)+'\n')
print('Closure files',len(rows))
