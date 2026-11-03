"""Only pose source differs. Exact historical A-triangle render called for both arms."""
from common import *
def cad_scene(ring_kind):return ringscene(ring_kind)
extract(REPO/'experiments/TASK-VIEW-OBSERVABILITY-GT-EVAL-001/code/reprojection.py',['render'],globals())
def infer(a,b):
    sa,sb=source(a),source(b);d=matching(a,b);p,q=d['p'],d['q'];fit=d['usable']&~d['held'];T=np.linalg.inv(sb['T'])@sa['T']
    row=dict(A=a,B=b,raw_matches=len(p),usable=int(d['usable'].sum()),fit=int(fit.sum()),held=int((d['usable']&d['held']).sum()),match_origin=str(d['origin']),SIFT_S0_status='INSUFFICIENT_EVIDENCE',metric_scale_independent=False)
    if fit.sum()<12:return row,None
    # Both K normalized independently, no RF direction or rotation enters this estimator.
    pa=cv2.undistortPoints(p[fit,None,:].astype(float),sa['K'],None)[:,0];qb=cv2.undistortPoints(q[fit,None,:].astype(float),sb['K'],None)[:,0]
    cv2.setRNGSeed(0);E,im=cv2.findEssentialMat(pa,qb,np.eye(3),method=cv2.RANSAC,prob=.999,threshold=2./490.,maxIters=2000)
    if E is None or E.shape!=(3,3):row['SIFT_S0_status']='ESSENTIAL_FAILED_OR_AMBIGUOUS';return row,None
    nin,Rr,t,mask=cv2.recoverPose(E,pa,qb,np.eye(3),mask=im.copy());t=t[:,0]
    row.update(essential_RANSAC_inliers=int((im>0).sum()),recoverPose_cheirality_inliers=int(nin),R_B_from_A=Rr,t_direction_B=t,essential_E=E)
    if nin<8:row['SIFT_S0_status']='CHEIRALITY_INSUFFICIENT';return row,None
    row['SIFT_S0_status']='POSE_RETURNED_NO_METRIC_SCALE';L=np.linalg.norm(T[:3,3]);S=np.eye(4);S[:3,:3]=Rr;S[:3,3]=t*L;Tb=sa['T']@np.linalg.inv(S)
    angle=lambda x,y:float(np.degrees(np.arccos(np.clip(x@y/(np.linalg.norm(x)*np.linalg.norm(y)),-1,1))))
    row.update(RF_relative=T,SIFT_RF_scale_relative=S,SIFT_B_c2w=Tb,RF_translation_length_mm=L,rotation_difference_deg=float(Rotation.from_matrix(Rr@T[:3,:3].T).magnitude()*180/np.pi),translation_direction_difference_deg=angle(t,T[:3,3]),S1_name='SIFT + RF-scale',RF_R_or_t_direction_used_in_estimation=False)
    Fs=np.linalg.inv(sb['K']).T@E@np.linalg.inv(sa['K']);Ff=fundamental(sa['K'],sa['T'],sb['K'],sb['T'])
    for name,sel in [('fit',fit),('held',d['usable']&d['held'])]:
        row[name+'_RF_Sampson_px']=stats(sampson(Ff,p[sel],q[sel]));row[name+'_SIFT_Sampson_px']=stats(sampson(Fs,p[sel],q[sel]))
    good=np.zeros(len(p),bool);good[np.flatnonzero(fit)]=mask.ravel()>0
    directions=vis.camera_rays(q[good],sb['K'],Tb)[:,3:];ra=vis.camera_rays(p[good],sa['K'],sa['T'])[:,3:]
    dot=(ra*directions).sum(1)/(np.linalg.norm(ra,axis=1)*np.linalg.norm(directions,axis=1));par=np.degrees(np.arccos(np.clip(dot,-1,1)))
    H,hm=cv2.findHomography(p[fit],q[fit],cv2.RANSAC,2.,maxIters=2000,confidence=.999)
    row.update(parallax_deg=stats(par),homography_inlier_fraction=float(hm.mean())if hm is not None else None,match_hull_fraction_A=float(cv2.contourArea(cv2.convexHull(p[fit].astype(np.float32)))/(640*360)),match_hull_fraction_B=float(cv2.contourArea(cv2.convexHull(q[fit].astype(np.float32)))/(640*360)),near_degenerate=bool((len(par)and np.median(par)<.5)or(hm is not None and hm.mean()>=.9)))
    return row,Tb
def metrics(pred,B,lab,common):
    v=pred['valid'];pol=lab==1;cad=np.isfinite(pred['z_mm'])&(pred['z_mm']>pred['known_CAD_z_mm']+.05);e=abs(pred['RGBA'][:,:,:3].astype(float)-B).mean(2)
    aa=boundary(v);bb=boundary(pol);be=np.r_[cKDTree(bb).query(aa)[0],cKDTree(aa).query(bb)[0]]if len(aa)and len(bb)else np.empty(0)
    return dict(target_polyp_N=int(pol.sum()),predicted_N=int(v.sum()),shared_polyp_N=int(common.sum()),common_RGB=stats(e[common]),own_valid_RGB=stats(e[v&pol]),coverage=float((v&pol).sum()/max(1,pol.sum())),uncovered_target=int((pol&~v).sum()),outside_mask=int((v&~pol).sum()),outside_fraction=float((v&~pol).sum()/max(1,v.sum())),CAD_occluded_pixels=int(cad.sum()),CAD_occluded_image_fraction=float(cad.mean()),unknown_image_fraction=float((~v&~cad).mean()),mask_boundary_error_px=stats(be),physical_GT='NOT_EVALUABLE',B_RGB_used_to_color=False)
def main():
    f=load(R/'provenance/A_PORT_FIX_BEFORE_PREDICTION.json');assert sha(R/'config/PROTOCOL.json')==f['protocol']['sha256']
    for c in f['code']:assert sha(c['path'])==c['sha256']
    result=[];poses=[];out=R/'local_results/A';out.mkdir(exist_ok=True)
    for spec in protocol()['pairs']:
        a,b=spec['A'],spec['B'];sa,sb=source(a),source(b);pose,Tb=infer(a,b);poses.append(pose)
        for kind in ['Raw','Cleaned']:
            P,F,C,keep=archived_mesh(a,kind);rf=render(P,F,C,sb['K'],sb['T'],np.eye(4),CC[a]['scene_id']);sf=render(P,F,C,sb['K'],Tb,np.eye(4),CC[a]['scene_id'])if Tb is not None else None
            common=rf['valid']&(sb['labels']==1)&(sf['valid']if sf is not None else False)
            for name,pred in [('Ring-First',rf),('SIFT + RF-scale',sf)]:
                row=dict(A=a,B=b,kind=kind,method=name,input_vertices=len(P),input_faces=len(F),source_retained_vertices=int(keep.sum()),status='RETURNED'if pred is not None else pose['SIFT_S0_status'])
                if pred is not None:
                    path=out/(a+'__'+b+'_'+kind+'_'+('RF'if name=='Ring-First'else'SIFT')+'.npz');np.savez_compressed(path,**pred);row.update(metrics(pred,sb['RGB'],sb['labels'],common),prediction=asset(path))
                result.append(row)
            print('A',a,'->',b,kind,pose['SIFT_S0_status'],'RFcover',round((rf['valid']&(sb['labels']==1)).sum()/max(1,(sb['labels']==1).sum()),3),flush=True)
        # Same historical RAW triangle baseline: prove exact replay on the immutable old NPZ when available.
        hist=REPO/'experiments/TASK-VIEW-OBSERVABILITY-GT-EVAL-001/local_results/reprojection'
    save('metrics/A_POSES.json',poses);save('metrics/A_REPROJECTION.json',result)
    flat=[{k:v for k,v in x.items()if k!='prediction'}for x in result];keys=list(dict.fromkeys(k for x in flat for k in x));table('metrics/REPROJECTION_ERRORS.csv',[{k:x.get(k)for k in keys}for x in flat])
    save('provenance/A_PREDICTIONS_FROZEN.json',dict(files=[asset(p)for p in out.glob('*.npz')],pose=asset(R/'metrics/A_POSES.json'),no_GT=True,trained=False))
if __name__=='__main__':main()
