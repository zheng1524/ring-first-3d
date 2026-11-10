"""Separate autograd linearity from reselected discrete ray/contour/raster states."""
from tape import *

def main():
 guard_optimizer();c=Case('G02');ch=FreeVertices(c);q=torch.zeros((ch.N,3),device=device,dtype=torch.float64,requires_grad=True);obj=MultiObjective(c,ch);obj.attempt=40;obj.depth.begin(ch.mesh(q));records=[];arrays={}
 for cid in c.fit:
  previous=None
  for rep in range(8):
   obj.depth.begin(ch.mesh(q));ts,m=view_terms(c,ch,obj,q,cid);grads={k:gradient(t,q).cpu().numpy()for k,t in ts.items()};fid=None;z=None;active=None
   if cid in obj.depth.obs:
    zz,aa,z,fid=obj.depth.query(m,cid);active=aa.cpu().numpy()
   state={k:np.array(v).copy()for k,v in obj.contour.last[cid].items()};fr=c.fragments(m,cid);rast=fr.pix_to_face.detach().cpu().numpy();rec=dict(view=cid,repeat=rep,component_gradient_norm={k:float(np.linalg.norm(g))for k,g in grads.items()})
   if previous:
    pg,pfid,pz,pa,ps,pr=previous;rec.update(component_relative_change={k:float(np.linalg.norm(g-pg[k])/max(1e-30,np.linalg.norm(pg[k])))for k,g in grads.items()},contour_nn_changed_N=int((state['nn']!=ps['nn']).sum()),raster_face_assignment_changed_N=int((rast!=pr).sum()))
    if fid is not None:
     ids=np.flatnonzero(fid!=pfid);rec.update(depth_face_changed_N=len(ids),depth_active_changed_N=int((active!=pa).sum()),depth_z_change_max_mm=float(np.max(abs(z-pz))),changed_depth_ray_ids=ids.tolist())
     if len(ids):
      arrays[cid+'_'+str(rep)+'_ray_ids']=ids;arrays[cid+'_'+str(rep)+'_before_faces']=pfid[ids];arrays[cid+'_'+str(rep)+'_after_faces']=fid[ids];arrays[cid+'_'+str(rep)+'_before_z']=pz[ids];arrays[cid+'_'+str(rep)+'_after_z']=z[ids]
   records.append(rec);previous=(grads,fid,z,active,state,rast)
 # Reuse exactly one ray scene: same continuous geometry + same discrete branch.
 begin=obj.depth.begin;obj.depth.begin(ch.mesh(q));obj.depth.begin=lambda m:None
 G,_,_,fixed=instrument(c,ch,obj,q);obj.depth.begin=begin
 save('metrics/G02_DISCRETE_STATE_ISOLATION.json',dict(rows=records,fixed_ray_scene_additivity=fixed,GT_read=False,optimizer_steps=0,not_a_training_change=True));np.savez_compressed(R/'metrics/G02_CHANGED_DEPTH_FACES.npz',**arrays)
 print('DISCRETE_ISOLATION',[(x['view'],x.get('depth_face_changed_N',0),x.get('component_relative_change',{}))for x in records if x.get('depth_face_changed_N',0)],'fixed_error',fixed['additivity_relative_error'],flush=True)
if __name__=='__main__':main()
