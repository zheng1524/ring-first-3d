"""Freeze existing registry/R0 identities and bounded pilot configs; no inference."""
import json,shutil,time,hashlib
from pathlib import Path
from PIL import Image
from ring_first_3d.v6_raw.full_run import read,atomic_json,hash_file,table
W=Path('/home/liu/ring_first_3d_workspace');WT=Path(__file__).resolve().parents[1];TASK='TASK-V6-FRONTEND-RECOVERY-AND-PHOTO-PILOT-001';T=WT/'experiments'/TASK;O=W/'runs/v6_frontend_photo_pilot_001';B=W/'runs/v6_full_run_001'
GROUPS=['GP_Is_18.0mm_closed_R5_single_refY','GP_IIa_4.5mm_closed_R10_single_refY','GP_IIa_9.5mm_closed_R10_single_refY','GP_Is_7.0mm_closed_R5_single_refY','GP_Ip_20.0mm_closed_R10_single_refY','GP_Ip_8.8mm_closed_R5_single_refY']
def main():
 for p in [T/'config',T/'evidence',O]:p.mkdir(parents=True,exist_ok=True)
 snap=read(B/'SNAPSHOT.json');source=Path(read(snap['config'])['manifest']);allm=read(source);assert len(allm['videos'])==79 and len(allm['static_photos'])==120
 allm.update(task=TASK,baseline_manifest=str(source),baseline_manifest_sha256=hash_file(source));atomic_json(T/'evidence/ALL79_120_MANIFEST.json',allm)
 m=dict(allm,groups=GROUPS,videos=[v for v in allm['videos'] if v['group'] in GROUPS],static_photos=[p for p in allm['static_photos'] if Path(p['path']).stem.rsplit('_',1)[0] in GROUPS]);assert len(m['videos'])==12
 atomic_json(T/'evidence/PILOT_MANIFEST.json',m);rows=[];total=0;original_targets=0;pervideo=[]
 for v in m['videos']:
  state=read(B/'states'/(v['case']+'.json'));R=Path(state['run_path']);meta=read(R/'inputs/INPUT_IDENTITY.json');n=len(meta['frames'])-1;original_targets+=n
  files=[R/'inputs/INPUT_IDENTITY.json',R/'RUN_STATE.json']+[R/f for f in ['CAMERA_COMPLETE.json','CAMERA_FAILURE.json','PLAN_FROZEN.json','HERO_COMPLETE.json'] if (R/f).exists()]
  rec=dict(case=v['case'],state=state,original_target_count=n,files={str(p):hash_file(p) for p in files},outputs=[])
  if (R/'HERO_COMPLETE.json').exists():
   for p,h in read(R/'HERO_COMPLETE.json')['outputs'].items():
    assert hash_file(p)==h;rec['outputs'].append(dict(path=p,sha256=h,bytes=Path(p).stat().st_size))
  total+=state.get('renderable',0);rows.append(rec)
  pervideo.append(sum(p.stat().st_size for d in ['raw','meshes','predictions','observations','v5raw'] for p in (R/d).rglob('*') if p.is_file()))
 assert total==105
 atomic_json(T/'evidence/R0_IDENTITIES.json',dict(baseline_execution=snap['execution_commit'],videos=rows,source_count=total,original_target_denominator=original_targets))
 photos=[]
 for p in allm['static_photos']:
  assert hash_file(p['path'])==p['sha256']
  with Image.open(p['path']) as im:shape=list(im.size);exif=im.getexif();orientation=exif.get(274,1)
  photos.append(dict(p,group=Path(p['path']).stem.rsplit('_',1)[0],dimensions=shape,exif_present=bool(exif),orientation=orientation,intrinsics_basis='USER_CONFIRMED_SAME_OPTICS_ZOOM_CROP_DISTORTION_AS_VIDEO',independent_calibration=False))
 table(T/'evidence/PHOTO_INVENTORY.csv',photos)
 common=dict(task=TASK,manifest=str(T/'evidence/PILOT_MANIFEST.json'),minimum_free_bytes=1073741824,reuse_old_results=False)
 front=dict(baseline_root=str(B),photo_cache=str(O/'photo_prepared'),photo_intrinsics_basis='USER_CONFIRMED_SAME_OPTICS_ZOOM_CROP_DISTORTION_AS_VIDEO',policy='real_ring_boundary-original_anchor_component-zero_plan_only_fallback-v1')
 for variant in ['R1','R2']:
  atomic_json(T/'config'/(variant+'.json'),dict(common,run_root=str(O/variant),frontend=dict(front,include_photos=variant=='R2')))
 full=dict(common,manifest=str(T/'evidence/ALL79_120_MANIFEST.json'),run_root=str(W/'runs/v6_frontend_full_PENDING_APPROVAL'),frontend=dict(front,include_photos=True),approval_required=True)
 atomic_json(T/'config/FULL_PENDING_APPROVAL.json',full)
 disk=shutil.disk_usage(O);worst=2*original_targets+sum(sum(Path(p['path']).stem.rsplit('_',1)[0]==v['group'] for p in m['static_photos']) for v in m['videos'])
 atomic_json(T/'evidence/SPACE_PREFLIGHT.json',dict(epoch=time.time(),mount='/',total=disk.total,used=disk.used,free=disk.free,original_targets_per_variant=original_targets,photos=len(m['static_photos']),maximum_new_tuples=worst,baseline_source_count=105,baseline_selected_unit_bytes=pervideo,max_observed_unit_bytes=max(pervideo),estimated_raw_retained_bytes=worst*3600000,estimated_clean_retained_bytes=worst*2500000,transient_per_video_bytes=170000000,reserve_bytes=1073741824,policy='No old asset copies; exact plans freeze before inference. Stage disk guard >=1 GiB. Clean keep FACE_EVIDENCE + Trusted only, redundant exports removed with receipt. Max-budget estimate may exceed available disk; pause rather than delete protected assets. Actual legal budgets expected lower but never assumed passed.',full_run_space_required_bytes=79*24*6100000+1073741824))
 print(json.dumps(dict(videos=len(m['videos']),photos=len(m['static_photos']),baseline_sources=total,max_new_tuples=worst,free_bytes=disk.free)))
if __name__=='__main__':main()
