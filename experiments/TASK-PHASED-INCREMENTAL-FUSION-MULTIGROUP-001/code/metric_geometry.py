"""Existing tissue-base H95 and isolated projected-Feret prototype. No GT/Dxy imports."""
from pipeline import *
from scipy.spatial import ConvexHull
from scipy.spatial.distance import pdist,squareform
def plane_basis(n):
    axis=np.eye(3)[np.argmin(abs(n))];u=np.cross(n,axis);u/=np.linalg.norm(u);v=np.cross(n,u);return u,v
def projected_feret(P,n):
    u,v=plane_basis(n);q=np.c_[P@u,P@v]
    if len(q)<3:return None
    try:hull=ConvexHull(q);ids=hull.vertices;D=squareform(pdist(q[ids]));i,j=np.unravel_index(np.argmax(D),D.shape);a,b=ids[i],ids[j];return dict(value_mm=float(D[i,j]),vertex_ids=[int(a),int(b)],endpoints_projected_mm=q[[a,b]],plane_basis_uv=[u,v],hull_indices=ids,hull_area_mm2=float(hull.volume))
    except Exception:return None
def projection_fill(P,F,n,feret):
    u,v=np.array(feret['plane_basis_uv']);q=np.c_[P@u,P@v];step=cfg()['projection_grid_mm'];lo=q.min(0);wh=np.ceil((q.max(0)-lo)/step).astype(int)+5
    if np.any(wh>4000):return dict(fill_fraction=0.,reason='FOOTPRINT_TOO_LARGE_FOR_FIXED_DIAGNOSTIC_GRID')
    xy=np.rint((q-lo)/step).astype(np.int32)+2;mask=np.zeros((wh[1],wh[0]),np.uint8);hull=np.zeros_like(mask)
    for f in F:cv2.fillConvexPoly(mask,xy[f],1)
    cv2.fillConvexPoly(hull,xy[np.array(feret['hull_indices'])],1);return dict(fill_fraction=float(mask.sum()/max(1,hull.sum())),original_triangle_pixels=int(mask.sum()),hull_pixels=int(hull.sum()),grid_mm=step,meaning='Projected original/subdivided source faces; raster used only for observed-fill diagnostic, not to add geometry')
def measurement_mesh(sc,mode):
    parts=[];source_maps=[];allarea=0.;offset=0
    for rank,cid in enumerate(sc['reference_order']):
        if mode=='primary'and rank>0:continue
        if mode=='second'and rank>1:continue
        a=dict(np.load(R/f'local_results/scenes/{sc["id"]}/{cid}_faces_exact.npz'));status=a['face_status'];take=np.isin(status,[0,5]);full=np.ones(len(status),bool)if rank==0 else status==5;allarea+=float(area(a['XYZ_mm'],a['faces'][full]).sum());F=a['faces'][take]
        if not len(F):continue
        ids=np.unique(F);back=np.full(len(a['XYZ_mm']),-1,int);back[ids]=np.arange(len(ids));parts.append(mesh(a['XYZ_mm'][ids],back[F]));source_maps += [dict(reference=cid,source_vertex_id=int(i)if i<int(a['original_vertex_N'])else None,source_edge_original_ids=a['source_edge_original_ids'][i].tolist(),parent_mesh_file=str(R/f'local_results/scenes/{sc["id"]}/{cid}_faces_exact.npz'))for i in ids];offset+=len(ids)
    if not parts:return None,[],allarea
    return trimesh.util.concatenate(parts),source_maps,allarea
def main():
    verify();o=o3d_module();old=load(PHASE/'metrics/D3_height_ROI_trials.json');rows=[];diam=[]
    save('provenance/METRIC_EXECUTION_FROZEN.json',dict(**stamp([Path(__file__),R/'config.json',PHASE/'metrics/D3_height_ROI_trials.json']),historical_G01_fits_reused=True,formal_Dxy_imports=False,nominal_group_sizes_used=False))
    for sc in load(R/'metrics/B_scenes.json'):
        bymode={mode:scene_points(sc,mode)[0]for mode in ['primary','second','core']}
        for cid in sc['references']:
            s=source(cid);b=background(cid);p=s['p'];dist=cv2.distanceTransform((p['labels']!=1).astype(np.uint8),cv2.DIST_L2,5)[b['uv'][:,1],b['uv'][:,0]];head=cohorts(s['a'],p)['head_source_proxy'];center=np.median(s['P'][head],0)
            for lower,upper in cfg()['D3_base_pixel_ROIs']:
                sel=(dist>=lower)&(dist<=upper)&b['quality'];Q=b['P'][sel];base=dict(scene=sc['id'],group=sc['group'],reference=cid,ROI_pixels=[lower,upper],background_input_N=len(Q),camera_condition=s['c']['condition'],source_camera_qualified=s['c']['source_camera_qualified'],Ring_plane_used=False);hist=next((x for x in old if x['reference']==cid and x['ROI_pixels']==[lower,upper]),None)
                if hist is not None:
                    plane=np.array(hist['plane'])if'plane'in hist else None;fraction=hist.get('inlier_fraction',0);reported=hist.get('inlier_N',0);fitpass=hist['physical_height_mm']is not None;origin='EXACT_PREVIOUS_PHASE_D_PLANE_AND_USABILITY';assert len(Q)==hist['background_input_N']
                elif len(Q)>=cfg()['D3_plane_minimum_points']:
                    o.utility.random.seed(cfg()['random_seed']);cloud=o.geometry.PointCloud(o.utility.Vector3dVector(Q));coeff,ii=cloud.segment_plane(distance_threshold=cfg()['D3_plane_inlier_distance_mm'],ransac_n=3,num_iterations=cfg()['D3_plane_iterations']);plane=np.array(coeff);plane/=np.linalg.norm(plane[:3]);plane*=1 if center@plane[:3]+plane[3]>=0 else-1;fraction=len(ii)/len(Q);reported=len(ii);fitpass=fraction>=cfg()['D3_plane_minimum_inlier_fraction'];origin='SAME_FROZEN_RANSAC_METHOD_ON_EXISTING_BACKGROUND'
                else:plane=None;fraction=0;reported=0;fitpass=False;origin='INSUFFICIENT_BACKGROUND'
                eligible=fitpass and bool(s['c']['source_camera_qualified']);code=cid+'_'+str(upper);folder=R/'local_results/metric_geometry';folder.mkdir(parents=True,exist_ok=True);inlier=np.zeros(len(Q),bool)if plane is None else abs(Q@plane[:3]+plane[3])<=cfg()['D3_plane_inlier_distance_mm'];np.savez_compressed(folder/(code+'.npz'),background_XYZ_mm=Q,background_RGB=b['rgb'][sel],background_source_uv=b['uv'][sel],background_original_ids=np.flatnonzero(sel),inlier_by_frozen_plane=inlier,plane=np.full(4,np.nan)if plane is None else plane,Polyp_XYZ_mm=bymode['core'],Polyp_signed_h_mm=np.full(len(bymode['core']),np.nan)if plane is None else bymode['core']@plane[:3]+plane[3]);heights={mode:None if plane is None else float(np.quantile(P@plane[:3]+plane[3],.95))for mode,P in bymode.items()};row=dict(**base,plane=plane,inlier_N_reported=reported,inlier_fraction=fraction,plane_residual_inlier_N=int(inlier.sum()),numeric_fit_pass=fitpass,base_metric_usable=eligible,origin=origin,H95_mm=heights['core']if eligible else None,diagnostic_H95_candidate_mm=heights['core'],per_model_candidate_H95_mm=heights,Polyp_exposure_N={k:len(v)for k,v in bymode.items()},base_status='MODEL_CONDITIONAL_BASE'if eligible else'NOT_EVALUABLE_UNQUALIFIED_CAMERA'if fitpass else'NOT_EVALUABLE_BASE_FIT_REJECTED',GT_error=None);rows.append(row)
                for mode in ['primary','second','core']:
                    M,mapping,totalarea=measurement_mesh(sc,mode);reason=[];f=None;fill=None;frac=0
                    if not eligible:reason.append(row['base_status'])
                    if M is None:reason.append('NO_OBSERVATION_SUPPORTED_FACE_SET')
                    else:
                        frac=float(M.area/totalarea)if totalarea else 0
                        if frac<cfg()['metric_minimum_supported_area_fraction']:reason.append('OBSERVED_MODEL_SURFACE_SUPPORT_INSUFFICIENT')
                        if plane is not None:
                            f=projected_feret(np.asarray(M.vertices),plane[:3])
                            if f is None:reason.append('DEGENERATE_PROJECTED_FOOTPRINT')
                            else:
                                fill=projection_fill(np.asarray(M.vertices),M.faces,plane[:3],f)
                                if fill['fill_fraction']<cfg()['projection_hull_fill_minimum']:reason.append('OPEN_PROJECTION_NOT_SUFFICIENTLY_SUPPORTED')
                    endpoint=[]
                    if f is not None:
                        for idx in f['vertex_ids']:endpoint.append(dict(**mapping[idx],XYZ_mm=M.vertices[idx]))
                    diam.append(dict(scene=sc['id'],group=sc['group'],base_reference=cid,ROI_pixels=[lower,upper],model=mode,identity='3D MODEL PROJECTED DIAMETER — PROTOTYPE',status='MODEL_CONDITIONAL_PROTOTYPE'if not reason else'NOT_EVALUABLE',Dproj_mm=f['value_mm']if f is not None and not reason else None,diagnostic_candidate_Dproj_mm=f['value_mm']if f is not None else None,not_evaluable_reasons=reason,base_plane=plane,supported_model_area_fraction=frac,projection_support=fill,endpoints=endpoint,excluded='CONFLICT/UNKNOWN and rejected density candidates; no historical measurement fallback',GT_error=None))
        print('C_D',sc['id'],'conditions',sum(x['scene']==sc['id']for x in rows),'usable',sum(x['scene']==sc['id']and x['base_metric_usable']for x in rows),flush=True)
    save('metrics/C_height_geometry.json',rows);csvsave('metrics/C_height_geometry.csv',rows);save('metrics/D_projected_diameter.json',diam);csvsave('metrics/D_projected_diameter.csv',diam)
if __name__=='__main__':main()
