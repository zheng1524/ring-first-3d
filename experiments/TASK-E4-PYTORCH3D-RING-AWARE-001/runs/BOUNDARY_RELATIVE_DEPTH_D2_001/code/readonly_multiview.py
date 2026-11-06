"""AFTER freeze ONLY. Evidence proxies, never consumed by training or ranking."""
from common import *
from evaluate import pointcast

def main():
 freeze=load(R/'assets_index/PREDICTIONS_FROZEN.json');assert freeze['all_expected_finals'];src={x['id']:x for x in load('/home/liu/ring_first_3d_neural_e1/experiments/TASK-NEURAL-E1-PIPELINE-RECOVERY-001/provenance/INPUT_ELIGIBILITY.json')['references']};rows=[];summ=[]
 for name in['real_Ip','real_IIa','real_Is']:
  meta=getcase(name);ring=np.load(R/'inputs'/name/'RING.npz');rs=scene(ring['V'],ring['F']);data={}
  for view in meta['views']:
   cid=view['id'];obs=dict(np.load(R/'depth_observations'/(cid+'.npz')));raw=np.load(src[cid]['E1_actual_native']['path']);data[cid]=(view,obs,raw['depth_mm'],dict(np.load(R/'inputs'/name/(cid+'.npz'))))
  for ca,(va,a,_,_)in data.items():
   ray=np.c_[a['uv'],np.ones(len(a['uv']))]@np.linalg.inv(a['K']).T;X=(ray*a['z'][:,None])@a['T'][:3,:3].T+a['T'][:3,3]
   for cb,(vb,b,dense,image)in data.items():
    if ca==cb:continue
    uv,z,rz=pointcast(rs,X,b['K'],b['T']);px=np.rint(uv).astype(int);mapped=np.c_[uv,np.ones(len(uv))]@np.linalg.inv(b['K']).T@image['K'].T;ip=np.rint(mapped[:,:2]/mapped[:,2:]).astype(int);counts={}
    for i in range(len(X)):
     x,y=px[i];xx,yy=ip[i];observed=None;diff=None
     if z[i]<=0 or not(0<=x<dense.shape[1]and 0<=y<dense.shape[0]and 0<=xx<640 and 0<=yy<360):state='OUTSIDE_OR_BEHIND_CAMERA'
     elif rz[i]<z[i]-.05:state='CAD_OCCLUDED'
     elif image['labels'][yy,xx]==2:state='RING_LABEL_UNRESOLVED'
     elif image['labels'][yy,xx]!=1:state='NO_POLYP_SURFACE_OBSERVATION'
     elif not np.isfinite(dense[y,x])or dense[y,x]<=0:state='MISSING_OTHER_DEPTH'
     else:
      observed=float(dense[y,x]);diff=float(z[i]-observed);state='NEAR_SURFACE_PROXY'if abs(diff)<=.5 else'IN_FRONT_OF_OTHER_DEPTH_PROXY'if diff<-.5 else'BEHIND_OTHER_DEPTH_OCCLUSION_PROXY'
     counts[state]=counts.get(state,0)+1;rows.append(dict(case=name,source=ca,target=cb,source_pixel_id=int(a['pixel_id'][i]),state=state,projected_z_mm=float(z[i]),other_HERO_z_mm=observed,difference_mm=diff,source_qualification=va['qualification'],target_qualification=vb['qualification'],for_diagnostic_only=True))
    summ.append(dict(case=name,source=ca,target=cb,fixed_N=len(X),counts=counts,interpretation='uncalibrated geometric proxy; uncertain cameras and correlated HERO, not truth',used_for_loss_weights_or_ranking=False))
 table('metrics/READONLY_MULTIVIEW_HERO.csv',rows);save('metrics/READONLY_MULTIVIEW_HERO_SUMMARY.json',dict(run_after_prediction_freeze=True,prediction_freeze_sha=sha(R/'assets_index/PREDICTIONS_FROZEN.json'),rows=summ,optimizer_dependency=False,not_used_for_model_ranking=True))
if __name__=='__main__':main()
