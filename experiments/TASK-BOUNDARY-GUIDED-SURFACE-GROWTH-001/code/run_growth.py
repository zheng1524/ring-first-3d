"""Actual incremental frontier update / reference search / frozen HERO loop."""
from growth import *
from hero_adapter import infer,pose_of
def choose_new_views(sid,blocks,attempted):
    current=[view_for(c['id'])for c in cases()if sceneid(c)==sid];held=set(load(R/'provenance/EVALUATION_TARGETS_FROZEN.json')['target_ids']);fr=frontier(blocks);ix=np.flatnonzero(fr['eligible']);P=fr['midpoints'][ix];L=fr['lengths'][ix];primary=load(R/'provenance/MAIN_SURFACES_SELECTED.json')['selections'][sid];rows=[]
    for v in views().values():
        if v['type']!='video'or v['source_id']!=sid.replace('_','_video',1):continue
        reason=None
        if v['id']in held:reason='FROZEN_EVALUATION_FRAME'
        elif v['id']in attempted or any(x['id']==v['id']for x in current):reason='REFERENCE_ALREADY_PROCESSED'
        gap=min(angle(np.array(v['view_direction']),np.array(x['view_direction']))for x in current)
        if not reason and gap<cfg()['growth_min_direction_novelty_deg']:reason='NO_RESOLVABLE_NEW_DIRECTION_AT_FROZEN_3DEG_RULE'
        support=additional_mask_support(P,dict(v,ring_case=primary))if len(P)else np.zeros(0,bool);visible=float(L[support].sum());quality=1.0 if v['pose_status']in['VALIDATED','LOCAL_GEOMETRY_SCREENED']else .75
        if not reason and visible<=0:reason='NO_VISIBLE_CURRENT_FRONTIER'
        rows.append(dict(scene=sid,view=v['id'],direction_gap_deg=gap,visible_frontier_mm=visible,pose_status=v['pose_status'],score=visible*(.25+np.sin(np.deg2rad(min(gap,60))))*quality,status='ELIGIBLE'if not reason else reason))
    ordered=sorted([r for r in rows if r['status']=='ELIGIBLE'],key=lambda x:-x['score']);return ordered,rows
def source_views(v):
    held=set(load(R/'provenance/EVALUATION_TARGETS_FROZEN.json')['target_ids']);vv=[x for x in views().values()if x['source_id']==v['source_id']and x['id']!=v['id']and x['id']not in held];vv.sort(key=lambda w:(w['pose_status']not in ['VALIDATED','LOCAL_GEOMETRY_SCREENED'],abs(angle(np.array(w['view_direction']),np.array(v['view_direction']))-7)));return vv[:3]
def run(sid):
    snapshots=sorted((R/'local_results/scenes').glob(sid+'_S[0-9][0-9][0-9].json'));latest=load(snapshots[-1]);blocks=latest['blocks'];round_id=int(latest['step'])+1;records=load(R/f'metrics/growth_steps_{sid}.json')if(R/f'metrics/growth_steps_{sid}.json').exists()else[];candidate_records=load(R/f'metrics/patch_candidates_{sid}.json')if(R/f'metrics/patch_candidates_{sid}.json').exists()else[];view_records=load(R/f'metrics/view_search_{sid}.json')if(R/f'metrics/view_search_{sid}.json').exists()else[];previous_HERO=load(R/'metrics/new_HERO_sources.json')if(R/'metrics/new_HERO_sources.json').exists()else[];previous_HERO=[x for x in previous_HERO if x['group']+'_'+x['video']==sid];attempted={x['reference_view']for x in previous_HERO};no_gain=0;new_count=len(previous_HERO);stop=None
    checkpoint=R/f'local_results/scenes/{sid}_CHECKPOINT.json'
    if checkpoint.exists():no_gain=load(checkpoint).get('consecutive_new_reference_no_gain',0)
    if len(records)<round_id-1:
        for path in snapshots[1:]:
            snap=load(path)
            if snap['step']>len(records):records.append(dict(snap['record'],snapshot=path.stem,resume_recovered_snapshot=True))
    while True:
        accepted=None;rank=rank_references(sid,blocks)
        for c in rank:
            updated,rows=attempt_reference(blocks,c['reference'],round_id)
            for r in rows:r.update(scene=sid,round_attempt=round_id,source_search='EXISTING_CLEANED_F1_COMPLETE_SURFACES')
            candidate_records+=rows
            if updated is not None:accepted=next(r for r in rows if r['accepted']);break
        if accepted is None:
            both('patch_candidates_'+sid,candidate_records)
            choices,allviews=choose_new_views(sid,blocks,attempted)
            for r in allviews:r.update(round_attempt=round_id)
            view_records+=allviews
            if not choices:stop='NO_VALID_NEW_VIEW'if any(r['status']=='NO_RESOLVABLE_NEW_DIRECTION_AT_FROZEN_3DEG_RULE'for r in allviews)else'DATA_EXHAUSTED';break
            v=views()[choices[0]['view']];attempted.add(v['id']);src=source_views(v)
            if len(src)<3:stop='NO_VALID_NEW_VIEW_INSUFFICIENT_SOURCE_CAMERAS';break
            frozen=R/f'provenance/new_reference_step_{sid}_{new_count:02d}.json';save(str(frozen.relative_to(R)),dict(reference=v,source_views=src,selection=choices[0],rule='current frontier visibility plus angular novelty before HERO and image error',GT_used=False));cid=infer(v,src,round_id);new_count+=1
            if cid:
                updated,rows=attempt_reference(blocks,cid,round_id)
                for r in rows:r.update(scene=sid,round_attempt=round_id,source_search='NEW_HERO_FROM_CURRENT_FRONTIER')
                candidate_records+=rows
                if updated is not None:accepted=next(r for r in rows if r['accepted'])
            if accepted is None:
                no_gain+=1;save(str(checkpoint.relative_to(R)),dict(consecutive_new_reference_no_gain=no_gain,round_next=round_id));print('NO PATCH',sid,v['id'],'consecutive',no_gain,flush=True)
                if no_gain>=cfg()['growth_stop_after_consecutive_new_reference_no_gain']:stop='PATCH_REJECTED_CONSECUTIVE_NEW_VIEW_NO_ACCEPTABLE_GAIN';break
                continue
        no_gain=0;save(str(checkpoint.relative_to(R)),dict(consecutive_new_reference_no_gain=0,round_next=round_id+1));previous=copy.deepcopy(blocks);blocks=updated;accepted=dict(accepted);accepted.pop('extension_original_face_ids',None);f0=frontier(previous);tag,f1=snapshot(sid,round_id,blocks,accepted);record=dict(accepted,frontier_before_mm=f0['total_length_mm'],frontier_after_mm=f1['total_length_mm'],eligible_frontier_after_mm=f1['eligible_length_mm'],snapshot=tag);records.append(record);save(f'local_results/scenes/{sid}_S{round_id:03d}_PreJoint.json',dict(scene=sid,step=round_id,before_blocks=previous,registration=accepted.get('joint_alignment',{}),new_source=c['reference']if accepted.get('reference')is None else accepted['reference'],note='same selected new patch; old/new component transforms before the proposed joint alignment are reconstructable from previous scene and candidate_H/old_delta/new_delta'))
        print('ACCEPT',sid,'S'+str(round_id),accepted['reference'],'faces',accepted['extension_complete_faces'],'area',round(accepted['delta_area_mm2'],4),'joint',accepted['joint_alignment'].get('accepted',False),flush=True);round_id+=1;both('growth_steps_'+sid,records);both('patch_candidates_'+sid,candidate_records);both('view_search_'+sid,view_records)
    save(f'local_results/scenes/{sid}_Final.json',dict(scene=sid,blocks=blocks,accepted_steps=round_id-1,stop_reason=stop,new_HERO_attempts=new_count,GT_used=False));both('growth_steps_'+sid,records);both('patch_candidates_'+sid,candidate_records);both('view_search_'+sid,view_records);summary=dict(scene=sid,group=sid[:3],accepted_steps=round_id-1,new_HERO_attempts=new_count,delta_complete_original_face_area_mm2=sum(r['delta_area_mm2']for r in records),stop_reason=stop,status='ENGINEERING_GROWTH_CANDIDATE_NOT_PHYSICAL_GT',condition=case(blocks[0]['reference'])['condition']);save(f'metrics/summary_{sid}.json',summary);print('SCENE DONE',summary,flush=True)
def main():
    verify();path=R/'provenance/GROWTH_IMPLEMENTATION_FROZEN.json'
    if not path.exists():save(str(path.relative_to(R)),stamp([R/'code'/x for x in ['assets.py','frontier.py','growth.py','hero_adapter.py','run_growth.py']]+[R/'config/growth_rules.json',R/'provenance/EVALUATION_TARGETS_FROZEN.json'],before_growth=True,latest_user_revision_applied=True,GT_used=False))
    elif any(sha(f['path'])!=f['sha256']for f in load(path)['files']):
        current=stamp([Path(f['path'])for f in load(path)['files']],revision_reason='source ID adapter, resume/checkpoint safety and condition-based quality naming; no acceptance rule or threshold change',GT_used=False)
        revisions=sorted((R/'provenance').glob('GROWTH_IMPLEMENTATION_REVISION_*.json'))
        if not revisions or load(revisions[-1])['files']!=current['files']:save('provenance/GROWTH_IMPLEMENTATION_REVISION_'+str(len(revisions)+1).zfill(3)+'.json',current)
    for sid in sys.argv[1:]or['G06_004','G07_004','G08_005','G01_004','G01_005']:
        if(R/f'local_results/scenes/{sid}_Final.json').exists():print('PRESERVE EXISTING FINAL',sid,flush=True);continue
        run(sid)
if __name__=='__main__':main()
