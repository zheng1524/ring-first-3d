#!/usr/bin/env python3
"""M2F7 HIST-V6 raw-only runner.

Calls frozen V6 modules in place.  The only V6 adaptation is the approved
original16 branch: V6 reads V5 observations/candidates from a *fresh* V5
runtime root recomputed from the 22 raw frames, never from historical V5.
"""
import argparse, json, hashlib, os, sys, shutil, subprocess
from pathlib import Path
import cv2, numpy as np

WS=Path('/home/liu/ring_first_3d_workspace')
EXP=WS/'experiments/TASK-M2F7-HIST-G01-CAUSAL-001'
RUN=WS/'runs/m2f7_hist_g01/hist_v6'
V6=Path('/home/liu/polyp_research/ring_anchor_3d/experiments/ring_first_v6_local_reconstruction')
V5=Path('/home/liu/polyp_research/ring_anchor_3d/experiments/ring_first_v5_geometry_crossvideo')
V4=Path('/home/liu/polyp_research/ring_anchor_3d/experiments/surface_reconstruction_v4')
V4SYN=Path('/home/liu/polyp_research/ring_anchor_3d/experiments/ring_first_v4_synthetic_audit')
F1=Path('/home/liu/polyp_research/ring_anchor_3d/experiments/surface_fusion_v1')
DXY=Path('/home/liu/new-polyp-dxy')
RAW=WS/'smart_endoscope_20260805 (1)/raw/GP_Ip_12.0mm_closed_R10_single_refY_005.mp4'
V5RAW=RUN/'v5raw'
V6SCRIPTS=V6/'scripts'
CONFIG_HASH='d2f61b29b454a7f7e48b5d5f1254cd806ff9348335f220fb1e5f11ddedc61ddc'

def h(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,x): Path(p).parent.mkdir(parents=True,exist_ok=True); Path(p).write_text(json.dumps(x,indent=1,default=str)+'\n')
def trace(stage, route, entry, inputs, outputs, status, extra=None):
 p=RUN/'RUN_TRACE.jsonl';p.parent.mkdir(parents=True,exist_ok=True)
 rec=dict(run_id='HIST-V6-G01-005-RAW-001',group_id='GP_Ip_12.0mm_closed_R10_single_refY',video_id='005',stage=stage,route_id=route,route_version='v6-unregistered',entrypoint=entry,inputs=[str(x) for x in inputs],outputs=[str(x) for x in outputs],status=status,code_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=WS,text=True).strip(),config_hash=CONFIG_HASH)
 if extra:rec.update(extra)
 with p.open('a') as f:f.write(json.dumps(rec,sort_keys=True,default=str)+'\n')

def setup_dirs():
 for d in ['inputs','observations','predictions','metrics','raw','meshes','scenes','visualizations','v5raw/inputs','v5raw/observations','v5raw/predictions','v5raw/metrics']:
  (RUN/d).mkdir(parents=True,exist_ok=True)
 # run-local source/aliases; no historical writes
 (V5RAW/'scripts').unlink(missing_ok=True)
 (V5RAW/'scripts').symlink_to(V5/'scripts')
 (V5RAW/'config.json').write_bytes((V5/'config.json').read_bytes())
 (RUN/'scripts').mkdir(parents=True,exist_ok=True)
 # source aliases required by existing V6 path constants
 for name,target in [('ring_first_v5_geometry_crossvideo',V5),('surface_reconstruction_v4',V4),('ring_first_v4_synthetic_audit',V4SYN),('surface_fusion_v1',F1)]:
  p=RUN.parent/name
  if p.exists() or p.is_symlink(): p.unlink()
  p.symlink_to(target)
 (RUN/'config.json').write_bytes((V6/'config.json').read_bytes())

def make_inputs():
 ledger0=json.loads((V6/'inputs/ledger005_preseg.json').read_text())
 sys.path.insert(0,str(DXY/'src'))
 from dxy_mid.segmentation import INITSegmentation
 import torch
 torch.set_num_threads(4)
 model=INITSegmentation(str(Path('/home/liu/polyp_research/experiments/v8_5_cross_ring_pipeline_audit_20261014/freeze/model')),'cuda' if torch.cuda.is_available() else 'cpu')
 cap=cv2.VideoCapture(str(RAW)); frames=[]
 while True:
  ok,im=cap.read()
  if not ok:break
  frames.append(im)
 cap.release();assert len(frames)==861
 rows=[]
 for a in ledger0:
  i=int(a['raw_frame']);im=cv2.resize(frames[i],(640,360),interpolation=cv2.INTER_AREA)
  rgb=RUN/'inputs'/f'v005_{i:05d}.png';cv2.imwrite(str(rgb),im)
  mask=RUN/'inputs'/f'v005_{i:05d}_mask.png';lab=model.predict(str(rgb));cv2.imwrite(str(mask),lab)
  rows.append(dict(id=f'v005_{i:05d}',source=RAW.name,source_id='005',raw_frame=i,time_sec=a.get('time_sec'),old_index=a.get('old_index'),native_resolution=[1280,720],RGB_path=str(rgb),Mask_path=str(mask),RGB_SHA256=h(rgb),Mask_SHA256=h(mask),original16=bool(a['original16']),role='M2F7 raw decode + INIT segmentation',exact_sequential_identity=True))
 write(RUN/'inputs/ledger005_preseg.json',rows);write(RUN/'inputs/ledger005.json',rows)
 write(V5RAW/'inputs/ledger.json',rows)
 # freeze input manifest; verify paths exist and hashes
 files={str(RUN/'config.json'):h(RUN/'config.json'),str(RUN/'inputs/ledger005_preseg.json'):h(RUN/'inputs/ledger005_preseg.json'),str(RAW):h(RAW)}
 for r in rows:files[r['RGB_path']]=r['RGB_SHA256'];files[r['Mask_path']]=r['Mask_SHA256']
 write(RUN/'metrics/freeze_inputs.json',dict(files=files,GT_selection=False,historical_measurement_fallback=0,source='M2F7_RAW'))
 write(V5RAW/'metrics/freeze_inputs.json',dict(files={str(V5RAW/'config.json'):h(V5RAW/'config.json'),str(V5RAW/'inputs/ledger.json'):h(V5RAW/'inputs/ledger.json')},GT_selection=False,historical_measurement_fallback=0))
 trace('input','hist-v6-raw-input','m2f7_hist_v6.py::make_inputs',[RAW],[RUN/'inputs/ledger005_preseg.json'],'PASS',{'frames':len(rows),'rgb_sha256':h(RUN/'inputs/ledger005_preseg.json')})
 print('INPUTS',len(rows),flush=True)

def import_sources():
 sys.path[:0]=[str(V6SCRIPTS),str(V5/'scripts'),str(DXY/'src')]
 import v6_common,prepare_ring,track005,local_ring_sfm,validate_select,select_supported_views,run_mvs005,run_mvs005_supported,package_surfaces
 # V5 raw modules; patch their module-level run root to v5raw
 import g5_common,ring_observations,ring_candidates_diverse
 g5_common.R=V5RAW;ring_observations.R=V5RAW;ring_candidates_diverse.R=V5RAW
 # V6 run root; patch all script globals that were copied by 'from v6_common import *'
 v6_common.R=RUN;v6_common.V5=V5RAW;v6_common.E=RUN.parent;v6_common.REPO=Path('/home/liu/polyp_research')
 mods=[prepare_ring,track005,local_ring_sfm,validate_select,select_supported_views,run_mvs005,run_mvs005_supported,package_surfaces]
 for m in mods:
  m.R=RUN;m.V5=V5RAW
  if hasattr(m,'REPO'):m.REPO=Path('/home/liu/polyp_research')
  if hasattr(m,'V4'):m.V4=V4
  if hasattr(m,'F1'):m.F1=F1
 return dict(v6_common=v6_common,prepare_ring=prepare_ring,track005=track005,local_ring_sfm=local_ring_sfm,validate_select=validate_select,select_supported_views=select_supported_views,run_mvs005=run_mvs005,run_mvs005_supported=run_mvs005_supported,package_surfaces=package_surfaces,g5_common=g5_common,ring_observations=ring_observations,ring_candidates_diverse=ring_candidates_diverse)

def run_stage(name, mods):
 if name=='v5obs':
  mods['ring_observations'].main();trace('v5_ring_observation','v5-ring-observations','ring_observations.py::main',[V5RAW/'inputs/ledger.json'],[V5RAW/'metrics/ring_observations.json'],'PASS')
 if name=='v5cand':
  mods['ring_candidates_diverse'].main();trace('v5_ring_candidates','v5-ring-candidates','ring_candidates_diverse.py::main',[V5RAW/'metrics/ring_observations.json'],[V5RAW/'predictions/ring_candidates_diverse.json'],'PASS')
 if name=='ring':
  mods['prepare_ring'].main();trace('v6_prepare_ring','v6-prepare-ring','prepare_ring.py::main',[RUN/'inputs/ledger005_preseg.json',V5RAW/'predictions/ring_candidates_diverse.json'],[RUN/'predictions/ring_candidates005.json'],'PASS')
 if name=='track':
  mods['track005'].main();trace('v6_track005','rf-frozen-tracks005@1','track005.py::main',[RUN/'predictions/ring_candidates005.json'],[RUN/'observations/tracks005.npz'],'PASS')
 if name=='ba':
  mods['local_ring_sfm'].main();trace('v6_local_ring_sfm','rf-frozen-ba-local-ring-sfm@1','local_ring_sfm.py::main',[RUN/'observations/tracks005.npz'],[RUN/'predictions/local005_camera_0.npz',RUN/'predictions/local005_camera_1.npz'],'PASS')
 if name=='validate':
  mods['validate_select'].main();trace('v6_validate_select','v6-validate-select','validate_select.py::main',[RUN/'predictions/local005_camera_0.npz'],[RUN/'metrics/local_validation.json',RUN/'inputs/MVS_cases.json'],'PASS')
 if name=='support':
  import runpy; mods['v6_common'].R=RUN; runpy.run_path(str(V6SCRIPTS/'select_supported_views.py'));trace('v6_support','v6-supported-views','select_supported_views.py::main',[RUN/'metrics/local_validation.json'],[RUN/'inputs/MVS_supported_cases.json'],'PASS')
 if name=='hero':
  mods['run_mvs005'].main();trace('v6_hero','surface_fusion_v1/run_mvs_adapter3','run_mvs005.py::main',[RUN/'inputs/MVS_cases.json'],[RUN/'raw'],'PASS')
 if name=='hero_supported':
  mods['run_mvs005_supported'].main();trace('v6_hero_supported','surface_fusion_v1/run_mvs_adapter3','run_mvs005_supported.py::main',[RUN/'inputs/MVS_supported_cases.json'],[RUN/'raw'],'PASS')
 if name=='mesh':
  mods['package_surfaces'].main();trace('v6_mesh','v6-depth-mesh','package_surfaces.py::main',[RUN/'raw'],[RUN/'meshes'],'PASS')

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--stage',action='append',default=[]);a=ap.parse_args();setup_dirs()
 if not a.stage or any(s in ('v5obs','v5cand','ring') for s in a.stage):make_inputs()
 if not a.stage:print('INPUTS_ONLY');return
 mods=import_sources()
 for s in a.stage:run_stage(s,mods)
 print('DONE',a.stage,flush=True)
if __name__=='__main__':main()
