"""Publish task-local initializations into the unchanged inherited interfaces."""
from common import *
import shutil

def link(a,b):
    b.parent.mkdir(parents=True,exist_ok=True)
    if not b.exists():b.symlink_to(a.resolve(),target_is_directory=a.is_dir())

def arm_case(tag,n,initial,phase='A'):
    root=R/'arms'/tag
    for d in ['inputs','depth_observations','local_results','metrics','config','provenance','runtime']:(root/d).mkdir(parents=True,exist_ok=True)
    src=R/'inputs'/n;dst=root/'inputs'/n;dst.mkdir(exist_ok=True)
    for p in src.iterdir():
        if p.is_file()and p.name!='INITIAL.npz':link(p,dst/p.name)
    if not(dst/'INITIAL.npz').exists():shutil.copyfile(initial,dst/'INITIAL.npz')
    for p in(R/'depth_observations').glob('*.npz'):link(p,root/'depth_observations'/p.name)
    cfg=load(R/'config/PROTOCOL.json');(root/'config/PROTOCOL.json').write_text(json.dumps(cfg,ensure_ascii=False,indent=2)+'\n');(root/'config/ARM.json').write_text(json.dumps(dict(tag=tag,phase=phase,loss='D0_013',budget=cfg['phase_A']['downstream']if phase=='A'else{k:cfg['phase_B'][k]for k in['max_proposals','max_accepted','consecutive_rejection_stop']}),indent=2)+'\n')
    return root

def export_A(n):
    dest=R/'initializations'/n;dest.mkdir(parents=True,exist_ok=True);p=dest/'Init-A.npz'
    if not p.exists():shutil.copyfile(R/'inputs'/n/'INITIAL.npz',p)
    z=np.load(p);trimesh.Trimesh(z['V'],z['F_solid'],process=False).export(dest/'Init-A_mm.ply')
    return p
