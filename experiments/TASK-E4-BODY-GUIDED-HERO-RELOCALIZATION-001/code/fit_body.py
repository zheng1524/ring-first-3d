"""Fresh image-only nine-parameter ellipsoid, A1 conic math; no HERO/old Body parameters."""
from geometry import *
from scipy.optimize import least_squares
from scipy.special import expit
CFG=load(R/'config/PROTOCOL.json')

def body_fit(g,views,ringV,ringF,output):
 rt=scene(ringV,ringF);data=[];O=[];D=[];er=[]
 for v in views:
  K,C,labels=v['K'],v['C'],v['labels'];e=ellipse_descriptor(labels==1);curve=ellipse_curve(e);h,w=labels.shape;yy,xx=np.mgrid[3:h:8,3:w:8];grid=np.c_[xx.ravel(),yy.ravel()];qp=ellipse_coords(grid,e);target=(qp*qp).sum(1)<=1;lab=labels[grid[:,1].astype(int),grid[:,0].astype(int)];known=(lab!=2)&~((lab==1)&~target);cad=rayquery(rt,C,K,grid)['t_hit'];d=np.r_[e['center'],1.]@np.linalg.inv(K).T@C[:3,:3].T;d/=np.linalg.norm(d);O.append(C[:3,3]);D.append(d);data.append(dict(v=v,e=e,curve=curve,grid=grid,target=target,known=known,cad=cad));er.append(e['axes'].mean()/np.mean([K[0,0],K[1,1]]))
 N=np.eye(3)[None]-np.array(D)[:,:,None]*np.array(D)[:,None,:];mat=N.sum(0);c0=np.linalg.lstsq(mat,np.einsum('nij,nj->i',N,np.array(O)),rcond=None)[0];radius=float(np.linalg.norm(ringV[:,:2],axis=1).min());c0=np.clip(c0,-4*radius,4*radius);z=[float((c0-o)@v['C'][:3,2])for o,v in zip(O,views)];a0=float(np.clip(np.median(np.array(er)*np.maximum(z,radius)),radius*.1,radius*3));base=np.r_[c0,np.zeros(3),np.log([a0]*3)];lo=np.r_[np.full(3,-4*radius),np.full(3,-np.pi),np.log(np.full(3,.05*radius))];hi=np.r_[np.full(3,4*radius),np.full(3,np.pi),np.log(np.full(3,4*radius))]
 nres=sum(128+128+len(d['grid'])for d in data)+9
 def residual(p):
  try:
   rr=[]
   for d in data:
    v=d['v'];center,M,axes,curve=ellipse_projection(p,np.eye(3),v['K'],v['C']);norm=1/np.sqrt(len(data));target=d['curve'];r=signed_distance(target,center,M,axes)/3/np.sqrt(len(target));dist=cKDTree(d['curve']).query(curve)[0]/3/np.sqrt(128);sd=signed_distance(d['grid'],center,M,axes);prob=expit(-sd/2);region=(prob-d['target'])*np.sqrt(d['known']/max(1,d['known'].sum()))*2;rr.extend([r*norm,dist*norm,region*norm])
   rr.append(np.r_[(p[:3]-base[:3])/(4*radius),p[3:6]/np.pi,(p[6:]-base[6:])/2]*np.sqrt(.002));a=np.concatenate(rr)
   if not np.isfinite(a).all():raise ValueError('nonfinite')
   return a
  except (ValueError,np.linalg.LinAlgError):return np.full(nres,100.)
 fits=[]
 for start in range(CFG['body_fit_starts']):
  p=base.copy();rng=np.random.default_rng(CFG['seed']+start)
  if start:p[:3]+=rng.normal(0,.2*radius,3);p[3:6]+=rng.normal(0,.25,3);p[6:]+=rng.normal(0,.2,3)
  p=np.clip(p,lo+1e-6,hi-1e-6);sol=least_squares(residual,p,method='trf',bounds=(lo,hi),loss='soft_l1',f_scale=.1,max_nfev=CFG['body_fit_nfev'],x_scale='jac',ftol=1e-5,xtol=1e-5,gtol=1e-5);fits.append(dict(start=start,p=sol.x,cost=float(np.sum(residual(sol.x)**2)),success=sol.success,nfev=sol.nfev,message=sol.message))
 chosen=min(fits,key=lambda a:(a['cost'],a['start']));p=np.array(chosen['p']);V,F=ellipse_mesh(p);output.mkdir(parents=True,exist_ok=True);np.savez_compressed(output/'Body-E.npz',V=V,F=F,p=p,R0=np.eye(3));trimesh.Trimesh(V,F,process=False).export(output/'Body-E_mm.ply');save(str(output.relative_to(R)/'Body-E_FIT.json'),dict(group=g,parameters=p,axes_mm=np.exp(p[6:]),center_mm=p[:3],rotation=Rotation.from_rotvec(p[3:6]).as_matrix(),fit_views=[v['id']for v in views],initial_image_ray_center=c0,center_information_eigenvalues=np.linalg.eigvalsh(mat),starts=fits,selected_start=chosen['start'],selection='image-only FIT cost; no HERO/depth/old Body parameters; finite budget, no GT',target_ellipses=[dict(id=d['v']['id'],ellipse=d['e'])for d in data],warning='ellipse targets are generic Mask-derived core descriptors, not DXY or certified anatomical head borders'))
 return V,F

def main():
 for g in CFG['case_order']:
  vv=[]
  for cid in load(R/'config'/(g+'_BODY_FIT_VIEWS.json'))['ids']:
   p=R/'inputs'/g/(cid+'.npz');a=np.load(p);vv.append(dict(id=cid,K=a['K'],C=a['T'],labels=a['labels']));
  rv=np.load(R/'inputs'/g/'RING.npz');out=R/'local_results'/g;body_fit(g,vv,rv['V'],rv['F'],out);src=P/'runs'/g/'B3/FINAL.npz';a=np.load(src);np.savez_compressed(out/'Body-U.npz',V=a['V'],F=a['F'],F_solid=a['F_solid'],inferred_base_faces=a['inferred_base_faces']);save('provenance/'+g+'_BODY_SOURCES.json',dict(Body_E=asset(out/'Body-E.npz'),Body_E_math='fresh nine-parameter analytic A1 conic fitting from2D only',Body_U=asset(src),Body_U_commit='e2d1eb16da103c0fa198596b4434c4ddfaebef8a',historical018_B2_optional_only=str(REPO/'experiments/TASK-E4-HERO-BODY-ADAPT-018/arms/B2_TRUSTED_COH16/local_results'/g/'FINAL.npz'),GT_used=False));print('BODY_FIT_DONE',g,flush=True)
 save('provenance/BODIES_FROZEN.json',dict(epoch=time.time(),files=[asset(p)for p in(R/'local_results').glob('*/Body-?.npz')],Body_not_updated_after=True))
if __name__=='__main__':main()
