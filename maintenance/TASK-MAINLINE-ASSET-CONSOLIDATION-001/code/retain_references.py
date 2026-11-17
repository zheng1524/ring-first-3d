"""Retain curated historical evidence and replace only new-tree duplicate paths."""
import os,json,hashlib,subprocess,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[3];T=Path(__file__).resolve().parents[1];C=R/'src/ring_first_3d/mainline';BASE=Path('/home/liu/ring_first_3d_growth_recovery');v=json.loads((T/'COPY_VERIFICATION.json').read_text());rows=v['files']
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def record(p,d,data,task,commit):
    d.parent.mkdir(parents=True,exist_ok=True)
    if d.exists():assert d.read_bytes()==data
    else:d.write_bytes(data)
    h=hashlib.sha256(data).hexdigest();rows.append(dict(original_path=str(p),source_task=task,source_commit=commit,original_sha256=h,new_path=str(d.relative_to(R)),new_sha256=h,status='EXACT_COPY',modified=False,reason='Retained historical evidence / approved visualization interface',path_adaptations=[]))
for name in ['real_p0_renderer.py','_phasec_c0_view_frozen.py','pointcloud_audit_renderer.py']:
    path='visualization/'+name;data=subprocess.check_output(['git','show','5636aaeb:'+path],cwd=BASE);record(path,C/'frozen_registry'/path,data,'APPROVED_P0_VISUALIZATION','5636aaebd61a3d53b69f528692c4c7095df46508')

# Relative compatibility links preserve original report image links without copies.
links={R/'mainline/results/visualization':R/'mainline/visualization/stalk_growth',
R/'mainline/visualization/TECHNICAL_REPORT.md':R/'mainline/results/TECHNICAL_REPORT.md',R/'mainline/visualization/RESULT_CARD.md':R/'mainline/results/RESULT_CARD.md',R/'mainline/visualization/FAILURE_REGISTRY.json':R/'mainline/results/FAILURE_REGISTRY.json'}
growth=C/'lineage/experiments/TASK-E4-G01-G03-GROWTH-RECOVERY-001'
links.update({growth/'review_assets':R/'mainline/results',growth/'visualization':R/'mainline/visualization/stalk_growth',growth/'metrics':R/'mainline/results/metrics'})
for p,d in links.items():
    p.parent.mkdir(parents=True,exist_ok=True)
    if not p.exists():p.symlink_to(os.path.relpath(d,p.parent))

# Preserve all existing curated tracked records under each promoted alias.
for alias in(R/'experiments').iterdir():
    if not alias.is_symlink():continue
    prefix=str(alias.relative_to(R));dest=alias.resolve();files=subprocess.check_output(['git','ls-files','-z','--',prefix],cwd=R).split(b'\0')
    for raw in files:
        if not raw:continue
        path=raw.decode();q=dest/Path(path).relative_to(prefix)
        if q.exists():continue
        data=subprocess.check_output(['git','show','bac3fc89:'+path],cwd=R);record(path,q,data,alias.name,'bac3fc89ef95db522b63cf6bb98e6914b9382864')

# Select at most three actual pictures per historical route, not whole result trees.
routes={
'TSDF':('/home/liu/ring_first_3d_e3d0','TASK-E3-D0-OPEN3D-TSDF-BASELINE-001'),
'NeuralFusion':('/home/liu/ring_first_3d_e3n0_eight','TASK-E3-N0-NEURALFUSION-EIGHT-VIEW-001'),
'MonoSDF_INCOMPLETE_TRAINING':('/home/liu/ring_first_3d_e3_sdf_multi','TASK-E3-SDF-RTX4090-M1-10X-MULTIPOLYP-001'),
'Native_HERO_Depth_018':('/home/liu/ring_first_3d_e4_sdf_localization','TASK-E4-HERO-BODY-ADAPT-018'),
'CrossVideo_BA_021':('/home/liu/ring_first_3d_e4_sdf_localization','TASK-E4-RING-ANCHORED-JOINT-BA-021')}
summary=[]
for label,(root,task)in routes.items():
    root=Path(root);old=root/'experiments'/task;dest=R/'mainline/references/historical_diagnostics'/label
    if not old.exists():continue
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip();pics=sorted((old/'figures').glob('*.png'))[:3]
    for p in [old/f for f in ['TECHNICAL_REPORT.md','RESULT_CARD.md','FAILURE_REGISTRY.json','FAILURE_LEDGER.md']]+pics:
        if p.is_file():record(p,dest/p.name,p.read_bytes(),task,commit)
    summary.append(dict(route=label,task=task,source=str(old),retained_images=[str((dest/p.name).relative_to(R))for p in pics],scientific_state='INCOMPLETE_TRAINING_NOT_SCIENTIFIC_FAILURE'if'MonoSDF'in label else'ORIGINAL_REPORT_STATUS_RETAINED'))
v.update(files=rows,exact_copies=sum(not r['modified']for r in rows),adapted_copies=sum(r['modified']for r in rows));(T/'COPY_VERIFICATION.json').write_text(json.dumps(v,indent=2)+'\n')
(R/'mainline/manifests/SOURCE_PROVENANCE.json').write_text(json.dumps(dict(files=rows,source_status='ACTIVE_RESEARCH_MAINLINE',scientific_certification=False),indent=2)+'\n')
(R/'mainline/references/HISTORICAL_RETENTION.json').write_text(json.dumps(summary,indent=2)+'\n')
print('Retained copies',len(rows),'historical reference groups',len(summary))
