"""Bounded failure diagnostics; no network calls or deletion/parameter changes."""
from common import *
from evaluate import observations
from scipy import ndimage
def main():
    rows_input=[];regions=[];caps=[];profiles=[];crop_rows=[]
    for scene,ii in protocol()['orders'].items():
        for cid in ii:
            n=native(cid);c=cleaned(cid);cp=crop(cid);pid=cp['source_ids'][cp['valid']];h,w=n['depth'].shape;uv=np.c_[pid%w,pid//w];source_xyz=unproject(n['depth'].flat[pid].astype(float),n['T'],uv,n['Kn']);dr=np.linalg.norm(source_xyz-cp['output_X_mm'],axis=1)
            crop_rows.append(dict(source=cid,nearest_native_vs_continuous_crop_ray_XYZ_mm=stats(dr),difference_is_nearest_pixel_sampling_not_calibration=True,invalid_depth_zero=True,exact_original_ID_depth=True))
            lab,N=ndimage.label(n['native_labels']==1);sizes=np.bincount(lab.ravel())[1:];main=1+int(np.argmax(sizes));region=np.where(lab==main,'LARGEST_MASK_COMPONENT_HEAD_PROXY',np.where(lab>0,'OTHER_MASK_COMPONENTS_STALK_SIDE_UNVERIFIED','NON_POLYP'))
            baseline=n['valid'].copy()
            if cid in ['G01_004_ref08','G01_004_ref13','G01_004_ref03','G01_004_growth_r04','G01_004_new_r00','G01_004_growth_r14']:baseline=np.load(A3/'local_results/inputs/V6'/(cid+'.npz'))['valid']
            for label in ['LARGEST_MASK_COMPONENT_HEAD_PROXY','OTHER_MASK_COMPONENTS_STALK_SIDE_UNVERIFIED']:
                a=region==label;regions.append(dict(source=cid,region=label,raw_native_N=int((n['valid']&a).sum()),baseline_N=int((baseline&a).sum()),retained_N=int((c['valid']&a).sum()),new_suppressed_N=int((baseline&~c['valid']&a).sum()),anatomical_identity_not_certified=True))
        ref=ii[0];s=observations(ref)
        for cid in ii[1:]:
            t=cleaned(cid);uv,z=vis.project_camera(t['X'],s['Kn'],s['T']);h,w=s['depth'].shape;ok=np.isfinite(uv).all(1)&(z>0)&(uv[:,0]>=-.5)&(uv[:,0]<w-.5)&(uv[:,1]>=-.5)&(uv[:,1]<h-.5);j=np.flatnonzero(ok);pix=np.floor(uv[j]+.5).astype(int);eligible=s['valid'][pix[:,1],pix[:,0]];j=j[eligible];pix=pix[eligible];cad,_=cast(ringscene(scene),uv[j],s['Kn'],s['T']);visible=~(np.isfinite(cad)&(z[j]>cad+.002));j=j[visible];pix=pix[visible];delta=z[j]-s['depth'][pix[:,1],pix[:,0]]
            rows_input.append(dict(scene=scene,source=cid,reference=ref,projected_eligible_N=len(delta),axial_difference_to_first_source_mm=stats(delta),signed_median_mm=float(np.median(delta))if len(delta)else None,in_front_gt0p25_N=int((delta<-.25).sum()),behind_gt0p25_N=int((delta>.25).sum()),support_within_0p25_N=int((abs(delta)<=.25).sum()),not_physical_GT=True))
        for order in ['forward','reverse']:
            tag=f'{scene}_{order}_F{len(ii)-1}';m=trimesh.load(R/'meshes'/f'{tag}_raw_mm.ply',process=False);ds=mesh_scene(m.vertices,m.faces);a=np.load(R/'local_results'/f'{tag}_MC_identity.npz');allknown=a['face_all8_corners_known']
            for cid in ii:
                n=observations(cid);hit,fid=cast(ds,n['native_uv'],n['Kn'],n['T']);ok=n['visible']&np.isfinite(hit);bad=ok&(abs(hit-n['z'])>.25);ind=np.flatnonzero(bad);known_bad=allknown[fid[ind]]
                caps.append(dict(tag=tag,source=cid,visible_N=int(n['visible'].sum()),bad_first_hit_gt0p25_N=len(ind),bad_first_hit_all8_known_N=int(known_bad.sum()),bad_first_hit_unknown_boundary_N=int((~known_bad).sum()),boundary_proxy_not_causal_truth=True))
            # Exact first-source worst ray diagnostic, complete preserved intersections.
            hit,_=cast(ds,s['native_uv'],s['Kn'],s['T'])
            for scope,extra in [('ORIGINAL_FIXED_DENOMINATOR',np.ones(len(hit),bool)),('ACTUAL_RETAINED_INPUT',s['available'])]:
                eligible=s['visible']&np.isfinite(hit)&extra;indices=np.flatnonzero(eligible);k=indices[np.argmax(abs(hit[eligible]-s['z'][eligible]))];uv=s['native_uv'][k:k+1];result=ds.list_intersections(o3d.core.Tensor(vis.camera_rays(uv,s['Kn'],s['T']).astype(np.float32)));depth=np.sort(result['t_hit'].numpy())
                profiles.append(dict(tag=tag,source=ref,scope=scope,native_pixel_ID=int(s['native_id'][k]),native_uv=uv[0],original_HERO_Z_mm=float(s['z'][k]),first_Mesh_Z_mm=float(hit[k]),all_intersections_Z_mm=depth))
    table('metrics/INPUT_CROSSVIEW_DEPTH_DIFFERENCES.csv',rows_input);table('metrics/HEAD_STALK_SIDE_INPUT_PROXIES.csv',regions);table('metrics/FIRST_HIT_BOUNDARY_ATTRIBUTION.csv',caps);save('metrics/EXACT_WORST_RAY_INTERSECTIONS.json',profiles);table('metrics/CROP_NEAREST_PIXEL_QUANTIZATION.csv',crop_rows)
    print('VISIBILITY_DIAGNOSTICS_COMPLETE; no geometry changes')
if __name__=='__main__':main()
