"""Enumerate immutable original supports; freeze expanded budget before any new HERO."""
import csv,time,collections
from common import *
registry=read(P12/'evidence/INPUT_REGISTRY.json');frozen=B/'PLANS_FROZEN.json';assert not frozen.exists(),'Do not overwrite frozen plans'
base=read(B12/'BASELINE_FROZEN.json');assert all(sha(x['path'])==x['sha256']for x in base['files'])
plans=[];counts=[]
for r in registry:
 R=B12/'H004_RAW_BASELINE'/r['case'];cp=R/'registration/CAMERAS.json';sp=R/'selection/SUPPORTS.json';cameras={x['id']:x for x in read(cp)}if cp.exists()else{};supports=read(sp)if sp.exists()else[];n=0
 for support in supports:
  if support['support_N']!=3 or len(support['selected'])!=3:continue
  target=cameras[support['target']];selected=[cameras[x['id']]for x in support['selected']]
  assert target['HERO_target_eligible']and all(v['formal']for v in selected)
  plan=dict(group=r['group'],id=target['id'],view_id=target['id'],variant='GEOMETRIC3',target=target,support_views=selected)
  row=dict(case=r['case'],route='H004_RAW_BASELINE',plan=plan,ring_inner_mm=r['ring_inner_mm'],raw_sha256=r['raw_sha256'],source_cameras=str(cp),cameras_sha256=sha(cp),source_supports=str(sp),supports_sha256=sha(sp),target_qualified=True,support_qualified=[True]*3)
  fs=oldhero.frames(row);identity=frame_identity(fs,r['raw_sha256']);key=combo_id(identity);row.update(input_identity=identity,combo_id=key,source_id='H004_'+r['case']+'_'+target['id'],output=str(B/'H004'/r['case']/target['id']))
  prior=B12/'HERO_LIMITED/H004_RAW_BASELINE'/r['case'];reuse=False
  if(prior/'INPUT_FROZEN.json').exists():
   prev=read(prior/'INPUT_FROZEN.json')['frames'];want=[{k:v for k,v in x.items()if k!='raw_video_sha256'}for x in identity]
   if prev==want:
    assert (prior/'INFERENCE.json').exists()and sha(prior/'HERO_native.npz')==read(prior/'PREDICTION_SHA256.json')['sha256'];reuse=True
  row.update(action='REUSE'if reuse else'NEW',reuse_output=str(prior)if reuse else None);plans.append(row);n+=1
 counts.append(dict(case=r['case'],legal_targets=n))
assert len(set(x['combo_id']for x in plans))==len(plans)
protocol=dict(epoch=time.time(),groups=5,videos=10,legal_targets=len(plans),reuse=sum(p['action']=='REUSE'for p in plans),new_inference_budget=sum(p['action']=='NEW'for p in plans),per_target_original_tuple_count=1,resource_retries='None scheduled; any future retry requires explicit resource error receipt and identical frozen input, never a new combination',camera_refit=False,selection_uses_depth=False,M2F12_protocol_unchanged=True,baseline_sha256=sha(B12/'BASELINE_FROZEN.json'),model_sha256=MODEL_SHA,source_code_sha256=sha(__file__),official_infer_sha256=sha(CORE/'src/ring_first_hero/hero.py'),original_mesh_converter_sha256=sha(CORE/'src/ring_first_hero/geometry.py'),per_video=counts)
assert protocol['legal_targets']==76 and protocol['reuse']==7 and protocol['new_inference_budget']==69,protocol
save(frozen,dict(protocol=protocol,plans=plans));save(T/'evidence/HERO_BUDGET_FROZEN.json',protocol);print(protocol)
