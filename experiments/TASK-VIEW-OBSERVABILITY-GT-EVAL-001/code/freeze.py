"""Freeze existing predictions BEFORE opening GT. No prediction recomputation."""
from pathlib import Path
import json,hashlib,subprocess,datetime,shutil
R=Path(__file__).resolve().parents[1]
PREV=Path('/home/liu/ring_first_3d_incremental/experiments/TASK-PHASED-INCREMENTAL-FUSION-MULTIGROUP-001')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def state(p):
    def git(*a):return subprocess.check_output(['git','-C',str(p),*a]).decode(errors='replace')
    modified={}
    for entry in git('status','--porcelain','-z','-uno').split('\0'):
        if entry and (p/entry[3:]).is_file():modified[entry[3:]]=sha(p/entry[3:])
    return dict(HEAD=git('rev-parse','HEAD').strip(),branch=git('branch','--show-current').strip(),index_sha256=sha(Path(git('rev-parse','--git-path','index').strip()) if Path(git('rev-parse','--git-path','index').strip()).is_absolute() else p/git('rev-parse','--git-path','index').strip()),status=git('status','--porcelain','-z','-uall'),modified_sha256=modified)
def main():
    out=R/'provenance';out.mkdir(exist_ok=True)
    target=out/'PREDICTIONS_FROZEN.json'
    if target.exists():raise RuntimeError('Immutable prediction freeze exists')
    files=[]
    for base in ['code','metrics','provenance','local_results']:
        for p in sorted((PREV/base).rglob('*')):
            if p.is_file():files.append(dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p)))
    for n in ['config.json','TECHNICAL_REPORT.md','PROTOCOL.md']:
        p=PREV/n;files.append(dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p)))
    snapshot=R/'prediction_snapshot';snapshot.mkdir(exist_ok=True)
    names=['C_height_geometry.json','D_projected_diameter.json','D_observed_surface_definition_audit.json','B_scenes.json','B_source_ledger.json','B_main_scores.json','A_decisions.json']
    for n in names:shutil.copyfile(PREV/'metrics'/n,snapshot/n)
    obj=dict(UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),prior_root=str(PREV),GT_opened_this_task_before_freeze=False,files=files,snapshots={n:sha(snapshot/n)for n in names})
    obj['prediction_commit']=subprocess.check_output(['git','-C',str(PREV.parents[1]),'rev-parse','HEAD']).decode().strip()
    target.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
    roots=[Path('/home/liu/polyp_research'),Path('/home/liu/new-polyp-dxy')]+[Path('/home/liu')/n for n in ['ring_first_3d','ring_first_3d_scene_vis','ring_first_3d_abs_density','ring_first_3d_phase_d','ring_first_3d_incremental']]
    (out/'PROTECTED_START.json').write_text(json.dumps({str(p):state(p) for p in roots},ensure_ascii=False,indent=2)+'\n')
    print('Frozen',len(files),'files;',len(names),'metric snapshots; GT not opened')
if __name__=='__main__':main()
