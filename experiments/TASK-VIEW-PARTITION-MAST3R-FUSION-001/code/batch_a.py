"""Cleaned inputs and real centre-based directions; frozen block identities."""
from geometry import *
from scipy.cluster.hierarchy import linkage,fcluster
from scipy.spatial.distance import squareform
def clean_source(cid,P=None,F=None,uv=None,pack=None):
    if P is None:s=source(cid);P,F,uv,pack=s['P'],s['F'],s['uv'],s['p'];rho=s['a']['rho_surface_radius'];c=s['c']
    else:
        rho=(cKDTree(P).query_ball_point(P,cfg()['density_radius_mm'],return_length=True,workers=1)-1)/(np.pi*cfg()['density_radius_mm']**2);c=case(cid)if any(x['id']==cid for x in cases())else dict(group=cid[:3],video=cid.split('_')[1])
    threshold=cfg()['historical_T2_G01'][c['video']]if c['group']=='G01'else cfg()['other_groups_T2_experimental_transfer'];t2=rho<threshold;_,component,head=source_components(pack,uv);minor=component!=head;cut=np.quantile(uv[minor,1],.8)if minor.any()else np.inf;stalk=minor&(uv[:,1]>=cut);dr=cv2.distanceTransform((pack['labels']!=2).astype(np.uint8),cv2.DIST_L2,5)[uv[:,1],uv[:,0]];protected=stalk|(dr<=3);removed=t2&~protected
    # Protect original components without throwing any component away.
    comp=face_components(F);restored=np.zeros(len(P),bool)
    for k in np.unique(comp):
        ids=np.unique(F[comp==k])
        if removed[ids].all():restored[ids]=True
    removed&=~restored;faces=F[~removed[F].any(1)];ids=np.flatnonzero(~removed);folder=R/'local_results/cleaned';folder.mkdir(parents=True,exist_ok=True);np.savez_compressed(folder/(cid+'.npz'),XYZ_mm=P,source_uv=uv,original_ids=np.arange(len(P)),original_faces=F,rho_radius=rho,historical_T2_deleted=t2,protected_possible_stalk=stalk,protected_Ring=dr<=3,restored_component=restored,clean_removed=removed,kept_original_ids=ids,clean_faces_original_ids=faces,threshold=threshold)
    return dict(reference=cid,group=c['group'],raw_N=len(P),historical_T2_deleted_N=int(t2.sum()),clean_deleted_N=int(removed.sum()),clean_N=len(ids),T_points_per_mm2=threshold,rule_scope='HISTORICAL_G01_T2'if c['group']=='G01'else'EXPERIMENTAL_FIXED_TRANSFER_NO_SEARCH',possible_stalk_proxy_N=int(stalk.sum()),stalk_retained_N=int((stalk&~removed).sum()),Ring_protected_N=int((dr<=3).sum()),restored_entire_component_points=int(restored.sum()),raw_faces=len(F),clean_faces=len(faces),raw_area_proxy_mm2=float(area(P,F).sum()),clean_area_proxy_mm2=float(area(P,faces).sum()),clean_components=len(np.unique(face_components(faces))),new_interior_deleted_patches=interior_deletion_patches(F,removed),status='CLEAN_FOR_FUSION_EXPERIMENTAL_NOT_CERTIFIED',XYZ_changed=False)
def read_views():
    views=load(AUDIT/'metrics/camera_frame_inventory.json')
    for v in views:
        v['id']=v['source_id']+'_'+v['view_id'];v['pose_known']=True;v['type']='video';v['c2w']=np.array(v['c2w']);v['K']=np.array(v['K']);v['condition']=v['camera_condition'];v['camera_candidate_only']=v['pose_status']not in ['VALIDATED','LOCAL_GEOMETRY_SCREENED'];v['existing_refs']=[c['id']for c in cases()if c['group']==v['group']and c['video']==v['source_id'][-3:]and c['reference_index']==v['index']]
    for v in views:
        if v['source_id']=='G01_video005':
            ledger=load(OLD/'ring_first_v6_local_reconstruction/inputs/ledger005.json');entry=ledger[v['index']];v['RGB']=entry['RGB_path'];v['Mask']=entry['Mask_path'];v['frame_binding']='EXACT_V6_LEDGER_ENTRY_BY_CAMERA_INDEX'
        v['available']=Path(v['RGB']).is_file()and Path(v['Mask']).is_file()
    for p in load(OLD/'ring_first_v13_multisource/inputs/views.json'):
        if not p['id'].startswith('photo'):continue
        views.append(dict(id='G01_'+p['id'],group='G01',source_id='G01_'+p['id'],view_id=p['id'],index=None,RGB=p['RGB_path'],Mask=p['Mask_path'],K=p.get('K'),c2w=None,pose_known=False,pose_status='POSE_UNKNOWN_UNREGISTERED',condition='PHOTO_K_UNCERTIFIED',type='photo',existing_refs=[]))
    return views
def main():
    assert not(R/'provenance/INPUTS_FROZEN.json').exists()
    roots=[Path('/home/liu/polyp_research'),Path('/home/liu/new-polyp-dxy')]+[Path('/home/liu')/n for n in ['ring_first_3d','ring_first_3d_scene_vis','ring_first_3d_abs_density','ring_first_3d_phase_d','ring_first_3d_incremental','ring_first_3d_view_eval','ring_first_3d_ab_scene','ring_first_3d_panel2_depth','ring_first_3d_grazing']];save('runtime/PROTECTED_START.json',{str(p):state(p)for p in roots});views=read_views();files=[AUDIT/'metrics/camera_frame_inventory.json',R/'TASK.md',R/'config/rules.json'];cleanrows=[]
    for c in cases():
        source(c['id']);files +=[Path(c[k])for k in ['pack','mesh','source_points','RGB','Mask','camera_file']]+[DENS/f'local_fields/{c["id"]}_fields.npz',ring_path(c)];cleanrows.append(clean_source(c['id']))
    for v in views:files +=[Path(v['RGB']),Path(v['Mask'])]if v.get('available',True)else[]
    # Models already present, no downloads/copies. Verify official frozen SHA.
    weights=[('MASt3R',V9/'weights/MASt3R_official.pth','e28f91b488554653e2b46ddae9c78c1143e0bcb2e27d3e26cdb0b717f1568eb2'),('HERO',F1/'weights/mvsanywhere_hero_full.ckpt','00878bab903b1d384cd6bb9ea092e247a9036d429cb8bcc3d6dcbb81f67e556d')];modelrows=[]
    for name,p,expected in weights:
        h=sha(p);assert h==expected,(name,h);modelrows.append(dict(model=name,path=str(p),bytes=p.stat().st_size,sha256=h,pretrained_read_only=True,training=False));print('WEIGHT VERIFIED',name,flush=True)
    save('provenance/MODEL_WEIGHTS.json',modelrows)
    entries=[('视频读取/取帧',OLD/'ring_first_v12_pose_matching_audit/scripts/match12.py','cv2.VideoCapture / cached ledger','reuse cached frames; no new video decoder'),('图像/Mask',AUDIT/'code/inventory.py','camera_frame_inventory','source SHA and labels unchanged'),('Ring-First读取',GRAZ/'code/common.py','source / target_source','exact frozen K/c2w'),('HERO推理',F1/'scripts/run_mvs_adapter3.py','load_official','AST exact function, path globals rebound only'),('XYZ/开放原面',OLD/'ring_first_v1/scripts/common.py','unproject / depth_mesh','AST exact original mesh function; no second backprojector'),('清理',GRAZ/'code/cleaning.py','original fields / cohorts','T2 + original connectivity and stalk protection; no angle optimization'),('MASt3R',V8/'vendor/mast3r/mast3r/model.py','AsymmetricMASt3R.from_pretrained','official frozen local implementation'),('匹配接口',OLD/'ring_first_v12_pose_matching_audit/scripts/match12.py','loss_of_one_batch / fast_reciprocal_NNs','full-image and explicit ROI adapters'),('A→B',GRAZ/'code/geometry.py','projection / metric / common_metric','exact bounded module reuse'),('XYZ/GLB',REPO/'visualization/real_p0_renderer.py','draw_rgb_points / SameCameraScene','existing style; no new rendering system')]
    audit=[dict(function=a,entry=str(p),functions=fn,reused=True,change=mod,sha256=sha(p))for a,p,fn,mod in entries];files +=[Path(x['entry'])for x in audit]+[REPO/'visualization/same_camera_scene.py',GRAZ/'code/scene_renderer.py'];both('code_reuse_audit',audit);save('provenance/CODE_REUSE_MANIFEST.json',stamp([Path(x['entry'])for x in audit]));(R/'CODE_REUSE_AUDIT.md').write_text('# 本轮实际代码复用\n\n既有权重和核心实现只读；下表均绑定源码SHA。新代码仅组织分区、匹配、派生配准和聚合。\n\n|功能|实际入口 / 函数|复用|最小适配|\n|---|---|---|---|\n'+'\n'.join('|'+x['function']+'|'+x['entry']+' : '+x['functions']+'|是|'+x['change']+'|'for x in audit)+'\n')
    save('provenance/INPUTS_FROZEN.json',stamp(files,base_commit='4b815acf65fa799942ce31efcfc6eff25d6da776',GT_used=False));both('cleaned_input_audit',cleanrows);both('group_case_manifest',cases())
    rows=[];parts=[];edges=[];newrefs=[]
    for sid in dict.fromkeys(v['source_id']for v in views if v['pose_known']and v.get('available',True)):
        vv=[v for v in views if v['source_id']==sid and v.get('available',True)];cc=[c for c in cases()if c['group']==vv[0]['group']and c['video']==sid[-3:]];s=source(cc[0]['id']);cl=np.load(R/f'local_results/cleaned/{cc[0]["id"]}.npz');head=s['uv'][:,1]<=np.quantile(s['uv'][:,1],.6);center=np.median(s['P'][head&~cl['clean_removed']],0)
        for v in vv:
            C=np.asarray(v['c2w'])[:3,3];d=C-center;distance=np.linalg.norm(d);d/=distance;mask=cv2.imread(v['Mask'],0);im=cv2.imread(v['RGB']);v.update(polyp_center_proxy_mm=center,view_direction=d,view_distance_mm=distance,Ring_observation_inclination_deg=angle(d,[0,0,1]),Mask_polyp_N=int((mask==1).sum()),Mask_Ring_N=int((mask==2).sum()),blur_laplacian_var=float(cv2.Laplacian(cv2.cvtColor(im,cv2.COLOR_BGR2GRAY),cv2.CV_64F).var()),glare_fraction=float((im.max(2)>250).mean()));proj=projection(s['P'][~cl['clean_removed']],s['C'][~cl['clean_removed']],dict(id=v['id'],K=v['K'],c2w=v['c2w'],ring_case=s['c']['id']));v['frozen_reference_Mask_overlap']=float(((proj['layer']==1)&(mask==1)).sum()/max(1,(mask==1).sum()))
        dirs=np.array([v['view_direction']for v in vv]);distance=np.degrees(np.arccos(np.clip(dirs@dirs.T,-1,1)));np.fill_diagonal(distance,0);distance=(distance+distance.T)/2;groups=fcluster(linkage(squareform(distance),method='complete'),cfg()['partition_complete_link_degrees'],criterion='distance')if len(vv)>1 else np.ones(len(vv),int)
        for k in sorted(set(groups)):
            ix=np.flatnonzero(groups==k);sub=[vv[i]for i in ix];block=sid+'_B'+str(k);centre=np.mean(dirs[ix],0);centre/=np.linalg.norm(centre);med=min(sub,key=lambda v:angle(v['view_direction'],centre));held=max(sub,key=lambda v:v['index'])if len(sub)>=3 else None
            for v in sub:v['block']=block;v['role']='HOLDOUT'if held is v else'CORE';v['block_direction_difference_deg']=angle(v['view_direction'],centre)
            parts.append(dict(group=vv[0]['group'],source_id=sid,block=block,representative=med['id'],direction=centre,Core_Frames=[v['id']for v in sub if v is not held],Transition_Frames=[],Holdout_Frames=[held['id']]if held else[],existing_P0=[r for v in sub for r in v['existing_refs']],camera_condition=vv[0]['condition'],direction_span_deg=float(distance[np.ix_(ix,ix)].max()),coordinate_frame=vv[0]['coordinate_frame']))
        pp=[p for p in parts if p['source_id']==sid]
        for i,p in enumerate(pp):
            for q in pp[i+1:]:
                degrees=angle(np.array(p['direction']),np.array(q['direction']));p0=next(v for v in vv if v['id']==p['representative']);q0=next(v for v in vv if v['id']==q['representative']);overlap=min(p0['frozen_reference_Mask_overlap'],q0['frozen_reference_Mask_overlap']);adj=degrees<=cfg()['transition_maximum_degrees']and overlap>=cfg()['partition_minimum_source_projection_Mask_overlap'];edges.append(dict(group=p['group'],a=p['block'],b=q['block'],A=p['representative'],B=q['representative'],direction_angle_deg=degrees,overlap_proxy=overlap,status='CANDIDATE'if adj else'FAILED',reason='ANGLE_AND_PROJECTED_MASK_SUPPORT'if adj else'INSUFFICIENT_OVERLAP_OR_ANGULAR_ADJACENCY'))
                if adj:
                    for target,other in [(p,q),(q,p)]:
                        nonheld=[v for v in vv if v['block']==target['block']and v['role']!='HOLDOUT'];v=min(nonheld,key=lambda x:angle(x['view_direction'],np.array(other['direction'])));target['Transition_Frames'].append(v['id']);v['role']='TRANSITION'
        # Explicit maximum one new reference per real video. Farthest angular
        # gap to OLD P0, before matching/image errors, not highest RGB accuracy.
        olddirs=[v['view_direction']for v in vv if v['existing_refs']];available=[v for v in vv if not v['existing_refs']and v['role']!='HOLDOUT'and v['Mask_polyp_N']>200 and v['Mask_Ring_N']>100]
        for v in available:v['angular_gap_to_old_P0_deg']=min(angle(v['view_direction'],d)for d in olddirs)
        ranked=sorted(available,key=lambda v:(v['angular_gap_to_old_P0_deg'],v['blur_laplacian_var']),reverse=True)
        if ranked:
            v=ranked[0];other=[w for w in vv if w['id']!=v['id']and w['role']!='HOLDOUT'];other.sort(key=lambda w:(w['camera_candidate_only'],abs(angle(w['view_direction'],v['view_direction'])-7),-w['frozen_reference_Mask_overlap']));src=other[:3];newrefs.append(dict(group=v['group'],video=sid[-3:],reference_view=v['id'],block=v['block'],reference_index=v['index'],source_views=[x['id']for x in src],source_indices=[x['index']for x in src],angular_gap_to_old_deg=v['angular_gap_to_old_P0_deg'],camera_status=v['pose_status'],condition=v['condition'],status='PLANNED_NEW_HERO_INFERENCE',historical_case=cc[0]['id'],selection='largest gap to archived P0 among non-held actual frames; source selection prioritizes existing camera qualification and moderate baseline'))
        rows+=vv
    rows +=[v for v in views if not v['pose_known']or not v.get('available',True)];both('view_distribution',rows);both('view_partition',parts);both('adjacency_graph',edges);save('provenance/CAMERA_IDENTITY.json',rows);save('provenance/BLOCKS_AND_FRAME_ROLES_FROZEN.json',stamp([R/'metrics/view_distribution.json',R/'metrics/view_partition.json',R/'metrics/adjacency_graph.json'],before_matching_and_reprojection_errors=True));both('new_reference_plan',newrefs)
    print('BATCH A',len(rows),'views',len(parts),'blocks',len(newrefs),'planned fresh HERO refs',flush=True)
if __name__=='__main__':main()
