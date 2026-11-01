"""Fixed real original-face candidates, including unique/edge/extension cohorts."""
from context import *
GROUP_BITS={'BASE':1,'OWN_VISIBLE':2,'OPEN_BOUNDARY':4,'SOURCE_UNIQUE_PROXY':8,'STRETCH_PROXY':16,'MINOR_COMPONENT_PROXY':32,'RING_NEAR':64,'SMOOTH_INTERIOR_PROXY':128,'POSSIBLE_STALK_PROXY':256}
def candidates(cid):
    z=np.load(R/'local_results/candidates'/f'{cid}.npz');return {k:z[k]for k in z.files}
def main():
    allow_manifest();save('provenance/CANDIDATE_GROUP_BITS.json',GROUP_BITS);summary=[];bindings=[]
    sys.path.insert(0,str(VENDOR));import open3d as o3d
    for cid in IDS:
        s=source(cid);m=model(cid);row=next(r for r in load(B/'LOCAL_FIELD_MANIFEST.json')['fields']if r['source_id']==cid);folder=Path(row['runtime_sample_cache'])
        unique_path=folder/'coverage_flags.npz';a=register(unique_path);bindings.append(dict(source=cid,flag_cache=a,role='E3-B fixed unique-voxel flag only; not geometry input'))
        unique=np.load(unique_path)['unique_among_all_sources'];assert len(unique)==len(s['F'])
        X=m.center;cad_distance=camera(cid).scene.compute_distance(o3d.core.Tensor(X.astype(np.float32))).numpy();near=cad_distance<=protocol()['candidates']['Ring_near_distance_mm']
        # Own legal visibility is queried through the unchanged B1 implementation.
        fpath=folder/'original_face_evidence.npz';register(fpath);bindings.append(dict(source=cid,flag_cache=asset(fpath),role='E3-B own-visible flag only; same original face index, no geometry taken from cache'))
        visible=np.load(fpath)['valid_surface'];assert len(visible)==len(X)
        minor=m.area_by_component[m.component]<.01*m.area_by_component.max();smooth=(~m.boundary_face)&(~m.stretch)&(~minor)&(m.coherence>=.85)
        masks=dict(BASE=np.ones(len(X),bool),OWN_VISIBLE=visible,OPEN_BOUNDARY=m.boundary_face,SOURCE_UNIQUE_PROXY=unique,STRETCH_PROXY=m.stretch,MINOR_COMPONENT_PROXY=minor,RING_NEAR=near,SMOOTH_INTERIOR_PROXY=smooth,POSSIBLE_STALK_PROXY=s['clean']['protected_possible_stalk'][s['F']].any(1))
        budgets=dict(BASE=2048,OWN_VISIBLE=256,OPEN_BOUNDARY=256,SOURCE_UNIQUE_PROXY=256,STRETCH_PROXY=256,MINOR_COMPONENT_PROXY=128,RING_NEAR=256,POSSIBLE_STALK_PROXY=128)
        selected=np.unique(np.concatenate([fixed_indices(masks[k],n)for k,n in budgets.items()]));assert len(selected)<=3584
        tags=np.zeros(len(selected),np.uint16)
        for k,mask in masks.items():tags[mask[selected]]|=GROUP_BITS[k]
        q=m.query(X[selected]);qa=pf(cid).query(X[selected]);origin_align=np.isfinite(qa['native_Z_mm'])&np.isfinite(qa['original_mesh_Z_mm'])&(abs(qa['native_Z_mm']-qa['original_mesh_Z_mm'])<=protocol()['native_Raw_alignment_mm']);assert q['raw_udf_mm'].max()<=cfg()['zero_mm']
        p=R/'local_results/candidates';p.mkdir(exist_ok=True);np.savez_compressed(p/f'{cid}.npz',face_id=selected,XYZ=X[selected],normal=m.N[selected],area=s['area'][selected],tags=tags,
            own_visible=q['valid_surface'],own_cad=q['cad_occluded'],own_unknown=q['unknown'],own_nearest_competition=q['reliability_factors']['nearest_competition'],
            own_coherence=m.coherence[selected],own_incidence=q['reliability_factors']['incidence_abs'],origin_native_Raw_alignment=origin_align,cad_distance_mm=cad_distance[selected])
        summary.append(dict(source_id=cid,scene=s['c']['scene_id'],role=ROLES[cid],all_original_faces=len(s['F']),candidate_N=len(selected),candidate_original_face_ID_SHA256=array_hash(selected),candidate_XYZ_SHA256=array_hash(X[selected]),
            own_visible_N=int(q['valid_surface'].sum()),**{k+'_N':int((tags&bit!=0).sum())for k,bit in GROUP_BITS.items()},all_original_faces_retained=True))
        print('CANDIDATES',cid,len(selected),flush=True)
    table('metrics/CANDIDATE_COHORT.csv',summary);save('provenance/INHERITED_FLAG_BINDINGS.json',bindings);save('provenance/CANDIDATES_FROZEN.json',dict(rows=summary,candidate_N=sum(r['candidate_N']for r in summary),
        all_original_faces=461023,flags_only=True,point_sampling_before_pair_evidence=True,fixed_target_denominator='all sampled candidates, unchanged for V0-V3 and both observer stages'))
if __name__=='__main__':main()
