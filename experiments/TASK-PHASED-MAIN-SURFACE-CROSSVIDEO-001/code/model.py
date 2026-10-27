"""Frozen-source D0: explainable main selection, nonduplicate patches, conflict layers."""
from common import *
from source_rgb_projection import raster,errors,evaluate
from functools import lru_cache
def cfg():return load(R/'config.json')
@lru_cache(None)
def source(cid):
    c=next(c for c in cases()if c['id']==cid);a,p,rgb,m=data(c);P=a['XYZ_mm'];areas=np.linalg.norm(np.cross(P[m.faces[:,1]]-P[m.faces[:,0]],P[m.faces[:,2]]-P[m.faces[:,0]]),axis=1)/2
    return dict(c=c,a=a,p=p,rgb=rgb,m=m,P=P,areas=areas)
def targets():return load(R/'provenance/TARGETS_FROZEN.json')
def target(video,role):return[x for x in targets()if x['video']==video and x['role']==role]
def scene_for(t):return SameCameraScene(ring(cases()[0]),np.array(t['K']),np.array(t['c2w']),(640,360),str(OLD/'surface_fusion_v3/vendor'))
def mesh(P,F):return trimesh.Trimesh(P,F,process=False)
def nearest(P,m):
    sc=scene_for(target('004','selection')[0]);sc.scene=sc.o3d.t.geometry.RaycastingScene(nthreads=2);sc.scene.add_triangles(sc.o3d.core.Tensor(np.asarray(m.vertices,np.float32)),sc.o3d.core.Tensor(np.asarray(m.faces,np.uint32)));out=sc.scene.compute_closest_points(sc.o3d.core.Tensor(np.asarray(P,np.float32)));Q=out['points'].numpy();return np.linalg.norm(np.asarray(P)-Q,axis=1),out['primitive_normals'].numpy()
def point_projection(P,rgb,ids,t,kind=None):
    return raster(P,rgb,np.ones(len(P),int)if kind is None else kind,ids,np.array(t['K']),np.array(t['c2w']),(360,640),scene_for(t))
def point_explanation(s,t):
    pred=point_projection(s['P'],s['rgb'],np.arange(len(s['P'])),t);B=np.asarray(Image.open(t['RGB']).convert('RGB'));mask=cv2.imread(t['Mask'],0);valid=(pred['kind']==1)&(mask==1);err=np.abs(pred['RGBA'][:,:,:3].astype(float)-B).mean(2);ids=pred['source_original_id'];supported=np.zeros(len(s['P']),bool);supported[ids[valid&(err<=cfg()['source_rgb_support_MAE_maximum'])]]=True;N=int((mask==1).sum());return dict(target=t['id'],target_N=N,covered=int(valid.sum()),coverage=float(valid.sum()/N),RGB=errors(pred,B,valid),meaning='held-selection-view source RGB/Mask consistency, not true geometry'),supported
@lru_cache(None)
def background(cid):
    s=source(cid);p=s['p'];lab=p['labels'];rgb=np.asarray(Image.open(s['c']['RGB']).convert('RGB'));v,u=np.nonzero((lab==0)&np.isfinite(p['depth_mm'])&(p['depth_mm']>0));P=unproject(np.c_[u,v],p['depth_mm'][v,u],p['K'],p['pose']);a=s['a'];uv=np.c_[a['source_u'],a['source_v']];base=uv[:,1]>=np.quantile(uv[:,1],.8);center=np.median(uv[base],0);pv,pu=np.nonzero(lab==1);rv,ru=np.nonzero(lab==2);radius=max(np.ptp(pu)/2,np.ptp(ru)/2);q=cfg();ellipse=lambda k:((u-center[0])/(k*radius))**2+((v-center[1])/(q['background_ellipse_y_over_x']*k*radius))**2<=1
    mask=np.zeros(lab.shape,np.uint8);mask[uv[base,1],uv[base,0]]=1;contact=cv2.distanceTransform(1-mask,cv2.DIST_L2,5)[v,u]<=12;near_display=np.linalg.norm(P-np.median(s['P'][base],0),axis=1)<=q['background_display_far_outer_diameters']*2*(s['c']['R_mm']+.6);display=(ellipse(q['background_display_ellipse_scale'])&near_display)|contact;fit_roi=ellipse(q['background_fit_ellipse_scale']);z=p['depth_mm'];valid=np.isfinite(z)&(z>0);hi=cv2.dilate(np.where(valid,z,0).astype(np.float64),np.ones((3,3),np.uint8));lo=cv2.erode(np.where(valid,z,1e6).astype(np.float64),np.ones((3,3),np.uint8));gradient=(hi-lo)[v,u];col=rgb[v,u];quality=fit_roi&(col.max(1)<q['background_specular_value_max'])&(col.min(1)>q['background_dark_value_min'])&(gradient<=q['background_depth_gradient_max_mm'])
    folder=R/'local_results/background';folder.mkdir(parents=True,exist_ok=True);np.savez_compressed(folder/(cid+'.npz'),XYZ_mm=P,RGB=col/255.,source_uv=np.c_[u,v],display=display,fit_roi=fit_roi,quality=quality,gradient_mm=gradient,depth_axial_mm=z[v,u],base_proxy_uv=center)
    return dict(P=P,rgb=col/255.,uv=np.c_[u,v],display=display,fit_roi=fit_roi,quality=quality,gradient=gradient)
def model_conflicts(video):
    cc=[c for c in cases()if c['video']==video];rows=[];masks={};q=cfg()
    for c in cc:
        s=source(c['id']);P=s['P'];res=[];support=np.ones(len(P),int);front=np.zeros(len(P),bool)
        for other in cc:
            if other['id']==c['id']:continue
            p=source(other['id'])['p'];uv,z=vis.project_camera(P,p['K'],p['pose']);xy=np.rint(uv).astype(int);inside=(z>0)&(xy[:,0]>=0)&(xy[:,0]<640)&(xy[:,1]>=0)&(xy[:,1]<360);ii=np.flatnonzero(inside);x,y=xy[ii].T;ii=ii[(p['labels'][y,x]==1)&np.isfinite(p['depth_mm'][y,x])];x,y=xy[ii].T;r=z[ii]-p['depth_mm'][y,x];agree=abs(r)<=q['consistency_mm'];support[ii[agree]]+=1;front[ii[r<-q['consistency_mm']]]=True;rows.append(dict(source=c['id'],target=other['id'],source_N=len(P),same_object_visible_N=len(ii),agreement_N=int(agree.sum()),front_conflict_N=int((r<-q['consistency_mm']).sum()),residual_mm=stats(r),status='MODEL_CONSISTENCY_NOT_GT'))
        masks[c['id']]=dict(support=support,front=front)
    return rows,masks
def prepare():
    ds=load(ICF/'inputs/datasets.json');cc=cases();refs=load(ICF/'inputs/references.json');out=[];files=[R/'TASK.md',ICF/'inputs/datasets.json',ICF/'inputs/references.json',ICF/'inputs/H_frozen.json',ICF/'metrics/cross_exploratory.json',SPARSE/'code/run.py']
    for role,key in [('selection','D0_selection_targets'),('holdout','D1_held_targets')]:
        for video,indices in cfg()[key].items():
            camera=np.load(next(c['camera_file']for c in cc if c['video']==video));union=set(i for c in refs if c['video']==video for i in c['sources'])
            for index in indices:
                assert index not in union;f=ds[video]['ledger'][index];out.append(dict(video=video,role=role,index=index,id=f['id'],raw_frame=f['raw_frame'],RGB=f['RGB_path'],Mask=f['Mask_path'],K=camera['K'],c2w=camera['c2w'][index],not_in_any_source_HERO_inputs=True,whole_pipeline_independent=False));files += [f['RGB_path'],f['Mask_path']]
    prior={x['path']:x['sha256']for x in load(Path('/home/liu/ring_first_3d_abs_density/experiments/TASK-PHASEC-ABS-DENSITY-REPROJ-001/provenance/INPUTS.json'))['files']}
    for c in cc:
        for k in ['pack','mesh','source_points','RGB','Mask','camera_file']:assert sha(c[k])==prior[c[k]];files.append(c[k])
        files += [PREV/f'local_fields/{c["id"]}_fields.npz',Path('/home/liu/ring_first_3d_abs_density/experiments/TASK-PHASEC-ABS-DENSITY-REPROJ-001/local_results')/c['id']/'T2_exact.npz',Path('/home/liu/ring_first_3d_abs_density/experiments/TASK-PHASEC-ABS-DENSITY-REPROJ-001/local_results')/c['id']/'Final_Cleaned_exact.npz']
    for video in ['004','005']:
        for obj in ['Polyp','Background']:
            files += [ICF/f'meshes/{video}_{obj}_{method}.ply'for method in ['B_raw_multiref','C_confidence_fused']]+[ICF/f'provenance/{video}_{obj}_fusion.npz']
    files += [ring_path(cc[0])]+list((REPO/'visualization').glob('*.py'))+list((REPO/'visualization').glob('*.json'))
    save('provenance/TARGETS_FROZEN.json',out);save('provenance/CASES.json',cc);save('provenance/INPUTS.json',stamp(files));save('provenance/SOURCE_RULES_FROZEN.json',stamp(list((R/'code').glob('*.py'))+[R/'config.json',R/'PROTOCOL.md',R/'provenance/TARGETS_FROZEN.json']));print('FROZEN six references; selection and holdout targets separated; zero GT/upstream updates',flush=True)
def run_D0():
    verify();ranking=[];conflicts=[];index=[]
    for x in load(R/'provenance/SOURCE_RULES_FROZEN.json')['files']:assert sha(x['path'])==x['sha256'],x['path']
    for video in ['004','005']:
        cc=[c for c in cases()if c['video']==video];rows,diagnostics=model_conflicts(video);conflicts+=rows;rank=[];supportMasks={}
        for c in cc:
            s=source(c['id']);m=s['m'];a=s['a'];cl=face_components(m.faces);ca=np.bincount(cl,weights=s['areas']);largest=float(ca.max()/ca.sum());explain,photo=point_explanation(s,target(video,'selection')[0]);supportMasks[c['id']]=photo;T2=np.load(Path('/home/liu/ring_first_3d_abs_density/experiments/TASK-PHASEC-ABS-DENSITY-REPROJ-001/local_results')/c['id']/'T2_exact.npz');risk=np.zeros(len(s['P']),bool);risk[T2['deleted_original_indices']]=True;s['risk']=risk;final=np.load(Path('/home/liu/ring_first_3d_abs_density/experiments/TASK-PHASEC-ABS-DENSITY-REPROJ-001/local_results')/c['id']/'Final_Cleaned_exact.npz');assert np.array_equal(final['XYZ_mm'],s['P']);F=diagnostics[c['id']]['front'];terms=dict(selection_view_coverage=explain['coverage'],source_RGB_explanation=1-min(1,(80 if explain['RGB']['MAE']is None else explain['RGB']['MAE'])/80),largest_face_component=largest,nonconflict_source_fraction=1-F.mean(),not_frozen_T2_candidate_fraction=1-risk.mean());score=sum(cfg()['main_score_weights'][k]*v for k,v in terms.items());row=dict(id=c['id'],video=video,points=len(s['P']),faces=len(m.faces),raw_area_mm2=float(s['areas'].sum()),face_components=len(ca),score=score,score_terms=terms,selection_view=explain,Raw_equals_frozen_Final_Cleaned=True,real_anatomical_accuracy=None);rank.append(row);ranking.append(row)
        rank.sort(key=lambda x:(-x['score'],x['id']));main=rank[0]['id'];ambiguous=rank[0]['score']-rank[1]['score']<cfg()['main_ambiguity_gap'];accepted=mesh(source(main)['P'],source(main)['m'].faces);point_parts=[];face_records=[];folder=R/'local_results/D0'/video;folder.mkdir(parents=True,exist_ok=True);allfiles=[]
        for item in rank:
            cid=item['id'];s=source(cid);P=s['P'];F=s['m'].faces;dg=diagnostics[cid];photo=supportMasks[cid];status=np.full(len(F),3,int)
            if cid==main:
                status[:]=1;status[(dg['support'][F]>=2).all(1)&~dg['front'][F].any(1)&photo[F].all(1)]=0;status[dg['front'][F].any(1)]=2
            else:
                probes=np.concatenate([P[F[:,0]],P[F[:,1]],P[F[:,2]],P[F].mean(1),(P[F[:,0]]+P[F[:,1]])/2,(P[F[:,1]]+P[F[:,2]])/2,(P[F[:,2]]+P[F[:,0]])/2]);distance,norm=nearest(probes,accepted);D=distance.reshape(7,len(F)).T;normal=np.abs(np.sum(norm[3*len(F):4*len(F)]*s['m'].face_normals,axis=1));near=(D.max(1)<=cfg()['duplicate_distance_mm'])&(normal>=np.cos(np.deg2rad(cfg()['normal_compatibility_degrees'])));new=(D.min(1)>cfg()['duplicate_distance_mm'])&photo[F].all(1)&~dg['front'][F].any(1)&~s['risk'][F].any(1);status[near]=4;status[new]=5;status[dg['front'][F].any(1)]=2
                if new.any():accepted=trimesh.util.concatenate([accepted,mesh(P,F[new])])
            keep=status!=4;used=np.zeros(len(P),bool);used[np.unique(F[keep])]=True;unreferenced=np.ones(len(P),bool);unreferenced[np.unique(F)]=False;used|=unreferenced;core=np.zeros(len(P),bool);core[np.unique(F[(status==0)|(status==1)|(status==5)|(status==2)if cid==main else status==5])]=True
            point_parts.append(dict(id=cid,P=P[used],rgb=s['rgb'][used],original_ids=np.flatnonzero(used),core=core[used]));counts={str(k):dict(faces=int((status==k).sum()),area_mm2=float(s['areas'][status==k].sum()))for k in range(6)};record=dict(reference=cid,is_main=cid==main,class_counts=counts,original_points=len(P),displayed_source_points=int(used.sum()),preserved_original_faces=int(keep.sum()),new_observed_pose_conditional_area_mm2=float(s['areas'][status==5].sum()),unique_true_visible_area_mm2=None);face_records.append(record);np.savez_compressed(folder/(cid+'_source_exact.npz'),XYZ_mm=P,RGB=s['rgb'],faces=F,source_uv=np.c_[s['a']['source_u'],s['a']['source_v']],face_status=status,display_point_original_ids=np.flatnonzero(used),core_point_original_ids=np.flatnonzero(core),photo_support=photo,multi_support=dg['support'],front_conflict=dg['front'],frozen_Type2_risk=s['risk']);allfiles.append(str(folder/(cid+'_source_exact.npz')));background(cid)
        allP=np.r_[tuple(x['P']for x in point_parts)];allRGB=np.r_[tuple(x['rgb']for x in point_parts)];core=np.r_[tuple(x['core']for x in point_parts)];refid=np.concatenate([np.full(len(x['P']),cases().index(source(x['id'])['c']),int)for x in point_parts]);ids=np.r_[tuple(x['original_ids']for x in point_parts)];np.savez_compressed(folder/'scene_points_exact.npz',XYZ_mm=allP,RGB=allRGB,core=core,source_case_index=refid,source_original_id=ids)
        rec=dict(video=video,main_reference=main,main_selection='AMBIGUOUS_PROVISIONAL_MAIN'if ambiguous else'SCORE_SELECTED_POSE_CONDITIONAL_MAIN',ranking=rank,all_available_references=[c['id']for c in cc],source_faces=face_records,coordinate='independent video Ring local XYZ millimeters',source_adjustments='identity for every reference; no unreliable intra-video ICP',class_legend={'0':'MAIN_SUPPORTED_POSE_CONDITIONAL','1':'MAIN_UNKNOWN','2':'CONFLICT','3':'UNKNOWN','4':'DUPLICATE_NOT_DISPLAYED_SOURCE_PRESERVED','5':'NEWLY_OBSERVED_POSE_CONDITIONAL'},core_P0_points=int(core.sum()),all_layer_P0_points=len(allP),true_new_visible_area_mm2=None,supported_primary_observed_area_mm2=sum(x['class_counts']['0']['area_mm2']for x in face_records),new_nonduplicate_observed_triangle_area_mm2=sum(x['new_observed_pose_conditional_area_mm2']for x in face_records),status='MULTIREFERENCE_OPEN_LAYERS_NOT_GEOMETRY_CERTIFIED');save('metrics/D0_'+video+'.json',rec);index.append(rec);print('D0',video,'main',main,rec['main_selection'],'conditional new source area',rec['new_nonduplicate_observed_triangle_area_mm2'],flush=True)
    save('metrics/D0_scenes.json',index);save('metrics/main_surface_scores.json',ranking);csvsave('metrics/main_surface_scores.csv',ranking);save('metrics/multireference_conflicts.json',conflicts);csvsave('metrics/multireference_conflicts.csv',conflicts)
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['prepare','D0']);x=p.parse_args();prepare()if x.mode=='prepare'else run_D0()
