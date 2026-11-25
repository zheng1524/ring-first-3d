"""Expanded M2F13-only HERO budget; no camera refit, no support replacement."""
import time,traceback,inspect,subprocess
from common import *
import torch
from ring_first_hero.hero import load_official,infer
frozen=B/'PLANS_FROZEN.json';data=read(frozen);frozen_sha=sha(frozen);protocol=data['protocol'];plans=data['plans'];torch.set_num_threads(4);torch.manual_seed(20261115)
assert sha(CORE/'src/ring_first_hero/hero.py')==protocol['official_infer_sha256']and sha(CORE/'src/ring_first_hero/geometry.py')==protocol['original_mesh_converter_sha256']
# Reuse the complete existing evaluator; display-only adaptation exposes saturated tails.
source=inspect.getsource(oldhero.evaluate).replace("axs[0,2].set_title('Observed Ring |HERO - CAD| [mm]')","axs[0,2].set_title(f\"Ring error [mm]; >5 saturated\\nMAE {rm['MAE_mm']:.2f}, P95 {rm['p95_mm']:.2f}\")").replace('fraction=.04)','fraction=.04,extend="max")')
ns=dict(oldhero.__dict__);exec(compile(source,__file__+'::existing_evaluate_display_adapter','exec'),ns);evaluate=ns['evaluate']
head=subprocess.check_output(['git','-C',str(T.parents[1]),'rev-parse','HEAD']).decode().strip();model=None;results=[]
for row in plans:
 O=Path(row['output']);O.mkdir(parents=True,exist_ok=True);record={k:v for k,v in row.items()if k not in ['plan','input_identity']}
 try:
  assert sha(frozen)==frozen_sha and sha(row['source_cameras'])==row['cameras_sha256']and sha(row['source_supports'])==row['supports_sha256']
  fs=oldhero.frames(row);identity=frame_identity(fs,row['raw_sha256']);assert identity==row['input_identity']and combo_id(identity)==row['combo_id'];save(O/'INPUT_FROZEN.json',dict(combo_id=row['combo_id'],frames=identity,plans_sha256=frozen_sha))
  if row['action']=='REUSE':
   prior=Path(row['reuse_output']);assert read(prior/'INPUT_FROZEN.json')['frames']==[{k:v for k,v in x.items()if k!='raw_video_sha256'}for x in identity]
   assert sha(prior/'HERO_native.npz')==read(prior/'PREDICTION_SHA256.json')['sha256']
   for name in ['HERO_native.npz','RAW_NATIVE_MESH.npz','NATIVE_RGB_LABELS.npz','Raw_open_mesh.ply','INFERENCE.json']:
    p=O/name
    if not p.exists():p.symlink_to(prior/name)
    assert p.resolve()==(prior/name).resolve()
   save(O/'REUSE_RECEIPT.json',dict(original=str(prior),combo_id=row['combo_id'],original_depth_sha256=sha(prior/'HERO_native.npz'),new_inference=False))
  else:
   state=oldhero.inference_state(O)
   if state=='SPENT':raise RuntimeError('Prior attempt spent; no silent inference retry')
   if state=='NEW':
    starts=list((B/'H004').glob('*/*/INFERENCE_STARTED.json'));assert len(starts)<protocol['new_inference_budget']
    if model is None:model,receipt=load_official(rt['mvs_root'],rt['checkpoint'],rt['dino_root'],read(CORE/'provenance/upstream/SOURCE_COMPARISON.json'));save(B/'MODEL_RECEIPT.json',receipt)
    save(O/'INFERENCE_STARTED.json',dict(epoch=time.time(),combo_id=row['combo_id'],plans_sha256=frozen_sha,execution_git_commit=head,execution_code_sha256=sha(__file__),attempt=1,resource_retry=False));infer(model,fs,O)
  record['ring'],record['a_to_b']=evaluate(row,fs,O);record.update(status='COMPLETED',native_sha256=sha(O/'HERO_native.npz'),mesh_sha256=sha(O/'RAW_NATIVE_MESH.npz'))
 except Exception as ex:record.update(status='FAILED',error=repr(ex),traceback=traceback.format_exc());print(record['traceback'],flush=True)
 results.append(record);save(B/'H004_RESULTS.json',results);print('HERO_ALL',len(results),row['case'],row['plan']['id'],row['action'],record['status'],flush=True)
save(B/'HERO_RUN_RECEIPT.json',dict(execution_git_commit=head,runner_sha256=sha(__file__),original_evaluator_sha256=sha(P12/'code/hero_check.py'),display_only_adapter=True,new_inference_started=len(list((B/'H004').glob('*/*/INFERENCE_STARTED.json'))),budget=protocol['new_inference_budget'],completed=sum(x['status']=='COMPLETED'for x in results),failed=sum(x['status']=='FAILED'for x in results),no_camera_or_landmark_recompute=True))
