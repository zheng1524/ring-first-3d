"""Frozen cleaner reuse and one-level original-triangle incremental fusion."""
from assets import *
from historical_damage import damage
def area(P,F):return np.linalg.norm(np.cross(P[F[:,1]]-P[F[:,0]],P[F[:,2]]-P[F[:,0]]),axis=1)/2
def A():
    verify();rows=[];decisions=[];states={};thresholds=load(ABS/'provenance/VIDEO_THRESHOLDS_FROZEN.json')['videos']
    for c in cases():
        s=source(c['id']);path=ABS/f'local_results/{c["id"]}/T2_exact.npz';deleted=np.zeros(len(s['P']),bool);T=None
        if path.exists():
            h=np.load(path);deleted[h['deleted_original_indices']]=True;T=float(h['rho_threshold']);assert np.array_equal(deleted,s['a']['rho_surface_radius']<T)
        states[c['id']]=dict(old=deleted,T=T)
        folder=R/'local_results'/c['id'];folder.mkdir(parents=True,exist_ok=True);raw=ABS/f'local_results/{c["id"]}/spatial_regions.npz';(folder/'spatial_regions.npz').write_bytes(raw.read_bytes());np.savez_compressed(folder/'Raw_exact.npz',XYZ_mm=s['P'],RGB=s['rgb'],faces=s['m'].faces,source_uv=np.c_[s['a']['source_u'],s['a']['source_v']]);trimesh.points.PointCloud(s['P'],colors=np.rint(s['rgb']*255).astype(np.uint8)).export(folder/'Raw.ply');s['m'].export(folder/'Raw_original_mesh.ply')
    for sc in scenes():
        rr=[]
        for cid in sc['references']:
            s=source(cid);old=states[cid]['old'];exempt=np.zeros(len(old),bool);proof=np.full(len(old),'',dtype='<U64');photo=observation_support(s['P'],s['rgb'],target(sc['id']));front,_=source_conflicts(s['P'],cid,sc['references'])
            for other in sc['references']:
                if other==cid or not old.any():continue
                o=source(other);keep=~states[other]['old'][o['m'].faces].any(1)
                if not keep.any():continue
                ids=np.flatnonzero(old);dist,_=nearest(s['P'][ids],mesh(o['P'],o['m'].faces[keep]));chosen=ids[(dist<=cfg()['distance_exemption_mm'])&photo[ids]&~front[ids]];exempt[chosen]=True;proof[chosen]='OTHER_CLEAN_SOURCE_WITHIN_0.3mm_AND_TARGET_RGB_MASK'
            candidate=old&~exempt;folder=R/'local_results'/cid;s['old_density_risk']=old
            for label,deleted in [('Historical_Density',old),('Distance_Exempt_Candidate',candidate)]:
                row,facekeep=damage(s['c'],s['a'],s['p'],s['m'],deleted,label,states[cid]['T']);row.update(exempt_points=int(exempt.sum())if label=='Distance_Exempt_Candidate'else 0,independent_error_labels=False);rows.append(row);ids=np.flatnonzero(~deleted);back=np.full(len(deleted),-1,int);back[ids]=np.arange(len(ids));np.savez_compressed(folder/(label+'_exact.npz'),XYZ_mm=s['P'][ids],RGB=s['rgb'][ids],source_uv=np.c_[s['a']['source_u'][ids],s['a']['source_v'][ids]],kept_original_indices=ids,deleted_original_indices=np.flatnonzero(deleted),kept_original_face_indices=np.flatnonzero(facekeep),faces_original_indices=s['m'].faces[facekeep],exempt_original_indices=np.flatnonzero(exempt)if label=='Distance_Exempt_Candidate'else np.empty(0,int),exemption_reason=proof,delete_reason='frozen rho_surface_radius < historical T2; optional source-distance exemption',rho_threshold=np.nan if states[cid]['T']is None else states[cid]['T']);trimesh.Trimesh(s['P'][ids],back[s['m'].faces[facekeep]],vertex_colors=np.rint(s['rgb'][ids]*255).astype(np.uint8),process=False).export(folder/(label+'_original_faces.ply'))
                if label=='Distance_Exempt_Candidate':rr.append(row)
        active=all(x['structure_check_pass']for x in rr)and all(source(cid)['c']['condition']=='NORMAL_CONDITIONAL'for cid in sc['references']);has_threshold=any(states[cid]['T']is not None for cid in sc['references']);apply=active and has_threshold;decisions.append(dict(scene=sc['id'],group=sc['group'],references=len(sc['references']),historical_threshold_present=has_threshold,all_reference_structure_checks_pass=active,applied='DISTANCE_EXEMPT_CANDIDATE'if apply else'RAW',reason='Frozen structure checks and normal camera passed'if apply else'No density activation or safety/geometry evidence insufficient; no threshold tuning',GT_used=False))
        for cid in sc['references']:
            s=source(cid);folder=R/'local_results'/cid;z=np.load(folder/'Distance_Exempt_Candidate_exact.npz');delete=np.zeros(len(s['P']),bool)
            if apply:delete[z['deleted_original_indices']]=True
            ids=np.flatnonzero(~delete);fkeep=~delete[s['m'].faces].any(1);np.savez_compressed(folder/'Applied_exact.npz',XYZ_mm=s['P'][ids],RGB=s['rgb'][ids],kept_original_indices=ids,deleted_original_indices=np.flatnonzero(delete),kept_original_face_indices=np.flatnonzero(fkeep),faces_original_indices=s['m'].faces[fkeep],density_risk_original_indices=np.flatnonzero(states[cid]['old']),applied_stage='DISTANCE_EXEMPT_CANDIDATE'if apply else'RAW')
        print('A',sc['id'],decisions[-1]['applied'],[(x['id'],x['deleted_points'],x['exempt_points'],x['structure_check_pass'])for x in rr],flush=True)
    save('metrics/A_cleaning.json',rows);csvsave('metrics/A_cleaning.csv',rows);save('metrics/A_decisions.json',decisions);csvsave('metrics/A_decisions.csv',decisions)
def applied(cid):return dict(np.load(R/f'local_results/{cid}/Applied_exact.npz'))
def score_source(cid,sc):
    s=source(cid);a=applied(cid);P=s['P'];F=a['faces_original_indices'];t=target(sc['id']);pred=point_projection(P[a['kept_original_indices']],s['rgb'][a['kept_original_indices']],t);photo=observation_support(P,s['rgb'],t,pred);front,multi=source_conflicts(P,cid,sc['references']);lab=cv2.imread(t['Mask'],0);B=np.asarray(Image.open(t['RGB']).convert('RGB'));valid=(pred['kind']==1)&(lab==1);err=errors(pred,B,valid);cover=float(valid.sum()/(lab==1).sum());ar=area(P,F);cl=face_components(F);ca=np.bincount(cl,weights=ar);largest=float(ca.max()/ca.sum());risk=np.zeros(len(P),bool);risk[a['density_risk_original_indices']]=True;terms=dict(selection_view_coverage=cover,source_RGB_explanation=1-min(1,(err['MAE']or 80)/80),largest_face_component=largest,nonconflict_source_fraction=1-front.mean(),not_frozen_T2_candidate_fraction=1-risk.mean());score=sum(cfg()['main_score_weights'][k]*v for k,v in terms.items());return dict(reference=cid,scene=sc['id'],score=score,terms=terms,selection_target=t['id'],camera_condition=s['c']['condition'],target_qualification=t.get('source_camera_status','FROZEN_PHASE_D_SELECTION'),target_mask_N=int((lab==1).sum()),RGB=err),photo,front,multi
def probes(P,F):return np.concatenate([P[F[:,0]],P[F[:,1]],P[F[:,2]],P[F].mean(1),(P[F[:,0]]+P[F[:,1]])/2,(P[F[:,1]]+P[F[:,2]])/2,(P[F[:,2]]+P[F[:,0]])/2])
def B():
    verify();scores=[];summaries=[];ledger=[]
    for sc in scenes():
        cached={};ranking=[]
        for cid in sc['references']:
            rank,photo,front,multi=score_source(cid,sc);cached[cid]=(photo,front,multi);ranking.append(rank);scores.append(rank)
        ranking.sort(key=lambda x:(-x['score'],x['reference']));main=ranking[0]['reference'];order=[x['reference']for x in ranking];s0=source(main);accepted=mesh(s0['P'],applied(main)['faces_original_indices']);folder=R/'local_results/scenes'/sc['id'];folder.mkdir(parents=True,exist_ok=True);sources=[]
        for rank,cid in enumerate(order):
            s=source(cid);a=applied(cid);P=s['P'];F=a['faces_original_indices'];origF=a['kept_original_face_indices'];photo,front,multi=cached[cid];N=len(P);V=[p for p in P];colors=[c for c in s['rgb']];edges={};source_edge=[[-1,-1]for _ in P];bary=[];parent=[];children=[];faces=[];mixedN=0
            if cid==main:parents_mixed=np.zeros(len(F),bool)
            else:
                d,n=nearest(probes(P,F),accepted);D=d.reshape(7,len(F)).T;parents_mixed=(D.min(1)<=cfg()['duplicate_distance_mm'])&(D.max(1)>cfg()['duplicate_distance_mm'])
            for j,f in enumerate(F):
                if parents_mixed[j]:
                    mixedN+=1;mid=[]
                    for u,v in [(f[0],f[1]),(f[1],f[2]),(f[2],f[0])]:
                        key=tuple(sorted((int(u),int(v))))
                        if key not in edges:edges[key]=len(V);V.append((P[u]+P[v])/2);colors.append((s['rgb'][u]+s['rgb'][v])/2);source_edge.append(list(key))
                        mid.append(edges[key])
                    x,y,z=mid;ff=[[f[0],x,z],[x,f[1],y],[z,y,f[2]],[x,y,z]];weights=[[[1,0,0],[.5,.5,0],[.5,0,.5]],[[.5,.5,0],[0,1,0],[0,.5,.5]],[[.5,0,.5],[0,.5,.5],[0,0,1]],[[.5,.5,0],[0,.5,.5],[.5,0,.5]]]
                    for k,(tri,w)in enumerate(zip(ff,weights)):faces.append(tri);bary.append(w);parent.append(origF[j]);children.append(k+1)
                else:faces.append(f);bary.append(np.eye(3));parent.append(origF[j]);children.append(0)
            V=np.array(V);C=np.array(colors);Fout=np.array(faces,int);parent=np.array(parent,int);weights=np.array(bary,float);child=np.array(children,int);Pprobe=probes(V,Fout);probe_front,_=source_conflicts(Pprobe,cid,sc['references']);has_front=probe_front.reshape(7,len(Fout)).any(0);vertex_photo=(weights*photo[s['m'].faces[parent]][:,None,:]).sum(2)>=.5;photo_ok=vertex_photo.sum(1)>=cfg()['new_patch_minimum_supported_vertices'];risk=np.zeros(N,bool);risk[np.load(R/f'local_results/{cid}/Distance_Exempt_Candidate_exact.npz')['deleted_original_indices']]=True;weak=((weights*risk[s['m'].faces[parent]][:,None,:]).sum(2)>0).any(1);status=np.full(len(Fout),3,int)
            if cid==main:
                status[:]=1;status[photo_ok&~has_front&~weak&bool(s['c']['source_camera_qualified'])]=0;status[has_front]=2;mainF=np.arange(len(Fout));new=np.zeros(len(Fout),bool)
            else:
                dist,norm=nearest(Pprobe,accepted);D=dist.reshape(7,len(Fout)).T;fn=mesh(V,Fout).face_normals;nd=np.abs((norm[3*len(Fout):4*len(Fout)]*fn).sum(1));duplicate=(D.max(1)<=cfg()['duplicate_distance_mm'])&(nd>=np.cos(np.deg2rad(cfg()['normal_compatibility_degrees'])));new=(D.min(1)>cfg()['duplicate_distance_mm'])&photo_ok&~has_front&~weak&bool(s['c']['source_camera_qualified']);status[duplicate]=4;status[new]=5;status[has_front&photo_ok]=2
                if new.any():accepted=trimesh.util.concatenate([accepted,mesh(V,Fout[new])])
            ar=area(V,Fout);original_area=float(area(P,F).sum());assert np.isclose(ar.sum(),original_area,rtol=1e-12,atol=1e-9);np.savez_compressed(folder/(cid+'_faces_exact.npz'),XYZ_mm=V,RGB=C,original_vertex_N=N,source_edge_original_ids=np.array(source_edge,int),faces=Fout,parent_original_face_id=parent,child_code=child,parent_barycentric=weights,face_status=status,original_photo_support=photo,original_front_conflict=front,original_multi_support=multi,original_source_uv=np.c_[s['a']['source_u'],s['a']['source_v']]);counts={str(k):dict(faces=int((status==k).sum()),model_area_mm2=float(ar[status==k].sum()))for k in range(6)};row=dict(scene=sc['id'],group=sc['group'],reference=cid,rank=rank,is_primary=cid==main,applied_source_faces=len(F),subdivided_parent_faces=mixedN,original_source_area_mm2=original_area,output_subtriangle_area_mm2=float(ar.sum()),classes=counts,new_patch_area_mm2=float(ar[status==5].sum()),parent_ids_unique=len(np.unique(parent)),source_frame=s['c']['reference'],original_source_points=N);sources.append(row);ledger.append(row)
            print('B source',cid,'primary',cid==main,'mixed',mixedN,'newmm2',row['new_patch_area_mm2'],flush=True)
        rec=dict(**sc,main_reference=main,reference_order=order,ranking=ranking,ambiguous=len(ranking)>1 and ranking[0]['score']-ranking[1]['score']<cfg()['main_ambiguity_gap'],source_adjustment='identity only; primary never moved/averaged',source_summaries=sources,source_count=len(order),status='MULTIREFERENCE_MODEL_CONDITIONAL'if len(order)>1 else'NO_ADDITIONAL_REFERENCE_AVAILABLE',class_legend={'0':'PRIMARY_SUPPORTED_POSE_CONDITIONAL','1':'PRIMARY_UNKNOWN','2':'CONFLICT','3':'UNKNOWN','4':'DUPLICATE_OBSERVATION_PRESERVED','5':'ADDED_OBSERVED_PATCH_POSE_CONDITIONAL'},primary_raw_area_mm2=float(s0['areas'].sum()),primary_applied_area_mm2=float(area(s0['P'],applied(main)['faces_original_indices']).sum()),new_patch_area_mm2=sum(x['new_patch_area_mm2']for x in sources),true_anatomical_area=None,GT_used=False);summaries.append(rec)
    save('metrics/B_scenes.json',summaries);save('metrics/B_source_ledger.json',ledger);csvsave('metrics/B_source_ledger.csv',ledger);save('metrics/B_main_scores.json',scores);csvsave('metrics/B_main_scores.csv',scores)
def scene_mesh(sc,mode='core'):
    out=[]
    for rank,cid in enumerate(sc['reference_order']):
        if mode=='primary'and rank>0:continue
        if mode=='second'and rank>1:continue
        a=dict(np.load(R/f'local_results/scenes/{sc["id"]}/{cid}_faces_exact.npz'));st=a['face_status'];keep=st!=4 if mode=='evidence'else(np.ones(len(st),bool)if rank==0 else st==5);m=mesh(a['XYZ_mm'],a['faces'][keep]);m.visual.vertex_colors=np.rint(a['RGB']*255).astype(np.uint8);out.append(m)
    m=trimesh.util.concatenate(out);m.remove_unreferenced_vertices();return m
def scene_points(sc,mode='core'):
    pp=[];cc=[];rr=[];ii=[]
    for rank,cid in enumerate(sc['reference_order']):
        if mode=='primary'and rank>0:continue
        if mode=='second'and rank>1:continue
        a=dict(np.load(R/f'local_results/scenes/{sc["id"]}/{cid}_faces_exact.npz'));st=a['face_status'];keep=st!=4 if mode=='evidence'else(np.ones(len(st),bool)if rank==0 else st==5);ids=np.unique(a['faces'][keep]);ids=ids[ids<int(a['original_vertex_N'])]
        if rank==0:ids=applied(cid)['kept_original_indices']
        pp.append(source(cid)['P'][ids]);cc.append(source(cid)['rgb'][ids]);rr.append(np.full(len(ids),cases().index(source(cid)['c']),int));ii.append(ids)
    return np.concatenate(pp),np.concatenate(cc),np.concatenate(rr),np.concatenate(ii)
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['A','B']);a=p.parse_args();A()if a.stage=='A'else B()
