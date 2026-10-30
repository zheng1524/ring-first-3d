"""Post-output review ledger, boundary visibility and Ip small-structure audit."""
from evaluate import *
def review_status(row):
    if row.get('accepted'):return'ACCEPTED'
    if row.get('status')=='CONFLICT':return'CONFLICT'
    reason=row.get('reason','')
    if any(x in reason for x in ['NO_SOURCE_CONNECTED','NO_MEANINGFUL','NO_CONTINUOUS','NO_ELIGIBLE','NOT_ACTIVE_FRONTIER']):return'CANDIDATE'
    return'REJECTED'
def main():
    import common as shared
    registry=shared.cases();shared.cases=lambda:registry;globals()['cases']=lambda:registry;ledger=[];status_counts=[];frontiers=[];regions=[];stalk=[]
    eval_ids=set(load(R/'provenance/EVALUATION_TARGETS_FROZEN.json')['target_ids'])
    for sid in load(R/'provenance/MAIN_SURFACES_SELECTED.json')['selections']:
        final_path=R/f'local_results/scenes/{sid}_Final.json'
        if not final_path.exists():continue
        cid=load(R/'provenance/MAIN_SURFACES_SELECTED.json')['selections'][sid];candidate=load(R/f'metrics/patch_candidates_{sid}.json');counts={k:0 for k in ['ACCEPTED','CANDIDATE','CONFLICT','REJECTED']}
        for row in candidate:
            status=review_status(row);counts[status]+=1;ledger.append(dict(scene=sid,source=row['reference'],original_component=row['original_component'],round_attempt=row['round_attempt'],review_status=status,algorithm_status=row['status'],reason=row.get('reason'),area_mm2=row.get('delta_area_mm2'),complete_faces=row.get('extension_complete_faces'),original_source_mesh=case(row['reference'])['mesh'],evidence='figures/Fig8_G01_F1_F2_F3_full_and_zoom.png'if sid.startswith('G01')else'figures/Fig'+str({'G06_004':4,'G07_004':5,'G08_005':6}[sid])+'_'+sid+'_incremental_growth.png',rejected_means='not admitted to this growth output; all raw data preserved',scientific_accuracy='NOT_CERTIFIED'))
        status_counts.append(dict(scene=sid,condition=case(cid)['condition'],**counts,denominator='candidate-component attempts, repeated at updated frontiers; not independent cases or detection accuracy'))
        for version,blocks in [('S0',load_scene(sid,0)),('Final',load_scene(sid))]:
            f=frontier(blocks);P=f['midpoints'];N=len(P);support=np.zeros(N,int);frames=[v for v in views().values()if v['source_id']==sid.replace('_','_video',1)and v['id']not in eval_ids];edge_reference=np.array([blocks[j]['reference']for j in f['blocks']]);edge_source_view=np.array([view_for(ref)['id']for ref in edge_reference]);camera_centers=np.array([source(ref)['p']['pose'][:3,3]for ref in edge_reference]);directions=camera_centers-P;directions/=np.maximum(np.linalg.norm(directions,axis=1)[:,None],1e-12)
            for v in frames:support+=additional_mask_support(P,dict(v,ring_case=cid))&(edge_source_view!=v['id'])
            covered=np.zeros(N,bool)
            for bi,b in enumerate(blocks):
                ix=np.flatnonzero(f['blocks']==bi);other=[x for x in blocks if x['reference']!=b['reference']]
                if not len(ix)or not other:continue
                a=mesh_arrays(other);t=target_source(b['reference']);ray=raymesh(a['P'],a['F'],t);uv,z=vis.project_camera(P[ix],t['K'],t['c2w']);xy=np.floor(uv+.5).astype(int);ok=(z>0)&(xy[:,0]>=0)&(xy[:,0]<640)&(xy[:,1]>=0)&(xy[:,1]<360);q=np.flatnonzero(ok);u,v=xy[q].T;hit=ray['valid'][v,u]&(abs(z[q]-ray['z'][v,u])<=depth_tau(z[q],t['K']));covered[ix[q[hit]]]=True
            path=R/f'local_results/frontier_support/{sid}_{version}.npz';path.parent.mkdir(exist_ok=True);np.savez_compressed(path,XYZ_midpoints=P,XYZ_edges=f['XYZ_edges'],length_mm=f['lengths'],category=f['categories'],eligible=f['eligible'],source_block_index=f['blocks'],source_reference=edge_reference,source_view_id=edge_source_view,source_camera_unit_direction=directions,non_eval_OTHER_frame_Mask_support_count=support,non_eval_frame_ids=np.array([v['id']for v in frames]),co_projected_other_source_triangle=covered,unit='mm',GT_used=False)
            fr=frontiers.append(dict(scene=sid,version=version,source_boundary_length_mm=f['total_length_mm'],eligible_source_boundary_length_mm=f['eligible_length_mm'],eligible_with_other_frame_Mask_support_mm=float(f['lengths'][f['eligible']&(support>0)].sum()),eligible_co_projected_on_other_source_triangle_mm=float(f['lengths'][f['eligible']&covered].sum()),remaining_uncovered_eligible_length_proxy_mm=float(f['lengths'][f['eligible']&~covered].sum()),edge_N=N,source_XYZ_path=str(path),identity='sum of original-source boundary lengths; seams may be counted more than once; not object perimeter or physical truth'))
        blocks=load_scene(sid)
        for ref in sorted(set(b['reference']for b in blocks)):
            s=source(ref);fids=np.array(sorted({int(f)for b in blocks if b['reference']==ref for f,g in zip(b['face_ids'],b['face_generations'])if g>0}),int);ids=np.unique(s['F'][fids]);keep=np.zeros(len(s['P']),bool);keep[ids]=True;possible=cleaned(ref)['protected_possible_stalk'];stalk.append(dict(scene=sid,reference=ref,possible_stalk_proxy_source_N=int(possible.sum()),possible_stalk_proxy_new_face_vertex_N=int((possible&keep).sum()),not_true_anatomical_labels=True))
            if sid.startswith('G01')and len(fids):
                _,labels,head=source_components(s['p'],s['uv']);headmask=labels==head;ring=cv2.distanceTransform((s['p']['labels']!=2).astype(np.uint8),cv2.DIST_L2,5)[s['uv'][:,1],s['uv'][:,0]]<=3
                for name,mask in [('head_source_Mask_component_proxy',headmask),('possible_stalk_proxy',possible),('Ring_near_3px_proxy',ring)]:
                    selected=mask[s['F'][fids]].any(1);regions.append(dict(scene=sid,reference=ref,region=name,accepted_new_face_N=int(selected.sum()),new_complete_face_area_exposure_mm2=float(s['areas'][fids[selected]].sum()),source_component_new_face_denominator=len(fids),categories_overlap=True,clinical_region_status='UNKNOWN_MANUAL_CONFIRMATION_REQUIRED'))
        print('REVIEW AUDIT',sid,counts,flush=True)
    both('patch_review_ledger',ledger);both('review_status_by_scene',status_counts);both('frontier_support_summary',frontiers);both('G01_region_support',regions);both('possible_stalk_source_preservation',stalk)
if __name__=='__main__':main()
