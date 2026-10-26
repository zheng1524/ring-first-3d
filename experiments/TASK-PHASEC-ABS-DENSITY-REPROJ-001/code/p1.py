"""Video gate and three absolute-density trials; no density recomputation."""
from common import *
def diagnose(c):
    a,p,rgb,m=data(c);P=a['XYZ_mm'];rho=a['rho_surface_radius'];cfg=load(R/'config.json');lo=rho<=np.quantile(rho,cfg['low_quantile']);hi=rho>=np.quantile(rho,cfg['dense_quantile']);mask=np.zeros(p['labels'].shape,np.uint8);mask[a['source_v'][lo],a['source_u'][lo]]=1
    n,lab,st,_=cv2.connectedComponentsWithStats(mask);big=1+st[1:,cv2.CC_STAT_AREA].argmax();region=lab[a['source_v'],a['source_u']]==big;ev=np.linalg.eigvalsh(np.cov(P[region].T));extent=4*np.sqrt(max(0,ev[-1]));drop=np.quantile(rho,.8)/max(np.quantile(rho,.1),1e-9);spacing=np.median(a['knn_k_distance_mm'][region])/np.median(a['knn_k_distance_mm'][hi]);fraction=region.sum()/lo.sum();outer=2*(c['R_mm']+.6)
    passed=drop>=cfg['drop_q80_over_q10_minimum']and fraction>=cfg['low_region_fraction_minimum']and extent>=cfg['low_region_extent_outer_diameters_minimum']*outer and spacing>=cfg['low_region_k12_over_dense_median_minimum']
    return dict(id=c['id'],group=c['group'],video=c['video'],condition=c['condition'],original_points=len(P),rho_quantiles=np.quantile(rho,[.05,.1,.2,.5,.7,.8,.9,.95]),drop_q80_over_q10=drop,low_band_points=int(lo.sum()),largest_low_region_points=int(region.sum()),largest_low_region_fraction=fraction,region_center_XYZ_mm=np.median(P[region],0),region_bounds_XYZ_mm=[P[region].min(0),P[region].max(0)],region_extent_mm=extent,region_k12_over_dense=spacing,low_region_density=stats(rho[region]),dense_density=stats(rho[hi]),low_k12=stats(a['knn_k_distance_mm'][region]),dense_k12=stats(a['knn_k_distance_mm'][hi]),low_stretch=stats(a['adjacency_perspective_stretch_max'][region]),dense_stretch=stats(a['adjacency_perspective_stretch_max'][hi]),low_normalized_density=stats(a['rho_normalized'][region]),dense_normalized_density=stats(a['rho_normalized'][hi]),L=float(np.quantile(rho[region],.25)),D=float(np.quantile(rho[hi],.1)),reference_gate=bool(passed),support_identity='SPATIAL_DIAGNOSTIC_NOT_ERROR_LABEL'),lo,hi,region
def prepare():
    for x in load(PREV/'provenance/INPUT_FREEZE.json')['files']:assert sha(x['path'])==x['sha256']
    fields=load(PREV/'provenance/DIAGNOSTIC_OUTPUTS_FROZEN.json')['fields']
    for path,h in fields.items():assert sha(path)==h
    files=list(fields)+[PREV/'config.json',PREV/'code/density.py',PREV/'provenance/CASES.json',SPARSE/'code/run.py',ICF/'inputs/H_frozen.json',ICF/'inputs/datasets.json',ICF/'inputs/references.json',ICF/'scripts/export_scenes.py',OLD/'mast3r_group_consensus_bias_v1/scripts/setup.py',OLD/'mast3r_group_consensus_bias_v1/inputs/baselines.json']
    for c in cases():
        files += [c[k]for k in ['pack','mesh','source_points','RGB','Mask','camera_file']]+[ring_path(c)]
        a,p,rgb,m=data(c);assert len(a['XYZ_mm'])==c['points'];assert np.allclose(a['rho_surface_radius'],a['radius_neighbor_count']/(np.pi*.4**2),rtol=1e-14,atol=1e-12);assert np.array_equal(p['pose'],np.load(c['camera_file'])['c2w'][c['reference_index']])
        raw=np.load(c['source_points']);P=raw['points_mm']if'points_mm'in raw else raw['XYZ_mm'];assert np.array_equal(P,a['XYZ_mm'])
    files += list((REPO/'visualization').glob('*.py'))+list((REPO/'visualization').glob('*.json'))
    save('provenance/INPUTS.json',stamp(files));save('provenance/CASES.json',cases());csvsave('metrics/source_identity.csv',cases());print('PREPARED 8 groups / 9 videos / 13 refs / 213654 points',flush=True)
def freeze():
    verify();rows=[]
    for c in cases():
        row,low,dense,region=diagnose(c);rows.append(row);folder=R/'local_results'/c['id'];folder.mkdir(parents=True,exist_ok=True);np.savez_compressed(folder/'spatial_regions.npz',low_band=low,dense_proxy=dense,largest_low_region=region)
    csvsave('metrics/spatial_diagnostics.csv',rows);save('metrics/spatial_diagnostics.json',rows);cfg=load(R/'config.json');videos=[]
    for key in dict.fromkeys((c['group'],c['video'])for c in cases()):
        rr=[x for x in rows if(x['group'],x['video'])==key];passed=sum(x['reference_gate']for x in rr)/len(rr)>=cfg['video_reference_pass_fraction'];drop=np.median([x['drop_q80_over_q10']for x in rr]);L=np.median([x['L']for x in rr]);D=np.median([x['D']for x in rr]);ts=[float(L),float(np.sqrt(L*D)),float(D)]if passed else[]
        videos.append(dict(group=key[0],video=key[1],condition=rr[0]['condition'],references=len(rr),reference_passes=sum(x['reference_gate']for x in rr),density_drop=drop,gate='ENTER_CANDIDATE_TRIALS'if passed else'NO_CLEANING_REQUIRED'if drop<cfg['drop_q80_over_q10_minimum']else'INSUFFICIENT_EVIDENCE',absolute_thresholds=ts,threshold_rule=cfg['threshold_rule']))
    save('provenance/VIDEO_THRESHOLDS_FROZEN.json',dict(UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),videos=videos,no_deletion_run_yet=True));save('provenance/P1_CODE_AND_RULES_FROZEN.json',stamp(list((R/'code').glob('*.py'))+[R/'config.json',R/'PROTOCOL.md',R/'provenance/VIDEO_THRESHOLDS_FROZEN.json']));print('THRESHOLDS FROZEN',[(v['group'],v['video'],v['gate'],v['absolute_thresholds'])for v in videos],flush=True)
def damage(c,a,p,m,deleted,tier,T):
    P=a['XYZ_mm'];facekeep=~deleted[m.faces].any(1);F=m.faces;areas=m.area_faces;cl=face_components(F);sums=np.bincount(cl,weights=areas);main=cl==sums.argmax();newcl=face_components(F[facekeep]);remaining=main[facekeep];s=np.bincount(newcl[remaining],weights=areas[facekeep][remaining])if remaining.any()else np.array([0.]);e,cnt=edge_counts(F);old=set(map(tuple,e[cnt==1]));e,cnt=edge_counts(F[facekeep]);new=set(map(tuple,e[cnt==1]));reg=np.load(R/f'local_results/{c["id"]}/spatial_regions.npz');densefaces=reg['dense_proxy'][F].all(1);low=reg['largest_low_region'];co=cohorts(a,p)
    row=dict(id=c['id'],group=c['group'],video=c['video'],condition=c['condition'],tier=tier,threshold_points_per_mm2=T,original_points=len(P),deleted_points=int(deleted.sum()),deleted_fraction=float(deleted.mean()),type2_candidate_region_points=int(low.sum()),candidate_region_deleted=int((low&deleted).sum()),candidate_region_residual=int((low&~deleted).sum()),original_faces=len(F),kept_faces=int(facekeep.sum()),original_area_mm2=float(areas.sum()),removed_area_mm2=float(areas[~facekeep].sum()),raw_main_area_retained=float(areas[main&facekeep].sum()/areas[main].sum()),largest_continuous_raw_main_retained=float(s.max()/areas[main].sum()),largest_piece_fraction_of_remaining_main=float(s.max()/s.sum())if s.sum()else 0.,raw_components=len(sums),cleaned_components=len(np.unique(newcl)),new_boundary_edges=len(new-old),interior_deletion_patches=interior_deletion_patches(F,deleted),dense_proxy_faces=int(densefaces.sum()),dense_proxy_area_retained=float(areas[densefaces&facekeep].sum()/areas[densefaces].sum())if densefaces.any()else None,GT_accuracy=None)
    for name,sel in co.items():row[name+'_N']=int(sel.sum());row[name+'_deleted']=int((sel&deleted).sum());row[name+'_deleted_fraction']=float(deleted[sel].mean())if sel.any()else None
    cfg=load(R/'config.json');row['structure_check_pass']=bool((row['possible_stalk_proxy_deleted_fraction']or 0)<=1-cfg['stalk_proxy_retained_minimum']and row['largest_piece_fraction_of_remaining_main']>=cfg['remaining_main_piece_fraction_minimum']and(row['dense_proxy_area_retained']or 0)>=cfg['dense_proxy_area_retained_minimum']and row['interior_deletion_patches']<=cfg['interior_deletion_patches_maximum'])
    return row,facekeep
def run():
    verify()
    for x in load(R/'provenance/P1_CODE_AND_RULES_FROZEN.json')['files']:assert sha(x['path'])==x['sha256'],x['path']
    vs=load(R/'provenance/VIDEO_THRESHOLDS_FROZEN.json')['videos'];rows=[];decisions=[]
    for v in vs:
        cc=[c for c in cases()if c['group']==v['group']and c['video']==v['video']];vr=[]
        for c in cc:
            a,p,rgb,m=data(c);P=a['XYZ_mm'];folder=R/'local_results'/c['id'];uv=np.c_[a['source_u'],a['source_v']];np.savez_compressed(folder/'Raw_exact.npz',XYZ_mm=P,RGB=rgb,source_uv=uv,faces=m.faces);trimesh.points.PointCloud(P,colors=rgb).export(folder/'Raw.ply')
            trials=list(zip(['T1','T2','T3'],v['absolute_thresholds']))+[('GLOBAL50',load(R/'config.json')['global_control_threshold'])]
            for tier,T in trials:
                deleted=a['rho_surface_radius']<T;row,fkeep=damage(c,a,p,m,deleted,tier,T);vr.append(row);rows.append(row);ids=np.flatnonzero(~deleted);back=np.full(len(P),-1,int);back[ids]=np.arange(len(ids));np.savez_compressed(folder/f'{tier}_exact.npz',XYZ_mm=P[ids],RGB=rgb[ids],kept_original_indices=ids,deleted_original_indices=np.flatnonzero(deleted),delete_reason='rho_surface_radius < absolute_threshold',rho_threshold=T,kept_original_face_indices=np.flatnonzero(fkeep),source_uv=uv[ids],faces_original_indices=m.faces[fkeep]);trimesh.Trimesh(P[ids],back[m.faces[fkeep]],vertex_colors=rgb[ids],process=False).export(folder/f'{tier}_original_faces_only.ply')
        eligible=[t for t in ['T1','T2','T3']if len([x for x in vr if x['tier']==t])==len(cc)and all(x['structure_check_pass']for x in vr if x['tier']==t)]
        selected=eligible[-1]if eligible and v['condition']=='NORMAL_CONDITIONAL'else'RAW';status='EXPERIMENTAL_CLEANING'if selected!='RAW'else v['gate']if v['gate']!='ENTER_CANDIDATE_TRIALS'else'INSUFFICIENT_EVIDENCE'
        decisions.append(dict(**v,selected=selected,status=status,selected_threshold=next((x['threshold_points_per_mm2']for x in vr if x['tier']==selected),None),reason='Same video threshold and all-reference structure checks; RGB error not used'if selected!='RAW'else'No admitted threshold; raw preserved. Camera stress is never admitted as reliable cleaning.'))
        for c in cc:
            f=R/'local_results'/c['id'];src=f/'Raw_exact.npz'if selected=='RAW'else f/f'{selected}_exact.npz';z=dict(np.load(src));z.update(final_status=status,selected_tier=selected);np.savez_compressed(f/'Final_Cleaned_exact.npz',**z)
    csvsave('metrics/P1_candidate_damage.csv',rows);save('metrics/P1_candidate_damage.json',rows);csvsave('metrics/P1_video_decisions.csv',decisions);save('metrics/P1_video_decisions.json',decisions);save('provenance/P1_OUTPUT_FREEZE.json',stamp(list((R/'local_results').glob('*/*.npz'))+[R/'metrics/P1_video_decisions.json']));print('P1 COMPLETE',[(x['group'],x['video'],x['status'],x['selected'])for x in decisions],flush=True)
if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['prepare','freeze','run']);args=parser.parse_args();globals()[args.mode]()
