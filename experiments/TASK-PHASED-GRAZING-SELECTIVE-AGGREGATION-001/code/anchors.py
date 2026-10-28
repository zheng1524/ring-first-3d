"""Region-balanced SIFT/PnP diagnostics; derived rigid H, never frozen-camera edits."""
from geometry import *
def matches(src,dst):
    s=source(src);d=source(dst);sf=cv2.SIFT_create(nfeatures=cfg()['SIFT_features']);ka,da=sf.detectAndCompute(cv2.cvtColor(s['frame'],cv2.COLOR_RGB2GRAY),None);kb,db=sf.detectAndCompute(cv2.cvtColor(d['frame'],cv2.COLOR_RGB2GRAY),None)
    if da is None or db is None:return np.empty((0,2)),np.empty((0,2)),np.empty(0)
    ab=cv2.BFMatcher().knnMatch(da,db,k=2);ba=cv2.BFMatcher().knnMatch(db,da,k=2);q=cfg()['SIFT_ratio'];reverse={m.queryIdx:m.trainIdx for m,n in ba if m.distance<q*n.distance};good=[m for m,n in ab if m.distance<q*n.distance and reverse.get(m.trainIdx)==m.queryIdx]
    good.sort(key=lambda m:(m.distance,m.queryIdx,m.trainIdx));return np.array([ka[m.queryIdx].pt for m in good]).reshape(-1,2),np.array([kb[m.trainIdx].pt for m in good]).reshape(-1,2),np.array([m.distance for m in good])
def correspondences(src,dst):
    s=source(src);d=source(dst);ua,ub,cost=matches(src,dst);sa=np.floor(ua+.5).astype(int);sb=np.floor(ub+.5).astype(int);la=s['p']['labels'][sa[:,1],sa[:,0]];lb=d['p']['labels'][sb[:,1],sb[:,0]];distmask=cv2.distanceTransform((s['p']['labels']!=1).astype(np.uint8),cv2.DIST_L2,5);near=distmask[sa[:,1],sa[:,0]]<=60;kind=np.where((la==1)&(lb==1),'Polyp',np.where((la==0)&(lb==0)&near,'NearBackground',np.where((la==0)&(lb==0),'FarBackground','REJECT')))
    # One exact original XYZ nearest source pixel. No depth/color interpolation.
    b=np.load(INC/f'local_results/background/{src}.npz');P=np.r_[s['P'],b['XYZ_mm']];UV=np.r_[s['uv'],b['source_uv']];is_polyp=np.r_[np.ones(len(s['P']),bool),np.zeros(len(b['XYZ_mm']),bool)];distance,idx=cKDTree(UV).query(ua,workers=1);valid=(kind!='REJECT')&(distance<=2.)&(is_polyp[idx]==(kind=='Polyp'));n=len(ua);keep=[];counts={};grid=cfg()['anchor_grid'];limit=cfg()['anchor_max_per_region_cell']
    for i in range(n):
        if not valid[i]:continue
        gx=min(grid[0]-1,int(ua[i,0]*grid[0]/640));gy=min(grid[1]-1,int(ua[i,1]*grid[1]/360));key=(kind[i],gx,gy);cap=limit if kind[i]!='FarBackground' else max(1,limit//3)
        if counts.get(key,0)<cap:keep.append(i);counts[key]=counts.get(key,0)+1
    ii=np.array(keep,int);k=kind[ii];# Far background cannot outnumber Polyp + near background.
    far=np.flatnonzero(k=='FarBackground');close=np.flatnonzero(k!='FarBackground');take=np.r_[close,far[:len(close)]];ii=ii[np.sort(take)]
    return dict(P=P[idx[ii]],source_uv=ua[ii],target_uv=ub[ii],source_nearest_pixel_uv=UV[idx[ii]],source_array_index=idx[ii],region=kind[ii],raw_mutual_matches=n,balanced_matches=len(ii),source_pixel_distance=distance[ii],source_id=src,target_id=dst)
def residual(c,t,H):
    uv,z=vis.project_camera(transform(c['P'],H),np.asarray(t['K']),np.asarray(t['c2w']));err=np.linalg.norm(uv-c['target_uv'],axis=1);err[z<=0]=np.nan;return err
def ring_diagnostic(H):return dict(center_mm=float(np.linalg.norm(H[:3,3])),normal_deg=angle(H[:3,2],[0,0,1]),rotation_deg=rotangle(H),SE3=bool(np.allclose(H[:3,:3].T@H[:3,:3],np.eye(3),atol=1e-6)and np.linalg.det(H[:3,:3])>0 and np.allclose(H[3],[0,0,0,1])))
def fit_pair(src,dst,tag,old=None):
    c=correspondences(src,dst);t=target_source(dst);n=len(c['P']);fit=np.arange(n)%5!=0;held=~fit;folder=R/'local_results/anchors';folder.mkdir(parents=True,exist_ok=True);np.savez_compressed(folder/(tag+'_correspondences.npz'),**c,fit=fit,heldout=held);rows=[];Hset=[('FROZEN_IDENTITY',np.eye(4))] if source(src)['c']['video']==source(dst)['c']['video'] else []
    if old is not None:Hset+=old
    for seed in cfg()['PnP_seeds']:
        if fit.sum()<6:continue
        cv2.setRNGSeed(seed);ok,rv,tv,inliers=cv2.solvePnPRansac(c['P'][fit].astype(np.float64),c['target_uv'][fit].astype(np.float64),np.asarray(t['K']),None,iterationsCount=cfg()['PnP_iterations'],reprojectionError=cfg()['PnP_RANSAC_px'],confidence=.999,flags=cv2.SOLVEPNP_EPNP)
        if not ok:continue
        if inliers is not None and len(inliers)>=6:
            ids=np.flatnonzero(fit)[inliers.ravel()];rv,tv=cv2.solvePnPRefineLM(c['P'][ids],c['target_uv'][ids],np.asarray(t['K']),None,rv,tv)
        w2c=np.eye(4);w2c[:3,:3]=cv2.Rodrigues(rv)[0];w2c[:3,3]=tv.ravel();H=np.asarray(t['c2w'])@w2c;Hset.append(('SIFT_PNP_SEED'+str(seed),H))
    for name,H in Hset:
        err=residual(c,t,H);ring=ring_diagnostic(H);row=dict(pair=tag,source=src,target=dst,candidate=name,H_source_to_primary=H,balanced_matches=n,raw_mutual_matches=c['raw_mutual_matches'],fit_N=int(fit.sum()),heldout_N=int(held.sum()),fit_px=stats(err[fit]),heldout_px=stats(err[held]),Ring=ring,region_counts={r:int((c['region']==r).sum())for r in ['Polyp','NearBackground','FarBackground']},region_residuals={r:dict(fit=stats(err[fit&(c['region']==r)]),heldout=stats(err[held&(c['region']==r)]))for r in ['Polyp','NearBackground','FarBackground']},spatial_source_range_uv=np.ptp(c['source_uv'],axis=0)if n else None,pose_status='REGISTRATION_CANDIDATE',GT_used=False);rows.append(row)
    if not rows:rows=[dict(pair=tag,source=src,target=dst,candidate='NO_PNP_INPUT',balanced_matches=n,status='INSUFFICIENT_CORRESPONDENCES',H_source_to_primary=np.eye(4))]
    return rows,c
def main():
    verify();scores=load(R/'metrics/primary_scenes.json');records=[];same={}
    for sc in scores:
        main=sc['primary'];same[sc['id']]={main:dict(H=np.eye(4),status='PRIMARY_FROZEN')}
        for cid in sc['refs']:
            if cid==main:continue
            rr,c=fit_pair(cid,main,cid+'_to_'+main);records+=rr
            # Identity remains the scientific common Ring frame. Derived endpoints
            # are explicitly retained for diagnostics rather than altering cameras.
            same[sc['id']][cid]=dict(H=np.eye(4),status='FROZEN_SAME_VIDEO_RING_FRAME; depth conflicts retained',PnP_candidates=[x['candidate']for x in rr if x['candidate'].startswith('SIFT')])
    save('metrics/same_video_anchors.json',same);both('anchor_diagnostics_same_video',records)
    a=next(x for x in scores if x['id']=='G01_004');b=next(x for x in scores if x['id']=='G01_005');hist=load(PHASE/'metrics/D1_decision.json');old=[('HISTORICAL_LIGHTGLUE',np.array(hist['H_005_to_004'])),('HISTORICAL_LIGHTGLUE_PNP',np.array(hist['primary_output_H_005_to_004']))]
    rr,c=fit_pair(b['primary'],a['primary'],'G01_005_to_004',old);both('crossvideo_rigid_candidates',rr);records+=rr;both('anchor_diagnostics',records)
    # Choose using training anchors and Ring physical plausibility, never target
    # image errors. The independent held-out report is generated afterwards.
    eligible=[r for r in rr if r.get('Ring',{}).get('SE3')and r['Ring']['center_mm']<=cfg()['registration_candidate_Ring_center_mm']and r['Ring']['normal_deg']<=cfg()['registration_candidate_Ring_normal_deg']]
    def score(r):return r['fit_px']['median']if r.get('fit_px',{}).get('median')is not None else 1e9
    best=min(eligible or rr,key=score);H=np.array(best['H_source_to_primary']);new=[r for r in eligible if r['candidate'].startswith('SIFT')];stability=[dict(candidate=r['candidate'],rotation_deg=rotangle(np.array(r['H_source_to_primary'])@np.linalg.inv(H)),translation_mm=float(np.linalg.norm(np.array(r['H_source_to_primary'])[:3,3]-H[:3,3])))for r in new]
    # Low residual alone cannot certify an H derived from predicted depths.
    save('metrics/crossvideo_candidate.json',dict(selected=best['candidate'],H_005_to_004=H,selection='minimum training median among Ring-plausible finite candidates',training_N=best['fit_N'],heldout_N=best['heldout_N'],Ring=best['Ring'],stability=stability,status='REGISTRATION_CANDIDATE_NOT_FUSED_PENDING_INDEPENDENT_VIEWS',two_independent_constraints_required=True,GT_used=False))
    print('ANCHORS',len(records),'cross selected',best['candidate'],'matches',best['balanced_matches'],flush=True)
if __name__=='__main__':main()
