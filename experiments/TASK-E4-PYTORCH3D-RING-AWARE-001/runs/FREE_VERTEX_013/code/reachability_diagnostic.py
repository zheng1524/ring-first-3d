"""Read-only evidence of geometric reach and resolution, not a new optimizer/loss."""
from common import *
from evaluate import area_samples


def surface_ray_bound(V,F,origin,dirs):
 if not len(dirs):return np.empty(0)
 offset=V-origin;parallel=np.einsum('vi,ri->rv',offset,dirs);Y=offset[None]-parallel[:,:,None]*dirs[:,None];edges=np.unique(np.sort(np.r_[F[:,[0,1]],F[:,[1,2]],F[:,[2,0]]],1),axis=0);a=Y[:,edges[:,0]];b=Y[:,edges[:,1]];e=b-a;t=np.clip(-np.einsum('rei,rei->re',a,e)/np.maximum(np.einsum('rei,rei->re',e,e),1e-20),0,1);dist=np.linalg.norm(a+t[:,:,None]*e,axis=2).min(1);tri=Y[:,F];sign=[]
 for k in range(3):sign.append(np.einsum('rfi,ri->rf',np.cross(tri[:,:,k],tri[:,:,(k+1)%3]),dirs))
 ss=np.stack(sign,axis=-1);nondeg=abs(ss.sum(2))>1e-12;inside=nondeg&((ss>=-1e-12).all(2)|(ss<=1e-12).all(2));dist[inside.any(1)]=0;return dist

def main():
 rows=[]
 for n in ['G03','G01','G02','G10','G11']:
  z=np.load(R/'inputs'/n/'INITIAL.npz');V,F=z['V'],z['F'];m=trimesh.Trimesh(V,F,process=False);rr=np.load(R/'inputs'/n/'RING.npz');rt=scene(V,F);rs=scene(rr['V'],rr['F']);D=load(R/'inputs'/n/'CHART.json')['D_mm'];edge=np.linalg.norm(V[m.edges_unique[:,0]]-V[m.edges_unique[:,1]],axis=1)
  for v in getcase(n)['views']:
   if v['role']!='FIT':continue
   a=np.load(R/'inputs'/n/(v['id']+'.npz'));P=(V-a['T'][:3,3])@a['T'][:3,:3];uv=P@a['K'].T;uv=uv[:,:2]/uv[:,2:];depth=cast(rt,a['K'],a['T'],360,640);cad=cast(rs,a['K'],a['T'],360,640);pred=np.isfinite(depth)&(depth<cad);from scipy.ndimage import distance_transform_edt
   missing=(a['labels']==1)&~pred&(distance_transform_edt(~pred)>10);yy,xx=np.nonzero(missing);ids=np.linspace(0,len(xx)-1,min(256,len(xx))).astype(int)if len(xx)else[];u=np.c_[xx[ids],yy[ids],np.ones(len(ids))];ray=u@np.linalg.inv(a['K']).T;d=ray@a['T'][:3,:3].T;d/=np.linalg.norm(d,axis=1)[:,None]if len(d)else 1;offset=V-a['T'][:3,3];parallel=np.einsum('vi,ri->rv',offset,d);distance=np.linalg.norm(offset[None]-parallel[:,:,None]*d[:,None],axis=2)if len(d)else np.zeros((0,len(V)));md=distance.min(1)if len(d)else[];nearid=distance.argmin(1)if len(d)else[];lower=surface_ray_bound(V,F,a['T'][:3,3],d);rows.append(dict(case=n,view=v['id'],missing_far_N=int(missing.sum()),selected_missing_rays=len(ids),per_ray_nearest_vertex_ray_distance_mm=stats(md),nearest_support_vertex_N=len(np.unique(nearid)),continuous_surface_ray_necessary_displacement_mm=stats(lower),missing_ray_bound_over_025D_N=int((lower>.25*D).sum()),missing_ray_bound_over_1D_N=int((lower>D).sum()),bound_note='Exact triangle-to-infinite-line distance via projected triangles; necessary per-vertex movement lower bound for fixed faces, not GT depth. Camera-facing mesh condition recorded separately.',all_mesh_points_in_front=bool((P[:,2]>0).all()),edge_length_mm=stats(edge),original_vertex_N=len(V),original_face_N=len(F),Euler=m.euler_number,total_trust_025D_mm=.25*D,total_trust_1D_mm=D,topology_stalk_impossibility_proven=False,caveat='Distance to actual rays, not known missing-surface3D GT. Vertex-ray bound depends on sampling. Genus0 supports stalk without topology change; this is evidence not a proof of sufficient resolution.'))
 save('metrics/GEOMETRY_REACHABILITY.json',rows);table('metrics/GEOMETRY_REACHABILITY.csv',rows)
if __name__=='__main__':main()
