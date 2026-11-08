"""Cache-only, same-video inputs. No inference, pose fit, new Mask, or GT."""
from common import *
import shutil
OLD13=REPO/'experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/runs/FREE_VERTEX_013'
OLD14=REPO/'experiments/TASK-E4-PYTORCH3D-014'
TAGS=['S0','S8','S16','S32']
def link(source,dest):
 if not dest.exists():dest.symlink_to(source.resolve(),target_is_directory=source.is_dir())
def main():
 assert not(R/'provenance/INPUTS_FROZEN.json').exists(),'Preserve frozen input selection'
 allviews=load(OLD14/'config/ALL_VIEWS.json');reference=load(R/'config/REFERENCE_VIDEOS.json');cases=load(R/'config/CASE_LOCK.json');selection={};inventory=[];coverage=[];cache=[];inputs=[]
 for c in cases:
  n=c['name'];video=reference[n]['reference_video'];original=load(OLD13/'inputs'/n/'CASE.json');oldfit=[v['id']for v in original['views']if v['role']=='FIT'];oldheld={v['id']for v in original['views']if v['role']!='FIT'};vv=[dict(v)for v in allviews if v['case']==n and v['video']==video];by={v['id']:v for v in vv}
  assert all(i in by for i in oldfit+list(oldheld));assert all(by[v['id']]['video']==video for v in original['views'])
  held=oldheld|{v['id']for v in vv if v['role']!='FIT'};held-=set(oldfit);center=np.load(OLD13/'inputs'/n/'INITIAL.npz')['V'].mean(0);folder=R/'inputs'/n;folder.mkdir(exist_ok=True)
  for p in (OLD13/'inputs'/n).iterdir():
   if p.name!='CASE.json'and p.is_file():link(p,folder/p.name)
  for v in vv:
   cid=v['id'];v['role']='UPDATE_HOLDOUT'if cid in held else'FIT';assert np.allclose(v.get('Delta_T',np.eye(4)),np.eye(4),atol=1e-12),'Never import014video corrections';a=OLD13/'inputs'/n/(cid+'.npz');a=a if a.exists()else OLD14/'inputs'/n/(cid+'.npz');z=np.load(a);T=z['T'];assert np.allclose(T,v.get('T_original',T),atol=1e-12);d=T[:3,3]-center;v['direction']=(d/np.linalg.norm(d)).tolist();v['T']=T.tolist();v['K']=z['K'].tolist();v['camera_cache']=str(a);v['camera_correction_used']=False
   if not(folder/(cid+'.npz')).exists():link(a,folder/(cid+'.npz'))
   ss=OLD13/'inputs'/n/(cid+'_SIDES.npz');ss=ss if ss.exists()else OLD14/'inputs'/n/(cid+'_SIDES.npz');link(ss,folder/ss.name)
   inventory.append(dict(case=n,view=cid,video=video,role=v['role'],original013=cid in {x['id']for x in original['views']},raw_frame=v.get('raw_frame'),frame_binding=v.get('frame_binding'),qualification=v.get('qualification'),camera_cache=str(a),camera_sha256=sha(a),RGB_source=v.get('RGB_source'),Mask_source=v.get('Mask_source'),direction=v['direction'],no_video_correction=True))
  meta=dict(original,views=vv,reference_video=video,scope='single_video_only');save('inputs/'+n+'/CASE.json',meta)
  fit=[v for v in vv if v['role']=='FIT'];chosen=list(oldfit);order=[]
  while len(chosen)<min(32,len(fit)):
   D=np.array([by[i]['direction']for i in chosen]);remaining=[v for v in fit if v['id']not in chosen]
   winner=max(remaining,key=lambda v:(float((1-np.array(v['direction'])@D.T).min()),float(v.get('sharpness',0)),v['id']));chosen.append(winner['id']);order.append(winner['id'])
  selection[n]={tag:list(oldfit)if tag=='S0'else chosen[:min(int(tag[1:]),len(fit))]for tag in TAGS};selection[n]['HOLDOUT']=sorted(held);selection[n]['reference_video']=video
  assert set(oldfit)<=set(selection[n]['S8']);assert not(set(chosen)&held)
  for tag in TAGS:
   ids=selection[n][tag];D=np.array([by[i]['direction']for i in ids]);ang=np.degrees(np.arccos(np.clip(D@D.T,-1,1)));did=[i for i in ids if(OLD13/'depth_observations'/(i+'.npz')).exists()];NN=sum(len(np.load(OLD13/'depth_observations'/(i+'.npz'))['z'])for i in did)
   coverage.append(dict(case=n,arm=tag,video=video,actual_FIT_N=len(ids),candidate_FIT_N=len(fit),HOLDOUT_N=len(held),max_direction_span_deg=float(ang.max()),median_pairwise_angle_deg=float(np.median(ang[np.triu_indices(len(ids),1)]))if len(ids)>1 else 0.,HERO_source_ids=did,HERO_fixed_rays=NN,effective_013_depth_coefficient=.01*len(did)/len(ids),selection='nested greedy farthest camera direction, original013FIT protected; noGT'))
   arm=R/'arms'/tag
   for d in ['inputs','config','assets_index','local_results','metrics','runtime']:(arm/d).mkdir(parents=True,exist_ok=True)
   target=arm/'inputs'/n;target.mkdir(exist_ok=True)
   for p in folder.iterdir():
    if p.name!='CASE.json':link(p,target/p.name)
   ameta=original if tag=='S0'else dict(meta,views=[dict(v,role='FIT'if v['id']in ids else'UPDATE_HOLDOUT')for v in vv if v['id']in ids or v['id']in held]);(target/'CASE.json').write_text(json.dumps(ameta,ensure_ascii=False,indent=2))
   support=OLD13/'arms/FINAL_UNIFORM/local_results'/(n+'_P0_SUPPORT.npz');assert support.exists();shutil.copyfile(support,arm/'local_results'/support.name)
  # S0 is a verified exact historical replay cache, not a fallback for failed arms.
  s0=R/'arms/S0';src=OLD13/'arms/FINAL_UNIFORM/local_results'/n;dst=s0/'local_results'/n;dst.mkdir(exist_ok=True)
  for p in src.iterdir():
   if p.is_file():link(p,dst/p.name)
  for p in (OLD13/'arms/FINAL_UNIFORM/metrics').glob(n+'_*'):link(p,s0/'metrics'/p.name)
  cache.append(dict(case=n,source=str(src/'FINAL.npz'),sha256=sha(src/'FINAL.npz'),initial_exact=sha(folder/'INITIAL.npz')==sha(OLD13/'inputs'/n/'INITIAL.npz'),original_FIT_order_exact=oldfit,reference_video=video,method='A3/O3N/1D,800proposals/300accepted/80stall',reuse='explicit exact S0 control, never used to replace S8/S16/S32 failure'))
 for p in(OLD13/'depth_observations').glob('*.npz'):link(p,R/'depth_observations'/p.name)
 for tag in TAGS:
  arm=R/'arms'/tag;link(R/'depth_observations',arm/'depth_observations');shutil.copyfile(R/'config/PROTOCOL.json',arm/'config/PROTOCOL.json');shutil.copyfile(R/'config/CASE_LOCK.json',arm/'config/CASE_LOCK.json')
 save('config/VIEW_SELECTION.json',selection);save('provenance/S0_CACHE_VALIDATION.json',cache);table('VIEW_INVENTORY.csv',inventory);table('VIEW_COVERAGE.csv',coverage);save('metrics/VIEW_COVERAGE.json',coverage)
 # Freeze only actual inputs/parameters/code. No GT assets or historic GT metrics.
 for d in ['inputs','depth_observations','config','code']:
  inputs.extend(asset(p)for p in sorted((R/d).rglob('*'))if p.is_file())
 save('provenance/INPUTS_FROZEN.json',dict(epoch=time.time(),files=inputs,no_second_video=True,no_new_HERO_or_masks_or_cameras=True,GT_used=False))
 print('INPUTS_LOCKED',len(cases),len(inventory),[dict(case=c['name'],counts=[len(selection[c['name']][t])for t in TAGS])for c in cases])
if __name__=='__main__':main()
