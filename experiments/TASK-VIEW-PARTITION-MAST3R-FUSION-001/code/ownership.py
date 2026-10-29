"""View-block responsibility + source-connected selective point aggregation."""
from geometry import *
from matching import views
EXPLAINED,NOVEL,OCCLUDED,CONFLICT,UNKNOWN=range(5)
LABELS=['EXPLAINED','NOVEL_CANDIDATE','OCCLUDED','GEOMETRIC_CONFLICT','UNKNOWN']
def selected_mask(cid):return np.load(R/f'local_results/cleaned/{cid}.npz')['clean_removed']
@lru_cache(None)
def normal(cid):
    s=source(cid);P,F=s['P'],s['F'];cross=np.cross(P[F[:,1]]-P[F[:,0]],P[F[:,2]]-P[F[:,0]]);N=np.zeros_like(P);mass=np.zeros(len(P));degree=np.zeros(len(P),int)
    for j in range(3):np.add.at(N,F[:,j],cross);np.add.at(mass,F[:,j],np.linalg.norm(cross,axis=1));np.add.at(degree,F[:,j],1)
    l=np.linalg.norm(N,axis=1);coh=np.divide(l,mass,out=np.zeros(len(P)),where=mass>0);N=np.divide(N,l[:,None],out=np.zeros_like(P),where=l[:,None]>0);ray=s['p']['pose'][:3,3]-P;flip=(N*ray).sum(1)<0;N[flip]*=-1;return N,(degree>=3)&(coh>=.85)&(l>0)
# Reuse the exact previous original-face reverse projection and source-connected
# region functions. Only selected_mask resolves this task's CLEAN_FOR_FUSION.
ns=globals()
for n in ast.parse((GRAZ/'code/aggregation.py').read_text()).body:
    if isinstance(n,ast.FunctionDef)and n.name in ['classify','source_regions']:exec(compile(ast.Module(body=[n],type_ignores=[]),str(GRAZ/'code/aggregation.py'),'exec'),ns)
def view_of(c):return next(v for v in views().values()if v['source_id']==c['group']+'_video'+c['video']and v.get('index')==c['reference_index'])
def neighbor(c):
    v=view_of(c);vv=[w for w in views().values()if w['source_id']==v['source_id']and w.get('role')!='HOLDOUT'and w['id']!=v['id']and'view_direction'in w];vv.sort(key=lambda w:angle(np.array(v['view_direction']),np.array(w['view_direction'])));w=vv[0];return dict(id=w['id'],RGB=w['RGB'],Mask=w['Mask'],K=np.array(w['K']),c2w=np.array(w['c2w']),ring_case=c['id'],role='NON_HELD_NEIGHBOR_IMAGE_SUPPORT')
def ownership():
    rows=[];orders={};parts=load(R/'metrics/view_partition.json');vv=views()
    for sid in dict.fromkeys(sceneid(c)for c in cases()):
        cc=[c for c in cases()if sceneid(c)==sid];terms={}
        for c in cc:
            s=source(c['id']);keep=~selected_mask(c['id']);F=s['F'][keep[s['F']].all(1)];n,reliable=normal(c['id']);weight=vertex_area(s['P'],F);support=additional_mask_support(s['P'],neighbor(c));cl=face_components(F);ar=area(s['P'],F);pieces=np.bincount(cl,weights=ar);continuity=float(pieces.max()/pieces.sum())if len(pieces)and pieces.sum()else 0.;quality=1. if c['source_camera_qualified']else .75;quality=.5 if c['group']=='G07'else quality;terms[c['id']]=dict(normal_fraction=float(reliable[keep].mean()),continuity=continuity,neighbor_support_fraction=float(support[keep].mean()),area_retained_fraction=float(ar.sum()/max(1e-12,s['areas'].sum())),quality=quality,visible_area_proxy_mm2=float(ar.sum()),reliable_area_proxy_mm2=float(weight[reliable].sum()),P0_view=view_of(c))
        blocks=[p for p in parts if p['source_id']==cc[0]['group']+'_video'+cc[0]['video']];owners=[]
        for b in blocks:
            ranking=[]
            for c in cc:
                t=terms[c['id']];d=np.array(view_of(c)['view_direction']);theta=angle(d,np.array(b['direction']));eligible=theta<=cfg()['transition_maximum_degrees']or view_of(c)['block']==b['block'];alignment=max(0,float(np.cos(np.deg2rad(theta))));w=cfg()['ownership_weights'];score=t['quality']*(w['direction']*alignment+w['reliable_normal']*t['normal_fraction']+w['continuity']*t['continuity']+w['neighbor_support']*t['neighbor_support_fraction']+w['retained_original_area']*t['area_retained_fraction']);ranking.append(dict(reference=c['id'],score=score,direction_angle_deg=theta,eligible=eligible,terms={k:v for k,v in t.items()if k!='P0_view'}))
            good=[r for r in ranking if r['eligible']];good.sort(key=lambda r:-r['score']);owner=good[0]['reference']if good else None
            rows.append(dict(group=cc[0]['group'],scene=sid,block=b['block'],owner=owner,status='OBSERVED_BLOCK_OWNER_CONDITIONAL'if owner else'NO_P0_FOR_THIS_DIRECTION',ranking=ranking,unknown_surface_not_filled=True))
            if owner and owner not in owners:owners.append(owner)
        owners.sort(key=lambda cid:-max(x['score']for r in rows if r['scene']==sid for x in r['ranking']if x['reference']==cid));orders[sid]=owners+[c['id']for c in cc if c['id']not in owners]
    both('surface_ownership',rows);save('provenance/OWNERSHIP_ORDER_FROZEN.json',dict(orders=orders,source='fixed weights, cleaned continuity/directions and non-held Mask support; no heldout RGB errors',GT_used=False));return orders
def aggregate(sid,order,mode):
    clean=mode!='Raw_F2';P0=None;F0=None;results=[];regions=[];folder=R/'local_results/pointcloud_blocks'/sid/mode;folder.mkdir(parents=True,exist_ok=True)
    for rank,cid in enumerate(order):
        s=source(cid);removed=selected_mask(cid)if clean else np.zeros(len(s['P']),bool);keep=~removed;F=s['F'][keep[s['F']].all(1)];weights=vertex_area(s['P'],F);normal0,reliable=normal(cid);extra=additional_mask_support(s['P'],neighbor(s['c']));accepted=np.zeros(len(s['P']),bool);region=np.zeros(len(s['P']),int);status=np.full(len(s['P']),UNKNOWN,np.int8);delta=np.full(len(s['P']),np.nan)
        if rank==0:accepted=keep.copy();status[keep]=EXPLAINED
        else:
            t=dict(id=s['c']['reference'],K=s['p']['K'],c2w=s['p']['pose'],RGB=s['c']['RGB'],Mask=s['c']['Mask'],ring_case=cid)
            if not clean:
                # Original classifier's input-removal hook is disabled only for
                # the explicit Raw ablation; geometry function is unchanged.
                original=ns['selected_mask'];ns['selected_mask']=lambda _:np.zeros(len(s['P']),bool)
                try:status,delta,_=classify(P0,F0,s,t)
                finally:ns['selected_mask']=original
            else:status,delta,_=classify(P0,F0,s,t)
            region=source_regions(s,(status==NOVEL)&keep)
            for k in np.unique(region[region>0]):
                ids=np.flatnonzero(region==k);rf=float(reliable[ids].mean());sf=float(extra[ids].mean());ok=len(ids)>=cfg()['novel_minimum_points']and rf>=cfg()['novel_normal_reliable_fraction']and sf>=cfg()['novel_neighbor_support_fraction'];accepted[ids]=ok&extra[ids];regions.append(dict(scene=sid,method=mode,reference=cid,region=int(k),candidate_N=len(ids),accepted_N=int(accepted[ids].sum()),normal_reliable_fraction=rf,neighbor_Mask_support_fraction=sf,area_exposure_proxy_mm2=float(weights[ids].sum()),accepted_area_exposure_proxy_mm2=float(weights[ids[accepted[ids]]].sum()),status='OBSERVED_ADDITION_POSE_CONDITIONAL'if ok else'NOVEL_CANDIDATE_PRESERVED',not_true_unique_surface_area=True))
        accepted_faces=F[accepted[F].all(1)];np.savez_compressed(folder/(cid+'.npz'),XYZ_mm=s['P'],RGB=s['C'],source_uv=s['uv'],original_point_id=np.arange(len(s['P'])),original_faces=s['F'],normal=normal0,normal_reliable=reliable,class_id=status,class_names=np.array(LABELS),region=region,accepted=accepted,clean_removed=removed,neighbor_image_support=extra,source_c2w=s['p']['pose'],source_K=s['p']['K'],delta_to_explaining_model_mm=delta,H_after_backprojection=np.eye(4),reference=cid,new_HERO=s['c'].get('new_reference',False))
        counts={name:dict(N=int((status==k).sum()),source_area_exposure_proxy_mm2=float(weights[status==k].sum()))for k,name in enumerate(LABELS)};results.append(dict(scene=sid,method=mode,reference=cid,rank=rank,source_new_HERO=s['c'].get('new_reference',False),raw_N=len(s['P']),input_N=int(keep.sum()),accepted_N=int(accepted.sum()),accepted_new_N=int(accepted.sum())if rank else 0,accepted_new_area_proxy_mm2=float(weights[accepted].sum())if rank else 0,candidate_regions=int(region.max()),classes=counts,possible_stalk_proxy_not_deleted=True,source_XYZ_unchanged=True,accepted_original_face_components=len(np.unique(face_components(accepted_faces)))))
        if P0 is None:P0=s['P'].copy();F0=accepted_faces.copy()
        elif len(accepted_faces):F0=np.r_[F0,accepted_faces+len(P0)];P0=np.r_[P0,s['P']]
        print('F2',sid,mode,cid,'novel',counts['NOVEL_CANDIDATE']['N'],'added',int(accepted.sum())if rank else 0,flush=True)
    return results,regions
def pointset(sid,mode):
    orders=load(R/'provenance/OWNERSHIP_ORDER_FROZEN.json')['orders'];order=orders[sid];P=[];C=[];ref=[];ids=[];uv=[];classes=[]
    for j,cid in enumerate(order):
        s=source(cid)
        if mode in ['Raw_F1','Cleaned_F1']:take=np.ones(len(s['P']),bool)if mode=='Raw_F1'else~selected_mask(cid);st=np.full(len(s['P']),UNKNOWN)
        elif mode=='Single_Cleaned':
            if j:continue
            take=~selected_mask(cid);st=np.full(len(s['P']),EXPLAINED)
        else:
            z=np.load(R/f'local_results/pointcloud_blocks/{sid}/{mode}/{cid}.npz');take=z['accepted'];st=z['class_id']
        ii=np.flatnonzero(take);P.append(s['P'][ii]);C.append(s['C'][ii]);ref.append(np.full(len(ii),j,int));ids.append(ii);uv.append(s['uv'][ii]);classes.append(st[ii])
    return dict(P=np.concatenate(P),C=np.concatenate(C),reference_index=np.concatenate(ref),original_ids=np.concatenate(ids),source_uv=np.concatenate(uv),class_id=np.concatenate(classes),references=order)
def main():
    verify();orders=ownership();save('provenance/P8_RULES_AND_SOURCE_FROZEN.json',stamp([R/'config/rules.json',R/'config/aggregation_rules.json',Path(__file__),R/'provenance/NEW_CASES.json',R/'provenance/OWNERSHIP_ORDER_FROZEN.json',R/'provenance/BLOCKS_AND_FRAME_ROLES_FROZEN.json'],before_selective_aggregation=True,GT_used=False));rows=[];regions=[]
    for sid,order in orders.items():
        for mode in ['Raw_F2','ViewPartition_Cleaned_F2']:
            r,reg=aggregate(sid,order,mode);rows+=r;regions+=reg
    both('novel_surface_contribution',rows);both('novel_regions',regions);save('provenance/F2_GEOMETRY_FROZEN.json',stamp(list((R/'local_results/pointcloud_blocks').rglob('*.npz'))+[R/'metrics/novel_surface_contribution.json'],GT_used=False,unknown_conflict_preserved=True))
if __name__=='__main__':main()
