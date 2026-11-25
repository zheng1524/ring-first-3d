"""Read all M2F10 fixed-video generated surfaces; retain formal membership and aliases."""
import collections,time,traceback
from common import *
registry=read(P12/'evidence/INPUT_REGISTRY.json');bycase={x['case']:x for x in registry};root=W/'runs/m2f10_v6_multiview';finaldir=Path('/home/liu/.config/superpowers/worktrees/ring_first_3d_workspace/TASK-M2F10/experiments/TASK-M2F10-V6-MULTIVIEW-HERO-EXPANSION-001/evidence/final')
finals={r['case']:read(finaldir/('VIDEO_RESULT_'+r['case']+'.json'))['attempts'][-1]for r in registry};rows=[];failures=[];roots=[]
for state in sorted(root.rglob('RUN_STATE.json')):
 if any(p.startswith('M2F11')for p in state.parts):continue
 R=state.parent
 if R.name in bycase and(R/'inputs/ledger005.json').exists():roots.append(R)
for R in roots:
 r=bycase[R.name];L=read(R/'inputs/ledger005.json');state=read(R/'RUN_STATE.json');cases={};runs={}
 for name in ['MVS_cases.json','MVS_supported_cases.json']:
  if(R/'inputs'/name).exists():cases.update({c['tag']:c for c in read(R/'inputs'/name)})
 for name in ['MVS005_runs.json','MVS005_supported_runs.json']:
  if(R/'metrics'/name).exists():runs.update({c['tag']:c for c in read(R/'metrics'/name)})
 if (R/'metrics/local_validation.json').exists():
  val=read(R/'metrics/local_validation.json');vr=next(x for x in val['versions']if x['version']==val['primary'])['per_frame']
 else:
  vr=[dict(status='NOT_EVALUABLE')for _ in L];failures.append(dict(case=R.name,root=str(R),reason='INCOMPLETE_ATTEMPT_NO_VALIDATION',generated_surface=False))
 for raw in sorted((R/'raw').glob('*.npz')):
  tag=raw.stem;c=cases.get(tag)
  if not c:failures.append(dict(case=R.name,raw=str(raw),reason='NO_FROZEN_CASE_BINDING'));continue
  row=dict(case=R.name,route='V6',ring_inner_mm=r['ring_inner_mm'],raw_sha256=r['raw_sha256'],plan=c,v6_root=str(R),source_plan=str(R/'inputs'/('MVS_supported_cases.json'if tag.startswith('005_supported')else'MVS_cases.json')),native_path=str(raw),native_sha256=sha(raw),mesh_path=str(R/'meshes'/(tag+'_Polyp.ply')),source_id='V6_'+R.name+'_'+tag+'_'+sha(R/'RUN_STATE.json')[:8],run_state=str(R/'RUN_STATE.json'),run_state_sha256=sha(R/'RUN_STATE.json'),execution_code_commit=state.get('code_commit',state.get('git_commit','SEE_RUN_STATE')),target_qualified=vr[c['reference']]['status']=='VALIDATED',support_qualified=[vr[i]['status']=='VALIDATED'for i in c['sources']],model_receipt=runs.get(tag,{}).get('model_info',{}),original_tag=tag,action='EXISTING')
  row['formal']=str(R)==finals[R.name]['run_path'] and c['reference_id']in finals[R.name]['accepted_target_ids']and tag.startswith('005_supported')and Path(row['mesh_path']).exists()
  try:
   fs=oldhero.frames(row);z=np.load(raw);ids=[int(z['reference'])]+list(map(int,z['sources']));assert ids==[c['reference']]+c['sources']
   assert all(np.array_equal(f['c2w_mm'],z['c2w'][i])for f,i in zip(fs,ids));assert np.allclose(fs[0]['K'],z['K_full'])
   identity=frame_identity(fs,r['raw_sha256']);row.update(input_identity=identity,combo_id=combo_id(identity),status='EXISTING_NUMERIC',mesh_sha256=sha(row['mesh_path'])if Path(row['mesh_path']).exists()else None)
  except Exception as ex:row.update(status='INPUT_BINDING_FAILED',failure=repr(ex),combo_id=None);failures.append(dict(source_id=row['source_id'],reason=repr(ex)))
  rows.append(row)
 # Failed/not-run combinations remain visible separately; not generated surfaces.
 for tag,run in runs.items():
  if not run.get('success')and not(R/'raw'/(tag+'.npz')).exists():failures.append(dict(case=R.name,root=str(R),tag=tag,reason=run.get('failure','NOT_GENERATED'),generated_surface=False))
# M2F12's five native limited diagnostics are preserved as additional representations/aliases.
for old in read(B12/'HERO_PLANS_FROZEN.json')['plans']:
 if old['route']!='V6_LIMITED_DIAGNOSTIC'or old['status']!='READY':continue
 r=bycase[old['case']];fs=oldhero.frames(old);identity=frame_identity(fs,r['raw_sha256']);O=B12/'HERO_LIMITED/V6_LIMITED_DIAGNOSTIC'/old['case']
 rows.append(dict(case=old['case'],route='V6',ring_inner_mm=r['ring_inner_mm'],raw_sha256=r['raw_sha256'],plan=old['plan'],v6_root=old['v6_root'],native_path=str(O/'HERO_native.npz'),native_sha256=sha(O/'HERO_native.npz'),mesh_path=str(O/'RAW_NATIVE_MESH.npz'),mesh_sha256=sha(O/'RAW_NATIVE_MESH.npz'),source_id='V6_M2F12_'+old['case'],formal=False,target_qualified=old['target_own_validated'],support_qualified=old['support_own_validated'],model_receipt=read(B12/'HERO_LIMITED/MODEL_RECEIPT.json'),input_identity=identity,combo_id=combo_id(identity),status='EXISTING_NUMERIC',action='EXISTING',original_tag='M2F12_LIMITED_NATIVE',representation='native_M2F12'))
# Exact full input keys only; all origin records retained, canonical output prefers formal source.
buckets=collections.defaultdict(list)
for row in rows:buckets[row['combo_id']or row['source_id']].append(row)
for same in buckets.values():
 canonical=sorted(same,key=lambda x:(not x['formal'],x['source_id']))[0]
 for row in same:row.update(canonical_source_id=canonical['source_id'],canonical=row is canonical,alias_count=len(same))
formal=[r for r in rows if r['formal']];assert len(formal)==66,len(formal)
assert len(set((r['case'],r['plan']['reference_id'])for r in formal))==66
save(B/'V6_SOURCES.json',rows);save(B/'V6_NOT_GENERATED_AND_BINDING_FAILURES.json',failures)
summary=dict(epoch=time.time(),scope='all existing M2F10 RUN_STATE roots for fixed ten videos, including smoke/earlier attempts; exclude M2F11 and retired M2F8/M2F9',roots=len(roots),generated_origin_records=len(rows),unique_input_combinations=sum(r['canonical']for r in rows),formal_sources=len(formal),binding_failures=sum(r['status']=='INPUT_BINDING_FAILED'for r in rows),canonical_missing_mesh=sum(r['canonical']and not Path(r['mesh_path']).exists()for r in rows),aliases=len(rows)-sum(r['canonical']for r in rows));save(T/'evidence/V6_SOURCE_COLLECTION.json',summary);print(summary)
