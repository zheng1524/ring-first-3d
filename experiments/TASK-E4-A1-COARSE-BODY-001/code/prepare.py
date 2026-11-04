from common import *
def main():
    assert not(R/'config/PREREGISTERED.json').exists(),'FROZEN_PROTOCOL_EXISTS'
    scenes={
      'G01_004':dict(kind='Ip',group='G01',A=['G01_004_ref08','G01_004_ref13','G01_004_ref03'],B=['G01_004_growth_r14'],tier='CONDITIONAL_CAMERA_AND_HEAD_CUE',EH_extra=False),
      'G06_004':dict(kind='IIa',group='G06',A=['G06_004_growth_r01','G06_004_growth_r03'],B=['G06_004_growth_r06'],tier='CONDITIONAL_RESEARCH',EH_extra=True),
      'G08_005':dict(kind='IIa',group='G08',A=['G08_005_growth_r01','G08_005_growth_r02'],B=['G08_005_ref04'],tier='PRESSURE_LIMITED_CAMERA',EH_extra=True),
      'G07_004':dict(kind='Is',group='G07',A=['G07_004_ref04','G07_004_growth_r02'],B=['G07_004_new_r06'],tier='PRESSURE_HISTORICAL_HERO_CHAIN_UNQUALIFIED',EH_extra=False)}
    pr=dict(task=R.name,parent_commit='6550275d518020f50ae7a02dd9b8c6907ca6189b',UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),scenes=scenes,
      no_A2_execution=True,no_B1_B2=True,no_GT_real=True,GPU=0,new_HERO=0,camera_optimization=0,
      arms={'A1-0':['C','R'],'A1-1':['H','R'],'A1-2':['C','D','R'],'A1-3':['C','D','R'],'A1-2+H':['C','D','H','R'],'A1-3+H':['C','D','H','R']},
      models=dict(ellipsoid_parameters=9,Ip_star_L3_parameters=16,Is_open_cap_parameters=10,IIa_compact_height_parameters=11),
      cue='Ip fixed opening .35*DTmax and maximal-thickness connected component; original masks unchanged; head proxy not truth. Other classes original Polyp mask. P contour>3px from Ring; Q contact directions weight.35, not treated as measured anatomical contour.',
      observations=dict(support_directions=24,depth_pixels_per_view=32,depth_pairs_per_view=16,HERO_points_per_view=96,head_interior_depth_px=2,depth_gradient_limit_mm=.75,source_CAD_tolerance_mm=.05,HERO_area_quadrature='original incident face area/3, deterministic cumulative-area sampling; equal per-view mass and upstream RGB correlation normalization',
        noise_scale=dict(contour_px=3.,relative_depth_mm=.25,HERO_mm=.25),weights=dict(C=1.,D=1.,H=1.,R=.05),robust='soft_l1, f_scale1, each modality normalized sqrt(row count), view/correlation weights fixed before fits',
        missing='No fake first depths. Undefined relative-depth pair residual is censored, source-ray convex-support feasibility penalized in C; fixed-denominator miss counts and .25mm censored-score reported. Coverage loss/low hit gate prevents PASS; no discrete hit count used as differentiable loss.'),
      bounds=dict(center_offset_mm=10.,semiaxes_mm=[.25,15.],rotation_vector_component_rad=.8,IIa_ellipsoid_thickness_mm=[.05,3.],IIa_peak_mm=[.05,5.],star_coeff=[-.2,.2],star_log_radius_bound=.2,cap_cut=[-.65,.4],height_skew=[-.25,.25]),
      optimization=dict(method='scipy least_squares trf, float64, 3-point central numerical derivative',max_nfev=60,initializations=[0,1,2],seed=20261104,ftol=1e-5,xtol=1e-5,gtol=1e-5,select='minimum A training objective only, no B values or visual choice; all starts retained',mesh_points='24 longitude x13 latitude for optimizer; export96x49',
        initialization='A1-0/2/3 only A 2D centroid-ray triangulation, source camera frame, apparent widths and fixed class priors; A1-1 only qualified/conditional HERO point statistics; no B initialization. Star/cap/height common core initialization with A1-2.'),
      stability=dict(central_steps=[1e-3,5e-4],scales=dict(center_mm=1.,rotation_rad=.1,log_axis=.2,shape=.1),rank_thresholds=[1e-2,1e-3,1e-4,1e-6],J_tolerance=.1,uncertainty='range across all starts and fixed perturbation fits, not calibrated CI',
        fixed_perturbations=['A head support +1px','relative depth weight x.9','relative depth weight x1.1','last fit view removed','first fit camera right-body tx+.05mm and ry+.1deg'],perturb_budget_nfev=30),
      gates=dict(min_head_IoU=.5,min_fixed_depth_ray_hit=.8,maximum_outside_fraction=.35,max_axis_ratio=20.,minimum_whitened_singular_ratio=1e-3,minimum_relative_improvement=.05,nondegenerate='finite, positive, no spikes/nonmanifold/self-crossing certificate; budget exhaustion not automatically converged',G1='at least one qualified real case with frozen independent holdout and nondegenerate result; conditional upstream/selection/Gate dependencies cannot certify strict G1'),
      A_B='B not fit to parameters, but all existing B were used by upstream cameras, HERO/selection or Gate; label CONDITIONAL, not full-pipeline blind test',
      synthetic='Separate generated truth only; ellipsoid/cap/wide compact mound/head-stalk counterexamples; no synthetic score tunes real parameters. Models frozen before synthetic tests.',
      background='catalog existing data and Phase-D plane usability only; no fitting, attachment residual, gap measurement or new plane inference this round')
    save('config/PREREGISTERED.json',pr)
    manifest=[];qual=[];fitting=set(sum([s['A']for s in scenes.values()],[]));ids=sorted(set(sum([s['A']+s['B']for s in scenes.values()],[])))
    angles=np.arange(24)*2*np.pi/24;directions=np.c_[np.cos(angles),np.sin(angles)]
    for cid in ids:
        c=CC[cid];scene=c['scene_id'];sc=scenes[scene];s=source(cid);n=cleaned(cid);o=original(cid);h,meta=head_cue(s['labels'],sc['kind']);height,width=n['depth'].shape
        for k in ['RGB','Mask','pack','source_points','mesh','camera_file']:
            a=asset(c[k]);assert a['sha256']==c['files'][k]['sha256'];manifest.append(a)
        manifest +=[asset(c['E1_actual_native']['path']),asset(c['Ring_CAD']['path'])]
        if n['cleanup_path']:manifest.append(asset(n['cleanup_path']))
        boundary=contour(h).astype(float);ringdt=cv2.distanceTransform((s['labels']!=2).astype(np.uint8),cv2.DIST_L2,cv2.DIST_MASK_PRECISE)
        support=(boundary@directions.T).max(0);arg=(boundary@directions.T).argmax(0);q=ringdt[boundary[arg,1].astype(int),boundary[arg,0].astype(int)]<=3;support_weights=np.where(q,.35,1.)
        hn=cv2.resize(h.astype(np.uint8),(width,height),interpolation=cv2.INTER_NEAREST).astype(bool);dt=cv2.distanceTransform(hn.astype(np.uint8),cv2.DIST_L2,cv2.DIST_MASK_PRECISE)
        z=n['depth'];safe=n['valid']&hn&(dt>2)&(n['native_RGB'].min(2)<245)
        dz=np.zeros_like(z,float)
        for axis in [0,1]:dz=np.maximum(dz,abs(np.roll(z,1,axis)-z));dz=np.maximum(dz,abs(np.roll(z,-1,axis)-z))
        safe&=dz<=.75;v,u=np.nonzero(safe);uv=np.c_[u,v];rz,_=cast(ringscene(scene),uv,n['Kn'],s['T']);eligible=(z[v,u]<=rz+.05);uv=uv[eligible];uv=uv[select(np.arange(len(uv)),32)]
        zz=z[uv[:,1],uv[:,0]].astype(float);pairs=np.c_[np.arange(len(uv)//2),np.arange(len(uv)//2)+len(uv)//2]
        # Original face-area quadrature, source points and identities never moved/deleted.
        pu=o['uv'];uvn=np.floor((pu+.5)*[width/640,height/360]).astype(int);uvn=np.clip(uvn,[0,0],[width-1,height-1]);eligible=h[pu[:,1],pu[:,0]]&n['valid'][uvn[:,1],uvn[:,0]]&(s['RGB'][pu[:,1],pu[:,0]].min(1)<245)
        pz=vis.project_camera(o['P'],s['K'],s['T'])[1];rhit,_=cast(ringscene(scene),pu,s['K'],s['T']);eligible&=pz<=rhit+.05
        weights=np.zeros(len(o['P']));np.add.at(weights,o['F'].ravel(),np.repeat(o['area']/3,3));ii=np.flatnonzero(eligible&(weights>0));ww=weights[ii]
        if len(ii):sample=np.unique(np.searchsorted(np.cumsum(ww),(np.arange(min(96,len(ii)))+.5)/min(96,len(ii))*ww.sum()));hi=ii[sample];hw=weights[hi];hw/=hw.sum()
        else:hi=np.empty(0,int);hw=np.empty(0)
        # Archive pixels of all fixed native depth rays.
        depth_uv=(uv+.5)*[640/width,360/height]-.5
        np.savez_compressed(R/'inputs'/(cid+'.npz'),head=h,full_polyp=s['labels']==1,support=support,support_weights=support_weights,directions=directions,depth_native_uv=uv,depth_archive_uv=depth_uv,depth_mm=zz,pairs=pairs,depth_delta_mm=zz[pairs[:,0]]-zz[pairs[:,1]],HERO_X_mm=o['P'][hi],HERO_weights=hw,HERO_original_vertex_id=hi,K=s['K'],Kn=n['Kn'],T=s['T'],head_metadata=np.array(json.dumps(meta)),valid_native=n['valid'])
        up=c.get('HERO_input_views',[]);b=source(sc['B'][0]);bhash=sha(CC[sc['B'][0]]['RGB']);upstring=json.dumps(up)
        qual.append(dict(source=cid,physical_group=sc['group'],video=c['video'],kind=sc['kind'],role='A_FIT'if cid in fitting else'B_NOT_IN_CURRENT_FIT',tier=sc['tier'],current_camera_gate=GATE[cid]['qualification'],HERO_parent_camera_qualified=c['source_camera_qualified'],HERO_dependency_complete=c['HERO_dependency_complete'],B_RGB_in_HERO_metadata=bhash in upstring or CC[sc['B'][0]]['RGB']in upstring,holdout='CONDITIONAL_UPSTREAM_GATE_SELECTION_DEPENDENCIES',cleanup=n['cleanup_state'],head_status=meta.get('status','ORIGINAL_MASK_SOFT_CUE'),full_polyp_N=int((s['labels']==1).sum()),head_N=int(h.sum()),depth_fixed_pixels=len(uv),depth_fixed_pairs=len(pairs),HERO_point_N=len(hi),formal_3D_truth='NOT_EVALUABLE',RGB=c['RGB'],native_depth=c['E1_actual_native']['path'],distortion=c.get('distortion')))
        print('INPUT',cid,'head',int(h.sum()),'D',len(uv),'H',len(hi),flush=True)
    # Active Is search through the existing complete E3 source audit, never GT files.
    ledger=REPO/'experiments/TASK-E3-A-SOURCE-AUDIT-AND-PROBLEM-DEFINITION-001/metrics/E3_SOURCE_AND_VIEW_MANIFEST.csv'
    with ledger.open()as f:rr=list(csv.DictReader(f))
    isrows=[{k:x.get(k)for k in ['source_id','morphology','camera_status','qualification','native_HERO_path','RGB_path']}for x in rr if x.get('morphology')=='Is']
    save('provenance/IS_ACTIVE_SEARCH.json',dict(source=asset(ledger),candidates=isrows,qualified_Is_found=False,reason='G04/G05 archived cameras unqualified; G07 historical HERO chain unqualified despite partial current single-camera conditional passes; no promotion'))
    for cid in ['G01_005_raw00057','G01_005_raw00459','G01_005_raw00745']:
        c=CC[cid];qual.append(dict(source=cid,physical_group='G01',video='005',kind='Ip',role='AUDIT_ONLY',tier='NOT_EVALUABLE_CURRENT_GATE_AND_CLEANUP_MISSING',current_camera_gate='NOT_AUDITED_CURRENT_V0.1',HERO_parent_camera_qualified=c['source_camera_qualified'],cross_video_merge=False,formal_3D_truth='NOT_EVALUABLE'))
    for x in isrows:qual.append(dict(source=x['source_id'],kind='Is',role='IS_SUPPLEMENTAL_SEARCH',tier='NOT_EVALUABLE_UNQUALIFIED',current_camera_gate=x['camera_status'],formal_3D_truth='NOT_EVALUABLE'))
    table('03_DATA_QUALIFICATION.csv',qual);save('provenance/INPUT_MANIFEST.json',manifest)
    finalize_metadata()
def finalize_metadata():
    files=[REPO/'AGENTS.md',R/'TASK.md',R/'RA_TASK_REFERENCE.md',DXY/'v2.py',DXY/'v2_candidates.py',DXY/'geometry_competition.py',REPO/'visualization/real_p0_renderer.py',N0/'config/CAMERA_GATE_RESULTS.json',N0/'config/CAMERA_GATE_RULES.json',PART/'metrics/view_distribution.json']
    for name in ['TASK-PHASED-INCREMENTAL-FUSION-MULTIGROUP-001','TASK-E3-A-SOURCE-AUDIT-AND-PROBLEM-DEFINITION-001','TASK-E3-B-LOCAL-HERO-FIELDS-001','TASK-E3-C-VISIBILITY-CONSENSUS-001','TASK-E3-D0-OPEN3D-TSDF-BASELINE-001','TASK-E3-N0-NEURALFUSION-EIGHT-VIEW-001','TASK-E3-SDF-RTX4090-M1-10X-MULTIPOLYP-001','TASK-RING-FIRST-POSE-DEPTH-IDENTIFIABILITY-001']:files.append(REPO/'experiments'/name/'TECHNICAL_REPORT.md')
    files+=list((REPO/'docs').glob('KEY_TECHNICAL_VERSION*.md'))
    save('provenance/ASSET_AND_VERSION_AUDIT.json',[asset(p)for p in files]);save('provenance/PREPARED_INPUT_INDEX.json',[asset(p)for p in (R/'inputs').glob('*.npz')])
    # A2 catalog ONLY: retain historical plane/ROI qualifications, no new fits/constraints.
    with (INC/'metrics/C_height_geometry.csv').open()as f:planes=list(csv.DictReader(f))
    table('metrics/A2_BACKGROUND_CATALOG.csv',[{k:x[k]for k in ['scene','reference','ROI_pixels','background_input_N','camera_condition','base_metric_usable','base_status','origin','Ring_plane_used']}for x in planes])
    print('E4_ZERO_PREPARED_NO_OPTIMIZATION',flush=True)
if __name__=='__main__':
    if '--finalize'in sys.argv:finalize_metadata()
    else:main()
