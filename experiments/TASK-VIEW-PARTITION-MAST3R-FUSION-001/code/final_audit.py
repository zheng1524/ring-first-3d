"""Final source/support audit. Does not generate or select prediction geometry."""
from evaluate_d import *
def support_identity():
    rows=[]
    for sid in scene_ids():
        cc=[c for c in cases()if sceneid(c)==sid]
        for t in eval_targets(sid):
            h=sha(t['RGB']);same=[c['id']for c in cc if sha(c['RGB'])==h]
            rows.append(dict(scene=sid,target=t['id'],original_pre_frozen_role=t['role'],same_RGB_as_geometry_reference=same,target_RGB_sha256=h,independent_of_all_reference_images=not bool(same),support_status='SELF_VIEW_OR_EXISTING_GEOMETRY_SOURCE_NOT_INDEPENDENT'if same else'NO_FROZEN_HOLDOUT_DIAGNOSTIC_ONLY'if 'NO_FROZEN_HELD'in t['role']else'NEW_HERO_HELD_FRAME_NOT_WHOLE_PIPELINE_BLIND',normal_or_stress=case(cc[0]['id'])['condition']))
    both('evaluation_support_identity',rows)
    # Attach support identity without altering any numerical score or old role.
    lookup={(r['scene'],r['target']):r for r in rows}
    for name in ['scene_evaluation','new_HERO_marginal_validation']:
        data=load(R/f'metrics/{name}.json')
        for row in data:
            row['support_identity']=lookup[(row['scene'],row['target'])]['support_status'];row['independent_of_all_reference_images']=lookup[(row['scene'],row['target'])]['independent_of_all_reference_images']
        both(name,data)
    out=[]
    evaluations=load(R/'metrics/scene_evaluation.json');marginal=load(R/'metrics/new_HERO_marginal_validation.json')
    for sid in scene_ids():
        eligible=[r['target']for r in rows if r['scene']==sid and r['independent_of_all_reference_images']and'NO_FROZEN'not in r['support_status']]
        for pool,tt in [('ALL_PRE_FROZEN_DIAGNOSTICS',[r['target']for r in rows if r['scene']==sid]),('NON_SELF_PRE_FROZEN_HELD',eligible)]:
            for mode in list(dict.fromkeys(r['method']for r in evaluations if r['scene']==sid)):
                rr=[r for r in evaluations if r['scene']==sid and r['method']==mode and r['target']in tt];common=[r['common_with_single']for r in rr]
                out.append(dict(scene=sid,pool=pool,method=mode,target_frames=len(rr),condition=case(pointset(sid,'Single_Cleaned')['references'][0])['condition'],target_Polyp_pixel_exposures=sum(r['target_Polyp_N']for r in rr),covered_pixel_exposures=sum(r['covered_N']for r in rr),mean_frame_coverage=float(np.mean([r['coverage']for r in rr]))if rr else None,mean_frame_RGB_MAE=float(np.mean([r['RGB']['MAE']for r in rr]))if rr else None,common_support_pixel_exposures=sum(r['common_N']for r in common),mean_frame_common_single_MAE=float(np.mean([r['baseline']['MAE']for r in common]))if rr else None,mean_frame_common_method_MAE=float(np.mean([r['candidate']['MAE']for r in common]))if rr else None,physical_group=sid[:3],true_3D_accuracy='NOT_EVALUABLE_NO_GT'))
    both('evaluation_summary',out)
    return rows

def main():
    checks=[]
    def check(name,ok):
        checks.append(dict(check=name,passed=bool(ok)))
        assert ok,name
    verify();check('Original input SHA manifest unchanged',True)
    for model in load(R/'provenance/MODEL_WEIGHTS.json'):check(model['model']+' original weight SHA unchanged',sha(model['path'])==model['sha256'])
    for manifest in ['NEW_HERO_OUTPUTS_FROZEN','F2_GEOMETRY_FROZEN','P8_RULES_AND_SOURCE_FROZEN']:
        records=load(R/f'provenance/{manifest}.json')['files']
        for r in records:check(manifest+':'+str(Path(r['path']).relative_to(R)),sha(r['path'])==r['sha256'])
    check('Exactly four independent physical groups',len(set(c['group']for c in cases()))==4)
    check('Exactly nine historical plus five new sources',len(cases())==14 and sum(c.get('new_reference',False)for c in cases())==5)
    for c in cases():
        s=source(c['id']);z=np.load(R/f'local_results/cleaned/{c["id"]}.npz');uv,depth=vis.project_camera(s['P'],s['p']['K'],s['p']['pose'])
        check(c['id']+' pinhole UV identity',np.max(abs(uv-s['uv']))<1e-7)
        check(c['id']+' depth identity',np.max(abs(depth-s['p']['depth_mm'][s['uv'][:,1],s['uv'][:,0]]))<1e-7)
        check(c['id']+' exact source RGB',np.array_equal(np.rint(s['C']*255).astype(np.uint8),s['frame'][s['uv'][:,1],s['uv'][:,0]]))
        check(c['id']+' clean unchanged source XYZ',np.array_equal(z['XYZ_mm'],s['P']))
        check(c['id']+' protected possible stalk kept',not(z['clean_removed']&z['protected_possible_stalk']).any())
    for sid in scene_ids():
        for mode in ['Raw_F2','ViewPartition_Cleaned_F2']:
            a=pointset(sid,mode)
            for j,cid in enumerate(a['references']):
                ids=a['original_ids'][a['reference_index']==j];s=source(cid);z=np.load(R/f'local_results/pointcloud_blocks/{sid}/{mode}/{cid}.npz')
                check(mode+cid+' exact original-index XYZ/RGB',np.array_equal(a['P'][a['reference_index']==j],s['P'][ids])and np.array_equal(a['C'][a['reference_index']==j],s['C'][ids]))
                check(mode+cid+' only original faces',np.array_equal(z['original_faces'],s['F']))
                check(mode+cid+' no postbackprojection motion',np.array_equal(z['H_after_backprojection'],np.eye(4)))
                if j==0:check(mode+cid+' primary all kept',np.array_equal(z['accepted'],~z['clean_removed']))
                else:check(mode+cid+' only supported connected novel accepted',not(z['accepted']&((z['class_id']!=NOVEL)|~z['neighbor_image_support'])).any())
    edges=load(R/'metrics/registration_edges.json');graph=load(R/'metrics/pose_graph_status.json');check('Only two conditional verified graph edges',sum(e['status']=='VERIFIED_ADJACENT_CONSTRAINT'for e in edges)==2)
    check('Photos never became metric XYZ',not any('photo'in c['id'].lower()for c in cases()))
    check('G07 remains stress, not certified',all(not c['source_camera_qualified']for c in cases()if c['group']=='G07'))
    gate=load(R/'metrics/CROSSVIDEO_GATE.json');check('Cross gate explicitly NOT FUSED',not gate['fusion_certified']and gate['pointcloud_joint_only'])
    # A renderer cannot read B RGB/Mask: these fake paths must be harmless.
    s=source('G01_004_ref08');t=target_source('G01_004_ref08');t.update(RGB='/nonexistent/targetRGB',Mask='/nonexistent/targetMask');pred=projection(s['P'][:100],s['C'][:100],t);check('Projection independent of B RGB/Mask files',pred['RGBA'].shape==(360,640,4))
    glbs=load(R/'metrics/GLB_INDEX.json')
    for row in glbs:
        path=Path(row['path']);check(path.name+' persisted exact SHA',path.is_file()and sha(path)==row['sha256'])
        if row['method']=='ViewPartition_Cleaned_F2':
            loaded=trimesh.load(path,force='scene');geom=[g for g in loaded.geometry.values()if isinstance(g,trimesh.points.PointCloud)and g.metadata.get('source_reference')in pointset(row['scene'],'ViewPartition_Cleaned_F2')['references']and g.metadata.get('kind')!='ACTUAL_BACKGROUND_XYZ_DISPLAY_ONLY'];check(path.name+' true point primitives/source IDs',sum(len(g.vertices)for g in geom)==row['points'])
    identities=support_identity()
    start=load(R/'runtime/PROTECTED_START.json');end={p:state(Path(p))for p in start};save('runtime/PROTECTED_END.json',end)
    for p in start:check('Protected workspace unchanged: '+p,start[p]==end[p])
    inputs=[Path(f['path'])for f in load(R/'provenance/INPUTS_FROZEN.json')['files']]
    for c in cases():
        inputs +=[Path(c[k])for k in ['RGB','Mask','pack','mesh','camera_file','source_points']]
        if not c.get('new_reference'):inputs.append(INC/f'local_results/background/{c["id"]}.npz')
    inputs +=list((R/'code').glob('*.py'))+list((R/'config').glob('*.json'))
    save('provenance/FINAL_CODE_AND_SOURCE_MANIFEST.json',stamp(inputs,GT_used=False,read_only_external_sources=True))
    local=[]
    for p in sorted((R/'local_results').rglob('*')):
        if p.is_file():local.append(dict(path=str(p),relative=str(p.relative_to(R)),bytes=p.stat().st_size,sha256=sha(p),public_uploaded=False))
    save('provenance/OUTPUT_INDEX.json',dict(files=local,large_assets_local_only=True,GT_used=False))
    save('provenance/FINAL_REVIEW.json',dict(status='COMPLETE_EXPERIMENTAL_NOT_SCIENTIFICALLY_CERTIFIED',cross_video='NOT_FUSED',reference_count=14,new_HERO_count=5,MASt3R_new_forwards=18,protected_workspaces_unchanged=len(start),source_support_qualification=identities,GT_used=False,stop_after_task=True))
    both('final_validation_checks',checks);print('FINAL CHECKS',len(checks),'PASS; output files',len(local),'protected workspaces',len(start),flush=True)
if __name__=='__main__':main()
