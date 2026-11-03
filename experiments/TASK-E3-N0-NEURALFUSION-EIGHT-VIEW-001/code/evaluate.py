"""Fixed all-observation denominators, real first hits, all original face IDs."""
from common import *
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
@lru_cache(None)
def observations(cid):
    s=native(cid);uv=s['native_uv'];z=s['depth'].flat[s['native_id']].astype(float);cad,_=cast(ringscene(s['c']['scene_id']),uv,s['Kn'],s['T']);blocked=np.isfinite(cad)&(z>cad+.002)
    return dict(s,z=z,CAD_mm=cad,visible=~blocked,available=cleaned(cid)['valid'].flat[s['native_id']])
def full_p95(error):
    a=np.sort(np.abs(error));j=int(np.ceil((len(a)-1)*.95))
    if not len(a):return None,'NO_OBSERVATIONS'
    return (float(np.quantile(a,.95)),'FINITE')if np.isfinite(a[j])else(None,'INFINITE_DUE_TO_MISSES')
def evaluate(tag):
    run=load(R/f'metrics/{tag}_RUN.json');scene=run['scene'];ids=protocol()['orders'][scene];m=trimesh.load(R/'meshes'/f'{tag}_raw_mm.ply',process=False);P=np.asarray(m.vertices);F=np.asarray(m.faces);ss=mesh_scene(P,F);rayrows=[];rawrows=[];arrays={}
    for cid in ids:
        s=observations(cid);uv=s['native_uv'];hit,_=cast(ss,uv,s['Kn'],s['T']);z=s['z'];visible=s['visible'];finite=np.isfinite(hit);err=hit-z;d=distance(ss,s['X']);cat=np.full(len(z),'MISS',dtype='<U16');cat[~visible]='CAD_OCCLUDED';cat[visible&finite&(abs(err)<=.25)]='AGREE';cat[visible&finite&(err<-.25)]='NEAR';cat[visible&finite&(err>.25)]='FAR'
        p95,pstatus=full_p95(err[visible]);denom=max(1,visible.sum());rayrows.append(dict(tag=tag,scene=scene,order=run['order'],stage=run['stage'],source=cid,in_fusion=cid in run['sources'],fixed_original_native_N=len(z),input_available_N=int(s['available'].sum()),cleanup_removed_N=int((~s['available']).sum()),CAD_occluded_N=int((~visible).sum()),CAD_visible_N=int(visible.sum()),hit_N=int((visible&finite).sum()),miss_N=int((visible&~finite).sum()),agree_N=int((cat=='AGREE').sum()),near_N=int((cat=='NEAR').sum()),far_N=int((cat=='FAR').sum()),hit_fraction=float((visible&finite).sum()/denom),agree_fraction=float((cat=='AGREE').sum()/denom),point_retention_0p25=float((d[visible]<=.25).mean()),hit_only_error_mm=stats(err[visible&finite]),p95_with_misses_mm=p95,p95_with_misses_status=pstatus,physical_truth=False))
        for key,a in [('native_id',s['native_id']),('hit_mm',hit),('CAD_mm',s['CAD_mm']),('depth_mm',z),('category',cat),('available',s['available'])]:arrays[cid+'_'+key]=a
        raw=original(cid);centers=raw['P'][raw['F']].mean(1);dr=distance(ss,centers);area=raw['area'];near=dr<=.25;rawrows.append(dict(tag=tag,source=cid,original_face_N=len(centers),original_area_mm2=float(area.sum()),face_retained_N=int(near.sum()),area_retention_0p25=float(area[near].sum()/area.sum()),face_retention_0p25=float(near.mean()),distance_mm=stats(dr)))
        arrays[cid+'_original_face_id']=np.arange(len(centers));arrays[cid+'_face_distance_mm']=dr
    edges=m.edges_unique;counts=np.bincount(m.edges_unique_inverse);graph=coo_matrix((np.ones(2*len(edges)),(np.r_[edges[:,0],edges[:,1]],np.r_[edges[:,1],edges[:,0]])),shape=(len(P),len(P)));nc,labels=connected_components(graph,directed=False);areas=np.bincount(labels[F[:,0]],weights=m.area_faces,minlength=nc);angles=np.degrees(m.face_adjacency_angles)
    topology=dict(vertices_N=len(P),faces_N=len(F),area_mm2=float(m.area),bounds_mm=m.bounds,boundary_edges_N=int((counts==1).sum()),nonmanifold_edges_N=int((counts>2).sum()),components_N=int(nc),largest_component_area_fraction=float(areas.max()/areas.sum()),watertight=bool(m.is_watertight),adjacent_normal_angle_deg=stats(angles),axis_aligned_normal_fraction_5deg=float((np.abs(m.face_normals).max(1)>=np.cos(np.deg2rad(5))).mean()))
    centers=P[F].mean(1);cleanX=np.concatenate([cleaned(c)['X']for c in ids]);nearest=cKDTree(cleanX).query(centers)[0];supported=nearest<=.25;visible_any=np.zeros(len(F),bool);mask_conflict=np.zeros(len(F),bool);free_proxy=np.zeros(len(F),bool)
    for cid in ids:
        s=cleaned(cid);uv,z=vis.project_camera(centers,s['K'],s['T']);nuv,_=vis.project_camera(centers,s['Kn'],s['T']);h,w=s['depth'].shape;ok=np.isfinite(uv).all(1)&(z>0)&(uv[:,0]>=-.5)&(uv[:,0]<639.5)&(uv[:,1]>=-.5)&(uv[:,1]<359.5)&(nuv[:,0]>=-.5)&(nuv[:,0]<w-.5)&(nuv[:,1]>=-.5)&(nuv[:,1]<h-.5);j=np.flatnonzero(ok);p=np.floor(uv[j]+.5).astype(int);p2=np.floor(nuv[j]+.5).astype(int);cad,_=cast(ringscene(scene),uv[j],s['K'],s['T']);unblocked=~(np.isfinite(cad)&(z[j]>cad+.002));jj=j[unblocked];p=p[unblocked];p2=p2[unblocked];lab=s['labels'][p[:,1],p[:,0]];visible_any[jj]|=lab!=2;mask_conflict[jj]|=lab==0;legal=s['valid'][p2[:,1],p2[:,0]]&(lab==1);dd=s['depth'][p2[:,1],p2[:,0]];free_proxy[jj]|=legal&(z[jj]<dd-.25)
    category=np.where(supported,'OBSERVED_NEAR_PROXY',np.where(visible_any,'INFERRED_UNSUPPORTED_PROXY','UNKNOWN_OCCLUDED_OR_UNSEEN'));facecats={c:dict(N=int((category==c).sum()),area_mm2=float(m.area_faces[category==c].sum()))for c in np.unique(category)}
    arrays.update(mesh_face_id=np.arange(len(F)),mesh_face_category=category,mesh_face_nearest_input_mm=nearest,mesh_face_mask_BG_proxy=mask_conflict,mesh_face_free_space_proxy=free_proxy)
    np.savez_compressed(R/'local_results'/f'{tag}_evaluation.npz',**arrays)
    table(f'metrics/{tag}_RAYS.csv',rayrows);table(f'metrics/{tag}_RAW_FACES.csv',rawrows)
    result=dict(tag=tag,scene=scene,order=run['order'],stage=run['stage'],sources=run['sources'],topology=topology,rays=rayrows,raw_faces=rawrows,surface_categories=facecats,any_view_mask_BG_face_proxy_N=int(mask_conflict.sum()),any_view_free_space_face_proxy_N=int(free_proxy.sum()),unknown_boundary_face_N=run['unknown_boundary_face_N'],surface_labels_are_uncalibrated=True,GT=False,geometry_deleted_N=0)
    save(f'metrics/{tag}_METRICS.json',result);print('EVALUATED',tag,'faces',len(F),'all-view agreement',round(sum(r['agree_N']for r in rayrows)/sum(r['CAD_visible_N']for r in rayrows),4),flush=True)
    return result
def main():
    p=protocol()
    for scene,ii in p['orders'].items():
        for order in ['forward','reverse']:
            for i in range(len(ii)):
                tag=f'{scene}_{order}_F{i}'
                if not (R/f'metrics/{tag}_METRICS.json').exists():evaluate(tag)
    summaries=[]
    for p in sorted((R/'metrics').glob('*_METRICS.json')):
        r=load(p);rr=r['rays'];denom=sum(a['CAD_visible_N']for a in rr);area=sum(a['original_area_mm2']for a in r['raw_faces']);summaries.append(dict(tag=r['tag'],scene=r['scene'],order=r['order'],stage=r['stage'],view_N=len(r['sources']),fixed_visible_N=denom,hit_fraction=sum(a['hit_N']for a in rr)/denom,agree_fraction=sum(a['agree_N']for a in rr)/denom,Raw_area_retention=sum(a['original_area_mm2']*a['area_retention_0p25']for a in r['raw_faces'])/area,mesh_area_mm2=r['topology']['area_mm2'],mesh_faces_N=r['topology']['faces_N'],components_N=r['topology']['components_N'],largest_component_area_fraction=r['topology']['largest_component_area_fraction'],axis_normal_fraction=r['topology']['axis_aligned_normal_fraction_5deg'],unknown_boundary_fraction=r['unknown_boundary_face_N']/r['topology']['faces_N'],unsupported_face_fraction=r['surface_categories'].get('INFERRED_UNSUPPORTED_PROXY',{}).get('N',0)/r['topology']['faces_N']))
    table('metrics/PREFIX_SUMMARY.csv',summaries);save('metrics/PREFIX_SUMMARY.json',summaries)
if __name__=='__main__':main()
