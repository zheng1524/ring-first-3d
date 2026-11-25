import json,csv,hashlib,subprocess,io
from pathlib import Path
W=Path('/home/liu/ring_first_3d_workspace');T=Path('/home/liu/.config/superpowers/worktrees/ring_first_3d_workspace/TASK-M2F12/experiments/TASK-M2F12-CLEANUP-AND-HISTORICAL-004-CAMERA-RESTORATION-001');E=Path('/home/liu/polyp_research/ring_anchor_3d/experiments')
import sys;sys.path.insert(0,str(T/'code'));from historical_io import sha,SOURCES
import cv2,numpy as np
blob=subprocess.check_output(['git','-C',str(W),'show','2cd9822e1fbd3841a6151abc54acdc6ffe1d5a6c:experiments/TASK-M2F10-V6-MULTIVIEW-HERO-EXPANSION-001/evidence/final/VIDEO_METRICS.csv']);(T/'evidence/V6_VIDEO_METRICS.csv').write_bytes(blob);rows=list(csv.DictReader(io.StringIO(blob.decode())))
assert len(rows)==10 and len({r['group_id']for r in rows})==5
states=list((W/'runs/m2f10_v6_multiview/M2F10-FORMAL-20261125-02').rglob('RUN_STATE.json'));registry=[]
for r in rows:
 name=r['group_id']+'_'+r['video_id'];video=W/'smart_endoscope_20260805 (1)/raw'/(name+'.mp4');digest=sha(video);ss=[]
 for p in states:
  d=json.loads(p.read_text())
  if d['raw_video']==str(video):assert d['raw_video_sha256']==digest;assert d['code_commit']=='a38d4c822daf9a9b3cd88e1cd0edebdc70b9bfad';ss.append(dict(path=str(p),sha256=sha(p),run_id=d['run_id'],code_commit=d['code_commit']))
 assert ss
 cap=cv2.VideoCapture(str(video));n=int(cap.get(cv2.CAP_PROP_FRAME_COUNT));fps=cap.get(cv2.CAP_PROP_FPS);cap.release();frames=np.rint(np.linspace(round(n*82/1265),round(n*1192/1265),16)).astype(int).tolist()
 cfg=json.loads((E/'ring_first_v5_real_validation/config.json').read_text());ring=5. if '_R5_'in r['group_id']else 10.
 cfg.update(group=r['group_id'],video_id=r['video_id'],video=str(video),video_sha256=digest,nominal_frames=frames,raw_frames=frames,ring_inner_mm=ring,R_mm=ring/2+.6,intrinsics=[{'name':'F980','fx_native':980.}],formal_repetition=0,source_method='historical V5 C_F980_0 -> features019 -> native RF5DoF RGB; no V6 solved inputs',sampling='historical uniform16 schedule scaled by video length; exact seek image identity verified against sequential decode',HERO_budget_per_video=1,HERO_selection='first legal target in ascending verified raw-frame order with original support constraints; no depth-based reselection',optimization_variant=None)
 root=W/'runs/m2f12_historical004/H004_RAW_BASELINE'/name
 for sub in ['inputs/images','inputs/masks','observations','predictions','metrics','logs','preparation','runtime','scripts']:(root/sub).mkdir(parents=True,exist_ok=True)
 (root/'config.json').write_text(json.dumps(cfg,indent=2));registry.append(dict(case=name,group=r['group_id'],video_id=r['video_id'],raw_video=str(video),raw_sha256=digest,frames=n,fps=fps,nominal_frames=frames,ring_inner_mm=ring,V6_states=ss,config=str(root/'config.json'),config_initial_sha256=sha(root/'config.json')))
(T/'evidence/INPUT_REGISTRY.json').write_text(json.dumps(registry,indent=2));(T/'evidence/SOURCE_LOCK_PRE_RUN.json').write_text(json.dumps({str(p):sha(p) for p in list(SOURCES.values())+list((T/'code').glob('historical*.py'))},indent=2));print('frozen',len(rows),'videos',len(states),'V6 states; actual execution commit a38d4c8')
