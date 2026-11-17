"""Coverage-driven observations, fixed HOLDOUT, per-video/block balancing."""
from common import *
from ring_sides import sample
from scipy.cluster.hierarchy import linkage,fcluster

def main():
 old=load(R/'config/EXISTING_VIEWS.json');new=load(R/'config/DERIVED_VIEWS.json');views=list(old);duplicates=[]
 # Binding near-duplicates to archived images uses pixel arrays, never names. These
 # remain distinct archived encodings but carry the stricter split of either copy.
 for v in new:
  z=np.load(R/'inputs'/v['case']/(v['id']+'.npz'));im=z['RGB'];candidates=[a for a in old if a['sid']==v['sid']];diff=[]
  for a in candidates:
   aa=np.load(R/'inputs'/a['case']/(a['id']+'.npz'))['RGB'];diff.append(float(cv2.absdiff(im,aa).mean()))
  j=int(np.argmin(diff))if diff else -1
  if j>=0 and diff[j]<2.:
   a=candidates[j];duplicates.append(dict(new=v['id'],archived=a['id'],mean_RGB_abs=diff[j],status='NEAR_DUPLICATE_ENCODING_NOT_EXACT_SHA',policy='archival camera/mask canonical; protect HOLDOUT; do not multiply evidence'))
   a['aliases']+=v['aliases'];a['raw_candidate_aliases']=a.get('raw_candidate_aliases',[])+[v['id']]
   if v['role']!='FIT':a['role']='UPDATE_HOLDOUT'
   continue
  views.append(v)
 corrections=load(R/'config/VIDEO_CORRECTIONS.json')if(R/'config/VIDEO_CORRECTIONS.json').exists()else{};rows=[];selection={};coverage=[]
 for c in load(R/'config/CASE_LOCK.json'):
  n=c['name'];vv=[v for v in views if v['case']==n];center=np.load(R/'inputs'/n/'INITIAL.npz')['V'].mean(0)
  for v in vv:
   T=np.array(v['T']);v['T_original']=T.tolist();D=np.array(corrections.get(v['sid'],np.eye(4)));T=D@T;v['T']=T.tolist();v['Delta_T']=D.tolist()
   file=R/'inputs'/n/(v['id']+'.npz');a=dict(np.load(file));a['T']=T;np.savez_compressed(file,**a)
   sfile=R/'inputs'/n/(v['id']+'_SIDES.npz')
   if not sfile.exists():_,cl,band=sample(a['labels']);np.savez_compressed(sfile,classes=cl,band=band)
   dr=T[:3,3]-center;v['direction']=(dr/max(1e-12,np.linalg.norm(dr))).tolist();v['distance_mm']=float(np.linalg.norm(dr));g=cv2.cvtColor(a['RGB'],cv2.COLOR_RGB2GRAY);v['sharpness']=float(cv2.Laplacian(g,cv2.CV_64F).var());v['glare_fraction']=float((g>245).mean());v['Polyp_pixels']=int((a['labels']==1).sum())
  selection[n]={}
  for sid in sorted({v['sid']for v in vv}):
   vs=[v for v in vv if v['sid']==sid];ds=np.array([v['direction']for v in vs]);cl=fcluster(linkage(ds,method='complete'),t=.26,criterion='distance')if len(vs)>1 else np.ones(len(vs),int)
   for v,k in zip(vs,cl):v['direction_block']=int(k)
   fit=[v for v in vs if v['role']=='FIT'];protected=[v for v in fit if v['HERO_sources']or v['original013']];order=list(protected)
   if not order and fit:order=[max(fit,key=lambda v:v['sharpness'])]
   while len(order)<len(fit):
    left=[v for v in fit if v not in order];chosen=max(left,key=lambda v:(min(np.arccos(np.clip(np.dot(v['direction'],a['direction']),-1,1))for a in order),v['sharpness']))
    order.append(chosen)
   for label,num in [('C1_8',8),('C2_16',16),('C3_32',32),('C4_ALL',len(fit))]:
    chosen=order[:max(num,len(protected))];selection[n].setdefault(label,[]).extend(v['id']for v in chosen)
    dd=np.array([v['direction']for v in chosen]);ang=np.degrees(np.arccos(np.clip(dd@dd.T,-1,1)))if len(dd)else np.zeros((0,0));coverage.append(dict(case=n,sid=sid,arm=label,selected_N=len(chosen),FIT_available_N=len(fit),HERO_protected_N=len(protected),direction_blocks=len(set(v['direction_block']for v in chosen)),max_direction_span_deg=float(ang.max())if len(ang)else None,median_pairwise_angle_deg=float(np.median(ang[np.triu_indices(len(ang),1)]))if len(ang)>1 else None))
  selection[n]['C0']=[v['id']for v in vv if v['original013']and v['role']=='FIT'];selection[n]['HOLDOUT']=[v['id']for v in vv if v['role']!='FIT'];selection[n]['COMMON_FIT_EVALUATION']=[v['id']for v in vv if v['role']=='FIT']
  for v in vv:rows.append({k:v.get(k)for k in ['case','id','sid','video','role','RGB_source','Mask_source','RGB_sha','Mask_sha','raw_frame','time_sec','frame_binding','pose_source','qualification','HERO_sources','original013','direction','direction_block','distance_mm','sharpness','glare_fraction','Polyp_pixels','aliases']})
  save('inputs/'+n+'/CASE.json',dict(c,views=vv));print('PARTITION',n,len(vv),'FIT',sum(v['role']=='FIT'for v in vv),'HELD',len(selection[n]['HOLDOUT']),flush=True)
 save('config/ALL_VIEWS.json',views);save('config/VIEW_SELECTION.json',selection);save('VIEW_SELECTION.json',selection);table('VIEW_INVENTORY.csv',rows);table('VIEW_PARTITION.csv',rows);table('metrics/VIEW_COVERAGE.csv',coverage);table('metrics/NEAR_DUPLICATE_BINDINGS.csv',duplicates);save('provenance/VIEW_PARTITION_FREEZE.json',dict(epoch=time.time(),code=asset(Path(__file__)),inventory=asset(R/'VIEW_INVENTORY.csv'),selection=asset(R/'VIEW_SELECTION.json'),GT_used=False))
if __name__=='__main__':main()
