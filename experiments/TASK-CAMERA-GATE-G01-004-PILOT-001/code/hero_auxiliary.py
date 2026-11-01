"""Test 3 only: immutable original XYZ into real target RGB; never pose fitting."""
from common import *
PHASED=Path('/home/liu/ring_first_3d_phase_d/experiments/TASK-PHASED-MAIN-SURFACE-CROSSVIDEO-001')
# Exact historical raster; its one config lookup is supplied by the frozen pilot.
ns=dict(np=np,vis=vis,R=R,load=lambda p:dict(CAD_occlusion_tolerance_mm=cfg['CAD_occlusion_tolerance_mm']))
raster=extract(PHASED/'code/source_rgb_projection.py',['raster'],ns)['raster']
@lru_cache(None)
def original_xyz(cid):
    c=CC[cid];s=source(cid);z=np.load(c['source_points']);P=z['points_mm'] if 'points_mm' in z else z['XYZ_mm'];uv=z['uv'] if 'uv' in z else z['source_uv']
    F=z['original_faces'];p=np.load(c['pack']);uv=uv.astype(int)
    rays=vis.camera_rays(uv,s['K'],s['T']);back=rays[:,:3]+rays[:,3:]*p['depth_mm'][uv[:,1],uv[:,0],None]
    assert np.max(abs(back-P))<1e-6,'original XYZ not archived direct depth'
    C=s['RGB'][uv[:,1],uv[:,0]]/255.;return dict(P=P,uv=uv,C=C,F=F)
def matching_offset(a,b,T):
    plan=next((p for p in load(R/'config/RGB_ONLY_METHOD_SELECTION.json') if set([a,b])==set([p['A'],p['B']])),None)
    if plan is None or plan['selected_method'] is None:return dict(N=0,reason='NO_SUFFICIENT_RGB_PAIR; not substituted by HERO correspondences')
    d=match_data(plan['A'],plan['B'],plan['selected_method']);sel=d['independent_good'];p,q=(d['p'][sel],d['q'][sel]) if a==plan['A'] else (d['q'][sel],d['p'][sel]);x=original_xyz(a);dist,ii=cKDTree(x['uv']).query(p);sel=dist<=1.
    proj,depth=vis.project_camera(x['P'][ii[sel]],source(b)['K'],T);diff=proj-q[sel];good=np.isfinite(diff).all(1)&(depth>0);diff=diff[good]
    return dict(N=len(diff),median_dx_px=float(np.median(diff[:,0])) if len(diff) else None,median_dy_px=float(np.median(diff[:,1])) if len(diff) else None,error_px=stats(np.linalg.norm(diff,axis=1)),method=plan['selected_method'],source_XYZ_nearest_source_UV_within_px=1.,HERO_depth_uncertainty_and_RGB_correspondence_uncertainty_conflated=True)
def project(a,b,T,tag):
    x=original_xyz(a);s=source(b);sc=camera(b,T);ids=np.arange(len(x['P']));pred=raster(x['P'],x['C'],np.ones(len(ids),int),ids,s['K'],T,(360,640),sc)
    active=pred['kind']==1;pol=s['labels']==1;N=int(pol.sum());agree=active&pol;img=s['RGB'];err=np.mean(abs(pred['RGBA'][:,:,:3].astype(float)-img),axis=2)
    row=dict(source=a,target=b,target_pose=tag,source_original_point_N=len(ids),source_original_face_N=len(x['F']),target_Polyp_denominator=N,projected_visible_pixel_N=int(active.sum()),projected_Polyp_pixel_N=int(agree.sum()),target_Polyp_coverage=float(agree.sum()/max(1,N)),projected_Polyp_precision=float(agree.sum()/max(1,active.sum())),CAD_hidden=pred['CAD_hidden'],positive_points=pred['positive_points'],in_bounds_points=pred['in_bounds_points'],RGB_on_Polyp_MAE=stats(err[agree]),XYZ_matched_projection_offset=matching_offset(a,b,T),used_for_camera_qualification=False,source_XYZ_deformed=False,meaning='raw HERO consistency auxiliary; not depth/camera ground truth')
    folder=R/'runtime/projections';folder.mkdir(exist_ok=True);np.savez_compressed(folder/f'{short(a)}__{short(b)}_{tag}.npz',**pred)
    return row
def main():
    assert (R/'config/ORIGINAL_TEST12_FROZEN.json').exists() and (R/'config/BOUNDED_CORRECTION_RESULTS.json').exists()
    freeze('BEFORE_HERO_AUXILIARY.json',dict(original_Test12_already_complete=True,raw_geometry_input_only=True,no_XYZ_transformation=True))
    rows=[]
    for b in IDS:
        for a in IDS:
            if a==b:continue
            rows.append(project(a,b,source(b)['T'],'ORIGINAL'))
        print('HERO_AUX_ORIGINAL_TARGET',short(b),flush=True)
    for c in load(R/'config/BOUNDED_CORRECTION_RESULTS.json'):
        if 'corrected_c2w' not in c:continue
        for a in IDS:
            if a==c['camera']:continue
            rows.append(project(a,c['camera'],np.array(c['corrected_c2w']),'CORRECTED'))
    save('config/HERO_AUXILIARY.json',rows);table('config/HERO_AUXILIARY.csv',rows)
    save('config/CODE_REUSE_AFTER_AUXILIARY.json',REUSE)
    print('HERO_AUX_COMPLETE',len(rows),flush=True)
if __name__=='__main__':main()
