"""Post-prediction descriptions only; never modifies thresholds, masks or points."""
from common import *
def main():
    profiles=[];regions=[];rows=load(R/'metrics/P1_candidate_damage.json')
    for c in cases():
        a,p,rgb,m=data(c);P=a['XYZ_mm'];rho=a['rho_surface_radius'];r=dict(np.load(R/f'local_results/{c["id"]}/spatial_regions.npz'));direction=np.median(P[r['largest_low_region']],0)-np.median(P[r['dense_proxy']],0);direction/=np.linalg.norm(direction);s=P@direction;edges=np.linspace(s.min(),s.max()+1e-9,13);idx=np.clip(np.digitize(s,edges)-1,0,11)
        for b in range(12):
            sel=idx==b;profiles.append(dict(id=c['id'],bin=b,coordinate_mm=[edges[b],edges[b+1]],adaptive_dense_to_low_axis=direction,points=int(sel.sum()),rho=stats(rho[sel]),k12_mm=stats(a['knn_k_distance_mm'][sel]),normalized_density=stats(a['rho_normalized'][sel]),role='DESCRIPTIVE_ONLY; no fixed world axis or threshold feedback'))
        for row in [x for x in rows if x['id']==c['id']]:
            tier=row['tier'];z=np.load(R/f'local_results/{c["id"]}/{tier}_exact.npz');deleted=np.zeros(len(P),bool);deleted[z['deleted_original_indices']]=True;low=r['largest_low_region'];res=low&~deleted;mask=np.zeros(p['labels'].shape,np.uint8);mask[a['source_v'][res],a['source_u'][res]]=1;n,lab,st,_=cv2.connectedComponentsWithStats(mask);sizes=st[1:,cv2.CC_STAT_AREA];allface=low[m.faces].all(1);anyface=low[m.faces].any(1);retained=~deleted[m.faces].any(1)
            regions.append(dict(id=c['id'],tier=tier,low_region_original_points=int(low.sum()),low_region_residual_points=int(res.sum()),residual_source_components=n-1,residual_components_at_least20=int((sizes>=20).sum()),largest_residual_points=int(sizes.max())if len(sizes)else 0,low_region_all_vertices_face_area_mm2=float(m.area_faces[allface].sum()),low_region_any_vertex_face_area_mm2=float(m.area_faces[anyface].sum()),low_region_remaining_all_vertices_area_mm2=float(m.area_faces[allface&retained].sum()),islands_removed_by_region_rule=0,meaning='Source connectivity/area proxies; not true Type2 labels or anatomical errors'))
    save('metrics/dense_to_low_spatial_profiles.json',profiles);csvsave('metrics/dense_to_low_spatial_profiles.csv',profiles);save('metrics/P1_residual_regions.json',regions);csvsave('metrics/P1_residual_regions.csv',regions);save('provenance/DESCRIPTIVE_SOURCE.json',stamp([Path(__file__)]));print('DESCRIPTIONS',len(profiles),'profile bins;',len(regions),'residual area/component rows')
if __name__=='__main__':main()
