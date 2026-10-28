"""Main-surface reverse projection; source-connected observed additions, no weld."""
from geometry import *
EXPLAINED,NOVEL,OCCLUDED,CONFLICT,UNKNOWN=range(5)
LABELS=['EXPLAINED','NOVEL_CANDIDATE','OCCLUDED','GEOMETRIC_CONFLICT','UNKNOWN']
def selected_mask(cid):
    choice=load(R/'metrics/cleaning_decision.json')['selected'];return np.load(R/f'local_results/cleaning/{cid}/{choice}.npz')['deleted']
def normals(cid):return dict(np.load(R/f'local_results/cleaning/{cid}/normals_and_identity.npz'))
def rank_main():
    verify();rows=[];ss=[];q=cfg()['primary_quality']
    for sc in scenes():
        ranked=[]
        for cid in sc['refs']:
            s=source(cid);n=normals(cid);keep=~selected_mask(cid);F=s['F'][keep[s['F']].all(1)];weights=vertex_area(s['P'],F);good=n['reliable']&keep;cover=direction(s['P'],n['normal'],good,weights,s['p']['pose']);pred=projection(s['P'][keep],s['C'][keep],selection(sc['id']));m=metric(pred,selection(sc['id']));top=topology(s,~keep);quality=m['coverage']>=q['minimum_selection_point_coverage']and(m['RGB']['MAE']or 1e9)<=q['maximum_selection_RGB_MAE']and good.sum()/keep.sum()>=q['minimum_reliable_point_fraction']and s['c']['source_camera_qualified'];row=dict(scene=sc['id'],reference=cid,condition=s['c']['condition'],quality_admitted=bool(quality),reliable_point_N=int(good.sum()),reliable_fraction=float(good.sum()/keep.sum()),reliable_original_area_proxy_mm2=cover['reliable_area_proxy_mm2'],normal_direction=cover,source_camera_center_mm=s['p']['pose'][:3,3],source_optical_axis=s['p']['pose'][:3,2],selection=m,continuity=top,area_bin_5mm2=int(cover['reliable_area_proxy_mm2']//5));ranked.append(row)
        ranked.sort(key=lambda r:(r['quality_admitted'],r['area_bin_5mm2'],r['normal_direction']['covered_bins'],r['continuity']['largest_raw_main_piece_retention'],r['selection']['coverage']),reverse=True)
        for i,r in enumerate(ranked):r['rank']=i+1;rows.append(r)
        main=ranked[0];amb=len(ranked)>1 and ranked[1]['quality_admitted']==main['quality_admitted'] and abs(main['area_bin_5mm2']-ranked[1]['area_bin_5mm2'])<=1
        ss.append(dict(**sc,primary=main['reference'],reference_order=[r['reference']for r in ranked],status='SINGLE_REFERENCE_ONLY'if len(ranked)==1 else('PRIMARY_AMBIGUOUS'if amb else'PRIMARY_SELECTED'),parallel_diagnostic_primaries=[r['reference']for r in ranked[:2]]if amb else[main['reference']],quality_admitted=main['quality_admitted'],primary_XYZ_SHA256=hashlib.sha256(source(main['reference'])['P'][~selected_mask(main['reference'])].tobytes()).hexdigest(),primary_frozen=True))
        print('PRIMARY',sc['id'],main['reference'],'quality',main['quality_admitted'],'area proxy',main['reliable_original_area_proxy_mm2'],flush=True)
    both('primary_selection',rows);save('metrics/primary_scenes.json',ss);save('provenance/PRIMARY_FROZEN.json',stamp([R/'metrics/primary_selection.json',R/'metrics/primary_scenes.json',R/'metrics/cleaning_decision.json']))
def classify(P0,F0,s,t,H=np.eye(4)):
    """Project only fixed primary original faces into secondary real camera."""
    # t is in primary frame. Secondary original points transformed by H.
    primary=raymesh(P0,F0,t);P=transform(s['P'],H);uv,z=vis.project_camera(P,np.asarray(t['K']),np.asarray(t['c2w']));xy=np.floor(uv+.5).astype(int);inside=(z>0)&np.isfinite(uv).all(1)&(xy[:,0]>=0)&(xy[:,0]<640)&(xy[:,1]>=0)&(xy[:,1]<360);status=np.full(len(P),UNKNOWN,np.int8);delta=np.full(len(P),np.nan);ii=np.flatnonzero(inside);u,v=xy[ii].T;own=raymesh(P,s['F'][~selected_mask(s['c']['id'])[s['F']].any(1)],t);tau=depth_tau(z[ii],np.asarray(t['K']));self_z=own['raw_z'][v,u];ringz=primary['CAD_z'][v,u];occ=(z[ii]>ringz+cfg()['CAD_tolerance_mm'])|(z[ii]>self_z+tau);expl=primary['valid'][v,u];dz=z[ii]-primary['z'][v,u];delta[ii]=dz;status[ii[~occ&~expl]]=NOVEL;status[ii[~occ&expl&(abs(dz)<=tau)]]=EXPLAINED;status[ii[~occ&expl&(abs(dz)>tau)]]=CONFLICT;status[ii[occ]]=OCCLUDED
    # Removed source points stay UNKNOWN for downstream source integrity.
    status[selected_mask(s['c']['id'])]=UNKNOWN
    return status,delta,primary
def source_regions(s,mask):
    grid=np.full((360,640),-1,int);grid[s['uv'][:,1],s['uv'][:,0]]=np.arange(len(s['P']));image=np.zeros((360,640),np.uint8);image[s['uv'][mask,1],s['uv'][mask,0]]=1;_,labels=cv2.connectedComponents(image,connectivity=8);point_labels=labels[s['uv'][:,1],s['uv'][:,0]];return point_labels
def aggregate_one(sc,primary_override=None,suffix=''):
    main=primary_override or sc['primary'];s0=source(main);keep0=~selected_mask(main);F0=s0['F'][keep0[s0['F']].all(1)];base=s0['P'];folder=R/'local_results/scenes'/(sc['id']+suffix);folder.mkdir(parents=True,exist_ok=True);summary=[];regions=[];rr=[];total=[];t=selection(sc['id'])
    # Evaluate new points with the pre-frozen selection view; actual held-outs
    # remain unused for classification/acceptance.
    order=[main]+[cid for cid in sc['reference_order']if cid!=main]
    for rank,cid in enumerate(order):
        s=source(cid);n=normals(cid);keep=~selected_mask(cid);weights=vertex_area(s['P'],s['F'][keep[s['F']].all(1)]);support=additional_mask_support(s['P'],t);region=np.zeros(len(s['P']),int);accepted=np.zeros(len(s['P']),bool);delta=np.full(len(s['P']),np.nan)
        if rank==0:status=np.full(len(s['P']),UNKNOWN,np.int8);accepted=keep.copy();status[keep]=EXPLAINED
        else:
            status,delta,_=classify(base,F0,s,target_source(cid));region=source_regions(s,(status==NOVEL)&keep)
            for k in np.unique(region[region>0]):
                ids=np.flatnonzero(region==k);reliable=float(n['reliable'][ids].mean());fraction=float(support[ids].mean());co=cohorts(s);has_stalk=bool(co['possible_stalk_proxy'][ids].any());ok=len(ids)>=cfg()['novel_region_minimum_connected_points']and reliable>=cfg()['novel_region_minimum_reliable_fraction']and fraction>=cfg()['novel_region_minimum_additional_frame_mask_support'];accepted[ids]=ok&support[ids]
                row=dict(scene=sc['id']+suffix,primary=main,reference=cid,region_id=int(k),candidate_points=len(ids),accepted_points=int(accepted[ids].sum()),source_area_proxy_mm2=float(weights[ids].sum()),accepted_area_proxy_mm2=float(weights[ids[accepted[ids]]].sum()),normal_reliable_fraction=reliable,additional_real_frame=t['id'],additional_Mask_support_fraction=fraction,possible_stalk_proxy_present=has_stalk,accept=bool(ok),status='OBSERVED_ADDITION_POSE_CONDITIONAL'if ok else'NOVEL_CANDIDATE_UNCERTIFIED',reason='source-connected actual points + independent-source image Mask support; no nearest-surface veto'if ok else'normal, patch continuity or additional-view support insufficient; preserved',GT_used=False);regions.append(row)
        np.savez_compressed(folder/(cid+'.npz'),XYZ_mm=s['P'],RGB=s['C'],source_uv=s['uv'],original_point_id=np.arange(len(s['P'])),original_faces=s['F'],kept_original_faces=s['F'][keep[s['F']].all(1)],normal=n['normal'],beta_deg=n['beta_deg'],normal_reliable=n['reliable'],cleaning_removed=~keep,class_id=status,class_names=np.array(LABELS),region_id=region,accepted=accepted,selection_mask_support=support,depth_difference_to_primary_mm=delta,H_source_to_primary=np.eye(4),actual_video=s['c']['video'],reference_frame=s['c']['reference'],group=s['c']['group'])
        counts={name:dict(N=int((status==k).sum()),source_area_proxy_mm2=float(weights[status==k].sum()))for k,name in enumerate(LABELS)};summary.append(dict(scene=sc['id']+suffix,primary=main,reference=cid,is_primary=rank==0,raw_points=len(s['P']),selected_points=int(keep.sum()),classes=counts,accepted_new_points=int(accepted.sum())if rank else 0,accepted_new_area_proxy_mm2=float(weights[accepted].sum())if rank else 0,novel_regions=int(region.max()),not_certified_true_area=True));rr.append(dict(scene=sc['id']+suffix,source=cid,target_view=cid,**{name:int((status==k).sum())for k,name in enumerate(LABELS)}));print('REVERSE',sc['id']+suffix,cid,counts['NOVEL_CANDIDATE']['N'],'novel',int(accepted.sum())if rank else 0,'added',flush=True)
        total.append((s,accepted,keep,status,weights))
    newdir=[];initial=[]
    for s,ac,ke,st,w in total:
        n=normals(s['c']['id']);good=ac&n['reliable'];d=direction(s['P'],n['normal'],good,w,s['p']['pose']);newdir.append(np.array(d['hist_area_proxy_mm2']));initial.append(d)
    hist=np.sum(newdir,axis=0);primaryhist=newdir[0];active=hist>=max(1e-12,hist.sum()*cfg()['direction_bin_minimum_area_fraction']);oldactive=primaryhist>=max(1e-12,primaryhist.sum()*cfg()['direction_bin_minimum_area_fraction']);rec=dict(scene=sc['id']+suffix,primary=main,references=order,primary_points=int(keep0.sum()),added_points=sum(r['accepted_new_points']for r in summary),added_area_proxy_mm2=sum(r['accepted_new_area_proxy_mm2']for r in summary),candidate_regions=len(regions),accepted_regions=sum(r['accept']for r in regions),primary_direction_bins=int(oldactive.sum()),aggregate_direction_bins=int(active.sum()),new_direction_bins=np.flatnonzero(active&~oldactive),normal_hist_area_proxy_mm2=hist,primary_unchanged=True,status='SINGLE_REFERENCE_ONLY'if len(order)==1 else'OBSERVED_ADDITIONS_POSE_CONDITIONAL',uncertified_and_conflict_preserved=True)
    return summary,regions,rr,rec
def main():
    verify();summ=[];regions=[];rr=[];ss=[]
    for sc in load(R/'metrics/primary_scenes.json'):
        a,b,c,d=aggregate_one(sc);summ+=a;regions+=b;rr+=c;ss.append(d)
        if sc['status']=='PRIMARY_AMBIGUOUS':
            for alt in sc['parallel_diagnostic_primaries'][1:]:
                a,b,c,d=aggregate_one(sc,alt,'_alternate');summ+=a;regions+=b;rr+=c;ss.append(d)
    both('source_contribution',summ);both('novel_surface_candidates',regions);both('reverse_projection_regions',rr);both('aggregation_summary',ss)
if __name__=='__main__':
    rank_main()if len(sys.argv)>1 and sys.argv[1]=='primary'else main()
