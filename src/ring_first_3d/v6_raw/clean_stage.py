"""Shared pilot/full-run orchestration for unchanged 017+gap / TRUSTED-only clean."""
from pathlib import Path
import shutil
import numpy as np
from .full_run import read,atomic_json,hash_file
WT=Path(__file__).resolve().parents[3]

def clean_source(source,case,R,dest,variant='R1'):
 from .surface_clean import mapped_input_for_source
 from . import route
 for p,h in (route.FULL_CONFIG or {}).get('cad_sha256',{}).items():assert hash_file(p)==h,'FROZEN_CAD_DRIFT'
 from .trusted_restore import trusted_subset
 from ..mainline.native.cleaning import classify_native
 tag=source['tag'];R=Path(R);dest=Path(dest);dest.parent.mkdir(parents=True,exist_ok=True);receipt=dest/'COMPLETE.json'
 fixed={'cleaning.py':'a5fd471ad85767399c9013d3668863eb4a2950fcdf712267dd154a128db2e4e7','_clean_kernels.py':'e81b6166a7236616ea03a277d597c966c49da2233fc46d72afa2c19ba405d08a','cleaning_protocol.json':'99c00fe52effa2589c21ad93c2f06a3b1c4d9c86c4c0c37b9bf5a2db33495b56'}
 for name,h in fixed.items():assert hash_file(WT/'src/ring_first_3d/mainline/native'/name)==h,'CLEAN_KERNEL_DRIFT'
 paths=[R/'raw'/(tag+'.npz'),R/'meshes'/(tag+'_Polyp.ply'),R/'PLAN_FROZEN.json',R/'CAMERA_COMPLETE.json',R/'inputs/INPUT_IDENTITY.json',R/'inputs/ledger005.json']
 paths += [Path(a[k]) for a in read(R/'inputs/ledger005.json') for k in ['RGB_path','Mask_path']]
 paths += [Path('/home/liu/ring_first_3d_workspace/runs/m2f5_unified/cad')/('R5.npz' if '_R5_' in case else 'R10.npz'),Path(__file__).with_name('surface_clean.py')]
 parents={str(p):hash_file(p) for p in paths};parents.update(fixed)
 if receipt.exists():
  row=read(receipt)
  if 'parents' in row:assert row['parents']==parents,'CLEAN_PARENT_DRIFT'
  else:
   assert row['raw_mesh_sha256']==source['mesh_sha256'] and row['native_sha256']==hash_file(R/'raw'/(tag+'.npz')),'LEGACY_CLEAN_PARENT_DRIFT'
   assert row['classifier_sha256']==fixed['cleaning.py'] and row['kernel_sha256']==fixed['_clean_kernels.py'],'LEGACY_CLEAN_KERNEL_DRIFT'
  for p,h in row['retained_hashes'].items():assert hash_file(p)==h,'CLEAN_OUTPUT_DRIFT'
  return row
 if shutil.disk_usage(dest.parent).free<1073741824:raise RuntimeError('CLEAN_LOW_DISK_PAUSE')
 dest.mkdir(parents=True,exist_ok=True);c=dict(source,case=case,run=str(R),native_sha256=hash_file(R/'raw'/(tag+'.npz')))
 info=mapped_input_for_source(c);rec=classify_native(dest,info['cadpath'],mapped_input=info['payload']);e=dict(np.load(dest/'FACE_EVIDENCE.npz'));state=e['state'];sub=trusted_subset(info['V'],info['F'],state)
 assert np.array_equal(e['F'],info['F']) and np.array_equal(e['V'],info['V']) and np.array_equal(sub['F'],info['F'][state==0])
 removed=[]
 for name in ['Conservative_cleaned_mesh','Uncertain','Rejected','Unknown']:
  p=dest/(name+'.ply')
  if p.exists():removed.append(dict(path=str(p),bytes=p.stat().st_size,sha256=hash_file(p),reason='redundant export; exact faces/states/V/F retained in FACE_EVIDENCE'));p.unlink()
 row=dict(case=case,variant=variant,tag=tag,target=source['raw_target'],target_media_type=source['target_media_type'],target_view_id=source['target_view_id'],raw_mesh_sha256=c['mesh_sha256'],native_sha256=c['native_sha256'],raw_faces=len(info['F']),trusted_faces=len(sub['F']),raw_area_mm2=float(e['area_mm2'].sum()),states=[dict(code=i,faces=int((state==i).sum()),area_mm2=float(e['area_mm2'][state==i].sum())) for i in range(4)],protocol=rec,source_execution=read(R/'HERO_COMPLETE.json')['execution_commit'],classifier_sha256=hash_file(WT/'src/ring_first_3d/mainline/native/cleaning.py'),kernel_sha256=hash_file(WT/'src/ring_first_3d/mainline/native/_clean_kernels.py'),filter='F[state==0]',removed_regenerable_exports=removed,retained_hashes={str(p):hash_file(p) for p in dest.iterdir() if p.is_file()})
 row['parents']=parents;atomic_json(receipt,row);print('CLEAN',variant,case,tag,len(sub['F']),flush=True);return row
