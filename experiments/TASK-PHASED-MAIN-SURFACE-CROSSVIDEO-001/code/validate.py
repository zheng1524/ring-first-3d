"""Artifact-level audit: source identity, transforms, colors, GLB and old workspaces."""
from evaluation import *
import subprocess,struct
def main():
    rows=[]
    def check(name,value,detail=None):
        ok=bool(value);rows.append(dict(check=name,passed=ok,detail=detail));assert ok,name
    verify();check('all_input_SHA256_unchanged',True)
    archives=list((R/'provenance/frozen_sources').glob('*.py'))
    for name in ['SOURCE_RULES_FROZEN','EVALUATION_D2_FROZEN','D1_YAW_PROFILE_BEFORE_COMPUTE','D1_BACKUP_BEFORE_COMPUTE','D3_BEFORE_COMPUTE','POST_ANALYSIS_SOURCES']:
        manifest=load(R/f'provenance/{name}.json');files=manifest.get('files',[dict(path=str(R/'code/yaw_observability.py'),sha256=manifest.get('source_sha256'))])
        for f in files:
            current=sha(f['path'])==f['sha256'];archived=any(sha(p)==f['sha256']for p in archives);check(name+':'+Path(f['path']).name,current or archived,'current exact source'if current else'exact execution source archived; bookkeeping/metadata change documented')
    Ptotal=0
    for video in ['004','005']:
        d=load(R/f'metrics/D0_{video}.json');check(video+'_three_source_layers',len(d['all_available_references'])==3);main=d['main_reference']
        for c in [x for x in cases()if x['video']==video]:
            s=source(c['id']);a=dict(np.load(R/f'local_results/D0/{video}/{c["id"]}_source_exact.npz'));Ptotal+=len(s['P']);check(c['id']+'_XYZ_original_bit_exact',np.array_equal(a['XYZ_mm'],s['P']));check(c['id']+'_source_RGB_exact',np.array_equal(a['RGB'],s['rgb']));check(c['id']+'_original_faces_exact',np.array_equal(a['faces'],s['m'].faces));check(c['id']+'_source_pixel_identity',np.array_equal(a['source_uv'],np.c_[s['a']['source_u'],s['a']['source_v']]));check(c['id']+'_status_total_faces',len(a['face_status'])==len(a['faces'])and set(a['face_status'])<=set(range(6)))
            if c['id']==main:check(c['id']+'_entire_primary_preserved',not np.any(a['face_status']==4))
            b=dict(np.load(R/f'local_results/background/{c["id"]}.npz'));uv=b['source_uv'];z=s['p']['depth_mm'][uv[:,1],uv[:,0]];check(c['id']+'_background_frozen_depth_original_XYZ',np.array_equal(b['XYZ_mm'],unproject(uv,z,s['p']['K'],s['p']['pose'])));check(c['id']+'_background_mask_zero',np.all(s['p']['labels'][uv[:,1],uv[:,0]]==0));check(c['id']+'_source_camera_equals_frozen',np.array_equal(s['p']['pose'],np.load(c['camera_file'])['c2w'][c['reference_index']]))
        p=dict(np.load(R/f'local_results/D0/{video}/scene_points_exact.npz'))
        for i,c in enumerate(cases()):
            ids=p['source_case_index']==i
            if ids.any():check(c['id']+'_derived_points_have_original_ids',np.array_equal(p['XYZ_mm'][ids],source(c['id'])['P'][p['source_original_id'][ids]]))
    check('one_group_two_videos_six_references_98843_points',len(cases())==6 and Ptotal==98843)
    targets_held=target('004','holdout')+target('005','holdout');check('five_frozen_target_roles',len(targets())==5 and len(targets_held)==3 and all(t['not_in_any_source_HERO_inputs']for t in targets()))
    candidates=load(R/'metrics/D1_candidates.json');check('two_historical_five_GICP_one_PnP',len(candidates)==8 and sum(c['tag'].startswith('GICP')for c in candidates)==5)
    for c in candidates:check(c['tag']+'_SE3_no_scale',ring_geometry(np.array(c['H_005_to_004']))['SE3'])
    gate=load(R/'metrics/D2_gate.json');check('D2_NOT_FUSED_no_silent_fusion',gate['status']=='NOT_FUSED'and not list((R/'local_results').rglob('*D2_duplicate_face_indices.npz')))
    backup=load(R/'metrics/D1_backup_PnP.json');check('PnP_original_17_background_matches_3_fixed_subsets',backup['usable_background_nonheld_quality_N']==17 and len(backup['runs'])==3 and backup['resampling_stable']and not backup['target_depth_used'])
    disp=load(R/'metrics/D1_display_candidate.json');check('active_candidate_is_frozen_seed0',disp['candidate']=='CACHED_LIGHTGLUE_PNP_SEED0'and np.array_equal(disp['H_005_to_004'],backup['runs'][0]['H_005_to_004']))
    for video,other in [('005','004'),('004','005')]:
        P,rgb,kind=point_data(video,'D0_FULL');m=geometry(video,'D0_FULL');C=m.visual.vertex_colors[:,:3]/255.
        for t in target(other,'holdout'):
            dest=R/f'local_results/D1_evaluation/{disp["candidate"]}/{video}_to_{other}/{t["id"]}';p=dict(np.load(dest/'point_prediction_exact.npz'));valid=p['kind']>0;ids=p['source_original_id'][valid];check(video+'_'+t['id']+'_point_RGB_from_original_source_A',np.array_equal(p['RGBA'][valid,:3],np.rint(rgb[ids]*255).astype(np.uint8)));check(video+'_'+t['id']+'_transparent_unknown_positive_depth',np.all(p['RGBA'][~valid,3]==0)and np.all(p['z'][valid]>0));tri=dict(np.load(dest/'triangle_prediction_exact.npz'));valid=tri['kind']>0;F=m.faces[tri['face_id'][valid]];w=tri['source_barycentric'][valid];expected=np.rint(np.clip((C[F]*np.c_[1-w.sum(1),w][:,:,None]).sum(1),0,1)*255).astype(np.uint8);check(video+'_'+t['id']+'_original_triangle_source_RGB_no_B_recolor',np.array_equal(expected,tri['RGBA'][valid,:3]))
    d3=load(R/'metrics/D3_height_ROI_trials.json');check('D3_eighteen_conditions_no_Ring_base',len(d3)==18 and not any(x['Ring_plane_used']for x in d3));check('D3_failure_NaN_not_historical_fallback',sum(x['physical_height_mm']is not None for x in d3 if x['video']=='004')==0 and sum(x['physical_height_mm']is not None for x in d3 if x['video']=='005')==4)
    correction=load(R/'metrics/D3_height_sensitivity_corrected.json');check('zero_angle_height_equals_frozen_plane',len(correction)==18 and all(abs(v['change_from_original_mm'])<1e-8 for x in correction for v in x['normal_perturbations']if v['degrees']==0))
    glbs=load(R/'metrics/GLB_INDEX.json');check('three_independent_GLBs',len(glbs)==3)
    for item in glbs:
        p=Path(item['file']);check(p.name+'_SHA',sha(p)==item['sha256']);binary=p.read_bytes();length=struct.unpack_from('<I',binary,12)[0];tree=json.loads(binary[20:20+length]);scene=trimesh.load(p,force='scene',process=False);check(p.name+'_standalone_reload',len(scene.geometry)==item['geometries']);check(p.name+'_meters_and_no_GT',scene.metadata['serialized_unit']=='meters'and scene.metadata['GT_used']is False);ring_items=[x for x in tree['meshes']if x.get('extras',{}).get('identity')=='KNOWN_CAD_NOT_RECONSTRUCTED'];check(p.name+'_one_original_CAD',len(ring_items)==1)
        material=tree['materials'][ring_items[0]['primitives'][0]['material']];check(p.name+'_black_opaque_CAD',material['pbrMetallicRoughness']['baseColorFactor']==[0.,0.,0.,1.]and material.get('alphaMode','OPAQUE')=='OPAQUE')
        rg=next(g for g in scene.geometry.values()if g.metadata.get('identity')=='KNOWN_CAD_NOT_RECONSTRUCTED');check(p.name+'_CAD_full_thickness_and_scale',np.allclose(rg.extents,[.0124,.0124,.0012],atol=1e-9))
        refs=set();bgN=0
        for x in tree['meshes']:
            md=x.get('extras',{})
            if 'reference'not in md:continue
            refs.add(md['reference']);isbg=md.get('status')=='OBSERVED_BACKGROUND_MODEL_PREDICTED_UNCERTIFIED'
            if isbg:
                bgN+=1;check(p.name+'_'+md['reference']+'_POINTS_BG_source',x['primitives'][0]['mode']==0 and len(md['source_uv'])==len(md['original_background_ids']));g=scene.geometry[x['name']];b=dict(np.load(R/f'local_results/background/{md["reference"]}.npz'));ids=np.array(md['original_background_ids']);check(p.name+'_'+md['reference']+'_POINTS_BG_original_XYZ_RGB',np.allclose(g.vertices,b['XYZ_mm'][ids]/1000,atol=5e-9,rtol=0)and np.array_equal(g.colors[:,:3],np.rint(b['RGB'][ids]*255).astype(np.uint8)))
            if 'source_original_vertex_ids'in md:
                g=scene.geometry[x['name']];src=source(md['reference']);ids=np.array(md['source_original_vertex_ids']);fid=np.array(md['source_original_face_ids']);check(p.name+'_'+x['name']+'_source_geometry',np.allclose(g.vertices,src['P'][ids]/1000,atol=5e-9,rtol=0)and np.array_equal(ids[g.faces],src['m'].faces[fid]));check(p.name+'_'+x['name']+'_source_RGB',np.array_equal(g.visual.vertex_colors[:,:3],np.rint(src['rgb'][ids]*255).astype(np.uint8)))
        for node in scene.graph.nodes_geometry:
            T,gid=scene.graph.get(node);g=scene.geometry[gid];video=g.metadata.get('video')
            if video:
                expected_T=np.array(disp['H_005_to_004'])if video=='005'and'candidate'in p.name else np.eye(4);expected_T=expected_T.copy();expected_T[:3,3]/=1000;check(p.name+'_'+node+'_correct_node_transform',np.allclose(T,expected_T,atol=1e-12))
        expected=6 if'candidate'in p.name else 3;check(p.name+'_all_source_references_and_BG',len(refs)==expected and bgN==expected)
        if'candidate'in p.name:check(p.name+'_honest_NOT_FUSED',scene.metadata['status']=='CROSS_VIDEO_REGISTRATION_CANDIDATE_NOT_FUSED'and np.array_equal(scene.metadata['H_005_to_004_mm'],disp['H_005_to_004']))
    if (R/'provenance/GLB_METADATA_REPAIR.json').exists():
        for x in load(R/'provenance/GLB_METADATA_REPAIR.json')['assets']:check(Path(x['file']).name+'_metadata_only_binary_geometry_same',x['geometry_and_RGB_binary_unchanged'])
    figs=list((R/'figures').glob('*.png'));check('exactly_four_core_real_PNGs',len(figs)==4)
    for p in figs:
        with Image.open(p)as im:im.verify()
    for x in load(R/'metrics/DIAGNOSTIC_VIEW_INDEX.json'):
        p0=np.array(x['poses'][0]['c2w'])
        for z in x['poses'][1:]:T=np.array(z['c2w']);check(x['scene']+'_'+z['name']+'_baseline_translation',np.array_equal(T[:3,:3],p0[:3,:3])and np.allclose(T[:3,3]-p0[:3,3],z['translation_from_source_mm']*p0[:3,0]))
    protected=[]
    for path,old in load(R/'runtime/protected_start.json').items():
        def git(*args):return subprocess.check_output(['git','-C',path,*args],env={**os.environ,'GIT_OPTIONAL_LOCKS':'0'})
        idx=Path(git('rev-parse','--git-path','index').decode().strip());idx=idx if idx.is_absolute()else Path(path)/idx;record=dict(worktree=path,HEAD_unchanged=git('rev-parse','HEAD').decode().strip()==old['HEAD'],index_unchanged=sha(idx)==old['index_SHA256'],status_unchanged=hashlib.sha256(git('status','--porcelain=v1','-z','-uall')).hexdigest()==old['status_SHA256'],modified_scientific_files_unchanged=all(sha(Path(path)/f)==h for f,h in old['modified_files'].items()));protected.append(record);check(path+'_protected',all(record[k]for k in record if k!='worktree'))
    save('metrics/PROTECTED_WORKSPACES_VERIFIED.json',protected);save('metrics/VALIDATION.json',dict(status='PASS',checks_N=len(rows),checks=rows,GT_used=False,scope='engineering/source/provenance checks; no independent geometry certification'));print('VALIDATION_PASS',len(rows),flush=True)
if __name__=='__main__':main()
