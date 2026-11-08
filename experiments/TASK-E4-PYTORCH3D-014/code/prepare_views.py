"""Fixed raw candidate pool; exact sequential decoding and audited frozen segmentation."""
from common import *
import subprocess, traceback, gc

def main():
 os.environ.update(HF_HOME=str(R/'runtime/hf'),HF_MODULES_CACHE=str(R/'runtime/hf_modules'),HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
 dxy=Path('/home/liu/new-polyp-dxy');base=Path('/home/liu/polyp_research/ring_anchor_3d/experiments')
 sys.path[:0]=[str(dxy/'src'),str(base/'surface_benchmark_v1/vendor/dependencies'),str(base/'ring_first_v8_registration_narrow_baseline/vendor/dependencies')]
 from dxy_mid.segmentation import INITSegmentation
 import torch
 torch.set_num_threads(3)
 weights=Path('/home/liu/polyp_research/experiments/v8_5_cross_ring_pipeline_audit_20261014/freeze/model')
 model=INITSegmentation(weights,'cuda');existing=load(R/'config/EXISTING_VIEWS.json');assets=load(R/'config/RAW_ASSETS.json');rows=[];identity=[];errors=[]
 save('provenance/SEGMENTATION_SOURCE.json',dict(code=asset(dxy/'src/dxy_mid/segmentation.py'),weights=asset(weights/'model.safetensors'),policy='read-only original INIT weights; no model update'))
 for a in assets:
  if a['type']!='video':continue
  sid=a['sid'];out=R/'new_views'/sid
  for x in ['inputs','observations','predictions','metrics','scripts']:(out/x).mkdir(parents=True,exist_ok=True)
  done=out/'inputs/ledger_all.json'
  if done.exists():rows+=load(done);print('REUSE_PREPARED',sid,flush=True);continue
  try:
   path=a['source'];ptsj=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','frame=best_effort_timestamp_time','-of','json',path],text=True));pts=[float(x['best_effort_timestamp_time'])for x in ptsj['frames']];count=len(pts)
   temporal=np.rint(np.linspace(.1*(count-1),.9*(count-1),40)).astype(int);claim={}
   for v in existing:
    if v['sid']!=sid or v['raw_frame']is None:continue
    raw=int(v['raw_frame'])
    if 0<=raw<count:claim.setdefault(raw,[]).append(v)
   sample=sorted(set(temporal.tolist())|set(claim));cap=cv2.VideoCapture(path);L=[];hashes={v['RGB_content_sha']:v for v in existing if v['sid']==sid}
   timeline=out/'inputs/RAW_FRAME_TIMELINE.csv'
   with timeline.open('w',newline='')as fh:
    w=csv.writer(fh);w.writerow(['source_video_SHA256','raw_frame_zero_based','time_sec','candidate','RGB_content_SHA256'])
    for raw in range(count):
     ok,bgr=cap.read()
     if not ok:raise RuntimeError('sequential decode failed at '+str(raw))
     im=None;content_sha=None
     if raw in sample:
      im=cv2.resize(bgr,(640,360),interpolation=cv2.INTER_AREA);content_sha=hashlib.sha256(np.ascontiguousarray(im[:,:,::-1]).tobytes()).hexdigest()
     w.writerow([a['sha256'],raw,pts[raw],raw in sample,content_sha])
     if im is None:continue
     cid=sid+f'_raw{raw:05d}';rgb=out/f'inputs/{cid}.png';mask=out/f'observations/{cid}_labels.png';cv2.imwrite(str(rgb),im)
     aliases=[]
     for v in claim.get(raw,[]):
      archived=np.array(Image.open(v['RGB_source']).convert('RGB'));diff=np.abs(im[:,:,::-1].astype(float)-archived.astype(float));eq=content_sha==v['RGB_content_sha'];identity.append(dict(case=a['case'],sid=sid,id=v['id'],claimed_raw=raw,exact_pixels=eq,mean_abs_RGB_difference=float(diff.mean()),p95_abs_difference=float(np.quantile(diff,.95)),archived_source=v['RGB_source'],raw_RGB=str(rgb)))
      if eq:aliases.append(v['id'])
     exact=hashes.get(content_sha)
     if exact:aliases=list(set(aliases+[exact['id']]))
     labels=model.predict(rgb);assert labels.shape==(360,640);cv2.imwrite(str(mask),labels)
     slot=int(np.where(temporal==raw)[0][0])if raw in temporal else None
     rec=dict(id=cid,case=a['case'],sid=sid,video=a['video'],raw_frame=raw,key=slot,time_sec=pts[raw],source_video=path,source_video_SHA256=a['sha256'],RGB_path=str(rgb),RGB_source=str(rgb),RGB_SHA256=sha(rgb),RGB_content_sha=content_sha,Mask_path=str(mask),Mask_source=str(mask),Mask_SHA256=sha(mask),source_id=sid,camera_status='PENDING_REAL_RGB_GEOMETRY',frame_binding='EXACT_SEQUENTIAL_ZERO_BASED_AREA_NO_JPEG',native_resolution=[a['width'],a['height']],working_resolution=[640,360],role='UPDATE_HOLDOUT'if slot in [8,24]else'FIT',temporal_slot=slot,exact_existing_aliases=aliases,segmentation_success=True,Polyp_pixels=int((labels==1).sum()),Ring_pixels=int((labels==2).sum()))
     L.append(rec);print('SEG',sid,raw,len(L),len(sample),rec['Polyp_pixels'],rec['Ring_pixels'],flush=True)
   cap.release();assert len(L)==len(sample)
   save(done.relative_to(R),L);rows+=L
  except Exception:errors.append(dict(sid=sid,failure=traceback.format_exc()));print(errors[-1],flush=True)
  save('config/NEW_RAW_VIEWS.json',rows);table('metrics/RAW_IDENTITY_CHECKS.csv',identity);save('metrics/RAW_IDENTITY_CHECKS.json',identity);save('metrics/PREPARATION_FAILURES.json',errors)
 save('provenance/PREPARED_VIEWS_FREEZE.json',dict(epoch=time.time(),code=asset(Path(__file__)),ledger=asset(R/'config/NEW_RAW_VIEWS.json'),count=len(rows),failures=errors,GT_access=False));print('PREPARE_DONE',len(rows),flush=True)
if __name__=='__main__':main()
