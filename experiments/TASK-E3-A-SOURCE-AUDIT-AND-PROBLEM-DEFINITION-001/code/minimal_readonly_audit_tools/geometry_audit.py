"""CPU geometry/view/retention facts only; no fusion or field construction."""
from common import *

def own_maps(cid):
    uv=np.c_[np.tile(np.arange(640),360),np.repeat(np.arange(360),640)];z,fid=cast_mesh(cid,uv);cad=source_camera(cid).cast(uv)['t_hit'].numpy()
    valid=np.isfinite(z)&(z>0)&(z<=cad+.002);out=dict(raw_Z=z.reshape(360,640),raw_face=fid.reshape(360,640),CAD_Z=cad.reshape(360,640),visible=valid.reshape(360,640))
    p=R/'local_results/own';p.mkdir(exist_ok=True);np.savez_compressed(p/(cid+'.npz'),**out);return out

def normal_bins(N):
    az=np.mod(np.arctan2(N[:,1],N[:,0]),2*np.pi);el=np.arcsin(np.clip(N[:,2],-1,1));return np.minimum((az/(2*np.pi)*12).astype(int),11)+12*np.clip(((el+np.pi/2)/np.pi*6).astype(int),0,5)
def cam_bin(v):return int(np.floor(np.mod(np.degrees(np.arctan2(v[1],v[0])),360)/10))+36*int(np.clip(np.floor((np.degrees(np.arcsin(v[2]))+90)/10),0,17))

def analyze_sources():
    topology=[];retention=[];facts={};roi={}
    for sid in scenes():
        refs=[c for c in D['references']if c['scene_id']==sid];good=[c for c in refs if eligible(c)];used=good if good else refs
        P=np.concatenate([source(c['id'])['P']for c in used]);cad=ring(refs[0]['ring']);allP=np.r_[P,np.asarray(cad.vertices)];margin=max(2.,.25*np.ptp(cad.bounds,axis=0).max());lo=allP.min(0)-margin;hi=allP.max(0)+margin
        cand=np.concatenate([source(c['id'])['P']for c in refs]);roi[sid]=dict(world_frame=sid+'_LOCAL_RING_MM',Ring_origin_mm=np.asarray(cad.centroid),Ring_normal=[0,0,1],source_to_world='identity in archived source local Ring frame; no cross-video transform',
            minimum_mm=lo,maximum_mm=hi,center_mm=(lo+hi)/2,margin_mm=margin,qualified_reference_ids=[c['id']for c in good],
            all_available_candidate_envelope_mm=[cand.min(0),cand.max(0)],Polyp_envelope_mm=[P.min(0),P.max(0)],
            status='FROZEN_CONDITIONAL_GLOBAL_ROI'if good else'PROVISIONAL_STRESS_ONLY_NOT_FORMAL_GLOBAL_ROI',
            boundary_uncertainty='safety margin is protocol, not calibrated camera/shape error; no quantile cropping',Ring_origin_is_not_zero_surface=True)
    save('config/GLOBAL_ROI_FROZEN.json',roi);freeze('BEFORE_SOURCE_GEOMETRY_DIAGNOSTICS.json')
    for c in D['references']:
        cid=c['id'];s=source(cid);P,F,A=s['P'],s['F'],s['area'];centers=P[F].mean(1);N=np.cross(P[F[:,1]]-P[F[:,0]],P[F[:,2]]-P[F[:,0]]);N/=np.maximum(np.linalg.norm(N,axis=1,keepdims=True),1e-20)
        flip=(N*(s['T'][:3,3]-centers)).sum(1)<0;N[flip]*=-1
        _,Z=vis.project_camera(P,s['K'],s['T']);foot=Z[F].mean(1)/min(s['K'][0,0],s['K'][1,1]);edge=np.linalg.norm(P[F[:,[1,2,0]]]-P[F],axis=2).max(1);stretch=edge/np.maximum(foot,1e-12)>cfg()['stretch_proxy_max_edge_over_footprint']
        lab=face_components(F);area=np.bincount(lab,weights=A);minor=area[lab]<area.max()*.01;E,count=edge_counts(F);q=s['clean'];keep=~q['clean_removed'];cleanface=keep[F].all(1);protected=q['protected_possible_stalk']|q['protected_Ring'];protectedface=protected[F].any(1)
        maps=own_maps(cid);polyp=s['labels']==1;depthok=polyp&np.isfinite(s['depth'])&(s['depth']>0);actual=polyp&maps['visible'];missing=polyp&~maps['visible'];behind=polyp&np.isfinite(maps['raw_Z'])&(maps['raw_Z']>maps['CAD_Z']+.002)
        use=(~stretch)&(A>1e-12);bins=normal_bins(N);hist=np.bincount(bins[use],weights=A[use],minlength=72);active=np.flatnonzero(hist>=max(hist.sum()*.01,1e-12));v=s['T'][:3,3]-np.asarray(roi[c['scene_id']]['center_mm']);v/=np.linalg.norm(v)
        vox=np.floor(centers[use]/.5).astype(int);voxcodes={tuple(x)for x in vox};facts[cid]=dict(direction=v,camera_bin=cam_bin(v),normal_bins=set(map(int,active)),voxels=voxcodes,
            main_area_fraction=float(area.max()/A.sum()),stretch_fraction=float(A[stretch].sum()/A.sum()))
        topology.append(dict(scene=c['scene_id'],physical_group=c['group'],source=cid,reference_camera_screened=eligible(c),raw_vertices=len(P),raw_faces=len(F),raw_area_mm2=float(A.sum()),
            components=len(area),main_component_area_mm2=float(area.max()),main_component_area_fraction=float(area.max()/A.sum()),boundary_edges=int((count==1).sum()),nonmanifold_edges=int((count>2).sum()),
            stretched_face_proxy_N=int(stretch.sum()),stretched_area_proxy_mm2=float(A[stretch].sum()),stretched_area_proxy_fraction=float(A[stretch].sum()/A.sum()),minor_component_proxy_N=int((area<area.max()*.01).sum()),minor_component_area_proxy_mm2=float(A[minor].sum()),
            normal_coverage_bins=len(active),normal_area_histogram_mm2=hist,full_Polyp_Mask_N=int(polyp.sum()),qualified_numeric_depth_N=int(depthok.sum()),raw_triangle_first_hit_Polyp_N=int(actual.sum()),
            observed_but_no_visible_raw_triangle_N=int(missing.sum()),positive_Mask_raw_behind_CAD_N=int(behind.sum()),all_counts_are_source_proxies_not_GT=True))
        stages={'Raw':np.ones(len(F),bool),'Cleaned_F1':cleanface};fp=PART/f'local_results/pointcloud_blocks/{c["scene_id"]}/ViewPartition_Cleaned_F2/{cid}.npz'
        if fp.exists():stages['F2']=np.load(fp)['accepted'][F].all(1)
        blocks=load(GROW/f'local_results/scenes/{c["scene_id"]}_Final.json')['blocks'];my=[b for b in blocks if b['reference']==cid];ids=sorted({int(i)for b in my for i in b['face_ids']});chosen=np.zeros(len(F),bool);chosen[ids]=True
        stages['F3']=chosen
        for stage,mask in stages.items():
            included=stage!='F3'or bool(my);retention.append(dict(scene=c['scene_id'],source=cid,stage=stage,raw_face_denominator=len(F),raw_area_denominator_mm2=float(A.sum()),source_in_historical_output=included,
                original_faces_retained_N=int(mask.sum()),original_area_retained_mm2=float(A[mask].sum()),original_area_omitted_mm2=float(A[~mask].sum()),retained_area_fraction=float(A[mask].sum()/A.sum()),
                protected_proxy_raw_area_mm2=float(A[protectedface].sum()),protected_proxy_omitted_area_mm2=float(A[protectedface&~mask].sum()),
                identity='historical output membership, not physically certified destruction; F3 selection scope differs and may move geometry',strict_same_input_replay=False))
        if not fp.exists():retention.append(dict(scene=c['scene_id'],source=cid,stage='F2',raw_face_denominator=len(F),source_in_historical_output=False,
            original_faces_retained_N=None,original_area_retained_mm2=None,identity='NOT_IN_F2_HISTORICAL_INPUT_SET; not silently zero retention',strict_same_input_replay=False))
        p=R/'local_results/face_facts';p.mkdir(exist_ok=True);np.savez_compressed(p/(cid+'.npz'),oriented_face_normals=N,component=lab,stretch_proxy=stretch,minor_proxy=minor,
            clean_kept=cleanface,protected_proxy=protectedface,F3_kept=chosen,normal_bins=bins)
        print('SOURCE_GEOMETRY',cid,'faces',len(F),'visible',int(actual.sum()),'missing',int(missing.sum()),flush=True)
    table('metrics/E3_RAW_SURFACE_DIAGNOSTICS.csv',topology);table('metrics/E3_HISTORICAL_FACE_RETENTION.csv',retention)
    return facts,roi

def analyze_pairs(facts):
    rows=[]
    for a in D['references']:
        A=source(a['id']);n=len(A['P']);ix=np.unique(np.linspace(0,n-1,min(n,2048)).astype(int));P=A['P'][ix];uvA=A['uv'][ix];own=np.load(R/f'local_results/own/{a["id"]}.npz');ownok=own['visible'][uvA[:,1],uvA[:,0]]
        for b in D['references']:
            if a['scene_id']!=b['scene_id']or a['id']==b['id']:continue
            B=source(b['id']);uv,Z=vis.project_camera(P,B['K'],B['T']);xy=np.floor(uv+.5).astype(int);inside=(Z>0)&(xy[:,0]>=0)&(xy[:,0]<640)&(xy[:,1]>=0)&(xy[:,1]<360)
            ii=np.flatnonzero(inside&ownok);pixels=xy[ii];mask=B['labels'][pixels[:,1],pixels[:,0]]==1
            if len(ii):zB,fid=cast_mesh(b['id'],uv[ii]);cad=source_camera(b['id']).cast(uv[ii])['t_hit'].numpy()
            else:zB=np.empty(0);fid=np.empty(0,np.uint32);cad=np.empty(0)
            cadbehind=np.isfinite(cad)&(Z[ii]>cad+.002);targetvis=np.isfinite(zB)&(zB>0)&(zB<=cad+.002);good=mask&targetvis&~cadbehind;sel=ii[good];zz=zB[good];delta=Z[sel]-zz;tau=np.maximum(.5,3*zz/min(B['K'][0,0],B['K'][1,1]))
            cycle=np.array([])
            if len(sel):
                PB=unproject(zz,B['T'],uv[sel],B['K']);back,_=vis.project_camera(PB,A['K'],A['T']);cycle=np.linalg.norm(back-uvA[sel],axis=1)
            family_overlap=set(a['source_alias_hashes'])&set(b['source_alias_hashes']);row=dict(scene=a['scene_id'],A=a['id'],B=b['id'],pair_camera_reference_eligible=eligible(a)and eligible(b),
                source_sample_N=len(ix),source_own_visible_sample_N=int(ownok.sum()),target_in_image_N=int(inside.sum()),target_Polyp_Mask_N=int(mask.sum()),
                original_mesh_covisible_N=len(sel),source_mesh_overlap_fraction=len(sel)/len(ix),source_points_behind_target_CAD_N=int(cadbehind.sum()),
                ROI_camera_direction_angle_deg=angle(facts[a['id']]['direction'],facts[b['id']]['direction']),camera_translation_baseline_mm=float(np.linalg.norm(A['T'][:3,3]-B['T'][:3,3])),
                optical_axis_angle_deg=angle(A['T'][:3,2],B['T'][:3,2]),shared_HERO_parent_RGB_N=len(family_overlap),
                co_projected_signed_median_mm=None if not len(delta)else float(np.median(delta)),co_projected_abs_median_mm=None if not len(delta)else float(np.median(abs(delta))),
                co_projected_abs_p95_mm=None if not len(delta)else float(np.quantile(abs(delta),.95)),diagnostic_separated_layers_N=int((abs(delta)>tau).sum()),
                reciprocal_pixel_cycle_le2_N=int((cycle<=2).sum()),verified_same_physical_surface_N=0,
                interpretation='CORRESPONDENCE_UNRESOLVED; depth separation is not certified prediction error; CAD occlusion kept separately')
            rows.append(row)
    table('metrics/E3_VIEW_COVERAGE.csv',rows);return rows

def organize(facts,roi,pairs):
    roles={};proposal=[];coverage=[];rows=readrows(R/'metrics/E3_SOURCE_AND_VIEW_MANIFEST.csv')
    for sid in scenes():
        refs=[c['id']for c in D['references']if c['scene_id']==sid];legal=[r for r in refs if eligible(CC[r])]
        historical=[r for r in refs if r in [x['id']for x in D['references'][:9]]];selected=[r for r in historical if r in legal];budget=4 if sid.startswith('G01') else 3
        allvox=set().union(*(facts[r]['voxels']for r in legal))if legal else set();allnorm=set().union(*(facts[r]['normal_bins']for r in legal))if legal else set();allcam={facts[r]['camera_bin']for r in legal}
        def sets(rr):return (set().union(*(facts[r]['voxels']for r in rr))if rr else set(),set().union(*(facts[r]['normal_bins']for r in rr))if rr else set(),{facts[r]['camera_bin']for r in rr})
        def linked(a,b):
            ab=next(p for p in pairs if p['A']==a and p['B']==b);ba=next(p for p in pairs if p['A']==b and p['B']==a)
            return min(ab['source_mesh_overlap_fraction'],ba['source_mesh_overlap_fraction'])>=.1
        while len(selected)<budget:
            have=sets(selected);candidates=[]
            for r in legal:
                if r in selected or selected and not any(linked(r,x)for x in selected):continue
                added=sets(selected+[r]);gain=sum(len(a-b)/max(len(c),1)for a,b,c in zip(added,have,[allvox,allnorm,allcam]));candidates.append((gain,r))
            if not candidates:break
            gain,r=sorted(candidates,key=lambda x:(-x[0],x[1]))[0]
            if gain<=0:break
            selected.append(r)
        for r in refs:roles[r]='UNQUALIFIED'if r not in legal else'CORE'if r in historical else'BRIDGE'if r in selected else'RESERVED'
        prefix=[]
        for r in selected:
            old=sets(prefix);prefix.append(r);new=sets(prefix);coverage.append(dict(scene=sid,added_source=r,role=roles[r],selected_N=len(prefix),camera_direction_bins=len(new[2]),normal_bins=len(new[1]),spatial_voxels=len(new[0]),
                marginal_camera_bins=len(new[2]-old[2]),marginal_normal_bins=len(new[1]-old[1]),marginal_voxels=len(new[0]-old[0]),all_eligible_source_N=len(legal),source_family_independence_gain=0 if len(prefix)>1 else 1))
        def components(rr):
            if not rr:return 0
            graph=np.eye(len(rr),dtype=bool)
            for i,a in enumerate(rr):
                for j,b in enumerate(rr):
                    if i<j:graph[i,j]=graph[j,i]=linked(a,b)
            return int(connected_components(coo_matrix(graph),directed=False)[0])
        proposal.append(dict(scene=sid,all_available_sources=refs,reference_screened_sources=legal,representative_sources=selected,
            all_screened_components=components(legal),representative_components=components(selected),
            all_camera_bins=len(allcam),all_normal_bins=len(allnorm),all_spatial_voxels=len(allvox),
            selected_camera_bins=len(sets(selected)[2]),selected_normal_bins=len(sets(selected)[1]),selected_spatial_voxels=len(sets(selected)[0]),
            all_source_family_N=len({r['source_family']for r in rows if r.get('record_kind')=='HERO_SOURCE'and r.get('source_id')in legal}),
            camera_and_normal_coverage_not_interchangeable=True,proposal_not_optimization_input_authorization=True))
    for row in rows:
        cid=row.get('source_id')
        if cid in facts:
            row['role']=roles[cid];row['view_direction']=clean(facts[cid]['direction']);row['view_angle_group']=str(facts[cid]['camera_bin'])
            row['camera_overlap_status']='DETERMINISTIC_SAME_VIDEO_COVISIBILITY_DIAGNOSTIC; not independent correspondence certification'
    table('metrics/E3_SOURCE_AND_VIEW_MANIFEST.csv',rows);table('metrics/E3_MARGINAL_SOURCE_COVERAGE.csv',coverage);save('provenance/SOURCE_ROLES.json',roles);save('provenance/SOURCE_ORGANIZATION.json',proposal)
    save('provenance/GEOMETRY_STAGE_STATUS.json',dict(source_N=36,pair_N=len(pairs),reference_screened_N=sum(eligible(c)for c in D['references']),
        all_same_surface_certified_N=0,new_fields_or_fusion_run=False,no_raw_mesh_written=True))

def main():
    save('config/ORGANIZATION_RULES_FROZEN.json',dict(score='equal sum of marginal voxel/normal-bin/camera-bin fractions of all reference-screened sources',
        ordering_tie_break='source_id lexicographic',input_quality='camera gate precedes coverage; no downstream SDF score',source_family='same RGB-ancestry component does not create independent votes'))
    facts,roi=analyze_sources();pairs=analyze_pairs(facts);organize(facts,roi,pairs);print('E3_GEOMETRY_ORGANIZATION_COMPLETE',len(pairs),'directed sampled pairs; no fusion')
if __name__=='__main__':main()
