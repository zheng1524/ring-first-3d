"""Existing virtual G01; the generator/evaluator alone access GT/injections.

Fixed-GT is explicitly a solver diagnostic using the same prior and b optimizer,
not a median(D-GT) estimate and not evidence for the free ellipsoid model.
"""
from fit_revision import *
sys.path.insert(0,str(ROOT/"src"))
from ring_first_3d.sim.scene import synthesize
import copy

def main():
 original=Path('/home/liu/.config/superpowers/worktrees/ring_first_3d_workspace/TASK-V6-VIRTUAL-REG-001/experiments/TASK-V6-VIRTUAL-POLYP-REGISTRATION-001')
 out=T/'runs/control';out.mkdir(parents=True,exist_ok=True)
 gt=np.load(original/'inputs/virtual_GT.npz');ring=np.load(original/'inputs/canonical_ring.npz');views=read(original/'inputs/VIEW_SOURCES.json')
 chosen=views['selected'][::4][:4]+[views['HOLDOUT'][0],views['HOLDOUT'][5]]
 frames=[];sources=[];truth=[];gt_scene=scene(gt['V'],gt['F']);cad=dict(V=ring['V'],F=ring['F'])
 for i,row in enumerate(chosen):
  C=np.array(row['Camera_to_Ring']);K=np.array(row['K']);obs,body,rg=synthesize(gt['V'],gt['F'],ring['V'],ring['F'],K,C)
  cid=row['view_id'];rgb=out/(cid+'.png');mask=out/(cid+'_mask.png');cv2.imwrite(str(rgb),obs['RGB'][:,:,::-1]);cv2.imwrite(str(mask),obs['labels'])
  vf=dict(id=cid,RGB_path=str(rgb),Mask_path=str(mask),RGB_SHA256=sha(rgb),Mask_SHA256=sha(mask));v=dict(case=row['video'],frames=[vf],ring_radius_mm=5.6)
  f=frame_data(v,0,C,K,out,row['role']);frames.append(f)
  if row['role']!='FIT':continue
  yy,xx=np.where(obs['labels']==1);uv=pick(np.c_[xx,yy],128);r=rays(uv,K,C);D=obs['depth_axial_mm'][uv[:,1],uv[:,0]]
  sources.append(dict(rays=r,D=D.copy(),uv=uv,raw_X=corrected_points(r,D,0),C=C,K=K,meta=dict(source_id=cid,case=row['video'],raw_target=i,support=[],reference=i)))
  truth.append(dict(source_id=cid,b=.25 if row['video']=='004'else -.25,exact_D=D.copy()))
 support=np.r_[0.,0.,1.,-gt['V'][:,2].min()]
 save(out/'GENERATOR.json',dict(shape=asset(original/'inputs/virtual_GT.npz'),ring=asset(original/'inputs/canonical_ring.npz'),views=asset(original/'inputs/VIEW_SOURCES.json'),selected=[r['view_id']for r in chosen],support=support,proxy='SYNTHETIC_HERO_PROXY',input_description='original renderer, ideal axial measurement, 4 FIT + 2 2D-only HOLDOUT views; visible-Mask/DXY initialization',GT_scope='generator and frozen evaluation, or explicitly labeled fixed-GT solver diagnostic'))
 fitframes=[f for f in frames if f['role']=='FIT'];p0,init=initialize(fitframes);rows=[]
 for condition in ['ZERO','OPPOSITE_025']:
  ss=copy.deepcopy(sources);injected=np.zeros(len(ss))if condition=='ZERO'else np.array([x['b']for x in truth])
  for s,b in zip(ss,injected):s['D']+=b;s['raw_X']=corrected_points(s['rays'],s['D'],0)
  prob=Problem(fitframes,ss,p0,cad=cad);p,b,logs=prob.solve(p0.copy(),np.zeros(len(ss)),CFG['alternations'],condition)
  freeze=out/(condition+'_PREDICTION_FREEZE.json');save(freeze,dict(p=p,b=b,initialization=init,stages=logs,configuration_sha256=sha(T/'config.json'),code_sha256=sha(T/'code/fit_revision.py')))
  V,F=body_mesh(p);np.savez_compressed(out/(condition+'_BODY.npz'),V=V,F=F,p=p,b=b)
  ev=evaluate(p,b,frames,ss,None,cad);dist=gt_scene.compute_distance(o3d.core.Tensor(V.astype(np.float32))).numpy()
  # Identical b optimization with priors, with fixed true geometry only here.
  class FixedTrueGeometry(Problem):
   def model_depth(self,p,s):
    z,_=cast(gt_scene,s['rays']);return z,np.isfinite(z),np.zeros(len(z),bool)
  fixed=FixedTrueGeometry([],ss,p0);bb=np.zeros(len(ss));fixedlogs=[]
  for k in range(20):bb,ll=fixed.solve_bias(p0,bb);fixedlogs.append(dict(iteration=k,steps=ll,b=bb.copy()))
  save(out/(condition+'_FIXED_GT_DIAGNOSTIC.json'),dict(diagnostic_only=True,method='same_source_parts_and_same_bounded_optimizer_with_same_priors',b=bb,stages=fixedlogs))
  planes=[]
  for name,plane in [('KNOWN_SUPPORT',support),('WRONG_HEIGHT',np.array([0.,0.,1.,0.])),('FLIPPED_SIDE',-support)]:
   cut=sum(int((s['raw_X']@plane[:3]+plane[3]<0).sum())for s in ss);err=None
   try:np.savez_compressed(out/(condition+'_'+name+'.npz'),**clip(V,F,plane),p=p,b=b)
   except ValueError as e:err=str(e)
   planes.append(dict(name=name,plane=plane,original_fixed_N=sum(len(s['D'])for s in ss),raw_cut_side_N=cut,clip_error=err))
  rows.append(dict(condition=condition,prediction_freeze=asset(freeze),injected_b_mm=injected,fitted_b_mm=b,coarse_bias_error_mm=b-injected,fixed_true_geometry_fitted_b_mm=bb,fixed_true_geometry_error_mm=bb-injected,mean_abs_coarse_bias_error_mm=float(np.abs(b-injected).mean()),maximum_fixed_true_geometry_bias_error_mm=float(np.max(abs(bb-injected))),parent_to_GT_oneway_vertex_mm=dict(median=float(np.median(dist)),P95=float(np.percentile(dist,95))),evaluation=ev,planes=planes,stages=logs))
 save(T/'evidence/CONTROL_REVISION.json',dict(config=asset(T/'config.json'),conditions=rows,conclusion='Fixed-GT prior-bearing diagnostic and actual low-dimensional model are separate; no shape or bias accuracy claim for real data',units='mm'))
 print([(r['condition'],r['fitted_b_mm'].tolist(),r['maximum_fixed_true_geometry_bias_error_mm'])for r in rows],flush=True)
if __name__=='__main__':main()
