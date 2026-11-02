"""Post-hoc source tracing, never input rejection or output deletion."""
from hero_tsdf_adapter import *
def main():
    allrawP=[];allrawF=[];offset=0
    for cid in G1:
        s=source(cid);allrawP.append(s['P']);allrawF.append(s['F']+offset);offset+=len(s['P'])
    sc=mesh_scene(np.concatenate(allrawP),np.concatenate(allrawF));m=output_mesh('G1');X=np.asarray(m.triangles_center);d=distance(sc,X);area=m.area_faces;f=int(np.argmax(d));xc=X[f];r=[]
    for cid in G1:
        s=source(cid);a=HEROToTSDFAdapter.from_source(s,cfg()['depth_trunc_mm']);vv,uu=np.nonzero(a.valid);uv=np.c_[uu,vv];z=s['depth'][vv,uu];P=unproject(z,s['T'],uv,s['Kn']);sr=mesh_scene(s['P'],s['F']);dn=distance(sr,P);ed=cv2.distanceTransform(a.valid.astype(np.uint8),cv2.DIST_L2,5)[vv,uu]
        p,zp=vis.project_camera(xc[None],s['Kn'],s['T']);u,v=np.floor(p[0]+.5).astype(int);inside=0<=v<s['depth'].shape[0]and 0<=u<s['depth'].shape[1]
        r.append(dict(source=cid,native_Polyp_N=len(P),native_points_over_1mm_from_own_raw_faces_N=int((dn>1).sum()),native_far_points_within2px_Mask_boundary_N=int(((dn>1)&(ed<=2)).sum()),native_max_distance_to_own_raw_faces_mm=float(dn.max()),farthest_G1_patch_projected_u=p[0,0],farthest_G1_patch_projected_v=p[0,1],farthest_G1_patch_axial_depth_mm=zp[0],native_depth_mm=s['depth'][v,u]if inside else np.nan,native_label=int(cv2.resize(s['labels'],(640,352),interpolation=cv2.INTER_NEAREST)[v,u])if inside else -1))
    table('NATIVE_RAW_DISCRETIZATION_DIAGNOSTICS.csv',r)
    # Extra clearly labeled post-hoc failure case, not a changed formal metric denominator.
    cid=max(r,key=lambda t:t['native_points_over_1mm_from_own_raw_faces_N'])['source'];s=source(cid);uv,z=vis.project_camera(xc[None],s['K'],s['T']);cases=load(R/'config/FAILURE_CASES.json');cases.append(dict(case_id='F4',source_id=cid,original_face_id=None,output_G1_face_id=f,X_mm=xc[0],Y_mm=xc[1],Z_mm=xc[2],pixel_u=uv[0,0],pixel_v=uv[0,1],selection_rule='POSTHOC: largest G1 original-six-Mesh distance; source with most native-vs-own-Raw far points (not asserted causal origin)',G0_distance_mm=float(distance(mesh_scene(output_mesh('G0').vertices,output_mesh('G0').faces),xc[None])[0]),G1_distance_mm=float(d[f]),status='OBSERVED',cause_status='HYPOTHESIS_UNRESOLVED',observation='G1 far surface relative to all original raw faces',hypothesis='raw triangulation omits unsupported depth discontinuities; native Polyp depths still integrated by TSDF; camera vs depth unresolved',evidence='figures/Fig4_failure_mechanisms.png'))
    save('config/FAILURE_CASES.json',cases);table('TSDF_FAILURE_CASES.csv',cases)
    save('config/EXTENSION_DIAGNOSIS.json',dict(posthoc=True,G1_total_area_mm2=float(area.sum()),area_gt_1mm_from_all_raw_faces_mm2=float(area[d>1].sum()),area_gt_1mm_fraction=float(area[d>1].sum()/area.sum()),max_output_to_raw_faces_mm=float(d.max()),farthest_output_face_id=f,farthest_X_mm=xc,raw_faces_unchanged=True,native_depths_unchanged=True,source_trace=r))
    print('EXTENSION',d.max(),area[d>1].sum(),r,flush=True)
if __name__=='__main__':main()
