"""Qualify first, fit independent local singles, then only approved connected subsets."""
from common import *
from observations_revision import prepare_video,to_joint
from geometry import *
import time,traceback,argparse,copy,fcntl

def transform_parameter(p,M):
    p=np.array(p,float);c,Q,a=decode(p,np.eye(3));return np.r_[M[:3,:3]@c+M[:3,3],Rotation.from_matrix(M[:3,:3]@Q).as_rotvec(),np.log(a)]

def run_configuration(g,name,videos,qualification,seeds=()):
    from fit_revision import Problem,initialize,evaluate
    from base_revision import estimate
    from observations import CFG
    out=T/'runs/results'/g/name;out.mkdir(parents=True,exist_ok=True)
    key=digest(dict(config=CFG,code=revision_key(),inputs=[v['index'] for v in videos],transforms={v['case']:v['transform'] for v in videos},qualification=qualification,seeds=seeds))
    if (out/'COMPLETE.json').exists() and read(out/'COMPLETE.json').get('cache_key')==key:
        for item in read(out/'COMPLETE.json')['files']:asset(item['path'],item['sha256'])
        return read(out/'RESULT.json')
    fs=[f for v in videos for f in v['frames']];fitfs=[f for f in fs if f['role']=='FIT'];ss=[s for v in videos for s in v['sources']]
    p0,init=initialize(fitfs);b=np.zeros(len(ss));base=estimate(ss);plane=np.array(base['plane']) if base.get('apply') else None;start=time.monotonic();cad=videos[0]['cad']
    problem=Problem(fitfs,ss,p0,cad=cad)
    # All starts share p0 as prior reference and exactly the same full-stage observations.
    trials=[];solutions=[]
    for label,pseed in [('coarse_2D',p0),*[(f'single_{i}',np.array(p)) for i,p in enumerate(seeds)]]:
        pp,bb,logs=problem.solve(np.array(pseed).copy(),b.copy(),CFG['alternations'],'FULL_PARENT')
        cost=sum(problem.values(pp,bb).values());trials.append(dict(seed=label,initial_p=pseed,objective=cost,stages=logs,p=pp,b=bb));solutions.append((pp,bb,logs))
    best=int(np.argmin([x['objective'] for x in trials]));p,b,logs=solutions[best];parent=p.copy();parentb=b.copy()
    if plane is not None:
        problem=Problem(fitfs,ss,p0,plane,cad=cad);p,b,more=problem.solve(p,b,CFG['clipped_alternations'],'FIXED_BASE_CLIPPED');logs=logs+more
    V,F=body_mesh(p);PV,PF=body_mesh(parent)
    np.savez_compressed(out/'PARENT.npz',V=PV,F=PF,p=parent,b=parentb)
    np.savez_compressed(out/'FINAL_UNCUT.npz',V=V,F=F,p=p,b=b)
    geom=dict(V=V,F=F,F_solid=F,inferred_base_faces=np.zeros(len(F),bool),original_face_ID=np.arange(len(F)))
    if plane is not None:geom=clip(V,F,plane)
    np.savez_compressed(out/'BODY.npz',**geom,p=p,b=b)
    candidate_error=None
    if base.get('candidate') and plane is None:
        try:np.savez_compressed(out/'WEAK_BASE_CANDIDATE.npz',**clip(V,F,base['plane']))
        except Exception as exc:candidate_error=repr(exc)
    ev=evaluate(p,b,fs,ss,plane,cad=cad)
    save(out/'BASE.json',base);save(out/'STAGES.json',logs);save(out/'STARTS.json',dict(selected=best,rule='same_full_FIT_objective_fixed_prior_reference_no_held',reference=p0,trials=trials));save(out/'EVALUATION.json',ev)
    np.savez_compressed(out/'CORRECTED_OBSERVATIONS.npz',raw_X=np.concatenate([s['raw_X'] for s in ss]) if ss else np.empty((0,3)),corrected_X=np.concatenate([corrected_points(s['rays'],s['D'],b[i]) for i,s in enumerate(ss)]) if ss else np.empty((0,3)),source_index=np.concatenate([np.full(len(s['D']),i) for i,s in enumerate(ss)]) if ss else np.empty(0,int))
    means={role:np.mean([r['IoU'] for r in ev['projections'] if r['role']==role]) for role in ['FIT','HOLDOUT']}
    r=dict(group=g,configuration=name,status='COARSE_INIT_COMPLETE',input_kind='DXY_MASK_HERO' if ss else'DXY_MASK_2D_ONLY',coordinate_frame=videos[0]['coordinate_frame'],videos=[v['case'] for v in videos],video_transforms={v['case']:v['transform'] for v in videos},qualification=qualification,cache_key=key,scientific_key=revision_key(),config_sha256=sha(T/'config.json'),p=p,initial_p=p0,initialization=init,bias=[dict(source_id=s['meta']['source_id'],b_mm=float(b[i]),bound_mm=CFG['bias_bound_mm'],weight=float(problem.w[i]),uncertainty='bounded_estimate_not_absolute_depth_truth') for i,s in enumerate(ss)],base_status=base['status'],base_applied=plane is not None,candidate_error=candidate_error,fit_IoU_mean=means['FIT'],held_IoU_mean=means['HOLDOUT'],source_N=len(ss),depth_fixed_N=sum(x['fixed_N'] for x in ev['depth']),depth_invalid_N=sum(x['invalid_N'] for x in ev['depth']),seconds=time.monotonic()-start,source_indices=[v['index']['path'] for v in videos],source_index_sha256=[v['index']['sha256'] for v in videos],cad=cad['identity'],stages=logs,method_success_not_shape_validation=True,real_GT='NOT_EVALUABLE',evaluation_scope='explicit_2D_held_only; upstream camera/HERO may use same frames')
    save(out/'RESULT.json',r);save(out/'COMPLETE.json',dict(cache_key=key,files=[asset(out/n) for n in ['RESULT.json','BASE.json','STAGES.json','STARTS.json','EVALUATION.json','BODY.npz','PARENT.npz','FINAL_UNCUT.npz','CORRECTED_OBSERVATIONS.npz']]+([asset(out/'WEAK_BASE_CANDIDATE.npz')] if (out/'WEAK_BASE_CANDIDATE.npz').exists() else [])))
    print('INIT',g,name,r['base_status'],round(r['seconds'],2),flush=True);return r

def run_group(g):
    qualification_path=T/'evidence/REGISTRATION_QUALIFICATION.json';whole=read(qualification_path);q=next(x for x in whole['groups'] if x['group']==g)
    oldaudit=OLD/'runs/inputs'/g/'AUDIT.json';a=read(oldaudit);save(T/'runs/inputs'/g/'AUDIT.json',dict(a,previous_audit=asset(oldaudit),qualification=asset(qualification_path)))
    folder=T/'runs/results'/g;folder.mkdir(parents=True,exist_ok=True)
    with open(folder/'RUN.lock','w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        videos={};results=[];failed=[]
        for v in a['videos']:
            case=v['case'];name=case.rsplit('_',1)[-1]
            try:
                vv=prepare_video(a,v);videos[case]=vv
                results.append(run_configuration(g,name,[vv],dict(status='SINGLE_LOCAL',registration_not_required=True)))
            except Exception as exc:failed.append(dict(configuration=name,status='FAILED',error=repr(exc),traceback=traceback.format_exc()))
        for comp in q['joint_components']:
            name=comp['name'];cases=comp['videos']
            try:
                assert len(cases)>=2 and all(c in videos for c in cases)
                mats={c:np.array(comp['T_local_to_joint'][c]) for c in cases};anchor=comp['anchor']
                vv=[to_joint(videos[c],mats[c],anchor) for c in cases]
                # Anchor CAD is physical fixed reference; no fitting or averaging of CAD.
                cad=videos[anchor]['cad']
                for v in vv:v['cad']=cad
                seed=[transform_parameter(r['p'],mats[r['videos'][0]]) for r in results if len(r['videos'])==1 and r['videos'][0] in cases]
                results.append(run_configuration(g,name,vv,dict(status='PASS_FOR_JOINT',component=comp,qualification_sha256=sha(qualification_path)),seed))
            except Exception as exc:failed.append(dict(configuration=name,status='FAILED',error=repr(exc),traceback=traceback.format_exc()))
        notrun=[]
        if not q['joint_components']:notrun=[dict(configuration='JOINT',status='NOT_RUN',reason=q.get('joint_not_run_reason'),qualification=q)]
        elif not any(set(c['videos'])=={v['case'] for v in a['videos']} for c in q['joint_components']):notrun=[dict(configuration='JOINT_FULL_GROUP',status='NOT_RUN',reason='Only approved connected subset is eligible; excluded videos remain local',qualification=q)]
        save(folder/'GROUP_RESULT.json',dict(group=g,results=results,failures=failed,not_run=notrun,all_video_cases=[v['case'] for v in a['videos']],qualification=q))
        print('GROUP',g,len(results),'FAILED',len(failed),'NOT_RUN',len(notrun),flush=True)
        return read(folder/'GROUP_RESULT.json')

if __name__=='__main__':
    pa=argparse.ArgumentParser();pa.add_argument('--group');args=pa.parse_args()
    groups=[args.group] if args.group else [x['group'] for x in read(T/'evidence/REGISTRATION_QUALIFICATION.json')['groups']]
    for g in groups:run_group(g)
