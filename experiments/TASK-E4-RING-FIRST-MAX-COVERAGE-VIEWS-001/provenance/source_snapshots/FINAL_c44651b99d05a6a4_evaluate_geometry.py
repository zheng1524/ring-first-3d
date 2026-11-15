"""Post-freeze native HERO evidence; full fixed native pixel sets, no ICP/fusion."""
from geometry_io import *
from coverage import direction_stats

def new_sources(g):
 out=[]
 for rec in load(N/'metrics/HERO_INFERENCE_RESULTS.json'):
  if rec['group']!=g or not rec['success']:continue
  root=N/'hero_fit'/rec['id'];cl=load(root/'CLEANING.json')
  if not cl['success']:continue
  m=dict(np.load(root/'TRUSTED_HERO.npz'));a=dict(np.load(root/'OBS_TRUSTED.npz'));out.append(dict(id=rec['id'],video=next(v['video']for v in load(camera_file(g))if v['id']==rec['view_id']),role='FIT',V=m['V'],F=m['F'],C=a['T'],K=a['K'],mesh=m,obs=a,source=rec,normal=a['normal'],X=a['X'],D=np.eye(4),rank=rec['rank'],variant=rec['variant'],clean=cl))
 return out

def normal_error(a,b,r):
 uv,z=projection(a['X'],b['C'],b['obs']['K']);p=np.floor(np.nan_to_num(uv,nan=-1e9,posinf=-1e9,neginf=-1e9)+.5).astype(int);shape=tuple(b['obs']['native_shape']);ng=np.full((*shape,3),np.nan);ng[b['obs']['uv'][:,1],b['obs']['uv'][:,0]]=b['normal'];inside=(p[:,0]>=0)&(p[:,0]<shape[1])&(p[:,1]>=0)&(p[:,1]<shape[0]);nb=np.full_like(a['normal'],np.nan);nb[inside]=ng[p[inside,1],p[inside,0]];nn=np.linalg.norm(a['normal'],axis=1)*np.linalg.norm(nb,axis=1);ang=np.degrees(np.arccos(np.clip(abs((a['normal']*nb).sum(1))/np.maximum(nn,1e-12),0,1)));return stats(ang[r['supported']])

def surfel_bins(sources):
 keys=[];area=[];sid=[]
 for i,s in enumerate(sources):
  tri=s['V'][s['F']];Nn=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);a=np.linalg.norm(Nn,axis=1)/2;Nn/=np.maximum(2*a[:,None],1e-15);Nn*=np.sign(Nn[np.arange(len(Nn)),np.argmax(abs(Nn),axis=1)])[:,None];keys.append(np.c_[np.floor(tri.mean(1)/.2).astype(int),np.rint(Nn/.5).astype(int)]);area.append(a);sid.append(np.full(len(a),i))
 if not keys:return dict(keys=np.empty((0,6)),weight=np.empty(0),counts=np.empty(0))
 key=np.concatenate(keys);ar=np.concatenate(area);si=np.concatenate(sid);uni,inv=np.unique(key,axis=0,return_inverse=True);w=np.zeros(len(uni));count=np.zeros(len(uni),int)
 for i in range(len(sources)):
  a=np.bincount(inv[si==i],weights=ar[si==i],minlength=len(uni));w+=a;count+=a>0
 w/=np.maximum(count,1);return dict(keys=uni,weight=w,counts=count)

def geometry_summary():
 allpairs=[];score=[];source_rows=[];countrows=[];sourcecontr=[];E4=[];photo=[]
 for g in GROUPS:
  conf,old=frozen_sources(g);_,auditold=frozen_sources(g,False);new=new_sources(g);main=[s for s in new if s['variant']=='GEOMETRIC3'];allS=old+main;rv=np.load(conf['ring']['path']);ring=scene(rv['V'],rv['F']);unions={};pernew={};dzscope=collections.defaultdict(list);oldkeys=surfel_bins(old);oldset=set(map(tuple,oldkeys['keys']));pr=np.load(selpath(g,'_PROXY.npz'));vis=np.load(selpath(g,'_VISIBILITY.npz'));selected=load(selpath(g,'_SELECTION.json'));views={v['id']:v for v in load(camera_file(g))};Ns=[8,12,20,28,36];local=N/'evaluation'/g;local.mkdir(exist_ok=True)
  for s in allS:
   ar=trimesh.triangles.area(s['V'][s['F']]);source_rows.append(dict(group=g,id=s['id'],origin='NEW_NATIVE'if any(x is s for x in main) else'OLD_FROZEN_FIT',video=s['video'],rank=s.get('rank'),TRUSTED_faces=len(ar),cumulative_source_area_mm2=float(ar.sum()),native_TRUSTED_observations=len(s['X']),unchanged_original_vertex_coords=True,not_unique_anatomical_area=True))
  for a in main:
   acc={k:np.zeros(len(a['X']),bool)for k in ['known','supported','front','behind','cad_occluded']};dzs=[];normals=[]
   for b in allS+ [b for b in auditold if b['role']=='HOLDOUT' or b['source'].get('evaluation_only',False)]:
    if a is b:continue
    r=multivis(a,b,ring);scope='PROTECTED_HOLDOUT'if b['role']=='HOLDOUT'else'RESERVED_OLD005_EVALUATION'if b['source'].get('evaluation_only',False)else'NEW_NEW'if any(x is b for x in main) else'NEW_OLD_FIT';nn=normal_error(a,b,r);row=dict(group=g,source=a['id'],target=b['id'],scope=scope,source_video=a['video'],target_video=b['video'],fixed_native_pixel_N=len(a['X']),known_N=int(r['known'].sum()),same_layer_N=int(r['supported'].sum()),front_disagreement_N=int(r['front'].sum()),deeper_possible_self_occlusion_N=int(r['behind'].sum()),CAD_occluded_N=int(r['cad_occluded'].sum()),unknown_N=int((~r['known']&~r['cad_occluded']).sum()),target_CAD_order_unreliable_N=int(r['target_Ring_order_unreliable'].sum()),depth_mm=stats(r['dz'][r['known']]),supported_normal_deg=nn,within_0p2_N=int((r['known']&(abs(r['dz'])<=.2)).sum()),within_0p5_N=int((r['known']&(abs(r['dz'])<=.5)).sum()),within_1p0_N=int((r['known']&(abs(r['dz'])<=1)).sum()),not_GT=True);allpairs.append(row);dzscope[scope].append(r['dz'][r['known']])
    if scope=='NEW_OLD_FIT':
     for k in acc:acc[k]|=r[k]
     dzs.extend(r['dz'][r['known']]);normals.append(nn)
   cls=np.full(len(a['X']),4,np.uint8);cls[acc['cad_occluded']&~acc['known']]=3;cls[acc['behind']&~acc['supported']]=2;cls[acc['front']&~acc['supported']]=1;cls[acc['supported']]=0;cls[acc['supported']&acc['front']]=5;np.savez_compressed(local/(a['id']+'_EVIDENCE.npz'),X=a['X'],native_pixel_id=a['obs']['pixel_id'],original_face_id=a['obs']['face_id'],class_id=cls,**acc);pernew[a['id']]=dict(N=len(a['X']),supported=int(acc['supported'].sum()),known=int(acc['known'].sum()),front=int(acc['front'].sum()),behind=int(acc['behind'].sum()),cad=int(acc['cad_occluded'].sum()),unknown=int((~acc['known']&~acc['cad_occluded']).sum()),depth_mm=stats(dzs));
  for n in Ns:
   use=[s for s in main if s['rank']<=n];union=surfel_bins(old+use);isnew=np.array([tuple(k)not in oldset for k in union['keys']]);cnt=dict(group=g,requested_target_N=n,actual_target_N=len(use),new_inferences_N=len(use),old_FIT_sources_N=len(old),cumulative_new_TRUSTED_area_mm2=sum(float(trimesh.triangles.area(s['V'][s['F']]).sum())for s in use),dedup_area_proxy_mm2=float(union['weight'].sum()),dedup_new_bin_area_proxy_mm2=float(union['weight'][isnew].sum()),original_proxy_mm2=float(oldkeys['weight'].sum()),new_surface_bins=int(isnew.sum()),new_bins_require_visibility_support_not_implied_true=True,HERO_unique_source_fixed_N=sum(pernew[s['id']]['N']for s in use),HERO_unique_support_N=sum(pernew[s['id']]['supported']for s in use),HERO_unique_front_N=sum(pernew[s['id']]['front']for s in use),HERO_unique_deeper_N=sum(pernew[s['id']]['behind']for s in use),HERO_unique_unknown_N=sum(pernew[s['id']]['unknown']for s in use),counts_overlap_across_targets=False,area_is_surfel_proxy_not_anatomical=True,requested_available=len(use)==n);countrows.append(cnt)
  for filtername,allowed in [('004',['004']),('004+005',['004','005']),('004+005+PHOTO',['004','005','PHOTO'])]:
   use=[s for s in main if s['video']in allowed];uu=surfel_bins(old+use);novel=np.array([tuple(k)not in oldset for k in uu['keys']]);sourcecontr.append(dict(group=g,sources=filtername,new_targets_N=len(use),new_area_bins_proxy_mm2=float(uu['weight'][novel].sum()),all_bins_area_proxy_mm2=float(uu['weight'].sum()),fixed_rank_selection=True,no_GT=True))
  for s in [s for s in new if s['variant']!='GEOMETRIC3']:
   target=s['source']['view_id'];a=next((x for x in main if x['id']==target),None)
   if a is None:continue
   za=np.load(a['source']['native'])['depth_mm'];zb=np.load(s['source']['native'])['depth_mm'];mask=np.asarray(Image.open(N/'hero_fit'/s['id']/'NATIVE_LABELS.png'))==1;dd=za[mask]-zb[mask];rr=[]
   for tag,x in [('NEW_GEOMETRIC3',a),('OLD018_LITERAL3',s)]:
    errs=[];known=0;support=0;den=0
    for b in auditold:
     if b['role']!='HOLDOUT':continue
     r=multivis(x,b,ring);errs.extend(r['dz'][r['known']]);known+=int(r['known'].sum());support+=int(r['supported'].sum());den+=len(x['X'])
    rr.append(dict(method=tag,depth_to_protected_HERO_mm=stats(errs),fixed_pair_pixel_N=den,known_N=known,same_layer_N=support,TRUSTED_area_mm2=float(trimesh.triangles.area(x['V'][x['F']]).sum()),native_TRUSTED_N=len(x['X'])))
   E4.append(dict(group=g,target=target,native_target_pixel_N=int(mask.sum()),paired_depth_difference_mm=stats(dd),same_frozen_target_camera=True,comparisons=rr,GT_accuracy='NOT_EVALUABLE'))
  for scope in ['NEW_OLD_FIT','NEW_NEW','PROTECTED_HOLDOUT','RESERVED_OLD005_EVALUATION']:
   rows=[r for r in allpairs if r['group']==g and r['scope']==scope];den=sum(r['fixed_native_pixel_N']for r in rows);kn=sum(r['known_N']for r in rows);rec=dict(group=g,scope=scope,old_FIT_sources_N=len(old),old_all_sources_N=len(auditold),new_HERO_sources_N=len(main),ordered_pairs_N=len(rows),fixed_native_pair_pixel_N=den,known_N=kn,same_layer_N=sum(r['same_layer_N']for r in rows),front_N=sum(r['front_disagreement_N']for r in rows),deeper_possible_occlusion_N=sum(r['deeper_possible_self_occlusion_N']for r in rows),CAD_occluded_N=sum(r['CAD_occluded_N']for r in rows),unknown_N=sum(r['unknown_N']for r in rows),depth_MAE_mm=sum(r['depth_mm']['MAE']*r['depth_mm']['N']for r in rows if r['depth_mm']['N'])/kn if kn else None,depth_median_mm=None,depth_p95_mm=None,median_p95_not_reconstructed_from_pair_aggregates=True,normal_macro_supported_MAE_deg=float(np.mean([r['supported_normal_deg']['MAE']for r in rows if r['supported_normal_deg']['N']]))if any(r['supported_normal_deg']['N']for r in rows)else None,within_0p2_N=sum(r['within_0p2_N']for r in rows),within_0p5_N=sum(r['within_0p5_N']for r in rows),within_1p0_N=sum(r['within_1p0_N']for r in rows),not_GT=True);pooled=stats(np.concatenate(dzscope[scope])if dzscope[scope]else[]);rec.update(depth_median_mm=pooled['median'],depth_p95_mm=pooled['p95'],depth_max_mm=pooled['maximum'],median_p95_not_reconstructed_from_pair_aggregates=False);score.append(rec)
  save('evaluation/'+g+'/PER_SOURCE_UNION.json',pernew);print('GEOMETRY_EVALUATED',g,len(main),'realnew','pairs',sum(r['group']==g for r in allpairs),flush=True)
 table('HERO_COVERAGE_AND_CONFLICT_SCORECARD.csv',score);save('metrics/HERO_COVERAGE_AND_CONFLICT_SCORECARD.json',score);table('metrics/HERO_PER_NATIVE_PAIR.csv',allpairs);save('metrics/HERO_PER_NATIVE_PAIR.json',allpairs);table('metrics/HERO_NATIVE_SOURCE_AREAS.csv',source_rows);save('metrics/HERO_COUNT_ACTUAL_COVERAGE.json',countrows);table('metrics/HERO_COUNT_ACTUAL_COVERAGE.csv',countrows);save('metrics/HERO_SOURCE_ACTUAL_CONTRIBUTIONS.json',sourcecontr);table('metrics/HERO_SOURCE_ACTUAL_CONTRIBUTIONS.csv',sourcecontr);save('metrics/E4_ACTUAL_SUPPORT_STRATEGY_COMPARISON.json',E4)
if __name__=='__main__':geometry_summary()
