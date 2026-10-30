"""Read-only legacy reuse, seed recovery and independently selected main surface."""
from geometry import *
@lru_cache(None)
def cleaned(cid):return np.load(R/f'local_results/cleaned/{cid}.npz')
def views():return {v['id']:v for v in load(BASE/'metrics/view_distribution.json')}
def view_for(cid):
    c=case(cid);return next(v for v in views().values()if v['group']==c['group']and v.get('index')==c['reference_index']and v['source_id']==c['group']+'_video'+c['video'])
@lru_cache(None)
def normal(cid):
    s=source(cid);P,F=s['P'],s['F'];v=np.cross(P[F[:,1]]-P[F[:,0]],P[F[:,2]]-P[F[:,0]]);N=np.zeros_like(P);mass=np.zeros(len(P));degree=np.zeros(len(P),int)
    for j in range(3):np.add.at(N,F[:,j],v);np.add.at(mass,F[:,j],np.linalg.norm(v,axis=1));np.add.at(degree,F[:,j],1)
    length=np.linalg.norm(N,axis=1);N=np.divide(N,length[:,None],out=np.zeros_like(P),where=length[:,None]>0);flip=(N*(s['p']['pose'][:3,3]-P)).sum(1)<0;N[flip]*=-1;coh=np.divide(length,mass,out=np.zeros(len(P)),where=mass>0)
    return N,(degree>=3)&(coh>=.85)&(length>0)
def clean_faces(cid):
    s=source(cid);return np.flatnonzero(~cleaned(cid)['clean_removed'][s['F']].any(1))
def face_partitions(cid,face_ids=None):
    s=source(cid);ids=clean_faces(cid)if face_ids is None else np.asarray(face_ids,int)
    if not len(ids):return []
    labels=face_components(s['F'][ids]);return [ids[labels==k]for k in np.unique(labels)]
def train_neighbor(cid):
    c=case(cid);v=view_for(cid);vv=[x for x in views().values()if x['source_id']==v['source_id']and x.get('role')!='HOLDOUT'and x['id']!=v['id']and x['id']not in load(R/'provenance/EVALUATION_TARGETS_FROZEN.json').get('target_ids',[])]
    vv.sort(key=lambda x:angle(np.array(x['view_direction']),np.array(v['view_direction'])));w=vv[0]if vv else v
    return dict(w,id=w['id'],ring_case=cid)
def old_F2(cid):
    return np.load(BASE/f'local_results/pointcloud_blocks/{sceneid(case(cid))}/ViewPartition_Cleaned_F2/{cid}.npz')
def initialize():
    assert not(R/'provenance/INPUTS_FROZEN.json').exists()
    protected=load(BASE/'runtime/PROTECTED_START.json');roots=list(protected)+[str(BASE.parents[1])];save('runtime/PROTECTED_START.json',{p:state(Path(p))for p in roots})
    all_inputs=[R/'TASK.md',R/'USER_STEERING.md',R/'config/growth_rules.json',BASE/'provenance/FINAL_CODE_AND_SOURCE_MANIFEST.json',BASE/'provenance/F2_GEOMETRY_FROZEN.json',BASE/'metrics/view_distribution.json',BASE/'metrics/registration_edges.json'];seedrows=[]
    for c in cases():
        s=source(c['id']);all_inputs +=[Path(c[k])for k in ['RGB','Mask','pack','mesh','source_points','camera_file']]+[R/f'local_results/cleaned/{c["id"]}.npz',BASE/f'local_results/pointcloud_blocks/{sceneid(c)}/ViewPartition_Cleaned_F2/{c["id"]}.npz',ring_path(c)]
        if c['group']in ['G06','G07','G08']and c.get('new_reference'):
            z=old_F2(c['id']);take=z['accepted'];ids=np.flatnonzero(take);fid=np.flatnonzero(take[s['F']].all(1));path=R/f'local_results/engineering_seed/{c["id"]}.npz';path.parent.mkdir(exist_ok=True);np.savez_compressed(path,XYZ_mm=s['P'],RGB=s['C'],source_uv=s['uv'],accepted_original_point_ids=ids,accepted_original_face_ids=fid,original_faces=s['F'],H_source_to_scene=np.eye(4),status='ENGINEERING_ACCEPTED_SEED_NOT_PHYSICAL_GT',adjustable_derived_geometry=True,originals_immutable=True)
            seedrows.append(dict(group=c['group'],source=c['id'],Cleaned_F1_source_points=int((~cleaned(c['id'])['clean_removed']).sum()),F2_accepted_points=len(ids),F2_complete_original_faces=len(fid),F2_complete_original_face_area_mm2=float(s['areas'][fid].sum()),face_components=len(face_partitions(c['id'],fid)),status='ENGINEERING_ACCEPTED_SEED',camera_condition=c['condition'],physical_accuracy='NOT_CERTIFIED',path=str(path),sha256=sha(path),new_user_revision_allows_derived_adjustment=True))
    both('engineering_seeds',seedrows)
    # Evaluation references are held before geometric scoring/growth. Source
    # history is audited explicitly, not silently called whole-pipeline blind.
    targets=[];unavailable=[]
    for sid in dict.fromkeys(sceneid(c)for c in cases()):
        cc=[c for c in cases()if sceneid(c)==sid];vv=[v for v in views().values()if v['source_id']==sid.replace('_','_video',1)and v.get('pose_known')];refhash={sha(c['RGB'])for c in cc};used=set();unknown=False
        for c in cc:
            p=source(c['id'])['p']
            if'sources'not in p:unknown=True;continue
            for x in p['sources']:
                if isinstance(x,(np.integer,int)):used|={v['id']for v in vv if v['index']==int(x)}
                else:used.add(str(x))
        pool=[v for v in vv if sha(v['RGB'])not in refhash];strict=[v for v in pool if v['id']not in used];pool=strict or pool
        if not pool:unavailable.append(dict(scene=sid,reason='NO_NON_REFERENCE_FRAME_WITH_FROZEN_POSE'));continue
        # Largest and median direction separation from archived main, no RGB error.
        anchor=view_for(cc[0]['id']);pool.sort(key=lambda v:angle(np.array(v['view_direction']),np.array(anchor['view_direction'])));chosen=[pool[-1]]
        if len(pool)>1:chosen.append(pool[len(pool)//2])
        chosen=list({v['id']:v for v in chosen}.values())
        for v in chosen:
            role='NON_REFERENCE_AND_NOT_KNOWN_HERO_SOURCE'if v['id']not in used else'NON_REFERENCE_BUT_KNOWN_HISTORICAL_HERO_SOURCE'
            if unknown:role+='; HISTORICAL_HERO_SOURCE_LIST_PARTLY_UNRECORDED'
            targets.append(dict(scene=sid,target=v['id'],view=v,role=role,source_geometry_RGB_distinct=True,condition=cc[0]['condition'],whole_pipeline_blind=False))
    save('provenance/EVALUATION_TARGETS_FROZEN.json',dict(targets=targets,target_ids=[x['target']for x in targets],unavailable=unavailable,selection='direction extremes/median before growth; exclude every known source ref, prefer frames not known as historical HERO sources',GT_used=False))
    save('provenance/INPUTS_FROZEN.json',stamp(all_inputs,base_commit='4adfe3aac780bf319aebf9cdd137f42e1e0eb055',GT_used=False,latest_user_revision='derived old/new geometry may jointly move; raw assets and controls remain immutable'))
    audit=[dict(source=str(BASE/'code'/n),sha256=sha(BASE/'code'/n),reuse='bounded wrapper/source reuse; R rebound; no network/backproject/render reimplementation')for n in ['common.py','geometry.py','render.py','hero_new.py','ownership.py','render_d.py']];save('provenance/CODE_REUSE.json',audit)
    main_selection()
    print('P0 recovery complete',len(seedrows),'seed sources /14 refs /4 physical groups',flush=True)
def main_selection():
    rows=[];selections={}
    for sid in dict.fromkeys(sceneid(c)for c in cases()):
        rr=[]
        for c in cases():
            if sceneid(c)!=sid:continue
            s=source(c['id']);fids=clean_faces(c['id']);F=s['F'][fids];parts=face_partitions(c['id']);largest=max(parts,key=lambda ids:s['areas'][ids].sum());ids=np.unique(s['F'][largest]);support=additional_mask_support(s['P'][ids],train_neighbor(c['id']));norm,reliable=normal(c['id']);w=vertex_area(s['P'],s['F'][largest])[ids];supported_area=float(w[support&reliable[ids]].sum());total=float(s['areas'][fids].sum());quality=1. if c['source_camera_qualified']else .75;quality=.5 if'UNQUALIFIED'in c['condition']else quality
            rr.append(dict(scene=sid,reference=c['id'],largest_complete_source_component_mm2=float(s['areas'][largest].sum()),credible_continuous_area_proxy_mm2=supported_area,continuity=float(s['areas'][largest].sum()/total),training_neighbor=train_neighbor(c['id'])['id'],training_Mask_support=float(support.mean()),normal_reliable_fraction=float(reliable[ids].mean()),camera_quality_factor=quality,camera_condition=c['condition'],main_face_ids=largest))
        scale=max(x['credible_continuous_area_proxy_mm2']for x in rr)
        for x in rr:
            x['score']=x['camera_quality_factor']*(.55*x['credible_continuous_area_proxy_mm2']/max(scale,1e-9)+.2*x['continuity']+.15*x['training_Mask_support']+.1*x['normal_reliable_fraction']);x.pop('main_face_ids')
        win=max(rr,key=lambda x:(x['score'],x['credible_continuous_area_proxy_mm2']));selections[sid]=win['reference'];rows+=rr
    both('main_surface_scores',rows);save('provenance/MAIN_SURFACES_SELECTED.json',dict(selections=selections,rule='quality-weighted largest continuous original-face supported area (55%), continuity20%, non-held neighbor Mask15%, normal10%; no GT or held RGB error',stage='before growth',GT_used=False));print('MAIN',selections,flush=True)
if __name__=='__main__':initialize()
