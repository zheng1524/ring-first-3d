"""Freeze source selection, one bounded A2 cleanup and per-group metric domains."""
from common import *
from scipy.spatial.transform import Rotation
from scipy import ndimage
extract(A2/'code/common.py',['neighbours'],globals())
LEGACY_V6=['G01_004_ref08','G01_004_ref13','G01_004_ref03','G01_004_growth_r04','G01_004_new_r00','G01_004_growth_r14']
RULES=dict(selection='G01 starts ref08/ref13/ref03 if admitted; then uncovered-block-first farthest direction+camera-center sampling over ALL remaining admitted11, strict/conditional Gate and Ring pass tie priorities, source ID final tie; no NF outputs',
    second_group='maximize (strict fraction, Ring-pass fraction, negative median Ring p95, block count, valid-depth fraction, admitted count); input-only; no inferred missing views',
    cleanup='accepted V6 baseline for existing6; raw-native baseline for others; one A2 candidate/projection pass for selected sources of each group; B proposals use latest all-B screen except Ring/identity unknown; no new manual spatial cuts',
    candidate_generation=load(A2/'config/A2_PREREGISTERED.json')['candidate_generation'],
    silhouette_margin_archived_px=8.,support_tolerance_mm=.25,CAD_epsilon_mm=.002,independent_opposing_blocks=2,
    CORE_protection='G01 existing CORE and other-group legacy ref source: interior>2 native px and original Raw distance<=1mm',
    mask_boundary='A2 native-label distanceTransform L2 mask5 only for candidate/protection; no new edge threshold search; B is all-B, not A3<=2px',
    crop='exact unchanged Gate A make_crop; raw label bbox; no3px gate',domain='all retained native XYZ+actual CAD; max(2mm,.1span) margin; ceil .001mm;128cube',
    evaluation='fixed RAW native Polyp finite-positive denominator; deletions unavailable, misses explicit; all original Raw faces; CAD separate; .25mm support proxy',
    runtime='complete forward and reverse all prefixes; quality never early-stop; engineering faults only; no training')
def direction(cid):return source(cid)['T'][:3,2]
def diversity(cid,chosen):
    a=source(cid);values=[]
    for other in chosen:
        b=source(other);angle=np.degrees(np.arccos(np.clip(direction(cid)@direction(other),-1,1)));distance_C=np.linalg.norm(a['T'][:3,3]-b['T'][:3,3]);values.append(angle+distance_C)
    return min(values)if values else 0.
def selection(gate):
    by={r['source']:r for r in gate['sources']};available={s:[c for c in IDS if CC[c]['scene_id']==s and by[c]['admission']!='NOT_ADMITTED']for s in SCENES}
    chosen=[c for c in ['G01_004_ref08','G01_004_ref13','G01_004_ref03']if c in available['G01_004']]
    while len(chosen)<min(8,len(available['G01_004'])):
        covered={block(c)for c in chosen};remaining=[c for c in available['G01_004']if c not in chosen]
        best=max(remaining,key=lambda c:(block(c)not in covered,by[c]['qualification']=='CONDITIONAL_USABLE',by[c]['Ring_pass'],diversity(c,chosen),c))
        chosen.append(best)
    quality=[]
    for scene in SCENES[1:]:
        allids=[c for c in IDS if CC[c]['scene_id']==scene];ii=available[scene];validfractions=[native(c)['valid'].sum()/max(1,(native(c)['native_labels']==1).sum())for c in ii]
        score=[sum(by[c]['qualification']=='CONDITIONAL_USABLE'for c in ii)/max(1,len(allids)),sum(by[c]['Ring_pass']for c in ii)/max(1,len(allids)),-float(np.median([by[c]['Ring_p95_px']for c in ii]))if ii else -1e9,len({block(c)for c in ii}),float(np.median(validfractions))if ii else 0,len(ii)]
        quality.append(dict(scene=scene,score=score,admitted_sources=ii,existing_source_N=len(allids),qualified_or_conditionally_admitted_N=len(ii),blocks=sorted({block(c)for c in ii})))
    second=max(quality,key=lambda r:r['score']);si=second['admitted_sources'];order=[]
    if si:order=[next((c for c in si if '_ref'in c),si[0])]
    while len(order)<min(8,len(si)):
        covered={block(c)for c in order};remaining=[c for c in si if c not in order];order.append(max(remaining,key=lambda c:(block(c)not in covered,by[c]['qualification']=='CONDITIONAL_USABLE',by[c]['Ring_pass'],diversity(c,order),c)))
    return {'G01_004':chosen,second['scene']:order},quality,by
def baseline(cid):
    n=native(cid)
    if cid in LEGACY_V6:
        p=np.load(A3/'local_results/inputs/V6'/(cid+'.npz'));depth=p['depth_mm'].copy();valid=p['valid'].copy();baseline_kind='ACCEPTED_V6'
    else:depth=np.where(n['valid'],n['depth'],0).astype(np.float32);valid=n['valid'].copy();baseline_kind='ORIGINAL_NATIVE'
    assert not (valid&~n['valid']).any();assert np.array_equal(depth[valid],n['depth'][valid]);v,u=np.nonzero(valid);uv=np.c_[u,v]
    return dict(n,depth=depth,valid=valid,native_uv=uv,native_id=v*depth.shape[1]+u,X=unproject(depth[v,u].astype(float),n['T'],uv,n['Kn']),baseline_kind=baseline_kind)
def cleanup(scene,ids,by):
    ss={cid:baseline(cid)for cid in ids};Q=np.concatenate([s['X']for s in ss.values()]);lo,hi=Q.min(0),Q.max(0);candidates=[];discovery=[]
    for cid,s in ss.items():
        X=s['X'];u,v=s['native_uv'].T;pixel=s['native_id'];raw=original(cid);d=distance(mesh_scene(raw['P'],raw['F']),X);dt=cv2.distanceTransform(s['valid'].astype(np.uint8),cv2.DIST_L2,5)[v,u];jump=neighbours(s['depth'],s['valid'])[v,u]
        extrema=np.zeros(len(X),bool);extrema[np.r_[X.argmin(0),X.argmax(0)]]=True;bound=np.minimum(abs(X-lo),abs(X-hi)).min(1)<=.25;discontinuous=jump>=1.;rawedge=(d>1)&(dt<=2)
        flags=extrema|bound|discontinuous|rawedge;j=np.flatnonzero(flags);priority=np.select([extrema,bound,discontinuous,rawedge],[1,2,3,4],default=9);ordered=j[np.lexsort((pixel[j],priority[j]))];pick=ordered[:512]
        for k in pick:candidates.append(dict(source=cid,native_id=int(pixel[k]),X_mm=float(X[k,0]),Y_mm=float(X[k,1]),Z_mm=float(X[k,2]),source_mask_interior_px=float(dt[k]),distance_to_own_Raw_mm=float(d[k]),depth_jump_mm=float(jump[k]),priority=int(priority[k])))
        discovery.append(dict(scene=scene,source=cid,raw_native_N=int(native(cid)['valid'].sum()),baseline_N=len(X),baseline_kind=s['baseline_kind'],flagged_N=len(j),review_N=len(pick),unreviewed_retained_N=len(j)-len(pick),raw_gt1mm_proxy_N=int((d>1).sum())))
    for i,r in enumerate(candidates):r['candidate_id']=scene+'_'+str(i)
    evidence=[];evby={r['candidate_id']:[]for r in candidates}
    for observer,t in ss.items():
        cc=[r for r in candidates if r['source']!=observer];X=np.array([[r[k]for k in ['X_mm','Y_mm','Z_mm']]for r in cc]);uv,z=vis.project_camera(X,t['K'],t['T']);nuv,_=vis.project_camera(X,t['Kn'],t['T']);h,w=t['depth'].shape
        inside=np.isfinite(uv).all(1)&np.isfinite(z)&(z>0)&(uv[:,0]>=-.5)&(uv[:,0]<639.5)&(uv[:,1]>=-.5)&(uv[:,1]<359.5)&(nuv[:,0]>=-.5)&(nuv[:,0]<w-.5)&(nuv[:,1]>=-.5)&(nuv[:,1]<h-.5)
        j=np.flatnonzero(inside);pix=np.floor(uv[j]+.5).astype(int);npix=np.floor(nuv[j]+.5).astype(int);lab=np.full(len(cc),-1,int);dist=np.full(len(cc),np.nan);cad=np.full(len(cc),np.inf);zd=np.full(len(cc),np.nan);zn=np.full(len(cc),np.nan);legal=np.zeros(len(cc),bool)
        dm=cv2.distanceTransform((t['labels']!=1).astype(np.uint8),cv2.DIST_L2,5);pack=np.load(t['c']['pack'])
        lab[j]=t['labels'][pix[:,1],pix[:,0]];dist[j]=dm[pix[:,1],pix[:,0]];cad[j],_=cast(ringscene(scene),uv[j],t['K'],t['T']);zd[j]=pack['depth_mm'][pix[:,1],pix[:,0]];zn[j]=t['depth'][npix[:,1],npix[:,0]];legal[j]=t['valid'][npix[:,1],npix[:,0]]
        hidden=np.isfinite(cad)&(z>cad+.002);qualified=by[observer]['negative_vote_eligible']
        for k,row in enumerate(cc):
            near=False;oppose=False;layer=False
            if not inside[k]:status='C_OUTSIDE_FIELD'
            elif hidden[k]:status='C_CAD_OCCLUDED'
            elif lab[k]==2:status='C_RING_MASK'
            elif lab[k]==1 and legal[k]and ((np.isfinite(zd[k])and zd[k]>0 and abs(z[k]-zd[k])<=.25)or abs(z[k]-zn[k])<=.25):near=True;status='D_NEAR_SUPPORT'
            elif lab[k]==1 and legal[k]:layer=qualified;status='B_LAYER_COMPETITION'if qualified else'C_UNQUALIFIED_LAYER'
            elif lab[k]==1:status='C_INVALID_OR_EXCLUDED_POLYP_DEPTH'
            elif lab[k]==0 and dist[k]>8:oppose=qualified;status='A_CONTOUR_PROXY'if qualified else'C_UNQUALIFIED_NEGATIVE_VOTER'
            else:status='C_BOUNDARY_UNKNOWN'
            ev=dict(candidate_id=row['candidate_id'],source=row['source'],native_id=row['native_id'],observer=observer,observer_block=block(observer),u=float(uv[k,0]),v=float(uv[k,1]),axial_Z_mm=float(z[k]),mask=int(lab[k]),outside_Polyp_px=float(dist[k]),CAD_first_hit_mm=float(cad[k]),CAD_occluded=bool(hidden[k]),near_support=near,layer_veto=layer,negative_vote=oppose,status=status,camera_qualification=by[observer]['qualification'],conditional_proxy_only=True)
            evidence.append(ev);evby[row['candidate_id']].append(ev)
    decisions=[];suppressed={cid:[]for cid in ids}
    for row in candidates:
        ev=evby[row['candidate_id']];opposing=sorted({r['observer_block']for r in ev if r['negative_vote']});near=[r['observer']for r in ev if r['near_support']];layer=[r['observer']for r in ev if r['layer_veto']];cid=row['source'];s=ss[cid]
        protect=(cid in CORE or '_ref'in cid)and row['source_mask_interior_px']>2 and row['distance_to_own_Raw_mm']<=1
        if near:cat='D_SUPPORTED_RETAIN'
        elif layer:cat='B_DEPTH_LAYER_RETAIN'
        elif protect:cat='C_UNKNOWN_RETAIN'
        elif len(opposing)>=2:cat='A_STRONG_CONTOUR_PROXY_EXCLUDE'
        else:cat='C_UNKNOWN_RETAIN'
        pid=row['native_id'];uv=np.array([[pid%s['depth'].shape[1],pid//s['depth'].shape[1]]]);archive=affine_uv(uv,s['K']@np.linalg.inv(s['Kn']))[0];p=np.floor(archive+.5).astype(int);legal=bool(np.isfinite(archive).all()and -.5<=archive[0]<639.5 and -.5<=archive[1]<359.5);label=int(s['labels'][p[1],p[0]])if legal else-1
        remove=cat.startswith('A_')or(cat.startswith('B_')and label in [0,1]);reason='A2_TWO_BLOCK_CONTOUR'if cat.startswith('A_')else('LATEST_ALL_B_MASK_SCREEN'if remove else'UNKNOWN_RING_OR_SUPPORTED_RETAIN')
        if remove:suppressed[cid].append(pid)
        decisions.append(dict(**row,category=cat,original_archive_mask=label,action='DERIVED_EXCLUDE'if remove else'RETAIN',reason=reason,opposing_blocks=opposing,near_sources=near,layer_sources=layer,CORE_protected=protect))
    counts=[]
    for cid,s in ss.items():
        n=native(cid);mask=np.zeros(s['valid'].shape,bool);mask.flat[np.array(suppressed[cid],np.int64)]=True;valid=s['valid']&~mask;depth=np.where(valid,s['depth'],0).astype(np.float32)
        out=R/'frozen_inputs/native'/(cid+'.npz');out.parent.mkdir(parents=True,exist_ok=True);np.savez_compressed(out,depth_mm=depth,valid=valid,original_native_id=np.arange(depth.size).reshape(depth.shape),historical_excluded=n['valid']&~s['valid'],incremental_excluded=mask)
        def topology(v):
            lab,N=ndimage.label(v);sizes=np.bincount(lab.ravel())[1:];holes=ndimage.binary_fill_holes(v)&~v;return dict(components_N=N,largest_component_N=int(sizes.max())if len(sizes)else 0,closed_hole_pixels=int(holes.sum()))
        before,after=topology(s['valid']),topology(valid);counts.append(dict(scene=scene,source=cid,raw_N=int(n['valid'].sum()),baseline_N=int(s['valid'].sum()),previous_removed_N=int((n['valid']&~s['valid']).sum()),incremental_removed_N=int(mask.sum()),cleaned_N=int(valid.sum()),before=before,after=after,additional_closed_hole_pixels=after['closed_hole_pixels']-before['closed_hole_pixels'],file=asset(out)))
    table('metrics/'+scene+'_CANDIDATE_DISCOVERY.csv',discovery);table('metrics/'+scene+'_CLEANUP_DECISIONS.csv',decisions);table('metrics/'+scene+'_PROJECTIVE_EVIDENCE.csv',evidence)
    save('metrics/'+scene+'_CLEANUP_SUMMARY.json',dict(sources=counts,candidate_N=len(candidates),categories={c:sum(r['category']==c for r in decisions)for c in sorted({r['category']for r in decisions})},rounds=1,manual_G01_region_not_transferred=True))
    return counts
def make_domain(scene,ids):
    m=ringmesh(scene);Q=np.concatenate([cleaned(c)['X']for c in ids]+[np.asarray(m.vertices)]);lo,hi=Q.min(0),Q.max(0);span=np.ptp(Q,axis=0).max();margin=max(2.,.1*span);L=float(np.ceil((span+2*margin)*1000)/1000);O=(lo+hi)/2-L/2
    ring=np.asarray(m.vertices);rm=(ring-O)/L;back=rm*L+O
    return dict(O_mm=O,L_mm=L,N=128,voxel_mm=L/128,world_cube_min_mm=O,world_cube_max_mm=O+L,source_extent_min_mm=lo,source_extent_max_mm=hi,margin_mm=margin,world_to_model='(X_mm-O_mm)/L_mm',ring_inverse_max_mm=float(np.linalg.norm(back-ring,axis=1).max()),ring_outer_diameter_inverse_mm=float(np.ptp(back,axis=0)[:2].max()),ring_outer_diameter_voxels=float(np.ptp(ring,axis=0)[:2].max()/(L/128)))
def main():
    assert not (R/'config/EXPERIMENT_FROZEN.json').exists(),'PREPARATION_FROZEN_NO_REPEAT'
    # Rule text is written before reading any qualification result or network output.
    if not (R/'config/PREPARATION_RULES.json').exists():save('config/PREPARATION_RULES.json',RULES)
    gate=load(R/'config/CAMERA_GATE_RESULTS.json');selected,quality,by=selection(gate);assert all(selected.values()),'NO_ADMITTED_GROUP_INPUTS'
    source_rows=[]
    for scene,ii in selected.items():
        for j,cid in enumerate(ii):source_rows.append(dict(scene=scene,stage='F'+str(j),source=cid,block=block(cid),qualification=by[cid]['qualification'],admission=by[cid]['admission'],Ring_pass=by[cid]['Ring_pass'],historical_screened=by[cid]['historical_screened'],selection_reason='prespecified CORE seed'if scene=='G01_004'and j<3 else'uncovered-block-first farthest pose from ALL available candidates',raw_frame=CC[cid]['raw_frame'],cached_reference=CC[cid]['reference']))
    save('config/VIEW_SELECTION_FROZEN.json',dict(orders=selected,second_group_input_quality=quality,sources=source_rows,selected_before_cleanup_and_network=True,selection_uses_GT=False))
    table('VIEW_SELECTION.csv',source_rows)
    p=R/'VIEW_SELECTION_8.md';p.write_text('# Frozen view selection\n\nAll rows retain current qualification. INSUFFICIENT_EVIDENCE is conditionally admitted research input, never certified pose. Selection uses ALL existing11 G01 candidates and fixed partition/pose rule, no NeuralFusion output.\n\n'+''.join(f"- {r['scene']} {r['stage']}: {r['source']}; {r['block']}; {r['qualification']}; Ring pass={r['Ring_pass']}.\n"for r in source_rows)+'\nSecond-group input-only scoring and all rejected/redundant candidates: config/VIEW_SELECTION_FROZEN.json and metrics/CAMERA_QUALIFICATION.csv. Missing eight sources are reported, not manufactured.\n')
    original_assets=[]
    for scene,ii in selected.items():
        for cid in ii:
            c=CC[cid]
            for key in ['RGB','Mask','pack','source_points','mesh','camera_file']:
                a=asset(c[key]);assert a['sha256']==c['files'][key]['sha256'];original_assets.append(a)
            a=asset(c['E1_actual_native']['path']);assert a['sha256']==c['E1_actual_native']['sha256'];original_assets.append(a)
            a=asset(c['Ring_CAD']['path']);assert a['sha256']==c['Ring_CAD']['sha256'];original_assets.append(a)
    save('provenance/ORIGINAL_SHA_START.json',dict(files=original_assets))
    for scene,ii in selected.items():
        previous=R/f'metrics/{scene}_CLEANUP_SUMMARY.json'
        if previous.exists():
            for row in load(previous)['sources']:assert sha(row['file']['path'])==row['file']['sha256']
            print('REUSE_COMPLETED_FIXED_CLEANUP',scene,flush=True)
        else:print('CLEAN',scene,cleanup(scene,ii,by),flush=True)
    domains={scene:make_domain(scene,ii)for scene,ii in selected.items()};geos=[]
    for scene,ii in selected.items():
        dom=domains[scene];O=np.array(dom['O_mm']);L=dom['L_mm']
        for cid in ii:
            s=cleaned(cid);cp=make_crop(s);path=R/'frozen_inputs/crops'/(cid+'.npz');path.parent.mkdir(parents=True,exist_ok=True);np.savez_compressed(path,**cp)
            X=s['X'];model=(X-O)/L;assert ((model>=0)&(model<1)).all();assert not (cp['depth_mm'][~cp['valid']]!=0).any()
            j=cp['source_ids'][cp['valid']];assert np.array_equal(cp['depth_mm'][cp['valid']],s['depth'].flat[j]);TM=s['T'].copy();TM[:3,3]=(TM[:3,3]-O)/L
            back=unproject(cp['depth_mm'][cp['valid']].astype(float)/L,TM,cp['output_uv'],cp['K_crop'])*L+O;err=float(np.linalg.norm(back-cp['output_X_mm'],axis=1).max());assert err<1e-5
            geos.append(dict(scene=scene,source=cid,native_retained_N=len(X),crop_N=int(cp['valid'].sum()),out_of_grid_N=0,crop_roundtrip_max_mm=err,source_ID_depth_exact=True,crop=asset(path),native=asset(R/'frozen_inputs/native'/(cid+'.npz'))))
    table('metrics/INPUT_GEOMETRY_VALIDATION.csv',geos)
    official=load(GA/'config/OFFICIAL_ARTIFACTS.json');checked=[]
    for a in official['official_files']:
        if a['relative_path'].startswith(('pipeline/','utils/geometry.py','pretrained_models/shapenet_noise_005/')):
            p=NF/a['relative_path'];assert sha(p)==a['sha256'];checked.append(asset(p))
    # Audited AST-only translator utility, without importing GT/training runtime.
    import shutil
    target=R/'runtime/official_readonly/training_utils.py';target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(RB/'runtime/official_readonly/training_utils.py',target)
    b=target.read_bytes();assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()=='997c7e67c5f3167fd6c084478ead72f2bdeaaf5e'
    save('provenance/OFFICIAL_CHECKED_FILES.json',dict(files=checked+[asset(target)]))
    cfg=dict(task=R.name,orders=selected,domains=domains,grid_N=128,latent_features=17,checkpoint=load(GA/'config/CHECKPOINT_FILES.json')[0],official_commit='4f0c14f67ad9d2368b68cbeb78c237a6328971e5',reverse_orders={scene:list(reversed(ii))for scene,ii in selected.items()},qualification=asset(R/'config/CAMERA_GATE_RESULTS.json'),selection=asset(R/'config/VIEW_SELECTION_FROZEN.json'),cleanup_rules=asset(R/'config/PREPARATION_RULES.json'),input_geometry=geos,quality_stop=False,optimizer_steps=0,GT=False,enhanced_20_30=False,evaluation=dict(agreement_mm=.25,CAD_epsilon_mm=.002,denominator='all original valid native Polyp pixels for selected sources, fixed for all prefixes/orders; cleanup availability separate',face_denominator='all original Raw faces and areas',normal_smoothing_geometry=False))
    save('config/EXPERIMENT_FROZEN.json',cfg);save('provenance/BEFORE_GPU.json',dict(protocol=asset(R/'config/EXPERIMENT_FROZEN.json'),technical_version=asset(REPO/'docs/KEY_TECHNICAL_VERSION_v1.0.md'),code=[asset(p)for p in (R/'code').glob('*.py')],inputs=[a for r in geos for a in [r['crop'],r['native']]],timestamp_UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),forward_N=0))
    print('FROZEN',selected,'DOMAINS',clean(domains),flush=True)
if __name__=='__main__':main()
