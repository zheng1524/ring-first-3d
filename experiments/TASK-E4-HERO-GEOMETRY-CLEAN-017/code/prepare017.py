from common017 import *
def main():
    assert not(R/'provenance/PREANALYSIS_FREEZE.json').exists()
    ep=Path('/home/liu/ring_first_3d_neural_e1/experiments/TASK-NEURAL-E1-PIPELINE-RECOVERY-001/provenance/INPUT_ELIGIBILITY.json')
    refs=load(ep)['references'];rows=[];files={ep};reuse=[LEG/'ring_first_v1/scripts/common.py',PHC/'TASK-PHASEC-SPARSE-STRETCH-CLEAN-VIS-001/code/run.py',PHC/'TASK-PHASEC-DENSITY-MULTIGROUP-001/code/density.py',REPO/'experiments/TASK-E3-B-LOCAL-HERO-FIELDS-001/code/mesh_local_field.py',REPO/'experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/code/figures.py']
    for c in refs:
        if c['scene_id']not in ['G01_004','G06_004']:continue
        pack=np.load(c['pack'])
        row=dict(source_id=c['id'],group=c['group'],video='004',native_depth=c['E1_actual_native']['path'],RGB=c['RGB'],Mask=c['Mask'],archive_pack=c['pack'],archive_mesh=c['mesh'],archive_points=c['source_points'],camera_metadata=c['camera_file'],ring=c['Ring_CAD']['path'],K=pack['K'],T=pack['pose'],qualification=c.get('pose_status'),upstream_RGB=c['HERO_input_views'],original_geometry_kind='single-reference unmodified archived Raw; not fusion')
        rows.append(row)
    for g in ['G03','G05']:
        root=LEG/'multigroup_ring_hero_visual_audit_v1/groups'/g;c=load(RUN009/'inputs'/g/'CASE.json');v=next(v for v in c['views']if v.get('HERO_source'));a=np.load(RUN009/'inputs'/g/(v['id']+'.npz'))
        rows.append(dict(source_id=v['id'],group=g,video='004',native_depth=v['HERO_source'],RGB=v['RGB_source'],Mask=v['Mask_source'],archive_pack=str(root/'predictions/004_gallery_surface.npz'),archive_mesh=str(root/'meshes/004/Polyp_raw_open.ply'),camera_metadata=str(root/'predictions/local005_camera_0.npz'),K=a['K'],T=a['T'],qualification=v['qualification'],original_geometry_kind='single-reference unmodified archived Raw; not fusion'))
    assert len(rows)==18 and len({r['source_id']for r in rows})==18
    for r in rows:
        for key in ['native_depth','RGB','Mask','archive_pack','archive_mesh','archive_points','camera_metadata','ring']:
            if key in r:assert Path(r[key]).is_file(),r[key];files.add(Path(r[key]))
        if 'ring'not in r:r['ring']=str(LEG/'surface_fusion_v2/inputs/R10_ring.obj');files.add(Path(r['ring']))
        for p in r.get('upstream_RGB',[]):files.add(Path(p['RGB']))
        z=np.load(r['native_depth']);D=z['depth_mm'];K=np.array(r['K']);S=np.diag([D.shape[1]/640,D.shape[0]/360,1.]);S[:2,2]=np.array([D.shape[1]/640,D.shape[0]/360])*.5-.5;Kn=S@K;r['Kn']=Kn;r['native_shape']=D.shape
        key=next((k for k in ['K_index_native','K_index']if k in z),None)
        if key:assert np.allclose(z[key],Kn,atol=1e-8)
        T=z['pose']if'pose'in z else z['reference_pose_mm'];assert np.allclose(T,r['T'],atol=1e-8)
        lab=np.array(Image.open(r['Mask']));p=np.load(r['archive_pack']);assert np.array_equal(lab,p['labels']);assert np.allclose(p['K'],K)and np.allclose(p['pose'],T)
        r['family_note']='shared HERO upstream RGB is correlated; no multi-view vote or selection'
    conf=dict(seed=20261110,groups=['G01','G03','G05','G06'],source_counts={g:sum(r['group']==g for r in rows)for g in ['G01','G03','G05','G06']},representations=['ARCHIVE_RAW','NATIVE_GRID'],inherited_density=load(PHC/'TASK-PHASEC-DENSITY-MULTIGROUP-001/config.json'),
        thresholds=dict(stretch_perspective=8.,stretch_tangent=4.,native_depth_jump_mm=.5,normal_coherence=.7,neighbor_angle_deg=65.,needle_quality=.15,edge_native_px=2.,incidence_min=.2,ring_near_mm=.3,ring_inside_mm=.02,ring_inside_samples_min=2,competition_mm=.02,competition_k=32,density_warning=.25,small_component_area_fraction=.001),
        rule='REJECT only (severe perspective AND reliable tangent stretch AND native depth jump AND needle/normal kink AND near original Mask edge AND non-grazing) OR (sampled CAD material penetration AND native depth jump AND needle/normal kink AND non-grazing); invalid/native-unbound/occluded/grazing is UNKNOWN and retained. All other anomalies UNCERTAIN retained.',
        independence='stretch/needle/area/density and depth jump/normal are correlated consequences of the same depth surface; not independent votes. Source-edge context and CAD are separate support; labels are uncalibrated artifact evidence, not truth.',
        all_groups_same_rule=True,threshold_search=0,GT=False,multiview_loss=False,multiview_deletion=False,vertex_update=False,interpolation=False,hole_filling=False,
        native_grid_definition='unfiltered two-triangle pixel lattice [a,b,c],[b,d,c], only all vertices finite positive native depth and nearest original Mask Polyp. No max-depth-jump prefilter. Stable lattice ID=2*(v*(W-1)+u)+side; created index topology, not original archive face identity.',
        archive_definition='exact existing single-reference vertex/face arrays, original face IDs unchanged; archive often historical bilinear depth 352->360. Output subsets preserve all input vertex values.',
        boundary_definition='EDT distance between foreground sample centre and closest background sample centre, padded background at image border; no half-pixel subtraction; mask mapped to native with frozen K, nearest pixel centre floor(u+.5).',
        nearest_competition='32 face-centroid candidates, exact point-to-triangle distance, exclude all vertex-sharing faces. Incomplete screen; UNCERTAIN only.',
        CAD_sampling='vertices, 3 edge midpoints, centroid, signed distance nsamples=3; watertight winding-consistent CAD required. Finite samples do not certify absence of intersection.',
        safeguards='No automatic threshold relaxation or additional deletion round. Any continuity/coverage loss is reported, not hidden. All retained vertices unchanged, only face subset. No anatomy labels/true-error GT.')
    save('config/PROTOCOL.json',conf);save('config/SOURCE_LOCK.json',rows)
    (R/'01_PROTOCOL.md').write_text('# 017 frozen protocol\n\n18 native HERO sources in four physical groups; G01 11, G03 1, G05 1, G06 5. Video004 only. No old Gate exclusion, no new HERO.\n\n'+json.dumps(clean(conf),ensure_ascii=False,indent=2)+'\n')
    files.update(reuse);files.update((R/'code').glob('*.py'));files.update((R/'config').glob('*.json'));files.add(R/'01_PROTOCOL.md')
    protected=[asset(p)for task in ['TASK-E4-UPDATE-CAUSALITY-016','TASK-E4-MULTIVIEW-INIT-STALK-015']for p in sorted((REPO/'experiments'/task).rglob('*'))if p.is_file()and not any(t in p.parts for t in ['runtime','__pycache__','.git']) and not any(t in str(p.resolve()).lower()for t in ['/gt_mapping/','/evaluation_only/','/audit_only/','oracle','.blend','native_cad_gt','/private_gt/'])]
    save('provenance/PREANALYSIS_FREEZE.json',dict(epoch=time.time(),files=[asset(p)for p in sorted(files)],protected_history=protected,GT_opened=False,rule_frozen_before_geometry_statistics=True))
    print('FROZEN',len(rows),'sources;',len(files),'input/code files;',len(protected),'history files',flush=True)
if __name__=='__main__':main()
