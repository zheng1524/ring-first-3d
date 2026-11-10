"""Frozen single-video pool; quota sampling uses existing direction partitions."""
from common import *
from scipy.ndimage import distance_transform_edt
import shutil
OLD15=REPO/'experiments/TASK-E4-MULTIVIEW-INIT-STALK-015'
POOL=REPO/'experiments/TASK-E4-SINGLE-VIDEO-013-FAST-001'

def link(a,b):
 b.parent.mkdir(parents=True,exist_ok=True)
 if not b.exists():b.symlink_to(a.resolve())

def weights(vs,ids):
 by={v['id']:v for v in vs};blocks={by[i].get('direction_block',0)for i in ids}
 return {i:1/len(blocks)/sum(by[j].get('direction_block',0)==by[i].get('direction_block',0)for j in ids)for i in ids}

def coverage(vs,ids):
 by={v['id']:v for v in vs};d=np.array([by[i]['direction']for i in ids]);ang=np.degrees(np.arccos(np.clip(d@d.T,-1,1)));pairs=ang[np.triu_indices(len(d),1)]
 return dict(N=len(ids),blocks=sorted({by[i]['direction_block']for i in ids}),max_span_deg=float(ang.max()),minimum_pair_deg=float(pairs.min())if len(pairs)else None,median_pair_deg=float(np.median(pairs))if len(pairs)else None,near_duplicate_direction_pairs_below3deg=int((pairs<3).sum()),direction_weights=weights(vs,ids),frame_order=[by[i].get('raw_frame')for i in ids])

def arm(tag,n,selected,initial,mode='BASE',stage='sampling'):
 root=R/'arms'/tag
 for d in ['inputs','config','local_results','metrics','runtime','provenance','depth_observations']:(root/d).mkdir(parents=True,exist_ok=True)
 src=R/'inputs'/n;out=root/'inputs'/n;out.mkdir(exist_ok=True)
 for p in src.iterdir():
  if p.is_file()and p.name not in ['CASE.json','INITIAL.npz']:link(p,out/p.name)
 link(initial,out/'INITIAL.npz')
 held=load(R/'config/VIEW_SELECTION_016.json')[n]['HOLDOUT'];meta=load(src/'CASE.json');meta['views']=[dict(v,role='FIT'if v['id']in selected else'UPDATE_HOLDOUT')for v in meta['views']if v['id']in selected+held]
 (out/'CASE.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
 for p in (R/'depth_observations').glob('*.npz'):link(p,root/'depth_observations'/p.name)
 cfg=load(R/'config/PROTOCOL.json');(root/'config/PROTOCOL.json').write_text(json.dumps(cfg,indent=2)+'\n');(root/'config/ARM.json').write_text(json.dumps(dict(tag=tag,phase=stage,mode=mode,loss='D0_013',budget=cfg['phase_A']['downstream']),indent=2)+'\n')
 return root

def main():
 assert not(R/'provenance/FORMAL_FREEZE.json').exists()
 selection={};inventory=[];audit=[]
 oldsel=load(OLD15/'config/VIEW_SELECTION.json');oldinventory=load(OLD15/'metrics/VIEW_INVENTORY.json');quality={x['view']:x for x in oldinventory if x['role']=='candidateFIT'}
 for c in load(R/'config/CASE_LOCK.json'):
  n=c['name'];master=load(POOL/'inputs'/n/'CASE.json');oldmeta=load(OLD15/'inputs'/n/'CASE.json');center=np.load(OLD15/'inputs'/n/'INITIAL.npz')['V'].mean(0);out=R/'inputs'/n;out.mkdir(exist_ok=True)
  for p in (POOL/'inputs'/n).iterdir():
   if p.is_file()and p.name!='CASE.json':link(p,out/p.name)
  fit=[dict(v)for v in master['views']if v['role']=='FIT'];held=oldsel[n]['HOLDOUT'];oldids=oldsel[n]['FIT'];mandatory=[i for i in oldids if(OLD15/'depth_observations'/(i+'.npz')).exists()]
  # Existing partition is an approximately15deg complete-link camera-direction
  # cluster, not a time bin. Preserve its definition for the paired experiment.
  for v in fit:
   a=np.load(out/(v['id']+'.npz'));d=a['T'][:3,3]-center;v['direction']=(d/np.linalg.norm(d)).tolist()
   assert 'direction_block'in v,'Explicit partition required; no silent default'
  by={v['id']:v for v in fit};blocks=sorted({v['direction_block']for v in fit});chosen=mandatory.copy();reasons={i:'FIXED_HERO_SOURCE_ANCHOR'for i in chosen}
  qs=np.array([[np.log1p(quality[v['id']]['sharpness']),quality[v['id']]['mask_complete_proxy'],quality[v['id']]['thin_structure_visibility_proxy'],quality[v['id']]['Ring_free_fraction']]for v in fit]);qs=(qs-qs.min(0))/np.maximum(np.ptp(qs,axis=0),1e-12);qscore={v['id']:float(qs[k]@np.array([.4,.2,.2,.2]))for k,v in enumerate(fit)}
  frames={v['id']:float(v['raw_frame'])if v.get('raw_frame')is not None else None for v in fit};knownframes=[v for v in frames.values()if v is not None];timescale=max(1.,max(knownframes)-min(knownframes))if knownframes else 1.
  while len(chosen)<min(8,len(fit)):
   candidates=[]
   for v in fit:
    if v['id']in chosen:continue
    angles=[float(np.degrees(np.arccos(np.clip(np.dot(v['direction'],by[x]['direction']),-1,1))))for x in chosen]
    if angles and min(angles)<3.:continue
    b=v['direction_block'];number=sum(by[x]['direction_block']==b for x in chosen);ang=min(angles)if angles else 180.;times=[abs(frames[v['id']]-frames[x])/timescale for x in chosen if frames[x]is not None]if frames[v['id']]is not None else[];td=min(times)if times else 0.
    candidates.append((number,-(.65*min(ang/15.,1)+.2*td+.15*qscore[v['id']]),v['id']))
   if not candidates:break
   _,_,cid=min(candidates);chosen.append(cid);reasons[cid]='MIN_DIRECTION_BLOCK_QUOTA_THEN_ANGLE_TIME_QUALITY'
  weights_old=weights(fit,oldids);weights_new=weights(fit,chosen);seen=[v for v in oldmeta['views']if v['role']=='FIT'];missing=sum('direction_block'not in v for v in seen)
  blockspan={str(b):coverage(fit,[v['id']for v in fit if v['direction_block']==b])['max_span_deg']for b in blocks};allcov=coverage(fit,[v['id']for v in fit]);oldcov=coverage(fit,oldids);newcov=coverage(fit,chosen)
  selection[n]=dict(OLD=oldids,BALANCED=chosen,HOLDOUT=held,HERO_anchors=mandatory,available_blocks=blocks,missing_selected_blocks=sorted(set(blocks)-set(newcov['blocks'])),minimum_new_nonanchor_separation_deg=3.,actual_frames=len(chosen),frame_order_not_timestamp=True)
  assert set(chosen).isdisjoint(held)and set(mandatory).issubset(chosen)
  assert {i for i in chosen if(OLD15/'depth_observations'/(i+'.npz')).exists()}==set(mandatory),'Do not change HERO observations'
  row=dict(case=n,available=allcov,old=oldcov,balanced=newcov,old_missing_direction_block_N=missing,actual_default_collapse=missing==len(seen),existing_block_max_pairwise_degrees=blockspan,missing_available_blocks=selection[n]['missing_selected_blocks'],HERO_source_ids_same=True)
  audit.append(row)
  for v in fit:
   cid=v['id'];item=dict(quality[cid]);item.update(case=n,view=cid,video=v['video'],direction=v['direction'],direction_block=v['direction_block'],raw_frame=v.get('raw_frame'),selected_old=cid in oldids,selected_balanced=cid in chosen,weight_old=weights_old.get(cid,0),weight_balanced=weights_new.get(cid,0),selection_reason=reasons.get(cid),HERO_anchor=cid in mandatory);inventory.append(item)
  vv=[dict(v,role='FIT'if v['id']in oldids else'COMMON_FIT_EVAL')for v in fit]+[dict(v,role='UPDATE_HOLDOUT')for v in master['views']if v['id']in held];meta=dict(master,views=vv);save('inputs/'+n+'/CASE.json',meta)
 for p in (OLD15/'depth_observations').glob('*.npz'):link(p,R/'depth_observations'/p.name)
 save('config/VIEW_SELECTION_016.json',selection);save('metrics/VIEW_SAMPLING_AUDIT.json',audit);table('metrics/VIEW_SAMPLING_AUDIT.csv',audit);table('metrics/VIEW_SELECTION_AND_WEIGHTS.csv',inventory);save('metrics/VIEW_SELECTION_AND_WEIGHTS.json',inventory)
 for c in load(R/'config/CASE_LOCK.json'):
  n=c['name'];initial=OLD15/'inputs'/n/'INITIAL.npz'
  arm('S0_015',n,selection[n]['OLD'],initial);arm('S1_BALANCED',n,selection[n]['BALANCED'],initial)
 for n in ['G01','G02','G03']:
  initial=OLD15/'arms/Init-A/local_results'/n/'FINAL.npz';root=arm('DIAGNOSTIC',n,selection[n]['OLD'],initial,'BASE','diagnosis');seed=OLD15/'arms/Stalk-A/inputs'/n/'STALK_SEED.json';shutil.copyfile(seed,root/'inputs'/n/'STALK_SEED.json')
 save('provenance/SAMPLING_BEFORE_FORMAL_OPTIMIZATION.json',dict(epoch=time.time(),source=asset(Path(__file__)),selection=asset(R/'config/VIEW_SELECTION_016.json'),GT_used=False,heldout_untouched=True))
 print('SAMPLING_PREPARED',[(x['case'],x['old']['N'],x['balanced']['N'],x['old_missing_direction_block_N'])for x in audit],flush=True)

if __name__=='__main__':main()
