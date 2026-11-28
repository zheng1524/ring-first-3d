"""Audit-preserving metadata migration; never call it a new numeric DXY run.

Reuses verified complete numerical evidence. Non-unique or missing exact source
identities trigger a true single-frame rerun using object-identity observation.
"""
from dxy_full import *
import shutil

def geometry_signature(r):
 s=r['selected']
 return dict(selected=None if s is None else {k:s[k] for k in ['center_px','basis_px','shape','weight']},P_count=r['P_count'],Q_count=r['Q_count'],X_count=r['X_count'],source_id=r['source_id'],role=r['role'],official_audit=r['official_audit'])

def main():
 inp=read(T/'evidence/DXY_INPUT_INDEX.json');oldfreeze=read(T/'evidence/DXY_IMPLEMENTATION_FREEZE.json');oldsha=oldfreeze['code_sha256'];newsha=sha(T/'code/dxy_full.py')
 assert oldsha!=newsha
 assert read(T/'evidence/DXY_BATCH_RECEIPT.json')['complete']==1700
 oldsrc=T/'runtime/selection_fix_prior/dxy_full.py';assert sha(oldsrc)==oldsha
 out=T/'runs/dxy_selection_pre_fix';out.mkdir(parents=True,exist_ok=True)
 records=[];corrected=0;reruns=[]
 existing=T/'evidence/DXY_SELECTION_METADATA_MIGRATION.json'
 if existing.exists():
  prior=read(existing);assert prior['new_wrapper_sha256']==newsha and prior['complete']==1700
  print('Migration already complete');return
 for row in inp['rows']:
  folder=T/'runs/dxy'/row['case']/row['frame_id'];receipt=read(folder/'COMPLETE.json');r=read(folder/'FRAME.json')
  expected_old=hashlib.sha256(json.dumps([row,inp['source'],oldsha],sort_keys=True).encode()).hexdigest()
  expected_new=hashlib.sha256(json.dumps([row,inp['source'],newsha],sort_keys=True).encode()).hexdigest()
  assert receipt['key']==expected_old and r['cache_key']==expected_old
  for f in receipt['files']:assert sha(f['path'])==f['sha256']
  backup=out/row['case']/row['frame_id'];backup.mkdir(parents=True,exist_ok=True)
  for name in ['FRAME.json','PROCESS.json.gz','COMPLETE.json']:
   assert not(backup/name).exists();shutil.copy2(folder/name,backup/name)
  before_signature=geometry_signature(r);curve_before=asset(folder/'CURVES.npz');official_before=[asset(p) for p in sorted((folder/'official').glob('*')) if p.is_file()]
  with gzip.open(folder/'PROCESS.json.gz','rt') as f:process=json.load(f)
  selected=r['selected'];oldid=r['selected_record_id'];newid=oldid;equivalent=[];reran=False
  if selected is not None:
   previous=next(x for x in process['default_candidate_pool'] if x['selected'])
   try:
    chosen,equivalent=resolve_selected_record(process['default_candidate_pool'],selected,previous['body'],previous['shape'],previous.get('origin'))
   except ValueError:
    # No guessing from nearby geometry or duplicated records. Execute the real
    # official pipeline and capture its actual chosen record object.
    shutil.copy2(folder/'CURVES.npz',backup/'CURVES.npz');shutil.copytree(folder/'official',backup/'official')
    r=run_frame(row,inp['source']);reran=True;reruns.append(row['source_id'])
    assert geometry_signature(r)==before_signature,'Numerical prediction changed; cannot call this metadata-only migration'
    oldarrays=dict(np.load(backup/'CURVES.npz'));newarrays=dict(np.load(folder/'CURVES.npz'))
    assert oldarrays.keys()==newarrays.keys()
    for key in oldarrays:
     x,y=oldarrays[key],newarrays[key]
     assert np.array_equal(x,y,equal_nan=True) if np.issubdtype(x.dtype,np.number) else np.array_equal(x,y)
    shutil.copy2(backup/'CURVES.npz',folder/'CURVES.npz');r['arrays']=asset(folder/'CURVES.npz')
    # Preserve original NPZ bytes after proving every generated array equal.
    with gzip.open(folder/'PROCESS.json.gz','rt') as f:process=json.load(f)
    chosen=next(x for x in process['default_candidate_pool'] if x['selected']);equivalent=r.get('selected_record_equivalent_ids',[chosen['record_id']])
   newid=chosen['record_id']
   for candidate in process['default_candidate_pool']:candidate['selected']=candidate['record_id']==newid
   r['selected']['record_id']=newid;r['selected_record_id']=newid
   identity=dict(record_id=newid,equivalent_record_ids=equivalent,method='observed_actual_record_object' if reran else 'unique_exact_native_parameters_and_origin_from_verified_original_pool',absolute_tolerance_px=1e-10)
  else:identity=dict(record_id=None,equivalent_record_ids=[],method='no_selected_curve')
  if oldid!=newid:corrected+=1
  process['selection_identity']=identity
  r['selection_identity']=identity;r['selected_record_equivalent_ids']=identity['equivalent_record_ids']
  r['execution_wrapper_sha256']=newsha if reran else oldsha;r['metadata_revalidation_wrapper_sha256']=newsha
  r['numeric_cache_reused']=not reran;r['cache_key']=expected_new
  with gzip.open(folder/'PROCESS.json.gz','wt',encoding='utf8') as f:json.dump(clean(process),f,ensure_ascii=False)
  r['process']=asset(folder/'PROCESS.json.gz');save(folder/'FRAME.json',r)
  assert geometry_signature(r)==before_signature
  assert sha(curve_before['path'])==curve_before['sha256'],'CURVES bytes changed'
  for f in official_before:assert sha(f['path'])==f['sha256'],'Official export bytes changed'
  files=[asset(f['path']) for f in receipt['files']]
  save(folder/'COMPLETE.json',dict(key=expected_new,files=files,migration=dict(old_key=expected_old,execution_wrapper_sha256=oldsha,metadata_revalidation_wrapper_sha256=newsha,numerical_reexecution=reran,backup=str(backup))))
  records.append(dict(source_id=row['source_id'],old_id=oldid,new_id=newid,equivalent_ids=identity['equivalent_record_ids'],numerical_reexecution=reran,backup=str(backup),original_FRAME=asset(backup/'FRAME.json'),original_PROCESS=asset(backup/'PROCESS.json.gz'),original_COMPLETE=asset(backup/'COMPLETE.json'),new_FRAME=asset(folder/'FRAME.json'),new_PROCESS=asset(folder/'PROCESS.json.gz'),new_COMPLETE=asset(folder/'COMPLETE.json'),geometry_signature=before_signature,curve_unchanged=curve_before,official_exports_unchanged=official_before,old_key=expected_old,new_key=expected_new))
  if len(records)%100==0:print('MIGRATED',len(records),flush=True)
 index=read(T/'evidence/DXY_FRAME_INDEX.json')
 for record in index['rows']:
  r=read(record['path']);record['sha256']=sha(record['path']);record['selected_record_id']=r['selected_record_id']
 save(T/'evidence/DXY_FRAME_INDEX.json',index)
 save(existing,dict(complete=len(records),corrected_selected_ids=corrected,old_wrapper_sha256=oldsha,new_wrapper_sha256=newsha,old_wrapper_snapshot=asset(oldsrc),official_DXY_commit=COMMIT,scientific_parameter_changes=False,all_selected_center_basis_weight_identical=True,all_CURVES_bytes_identical=True,all_official_exports_bytes_identical=True,numerical_reexecutions=reruns,records=records))
 save(T/'evidence/DXY_METADATA_REVALIDATION_FREEZE.json',dict(wrapper=asset(T/'code/dxy_full.py'),migrator=asset(__file__),migration=asset(existing),semantics='Metadata revalidation only except explicitly enumerated true numerical reruns; original full numerical execution receipts are preserved unchanged'))
 print('COMPLETE',len(records),'CORRECTED_IDS',corrected,'NUMERIC_RERUNS',len(reruns),flush=True)
if __name__=='__main__':main()
