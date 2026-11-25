#!/usr/bin/env python3
"""M2F8 V6-GENERALIZED adapter. Calls frozen V6/V5 source; no core algorithm copy."""
import sys,json,hashlib,runpy,argparse,traceback
from pathlib import Path
import cv2,numpy as np,pandas as pd
WS=Path('/home/liu/ring_first_3d_workspace');BASE=WS/'runs/m2f8_v6_general';INP=BASE/'current_inputs'
V6=Path('/home/liu/polyp_research/ring_anchor_3d/experiments/ring_first_v6_local_reconstruction');V6S=V6/'scripts'
V5=Path('/home/liu/polyp_research/ring_anchor_3d/experiments/ring_first_v5_geometry_crossvideo');V5S=V5/'scripts'
DXY=Path('/home/liu/new-polyp-dxy');GROUPS=['GP_Ip_12.0mm_closed_R10_single_refY','GP_Ip_20.0mm_closed_R10_single_refY','GP_IIa_14.0mm_closed_R10_single_refY','GP_Ip_8.8mm_closed_R5_single_refY','GP_Is_14.0mm_closed_R5_single_refY']
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,x):p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=1,default=str)+'\n')
def ring_r(g):return 3.1 if '_R5_' in g else 5.6

def prep_input(g,v):
 root=INP/'prepared'/f'{g}_{v}';m=json.loads((root/'PREPARED.json').read_text());run=BASE/'v6'/f'{g}_{v}'
 for d in ['inputs','observations','predictions','metrics','raw','meshes','scenes','visualizations']:(run/d).mkdir(parents=True,exist_ok=True)
 ((run/'scripts').unlink() if (run/'scripts').is_symlink() or (run/'scripts').exists() else None);(run/'scripts').symlink_to(V6S, target_is_directory=True)
 (run/'v5raw').mkdir(parents=True,exist_ok=True)
 ((run/'v5raw'/'scripts').unlink() if (run/'v5raw'/'scripts').is_symlink() or (run/'v5raw'/'scripts').exists() else None);(run/'v5raw'/'scripts').symlink_to(V5S, target_is_directory=True)
 rows=[];clean=INP/'clean_labels'/f'{g}_{v}'
 for i,q in enumerate(m['views']):
  z=np.load(q['cache']); rgbp=run/'inputs'/f'{q["view"]}.png';maskp=run/'inputs'/f'{q["view"]}_mask.png'
  cv2.imwrite(str(rgbp),z['RGB'][:,:,::-1]);cv2.imwrite(str(maskp),z['labels'])
  rows.append(dict(id=q['view'],source=Path(m['video_path']).name,source_id=v,raw_frame=int(q['raw_frame']),source_raw_frame=int(q['raw_frame']),RGB_path=str(rgbp),Mask_path=str(maskp),RGB_SHA256=h(rgbp),Mask_SHA256=h(maskp),original16=False,role='M2F8 current M2F6 input'))
 # reference/held alias only for unmodified V6 protocol; preserve source_raw_frame
 ref=len(rows)//2; held=len(rows)-1
 if held==ref:held=max(0,ref-1)
 alias=[dict(r) for r in rows];
 alias[ref]['raw_frame']=459;alias[held]['raw_frame']=516
 write(run/'inputs/ledger005.json',alias);write(run/'inputs/ledger_actual.json',rows)
 write(run/'inputs/REFERENCE_RECEIPT.json',dict(reference_row=rows[ref],heldout_row=rows[held],alias_459=rows[ref]['source_raw_frame'],alias_516=rows[held]['source_raw_frame'],reason='V6 fixed protocol IDs mapped to current selected frames; source IDs preserved'))
 write(run/'config.json',json.loads((V6/'config.json').read_text()))
 return run,rows,alias,ref,held

def source_modules(ring_R):
 sys.path[:0]=[str(V6S),str(V5S),str(DXY/'src')]
 import g5_common,g5_common as g5
 # parameterize the one authoritative V5/V6 Ring formula; no second formula
 orig=g5.contour_project
 def cp(pose,n=256,K0=None):
  if K0 is None:K0=g5.K
  return g5.contours(pose[:3,3],pose[:3,:3],K0,R=ring_R,r=.6,n=n)
 g5.contour_project=cp
 import v6_common
 v6_common.ring_residual=g5.torus_residual;v6_common.contours=cp
 import ring_candidates_new,local_ring_sfm,track005
 local_ring_sfm.ring_residual=g5.torus_residual;local_ring_sfm.contours=cp
 return dict(g5=g5,v6=v6_common,ns=ring_candidates_new.ns,lba=local_ring_sfm,track=track005)

def build_ring(run,rows,ring_R,mods):
 # V5 DXY observations on current raw labels, then the existing V5 seed/solve path with R5/R10 parameter
 v5root=run/'v5raw';v5root.mkdir(parents=True,exist_ok=True);(v5root/'inputs').mkdir(exist_ok=True);(v5root/'metrics').mkdir(exist_ok=True);(v5root/'observations').mkdir(exist_ok=True);(v5root/'predictions').mkdir(exist_ok=True)
 write(v5root/'inputs/ledger.json',rows);write(v5root/'config.json',json.loads((V5/'config.json').read_text()))
 files={str(v5root/'config.json'):h(v5root/'config.json'),str(v5root/'inputs/ledger.json'):h(v5root/'inputs/ledger.json')};write(v5root/'metrics/freeze_inputs.json',dict(files=files,GT_selection=False,historical_measurement_fallback=0))
 import g5_common,ring_observations
 g5_common.R=v5root;ring_observations.R=v5root;ring_observations.verify=lambda *x: None
 ring_observations.main()
 import ring_candidates_new
 ns=ring_candidates_new.ns;ns['rad']=ring_R;ns['tube']=.6
 obs={a['id']:dict(np.load(v5root/'observations'/f'{a["id"]}.npz')) for a in rows}
 st={a['source']:a for a in json.loads((v5root/'metrics/ring_observations.json').read_text())} if (v5root/'metrics/ring_observations.json').exists() else {}
 K=np.asarray(json.loads((V5/'config.json').read_text())['K'],float);records=[]
 for a in rows:
  ob=obs[a['id']];ob['mask']=ob['ring_mask'];ns.update(K=K,cfg=dict(seed_depth_factors=[.85,1.,1.2],seed_inclinations_deg=[0,35,60],seed_azimuths_deg=[0,90,180,270],seed_retain=4,max_nfev=100,huber_px=1.,numerical_success_max_training_px=3.))
  def residual(x,ref,observations):
   cen,Q=ns['decode'](x,ref);po=np.eye(4);po[:3,:3]=Q.T;po[:3,3]=-Q.T@cen;return g5_common.torus_residual(po,ob,K0=K)
  ns['residual']=residual;seeds=ns['image_seeds'](ob);e=st.get(a['source_id'],{}).get('geometry',{}).get('centerline') if st else None
  if e:
   z=ring_R*K[0,0]/e['major_radius'];xy=(np.array([e['cx'],e['cy']])-K[:2,2])/np.diag(K)[:2];inc=np.arccos(np.clip(e['minor_radius']/e['major_radius'],0,1));az=np.deg2rad(e['angle_deg'])
   for sign in [-1,1]:seeds.append(np.r_[xy,np.log(z),sign*inc*np.cos(az),sign*inc*np.sin(az)])
  seeds=ns.get('diverse_four',lambda s,f:s)(seeds,lambda x:float(np.mean(2*(np.sqrt(1+residual(x,np.eye(4),[ob])**2)-1)))) if 'diverse_four' in ns else seeds
  fit=ns['solve']([ob],np.eye(4),seeds);allfit=[{k:v for k,v in fit.items() if k not in ['alternatives','ambiguity_alternatives']}]+fit['alternatives'];cands=[]
  for x in allfit:
   Q=np.array(x['Q']);c=np.array(x['center']);po=np.eye(4);po[:3,:3]=Q.T;po[:3,3]=-Q.T@c;cands.append(dict(**x,c2r=po.tolist(),heldout=g5_common.stats(g5_common.torus_residual(po,ob,'held')),azimuth_gauge='arbitrary representative'))
  records.append(dict(id=a['id'],source_id=a['source_id'],K=K,candidates=cands,rotation_symmetry_unresolved=True,no_gt_inputs=True))
 write(run/'predictions/ring_candidates005.json',records)
 # V6 observations aliases
 for a in rows:
  src=v5root/'observations'/f'{a["id"]}.npz';np.savez_compressed(run/'observations'/f'{a["id"]}_ring.npz',**dict(np.load(src)))
 write(run/'metrics/segmentation_ring005.json',[dict(id=a['id'],Ring_pixels=int((cv2.imread(a['Mask_path'],0)==2).sum())) for a in rows])
 v6=mods['v6'];v6.R=run;v6.V5=v5root;v6.REPO=Path('/home/liu/polyp_research');v6.freeze('ring_inputs',[run/'inputs/ledger005.json',run/'predictions/ring_candidates005.json']+list((run/'observations').glob('*_ring.npz')))
 return records

def run_v6(run,rows,mods,ring_R):
 # V6 track/BA/validate/support, root-local and alias ledger
 for name,mod in [('track005',mods['track']),('local_ring_sfm',mods['lba'])]:
  mod.R=run;mod.V5=run/'v5raw';mod.REPO=Path('/home/liu/polyp_research')
 mods['v6'].R=run
 mods['track'].main()
 try:
  mods['v6'].R=run;mods['lba'].main()
 except Exception as e:
  write(run/'metrics/FAIL_local_ring_sfm.json',dict(error=repr(e),traceback=traceback.format_exc()))
 import runpy
 try:
  sys.path.insert(0,str(V6S));import validate_select
  validate_select.R=run;validate_select.V5=run/'v5raw';validate_select.contours=mods['v6'].contours;validate_select.main()
 except Exception as e:write(run/'metrics/FAIL_validate.json',dict(error=repr(e),traceback=traceback.format_exc()))
 try:
  mods['v6'].R=run;runpy.run_path(str(V6S/'select_supported_views.py'))
 except Exception as e:write(run/'metrics/FAIL_support.json',dict(error=repr(e),traceback=traceback.format_exc()));print('SUPPORT_FAIL',run.name,e,flush=True)
 # HERO entrypoints; unsupported cases may still run, supported only if support file exists
 sys.path.insert(0,str(V6S));import run_mvs005,run_mvs005_supported,package_surfaces
 for m in [run_mvs005,run_mvs005_supported,package_surfaces]:m.R=run;m.V5=run/'v5raw';m.REPO=Path('/home/liu/polyp_research')
 try:
  if (run/'inputs/MVS_cases.json').exists():run_mvs005.main()
 except Exception as e:write(run/'metrics/FAIL_run_mvs005.json',dict(error=repr(e),traceback=traceback.format_exc()));print('HERO_FAIL',run.name,'unsupported',e,flush=True)
 try:
  if (run/'inputs/MVS_supported_cases.json').exists():run_mvs005_supported.main()
 except Exception as e:write(run/'metrics/FAIL_run_mvs005_supported.json',dict(error=repr(e),traceback=traceback.format_exc()));print('HERO_FAIL',run.name,'supported',e,flush=True)
 try:
  if (run/'inputs/MVS_supported_cases.json').exists():package_surfaces.main()
 except Exception as e:write(run/'metrics/FAIL_package.json',dict(error=repr(e),traceback=traceback.format_exc()));print('MESH_FAIL',run.name,e,flush=True)

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--groups',default=','.join(GROUPS));ap.add_argument('--videos',default='004,005');ap.add_argument('--limit',type=int,default=0);a=ap.parse_args();gs=[x for x in a.groups.split(',') if x];vs={x.zfill(3) for x in a.videos.split(',') if x};n=0
 for g in gs:
  for p in sorted((INP/'prepared').glob(f'{g}_*')):
   v=p.name.rsplit('_',1)[1]
   if v not in vs:continue
   run,rows,alias,ref,held=prep_input(g,v);mods=source_modules(ring_r(g));build_ring(run,rows,ring_r(g),mods);run_v6(run,rows,mods,ring_r(g));print('V6_DONE',g,v,run,flush=True);n+=1
   if a.limit and n>=a.limit:break
  if a.limit and n>=a.limit:break
 print('DONE',n)
if __name__=='__main__':main()
