from register import *
from native005_extension import pnp_bank
from evaluate_geometry import *
from scipy.linalg import logm

def main():
 hod=[];histphotos=[];gauge=[];ranks=[]
 for g in GROUPS:
  vs=load(camera_file(g));ext='_NATIVE005'if g=='G01'else'';rr=load(N/'registration'/g/('JOINT_FULL6'+ext+'_FINAL.json'));h=np.array(rr['source_H']['005']);sel=rr['selected'];bases={v['id']:v for v in load(N/'config'/(g+'_INITIAL_CAMERAS.json'))};
  if g=='G01':
   for c in list(bases):
    pp=N/'registration/G01/NATIVE005_EXTENSION'/(c+'_INITIAL.json')
    if pp.exists():bases[c]=load(pp)
  anchor=next((c for c in sel if bases[c]['video']=='005'),None)
  if anchor:
   qa=np.array(rr['q'][anchor]);Gg=exp(qa);hp=h@Gg;maxerr=0.;local={}
   for c in sel:
    if bases[c]['video']!='005':continue
    L=np.linalg.inv(Gg)@exp(np.array(rr['q'][c]));local[c]=L;oldC=h@exp(np.array(rr['q'][c]))@np.array(bases[c]['C']);newC=hp@L@np.array(bases[c]['C']);maxerr=max(maxerr,float(abs(oldC-newC).max()),float(abs(newC-np.array(rr['poses'][c])).max()))
   gauge.append(dict(group=g,anchor005=anchor,H005_anchor_fixed=hp,local_transforms=local,anchor_local_identity_error=float(abs(local[anchor]-np.eye(4)).max()),all_world_camera_max_error=maxerr,optimization_used_pose_priors_for_H_local_split=True,post_freeze_exact_gauge_canonicalization_not_new_optimization=True,shared_source_SE3_is_residual_to_RGB_initialization=True));assert maxerr<1e-10
  for c in sel:
   v=next(v for v in vs if v['id']==c);geom=load(v.get('rgb_geometry_path',N/'inputs'/c/'RGB_GEOMETRY.json'));Cb=np.array(bases[c]['C']);Js=[]
   for m in geom['fit_pnp_inliers']:
    J=[]
    for k in range(6):
     q=np.zeros(6);q[k]=1e-5;a=projection(np.array(m['X'])[None],exp(q)@Cb,K0)[0][0];q[k]=-1e-5;b=projection(np.array(m['X'])[None],exp(q)@Cb,K0)[0][0];J.append((a-b)/2e-5)
    Js.append(np.array(J).T)
   sv=np.linalg.svd(np.concatenate(Js),compute_uv=False);ranks.append(dict(group=g,id=c,initial_RGB_rank6=int((sv>sv[0]*1e-5).sum())==6,condition=float(sv[0]/sv[-1]),precondition_10inliers=True,rank_checked_retrospectively_from_frozen_initial_state=True,not_claimed_preregistered_rank_gate=True))
  for v in vs:
   if v['role']!='HOLDOUT':continue
   orig=v.get('initial_pose')
   if orig is None:hod.append(dict(group=g,id=v['id'],status='MISSING_ORIGINAL_HOLDOUT_POSE',unit='mm'));continue
   base=np.array(orig);C=h@base if v['video']=='005'else base;ob=observe(v);e=None
   if g=='G01'and v['video']=='005':geom=pnp_bank(v,'005') # diagnostic solve output never used as camera
   else:
    ff=features(v);mp=rgb_map(g);mm=mutual(mp['des'],ff['des']);matches=[dict(landmark=k,X=mp['X'][k],uv=ff['xy'][j],role='FEATURE_HELD')for k,j,d in mm];geom=dict(matches=matches,fit_pnp_inliers=[])
   e=errors(v|dict(evaluation_map_H=h),C,geom);hod.append(dict(group=g,id=v['id'],video=v['video'],status='EVALUATION_ONLY_FROZEN_LEGACY_CAMERA_PLUS_SHARED_H',legacy_camera_conditional=True,new_HOLDOUT_local_fit_used=False,Ring=physical(v,C,ob),RGB=e,C=C,GT=False))
  if g=='G01':
   for p in load(Q/'config/G01_PHOTO_POSES.json'):
    v=next(v for v in vs if v['id']==p['id']);C=np.array(p['C']);geom=load(v.get('rgb_geometry_path',N/'inputs'/v['id']/'RGB_GEOMETRY.json'));H21=np.array(load(P/'results/B3.json')['T']);H0=np.array(load(U/'config/H0.json')['G01_005_to004']);histphotos.append(dict(id=v['id'],method='HISTORICAL_021_QUICK_NUMERIC_PHOTO',Ring=physical(v,C,observe(v)),RGB=errors(v|dict(evaluation_map_H=H21@np.linalg.inv(H0)),C,geom),source=asset(Q/'config/G01_PHOTO_POSES.json'),same_actual_photo_data=True,metric_camera_truth=False))
 save('metrics/HOLDOUT_CAMERA_ONLY_AUDIT.json',hod);table('metrics/HOLDOUT_CAMERA_ONLY_AUDIT.csv',hod);save('metrics/G01_HISTORICAL_PHOTO_SAME_DATA_EVALUATION.json',histphotos);save('metrics/EXACT_SOURCE_GAUGE_CANONICALIZATION.json',gauge);save('metrics/ACTUAL_RELEASED_CAMERA_INITIAL_RANKS.json',ranks);print('POST_FREEZE_AUDIT',len(hod),'held',len(ranks),'initial rank checks',sum(r['initial_RGB_rank6']for r in ranks),flush=True)
 # E4 fixed common original native pixel sets and common visibility, no selection.
 comp=[]
 for g in GROUPS:
  new=new_sources(g);conf,old=frozen_sources(g,False);ringm=np.load(conf['ring']['path']);ring=scene(ringm['V'],ringm['F'])
  for b in [s for s in new if s['variant']!='GEOMETRIC3']:
   a=next(s for s in new if s['id']==b['source']['view_id']);common,ia,ib=np.intersect1d(a['obs']['pixel_id'],b['obs']['pixel_id'],return_indices=True);aa=a|dict(X=a['X'][ia]);bb=b|dict(X=b['X'][ib]);d0=[];d1=[];nk0=nk1=0;den=0;su0=su1=0
   for t in [x for x in old if x['role']=='HOLDOUT']:
    r0=multivis(aa,t,ring);r1=multivis(bb,t,ring);co=r0['known']&r1['known'];d0.extend(r0['dz'][co]);d1.extend(r1['dz'][co]);nk0+=int(r0['known'].sum());nk1+=int(r1['known'].sum());den+=len(common);su0+=int(r0['supported'].sum());su1+=int(r1['supported'].sum())
   comp.append(dict(group=g,target=a['id'],fixed_common_native_pixel_N=len(common),fixed_ordered_native_pair_N=den,common_visible_pair_N=len(d0),NEW_GEOMETRIC3_common_depth_mm=stats(d0),OLD018_LITERAL3_common_depth_mm=stats(d1),NEW_known_N=nk0,OLD_known_N=nk1,NEW_support_N=su0,OLD_support_N=su1,not_GT=True,decision_only_no_training_or_pose_selection=True))
 save('metrics/E4_FIXED_COMMON_NATIVE_PIXEL_COMPARISON.json',comp);print('E4_FIXED_COMMON_DONE',len(comp),flush=True)
if __name__=='__main__':main()
