"""Finite actual-asset queries and evidence records. No observation field is built."""
from common import *

def main():
    freeze('BEFORE_CASEBOOK_REV002.json'if(R/'provenance/BEFORE_CASEBOOK.json').exists()else'BEFORE_CASEBOOK.json');rows=[];missing=[];queries=[];tax=[]
    facts=readrows(R/'metrics/E3_RAW_SURFACE_DIAGNOSTICS.csv');pairs=readrows(R/'metrics/E3_VIEW_COVERAGE.csv')
    for c in D['references']:
        cid=c['id'];s=source(cid);P,F=s['P'],s['F'];Q=P[F].mean(1);ff=np.load(R/f'local_results/face_facts/{cid}.npz');N=ff['oriented_face_normals'];cad=ring(c['ring']);radius=np.linalg.norm(Q[:,:2],axis=1)
        # Region names describe coordinates/proxies, never manual anatomy labels.
        center=Q.mean(0);head=np.linalg.norm(Q-center,axis=1);near=np.hypot(radius-np.ptp(cad.bounds,axis=0)[0]/2,Q[:,2])
        radial=np.sqrt(np.sum((Q[:,:2]-center[:2])**2,axis=1));stalk=s['clean']['protected_possible_stalk'][F].any(1);protected_Ring=s['clean']['protected_Ring'][F].any(1)
        choices={'HEAD':int(np.argmin(head)),'RING_NEAR':int(np.argmin(near)),'ABOVE_RING':int(np.argmax(Q[:,2])),
            'BELOW_RING':int(np.argmin(Q[:,2])),'SIDE':int(np.argmax(radial)),
            'THIN_BASE_PROXY':int(np.flatnonzero(stalk)[0])if stalk.any()else None,
            'STRETCH_PROXY':int(np.flatnonzero(ff['stretch_proxy'])[0])if ff['stretch_proxy'].any()else None,
            'MINOR_COMPONENT_PROXY':int(np.flatnonzero(ff['minor_proxy'])[0])if ff['minor_proxy'].any()else None}
        pp=[r for r in pairs if r['A']==cid];peer=sorted(pp,key=lambda r:(-float(r['source_mesh_overlap_fraction']),r['B']))[0]['B'];B=source(peer)
        for region,fid in choices.items():
            if fid is None:
                rows.append(dict(case_id=cid+'_'+region,scene=c['scene_id'],source_id=cid,region=region,status='UNKNOWN_NO_PROXY_CANDIDATE',manual_anatomy_confirmed=False));continue
            X=Q[fid];uv,z=vis.project_camera(X[None],s['K'],s['T']);cadZ=source_camera(cid).cast(uv)['t_hit'].numpy()[0];srcZ,_=cast_mesh(cid,uv)
            uB,zB=vis.project_camera(X[None],B['K'],B['T']);inside=bool(zB[0]>0 and 0<=uB[0,0]<640 and 0<=uB[0,1]<360)
            hit,faceB=cast_mesh(peer,uB)if inside else(np.array([np.inf]),np.array([-1]));cadB=source_camera(peer).cast(uB)['t_hit'].numpy()[0]if inside else np.inf
            blocked=bool(np.isfinite(cadZ)and z[0]>cadZ+.002);otherblocked=bool(np.isfinite(cadB)and zB[0]>cadB+.002)
            delta=float(zB[0]-hit[0])if inside and np.isfinite(hit[0])else None
            rawuv=s['uv'][F[fid]].tolist();family=next(r for r in readrows(R/'metrics/E3_SOURCE_AND_VIEW_MANIFEST.csv')if r['source_id']==cid)['source_family']
            rows.append(dict(case_id=cid+'_'+region,scene=c['scene_id'],physical_group=c['group'],source_id=cid,region=region,status='CONDITIONAL_GEOMETRY_PROXY',
                original_face_id=fid,original_vertex_ids=F[fid],original_vertex_pixels=rawuv,centroid_pixel=uv[0],XYZ_mm=X,camera_K=s['K'],camera_c2w=s['T'],
                source_camera_screened=eligible(c),oriented_normal_toward_camera=N[fid],source_family=family,source_axial_Z_mm=float(z[0]),source_raw_first_Z_mm=float(srcZ[0]),
                CAD_first_Z_mm=float(cadZ)if np.isfinite(cadZ)else None,CAD_in_front_of_candidate=blocked,peer=peer,peer_pixel=uB[0],peer_original_face_id=int(faceB[0])if np.isfinite(hit[0])else None,
                peer_CAD_in_front_of_candidate=otherblocked,projected_depth_difference_mm=delta,
                cross_source_correspondence_qualification='NOT_CERTIFIED; highest sampled overlap is not an identity match',
                conflict_class='DISTINCT_SURFACES_OR_OCCLUSION'if blocked or otherblocked else'CORRESPONDENCE_UNRESOLVED',
                physical_surface_depth_error_mm=None,free_space_evidence='CONDITIONAL_ONLY_IF_TRUSTED_FIRST_SURFACE; no blanket ROI-entry outside assumption',
                cleaned_kept=bool(ff['clean_kept'][fid]),F3_kept=bool(ff['F3_kept'][fid]),possible_stalk_proxy=bool(stalk[fid]),Ring_protection_proxy=bool(protected_Ring[fid]),manual_anatomy_confirmed=False,
                anatomical_region='NOT_PROVIDED; HEAD/SIDE/THIN are deterministic location/protection proxies'))
        own=np.load(R/f'local_results/own/{cid}.npz');mask=s['labels']==1;raw=np.isfinite(own['raw_Z']);behind=mask&raw&(own['raw_Z']>own['CAD_Z']+.002);no_triangle=mask&~raw
        missing.append(dict(scene=c['scene_id'],source=cid,full_Polyp_Mask_N=int(mask.sum()),no_raw_first_triangle_N=int(no_triangle.sum()),
            raw_triangle_behind_CAD_positive_Mask_N=int(behind.sum()),no_visible_triangle_total_N=int((mask&~own['visible']).sum()),
            interpretation='no raw first triangle may be mesh-edge/raster gap; positive Mask vs CAD is a contradiction, not certified legitimate occlusion',
            sample_missing_pixels=np.argwhere(no_triangle)[np.linspace(0,max(0,no_triangle.sum()-1),min(8,no_triangle.sum())).astype(int)][:,::-1]if no_triangle.any()else[]))
        # Only 3 queries / source, no scalar grid or learned field.
        fid=choices['HEAD'];X=Q[fid];n=N[fid];test=np.array([X,X+.05*n,X-.05*n]);sys.path.insert(0,str(VENDOR));import open3d as o3d
        closest=mesh_scene(cid).compute_closest_points(o3d.core.Tensor(test.astype(np.float32)))['points'].numpy();distance=np.linalg.norm(test-closest,axis=1)
        for j,kind in enumerate(['ORIGINAL_TRIANGLE_CENTROID','CAMERA_ORIENTED_PLUS_005MM','CAMERA_ORIENTED_MINUS_005MM']):
            uv,z=vis.project_camera(test[j:j+1],s['K'],s['T']);hit,_=cast_mesh(cid,uv);queries.append(dict(source=cid,original_face_id=fid,query_kind=kind,XYZ_mm=test[j],
                unsigned_original_triangle_distance_mm=float(distance[j]),projective_first_Z_minus_query_Z_mm=float(hit[0]-z[0])if np.isfinite(hit[0])else None,
                signed_Euclidean_distance_mm=None,sign_status='NOT_DEFINED_FOR_OPEN_MESH',test='CENTROID_ZERO_CHECK'if j==0 else'LOCAL_SIGN_NOT_GLOBAL_INTERIOR',
                numerical_check_pass=bool(distance[j]<2e-5)if j==0 else bool(distance[j]<=.05002)))
    table('metrics/E3_CASEBOOK_POINTS.csv',rows);table('metrics/E3_OBSERVED_WITHOUT_TRIANGLE.csv',missing);table('metrics/E3_CONTRACT_QUERIES.csv',queries)
    for sid in scenes():
        f=[r for r in facts if r['scene']==sid];p=[r for r in pairs if r['scene']==sid];m=[r for r in missing if r['scene']==sid];cases=[r for r in rows if r['scene']==sid]
        values={
            'E1':('UNKNOWN',0,'certified same-physical-surface systematic depth error; no independent correspondence labels'),
            'E2':('CONDITIONAL',sum(int(r['diagnostic_separated_layers_N'])for r in p),'directed sampled projected separations only; repeated points/pairs; not physical error count'),
            'E3':('CONDITIONAL',sum(int(r['stretched_face_proxy_N'])for r in f),'original-face edge/footprint >8 proxy; not certified false anatomy'),
            'E4':('CONDITIONAL',sum(int(r['minor_component_proxy_N'])for r in f),'components below 1% largest source area; not certified false fragments'),
            'E5':('UNKNOWN',0,'multiple candidate layers occur; certified false duplicate physical surfaces=0'),
            'E6':('VERIFIED',sum(r['no_raw_first_triangle_N']for r in m),'source Polyp pixels lacking raw triangle hit; includes original mesh/raster boundary, 3D location unknown'),
            'E7':('VERIFIED',sum(r['raw_triangle_behind_CAD_positive_Mask_N']for r in m),'fixed CAD precedes raw candidate along positive-Mask rays; sensor/pose/Mask/geometry contradiction unresolved'),
            'E8':('UNKNOWN',0,'no certified count of truly unobservable anatomy; unknown spatial evidence is not absent anatomy'),
            'E9':('VERIFIED',sum(not eligible(c)for c in D['references']if c['scene_id']==sid),'reference cameras failing archived screen; pair correspondence also unresolved')}
        for key,(status,N,meaning)in values.items():tax.append(dict(scene=sid,physical_group=sid.split('_')[0],error_code=key,status=status,N=N,denominator_source_N=len(f),meaning=meaning,
            SAME_SURFACE_DEPTH_CONFLICT_certified_N=0,DISTINCT_SURFACES_OR_OCCLUSION_case_N=sum(r.get('conflict_class')=='DISTINCT_SURFACES_OR_OCCLUSION'for r in cases),
            CORRESPONDENCE_UNRESOLVED_case_N=sum(r.get('conflict_class')=='CORRESPONDENCE_UNRESOLVED'for r in cases),manual_true_anatomy_labels='NOT_PROVIDED'))
    table('metrics/E3_ERROR_TAXONOMY.csv',tax);save('provenance/CASEBOOK_STATUS.json',dict(case_records=len(rows),actual_queries=len(queries),all_numeric_query_checks=all(q['numerical_check_pass']for q in queries),
        same_surface_certified=0,LocalField_implemented=False,geometry_modified=False));print('E3_CASEBOOK_COMPLETE',len(rows),len(queries),flush=True)
if __name__=='__main__':main()
