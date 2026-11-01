"""Fixed-cohort REP->ALL observation ablations and complete source evidence."""
from visibility import *
from collections import Counter
REASON_BITS={1:'INVALID_PROJECTION_OR_NATIVE_DEPTH',2:'NON_POLYP_MASK',4:'CAD_OCCLUDED',8:'NATIVE_FIRST_DEPTH_BEHIND_CAD',16:'TARGET_NATIVE_RAW_DISAGREEMENT',32:'NATIVE_ONLY_FREE_RESPONSE',64:'TARGET_FIRST_FACE_QUALITY_UNQUALIFIED',128:'MASK_OR_RING_EDGE_UNCERTAINTY',256:'ORIGIN_NOT_LEGALLY_VISIBLE',512:'B1_NEAREST_OR_NATIVE_AMBIGUITY',1024:'NORMAL_COMPATIBILITY_UNRESOLVED',2048:'ORIGIN_NATIVE_RAW_DISAGREEMENT'}
def compact(v):
    if isinstance(v,(float,np.floating)):return ''if not np.isfinite(v)else format(float(v),'.8g')
    if isinstance(v,(bool,np.bool_)):return int(v)
    if isinstance(v,(int,np.integer)):return int(v)
    return v
def export_stage(stage):
    agg={};per_source=[];strata=[]
    for sid in scene_ids():
        agg[sid]={}
        for variant in range(4):
            totals=Counter();nall=0;ss=oo=ff=cs=co=cf=0.
            for origin in ordered_sources(sid):
                c=candidates(origin);r=reduce(origin,stage,variant);n=len(c['face_id']);counts=Counter(r['label'].tolist());totals.update(counts);nall+=n
                folder=R/'local_results/reduced';folder.mkdir(exist_ok=True);np.savez_compressed(folder/f'{origin}__{stage}__V{variant}.npz',**r)
                per_source.append(dict(stage=stage,variant='V'+str(variant),scene=sid,source_id=origin,candidate_N=n,observer_N=r['observer_N'],**dict(counts),
                    mean_raw_S_sum=float(r['rawS'].sum()/n),mean_raw_O_sum=float(r['rawO'].sum()/n),mean_raw_F_sum=float(r['rawF'].sum()/n),
                    mean_corr_S_sum=float(r['normS'].sum()/n),mean_corr_O_sum=float(r['normO'].sum()/n),mean_corr_F_sum=float(r['normF'].sum()/n),correlation_vote_mass=r['vote_mass'],
                    source_unique_candidate_N=int(((c['tags']&8)!=0).sum()),all_candidate_geometries_retained_N=n,physical_truth='UNRESOLVED'))
                ss+=r['rawS'].sum();oo+=r['rawO'].sum();ff+=r['rawF'].sum();cs+=r['normS'].sum();co+=r['normO'].sum();cf+=r['normF'].sum()
                for name,mask in dict(ALL=np.ones(n,bool),CO_VISIBLE_SMOOTH_PROXY=c['own_visible']&((c['tags']&128)!=0)&((c['tags']&8)==0)&(r['valid']>0),STRETCH_PROXY=(c['tags']&16)!=0,SOURCE_UNIQUE_PROXY=(c['tags']&8)!=0,POSSIBLE_STALK_PROXY=(c['tags']&256)!=0).items():
                    den=int(mask.sum());strata.append(dict(stage=stage,variant='V'+str(variant),scene=sid,source_id=origin,stratum=name,candidate_N=den,
                        any_valid_other_source_N=int((mask&(r['valid']>0)).sum()),any_external_support_N=int((mask&(r['support']>0)).sum()),any_free_proxy_N=int((mask&(r['free']>0)).sum()),
                        no_admissible_opposition_N=int((mask&(r['free']==0)).sum()),unknown_or_unresolved_N=int((mask&np.isin(r['label'],['UNKNOWN','CORRESPONDENCE_UNRESOLVED'])).sum()),
                        support_response_sum=float(r['rawS'][mask].sum()),corr_support_response_sum=float(r['normS'][mask].sum()),observer_N=r['observer_N'],all_geometries_retained_N=den))
            agg[sid]['V'+str(variant)]=dict(candidate_N=nall,class_counts=dict(totals),raw_channel_mean=dict(S=ss/nall,O=oo/nall,F=ff/nall),correlation_normalized_channel_mean=dict(S=cs/nall,O=co/nall,F=cf/nall),all_candidates_retained_N=nall,
                semantics='evidence proxies, not physical correctness; numeric-only V0 Support is not qualified physical support')
    table('metrics/'+stage+'_SOURCE_ABLATION.csv',per_source);table('metrics/'+stage+'_STRATUM_RESULTS.csv',strata);save('provenance/'+stage+'_ABLATION.json',agg);return agg
def reduced(origin,stage='ALL_OBSERVERS',variant=3):
    z=np.load(R/'local_results/reduced'/f'{origin}__{stage}__V{variant}.npz');return {k:z[k]for k in z.files}
def export_tables():
    evidence=[];matrix=[];conflicts=[];changes=[]
    p=R/'metrics/OBSERVATION_SOURCE_EVIDENCE.csv.gz'
    header=['candidate_id','origin','original_face_id','observer','observer_original_first_face_id','delta_native_mm','delta_Raw_mm','pair_interval_halfwidth_mm','native_depth_mm','Raw_depth_mm','candidate_observer_Z_mm','S_numeric','O_numeric','F_numeric',
        'minimum_admissible','support_V0','support_V1','support_V3','behind_first_surface','CAD_occluded','free_proxy_V2','free_proxy_V3','native_only_free','target_native_Raw_agree','origin_native_Raw_agree','target_first_face_quality','mask_Ring_safe','strict_upstream_chain','reason_bits','upstream_RGB_Jaccard','correlation_weight_ALL','camera_quality_proxy']
    with gzip.open(p,'wt',newline='')as stream:
        writer=csv.writer(stream,lineterminator='\n');writer.writerow(header)
        for origin in IDS:
            c=candidates(origin);r=reduced(origin);rep=reduced(origin,'REP_OBSERVERS');v2=reduced(origin,variant=2);active=[b for b in stages(CC[origin]['scene_id'])['ALL_OBSERVERS']if b!=origin];weights=correlation_weights(origin,active);reason_or=np.zeros(len(c['face_id']),np.uint32)
            for observer in active:
                z=np.load(observer_file(origin,observer));q={k:z[k]for k in z.files};z.close();reason_or|=q['reason'];matrix.append(dict(origin=origin,observer=observer,scene=CC[origin]['scene_id'],candidate_N=len(c['face_id']),minimum_admissible_N=int(q['minimum'].sum()),Support_V0_N=int(q['support0'].sum()),Support_V1_N=int(q['support1'].sum()),Support_V3_N=int(q['support3'].sum()),
                    behind_first_surface_N=int(q['behind'].sum()),CAD_occluded_N=int(q['cad'].sum()),free_proxy_V2_N=int(q['native_free'].sum()),free_proxy_V3_N=int(q['free3'].sum()),native_only_free_N=int(q['native_only'].sum()),native_Raw_disagreement_N=int((q['numeric']&~q['align']).sum()),
                    shared_RGB_N=len(parent_hashes(origin)&parent_hashes(observer)),RGB_Jaccard=jaccard(origin,observer),source_family=source(origin)['row']['source_family'],correlation_weight=weights[observer],camera_quality_proxy=float(q['qcam'][0]),
                    mean_raw_S=float(q['S'][q['minimum']].sum()/len(c['face_id'])),mean_corr_S=float((q['S']*q['minimum']*q['qcam']*weights[observer]).sum()/len(c['face_id'])),physical_same_surface_certified_N=0))
                for j,fid in enumerate(c['face_id']):
                    row=[origin+':'+str(fid),origin,int(fid),observer,int(q['observer_first_face_id'][j]),q['delta'][j],q['raw_delta'][j],q['tau'][j],q['D'][j],q['M'][j],q['z'][j],q['S'][j],q['O'][j],q['F'][j],q['minimum'][j],q['support0'][j],q['support1'][j],q['support3'][j],q['behind'][j],q['cad'][j],q['native_free'][j],q['free3'][j],q['native_only'][j],q['align'][j],q['origin_align'][j],q['target_quality'][j],q['mask_safe'][j],q['strict_chain'][j],int(q['reason'][j]),jaccard(origin,observer),weights[observer],q['qcam'][j]]
                    writer.writerow([compact(x)for x in row])
                    if q['native_free'][j]:conflicts.append(dict(candidate_id=origin+':'+str(fid),source_id=origin,original_face_id=int(fid),observer=observer,delta_native_mm=q['delta'][j],delta_Raw_mm=q['raw_delta'][j],interval_halfwidth_mm=q['tau'][j],
                        free_V2_proxy=True,free_V3_admissible_proxy=bool(q['free3'][j]),native_only=bool(q['native_only'][j]),native_Raw_agreement=bool(q['align'][j]),origin_native_Raw_agreement=bool(q['origin_align'][j]),target_quality=bool(q['target_quality'][j]),Mask_Ring_safe=bool(q['mask_safe'][j]),
                        strict_chain=bool(q['strict_chain'][j]),source_unique_proxy=bool(c['tags'][j]&8),stretch_proxy=bool(c['tags'][j]&16),reason_bits=int(q['reason'][j]),geometry_retained=True,physical_error_truth='UNRESOLVED'))
            for j,fid in enumerate(c['face_id']):
                evidence.append(dict(candidate_id=origin+':'+str(fid),source_id=origin,original_face_id=int(fid),scene=CC[origin]['scene_id'],role=ROLES[origin],X_mm=c['XYZ'][j,0],Y_mm=c['XYZ'][j,1],Z_mm=c['XYZ'][j,2],normal_x=c['normal'][j,0],normal_y=c['normal'][j,1],normal_z=c['normal'][j,2],sample_tags=int(c['tags'][j]),
                    own_visible=bool(c['own_visible'][j]),source_unique_proxy=bool(c['tags'][j]&8),observer_N=int(r['observer_N']),valid_source_count=int(r['valid'][j]),unknown_source_count=int(r['unknown'][j]),Support_count=int(r['support'][j]),Occlusion_count=int(r['occluded'][j]),CAD_source_count=int(r['cad'][j]),Free_space_violation_proxy_count=int(r['free'][j]),
                    V2_native_free_proxy_count=int(v2['free'][j]),strict_chain_free_proxy_count=int(r['strictfree'][j]),raw_S=float(r['rawS'][j]),raw_O=float(r['rawO'][j]),raw_F=float(r['rawF'][j]),correlation_S=float(r['normS'][j]),correlation_O=float(r['normO'][j]),correlation_F=float(r['normF'][j]),
                    source_family=source(origin)['row']['source_family'],correlation_vote_mass=float(r['vote_mass']),reason_bits=int(reason_or[j]),evidence_class=r['label'][j],geometry_retained=True,physical_truth='UNRESOLVED'))
                if rep['label'][j]!=r['label'][j]or rep['support'][j]!=r['support'][j]or rep['free'][j]!=r['free'][j]:changes.append(dict(candidate_id=origin+':'+str(fid),source_id=origin,original_face_id=int(fid),REP_class=rep['label'][j],ALL_class=r['label'][j],REP_Support_N=int(rep['support'][j]),ALL_Support_N=int(r['support'][j]),REP_free_N=int(rep['free'][j]),ALL_free_N=int(r['free'][j]),candidate_position_unchanged=True))
    def small_table(name,data):
        keys=list(dict.fromkeys(k for r in data for k in r));path=R/name
        with path.open('w',newline='')as f:
            w=csv.writer(f,lineterminator='\n');w.writerow(keys)
            for r in data:w.writerow([compact(r.get(k,''))for k in keys])
    small_table('VISIBILITY_EVIDENCE.csv',evidence);small_table('SOURCE_SUPPORT_MATRIX.csv',matrix);small_table('FREE_SPACE_CONFLICTS.csv',conflicts);small_table('metrics/OBSERVER_STAGE_CHANGES.csv',changes)
    save('provenance/EVIDENCE_REASON_BITS.json',REASON_BITS);save('provenance/EVIDENCE_TABLE_INDEX.json',dict(candidate_N=len(evidence),directed_pair_N=len(matrix),native_free_candidate_observer_N=len(conflicts),stage_changes_N=len(changes),
        per_observer_table=asset(p),rounding='CSV .8g for compact review; unrounded arrays local, exact code/protocol reproduces decisions',physical_truth='not available; all classifications are geometric evidence proxies'))
def main():
    allow_manifest();freeze('BEFORE_OBSERVATIONS.json');start=time.monotonic();nrep=calculate_stage('REP_OBSERVERS');rep=export_stage('REP_OBSERVERS');save('provenance/REP_STAGE_COMPLETE.json',dict(queries=nrep,seconds=time.monotonic()-start,completed_before_RESERVED_observations=True))
    nall=calculate_stage('ALL_OBSERVERS');allresults=export_stage('ALL_OBSERVERS');export_tables();save('V0_V3_ABLATION.json',dict(REP_OBSERVERS=rep,ALL_OBSERVERS=allresults,
        candidate_denominator='fixed all17 source candidate centroids in both stages; original own-source anchors invariant, self never an external observer',source_selection='unchanged E3-A roles',
        physical_group_N=3,video_N=4,G07='UNQUALIFIED_STRESS_IDENTITY_ONLY_NOT_IN_FORMAL_NUMERIC_SUCCESS_RATE',minimum_free_gates_always_used=True,
        ring_ablation_limit='CAD already present in inherited B0: V2 also uses mandatory CAD gate; V3 adds stricter masks/local-quality/correlation, not an intentionally unsafe CAD-free baseline'))
    save('provenance/CONSENSUS_RUN_STATUS.json',dict(total_candidate_observer_queries=nrep+nall,REP_queries=nrep,RESERVED_added_queries=nall,seconds=time.monotonic()-start,
        total_raw_faces=461023,deleted_faces=0,moved_faces=0,new_depth_predictions=0,GPU=0,global_field_fit=0,VFUSE_CNN=False));print('E3C_CONSENSUS_COMPLETE',nrep+nall,flush=True)
def resume_export():
    allow_manifest();start=time.monotonic();rep=load(R/'provenance/REP_OBSERVERS_ABLATION.json');allresults=load(R/'provenance/ALL_OBSERVERS_ABLATION.json');export_tables()
    save('V0_V3_ABLATION.json',dict(REP_OBSERVERS=rep,ALL_OBSERVERS=allresults,candidate_denominator='fixed all17 candidates and invariant own-source anchors; self never an external observer',source_selection='unchanged E3-A roles',physical_group_N=3,video_N=4,
        G07='UNQUALIFIED_STRESS_IDENTITY_ONLY_NOT_IN_FORMAL_NUMERIC_SUCCESS_RATE',minimum_free_gates_always_used=True,ring_ablation_limit='inherited B0 already includes CAD; V2 minimum CAD gate retained, V3 adds stricter Ring/Mask/local-quality/correlation gates'))
    nrep=sum(len(candidates(a)['face_id'])*(len(stages(CC[a]['scene_id'])['REP_OBSERVERS'])-(a in stages(CC[a]['scene_id'])['REP_OBSERVERS']))for a in IDS)
    ntotal=sum(len(candidates(a)['face_id'])*(len(scene_sources(CC[a]['scene_id']))-1)for a in IDS)
    save('provenance/CONSENSUS_RUN_STATUS.json',dict(total_candidate_observer_queries=ntotal,REP_queries=nrep,RESERVED_added_queries=ntotal-nrep,export_resume_seconds=time.monotonic()-start,resumed_export_only=True,field_queries_repeated_on_resume=False,
        total_raw_faces=461023,deleted_faces=0,moved_faces=0,new_depth_predictions=0,GPU=0,global_field_fit=0,VFUSE_CNN=False));print('E3C_EXPORT_RESUMED_COMPLETE',ntotal,flush=True)
if __name__=='__main__':resume_export()if'--export-only'in sys.argv else main()
