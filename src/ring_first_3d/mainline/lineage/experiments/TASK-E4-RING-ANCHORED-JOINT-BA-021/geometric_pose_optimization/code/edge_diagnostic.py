"""Trace CAD front-facing/culling/type switches in actual failed Ring geometry."""
from geometric import *
from ring020 import contours
import open3d as o3d

def edge_state(cad,C,K):
 front=np.sum(cad.N*(C[:3,3]-cad.FC),axis=1)>0;ii=np.flatnonzero(front[cad.adj[:,0]]!=front[cad.adj[:,1]]);ed=cad.edge[ii];X=cad.V[ed];P0=(X.mean(1)-C[:3,3])@C[:3,:3];q=P0@K.T;uv=q[:,:2]/q[:,2:];ray=P0/P0[:,2:];zz=cad.cad.cast_rays(o3d.core.Tensor(np.c_[np.broadcast_to(C[:3,3],ray.shape),ray@C[:3,:3].T].astype(np.float32)))['t_hit'].numpy();vis=(P0[:,2]>0)&(zz>=P0[:,2]-.002);cc=contours(np.isfinite(cast(cad.cad,K,C,360,640)));di={k:cKDTree(p).query(uv)[0]if len(p)else np.full(len(uv),np.inf)for k,p in cc.items()};return {tuple(e):dict(edge=e,uv=u,visible=bool(v),ray_hit_finite=bool(np.isfinite(z)),ray_first_hit_status='FINITE_HIT'if np.isfinite(z)else'MISS_PLUS_INF',ray_gap_mm=float(z-p[2]),inner_distance_px=float(i),outer_distance_px=float(o),type='inner'if i<o else'outer')for e,u,v,z,p,i,o in zip(ed,uv,vis,zz,P0,di['inner'],di['outer'])}
def main():
 views=load(M/'config/VIEWS.json');out=[]
 for group,axis in [('G05',0),('G06',1),('G03',2),('G01',5)]:
  v=next(v for v in views if v['group']==group and v['role']=='FIT');p=Problem([v]);cad=p.cads[v['ring_path']];q=np.zeros(6);state={}
  for sign in [0,1,-1]:state[sign]=edge_state(cad,canon_np(p.C(tt(q+np.eye(6)[axis]*.0001*sign),v).detach().numpy()),np.array(v['K']))
  differences=[]
  for e in set(state[0])|set(state[1])|set(state[-1]):
   aa=[state[s].get(e)for s in [0,1,-1]];signature=[(a['visible'],a['type'])if a else None for a in aa]
   if len(set(signature))>1:
    cause='FRONT_FACING_EDGE_IDENTITY_SWITCH'if any(a is None for a in aa)else'RAY_VISIBILITY_CULLING_SWITCH'if len({a['visible']for a in aa})>1 else'INNER_OUTER_HARD_RASTER_CLASS_SWITCH';differences.append(dict(CAD_vertex_ids=e,XYZ_mm=cad.V[list(e)],states=dict(zip(['base','plus','minus'],aa)),cause=cause))
  out.append(dict(group=group,view=v['id'],axis=axis,h=.0001,changed_edges=differences,not_optimization=True));print('EDGE_SWITCH_TRACE',group,len(differences),flush=True)
 save('metrics/CAD_VISIBILITY_SWITCH_CAUSES.json',out)
 save('metrics/INFINITE_RAY_MISS_PREDICATE_CHECK.json',dict(expression='t_hit >= point_depth - .002',ray_miss=float('inf'),test_point_depth_mm=40.,current_result=bool(float('inf')>=40.-.002),expected_knowledge_state='UNKNOWN_NOT_CERTIFIED_VISIBLE',isolation_only_no_algorithm_repair=True))
if __name__=='__main__':main()
