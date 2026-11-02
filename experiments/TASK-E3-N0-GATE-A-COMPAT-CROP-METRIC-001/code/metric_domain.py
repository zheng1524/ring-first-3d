"""Two diagnostic domains; do not select/freeze a physical ROI after an outlier stop."""
from crop import *
def make_domain(X):
    Q=np.r_[X,ringmesh().vertices];lo=Q.min(0);hi=Q.max(0);margin=max(2.,.1*np.ptp(Q,axis=0).max());L=float(np.ceil((np.ptp(Q,axis=0).max()+2*margin)*1000)/1000);O=(lo+hi)/2-L/2;F=np.eye(4);F[:3,:3]/=L;F[:3,3]=-O/L;inv=np.linalg.inv(F)
    return dict(O_mm=O,L_mm=L,N=128,voxel_mm=L/128,resolution_model=1/128,metric_to_model=F,model_to_metric=inv,world_cube_min_mm=O,world_cube_max_mm=O+L,model_bbox=[[0,0,0],[1,1,1]],world_to_model='(X_mm-O_mm)/L_mm',ring_outer_diameter_voxels=12.4/(L/128),source_extent_min_mm=lo,source_extent_max_mm=hi)
def main():
    cfg=config();ss={cid:native(cid)for cid in IDS};far={};insidepoints=[]
    for cid,s in ss.items():
        d=distance(mesh_scene(s['P'],s['F']),s['X']);far[cid]=d>1.;insidepoints.append(s['X'][d<=1.]);np.savez_compressed(R/'local_results'/(cid+'_native_raw_diagnostic.npz'),native_id=s['native_id'],distance_to_own_original_raw_faces_mm=d,diagnostic_far_gt_1mm=d>1.)
    full=make_domain(np.concatenate([s['X']for s in ss.values()]));body=make_domain(np.concatenate(insidepoints));domains={'ALL_INPUTS':full,'RAW_AGREEMENT_DIAGNOSTIC_ONLY':body};rows=[]
    for name,dom in domains.items():
        L=dom['L_mm'];O=np.asarray(dom['O_mm']);checks=[]
        for cid,s in ss.items():
            X=s['X'];model=(X-O)/L;back=model*L+O;err=np.linalg.norm(back-X,axis=1);T=s['T'].copy();T[:3,3]=(T[:3,3]-O)/L;uv=s['native_uv'];z=s['depth'][uv[:,1],uv[:,0]].astype(float)/L;from_camera=unproject(z,T,uv,s['Kn']);cerr=np.linalg.norm((from_camera-model)*L,axis=1);out=((model<0)|(model>=1)).any(1)
            row=dict(domain=name,source=cid,native_point_denominator=len(X),out_of_grid_N=int(out.sum()),all_points_retained_as_inputs=True,diagnostic_far_N=int(far[cid].sum()),world_model_roundtrip_max_mm=float(err.max()),camera_depth_model_consistency_max_mm=float(cerr.max()),occupied_voxel_N=len(np.unique(np.floor(model[~out]*128).astype(int),axis=0)),voxel_mm=L/128,model_scale_per_mm=1/L,c2w_rotation_changed=False)
            rows.append(row);checks.append(row)
        ring=np.asarray(ringmesh().vertices);rmodel=(ring-O)/L;rb=rmodel*L+O;dom['ring_inverse_max_mm']=float(np.linalg.norm(rb-ring,axis=1).max());dom['ring_outer_diameter_inverse_mm']=float(np.ptp(rb,axis=0)[:2].max());dom['per_source']=checks
    ratio=full['L_mm']/body['L_mm'];stop=ratio>1.5 or any(r['out_of_grid_N']for r in rows if r['domain']=='RAW_AGREEMENT_DIAGNOSTIC_ONLY')
    save('METRIC_TRANSFORM.json',dict(status='REQUEST_RESEARCHER_ROI_DECISION'if stop else 'CANDIDATE_FOR_PM_REVIEW',active_transform=None,domains=domains,all_to_diagnostic_side_ratio=ratio,source_input_deletions=0,candidate_B_is_not_an_input_filter=True,full_domain_can_enclose_all_points=True,physical_ROI_frozen=False,reason='Known raw/native far candidates inflate a single128cube; diagnostic alternative leaves original legal observations OUT_OF_GRID. No automatic deletion, clipping or domain selection.',Gate_B_authorized=False))
    table('MODEL_DOMAIN_DIAGNOSTICS.csv',rows);save('config/METRIC_STOP.json',dict(stop_requires_researcher=bool(stop),full_cube_L_mm=full['L_mm'],full_voxel_mm=full['voxel_mm'],full_ring_outer_diameter_voxels=full['ring_outer_diameter_voxels'],diagnostic_cube_L_mm=body['L_mm'],diagnostic_voxel_mm=body['voxel_mm'],diagnostic_OUT_OF_GRID_total=sum(r['out_of_grid_N']for r in rows if r['domain']=='RAW_AGREEMENT_DIAGNOSTIC_ONLY'),side_inflation_ratio=ratio,input_pixels_deleted=0,active_model_domain=None))
    print('METRIC_STOP',load(R/'config/METRIC_STOP.json'),flush=True)
if __name__=='__main__':main()
