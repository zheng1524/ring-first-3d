"""Package already completed evidence; never rerun or modify fusion here."""
from hero_tsdf_adapter import *
import re

def main():
    c=load(R/'config/BEFORE_ANY_INTEGRATION.json')
    for key,file in [('config','TSDF_CONFIG.json'),('manifest','HERO_TSDF_INPUT_MANIFEST.json'),('selection','VIEW_COVERAGE_SELECTION.csv')]:assert sha(R/file)==c[key]['sha256'],'FROZEN_INPUT_CHANGED'
    A=REPO/'experiments/TASK-E3-A-SOURCE-AUDIT-AND-PROBLEM-DEFINITION-001';B=REPO/'experiments/TASK-E3-B-LOCAL-HERO-FIELDS-001';C=REPO/'experiments/TASK-E3-C-VISIBILITY-CONSENSUS-001';CG=REPO/'experiments/TASK-CAMERA-GATE-G01-004-PILOT-001'
    inherited=[dict(role=role,asset=asset(path))for role,path in [('E1 exact guard/IO/AST helper reuse',E1/'code/common.py'),('exact unproject helper',OLD/'ring_first_v1/scripts/common.py'),('exact frozen projector/pixel-center K helpers',REPO/'visualization/real_p0_renderer.py'),('exact same-camera physical scale bar',REPO/'visualization/same_camera_scene.py'),('E3A source organization',A/'provenance/SOURCE_ORGANIZATION.json'),('E3A fixed ROI/frame reference; no clipping',A/'config/GLOBAL_ROI_FROZEN.json'),('E3B native ancestry rules adapted; not module-main execution',B/'code/hero_native_adapter.py'),('E3C posthoc diagnostic only',C/'VISIBILITY_EVIDENCE.csv'),('Camera Gate conditional evidence; parent immutable',CG/'CAMERA_QUALIFICATION.csv'),('View Partition inherited direction blocks',PART/'metrics/view_distribution.json')]]
    save('config/INHERITED_EVIDENCE_INDEX.json',dict(entries=inherited,metadata_only_or_posthoc=True,inputs_are_only_frozen_six_original_HERO_depths=True))
    required=['TECHNICAL_REPORT.md','FAILURE_LEDGER.md','REPRODUCE.md','HERO_TSDF_INPUT_MANIFEST.json','VIEW_COVERAGE_SELECTION.csv','TSDF_CONFIG.json','G0_G1_METRICS.csv','TSDF_FAILURE_CASES.csv','NEXT_STAGE_RECOMMENDATION.md']
    for p in required:assert (R/p).is_file(),p
    links=[]
    for p in R.glob('*.md'):
        if p.name=='TASK.md':continue
        for link in re.findall(r'\]\(([^)]+)\)',p.read_text()):
            if link.startswith(('http:','https:','#')):continue
            ok=(p.parent/link.split('#')[0]).exists();links.append(dict(document=p.name,target=link,exists=ok));assert ok,(p.name,link)
    for p in(R/'code').glob('*.py'):compile(p.read_text(),str(p),'exec')
    pngs=[]
    for p in sorted((R/'figures').glob('*.png')):
        im=Image.open(p);assert im.width>=1500 and im.height>=1200;pngs.append(dict(**asset(p),width=im.width,height=im.height))
    assert len(pngs)==4
    preview=load(R/'PREVIEW_INDEX.json')
    for a in preview['files']:assert sha(a['path'])==a['sha256']
    before=load(R/'config/PROTECTED_START.json');after=protected_state();assert before==after,'HISTORICAL_WORKTREE_CHANGED'
    save('FINAL_STATUS.json',dict(task=R.name,branch='exp/'+R.name,parent_commit=git(REPO,'rev-parse','HEAD'),user_date='2026-11-02 Asia/Shanghai',numeric_Mesh_output_success=dict(videos=1,target=1,SINGLE=True,G0=True,G1=True),scientific_quality='NOT_ACCEPTED_PENDING_PM',preregistered_engineering_gate='FAIL_RETAINED',adapter_formally_frozen=False,scientific_parameters_frozen=False,GPU_authorization='NOT_GRANTED',GPU_use=0,new_inference=0,neural_training=0,camera_updates=0,GT_read=False,historical_fallback=0,diameter_prediction=None,source_count_G0=3,source_count_G1=6,view_blocks_G1=5,checks_pass=24,checks_fail=1,unknown_back_completion=False,full_TSDF_weights_serialization_available=False,official_TSDF_replay_verified=True,all_historical_worktrees_unchanged=True,next_stage_started=False))
    save('config/DELIVERY_VALIDATION.json',dict(required_files=required,links=links,syntax_files=len(list((R/'code').glob('*.py'))),PNG=pngs,all_historical_worktrees_unchanged=True,preintegration_config_SHA_unchanged=True,preview_faces_verified=True,official_replay_CLI_test='runtime/replay_G0_delivery_check/REPLAY.json'))
    files=[p for p in R.rglob('*')if p.is_file()and not any(part in ['runtime','local_results','__pycache__']for part in p.relative_to(R).parts)and p.name!='DELIVERY_INDEX.json']
    save('DELIVERY_INDEX.json',dict(files=[asset(p)for p in sorted(files)],uploaded_selection='all listed task files except task-local runtime/local_results; raw data not copied',local_large_evidence_index='LOCAL_RESULTS_INDEX.json',code_frozen_for_review=True,adapter_scientifically_frozen=False))
    print('DELIVERY_CHECKED',len(files),'files',sum(p.stat().st_size for p in files),'bytes; no gate relaxation',flush=True)
if __name__=='__main__':main()
