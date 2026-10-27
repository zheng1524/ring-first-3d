"""Source/geometry preservation audit; no clinical ground truth or new optimization."""
from review_assets import *
import subprocess,struct
def main():
    checks=[]
    def ck(name,ok):assert bool(ok),name;checks.append(dict(check=name,passed=True))
    verify();ck('all_frozen_inputs_SHA_unchanged',True)
    for f in load(R/'provenance/RULES_FROZEN.json')['files']:ck('frozen_rule_'+Path(f['path']).name,sha(f['path'])==f['sha256'])
    total=0
    for c in cases():
        s=source(c['id']);raw=np.load(R/f'local_results/{c["id"]}/Raw_exact.npz');total+=len(s['P']);ck(c['id']+'_Raw_XYZ_RGB_faces_original',np.array_equal(raw['XYZ_mm'],s['P'])and np.array_equal(raw['RGB'],s['rgb'])and np.array_equal(raw['faces'],s['m'].faces));old=np.load(R/f'local_results/{c["id"]}/Historical_Density_exact.npz');cand=np.load(R/f'local_results/{c["id"]}/Distance_Exempt_Candidate_exact.npz');T=float(old['rho_threshold']);expected=np.flatnonzero(s['a']['rho_surface_radius']<T)if np.isfinite(T)else np.empty(0,int);ck(c['id']+'_historical_absolute_threshold_exact',np.array_equal(expected,old['deleted_original_indices']));ck(c['id']+'_distance_exemption_only_restores_old_candidates',set(cand['deleted_original_indices'])==set(expected)-set(cand['exempt_original_indices']))
        for label in ['Historical_Density','Distance_Exempt_Candidate','Applied']:
            a=np.load(R/f'local_results/{c["id"]}/{label}_exact.npz');ids=a['kept_original_indices'];deleted=np.zeros(len(s['P']),bool);deleted[a['deleted_original_indices']]=True;Fid=a['kept_original_face_indices'];ck(c['id']+'_'+label+'_source_indices_only',np.array_equal(a['XYZ_mm'],s['P'][ids])and np.array_equal(a['RGB'],s['rgb'][ids])and np.array_equal(Fid,np.flatnonzero(~deleted[s['m'].faces].any(1)))and np.array_equal(a['faces_original_indices'],s['m'].faces[Fid]))
        oldfinal=np.load(ABS/f'local_results/{c["id"]}/Final_Cleaned_exact.npz');ck(c['id']+'_history_Raw_identity_honest',np.array_equal(oldfinal['XYZ_mm'],s['P']));p=s['p'];b=np.load(R/f'local_results/background/{c["id"]}.npz');uv=b['source_uv'];ck(c['id']+'_background_actual_frozen_XYZ',np.array_equal(b['XYZ_mm'],unproject(uv,p['depth_mm'][uv[:,1],uv[:,0]],p['K'],p['pose']))and np.all(p['labels'][uv[:,1],uv[:,0]]==0));ck(c['id']+'_camera_unchanged',np.array_equal(p['pose'],np.load(c['camera_file'])['c2w'][c['reference_index']]))
    ck('four_groups_nine_refs_147540_original_point_exposures',len(cases())==9 and len(set(c['group']for c in cases()))==4 and total==147540)
    witnesses=load(R/'metrics/A_exemption_evidence.json');ck('all_exemptions_have_concrete_other_source_witness',len(witnesses)==sum(len(np.load(R/f'local_results/{c["id"]}/Distance_Exempt_Candidate_exact.npz')['exempt_original_indices'])for c in cases())and all(w['distance_mm']<=.3 and w['target_RGB_Mask_supported']and w['no_front_conflict']for w in witnesses))
    for sc in load(R/'metrics/B_scenes.json'):
        ck(sc['id']+'_no_invented_multi_reference_success',len(sc['references'])>1 or sc['status']=='NO_ADDITIONAL_REFERENCE_AVAILABLE')
        for rank,cid in enumerate(sc['reference_order']):
            s=source(cid);a=np.load(R/f'local_results/scenes/{sc["id"]}/{cid}_faces_exact.npz');P=a['XYZ_mm'];F=a['faces'];parents=a['parent_original_face_id'];w=a['parent_barycentric'];N=int(a['original_vertex_N']);ck(cid+'_all_original_vertices_fixed',np.array_equal(P[:N],s['P'])and np.array_equal(a['RGB'][:N],s['rgb']));ck(cid+'_source_parent_barycentric_geometry',np.all(w>=0)and np.allclose(w.sum(2),1)and np.allclose(P[F],np.einsum('fij,fjk->fik',w,s['P'][s['m'].faces[parents]]),atol=1e-12,rtol=0));ck(cid+'_no_surface_area_created_or_lost_by_subdivision',np.allclose(np.bincount(parents,weights=area(P,F),minlength=len(s['m'].faces))[applied(cid)['kept_original_face_indices']],s['areas'][applied(cid)['kept_original_face_indices']],atol=1e-9,rtol=1e-10));ck(cid+'_exact_applied_parent_identity',np.array_equal(np.unique(parents),applied(cid)['kept_original_face_indices']))
            if rank==0:ck(cid+'_entire_primary_faces_unchanged',np.array_equal(F,applied(cid)['faces_original_indices'])and np.all(a['child_code']==0))
            if len(P)>N:
                edge=a['source_edge_original_ids'][N:];ck(cid+'_midpoints_exactly_on_original_edges',np.array_equal(P[N:],s['P'][edge].mean(1))and np.array_equal(a['RGB'][N:],s['rgb'][edge].mean(1)))
        for mode in ['primary','second','core','evidence']:
            pts,rgb,refs,ids=scene_points(sc,mode)
            for i,c in enumerate(cases()):
                mask=refs==i
                if mask.any():ck(sc['id']+'_'+mode+'_'+c['id']+'_diagnostic_only_actual_P0_points',np.array_equal(pts[mask],source(c['id'])['P'][ids[mask]])and np.array_equal(rgb[mask],source(c['id'])['rgb'][ids[mask]]))
    oldplanes=load(PHASE/'metrics/D3_height_ROI_trials.json');heights=load(R/'metrics/C_height_geometry.json');ck('all_27_base_conditions_kept',len(heights)==27)
    for row in heights:
        if row['group']=='G01':
            old=next(x for x in oldplanes if x['reference']==row['reference']and x['ROI_pixels']==row['ROI_pixels']);ck(row['reference']+str(row['ROI_pixels'])+'_old_base_exact_no_gate_relaxation',np.array_equal(row['plane'],old.get('plane'))and row['numeric_fit_pass']==(old['physical_height_mm']is not None))
        if not row['base_metric_usable']:ck(row['reference']+str(row['ROI_pixels'])+'_failed_height_is_NaN',row['H95_mm']is None)
        ck(row['reference']+str(row['ROI_pixels'])+'_no_Ring_base_or_unqualified_measurement',not row['Ring_plane_used']and(not row['base_metric_usable']or row['source_camera_qualified']))
    initial=load(R/'metrics/D_projected_diameter.json');audit=load(R/'metrics/D_observed_surface_definition_audit.json');ck('all_81_diameter_conditions_and_initial_failures_preserved',len(initial)==len(audit)==81 and all(a['strict_initial_status']==b['status']and a['strict_initial_Dproj_mm']==b['Dproj_mm']for a,b in zip(audit,initial)));ck('no_forced_diameter_or_GT_fallback',all(x['observed_surface_Dproj_mm']is None and x['clinical_full_Dxy_mm']is None for x in audit))
    for row in load(R/'metrics/E_visible_coverage.json'):
        if row['method']in ['B','C']:continue
        sc=next(x for x in load(R/'metrics/B_scenes.json')if x['id']==row['scene']);P,rgb,_r,_id=scene_points(sc,row['method']);z=np.load(R/f'local_results/coverage/{row["scene"]}/{row["method"]}/{row["target"]}/source_RGB_prediction.npz');valid=z['point_RGBA'][:,:,3]>0;ids=z['point_original_id'][valid];ck(row['scene']+row['method']+row['target']+'_predicted_RGB_only_source',np.array_equal(z['point_RGBA'][valid,:3],np.rint(rgb[ids]*255).astype(np.uint8)))
    glbs=load(R/'metrics/GLB_INDEX.json');ck('ten_independent_GLB_scenes',len(glbs)==10)
    for rec in glbs:
        p=Path(rec['path']);ck(p.name+'_SHA',sha(p)==rec['sha256']);sc=trimesh.load(p,force='scene',process=False);ck(p.name+'_standalone_source_scene',len(sc.geometry)==rec['geometries']and not sc.metadata['GT_used']and sc.metadata['primary_original_geometry_fixed']);cad=[g for g in sc.geometry.values()if g.metadata.get('identity')=='KNOWN_CAD'];ck(p.name+'_one_physical_CAD',len(cad)==1);info=next(s for s in load(R/'metrics/B_scenes.json')if s['id']==rec['scene']);ck(p.name+'_CAD_physical_mm_to_m',np.allclose(cad[0].extents,ring(source(info['main_reference'])['c']).extents/1000,atol=1e-9,rtol=0));binary=p.read_bytes();n=struct.unpack_from('<I',binary,12)[0];tree=json.loads(binary[20:20+n]);bg=[m for m in tree['meshes']if m.get('extras',{}).get('kind')=='ACTUAL_BACKGROUND_FROZEN_DEPTH'];ck(p.name+'_POINTS_background_source_extras',len(bg)==len(info['references'])and all(m['primitives'][0]['mode']==0 and len(m['extras']['source_uv'])==len(m['extras']['source_original_indices'])for m in bg));cadmesh=next(m for m in tree['meshes']if m.get('extras',{}).get('identity')=='KNOWN_CAD');mat=tree['materials'][cadmesh['primitives'][0]['material']];ck(p.name+'_opaque_black_solid_CAD',mat['pbrMetallicRoughness']['baseColorFactor']==[0.,0.,0.,1.]);ck(p.name+'_no_hidden_scene_coordinate_change',all(np.array_equal(sc.graph.get(node)[0],np.eye(4))for node in sc.graph.nodes_geometry))
        for g in sc.geometry.values():
            md=g.metadata
            if 'source_mesh_vertex_indices'in md:
                a=np.load(md['source_exact_file']);vid=np.array(md['source_mesh_vertex_indices']);ck(p.name+'_'+md['reference']+'_'+md['source_class']+'_exact_source_vertices_RGB',np.allclose(g.vertices,a['XYZ_mm'][vid]/1000,atol=5e-9,rtol=0)and np.array_equal(g.visual.vertex_colors[:,:3],np.rint(a['RGB'][vid]*255).astype(np.uint8)))
    for item in load(R/'metrics/VISUALIZATION_INDEX.json'):
        for path in item['core_png']:
            with Image.open(path)as im:im.verify()
    ck('four_group_public_actual_PNGs',len(list((R/'figures').glob('*.png')))==4);ck('local_index_and_overview_exist',(R/'visualizations/index.html').is_file()and(R/'visualizations/Overview_Contact_Sheet.png').is_file())
    protected=[]
    for path,old in load(R/'runtime/protected_start.json').items():
        git=lambda *args:subprocess.check_output(['git','-C',path,*args],env={**os.environ,'GIT_OPTIONAL_LOCKS':'0'});idx=Path(git('rev-parse','--git-path','index').decode().strip());idx=idx if idx.is_absolute()else Path(path)/idx;row=dict(path=path,HEAD=git('rev-parse','HEAD').decode().strip()==old['HEAD'],index=sha(idx)==old['index_SHA256'],status=hashlib.sha256(git('status','--porcelain=v1','-z','-uall')).hexdigest()==old['status_SHA256'],modified_science_unchanged=all(sha(Path(path)/p)==h for p,h in old['modified_files'].items()));protected.append(row);ck(path+'_protected',all(v for k,v in row.items()if k!='path'))
    save('metrics/PROTECTED_WORKSPACES.json',protected);save('metrics/VALIDATION.json',dict(status='PASS',checks_N=len(checks),checks=checks,independent_geometry_certification=False));print('VALIDATION_PASS',len(checks),flush=True)
if __name__=='__main__':main()
