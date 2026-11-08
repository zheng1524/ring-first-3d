"""Full raw asset census and existing camera/HERO identity import. NoGT, no pose guesses."""
from common import *
import shutil,subprocess
OLD13=REPO/'experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/runs/FREE_VERTEX_013'
RAW=Path('/home/liu/polyp_research/smart_endoscope_20260805/raw')
E1=Path('/home/liu/ring_first_3d_neural_e1/experiments/TASK-NEURAL-E1-PIPELINE-RECOVERY-001/provenance/INPUT_ELIGIBILITY.json')
INV=Path('/home/liu/ring_first_3d_view_eval/experiments/TASK-VIEW-OBSERVABILITY-GT-EVAL-001/metrics/camera_frame_inventory.json')
def content(im):return hashlib.sha256(np.ascontiguousarray(im).tobytes()).hexdigest()
def main():
 cases=load(R/'config/CASE_LOCK.json');lookup={c['name']:c for c in cases};rawrows=[];sources=[];views=[];dedup={};conflicts=[]
 for c in cases:
  n=c['name'];dest=R/'inputs'/n;shutil.copytree(OLD13/'inputs'/n,dest,dirs_exist_ok=True)
  for p in (OLD13/'depth_observations').glob(n+'*.npz'):(R/'depth_observations').mkdir(exist_ok=True);shutil.copyfile(p,R/'depth_observations'/p.name)
  shutil.copyfile(OLD13/'inputs'/n/'INITIAL.npz',dest/'INITIAL.npz')
  for p in sorted(RAW.glob(c['identity']+'_*')):
   if p.suffix.lower()not in ['.mp4','.jpg','.png']:continue
   row=dict(case=n,id=n+'_asset_'+p.stem.rsplit('_',1)[1],type='video'if p.suffix=='.mp4'else'photo',source=str(p),sha256=sha(p),bytes=p.stat().st_size,physical_specimen=c['physical_specimen'],video=p.stem.rsplit('_',1)[1]if p.suffix=='.mp4'else None)
   if row['type']=='video':
    cap=cv2.VideoCapture(str(p));row.update(frame_count=int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),fps=float(cap.get(cv2.CAP_PROP_FPS)),width=int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),height=int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)));cap.release();row['status']='READABLE'if row['frame_count']>0 else'NOT_DECODABLE';row['sid']=n+'_v'+row['video']
   else:row.update(status='INVENTORIED_NO_VERIFIED_PHOTO_INTRINSICS_OR_POSE',camera=None,Mask=None)
   rawrows.append(row)
 def add(n,cid,rgb,labels,K,T,video,role='FIT',hero=None,source=None,raw_frame=None,pose_status='FROZEN_CANDIDATE',original013=False):
  if not(Path(rgb).exists()and Path(labels).exists()):conflicts.append(dict(case=n,id=cid,reason='MISSING_RGB_OR_MASK',RGB=rgb,Mask=labels));return
  im=np.array(Image.open(rgb).convert('RGB'));lab=np.array(Image.open(labels));assert im.shape[:2]==lab.shape==(360,640);key=(n,video,content(im));labsha=content(lab);ids=dedup.get(key);record=dict(id=cid,case=n,sid=n+'_v'+video,video=video,role=role,RGB_source=str(rgb),Mask_source=str(labels),RGB_sha=sha(rgb),Mask_sha=sha(labels),RGB_content_sha=key[2],Mask_content_sha=labsha,K=np.asarray(K),T=np.asarray(T),raw_frame=raw_frame,frame_binding='EXACT_ARCHIVED_ASSET_SHA_CAMERA_SOURCE; rawframe unverified unless pixelconfirmed',qualification=pose_status,pose_source=source,original013=original013,HERO_sources=[]if hero is None else[hero],aliases=[cid],available_camera=True,admission='INPUT_INTEGRITY_ONLY',is_photo=False)
  if ids is not None:
   old=views[ids];old['aliases'].append(cid)
   if hero is not None and hero not in old['HERO_sources']:old['HERO_sources'].append(hero)
   if not(np.allclose(np.asarray(old['K']),K,atol=1e-8)and np.allclose(np.asarray(old['T']),T,atol=1e-6))or old['Mask_content_sha']!=labsha:conflicts.append(dict(case=n,id=cid,canonical=old['id'],reason='SAME_IMAGE_SECONDARY_CAMERA_OR_MASK_VERSION',policy='013first, thenE1 theninventory; secondarynot silentlyused',source=source))
   old['original013']|=original013
   if role!='FIT':old['role']=role
   return
  dedup[key]=len(views);views.append(record);out=R/'inputs'/n;np.savez_compressed(out/(cid+'.npz'),RGB=im,labels=lab,K=K,T=T)
 # 013 has highest canonical priority and frozen holdout identity.
 for c in cases:
  n=c['name']
  for v in c['views']:
   z=np.load(OLD13/'inputs'/n/(v['id']+'.npz'));video='005'if n=='G08'else'004';add(n,v['id'],v.get('RGB_source',v.get('source_RGB')),v.get('Mask_source',v.get('source_Mask')),z['K'],z['T'],video,v['role'],v.get('HERO_source'),str(OLD13/'inputs'/n/(v['id']+'.npz')),v.get('raw_frame'),v['qualification'],True)
 for a in load(E1)['references']:
  n=a['id'].split('_')[0]
  if n not in lookup:continue
  pack=Path(a['pack']);z=np.load(pack);hero=a.get('E1_actual_native',{}).get('path');add(n,a['id'],a['RGB'],a['Mask'],z['K'],z['pose'],a['id'].split('_')[1],hero=hero,source=str(pack),raw_frame=a.get('raw_frame'),pose_status=a.get('pose_status','FROZEN_CANDIDATE'))
 for a in load(INV):
  n=a['group']
  if n not in lookup:continue
  rgb=a['RGB'];lab=a['Mask']
  if a['source_id']=='G01_video005':
   ledger=load(Path('/home/liu/polyp_research/ring_anchor_3d/experiments/ring_first_v6_local_reconstruction/inputs/ledger005.json'));ent=ledger[a['index']];rgb=ent['RGB_path'];lab=ent['Mask_path']
  add(n,a['source_id']+'_'+a['view_id'],rgb,lab,a['K'],a['c2w'],a['source_id'][-3:],source=str(INV)+'#'+str(a['index']),pose_status=a['pose_status'])
 # All8 existing per-video camera outputs (including non-HERO frames) from original pipeline.
 for c in cases:
  n=c['name'];anchor=next((v for v in c['views']if 'camera_index'in v),None)
  if anchor is None:continue
  root=Path(anchor['RGB_source']).parent.parent
  if not(root/'inputs/ledger005.json').exists():continue
  L=load(root/'inputs/ledger005.json');m=load(root/'inputs/MVS_cases.json')[0];cam=root/f'predictions/local005_camera_{m["primary_version"]}.npz';z=np.load(cam);vid=Path(L[0]['source_video']).stem.rsplit('_',1)[1]
  for i,v in enumerate(L):add(n,n+'_'+v['id'],v['RGB_path'],v['Mask_path'],z['K'],z['c2w'][i],vid,source=str(cam)+'#'+str(i),raw_frame=v['raw_frame'],pose_status='FROZEN_MODEL_CANDIDATE')
 for c in cases:
  vv=[v for v in views if v['case']==c['name']];save('inputs/'+c['name']+'/CASE.json',dict(c,views=[dict(id=v['id'],role=v['role'],qualification=v['qualification'],video=v['video'],HERO_source=v['HERO_sources'][0]if v['HERO_sources']else None)for v in vv]))
 save('config/EXISTING_VIEWS.json',views);save('config/RAW_ASSETS.json',rawrows);table('metrics/RAW_ASSET_INVENTORY.csv',rawrows);table('metrics/IDENTITY_CONFLICTS.csv',conflicts);save('metrics/IDENTITY_CONFLICTS.json',conflicts);save('provenance/EXISTING_INPUTS.json',dict(epoch=time.time(),sources=[asset(E1),asset(INV)],views=len(views),rawvideos=sum(x['type']=='video'for x in rawrows),photos=sum(x['type']=='photo'for x in rawrows),old_tags_exclude_case=False));print('EXISTING',len(views),'RAW',len(rawrows),'CONFLICTS',len(conflicts))
if __name__=='__main__':main()
