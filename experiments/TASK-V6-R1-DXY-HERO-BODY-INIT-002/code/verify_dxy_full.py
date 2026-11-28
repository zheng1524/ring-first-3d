"""Check complete DXY data, true candidate identities, and old overlap equality."""
from dxy_full import *
from collections import Counter

def main():
 inp=read(T/'evidence/DXY_INPUT_INDEX.json');rows=inp['rows'];counts=Counter();quality=Counter();reliability=Counter();missing=[];oldstats=Counter();errors=[];equal=0;maxdelta=0.;pixels=[];profile_selected=[]
 for row in rows:
  p=T/'runs/dxy'/row['case']/row['frame_id']/'FRAME.json'
  if not p.exists():missing.append(row['source_id']);continue
  r=load_frame(row['case'],row['frame_id']);a=r.pop('data');counts[r['status']]+=1;quality[r['quality']]+=1
  expected_key=hashlib.sha256(json.dumps([row,inp['source'],sha(T/'code/dxy_full.py')],sort_keys=True).encode()).hexdigest()
  assert r['cache_key']==expected_key and read(p.parent/'COMPLETE.json')['key']==expected_key
  assert r['source_id']==row['source_id'] and r['role']==row['role']
  reliability['curve_generated']+=r['selected'] is not None
  for flag in ['strict_stable','normal_Gate_pass','Q_conflict_recovery','P_zero_occlusion_inference']:
   reliability[flag]+=bool(r['official_audit'].get(flag,False))
  reliability['pixel_only_uncertain']+=r['status']=='PIXEL_ONLY'
  reliability['no_selected_curve']+=r['selected'] is None
  for kind in ['RGB','Mask']:assert sha(row[kind])==row[kind+'_sha256']
  assert cv2.imread(row['Mask'],0).shape==tuple(row['native_shape'])
  with gzip.open(r['process']['path'],'rt') as f:process=json.load(f)
  chosen=[x for x in process['default_candidate_pool'] if x['selected']]
  if r['selected']:
   assert len(chosen)==1 and chosen[0]['record_id']==r['selected_record_id']
   assert not chosen[0]['diagnostic_profile']
   assert np.allclose(a['selected_curve'],curve(r['selected']))
   assert r['selected']['weight']>0
  else:assert len(chosen)==0 and len(a['selected_curve'])==0
  if r['status']=='PIXEL_ONLY':
   assert not r['official_measurement_valid'] and r['selected'] is not None
   assert 'D_frame_mm' not in r['selected'];assert len(a['P'])>=20 and len(a['Q'])==0
   pixels.append(dict(source_id=r['source_id'],official_ring_valid=r['official_ring_valid'],official_reason=r['official_reason'],P_count=r['P_count'],selected=r['selected']))
  if len(a['Q']):
   assert np.allclose(np.linalg.norm(a['Q_normals'],axis=1),1)
   assert np.all(a['Q_lo']<=0) and np.all(a['Q_hi']>=0)
  old=OLD/'runs/observations'/row['group']/row['case']/(row['frame_id']+'_DXY.json')
  if old.exists():
   b=read(old);oldstats['previous_frames']+=1
   if b['available']:
    oldstats['previous_available']+=1
    assert r['status']=='OFFICIAL'
    delta=max(np.max(np.abs(np.asarray(r['selected']['center_px'])-b['center_px'])),np.max(np.abs(np.asarray(r['selected']['basis_px'])-b['basis_px'])))
    maxdelta=max(maxdelta,float(delta));equal+=delta<1e-9
   else:oldstats['previous_missing']+=1;oldstats['missing_recovered']+=bool(r['selected'])
 for item in inp['source']['files']:assert sha(item['path'])==item['sha256']
 assert len(rows)==1700 and len({x['case'] for x in rows})==79 and len({x['group'] for x in rows})==39
 result=dict(expected=1700,completed=sum(counts.values()),statuses=dict(counts),quality=dict(quality),reliability=dict(reliability),missing=missing,old_overlap=dict(oldstats),old_available_equal=int(equal),old_available_max_center_basis_difference_px=maxdelta,pixel_recovered=pixels,official_measurement_is_not_pixel_outlet=True,held_role_preserved=True,input_identity=asset(T/'evidence/DXY_INPUT_INDEX.json'),implementation=asset(T/'code/dxy_full.py'))
 save(T/'evidence/DXY_VERIFICATION.json',result)
 print(json.dumps({k:v for k,v in result.items() if k!='pixel_recovered'},ensure_ascii=False))
 assert not missing,'Not all ledger frames completed'
 assert oldstats['previous_frames']==790 and oldstats['previous_missing']==32 and equal==oldstats['previous_available']
if __name__=='__main__':main()
