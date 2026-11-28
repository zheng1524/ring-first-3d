"""Generator/evaluator owns GT. Optimizer receives synthetic measured pixels and known support only."""
from fit import *
from ring_first_3d.sim.scene import synthesize
def main():
 original=Path('/home/liu/.config/superpowers/worktrees/ring_first_3d_workspace/TASK-V6-VIRTUAL-REG-001/experiments/TASK-V6-VIRTUAL-POLYP-REGISTRATION-001')
 out=T/'runs/control';out.mkdir(parents=True,exist_ok=True);gt=np.load(original/'inputs/virtual_GT.npz');ring=np.load(original/'inputs/canonical_ring.npz');views=read(original/'inputs/VIEW_SOURCES.json');chosen=views['selected'][::max(1,len(views['selected'])//4)][:4]+views['HOLDOUT'][:2]
 frames=[];sources=[];truth=[]
 for i,row in enumerate(chosen):
  C=np.array(row['Camera_to_Ring']);K=np.array(row['K']);obs,body,rg=synthesize(gt['V'],gt['F'],ring['V'],ring['F'],K,C);cid=row['view_id'];rgb=out/(cid+'.png');mask=out/(cid+'_mask.png');cv2.imwrite(str(rgb),obs['RGB'][:,:,::-1]);cv2.imwrite(str(mask),obs['labels'])
  vf=dict(id=cid,RGB_path=str(rgb),Mask_path=str(mask),RGB_SHA256=sha(rgb),Mask_SHA256=sha(mask));v=dict(case=row['video'],frames=[vf],ring_radius_mm=5.6)
  f=frame_data(v,0,C,K,out,row['role']);frames.append(f)
  if row['role']!='FIT':continue
  yy,xx=np.where(obs['labels']==1);uv=pick(np.c_[xx,yy],128);r=rays(uv,K,C);trueD=obs['depth_axial_mm'][uv[:,1],uv[:,0]];b=.25 if row['video']=='004'else -.25;D=trueD+b
  X=corrected_points(r,D,0);sources.append(dict(rays=r,D=D,uv=uv,raw_X=X,C=C,K=K,meta=dict(source_id=cid,case=row['video'],raw_target=i,support=[],reference=i)))
  # Generator-only exact-coordinate and bias-sign assertions, using full original triangle scene.
  reverse=corrected_points(r,D,b);expected=body['points'][uv[:,1],uv[:,0]];error=np.max(np.linalg.norm(reverse-expected,axis=1));assert error<.001
  truth.append(dict(source_id=cid,injected_b_mm=b,axial_inverse_max_mm=error))
 # Known synthetic support touches the original mesh's lowest attachment point.
 support=np.r_[0.,0.,1.,-gt['V'][:,2].min()];save(out/'GENERATOR.json',dict(shape=asset(original/'inputs/virtual_GT.npz'),ring=asset(original/'inputs/canonical_ring.npz'),view_manifest=asset(original/'inputs/VIEW_SOURCES.json'),truth=truth,support=support,support_origin='controlled contact plane at existing mesh minimum Z; not claimed preexisting real support',proxy='SYNTHETIC_HERO_PROXY',GT_not_optimizer_input=True))
 fitframes=[f for f in frames if f['role']=='FIT'];p0,init=initialize(fitframes);problem=Problem(fitframes,sources,p0);p,b,logs=problem.solve(p0.copy(),np.zeros(len(sources)),CFG['alternations'],'CONTROL_FULL')
 # Freeze prediction before evaluating against the original GT triangles and injected b.
 save(out/'PREDICTION_FREEZE.json',dict(p=p,b=b,initialization=init,stages=logs,config_sha256=sha(T/'config.json')))
 V,F=body_mesh(p);np.savez_compressed(out/'PARENT.npz',V=V,F=F,p=p,b=b);conditions=[]
 for name,plane in [('KNOWN_SUPPORT',support),('WRONG_HEIGHT',np.array([0.,0.,1.,0.])),('FLIPPED_SIDE',-support)]:
  prob=Problem(fitframes,sources,p0,plane);q,bq,ll=prob.solve(p.copy(),b.copy(),1,name);ev=evaluate(q,bq,frames,sources,plane);VV,FF=body_mesh(q);error=None
  try:np.savez_compressed(out/(name+'.npz'),**clip(VV,FF,plane),p=q,b=bq)
  except Exception as e:error=repr(e)
  conditions.append(dict(name=name,plane=plane,metrics=ev,clip_error=error,stages=ll,p=q,b=bq,original_trusted_cut_side_N=int(sum((s['raw_X']@plane[:3]+plane[3]<0).sum()for s in sources))))
 gt_scene=scene(gt['V'],gt['F']);distance=gt_scene.compute_distance(o3d.core.Tensor(V.astype(np.float32))).numpy()
 exact=[]
 for s,t in zip(sources,truth):
  z,_=cast(gt_scene,s['rays']);estimate=float(np.median(s['D']-z));assert abs(estimate-t['injected_b_mm'])<.001;exact.append(dict(source_id=t['source_id'],estimated_b_mm=estimate,error_mm=abs(estimate-t['injected_b_mm'])))
 save(T/'evidence/CONTROL_RESULT.json',dict(GT_shape=asset(original/'inputs/virtual_GT.npz'),fixed_exact_mesh_bias_diagnostic=exact,coarse_model_bias=[dict(source_id=t['source_id'],injected=t['injected_b_mm'],fitted=float(x))for t,x in zip(truth,b)],parent_to_GT_mm=dict(median=float(np.median(distance)),p95=float(np.percentile(distance,95))),conditions=conditions,interpretation='Exact-geometry bias diagnostic separated from nonellipsoidal G01 coarse fit; model mismatch and common-depth ambiguity retained',no_GT_tuning=True))
 print('CONTROL_COMPLETE',[(r['name'],r['original_trusted_cut_side_N'],r['clip_error'])for r in conditions],flush=True)
if __name__=='__main__':main()
