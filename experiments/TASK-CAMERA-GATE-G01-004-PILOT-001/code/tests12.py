"""Only Ring silhouette and real-RGB epipolar tests; no HERO access here."""
from common import *
def ring_test(cid,T=None,save_images=False,tag='ORIGINAL'):
    s=source(cid);T=s['T'] if T is None else T;cam=camera(cid,T)
    u,v=np.meshgrid(np.arange(640),np.arange(360));depth=cam.cast(np.c_[u.ravel(),v.ravel()])['t_hit'].numpy().reshape(360,640)
    cad=np.isfinite(depth);observed=s['labels']==2;pol=s['labels']==1
    occlusion_dist=cv2.distanceTransform((~pol).astype(np.uint8),cv2.DIST_L2,5)
    a,b=boundary(observed),boundary(cad);clear=cfg['ring_occlusion_boundary_clearance_px'];border=cfg['image_border_clearance_px']
    def valid(p):return (at(occlusion_dist,p)>clear)&(p[:,0]>=border)&(p[:,0]<640-border)&(p[:,1]>=border)&(p[:,1]<360-border)
    qa,qb=a[valid(a)],b[valid(b)]
    da=cKDTree(b).query(qa)[0] if len(b) else np.full(len(qa),np.inf)
    db=cKDTree(a).query(qb)[0] if len(a) else np.full(len(qb),np.inf)
    both=np.r_[da,db];st=stats(both);enough_ring=min(len(qa),len(qb))>=cfg['ring_min_observable_boundary_pixels']
    passed=enough_ring and st['MAE'] is not None and st['MAE']<=cfg['ring_max_MAE_px'] and st['p95']<=cfg['ring_max_p95_px']
    contradiction=enough_ring and (st['MAE']>cfg['ring_clear_contradiction_MAE_px'] or st['p95']>cfg['ring_clear_contradiction_p95_px'])
    def shape(mask):
        y,x=np.nonzero(mask);p=np.c_[x,y];e=np.linalg.eigvalsh(np.cov(p.T)) if len(p)>2 else np.array([np.nan,np.nan])
        return dict(N=len(p),centroid_px=p.mean(0) if len(p) else [None,None],covariance_eigenvalues=e,minor_major_ratio=np.sqrt(e[0]/e[1]) if e[1]>0 else None)
    ca,cb=shape(observed),shape(cad);eligible=~pol;intersection=int((observed&cad&eligible).sum());union=int(((observed|cad)&eligible).sum())
    row=dict(camera=cid,pose=tag,visible_contour=st,observed_to_CAD=stats(da),CAD_to_observed=stats(db),raw_unqualified_symmetric=stats(np.r_[cKDTree(b).query(a)[0],cKDTree(a).query(b)[0]]),observed_boundary=len(a),CAD_boundary=len(b),observed_eligible_N=len(qa),CAD_eligible_N=len(qb),observed_shape=ca,CAD_shape=cb,centroid_difference_px=float(np.linalg.norm(np.asarray(ca['centroid_px'])-cb['centroid_px'])),unoccluded_mask_IoU=intersection/max(1,union),Ring_pass=bool(passed),clear_contradiction=bool(contradiction),adequate=bool(enough_ring),full_SE3_certified=False,rotation_symmetry='continuous common yaw about Ring Z cannot be certified by Ring alone')
    if save_images:
        folder=R/'runtime/ring';folder.mkdir(exist_ok=True)
        np.savez_compressed(folder/f'{short(cid)}_{tag}.npz',CAD_mask=cad,CAD_depth_mm=depth,observed_boundary=a,CAD_boundary=b,observed_valid=valid(a),CAD_valid=valid(b))
    return row
def annotate(p,q,a,b):
    aa,bb=source(a),source(b);inside_both=inside(p)&inside(q);ca,cb=at(aa['labels'],p),at(bb['labels'],q)
    glare=(at(aa['RGB'],p).min(1)>=cfg['specular_min_channel'])|(at(bb['RGB'],q).min(1)>=cfg['specular_min_channel'])
    usable=inside_both&(ca==cb)&(ca!=2)&~glare;held=fit_partition(p,q);train=usable&~held
    F=np.full((3,3),np.nan);H=np.full((3,3),np.nan)
    if train.sum()>=cfg['fit_min_matches']:
        cv2.setRNGSeed(cfg['seed']);f,_=cv2.findFundamentalMat(p[train],q[train],cv2.FM_RANSAC,cfg['fundamental_RANSAC_px'],cfg['RANSAC_confidence'],cfg['RANSAC_max_iterations'])
        if f is not None and f.shape==(3,3):F=f
        cv2.setRNGSeed(cfg['seed']);h,_=cv2.findHomography(p[train],q[train],cv2.RANSAC,cfg['fundamental_RANSAC_px'],maxIters=cfg['RANSAC_max_iterations'],confidence=cfg['RANSAC_confidence'])
        if h is not None:H=h
    independent_error=sampson(F,p,q);independent_good=usable&np.isfinite(independent_error)&(independent_error<=cfg['fundamental_RANSAC_px'])
    herr=np.full(len(p),np.nan)
    if np.isfinite(H).all():
        hp=np.c_[p,np.ones(len(p))]@H.T;hq=np.c_[q,np.ones(len(q))]@np.linalg.inv(H).T
        herr=(np.linalg.norm(hp[:,:2]/hp[:,2,None]-q,axis=1)+np.linalg.norm(hq[:,:2]/hq[:,2,None]-p,axis=1))/2
    return dict(p=p,q=q,usable=usable,held=held,category_A=ca,category_B=cb,glare=glare,F=F,independent_error=independent_error,independent_good=independent_good,H=H,homography_error=herr)
def matching_inventory():
    (R/'config/matches').mkdir(exist_ok=True)
    plans=load(R/'config/MATCH_PLAN_FROZEN.json');out=[]
    for plan in plans:
        a,b=plan['A'],plan['B'];methods=[]
        for m in plan['methods']:
            if m['kind']=='EXISTING_RGB_MATCHES':
                assert sha(m['asset']['path'])==m['asset']['sha256'];z=np.load(m['asset']['path']);p,q=(z['q'],z['p']) if m['reverse'] else (z['p'],z['q'])
            else:p,q,_=SIFT(CC[a],CC[b])
            d=annotate(p,q,a,b);fit=d['independent_good']&~d['held'];held=d['independent_good']&d['held']
            sufficient=enough(p[fit],q[fit],cfg['fit_min_matches']) and enough(p[held],q[held],cfg['held_min_matches'])
            np.savez_compressed(observations_path(a,b,m['method']),**d)
            methods.append(dict(method=m['method'],origin=m['kind'],raw_N=len(p),usable_N=int(d['usable'].sum()),independent_fit_N=int(fit.sum()),independent_held_N=int(held.sum()),fit_coverage_A=coverage(p[fit]),fit_coverage_B=coverage(q[fit]),held_coverage_A=coverage(p[held]),held_coverage_B=coverage(q[held]),sufficient_RGB_only=bool(sufficient),matches_file=asset(observations_path(a,b,m['method'])),input=m['asset']))
        selected=next((m['method'] for m in methods if m['sufficient_RGB_only']),None)
        out.append(dict(A=a,B=b,pair_id=pair_id(a,b),extra_holdout=plan['extra_holdout'],methods=methods,selected_method=selected,selection_uses_pose_or_HERO=False))
        print('RGB_MATCHES',plan['pair_id'],[(m['method'],m['raw_N'],m['independent_fit_N'],m['independent_held_N'],m['sufficient_RGB_only']) for m in methods],'selected',selected,flush=True)
    save('config/RGB_ONLY_METHOD_SELECTION.json',out)
    freeze('BEFORE_FROZEN_POSE_MATCH_SCORING.json',dict(selection=asset(R/'config/RGB_ONLY_METHOD_SELECTION.json')))
    return out
def geometric_diagnostics(a,b,p,q,Ta=None,Tb=None):
    sa,sb=source(a),source(b);Ta=sa['T'] if Ta is None else Ta;Tb=sb['T'] if Tb is None else Tb
    if not len(p):return dict(parallax_deg=stats([]),positive_fraction=None,triangulation_reprojection_px=stats([]))
    ra=vis.camera_rays(p,sa['K'],Ta)[:,3:];rb=vis.camera_rays(q,sb['K'],Tb)[:,3:]
    ra/=np.linalg.norm(ra,axis=1)[:,None];rb/=np.linalg.norm(rb,axis=1)[:,None]
    angles=np.degrees(np.arccos(np.clip((ra*rb).sum(1),-1,1)))
    h=cv2.triangulatePoints(sa['K']@np.linalg.inv(Ta)[:3],sb['K']@np.linalg.inv(Tb)[:3],p.T,q.T);X=(h[:3]/h[3]).T
    ua,za=vis.project_camera(X,sa['K'],Ta);ub,zb=vis.project_camera(X,sb['K'],Tb)
    return dict(parallax_deg=stats(angles),positive_fraction=float(((za>0)&(zb>0)&np.isfinite(X).all(1)).mean()),triangulation_reprojection_px=stats((np.linalg.norm(ua-p,axis=1)+np.linalg.norm(ub-q,axis=1))/2),HERO_used=False)
def pair_test(a,b,method,Ta=None,Tb=None):
    sa,sb=source(a),source(b);Ta=sa['T'] if Ta is None else Ta;Tb=sb['T'] if Tb is None else Tb;d=match_data(a,b,method);p,q=d['p'],d['q']
    error=sampson(fundamental(sa['K'],Ta,sb['K'],Tb),p,q);groups={}
    for name,sel in [('all_usable',d['usable']),('independent_F_consensus',d['independent_good']),('fit',d['independent_good']&~d['held']),('held',d['independent_good']&d['held'])]:
        e=error[sel];groups[name]=dict(N=int(sel.sum()),error_px=stats(e),inlier_N=int((e<=cfg['pose_inlier_px']).sum()),inlier_fraction=float((e<=cfg['pose_inlier_px']).mean()) if len(e) else None,coverage_A=coverage(p[sel]),coverage_B=coverage(q[sel]),**geometric_diagnostics(a,b,p[sel],q[sel],Ta,Tb))
    fit=d['independent_good']&~d['held'];held=d['independent_good']&d['held'];sufficient=enough(p[fit],q[fit],cfg['fit_min_matches']) and enough(p[held],q[held],cfg['held_min_matches'])
    checks=[]
    for name in ['fit','held']:
        r=groups[name];st=r['error_px'];checks.append(bool(st['median'] is not None and st['median']<=cfg['pose_max_median_px'] and st['p95']<=cfg['pose_max_p95_px'] and r['inlier_fraction']>=cfg['pose_min_inlier_fraction']))
    g=groups['independent_F_consensus'];st=g['error_px'];clear=sufficient and (st['median']>=cfg['contradiction_min_median_px'] or g['inlier_fraction']<=cfg['contradiction_max_inlier_fraction'])
    fitr=groups['fit'];fit_clear=bool(sufficient and (fitr['error_px']['median']>=cfg['contradiction_min_median_px'] or fitr['inlier_fraction']<=cfg['contradiction_max_inlier_fraction']))
    hsel=d['independent_good'];homfrac=float((d['homography_error'][hsel]<=cfg['fundamental_RANSAC_px']).mean()) if hsel.any() else None
    geom_ok=g['parallax_deg']['median'] is not None and g['parallax_deg']['median']>=cfg['minimum_parallax_deg'] and g['positive_fraction']>=cfg['minimum_positive_triangulation_fraction']
    return dict(A=a,B=b,method=method,sufficient=bool(sufficient),groups=groups,pair_pass=bool(sufficient and all(checks) and geom_ok),clear_contradiction=bool(clear),fit_clear_contradiction=fit_clear,homography_F_consensus_fraction=homfrac,near_planar_or_low_parallax=bool((homfrac is not None and homfrac>=cfg['planar_homography_fraction']) or (g['parallax_deg']['median'] is not None and g['parallax_deg']['median']<cfg['minimum_parallax_deg'])),independent_F_identity='RGB-only RANSAC F fitted to nonheld points; no candidate pose or HERO; not correspondence ground truth',full_pose_truth=False)
def main():
    assert sha(R/'config/protocol.json')==load(R/'config/BEFORE_FORMAL_RUN.json')['protocol']['sha256']
    plan=matching_inventory();rings=[ring_test(cid,save_images=True) for cid in IDS];pairs=[]
    for p in plan:
        for m in p['methods']:
            r=pair_test(p['A'],p['B'],m['method']);r['selected_for_gate']=m['method']==p['selected_method'];r['extra_holdout']=p['extra_holdout'];pairs.append(r)
    save('config/ORIGINAL_TEST12.json',dict(Ring=rings,pairs=pairs,all_original_results_before_any_correction=True,HERO_used=False))
    freeze('ORIGINAL_TEST12_FROZEN.json',dict(results=asset(R/'config/ORIGINAL_TEST12.json')))
    for r in rings:print('RING',short(r['camera']),r['visible_contour'],'pass',r['Ring_pass'],'clear',r['clear_contradiction'],flush=True)
    for r in pairs:
        if r['selected_for_gate']:print('GEOMETRY',pair_id(r['A'],r['B']),r['method'],r['groups']['held']['error_px'],'pass',r['pair_pass'],'clear',r['clear_contradiction'],flush=True)
if __name__=='__main__':main()
