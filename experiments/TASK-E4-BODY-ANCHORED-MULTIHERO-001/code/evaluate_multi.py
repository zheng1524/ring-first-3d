"""Independent evaluation AFTER all predictions freeze; never imported by optimizer."""
from native_multi import *
from safe_geometry import dense_face_distance,self_intersections
import ast
from scipy.spatial import ConvexHull
P18=REPO/'experiments/TASK-E4-HERO-BODY-ADAPT-018'

def iou(a,b):return float((a&b).sum()/max(1,(a|b).sum()))
def pixerr(a,b):
 ca,cb=contour(a),contour(b)
 if not len(ca)or not len(cb):return None
 return float(.5*(cKDTree(ca).query(cb)[0].mean()+cKDTree(cb).query(ca)[0].mean()))
def measurement(V,F,plane):
 n=np.array(plane[:3]);n/=np.linalg.norm(n);axis=np.cross(n,[1,0,0])
 if np.linalg.norm(axis)<.1:axis=np.cross(n,[0,1,0])
 axis/=np.linalg.norm(axis);other=np.cross(n,axis);xy=V@np.c_[axis,other];hull=ConvexHull(xy);p=xy[hull.vertices];dxy=np.sqrt(((p[:,None]-p[None])**2).sum(2)).max();height=V@n+plane[3];m=trimesh.Trimesh(V,F,process=False);si=self_intersections(V,F)['intersections'];vol=abs(m.volume)if m.is_watertight and m.is_winding_consistent and not si else None
 return dict(Dxy_model_mm=float(dxy),estimated_base_Hmax_mm=float(height.max()),estimated_base_H95_mm=float(np.quantile(height,.95)),base_height_status='CONDITIONAL_FROZEN_BACKGROUND_PLANE_NOT_GT',area_solid_mm2=float(m.area),volume_conditional_mm3=vol,volume_status='CONDITIONAL_CLOSED_INFERRED_BACK_OR_CAP'if vol is not None else'NOT_EVALUABLE',watertight=m.is_watertight,winding_consistent=m.is_winding_consistent,self_intersections=si,components=len(m.split(only_watertight=False)))

def main():
 frozen=load(R/'provenance/PREDICTIONS_FROZEN.json');assert frozen['completed']==16
 for a in frozen['files']:assert sha(a['path'])==a['sha256']
 src=REPO/'experiments/TASK-E4-RING-ANCHORED-JOINT-BA-021/code/evaluate020.py';node=next(n for n in ast.parse(src.read_text()).body if isinstance(n,ast.FunctionDef)and n.name=='visibility_query');ns=dict(np=np,o3d=o3d);exec(compile(ast.get_source_segment(src.read_text(),node),str(src),'exec'),ns);visibility=ns['visibility_query'];records=[];per=[];bias=[];pairs=[];corrs=[];holdrows=[];pool={}
 for g in CFG['groups']:
  ss=[Source(s)for s in load(R/'config/SOURCES.json')if s['group']==g];initial=np.load(R/'inputs'/g/'INITIAL.npz');V0,F=initial['V'],initial['F'];Fs=initial['F_solid'];rv=np.load(R/'inputs'/g/'RING.npz');ring=scene(rv['V'],rv['F']);plane=load(R/'inputs'/g/'BASE_SELECTION.json')['selected_plane'];normalization=load(R/'inputs'/g/'NORMALIZATION.json');source_weights(ss,np.array(normalization['center']));oldactive={};meta=load(P18/'inputs'/g/'ALL_VIEW_META.json');caches={}
  for v in meta['views']:
   p=P18/'inputs'/g/(v['id']+'.npz')
   if not p.exists():p=P18/'holdout'/g/(v['id']+'.npz')
   if not p.exists():continue
   a=dict(np.load(p));h,w=a['labels'].shape;caches[v['id']]=dict(v=v,a=a,cad=cast(ring,a['K'],a['T'],h,w))
  held=[Source(dict(id='HOLDOUT__'+v['id'],mesh=str(P18/'holdout/hero'/v['id']/'TRUSTED_HERO.npz'),obs=str(P18/'holdout/hero'/v['id']/'OBS_TRUSTED.npz'),pack=load(P18/'holdout/hero'/v['id']/'SOURCE.json')['pack'],root=str(P18/'holdout/hero'/v['id']),source=str(P18/'holdout/hero'/v['id']/'SOURCE.json'),parent_sha=[]))for v in meta['views']if v['role']!='FIT']
  for arm in CFG['arms']:
   out=np.load(R/'runs'/g/arm/'FINAL.npz');V=out['V'];body=scene(V,F);names=list(out['source_ids']);theta=out['theta'];allareas=[];spatial=[];hitN=0;NN=0;errsum=0;rawerrsum=0;fixedsum=0;rawfixed=0;active_errors=[];raw_errors=[];matched=0;unexplained=0;conflict=0;unknown=0;common=0;added=0;lost=0
   for s in ss:s.theta=theta[names.index(s.id)]
   peer_conflicts(ss,ring)
   for s in ss:
    cr=correspond(s,V,F,body,ring,full=True);ii=cr['index'];act=cr['hit']&cr['known']&(cr['z']<cr['cad_z']-.05);err=cr['z']-(s.z0+s.A@s.theta);rawerr=cr['z']-s.z0;n=len(ii);nh=int(act.sum());hitN+=nh;NN+=n;errsum+=abs(err[act]).sum();rawerrsum+=abs(rawerr[act]).sum();pen=np.where(act,np.minimum(abs(err),10.),10.);fixedsum+=pen.sum();rawfixed+=np.where(act,np.minimum(abs(rawerr),10.),10.).sum();active_errors.append(err[act]);raw_errors.append(rawerr[act])
    if arm=='B0':oldactive[s.id]=act.copy()
    cm=int((act&oldactive[s.id]).sum());ad=int((act&~oldactive[s.id]).sum());lo=int((~act&oldactive[s.id]).sum());common+=cm;added+=ad;lost+=lo;counts={k:int((cr['state']==i).sum())for i,k in enumerate(['MATCHED','UNEXPLAINED','CONFLICT','UNKNOWN'])};matched+=counts['MATCHED'];unexplained+=counts['UNEXPLAINED'];conflict+=counts['CONFLICT'];unknown+=counts['UNKNOWN'];dV=s.vertices();ar=trimesh.triangles.area(dV[s.m['F']]);allareas.append(ar.sum());spatial.append(s.points()[::max(1,len(s.uv)//4096)]);rec=dict(group=g,arm=arm,source=s.id,video=s.rec['video'],N=n,hit_N=nh,hit_ratio=nh/n,miss_N=n-nh,common_hit_B0=cm,new_hit_B0=ad,lost_hit_B0=lo,fixed_penalty_10mm=float(pen.mean()),depth_corrected=stats(err[act]),depth_raw=stats(rawerr[act]),**counts,theta_mm=s.theta,max_axial_correction_mm=float(np.max(abs(s.A@s.theta))),trusted_faces=len(s.m['F']),trusted_original_area_mm2=s.rec['cleaning']['trusted_area_mm2'],trusted_deformed_area_mm2=float(ar.sum()),retained_face_ratio=1.,normal_sources='analytic inverse transpose of ray correction Jacobian');per.append(rec);np.savez_compressed(R/'local_results'/(g+'_'+arm+'_'+s.id+'_CORRESPONDENCE.npz'),native_pixel_id=s.o['pixel_id'],original_native_face_id=s.o['face_id'],state=cr['state'],body_face=cr['face'],distance_mm=cr['distance'],hit=act,depth_error_mm=err,raw_depth_error_mm=rawerr);bias.append(dict(group=g,arm=arm,source=s.id,b_mm=s.theta[0],a_mm=s.theta[1],c_mm=s.theta[2],max_depth_correction_mm=np.max(abs(s.A@s.theta))))
   # Original 018 holdout native sources: never bias corrected or used in fitting.
   for s in held:
    s.peer_conflict=np.zeros(len(s.uv),bool);cr=correspond(s,V,F,body,ring,full=True);active=cr['hit']&cr['known']&(cr['z']<cr['cad_z']-.05);e=cr['z']-s.z0;holdrows.append(dict(group=g,arm=arm,source=s.id,N=len(e),hit=int(active.sum()),miss=int((~active).sum()),depth=stats(e[active]),fixed_penalty_10mm=float(np.where(active,np.minimum(abs(e),10.),10.).mean())))
   views=[]
   for cid,a in caches.items():
    d=a['a'];h,w=d['labels'].shape;z=cast(body,d['K'],d['T'],h,w);pred=np.isfinite(z)&(z<a['cad']);target=d['labels']==1;row=dict(group=g,arm=arm,view=cid,role=a['v']['role'],IoU=iou(pred,target),symmetric_contour_px=pixerr(pred,target),N_pixels=h*w,foreground_N=int(target.sum()),CAD_occluded_body_N=int((np.isfinite(z)&(z>=a['cad'])).sum()));views.append(row);corrs.append(row)
   gridcells=np.unique(np.floor(np.concatenate(spatial)/.25).astype(int),axis=0);mm=measurement(V,Fs,plane);sd=dense_face_distance(ring,V,Fs,rv['V'],64,rv['F']);d=np.linalg.norm(V-V0,axis=1);tri=V[Fs];tri0=V0[Fs];ratio=trimesh.triangles.area(tri)/np.maximum(trimesh.triangles.area(tri0),1e-15);e=np.linalg.norm(tri[:,[1,2,0]]-tri,axis=2)/np.maximum(np.linalg.norm(tri0[:,[1,2,0]]-tri0,axis=2),1e-15)
   rec=dict(group=g,arm=arm,source_N=len(ss),fixed_N=NN,hit_N=hitN,hit_ratio=hitN/NN,miss_N=NN-hitN,matched_N=matched,unexplained_N=unexplained,conflict_N=conflict,unknown_N=unknown,common_hit_B0=common,new_hit_B0=added,lost_hit_B0=lost,depth_corrected_MAE_mm=errsum/max(1,hitN),depth_corrected_median_mm=stats(np.concatenate(active_errors))['median'],depth_corrected_p95_mm=stats(np.concatenate(active_errors))['p95'],depth_raw_MAE_mm=rawerrsum/max(1,hitN),fixed_penalty_10mm=fixedsum/NN,raw_fixed_penalty_10mm=rawfixed/NN,FIT_IoU=np.mean([v['IoU']for v in views if v['role']=='FIT']),HOLDOUT_IoU=np.mean([v['IoU']for v in views if v['role']!='FIT']),FIT_contour_px=np.mean([v['symmetric_contour_px']for v in views if v['role']=='FIT'and v['symmetric_contour_px']is not None]),max_displacement_mm=d.max(),mean_displacement_mm=d.mean(),min_area_ratio=ratio.min(),max_edge_stretch=e.max(),Ring64_min_mm=sd.min(),Ring64_faces_below_minus1um=int((sd<-.001).sum()),retained_original_faces_ratio=1.,cumulative_source_area_mm2=float(sum(allareas)),sampled_union_voxel_cells_025mm=len(gridcells),union_proxy_not_anatomical_area=True,**mm);records.append(rec);save('metrics/'+g+'_'+arm+'_EVALUATION.json',rec);print('EVAL',g,arm,'MAE',rec['depth_corrected_MAE_mm'],'fit',rec['FIT_IoU'],'hold',rec['HOLDOUT_IoU'],flush=True)
   # Fixed stratified native source samples, same ordered pairs in every arm.
   grids={}
   for t in ss:
    h,w=map(int,t.o['native_shape']);grid=np.full((h,w),np.nan);grid[t.uv[:,1],t.uv[:,0]]=t.z0+t.A@t.theta;grids[t.id]=grid
   for s in ss:
    X=s.points()[s.sub]
    for t in ss:
     if s.id==t.id:continue
     q=visibility(X,t.C,t.K,grids[t.id],ring);known=q['known'];tag='PHOTO_INVOLVED'if 'PHOTO'in[s.rec['video'],t.rec['video']]else'SAME_VIDEO'if s.rec['video']==t.rec['video']else'CROSS_VIDEO';pool.setdefault((g,arm,tag),[]).append(q['dz'][known]);er=stats(q['dz'][known]);pairs.append(dict(group=g,arm=arm,source=s.id,target=t.id,pair_type='PHOTO_INVOLVED'if 'PHOTO'in[s.rec['video'],t.rec['video']]else'SAME_VIDEO'if s.rec['video']==t.rec['video']else'CROSS_VIDEO',N=len(X),common_valid=int(known.sum()),supported=int(q['supported'].sum()),front_disagreement=int(q['front'].sum()),deeper_observation=int(q['behind'].sum()),CAD_occluded=int(q['cad_occluded'].sum()),UNKNOWN=int((~known).sum()),MAE_mm=er['MAE'],median_mm=er['median'],p95_mm=er['p95'],front_is_uncalibrated_proxy=True))
  print('GROUP_EVAL_DONE',g,flush=True)
 agg=[]
 for key,arr in pool.items():
  g,arm,tag=key;rr=[p for p in pairs if p['group']==g and p['arm']==arm and p['pair_type']==tag];agg.append(dict(group=g,arm=arm,pair_type=tag,**stats(np.concatenate(arr)),fixed_N=sum(p['N']for p in rr),common_N=sum(p['common_valid']for p in rr),supported=sum(p['supported']for p in rr),front=sum(p['front_disagreement']for p in rr),deeper=sum(p['deeper_observation']for p in rr),CAD_occluded=sum(p['CAD_occluded']for p in rr),UNKNOWN=sum(p['UNKNOWN']for p in rr)))
 save('metrics/HERO_PAIR_AGGREGATES.json',agg);table('metrics/HERO_PAIR_AGGREGATES.csv',agg)
 save('metrics/COMPARISON.json',records);table('metrics/COMPARISON.csv',records);save('metrics/SOURCE_GEOMETRY.json',per);table('metrics/SOURCE_GEOMETRY.csv',per);table('metrics/BIAS_PARAMETERS.csv',bias);table('metrics/PER_VIEW.csv',corrs);save('metrics/PER_VIEW.json',corrs);table('metrics/INDEPENDENT_HOLDOUT_HERO.csv',holdrows);save('metrics/INDEPENDENT_HOLDOUT_HERO.json',holdrows);table('metrics/HERO_PAIR_CONSISTENCY.csv',pairs);save('metrics/HERO_PAIR_CONSISTENCY.json',pairs)
if __name__=='__main__':main()
