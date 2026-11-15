from prepare_controls import triangulate_grid,face_normals_grid
from resection import *

def main():
 root=R/'controls';cfg=load(root/'SCENE.json');views={v['id']:v for v in cfg['views']};fit=[v for v in cfg['views']if v['role']=='FIT'];refs=[]
 for v in cfg['views']:
  a=np.load(root/'inputs'/(v['id']+'_BASE.npz'));rgb=np.array(Image.open(root/'inputs'/(v['id']+'_RGB.png')).convert('RGB'));path=root/'inputs'/(v['id']+'_FRAME.npz');np.savez_compressed(path,RGB=rgb,labels=a['labels'],K=a['K'],C=a['C']);features('CTRL_IMAGE__'+v['id'],path)
  if v['role']=='FIT':refs.append(dict(id=v['id'],cache=str(path),C=np.array(v['C']),K=np.array(v['K'])))
 perturbs={};H=np.eye(4);perturbs['C0_ZERO']=(H,0.,None);perturbs['C1_DEPTH']=(H,3.,None);H2=pose_delta(np.r_[[1.5,-1.,.75],np.radians([5,-4,7])]);perturbs['C2_POSE']=(H2,0.,None);H3=yaw(35);H3[:3,3]=[8,-6,3];perturbs['C3_FAR']=(H3,0.,None);perturbs['C4_LEFT']=(np.eye(4),0.,'left');perturbs['C4_RIGHT']=(np.eye(4),0.,'right');records=[];truth=[]
 for name,(Hb,bias,part)in perturbs.items():
  view='IIa6.5_R10_obs04'if part=='right'else'IIa6.5_R10_obs00';base=np.load(root/'inputs'/(view+'_BASE.npz'));frame=np.load(root/'inputs'/(view+'_FRAME.npz'));K=base['K'];Ct=base['C'];z=base['z'];mask=base['labels']==1;X,F,uv,pix,N=triangulate_grid(z,mask,K,Ct);trueX=X.copy();original_face=np.arange(len(F));
  if part:
   keep=X[:,0]<-.5 if part=='left'else X[:,0]>.5;oldF=F.copy();good=keep[F].all(1);mapping=np.full(len(X),-1);mapping[keep]=np.arange(keep.sum());F=mapping[F[good]];original_face=original_face[good];X=X[keep];trueX=trueX[keep];uv=uv[keep];pix=pix[keep];N=N[keep]
  rays0=rays(Ct,K,uv)[:,3:];zz=z.ravel()[pix]+bias
  if bias:X=Ct[:3,3]+rays0*zz[:,None];N=face_normals_grid(X,F)
  X=transform(X,Hb);N=N@Hb[:3,:3].T;C=Hb@Ct;folder=root/'inputs'/name;folder.mkdir(exist_ok=True);mesh=folder/'RAW_IDEAL_SURFACE.npz';np.savez_compressed(mesh,V=X,F=F,original_face_id=original_face,uv=uv,K=K,T=C);obs=folder/'OBS.npz';h,w=z.shape;cad=rayquery(scene(np.load(root/'inputs/RING.npz')['V'],np.load(root/'inputs/RING.npz')['F']),C,K,uv)['t_hit'];np.savez_compressed(obs,X=X,z=zz,uv=uv,pixel_id=pix,normal=N,K=K,T=C,native_shape=[h,w],cad_z=cad,weight=np.ones(len(X)),face_id=np.zeros(len(X),int));e=ellipse_descriptor(base['labels']==1);q=ellipse_coords(uv,e);eligible=np.linalg.norm(q,axis=1)<=CFG['region_core_radius'];ids=sample_spatial(np.flatnonzero(eligible),q[eligible],CFG['region_anchors']);cache=folder/'FRAME.npz';np.savez_compressed(cache,RGB=frame['RGB'],labels=base['labels'],K=K,C=C,uv=uv,q=q,anchor_index=ids,ellipse_center=e['center'],ellipse_axes=e['axes'],ellipse_U=e['U']);rec=dict(id=name,group='CONTROL',video='VIRTUAL',view_id=view,obs=str(obs),mesh=str(mesh),view_cache=str(cache),C=C,K=K,ring_path=str(root/'inputs/RING.npz'),depth_type='IDEAL_GT_DEPTH_UPPER_BOUND',raw_shape_fixed=True);records.append(rec);np.savez_compressed(root/'audit_only'/(name+'_TRUE.npz'),X=trueX,C=Ct,H_bad=Hb,depth_bias_mm=bias,uv=uv,pixel_id=pix);truth.append(dict(control=name,rotation_deg=pose_difference(Hb,np.eye(4))['rotation_deg'],translation_mm=float(np.linalg.norm(Hb[:3,3])),axial_bias_mm=bias,part=part,truth=str(root/'audit_only'/(name+'_TRUE.npz'))))
  fs=features('CTRL_IMAGE__'+view,root/'inputs'/(view+'_FRAME.npz'));matches=[]
  for ref in refs:
   ff=features('CTRL_IMAGE__'+ref['id'],ref['cache']);mm=match_desc(fs['des'],ff['des']);p=fs['xy'][mm[:,0]];q0=ff['xy'][mm[:,1]];rng=np.random.default_rng(int(hashlib.sha256((view+ref['id']+str(CFG['seed'])).encode()).hexdigest()[:8],16));ii=rng.permutation(len(mm));cut=int(len(ii)*CFG['sift_fit_fraction']);fi,he=ii[:cut],ii[cut:];flag=np.zeros(len(fi),bool)
   if len(fi)>=8:
    cv2.setRNGSeed(CFG['seed'])
    try:fund,flag0=cv2.findFundamentalMat(p[fi],q0[fi],cv2.USAC_MAGSAC,CFG['sift_MAGSAC_px'],.999,10000);flag=flag0.ravel().astype(bool)if flag0 is not None else flag
    except cv2.error:pass
   good=fi[flag];good=good[np.linspace(0,len(good)-1,min(CFG['sift_max_pair_points'],len(good)),dtype=int)]if len(good)else good;fitpath=folder/(ref['id']+'_FIT.npz');fullpath=folder/(ref['id']+'_ALL.npz');np.savez_compressed(fitpath,p=p[good],q=q0[good]);np.savez_compressed(fullpath,p=p,q=q0,index_pairs=mm,FIT_index=good,HOLDOUT_index=he);matches.append(dict(reference=ref['id'],ref_C=ref['C'],ref_K=ref['K'],fit_match=str(fitpath),match=str(fullpath),FIT_N=len(good),HOLDOUT_N=len(he)))
  rec['references']=matches;print('CONTROL_READY',name,len(X),sum(m['FIT_N']for m in matches),flush=True)
 save('controls/SOURCES.json',records);save('controls/audit_only/KNOWN_PERTURBATIONS.json',truth);save('controls/CONTROL_PROTOCOL.json',dict(cases=['C0_ZERO','C1_DEPTH','C2_POSE','C3_FAR','C4_LEFT','C4_RIGHT'],C1_depth_mm=3.,C2_rotvec_deg=[5,-4,7],C2_t_mm=[1.5,-1,.75],C3_yaw_deg=35,C3_t_mm=[8,-6,3],C4='true distinct left/right patches from two actual cameras, no invented shared correspondences',zero_drift_tolerance_mm=.1,zero_drift_tolerance_deg=1.,control_GT_not_used_real_fit=True))
if __name__=='__main__':main()
