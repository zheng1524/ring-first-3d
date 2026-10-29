"""Metric original-XYZ PnP + Ring constraints. Frozen cameras never overwritten."""
from matching import views,source_view
from geometry import *
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
def to_w2c(x):
    W=np.eye(4);W[:3,:3]=cv2.Rodrigues(x[:3])[0];W[:3,3]=x[3:];return W
def pose_parameters(W):return np.r_[cv2.Rodrigues(W[:3,:3])[0].ravel(),W[:3,3]]
def project_w(P,x,K):
    W=to_w2c(x);Q=transform(P,W);h=Q@K.T;return h[:,:2]/np.maximum(Q[:,2,None],1e-6),Q[:,2]
def ring_stats(W,target):
    if target.get('c2w')is None:return dict(center_mm=None,normal_axis_deg=None,reason='PHOTO_NO_CERTIFIED_METRIC_POSE')
    H=np.array(target['c2w'])@W;n=H[:3,2];return dict(center_mm=float(np.linalg.norm(H[:3,3])),normal_axis_deg=float(np.degrees(np.arccos(np.clip(abs(n[2]),0,1)))),H_source_to_target_world=H,scale_singular_values=np.linalg.svd(H[:3,:3])[1])
def anchors(pair,method):
    d=dict(np.load(R/f'local_results/matches/{pair["id"]}_{method}.npz'));s=source(pair['source_case']);cl=np.load(R/f'local_results/cleaned/{pair["source_case"]}.npz');keep=cl['kept_original_ids'];b=np.load(INC/f'local_results/background/{pair["source_case"]}.npz');bgids=np.flatnonzero(b['quality']);P=np.r_[s['P'][keep],b['XYZ_mm'][bgids]];UV=np.r_[s['uv'][keep],b['source_uv'][bgids]];kind=np.r_[np.ones(len(keep),bool),np.zeros(len(bgids),bool)];distance,idx=cKDTree(UV).query(d['p']);ok=d['usable']&(distance<=2)&(kind[idx]==(d['region']=='Polyp'));N=len(ok);selected=[]
    for held in [False,True]:
        counts={};ids=np.flatnonzero(ok&(d['held']==held));ids=ids[np.argsort(-d['confidence'][ids],kind='stable')]
        for i in ids:
            if not held and not d['train_F_inlier'][i]:continue
            reg=str(d['region'][i]);cell=(reg,int(d['p'][i,0]//160),int(d['p'][i,1]//120));limit=cfg()['per_region_grid_cap']if reg!='FarBackground'else max(1,cfg()['per_region_grid_cap']//3)
            if counts.get(cell,0)<limit:selected.append(int(i));counts[cell]=counts.get(cell,0)+1
    ids=np.array(sorted(selected),int);return dict(P=P[idx[ids]],source_uv=d['p'][ids],target_uv=d['q'][ids],region=d['region'][ids],held=d['held'][ids],raw_match_ids=ids,source_point_array_index=idx[ids],confidence=d['confidence'][ids],source_polyp_original_ids=keep,source_background_cache_ids=bgids)
def residuals(x,P,image,K,t,s,ringdt):
    uv,z=project_w(P,x,K);image_res=(uv-image).ravel()/2.;cadP=s['ring'].vertices[::max(1,len(s['ring'].vertices)//160)];pu,zz=project_w(cadP,x,K);sample=cv2.remap(ringdt.astype(np.float32),pu[:,0].astype(np.float32).reshape(1,-1),pu[:,1].astype(np.float32).reshape(1,-1),cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT,borderValue=100).ravel()/4.;positive=np.minimum(z,0)*10;g=ring_stats(to_w2c(x),t);prior=np.empty(0)
    if g['center_mm']is not None:
        H=np.array(g['H_source_to_target_world']);prior=np.r_[H[:3,3]/cfg()['Ring_prior_center_sigma_mm'],H[:2,2]/np.sin(np.deg2rad(cfg()['Ring_prior_normal_sigma_deg']))]
    return np.r_[image_res,sample,positive,prior]
def main():
    verify();vv=views();pairs=load(R/'provenance/MATCHING_PAIRS_FROZEN.json')['pairs'];rows=[];decisions=[];vrows=[]
    for pair in pairs:
        t=vv[pair['B']];K=np.array(t['K']);s=source(pair['source_case']);mask=cv2.imread(t['Mask'],0);ringdt=cv2.distanceTransform((mask!=2).astype(np.uint8),cv2.DIST_L2,5);pairrows=[]
        for method in ['SIFT','MASt3R_FULL','MASt3R_ROI']:
            path=R/f'local_results/matches/{pair["id"]}_{method}.npz'
            if not path.exists():continue
            a=anchors(pair,method);fit=~a['held'];held=a['held'];P=a['P'];image=a['target_uv'];folder=R/'local_results/registrations';folder.mkdir(exist_ok=True);np.savez_compressed(folder/(pair['id']+'_'+method+'_anchors.npz'),**a)
            for seed in cfg()['PnP_seeds']:
                rec=dict(pair=pair['id'],group=pair['group'],method=method,seed=seed,source_case=pair['source_case'],target_view=pair['B'],kind=pair['kind'],fit_N=int(fit.sum()),held_N=int(held.sum()),regions={k:dict(fit_N=int((fit&(a['region']==k)).sum()),held_N=int((held&(a['region']==k)).sum()))for k in ['Polyp','NearBackground','FarBackground']},status='NOT_EVALUABLE_INSUFFICIENT_3D2D',K_identity='HISTORICAL_K490_UNCALIBRATED_PHOTO'if pair['kind']=='PHOTO'else'FROZEN_K')
                if fit.sum()>=6:
                    cv2.setRNGSeed(seed);ok,rv,tv,inliers=cv2.solvePnPRansac(P[fit],image[fit],K,None,iterationsCount=cfg()['PnP_iterations'],reprojectionError=cfg()['PnP_RANSAC_px'],confidence=.999,flags=cv2.SOLVEPNP_EPNP)
                    if ok and inliers is not None and len(inliers)>=6:
                        ii=np.flatnonzero(fit)[inliers.ravel()];x0=np.r_[rv.ravel(),tv.ravel()];opt=least_squares(residuals,x0,args=(P[ii],image[ii],K,t,s,ringdt),loss='soft_l1',f_scale=2,max_nfev=cfg()['local_refinement_max_nfev']);W=to_w2c(opt.x);uv,z=project_w(P,opt.x,K);err=np.linalg.norm(uv-image,axis=1);g=ring_stats(W,t);region={k:dict(fit_N=rec['regions'][k]['fit_N'],held_N=rec['regions'][k]['held_N'],fit_px=stats(err[fit&(a['region']==k)]),held_px=stats(err[held&(a['region']==k)]))for k in rec['regions']};physical=np.abs(err[held]*z[held]/min(K[0,0],K[1,1]));rec.update(status='REGISTRATION_CANDIDATE',w2c_target_in_source=W,c2w_target_in_source=np.linalg.inv(W),Ring=g,inlier_N=len(ii),fit_px=stats(err[fit]),held_px=stats(err[held]),held_transverse_mm=stats(physical),positive_depth_fraction=float((z>0).mean()),regions=region,source_3D_covariance_eigenvalues=np.linalg.eigvalsh(np.cov(P[fit].T)),optimizer_success=bool(opt.success),optimizer_nfev=int(opt.nfev),source_geometry_changed=False)
                pairrows.append(rec);rows.append(rec)
        # Freeze a training-only primary endpoint, no choosing by heldout RGB.
        good=[x for x in pairrows if x['status']=='REGISTRATION_CANDIDATE'];eligible=[x for x in good if x['Ring']['center_mm']is None or(x['Ring']['center_mm']<=3 and x['Ring']['normal_axis_deg']<=15)]
        def score(x):return x['fit_px']['median']+.2*(x['Ring']['center_mm']or 0)
        if not good:decisions.append(dict(**pair,status='FAILED',reason='NO_FINITE_PNP',selected=None));continue
        win=min(eligible or good,key=score);W=np.array(win['w2c_target_in_source']);stability=[]
        for x in good:
            if x['method']!=win['method']:continue
            Q=np.array(x['w2c_target_in_source']);delta=np.linalg.inv(W)@Q;stability.append(dict(seed=x['seed'],rotation_deg=float(np.degrees(np.linalg.norm(Rotation.from_matrix(delta[:3,:3]).as_rotvec()))),translation_mm=float(np.linalg.norm(delta[:3,3]))))
        constraints=dict(metric_K_known=pair['kind']!='PHOTO',Ring_plausible=win['Ring']['center_mm']is not None and win['Ring']['center_mm']<=3 and win['Ring']['normal_axis_deg']<=15,Polyp_fit_and_held=win['regions']['Polyp']['fit_N']>=6 and win['regions']['Polyp']['held_N']>=3,near_BG_fit_and_held=win['regions']['NearBackground']['fit_N']>=6 and win['regions']['NearBackground']['held_N']>=3,repeatable=len(stability)==2 and all(x['rotation_deg']<=2 and x['translation_mm']<=1 for x in stability),positive=win['positive_depth_fraction']>=.95,held_physical_support=win['held_transverse_mm']['p95']is not None and win['held_transverse_mm']['p95']<=1,normal_camera_condition=t['group']!='G07')
        status='VERIFIED_PAIR_INTERNAL_CONSISTENCY'if all(constraints.values())else'REGISTRATION_CANDIDATE';decision=dict(**pair,selected=win['method']+'_seed'+str(win['seed']),method=win['method'],w2c_target_in_source=W,c2w_target_in_source=np.linalg.inv(W),Ring=win['Ring'],fit_N=win['fit_N'],held_N=win['held_N'],held_px=win['held_px'],regions=win['regions'],constraints=constraints,stability=stability,status=status,selection='training median + Ring plausibility only; holdout checks qualify, never select winner',no_frozen_camera_update=True);decisions.append(decision)
        # Exact source-only prediction into actual target; B RGB read only here.
        tt=dict(id=t['id'],RGB=t['RGB'],Mask=t['Mask'],K=K,c2w=np.linalg.inv(W),ring_case=pair['source_case']);clean=np.load(R/f'local_results/cleaned/{pair["source_case"]}.npz')['kept_original_ids'];pred=projection(s['P'][clean],s['C'][clean],tt,clean);m=metric(pred,tt);vrows.append(dict(pair=pair['id'],group=pair['group'],target=t['id'],role='PAIR_TARGET_USED_FOR_PNP_NOT_INDEPENDENT_FRAME',status=status,**m));np.savez_compressed(folder/(pair['id']+'_projection.npz'),**pred)
        print('PNP',pair['id'],decision['selected'],status,'Ring',win['Ring']['center_mm'],constraints,flush=True)
        both('registration_candidates',rows);both('registration_edges',decisions);both('registration_validation',vrows)
    both('registration_candidates',rows);both('registration_edges',decisions);both('registration_validation',vrows);save('provenance/REGISTRATION_OUTPUT_FROZEN.json',stamp([R/'metrics/registration_candidates.json',R/'metrics/registration_edges.json',Path(__file__)],GT_used=False));qualify_independent(decisions)
def qualify_independent(edges):
    save('metrics/registration_pair_checks_frozen.json',edges);vv=views();rows=[];qualified=[]
    for e in edges:
        if e.get('selected')is None:qualified.append(e);continue
        e=dict(e);e['pair_internal_status']=e['status'];target=vv[e['B']];sid=target['source_id'];held=[v for v in vv.values()if v['source_id']==sid and v.get('role')=='HOLDOUT'and v.get('pose_known')]
        if e['kind']=='PHOTO' or not held:
            e['independent_frame_status']='NOT_EVALUABLE_NO_FROZEN_HELD_CAMERA';e['status']='REGISTRATION_CANDIDATE';qualified.append(e);continue
        held.sort(key=lambda v:angle(np.array(v['view_direction']),np.array(target['view_direction'])));v=held[0];H=np.array(e['Ring']['H_source_to_target_world']);s=source(e['source_case']);ids=np.load(R/f'local_results/cleaned/{e["source_case"]}.npz')['kept_original_ids'];t=dict(v,id=v['id'],c2w=np.linalg.inv(H)@np.array(v['c2w']),ring_case=e['source_case']);pred=projection(s['P'][ids],s['C'][ids],t,ids);m=metric(pred,t);ratio=m['covered_N']/max(1,m['covered_N']+m['outside_Polyp_N']);check=m['coverage']>=.55 and ratio>=.75;e['independent_frame_status']='SUPPORTED_CONDITIONALLY'if check else'FAILED_COVERAGE_OR_EXTRA_PROJECTION';e['independent_frame']=v['id'];e['independent_metric']=m;e['status']='VERIFIED_ADJACENT_CONSTRAINT'if check and e['pair_internal_status']=='VERIFIED_PAIR_INTERNAL_CONSISTENCY'else'REGISTRATION_CANDIDATE';qualified.append(e);rows.append(dict(pair=e['id'],group=e['group'],target=v['id'],role='FROZEN_THIRD_FRAME_NOT_USED_IN_PNP_OR_MATCH_SELECTION; not whole-pipeline-new blind',status=e['status'],**m));folder=R/'local_results/registrations';np.savez_compressed(folder/(e['id']+'_heldout_projection.npz'),**pred)
    both('registration_edges',qualified);both('independent_registration_validation',rows);pose_graph(qualified)
def pose_graph(edges):
    """Only internally verified pair constraints enter numeric graph optimization."""
    o=o3d();parts=load(R/'metrics/view_partition.json');nodes=[p['block']for p in parts];index={x:i for i,x in enumerate(nodes)};erows=[];included=[]
    for e in edges:
        status=e['status'];a=e['block_A'];b=e['block_B']
        active=status=='VERIFIED_ADJACENT_CONSTRAINT'and a in index and b in index and a!=b and e['kind']!='PHOTO'
        if active:included.append(e)
        erows.append(dict(pair=e['id'],a=a,b=b,edge_status=status,included_in_optimization=bool(active),no_unverified_candidate_edge_in_solver=True))
    parent=list(range(len(nodes)))
    def root(i):
        while parent[i]!=i:i=parent[i]
        return i
    for e in included:parent[root(index[e['block_B']])]=root(index[e['block_A']])
    components={}
    for i,n in enumerate(nodes):components.setdefault(root(i),[]).append(n)
    out=[]
    for ci,nn in enumerate(components.values()):
        gg=o.pipelines.registration.PoseGraph();ix={n:i for i,n in enumerate(nn)}
        for n in nn:gg.nodes.append(o.pipelines.registration.PoseGraphNode(np.eye(4)))
        for e in included:
            if e['block_A']in ix and e['block_B']in ix:gg.edges.append(o.pipelines.registration.PoseGraphEdge(ix[e['block_A']],ix[e['block_B']],np.array(e['Ring']['H_source_to_target_world']),np.eye(6),uncertain=False))
        if len(gg.edges):
            opt=o.pipelines.registration.GlobalOptimizationOption(max_correspondence_distance=1,edge_prune_threshold=.25,reference_node=0);o.pipelines.registration.global_optimization(gg,o.pipelines.registration.GlobalOptimizationLevenbergMarquardt(),o.pipelines.registration.GlobalOptimizationConvergenceCriteria(),opt)
        out +=[dict(block=n,component=ci,root=nn[0],H_block_to_root=gg.nodes[j].pose,status='CONDITIONAL_CONNECTED_COMPONENT'if len(nn)>1 else'INDEPENDENT_LOCAL_GAUGE_NOT_COMMON_WORLD')for j,n in enumerate(nn)]
    both('pose_graph_edges',erows);both('pose_graph_nodes',out);save('metrics/pose_graph_status.json',dict(nodes=len(nodes),components=len(components),optimized_edges=len(included),candidate_edges=sum(x['edge_status']=='REGISTRATION_CANDIDATE'for x in erows),cross_video_unified=any(e['kind']=='CROSS_VIDEO'for e in included),unconnected_components_kept_separate=True,GT_used=False,repair='initial all-node call rejected by Open3D as disconnected; now optimize each real connected component independently; no extra edge invented'))
if __name__=='__main__':main()
