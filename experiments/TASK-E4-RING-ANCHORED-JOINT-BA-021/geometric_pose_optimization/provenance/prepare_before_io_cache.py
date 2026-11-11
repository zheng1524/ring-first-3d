"""Canonical video identity/real feature inputs. No HERO or body read during fitting."""
from gcommon import *
import features019 as feat
from scipy.ndimage import distance_transform_edt
import collections

def main():
 if(M/'provenance/INPUTS_FROZEN.json').exists():print('PREPARED_ALREADY');return
 snapshot();guard_fit();groups=load(P/'config/FOUR_GROUP_INPUTS.json');H=np.array(load(P/'results/B3.json')['T']);vv=[]
 for g in groups:
  rows=load(P/'config/VIEWS.json')if g['group']=='G01'else[g0['meta']|dict(cache=g0['cache'],id=g0['view_id'],role=g0['role'])for g0 in g['views']]
  for v in rows:
   a=np.load(v['cache']);T=np.array(a['T']);T=H@T if g['group']=='G01'and v['video']=='005'else T;v=v|dict(group=g['group'],T=T,K=a['K'],RGB_SHA256=sha(v['RGB_source']),capture_type='VIDEO_FRAME',ring_path=g['ring']['path']);vv.append(v)
 save('config/VIEWS.json',vv);feat.R=M;feat.VIEWS={v['id']:v for v in vv};feat.save=save;feat.table=table
 for v in vv:
  existing=P/'features'/(v['id']+'.npz')
  if existing.exists():
   np.savez_compressed(M/'features'/(v['id']+'.npz'),**dict(np.load(existing)))
  else:feat.features(v)
  src=P/('ring_evidence_v2'if v['group']=='G01'else'group_ring_evidence')/(v['id']+'.npz')
  if not src.exists():
   from geometry021 import actual_ring_points
   e=actual_ring_points(dict(view_id=v['id'],cache=v['cache']),10.)
  else:e=dict(np.load(src))
  # Keep existing observed physical I/O identities. Full fitted ellipses are not observations.
  np.savez_compressed(M/'ring_evidence'/(v['id']+'.npz'),**e)
 for g in groups:
  group=g['group']
  for vid in sorted({v['video']for v in vv if v['group']==group}):
   label=group+'_'+vid;orig='CROSS_004'if vid=='004'else'INDEPENDENT_005'
   if group=='G01':
    lm=dict(np.load(P/'landmarks'/(orig+'.npz')));lm['X']=lm['X']@H[:3,:3].T+H[:3,3]if vid=='005'else lm['X'];np.savez_compressed(M/'landmarks'/(label+'.npz'),**lm);save('landmarks/'+label+'_OBSERVATIONS.json',load(P/'landmarks'/(orig+'_OBSERVATIONS.json')))
   else:
    ids=[v['id']for v in vv if v['group']==group and v['video']==vid and v['role']=='FIT'];feat.landmarks(ids,label)
  print('REAL_FEATURE_MAPS_PREPARED',group,flush=True)
 # Real descriptor-only identities, unique per landmark and target feature. No geometry-nearest identities.
 summary=[]
 for v in vv:
  label=v['group']+'_'+v['video'];lm=np.load(M/'landmarks'/(label+'.npz'));obs=load(M/'landmarks'/(label+'_OBSERVATIONS.json'));f=np.load(M/'features'/(v['id']+'.npz'));bank=[]
  for k,t in enumerate(obs):
   for o in t['observations']:
    if o['view']==v['id']:continue
    ff=np.load(M/'features'/(o['view']+'.npz'));bank.append((k,o['view'],o['feature_id'],ff['des'][o['feature_id']]))
  matches=[]
  if bank:
   inds=feat.match_desc(np.array([r[3]for r in bank]),f['des']);can=[]
   for i,j in inds:
    k,sid,fid,d=bank[i];can.append(dict(landmark_id=k,photo_feature_id=int(j),uv=f['xy'][j],X=lm['X'][k],descriptor_source=sid,source_feature_id=fid,descriptor_distance=float(np.linalg.norm(d-f['des'][j])),role='FEATURE_HELD'if k%5==0 else'FEATURE_FIT'))
   usedk=set();usedj=set()
   for m in sorted(can,key=lambda a:a['descriptor_distance']):
    if m['landmark_id']in usedk or m['photo_feature_id']in usedj:continue
    usedk.add(m['landmark_id']);usedj.add(m['photo_feature_id']);matches.append(m)
  # RGB-RANSAC PnP is a fixed input filter, not output-based selection. Never use held IDs in PnP.
  ff=[m for m in matches if m['role']=='FEATURE_FIT'];inls=[];pnp=False
  if len(ff)>=6:
   cv2.setRNGSeed(20261112);ok,r,t,ii=cv2.solvePnPRansac(np.array([m['X']for m in ff]),np.array([m['uv']for m in ff]),np.array(v['K']),None,iterationsCount=1000,reprojectionError=3.,confidence=.999,flags=cv2.SOLVEPNP_EPNP)
   if ok and ii is not None and len(ii)>=6:inls=[ff[i]for i in ii.ravel()];pnp=True
  # Legal 2D--2D fallback: up to3 angularly complementary FIT reference cameras, frozen P0.
  epis=[]
  if not pnp:
   refs=[r for r in vv if r['group']==v['group']and r['video']==v['video']and r['role']=='FIT'and r['id']!=v['id']];refs=sorted(refs,key=lambda r:-np.linalg.norm(np.array(r['T'])[:3,3]-np.array(v['T'])[:3,3]))[:3]
   for ref in refs:
    a=feat.matches(ref,v);ii=np.flatnonzero(a['RGB_RANSAC']);ii=ii[np.linspace(0,len(ii)-1,min(128,len(ii)),dtype=int)]if len(ii)else ii
    for j in ii:epis.append(dict(reference=ref['id'],p=a['p'][j],q=a['q'][j],target_feature=int(a['index_pairs'][j,1]),role='FEATURE_HELD'if int(a['index_pairs'][j,1])%5==0 else'FEATURE_FIT'))
  save('inputs/'+v['id']+'/RGB_GEOMETRY.json',dict(matches=matches,fit_pnp_inliers=inls,PNP_input_filter_success=pnp,epipolar=epis,no_depth_used=True,landmark_bank=asset(M/'landmarks'/(label+'.npz')),target_cache=asset(Path(v['cache']))));summary.append(dict(group=v['group'],id=v['id'],role=v['role'],map_points=len(lm['X']),RGB_matches=len(matches),fit_PNP=len(inls),held_features=sum(m['role']=='FEATURE_HELD'for m in matches),fallback_epi_N=len(epis)))
 table('metrics/REAL_SIFT_INPUT_COUNTS.csv',summary);save('metrics/REAL_SIFT_INPUT_COUNTS.json',summary);save('provenance/INPUTS_FROZEN.json',dict(epoch=time.time(),views=asset(M/'config/VIEWS.json'),protocol=asset(M/'config/PROTOCOL.json'),sources=[asset(Path(v['cache']))for v in vv],map_counts=summary,HERO_GT_body_used=False));print('GEOMETRIC_PREPARED',len(vv),flush=True)
if __name__=='__main__':main()
