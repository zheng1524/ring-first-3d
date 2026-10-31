"""C0 and C1.1: re-execute the frozen E0 CPU audit by exact AST extraction."""
from common import *
import itertools

def main():
    save('provenance/C0_BEFORE_TEST_FREEZE.json',dict(UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),
         code=[asset(p) for p in sorted((R/'code').glob('*.py'))],config=asset(R/'config/CPU_CONTRACT.json'),
         E0_audit=asset(E0/'code/audit.py'),GT_read=False,model_run_N=0))
    ns=dict(globals())
    extract(E0/'code/audit.py',['audit_inputs'],ns)
    refs,leaks,tests=ns['audit_inputs']()
    # Native pointer aliases are corrected only from the existing infer/package
    # supplement, and their bytes/shape are checked again. Nothing is invented.
    native_fix={x['source']:x for x in load(E0/'provenance/NATIVE_DEPTH_CHAIN_SUPPLEMENT.json')['rows']}
    native_rows=[]
    for c in refs:
        old=c['native_depth'];fix=native_fix.get(c['id'])
        a=asset(fix['actual_native_path'] if fix else old.get('path','/MISSING'), 'actual_native_HERO',
                fix['actual_native_SHA256'] if fix else old.get('sha256'))
        row=dict(source=c['id'],scene=c['scene_id'],display_pointer=old.get('path'),**a)
        if a['status']=='AVAILABLE':
            with np.load(a['path']) as z:
                row.update(keys=list(z.files),array_shapes={k:list(z[k].shape) for k in z.files})
            row['native_identity']='RAW_CHAIN_CORRECTED' if fix else 'ORIGIN_RECORDED_NATIVE'
        else: row['native_identity']='MISSING'
        c['E1_actual_native']=row
        if row['status']!='AVAILABLE' or row.get('hash_match') is False:
            c['input_status']='DATA_INELIGIBLE'
        native_rows.append(row)
    D=load(R/'provenance/INPUT_ELIGIBILITY.json');D['references']=refs
    save('provenance/INPUT_ELIGIBILITY.json',D)
    table('metrics/NATIVE_DEPTH_AUDIT.csv',native_rows)
    ledger=[]
    nodes={};edges=[]
    def node(i,**kw): nodes[i]=dict(id=i,**kw)
    for c in refs:
        cid=c['id'];sid=c['scene_id'];rgb=c['files']['RGB']['sha256'];rid='rgb:'+rgb
        node(rid,kind='real_RGB',path=c['RGB'],sha256=rgb,scene=sid)
        node('camera:'+cid,kind='frozen_camera',path=c['camera_file'],sha256=c['files']['camera_file']['sha256'],scene=sid)
        node('hero:'+cid,kind='HERO_estimate_NOT_GT',path=c['E1_actual_native']['path'],sha256=c['E1_actual_native'].get('sha256'),scene=sid)
        for v in c['HERO_input_views']:
            parent='rgb:'+v['sha256'];node(parent,kind='real_RGB',path=v['RGB'],sha256=v['sha256'],scene=sid)
            edges.append(dict(parent=parent,child='hero:'+cid,relation='HERO_INPUT'))
        f2=PART/f'local_results/pointcloud_blocks/{sid}/ViewPartition_Cleaned_F2/{cid}.npz'
        derivatives=[('Raw',Path(c['source_points']),'hero:'+cid),('Cleaned',Path(c['cleaned_flags']['path']),'Raw:'+cid),
                     ('F1',Path(c['cleaned_flags']['path']),'Cleaned:'+cid),('F2',f2,'Cleaned:'+cid)]
        for kind,p,parent in derivatives:
            info=asset(p,kind);node(kind+':'+cid,kind=kind,scene=sid,independent_observation_increment=0,**info)
            edges.append(dict(parent=parent,child=kind+':'+cid,relation='DERIVED_NOT_NEW_VIEW'))
        ledger.append(dict(group=c['group'],scene=sid,source_id=cid,reference_RGB_SHA256=rgb,
            RGB=c['files']['RGB'],Mask=c['files']['Mask'],pack=c['files']['pack'],actual_native=c['E1_actual_native'],
            Raw_XYZ=c['files']['source_points'],Raw_mesh=c['files']['mesh'],Cleaned=c['cleaned_flags'],
            F1_parent=cid+' Cleaned source-index union',F2=asset(f2,'F2'),
            K_pose=c['files']['camera_file'],K=c['K_raw'],c2w=c['c2w_mm'],camera_quality=c['condition'],
            Ring_CAD=c['Ring_CAD'],coordinate_frame=c['coord_frame'],HERO_input_views=c['HERO_input_views'],
            native_status=c['E1_actual_native']['status'],source_status=c['input_status'],
            training_eligibility='UNQUALIFIED_STRESS' if 'UNQUALIFIED' in c['condition'] else 'CONDITIONAL_NEXT_TASK_ONLY',
            evaluation_eligibility='NO_STRICT_HOLDOUT_CERTIFICATION'))
    f3rows=[]
    for sid in dict.fromkeys(c['scene_id'] for c in refs):
        p=GROW/f'local_results/glb/{sid}_Joint_sources.npz'; scene=GROW/f'local_results/scenes/{sid}_Final.json'
        a=asset(p,'F3 source-indexed existing geometry');a['scene']=sid
        node('F3:'+sid,kind='F3_derived_NOT_GT',scene=sid,independent_observation_increment=0,**asset(p))
        if p.is_file():
            with np.load(p) as z:
                parents=sorted(set(z['source_reference'].tolist()));a.update(point_N=len(z['original_point_id']),parents=parents,keys=z.files)
                for parent in parents:edges.append(dict(parent='Raw:'+parent,child='F3:'+sid,relation='HISTORICAL_ACCEPTED_AND_JOINT_DERIVED'))
        a['scene_faces']=asset(scene);f3rows.append(a)
    save('provenance/F3_SOURCE_AUDIT.json',f3rows)
    save('provenance/E1_SOURCE_DAG.json',dict(nodes=list(nodes.values()),edges=edges,
         note='HERO depth is estimated; F1/F2/F3 are correlated priors. Graph edges are provenance, not new observations.'))
    table('metrics/E1_SOURCE_MANIFEST.csv',ledger)
    # Every same-video reference pair is inspected; the preregistered initial
    # triples are reported as proposals, never chosen using target errors.
    gn=legacy_geometry_namespace(D);points=gn['points'];pairs=[]
    for a,b in itertools.permutations(refs,2):
        if a['scene_id']!=b['scene_id']: continue
        P,_,_,_=points(a['id']);K=np.asarray(b['K_raw']);T=np.asarray(b['c2w_mm'])
        xy,z=vis.project_camera(P,K,T);good=np.isfinite(xy).all(1)&(z>0)
        px=np.zeros_like(xy,dtype=int);px[good]=np.floor(xy[good]+.5).astype(int)
        good&=(px[:,0]>=0)&(px[:,0]<640)&(px[:,1]>=0)&(px[:,1]<360)
        ids=np.flatnonzero(good);pp=np.load(b['pack']);x,y=px[ids].T
        hit=SameCameraScene(ring(b['ring']),K,T,(640,360),str(VENDOR)).cast(xy[ids])['t_hit'].numpy()
        occ=np.isfinite(hit)&(z[ids]>hit+conventions()['CAD_occlusion_tolerance_mm'])
        fg=pp['labels'][y,x]==1;valid=fg&~occ&np.isfinite(pp['depth_mm'][y,x])&(pp['depth_mm'][y,x]>0)
        dz=abs(z[ids][valid]-pp['depth_mm'][y[valid],x[valid]])
        tau=np.maximum(.5,3*z[ids][valid]/min(K[0,0],K[1,1]))
        A=np.asarray(a['c2w_mm']);ang=np.degrees(np.arccos(np.clip(A[:3,2]@T[:3,2],-1,1)))
        shared=set(a['source_alias_hashes'])&set(b['source_alias_hashes'])
        pairs.append(dict(scene=a['scene_id'],source=a['id'],target=b['id'],source_point_N=len(P),projected_in_frame_N=len(ids),
            target_mask_N=int(fg.sum()),CAD_occluded_N=int(occ.sum()),common_visible_depth_N=len(dz),
            covisible_source_fraction=len(dz)/len(P),optical_axis_angle_deg=ang,baseline_mm=np.linalg.norm(A[:3,3]-T[:3,3]),
            RGB_duplicate=a['files']['RGB']['sha256']==b['files']['RGB']['sha256'],shared_HERO_RGB_N=len(shared),
            depth_absolute_delta=stats(dz),depth_conflict_N=int((dz>tau).sum()),
            depth_conflict_fraction=float((dz>tau).mean()) if len(dz) else None,
            depth_is_GT=False,pose_status='FROZEN_CONDITIONAL_SAME_VIDEO'))
    table('metrics/REFERENCE_COVISIBILITY.csv',pairs)
    proposals={'G01_004':['G01_004_ref03','G01_004_ref08','G01_004_ref13'],
               'G01_005':['G01_005_raw00057','G01_005_raw00459','G01_005_raw00745']}
    rr=[]
    for c in refs:
        chosen=c['id'] in proposals.get(c['scene_id'],[])
        role='UNQUALIFIED' if 'UNQUALIFIED' in c['condition'] else 'CORE' if chosen else 'TRANSITION'
        pp=[p for p in pairs if p['source']==c['id'] and p['target'] in proposals.get(c['scene_id'],[])]
        rr.append(dict(scene=c['scene_id'],source=c['id'],role=role,source_camera_qualified=c['source_camera_qualified'],
            native_status=c['E1_actual_native']['status'],input_status=c['input_status'],candidate_only=True,
            proposed_from='preregistration initial triple' if chosen else 'remaining real audited pool',
            distinct_RGB=True,eligible_HERO_dependencies=c['HERO_dependency_complete'],candidate_pair_evidence=pp))
    save('provenance/G01_PROPOSED_INPUTS.json',dict(proposals=proposals,not_authorization_to_train=True,
          evidence_selection='Fixed initial preregistration triple; no GT or evaluation error selection',rows=rr))
    table('metrics/INPUT_QUALIFICATION.csv',rr)
    # Photo geometry remains unregistered even where an intrinsic candidate exists.
    matching=load(PART/'metrics/matching_comparison.json')
    photo=[]
    for v in D['views']:
        if 'photo' not in v['id']:continue
        matches=[x for x in matching if v['id'] in json.dumps(x)]
        photo.append(dict(id=v['id'],RGB=asset(v['RGB']),Mask=asset(v['Mask']),K_candidate=v.get('K'),
            c2w=v.get('c2w'),pose_status=v.get('pose_status'),matching_evidence=matches,
            eligibility='DATA_INELIGIBLE_FOR_METRIC_RECON',reason='Uncertified K/pose; actual image/match candidate only'))
    save('provenance/PHOTO_QUALIFICATION.json',photo)
    for name in ['adjacency_graph.csv','registration_edges.json','matching_comparison.json']:
        p=PART/'metrics'/name
        save('provenance/MAST3R_'+name.replace('.csv','.json'),dict(source=asset(p),
            content=list(csv.DictReader(p.open())) if p.suffix=='.csv' else load(p),new_matching_run=False))
    # Additional synthetic controls catch errors that correct real data cannot.
    K=np.array([[400.,0,319.5],[0,420.,179.5],[0,0,1.]])
    uv=np.array([[0.,0.],[639,359],[319.5,179.5],[40,300]])
    T=np.eye(4);T[:3,3]=[2,3,-40];z=np.array([40.,41.,42.,43.]);P=unproject(z,T,uv,K)
    ray=vis.camera_rays(uv,K,T);unit=ray[:,3:]/np.linalg.norm(ray[:,3:],axis=1,keepdims=True)
    wrong=T[:3,3]+unit*z[:,None];correct=T[:3,3]+unit*(z*np.linalg.norm(ray[:,3:],axis=1))[:,None]
    synt=[dict(test='z_depth_is_not_ray_length',expected='wrong Z-as-length fails',wrong_max_mm=np.max(abs(wrong-P)),correct_max_mm=np.max(abs(correct-P)),pass_test=bool(np.max(abs(wrong-P))>.1 and np.max(abs(correct-P))<1e-6)),
          dict(test='c2w_w2c_roundtrip',N=4,error=np.max(abs(np.linalg.inv(T)@T-np.eye(4))),pass_test=bool(np.allclose(np.linalg.inv(T)@T,np.eye(4),atol=1e-6))),
          dict(test='resize_half_pixel_negative',N=4,missing_offset_px=.25,pass_test=bool(np.max(abs(vis.scaled_intrinsics(K,(640,360),(320,180))[:2,2]-K[:2,2]*.5))==.25))]
    table('metrics/SYNTHETIC_CONVENTION_TESTS.csv',synt)
    table('metrics/OPENCV_METRIC_TESTS.csv',tests)
    # Exact file/function signatures including unsafe legacy mains, no model load.
    reuse=[]
    for item in load(E0/'provenance/CODE_REUSE_EXECUTED.json'):
        p=Path(item['path']);tree=ast.parse(p.read_text())
        names={e['name']for e in item['entrypoints']}
        for n in tree.body:
            if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and (not names or n.name in names):
                reuse.append(dict(role=item['role'],path=str(p),SHA256=sha(p),function=n.name,
                    signature=ast.unparse(n.args) if isinstance(n,ast.FunctionDef) else 'class',
                    executable='READ_ONLY_OR_EXACT_FUNCTION_ONLY',adapter='source-index / file format bridge; legacy main not called',
                    E0_file_hash_equal=sha(p)==item['file_SHA256']))
    for p in [E0/'code/audit.py',E0/'code/sdf_run.py',E0/'code/map_run.py',SDF/'code/model/ray_sampler.py',SDF/'code/model/density.py',SDF/'code/model/network.py',MAP/'mapanything/utils/inference.py']:
        reuse.append(dict(role='CPU/static only',path=str(p),SHA256=sha(p),function='all; see AST/source evidence',signature='STATIC',executable='NO_MAIN_NO_NETWORK_FORWARD',adapter='audit.main invokes CUDA probe; model mains forbidden'))
    table('CODE_REUSE_E1.csv',reuse)
    edge=list(csv.DictReader((R/'provenance/HERO_DEPENDENCY_EDGES.csv').open()))
    save('metrics/C0_SUMMARY.json',dict(expected_reference_N=36,audited_reference_N=len(refs),
        independently_readable_native_N=sum(x['status']=='AVAILABLE' and x.get('hash_match') is not False for x in native_rows),
        reference_RGB_identity_N=len({x['files']['RGB']['sha256']for x in refs}),
        HERO_RGB_identity_N=len({x['RGB_SHA256']for x in edge}),HERO_dependency_edge_N=len(edge),
        strict_holdout_N=0,photo_N=len(photo),model_run_N=0,scientific_success='NOT_EVALUATED',
        C0_state='C0_LIMITED',limitations=['conditional archived cameras','strict holdout unavailable','photos unregistered','cross-video transform uncertified']))
    save('provenance/C0_EXECUTED_REUSE.json',REUSE)
    print('C0_COMPLETE',len(refs),'actual refs;',len(pairs),'same-video pairs;',len(native_rows),'native chains',flush=True)

if __name__=='__main__': main()
