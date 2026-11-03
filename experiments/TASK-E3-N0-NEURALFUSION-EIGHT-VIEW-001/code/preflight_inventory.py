"""Document/metadata inventory only. No experimental qualification or inference."""
from pathlib import Path
import json,csv,hashlib,shutil
R=Path(__file__).resolve().parents[1];REPO=R.parents[1]
PREVIOUS=Path('/home/liu/ring_first_3d_e3n0_gate_b')
A3=Path('/home/liu/ring_first_3d_e3n0_a3/experiments/TASK-E3-N0-GATE-A3-MASK-BOUNDARY-CLEANUP-001')
def asset(p):return dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size)
def save(name,value):
    p=R/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def main():
    assert not (R/'config/EXPERIMENT_FROZEN.json').exists(),'PREFLIGHT_ONLY_DO_NOT_OVERWRITE_FROZEN_EXPERIMENT'
    docs=[]
    for task,commit in [
        ('TASK-E3-A-SOURCE-AUDIT-AND-PROBLEM-DEFINITION-001','8f5f7ea59efb32a0f633409386431811444ee399'),
        ('TASK-E3-B-LOCAL-HERO-FIELDS-001','a7c6233f33f9a2ec84b4ce19f668a187bd90b9c8'),
        ('TASK-E3-C-VISIBILITY-CONSENSUS-001','e8feece0718fee24a1b04b5e250629820e4f8299'),
        ('TASK-E3-D0-OPEN3D-TSDF-BASELINE-001','d69ade170352d1b5a1e46239f9516ab38c575648'),
        ('TASK-CAMERA-GATE-G01-004-PILOT-001','6423b2709d1b528124ba6cc855883ba8a437e28c'),
        ('TASK-E3-N0-GATE-A-COMPAT-CROP-METRIC-001','4b60db5d9402c2bb87692ba3b2b7819f3c7c1423'),
        ('TASK-E3-N0-GATE-A2-PROJECTIVE-CLEANUP-001','75ba88303f5ca2e3eee362451d7a717d92506e10'),
        ('TASK-E3-N0-GATE-A3-MASK-BOUNDARY-CLEANUP-001','b114ee0b5470f98303f20f4e2bcd1ccd1f3e5ed7'),
        ('TASK-E3-N0-GATE-B-NEURALFUSION-F0-F2-001','40ed60ae234ecac47be4e0235074fa280c79f2b1')]:
        p=PREVIOUS/'experiments'/task/'TECHNICAL_REPORT.md';docs.append(dict(kind=task,commit=commit,document=asset(p),full_report_read=True))
    extra=[PREVIOUS/'AGENTS.md',PREVIOUS/'COLLAB_STANDARD_v1.3.md',
        PREVIOUS/'experiments/TASK-CAMERA-GATE-G01-004-PILOT-001/CAMERA_GATE_PROTOCOL_v0.1.md',
        PREVIOUS/'experiments/TASK-CAMERA-GATE-G01-004-PILOT-001/config/protocol.json',
        A3/'V5_LOCAL_REPORT.md',A3/'V6_LOCAL_REPORT.md']
    docs.extend(dict(kind='module_document_or_local_record',document=asset(p),full_report_read=True)for p in extra)
    save('provenance/READING_AND_VERSION_RECEIPTS.json',dict(documents=docs,
        canonical_critical_technical_version_MD='NOT_LOCATED; REQUESTED_FROM_RESEARCHER',
        search_scope=['all local ring_first_3d worktrees','downloads','all Git-history MD filenames','remote branch tips','Codex attachments'],
        no_newer_Camera_Gate_document_located=True))
    request=Path('/home/liu/.codex/attachments/e0407865-e567-4a5e-8517-76405b13479f/Pasted text.txt')
    shutil.copy2(request,R/'TASK.md');save('provenance/APPROVED_TASK.json',asset(request))
    source_path=Path('/home/liu/ring_first_3d_neural_e1/experiments/TASK-NEURAL-E1-PIPELINE-RECOVERY-001/provenance/INPUT_ELIGIBILITY.json')
    refs=json.loads(source_path.read_text())['references'];scenes=['G01_004','G06_004','G07_004','G08_005'];rows=[]
    for scene in scenes:
        for c in refs:
            if c['scene_id']!=scene:continue
            n=c.get('E1_actual_native',{})
            rows.append(dict(scene=scene,source=c['id'],cached_reference=c['reference'],raw_frame=c['raw_frame']if c['raw_frame']is not None else'UNKNOWN_NOT_INFERRED',
                native_depth_path=n.get('path',''),native_file_exists=Path(n.get('path','MISSING')).is_file(),
                expected_native_SHA256=n.get('sha256',''),RGB_path=c['RGB'],Mask_path=c['Mask'],camera_path=c['camera_file'],
                camera_index=c['reference_index'],historical_reference_screened=c['source_camera_qualified'],
                latest_gate_this_task='NOT_RUN_PENDING_VERSION_DOCUMENT',selected_for_fusion=False,
                new_depth_predicted=False))
    with (R/'SOURCE_INVENTORY.csv').open('w',newline='')as f:
        w=csv.DictWriter(f,fieldnames=rows[0].keys(),lineterminator='\n');w.writeheader();w.writerows(rows)
    counts={scene:sum(a['scene']==scene for a in rows)for scene in scenes}
    save('TASK_STATUS.json',dict(status='PREFLIGHT_AWAITING_REQUIRED_CANONICAL_VERSION_DOCUMENT',source_reference_counts=counts,
        input_qualification_run=False,source_list_frozen=False,cleanup_run=False,domain_selected=False,
        GPU_forward_N=0,optimizer_steps=0,new_HERO_N=0,enhanced_20_30_run=False,
        legacy_F0_quality_stop='REVOKED_FOR_THIS_NEW_TASK_ONLY_BY_EXPLICIT_USER_INSTRUCTION',historical_conclusions_preserved=True))
    print('READ_ONLY_PREFLIGHT',counts,'GPU=0; version document pending')
if __name__=='__main__':main()
