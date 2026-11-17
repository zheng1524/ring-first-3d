"""Independent source/CAD material samples and frozen base relationship; no relabeling."""
from geometry021 import *
def one(group,H):
 conf,src=group_data(group,H);rv=np.load(conf['ring']['path']);cad=scene(rv['V'],rv['F']);rows=[];bases=[]
 for a in src:
  idx=np.unique(a['F']);fc=a['V'][a['F']].mean(1);P=np.r_[a['V'][idx],fc];sd=cad.compute_signed_distance(o3d.core.Tensor(P.astype(np.float32)),nsamples=11).numpy();fa=trimesh.triangles.area(a['V'][a['F']]);rows.append(dict(group=group,source=a['id'],referenced_vertex_N=len(idx),original_face_N=len(fc),vertices_inside_CAD_beyond02mm_N=int((sd[:len(idx)]<-.02).sum()),face_centers_inside_CAD_beyond02mm_N=int((sd[len(idx):]<-.02).sum()),min_signed_CAD_distance_mm=float(sd.min()),inside_face_centroid_area_proxy_mm2=float(fa[sd[len(idx):]<-.02].sum()),threshold_mm=.02,majority_parity_rays=11,not_exact_triangle_collision_certification=True,not_relabeling_TRUSTED=True));np.savez_compressed(R/'evaluation/groups'/group/(a['id']+'_RING_MATERIAL.npz'),original_face_id=a['mesh']['original_face_id'],referenced_original_vertex_id=idx,CAD_signed_distance_mm=sd,face_center_inside_beyond02mm=sd[len(idx):]<-.02)
 basepath=P18/'inputs'/group/'BASE_SELECTION.json';chpath=P18/'inputs'/group/'CHART.json';base=load(basepath);ch=load(chpath);p=np.array(base['plane'],float);p/=np.linalg.norm(p[:3]);cap=bool(ch['cap'])
 for n,z in conf['bodies'].items():
  b=np.load(z['path']);h=b['V']@p[:3]+p[3];ids=np.unique(b['F_solid'][b['inferred_base_faces']]);bases.append(dict(group=group,body=n,base_status=base.get('base_status','UNSPECIFIED'),cap_enabled=cap,plane=p,plane_source=asset(basepath),chart_source=asset(chpath),minimum_vertex_height_mm=float(h.min()),model_Hmax_above_estimated_base_mm=float(h.max()),model_H95_vertex_sample_mm=float(np.quantile(h,.95)),illegal_below_base_vertices_N=int((h<-1e-5).sum())if cap else None,cap_vertex_plane_distance_max_mm=float(abs(h[ids]).max())if len(ids)else None,Ring_vertex_height_to_estimated_base_mm=stats(rv['V']@p[:3]+p[3]),not_real_height_truth=True,base_is_not_Ring_plane=True))
 save('metrics/groups/'+group+'_HERO_RING_MATERIAL.json',rows);table('metrics/groups/'+group+'_HERO_RING_MATERIAL.csv',rows);save('metrics/groups/'+group+'_ESTIMATED_BASE_RELATION.json',bases);table('metrics/groups/'+group+'_ESTIMATED_BASE_RELATION.csv',bases);save('runtime/'+group+'_SOURCE_GEOMETRY_COMPLETE.json',dict(epoch=time.time()));print('SOURCE_GEOMETRY021',group,flush=True)
def main():
 for g in ['G03','G05','G06','G01']:
  while not(R/'runtime'/(g+'_QUANTITATIVE_COMPLETE.json')).exists():time.sleep(5)
  if not(R/'runtime'/(g+'_SOURCE_GEOMETRY_COMPLETE.json')).exists():one(g,load(R/'results/B3.json')['T']if g=='G01'else np.eye(4))
 save('runtime/SOURCE_GEOMETRY_COMPLETE.json',dict(epoch=time.time()))
if __name__=='__main__':main()
