from common import *
from evaluate import pointcast
from planes import compare
from scipy.ndimage import distance_transform_edt
import open3d as o3d

def basis(n):
 axis=np.eye(3)[np.argmin(abs(n))];u=np.cross(n,axis);u/=np.linalg.norm(u);return np.c_[u,np.cross(n,u),n]
def fit_plane(P,center):
 if len(P)<100:return None,[],0.
 o3d.utility.random.seed(0);pc=o3d.geometry.PointCloud(o3d.utility.Vector3dVector(P));plane,ids=pc.segment_plane(distance_threshold=.3,ransac_n=3,num_iterations=300);plane=np.array(plane);plane/=np.linalg.norm(plane[:3]);plane*=1 if center@plane[:3]+plane[3]>=0 else-1;return plane,np.array(ids,int),len(ids)/len(P)
def grid_native(a,dep):
 z=dep['depth_mm'];yy,xx=np.mgrid[:z.shape[0],:z.shape[1]];uv=np.c_[xx.ravel(),yy.ravel()];ray=np.c_[uv,np.ones(len(uv))]@np.linalg.inv(dep['Kn']).T;q=ray@a['K'].T;RGBuv=q[:,:2]/q[:,2:];px=np.clip(np.rint(RGBuv).astype(int),[0,0],[639,359]);X=(ray*z.ravel()[:,None])@a['T'][:3,:3].T+a['T'][:3,3];return uv,ray,RGBuv,px,X

def main():
 cfg=load(R/'config/PROTOCOL.json');cases=load(R/'config/CASE_LOCK.json');rows=[];base_rows=[];contact_rows=[]
 for c in cases:
  name=c['name'];root=R/'inputs'/name;rr=np.load(root/'RING.npz');rs=scene(rr['V'],rr['F']);observations=[];primary=next(v for v in c['views']if v['role']=='FIT'and v['HERO_source']);primary_id=primary['id'];primary_data=None
  for v in c['views']:
   if not v['HERO_source']:continue
   cid=v['id'];a=dict(np.load(root/(cid+'.npz')));dep=dict(np.load(root/(cid+'_DEPTH.npz')));uv,ray,rgbuv,px,X=grid_native(a,dep);z=dep['depth_mm'];lab=a['labels'];labels=lab[px[:,1],px[:,0]];valid=np.isfinite(z.ravel())&(z.ravel()>0);jump=np.zeros(z.shape)
   for ax in[0,1]:
    diff=abs(np.diff(z,axis=ax));s0=[slice(None)]*2;s1=s0.copy();s0[ax]=slice(None,-1);s1[ax]=slice(1,None);jump[tuple(s0)]=np.maximum(jump[tuple(s0)],diff);jump[tuple(s1)]=np.maximum(jump[tuple(s1)],diff)
   dt=distance_transform_edt(lab==1);dr=distance_transform_edt(lab!=2);dpoly=distance_transform_edt(lab!=1);classes=np.load(root/(cid+'_SIDES.npz'))['classes'];cad=cast(rs,dep['Kn'],a['T'],*z.shape).ravel();safe=valid&(labels==1)&(dt[px[:,1],px[:,0]]>=5)&(jump.ravel()<=.75)&(a['RGB'][px[:,1],px[:,0]].min(1)<245)&(z.ravel()<cad-.05);ix=np.flatnonzero(safe);ix=ix[np.linspace(0,len(ix)-1,min(256,len(ix))).astype(int)]if len(ix)else ix
   # Inherit fixed multiscale same-view pairing, not cross-view depth consistency.
   rng=np.random.default_rng(20261106);pairs=[];seen=set();tree=cKDTree(uv[ix])if len(ix)else None
   for scale in[4,16,48]:
    count=0
    for i in rng.permutation(len(ix)):
     ang=rng.uniform(0,2*np.pi);_,j=tree.query(uv[ix[i]]+scale*np.array([np.cos(ang),np.sin(ang)]));j=int(j);key=tuple(sorted([int(i),j]));gap=np.linalg.norm(uv[ix[i]]-uv[ix[j]])
     if key in seen or not(max(2,.5*scale)<=gap<=2*scale):continue
     line=np.rint(np.linspace(uv[ix[i]],uv[ix[j]],int(np.ceil(gap))+1)).astype(int);pp=np.c_[line,np.ones(len(line))]@np.linalg.inv(dep['Kn']).T@a['K'].T;pp=np.rint(pp[:,:2]/pp[:,2:]).astype(int);zz=z[line[:,1],line[:,0]]
     if not(lab[pp[:,1],pp[:,0]]==1).all()or not(np.isfinite(zz)&(zz>0)).all()or abs(np.diff(zz)).max()>.75:continue
     pairs.append(key);seen.add(key);count+=1
     if count>=64:break
   pairs=np.array(pairs,int).reshape(-1,2);np.savez_compressed(R/'depth_observations'/(cid+'.npz'),uv=uv[ix],pixel_id=ix,z=z.ravel()[ix],K=dep['Kn'],T=a['T'],weight=np.ones(len(ix)),pairs=pairs,pair_weight=np.ones(len(pairs)),native_shape=z.shape,RGB_uv=rgbuv[ix]);observations.append(dict(source=cid,role=v['role'],fixed_N=len(ix),pairs_N=len(pairs)));rows.append(dict(case=name,source=cid,role=v['role'],full_valid=int(valid.sum()),Polyp_N=int((valid&(labels==1)).sum()),interior_reliable_N=int(safe.sum()),fixed_N=len(ix),pair_N=len(pairs),raw_depth_same=True,Kn_pose_fixed=True))
   if cid==primary_id:primary_data=(a,dep,uv,px,X,valid,jump,cad,dt,dr,dpoly,classes,safe)
  a,dep,uv,px,X,valid,jump,cad,dt,dr,dpoly,classes,safe=primary_data;lab=a['labels'];label=lab[px[:,1],px[:,0]];pcloud=X[safe];center=np.median(pcloud,axis=0)if len(pcloud)else np.median(X[valid&(label==1)],axis=0);dist=dpoly[px[:,1],px[:,0]];Ringdist=dr[px[:,1],px[:,0]];bgqual=valid&(label==0)&(Ringdist>3)&(~np.isin(classes[px[:,1],px[:,0]],[1,2,4]))&(jump.ravel()<=.75)&(a['RGB'][px[:,1],px[:,0]].min(1)<245)&(dep['depth_mm'].ravel()<cad-.05);trials=[];points={}
  for upper in[30,45,60]:
   use=bgqual&(dist>=5)&(dist<=upper);ids=np.flatnonzero(use);ids=ids[np.linspace(0,len(ids)-1,min(5000,len(ids))).astype(int)]if len(ids)else ids;P=X[ids];plane,inliers,fraction=fit_plane(P,center);trials.append(dict(upper_px=upper,N=len(P),plane=plane,inlier_fraction=fraction,inlier_N=len(inliers),residual_mm=stats(P@plane[:3]+plane[3])if plane is not None else stats([])));points[upper]=(P,ids,inliers)
  good=[t for t in trials if t['plane']is not None];primary_trial=trials[1];plane=primary_trial['plane'];stability_angles=[];stability_offsets=[]
  if plane is not None:
   for t in good:
    aligned,angle,offset=compare(t['plane'],plane,center);t['plane']=aligned;stability_angles.append(angle);stability_offsets.append(offset)
  status='RELIABLE'if plane is not None and len(good)==3 and all(t['N']>=100 and t['inlier_fraction']>=.5 for t in trials)and max(stability_angles)<=10 and max(stability_offsets)<=.5 else'WEAK'if plane is not None else'UNOBSERVABLE'
  # Contact is measured from data only; no P0 is opened for this decision.
  contourmask=(lab==1)&(cv2.erode((lab==1).astype(np.uint8),np.ones((3,3),np.uint8))==0);native_contour=contourmask[px[:,1],px[:,0]];eligible=valid&(label==1)&(dt[px[:,1],px[:,0]]>=2)&(dt[px[:,1],px[:,0]]<=6)&(Ringdist>4)&(jump.ravel()<=.75)&(~np.isin(classes[px[:,1],px[:,0]],[1,2,4]));ci=np.flatnonzero(eligible);contact=np.zeros(len(ci),bool);distplane=np.full(len(ci),np.nan)
  if plane is not None and len(ci)and len(points[45][0]):
   distplane=X[ci]@plane[:3]+plane[3];near=cKDTree(points[45][0]).query(X[ci])[0];contact=(abs(distplane)<=.5)&(near<=1.)
  fraction=float(contact.mean())if len(ci)else 0.;contact_status='BROAD'if len(ci)>=20 and fraction>=.3 else'SMALL'if len(ci)>=20 and fraction<.1 else'UNCERTAIN';apply=status=='RELIABLE'and contact_status=='BROAD'
  if plane is not None:Q=basis(plane[:3]);anchor=center-(center@plane[:3]+plane[3])*plane[:3]
  else:Q=np.eye(3);anchor=np.full(3,np.nan)
  P,ids,inliers=points[45];np.savez_compressed(root/'BASE_EVIDENCE.npz',background_XYZ=P,background_native_ID=ids,background_RGB=a['RGB'][px[ids,1],px[ids,0]],plane=np.full(4,np.nan)if plane is None else plane,Q=Q,anchor=anchor,Polyp_internal_XYZ=pcloud,contact_XYZ=X[ci],contact=contact,contact_native_ID=ci,contact_distance_mm=distplane,background_RGB_uv=np.c_[uv[ids],np.ones(len(ids))]@np.linalg.inv(dep['Kn']).T@a['K'].T)
  result=dict(case=name,primary=primary_id,base_status=status,plane=plane,primary_ROI=[5,45],trials=trials,max_normal_change_deg=max(stability_angles)if stability_angles else None,max_anchor_offset_change_mm=max(stability_offsets)if stability_offsets else None,contact_status=contact_status,contact_N=len(ci),contact_supported_N=int(contact.sum()),contact_fraction=fraction,truncate_allowed=apply,plane_basis=Q,anchor=anchor,base_independent_of_Ring_plane=True,P0_used_for_contact=False,camera_historical_tag_not_used_for_base_status=True);save('inputs/'+name+'/BASE.json',result);base_rows.append(result);contact_rows.append(dict(case=name,status=contact_status,N=len(ci),supported_N=int(contact.sum()),fraction=fraction,truncate=apply));print('BASE',name,status,contact_status,fraction,flush=True)
 table('metrics/DEPTH_INPUT_AUDIT.csv',rows);save('metrics/BASE_QUALIFICATION.json',base_rows);table('metrics/BASE_QUALIFICATION.csv',base_rows);table('metrics/CONTACT_QUALIFICATION.csv',contact_rows)
if __name__=='__main__':main()
