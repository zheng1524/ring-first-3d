from common import *
import shutil,ast
P16=REPO/'experiments/TASK-E4-UPDATE-CAUSALITY-016';P17=REPO/'experiments/TASK-E4-HERO-GEOMETRY-CLEAN-017'
GROUPS=['G06','G05','G01','G03']
def main():
 assert not(R/'provenance/INPUT_PLAN_FROZEN.json').exists();selection=load(P16/'config/VIEW_SELECTION_016.json');old17={r['source_id']:r for r in load(P17/'config/SOURCE_LOCK.json')};plan=[];inputassets=[];supportplans=[]
 for g in GROUPS:
  meta=load(P16/'arms/S1_BALANCED/inputs'/g/'CASE.json');by={v['id']:v for v in meta['views']};fit=selection[g]['BALANCED'];held=selection[g]['HOLDOUT'];heldhash={sha(by[x]['RGB_source'])for x in held};heldcontent={hashlib.sha256(np.asarray(Image.open(by[x]['RGB_source']).convert('RGB')).tobytes()).hexdigest()for x in held}
  folder=R/'inputs'/g;folder.mkdir(exist_ok=True)
  for key in ['RING.npz','BASE_SELECTION.json','CHART.json','NORMALIZATION.json']:
   src=P16/'arms/S1_BALANCED/inputs'/g/key;shutil.copyfile(src,folder/key);inputassets.append(asset(src))
  initial=P16/'arms/S1_BALANCED/local_results'/g/'FINAL.npz';shutil.copyfile(initial,folder/'INITIAL.npz');inputassets.append(asset(initial))
  save('inputs/'+g+'/CASE.json',dict(meta,views=[by[c]for c in fit]));save('inputs/'+g+'/ALL_VIEW_META.json',meta)
  # All declared FIT directions come from frozen016, never held images/geometry.
  dirs={cid:np.array(by[cid]['direction'])for cid in fit}
  for cid in fit+held:
   v=by[cid];role='FIT'if cid in fit else'HOLDOUT';cache=P16/'arms/S1_BALANCED/inputs'/g/(cid+'.npz');a=np.load(cache);assert np.array_equal(a['RGB'],np.asarray(Image.open(v['RGB_source']).convert('RGB')));assert np.array_equal(a['labels'],np.asarray(Image.open(v['Mask_source'])));assert np.allclose(a['K'],v['K'])and np.allclose(a['T'],v['T']);inputassets.extend([asset(cache),asset(v['RGB_source']),asset(v['Mask_source'])])
   dest=folder if role=='FIT'else R/'holdout'/g;dest.mkdir(parents=True,exist_ok=True)
   for suffix in ['.npz','_SIDES.npz']:
    src=P16/'arms/S1_BALANCED/inputs'/g/(cid+suffix);assert src.exists();shutil.copyfile(src,dest/(cid+suffix));inputassets.append(asset(src))
   candidates=[x for x in fit if x!=cid];target=np.array(v['direction']);chosen=[]
   # Nearest source first for overlap, then complement the chosen direction set.
   chosen.append(max(candidates,key=lambda x:(float(dirs[x]@target),x)))
   while len(chosen)<3:
    left=[x for x in candidates if x not in chosen];win=max(left,key=lambda x:(.7*float(np.min(np.arccos(np.clip(np.array([dirs[z]for z in chosen])@dirs[x],-1,1))))+.3*float(dirs[x]@target),x));chosen.append(win)
   assert not set(chosen)&set(held)
   reuse=None;reason='NO_NATIVE_FOR_EXACT_TARGET'
   if cid in old17:
    old=old17[cid];parents=old.get('upstream_RGB',[])
    if parents:
     bad=[x for x in parents if sha(x['RGB'])in heldhash or hashlib.sha256(np.asarray(Image.open(x['RGB']).convert('RGB')).tobytes()).hexdigest()in heldcontent]
     if bad:reason='HISTORICAL_HERO_UPSTREAM_USES_PROTECTED_HOLDOUT'
     else:reuse=old;reason='EXACT_017_NATIVE_AND_RAW_WITH_KNOWN_NONHOLDOUT_PARENTS'
    else:reason='HISTORICAL_UPSTREAM_NOT_YET_PROVEN_HOLDOUT_FREE_REGENERATE'
   row=dict(group=g,video='004',view_id=cid,role=role,meta=v,cache=str(dest/(cid+'.npz')),support_views=chosen,support_policy='three same-video FIT sources only; no HOLDOUT RGB/Mask/depth in FIT generation',reuse=reuse,recovery_reason=reason,RGB_SHA256=sha(v['RGB_source']),Mask_SHA256=sha(v['Mask_source']),pose_cache_SHA256=sha(cache),input_complete=True)
   plan.append(row);supportplans.append(dict(group=g,view=cid,role=role,sources=chosen,reuse=bool(reuse),reason=reason))
  for p in(P16/'arms/S1_BALANCED/depth_observations').glob(g+'*.npz'):
   if p.stem in fit:
    dest=R/'depth_observations'/p.name;dest.parent.mkdir(exist_ok=True);shutil.copyfile(p,dest)
 save('config/VIEW_PLAN.json',plan);save('config/VIEW_SELECTION_016.json',{g:selection[g]for g in GROUPS});table('metrics/HERO_RECOVERY_PLAN.csv',supportplans)
 save('config/PROTOCOL.json',dict(seed=20261110,depth=load(P16/'arms/S1_BALANCED/config/PROTOCOL.json')['depth'],HERO_size=[352,640],HERO_refinement_steps=1,mesh_max_depth_jump_mm=.75,budget=dict(max_proposals=80,max_accepted=40,consecutive_rejection_stop=30),learning_rate=.02,hero_sigma_mm=.5,lambda_H=.01,lambda_S=1.,lambda_P=1.,Ring='unchanged hard GeometryGuard indicator, not a fabricated differentiable penalty',hero_raster='official P3D hard bin_size=0 at original native HERO resolution; perspective-correct barycentric world positions; no zbuf-as-mm',silhouette_raster='same016 objective/settings except official naive bin_size=0 for all arms to remove coarse-bin reentry instability',loss_huber='uncapped Huber, hit gradients do not saturate to zero',miss='fixed per-observation worst-feasible Huber+1 from initial axial vertex range plus total trust D; zero missing gradient explicitly reported',observations='all eligible native source pixels whose exact own-view original Raw first-hit face is TRUSTED/full and source is Polyp, positive depth, before Ring; no256 thinning',heldout='asset recovery/labeling separate; optimizer CASE FIT only and read firewall excludes all held paths; inherited initialization ancestry disclosed',new_optimizers=False,ARAP=False,new_SDF=False,GT=False))
 (R/'01_PROTOCOL.md').write_text('# 018 pre-registration\n\n29 FIT +14 HOLDOUT, frozen016 S1_BALANCED IDs. All per-view HERO must be complete before a group trains. Each group has one shared Mesh initialized from016 S1 FINAL. B0 static, B1 full HERO, B2 TRUSTED only, OLD_DEPTH separate. G01 adds single/two sources with same8 FIT silhouettes. Budgets80 proposals/40 accepted/30stall; unchanged GeometryGuard. All weights fixed, no GT or HOLDOUT selection. Hard Ring indicator, no extra finite Ring penalty. No oldD2 in newHERO arms. Native-resolution P3D correspondence; no-hit fixed denominator cost but no invented no-hit gradient. No subdivision unless measured resolution bottleneck.\n')
 files=inputassets+[asset(p)for p in sorted((R/'code').glob('*.py'))]+[asset(p)for p in sorted((R/'config').glob('*.json'))];save('provenance/INPUT_PLAN_FROZEN.json',dict(epoch=time.time(),files=files,FIT_N=sum(r['role']=='FIT'for r in plan),HOLDOUT_N=sum(r['role']=='HOLDOUT'for r in plan),GT=False));print('PREPARED_29_FIT_14_HOLDOUT',sum(bool(r['reuse'])for r in plan),'eligible reuse',flush=True)
if __name__=='__main__':main()
