"""Frozen-output comparison, actual-source exports and geometric change audit."""
from growth import *
from matplotlib import cm
def unique_points(blocks):
    record={}
    for b in blocks:
        s=source(b['reference']);P=block_P(b);F=s['F'][b['face_ids']];ids=np.unique(F);generations=np.zeros(len(s['P']),int)
        for j in range(3):np.maximum.at(generations,F[:,j],b['face_generations'])
        for i in ids:
            key=(b['reference'],int(i))
            if key in record:
                assert np.allclose(record[key][0],P[i],atol=1e-7,rtol=0),'same original vertex acquired incompatible derived transforms';record[key][3]=max(record[key][3],int(generations[i]));continue
            record[key]=[P[i],s['C'][i],s['uv'][i],int(generations[i]),np.array(b['H'])]
    keys=list(record);return dict(P=np.array([record[k][0]for k in keys]),C=np.array([record[k][1]for k in keys]),uv=np.array([record[k][2]for k in keys]),generation=np.array([record[k][3]for k in keys]),references=np.array([k[0]for k in keys]),original_ids=np.array([k[1]for k in keys]),point_H=np.array([record[k][4]for k in keys]))
def old_f2_points(sid):
    cc=[c for c in historical_cases()if sceneid(c)==sid];return dict(P=np.concatenate([source(c['id'])['P'][old_F2(c['id'])['accepted']]for c in cc]),C=np.concatenate([source(c['id'])['C'][old_F2(c['id'])['accepted']]for c in cc]))
def f1_points(sid,all_available=True):
    cc=[c for c in (cases()if all_available else historical_cases())if sceneid(c)==sid];return dict(P=np.concatenate([source(c['id'])['P'][~cleaned(c['id'])['clean_removed']]for c in cc]),C=np.concatenate([source(c['id'])['C'][~cleaned(c['id'])['clean_removed']]for c in cc]))
def f1_blocks(sid,all_available=True):
    cc=[c for c in (cases()if all_available else historical_cases())if sceneid(c)==sid];return [dict(id=c['id'],reference=c['id'],face_ids=clean_faces(c['id']),H=np.eye(4),face_generations=np.zeros(len(clean_faces(c['id'])),int),role='CLEANED_F1_UNSELECTED_CONTROL',original_component=-1)for c in cc]
def target_rows(sid):
    primary=load(R/'provenance/MAIN_SURFACES_SELECTED.json')['selections'][sid]
    for row in load(R/'provenance/EVALUATION_TARGETS_FROZEN.json')['targets']:
        if row['scene']==sid:yield dict(row['view'],ring_case=primary,id=row['target'],role=row['role'])
def no_joint(blocks):return [dict(b,H=np.eye(4))for b in blocks]
def component_growth_summary(blocks):
    refs=set(b['reference']for b in blocks);rows=[]
    for cid in refs:
        ids=np.array(sorted({int(f)for b in blocks if b['reference']==cid for f,g in zip(b['face_ids'],b['face_generations'])if g>0}),int);parts=face_partitions(cid,ids);areas=[float(source(cid)['areas'][p].sum())for p in parts];rows.append(dict(reference=cid,new_original_faces=len(ids),new_complete_source_area_mm2=float(source(cid)['areas'][ids].sum()),new_face_components=len(parts),largest_new_complete_source_component_mm2=max(areas)if areas else 0.))
    return rows
def export(sid,blocks,version):
    folder=R/'local_results/glb';folder.mkdir(exist_ok=True);a=unique_points(blocks);primary=blocks[0]['reference'];back=background(primary);models=[];npz=folder/(sid+'_'+version+'_sources.npz');np.savez_compressed(npz,XYZ_derived_mm=a['P'],RGB=a['C'],source_reference=a['references'],original_point_id=a['original_ids'],source_uv=a['uv'],generation=a['generation'],H_original_to_derived=a['point_H'],raw_XYZ_unchanged=True,unit='mm')
    for style in ['F3A_original_triangle_geometry','F3B_RGB_pointcloud']:
        sc=trimesh.Scene()
        if style.startswith('F3B'):
            for cid in sorted(set(a['references'])):
                ix=a['references']==cid;s=source(cid);g=trimesh.points.PointCloud(a['P'][ix]/1000,colors=np.rint(a['C'][ix]*255).astype(np.uint8));fids=np.array(sorted({int(f)for b in blocks if b['reference']==cid for f in b['face_ids']}),int);g.metadata.update(source_reference=cid,source_original_vertex_ids=a['original_ids'][ix].tolist(),source_uv=a['uv'][ix].tolist(),source_original_face_ids=fids.tolist(),source_original_faces=s['F'][fids].tolist(),point_H_source_to_scene=a['point_H'][ix].tolist(),point_generation=a['generation'][ix].tolist(),original_mesh=s['c']['mesh'],coordinate_frame=sid+'_LOCAL_RING_MM',raw_source_unit='mm',glb_unit='m',same_source_point_deduplicated_by_original_id=True);sc.add_geometry(g,node_name=cid+'_UNIQUE_SOURCE_RGB_POINTS')
        for j,b in enumerate(blocks):
            if style.startswith('F3B'):continue
            s=source(b['reference']);F=s['F'][b['face_ids']];ids,inverse=np.unique(F,return_inverse=True);P=block_P(b)[ids]/1000;colors=np.rint(s['C'][ids]*255).astype(np.uint8)
            if style.startswith('F3A'):
                g=trimesh.Trimesh(vertices=P,faces=inverse.reshape(-1,3),process=False);gen=np.array(b['face_generations']);last=max(1,max(int(np.max(x['face_generations']))for x in blocks));color=cm.turbo(gen/(last+1));color[gen==0]=[.94,.29,.55,1.]if b['role'].startswith('PRIMARY')else[.15,.65,.93,1.];g.visual.face_colors=np.rint(color*255).astype(np.uint8)
            else:g=trimesh.points.PointCloud(P,colors=colors)
            g.metadata.update(source_reference=b['reference'],source_original_vertex_ids=ids.tolist(),source_uv=s['uv'][ids].tolist(),source_original_face_ids=np.array(b['face_ids']).tolist(),source_original_faces=s['F'][b['face_ids']].tolist(),face_generation=np.array(b['face_generations']).tolist(),H_source_to_scene=np.asarray(b['H']).tolist(),original_mesh=s['c']['mesh'],coordinate_frame=sid+'_LOCAL_RING_MM',raw_source_unit='mm',glb_unit='m',role=b['role']);sc.add_geometry(g,node_name=b['id'])
        g=trimesh.points.PointCloud(back['P']/1000,colors=np.rint(back['C']*255).astype(np.uint8));g.metadata.update(kind='ACTUAL_BACKGROUND_XYZ_DISPLAY_ONLY',source_reference=primary,source_uv=back['uv'].tolist());sc.add_geometry(g,node_name='Background_ACTUAL_XYZ_DISPLAY_ONLY');ring=source(primary)['ring'].copy();ring.vertices=np.asarray(ring.vertices)/1000;ring.visual=trimesh.visual.TextureVisuals(material=trimesh.visual.material.PBRMaterial(baseColorFactor=[0,0,0,255],metallicFactor=0,roughnessFactor=.8,doubleSided=True));sc.add_geometry(ring,node_name='Ring_FIXED_BLACK_CAD');sc.metadata.update(task=R.name,scene=sid,version=version,original_inputs_preserved=True,GT_used=False,scientific_status='ENGINEERING_CANDIDATE_NOT_ABSOLUTE_ACCURACY',condition=case(primary)['condition'])
        def extras(tree):
            for m in tree['meshes']:
                if m['name']in sc.geometry:m.setdefault('extras',{}).update(clean(sc.geometry[m['name']].metadata))
        path=folder/(sid+'_'+version+'_'+style+'.glb');sc.export(path,tree_postprocessor=extras);models.append(dict(scene=sid,version=version,style=style,path=str(path),bytes=path.stat().st_size,sha256=sha(path),source_npz=str(npz),public_uploaded=False))
    return models
def overlap_diagnostic(blocks):
    rows=[]
    for cid in sorted(set(b['reference']for b in blocks)):
        own=[b for b in blocks if b['reference']==cid];other=[b for b in blocks if b['reference']!=cid]
        if not other:continue
        array=mesh_arrays(other);t=target_source(cid);ray=raymesh(array['P'],array['F'],t);A=[];D=[];over=[]
        for b in own:
            s=source(cid);centers=block_P(b)[s['F'][b['face_ids']]].mean(1);uv,z=vis.project_camera(centers,t['K'],t['c2w']);xy=np.floor(uv+.5).astype(int);valid=(z>0)&(xy[:,0]>=0)&(xy[:,0]<640)&(xy[:,1]>=0)&(xy[:,1]<360);ix=np.flatnonzero(valid);x,y=xy[ix].T;hit=ray['valid'][y,x];ix=ix[hit];x,y=xy[ix].T;d=z[ix]-ray['z'][y,x];A.extend(s['areas'][np.array(b['face_ids'])[ix]].tolist());D.extend(d.tolist());over.extend(depth_tau(z[ix],t['K']).tolist())
        area=np.array(A);delta=np.array(D);tol=np.array(over);rows.append(dict(reference=cid,co_projected_original_face_area_exposure_mm2=float(area.sum()),close_layer_exposure_mm2=float(area[abs(delta)<=tol].sum()),inconsistent_layer_exposure_mm2=float(area[abs(delta)>tol].sum()),axial_difference_mm=stats(delta),not_unique_physical_area=True,denominator='source face centers with an actual other-source triangle ray hit; area exposures may count both directions'))
    return rows
def main(selected_scenes=None):
    # Immutable process-local source registry permits an independent finished
    # scene to be evaluated while a different scene appends new references.
    import common as shared
    frozen_cases=shared.cases();shared.cases=lambda:frozen_cases;globals()['cases']=lambda:frozen_cases
    manifests=sorted((R/'provenance').glob('PREDICTIONS_EVAL_FREEZE_*.json'));seq=str(len(manifests)+1).zfill(3);registry=R/f'provenance/EVALUATION_CASE_REGISTRY_{seq}.json';save(str(registry.relative_to(R)),frozen_cases);save('provenance/PREDICTIONS_EVAL_FREEZE_'+seq+'.json',stamp(list((R/'local_results/scenes').glob('*Final.json'))+list((R/'local_results/scenes').glob('*S[0-9][0-9][0-9].json'))+[Path(__file__),R/'config/growth_rules.json',registry],GT_used=False,before_any_independent_target_RGB_error_in_this_call=True,all_parameters_and_geometry_preselected=True,selected_scenes=selected_scenes))
    rows=[];steps=[];summary=[];motion=[];models=[];overlaps=[];lineage=[]
    for sid in load(R/'provenance/MAIN_SURFACES_SELECTED.json')['selections']:
        if selected_scenes and sid not in selected_scenes:continue
        path=R/f'local_results/scenes/{sid}_Final.json'
        if not path.exists():continue
        final=load(path);b=final['blocks'];start=load_scene(sid,0);joint=unique_points(b);pre=unique_points(no_joint(b));s0=unique_points(start);mainblocks=[x for x in start if x['role'].startswith('PRIMARY')];primary=unique_points(mainblocks);methods={'Selected_Main':primary,'Initial_S0':s0,'Historical_Cleaned_F1':f1_points(sid,False),'Historical_F2':old_f2_points(sid),'AllAvailable_Cleaned_F1':f1_points(sid,True),'F3_PreJoint_SameFaces':pre,'F3_Joint':joint};models+=export(sid,b,'Joint');models+=export(sid,no_joint(b),'PreJoint_same_faces');models+=export(sid,start,'Initial_S0')
        for t in target_rows(sid):
            preds={method:projection(a['P'],a['C'],t)for method,a in methods.items()};base=preds['Initial_S0'];B=np.asarray(Image.open(t['RGB']).convert('RGB'));mask=cv2.imread(t['Mask'],0)==1;folder=R/'local_results/evaluation'/sid/t['id'];folder.mkdir(parents=True,exist_ok=True)
            for method,p in preds.items():
                m=metric(p,t);new=(p['layer']==1)&mask&(base['layer']!=1);lost=(base['layer']==1)&mask&(p['layer']!=1);generation=methods[method].get('generation');new_source=np.zeros(mask.shape,bool)
                if generation is not None:
                    valid=(p['layer']==1)&(p['source_id']>=0);new_source[valid]=generation[p['source_id'][valid]]>0
                rows.append(dict(scene=sid,group=sid[:3],condition=case(b[0]['reference'])['condition'],method=method,target=t['id'],role=t['role'],**m,common_with_S0=common_metric(base,p,t),new_target_pixel_N=int(new.sum()),lost_S0_target_pixel_N=int(lost.sum()),new_coverage=float(new.sum()/mask.sum()),lost_old_coverage=float(lost.sum()/mask.sum()),new_region_RGB=stats(abs(p['RGBA'][:,:,:3].astype(float)-B).mean(2)[new]),visible_new_generation_in_target_N=int((new_source&mask).sum())if generation is not None else None,new_generation_outside_S0_target_N=int((new_source&new).sum())if generation is not None else None,moved_old_geometry_only_new_coverage_N=int((new&~new_source).sum())if generation is not None else None));np.savez_compressed(folder/(method+'.npz'),**p)
            snapshots=sorted((R/'local_results/scenes').glob(sid+'_S[0-9][0-9][0-9].json'));previous=base
            for snap in snapshots[1:]:
                q=load(snap);a=unique_points(q['blocks']);p=projection(a['P'],a['C'],t);m=metric(p,t);prev=metric(previous,t);steps.append(dict(scene=sid,step=q['step'],target=t['id'],delta_C=m['coverage']-prev['coverage'],delta_covered_pixels=m['covered_N']-prev['covered_N'],target_Polyp_N=m['target_Polyp_N'],coverage=m['coverage'],common_previous=common_metric(previous,p,t),physical_accuracy='NOT_EVALUABLE_NO_GT'));previous=p
        initial_lookup={(ref,int(i)):P for ref,i,P in zip(s0['references'],s0['original_ids'],s0['P'])};final_lookup={(ref,int(i)):P for ref,i,P in zip(joint['references'],joint['original_ids'],joint['P'])};change=[]
        for key,P in initial_lookup.items():
            if key in final_lookup:change.append(float(np.linalg.norm(final_lookup[key]-P)))
        for block in b:
            H=np.array(block['H']);motion.append(dict(scene=sid,block=block['id'],reference=block['reference'],role=block['role'],H=H,translation_parameter_mm=float(np.linalg.norm(H[:3,3])),rotation_deg=rotangle(H),rigid_scale_singular_values=np.linalg.svd(H[:3,:3])[1],original_face_count=len(block['face_ids']),cumulative_motion_is_derived_only=True))
        contrib=component_growth_summary(b);both('source_surface_growth_'+sid,contrib)
        for version,bb in [('Initial_S0',start),('F3_PreJoint_SameFaces',no_joint(b)),('F3_Joint',b)]:
            for x in overlap_diagnostic(bb):overlaps.append(dict(scene=sid,version=version,**x))
        grows=load(R/f'metrics/growth_steps_{sid}.json');summary.append(dict(scene=sid,group=sid[:3],condition=case(b[0]['reference'])['condition'],accepted_steps=final['accepted_steps'],new_HERO_attempts=final['new_HERO_attempts'],initial_complete_face_area_mm2=float(sum(source(x['reference'])['areas'][x['face_ids']].sum()for x in start)),new_complete_original_face_area_mm2=float(sum(x['new_complete_source_area_mm2']for x in contrib)),largest_new_complete_source_component_mm2=max(x['largest_new_complete_source_component_mm2']for x in contrib),initial_unique_face_point_N=len(s0['P']),final_unique_face_point_N=len(joint['P']),old_initial_point_ids_retained_N=len(change),old_initial_point_id_denominator=len(initial_lookup),old_geometry_movement_mm=stats(change),accepted_joint_steps=sum(x['joint_alignment'].get('accepted',False)for x in grows),initial_boundary_length_mm=frontier(start)['total_length_mm'],final_boundary_length_mm=frontier(b)['total_length_mm'],stop_reason=final['stop_reason'],true_anatomical_area='NOT_CERTIFIED',GT_used=False))
        # Post-output lineage audit: did newly accepted blocks become anchors?
        for row in grows:
            j=row['joint_alignment'];parent=j.get('dominant_old_block','UNKNOWN');lineage.append(dict(scene=sid,step=row['round'],new_reference=row['reference'],overlap_parent_block=parent,parent_is_prior_growth=parent.startswith('growth_'),parent_is_engineering_seed=parent.startswith('seed_'),lineage_identity='actual anchor-parent record, not invented camera geometry',delta_area_mm2=row['delta_area_mm2']))
        print('EVALUATED',sid,'new area',summary[-1]['new_complete_original_face_area_mm2'],'old movement p95',summary[-1]['old_geometry_movement_mm']['p95'],flush=True)
    both('crossframe_comparison',rows);both('per_round_crossframe_gain',steps);both('growth_summary',summary);both('component_motion',motion);both('GLB_INDEX',models);both('overlap_layer_diagnostic',overlaps);both('growth_lineage',lineage);print('Independent diagnostic comparison complete',flush=True)
if __name__=='__main__':main(sys.argv[1:]or None)
