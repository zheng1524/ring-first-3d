"""Reuse v0.1 Ring/RGB tests uniformly; no pose fitting, no HERO for Gate."""
from common import *
from scipy.spatial.transform import Rotation
os.environ['CUDA_VISIBLE_DEVICES']=''
cfg=load(CG/'config/protocol.json')
extract(CG/'code/common.py',['boundary','at','inside','fit_partition','select_uniform','local_pose','skew','fundamental','sampson','coverage','enough'],globals())
extract(CG/'code/tests12.py',['ring_test','annotate','geometric_diagnostics','pair_test'],globals())
extract(OLD.parent/'scripts/geometry.py',['torus_contours'],globals())
extract(CG/'code/correction.py',['numerical_jac'],globals())
def short(cid):return cid
def pair_id(a,b):return a+'__'+b
def camera(cid,T=None):
    s=source(cid);return SameCameraScene(ringmesh(s['c']['scene_id']),s['K'],s['T']if T is None else T,(640,360),VENDOR)
def observations_path(a,b,method):return R/'local_results/matches'/(pair_id(a,b)+'_'+method+'.npz')
def match_data(a,b,method):return dict(np.load(observations_path(a,b,method)))
SIFT_NS=dict(np=np,cv2=cv2,cfg=lambda:cfg,image=lambda v:source(v['id'])['RGB'])
extract(PART/'code/matching.py',['sift'],SIFT_NS);SIFT=SIFT_NS['sift']
def cache_plan(a,b):
    out=[]
    for method in cfg['matching_methods_priority']:
        found=None
        for x,y,reverse in [(a,b,False),(b,a,True)]:
            p=OLD/'ring_first_v13_multisource/observations'/f"{method}_{CC[x]['reference']}__{CC[y]['reference']}.npz"
            if p.is_file():found=dict(method=method,path=str(p),reverse=reverse,origin='EXISTING_RGB_MATCHES');break
        # The original pilot already audited image identity; use its frozen cache.
        for x,y,reverse in [(a,b,False),(b,a,True)]:
            p=CG/'config/matches'/f"{x.removeprefix('G01_004_')}__{y.removeprefix('G01_004_')}_{method}.npz"
            if found is None and p.is_file():found=dict(method=method,path=str(p),reverse=reverse,origin='EXISTING_RGB_MATCHES')
        if found:out.append(found)
        elif method=='SIFT':out.append(dict(method=method,path=None,reverse=False,origin='NEW_CPU_SIFT'))
    return out
def observability(cid,selected):
    """Same unregularized residual/Jacobian/scales and exact Ring-yaw null."""
    s=source(cid);scene=s['c']['scene_id'];rr=np.load(R/f'runtime/ring/{cid}_ORIGINAL.npz');p=rr['observed_boundary'][rr['observed_valid']];p=select_uniform(p[~fit_partition(p,p)],cfg['ring_fit_boundary_max'])
    scales=np.r_[np.full(3,np.deg2rad(cfg['rotation_scale_deg'])),np.full(3,cfg['translation_scale_mm'])]
    records=[]
    for row in selected:
        if cid not in [row['A'],row['B']]or row['selected_method']is None:continue
        if row['extra_holdout']and cid!=row['holdout_id']:continue
        d=match_data(row['A'],row['B'],row['selected_method']);j=select_uniform(np.flatnonzero(d['independent_good']&~d['held']),cfg['matching_fit_cap_per_relation'])
        records.append(dict(A=row['A'],B=row['B'],p=d['p'][j],q=d['q'][j]))
    M=ringmesh(scene);rad=np.linalg.norm(M.vertices[:,:2],axis=1);major=(rad.max()+rad.min())/2;minor=(rad.max()-rad.min())/2
    radial_error=float(np.max(abs(np.sqrt((rad-major)**2+M.vertices[:,2]**2)-minor)))
    if radial_error>cfg['torus_CAD_max_radial_error_mm']:
        return dict(rank=None,full_local_numerical_rank=False,reason='CAD_NOT_COMPATIBLE_WITH_ANALYTIC_OBSERVABILITY_ADAPTER',radial_error_mm=radial_error)
    def residual(y):
        T=local_pose(s['T'],y*scales);curves=torus_contours(T[:3,3],T[:3,:3],s['K'],R=major,r=minor,n=cfg['torus_curve_samples']).reshape(-1,2)
        ringr=cKDTree(curves).query(p)[0]/cfg['ring_max_MAE_px']/np.sqrt(max(1,len(p)))
        ir=[]
        for rec in records:
            sa,sb=source(rec['A']),source(rec['B']);Ta=T if rec['A']==cid else sa['T'];Tb=T if rec['B']==cid else sb['T']
            ir.append(sampson(fundamental(sa['K'],Ta,sb['K'],Tb),rec['p'],rec['q'],signed=True))
        v=np.concatenate(ir)/cfg['pose_inlier_px']if ir else np.empty(0)
        return np.r_[ringr,v/np.sqrt(max(1,len(v)))]
    J=numerical_jac(residual,np.zeros(6));n=len(p);g=np.r_[np.array([0.,0.,1.]),np.cross([0.,0.,1.],s['T'][:3,3])]/scales;g/=np.linalg.norm(g)
    J[:n]-=(J[:n]@g)[:,None]*g[None,:];sing=np.linalg.svd(J,compute_uv=False)
    rank=int((sing>max(1e-10,sing[0]*cfg['observability_singular_ratio_min'])).sum())if len(sing)else 0
    return dict(rank=rank,full_local_numerical_rank=rank==6,singular_values=sing,ring_only_singular_values=np.linalg.svd(J[:n],compute_uv=False),ring_exact_yaw_null=g,fit_match_N=sum(len(r['p'])for r in records),prior_included=False,radial_error_mm=radial_error)
def main():
    assert not (R/'config/CAMERA_GATE_RESULTS.json').exists(),'ONE_FIXED_GATE_RUN'
    anchors={scene:([c for c in CORE]if scene=='G01_004'else [c for c in IDS if CC[c]['scene_id']==scene][:1]+sorted([c for c in IDS if CC[c]['scene_id']==scene and c not in [x for x in IDS if CC[x]['scene_id']==scene][:1]],key=lambda c:CC[c]['reference_index'])[:2])for scene in SCENES}
    plans=[]
    for scene,base in anchors.items():
        seen=set()
        for a in [c for c in IDS if CC[c]['scene_id']==scene]:
            for b in base:
                if a==b:continue
                key=tuple(sorted([a,b]))
                if key in seen:continue
                seen.add(key);a1,b1=key
                plans.append(dict(A=a1,B=b1,scene=scene,methods=cache_plan(a1,b1),extra_holdout=base[2]in key,holdout_id=base[2]))
    rules=dict(cfg,scope=IDS,anchors_by_scene=anchors,pose_optimization=False,extension='identical v0.1 formulas; anchors frozen by source identity/index, not pose errors; G01 original3; other groups legacy CORE plus lowest-index2',qualification_not_admission=True)
    save('config/CAMERA_GATE_RULES.json',rules);save('config/MATCH_PLAN_FROZEN.json',plans)
    save('provenance/BEFORE_CAMERA_GATE.json',dict(rules=asset(R/'config/CAMERA_GATE_RULES.json'),plan=asset(R/'config/MATCH_PLAN_FROZEN.json'),code=[asset(p)for p in (R/'code').glob('*.py')],HERO_used=False))
    (R/'runtime/ring').mkdir(exist_ok=True);(R/'local_results/matches').mkdir(exist_ok=True)
    rings=[]
    for cid in IDS:
        r=ring_test(cid,save_images=True);rings.append(r);print('RING',cid,'MAE',r['visible_contour']['MAE'],'p95',r['visible_contour']['p95'],'PASS',r['Ring_pass'],'CLEAR',r['clear_contradiction'],flush=True)
    selected=[];pairs=[]
    for plan in plans:
        methods=[];a,b=plan['A'],plan['B']
        for m in plan['methods']:
            if m['path']:
                z=np.load(m['path']);p,q=(z['q'],z['p'])if m['reverse']else(z['p'],z['q'])
            else:p,q,_=SIFT(CC[a],CC[b])
            d=annotate(p,q,a,b);fit=d['independent_good']&~d['held'];held=d['independent_good']&d['held'];sufficient=enough(p[fit],q[fit],cfg['fit_min_matches'])and enough(p[held],q[held],cfg['held_min_matches'])
            np.savez_compressed(observations_path(a,b,m['method']),**d)
            methods.append(dict(**m,raw_N=len(p),usable_N=int(d['usable'].sum()),fit_N=int(fit.sum()),held_N=int(held.sum()),sufficient_RGB_only=bool(sufficient),input_SHA256=sha(m['path'])if m['path']else None))
        choose=next((m['method']for m in methods if m['sufficient_RGB_only']),None)
        row=dict(plan,methods=methods,selected_method=choose);selected.append(row)
        for m in methods:
            result=pair_test(a,b,m['method']);result.update(selected_for_gate=m['method']==choose,extra_holdout=plan['extra_holdout']);pairs.append(result)
        print('RGB',a,b,'selected',choose,[(m['method'],m['fit_N'],m['held_N'])for m in methods],flush=True)
    save('config/RGB_ONLY_METHOD_SELECTION.json',selected)
    qualifications=[]
    for cid in IDS:
        rr=next(r for r in rings if r['camera']==cid);rel=[r for r in pairs if r['selected_for_gate']and cid in [r['A'],r['B']]];obs=observability(cid,selected);reasons=[]
        contradiction=rr['clear_contradiction']or any(r['clear_contradiction']for r in rel)
        if rr['clear_contradiction']:reasons.append('RING_CLEAR_GEOMETRY_CONTRADICTION')
        if any(r['clear_contradiction']for r in rel):reasons.append('SUFFICIENT_REAL_RGB_GEOMETRY_CONTRADICTION')
        base=anchors[CC[cid]['scene_id']];required=set(base)-{cid};present={r['B']if r['A']==cid else r['A']for r in rel}
        if not rr['Ring_pass']:reasons.append('RING_OUTSIDE_PASS_TOLERANCE_OR_INSUFFICIENT')
        reasons.extend('INSUFFICIENT_RGB_RELATION:'+b for b in sorted(required-present))
        if any(not r['pair_pass']for r in rel):reasons.append('RGB_PARALLAX_CHEIRALITY_OR_ERROR_NOT_PASSED')
        if not obs['full_local_numerical_rank']:reasons.append('LOCAL_DATA_ONLY_POSE_UNOBSERVABLE')
        status='UNQUALIFIED_GEOMETRY'if contradiction else ('INSUFFICIENT_EVIDENCE'if reasons else 'CONDITIONAL_USABLE')
        admit=not contradiction and rr['adequate']
        qualifications.append(dict(source=cid,scene=CC[cid]['scene_id'],block=block(cid),historical_screened=CC[cid]['source_camera_qualified'],qualification=status,reasons=reasons,Ring_pass=rr['Ring_pass'],Ring_MAE_px=rr['visible_contour']['MAE'],Ring_p95_px=rr['visible_contour']['p95'],sufficient_RGB_relation_N=len(rel),passed_RGB_relation_N=sum(r['pair_pass']for r in rel),observability=obs,admission='CONDITIONAL_RESEARCH_INPUT'if admit else 'NOT_ADMITTED',negative_vote_eligible=bool(admit and rr['Ring_pass']),pose_changed=False,GT=False))
        print('QUAL',cid,status,'admit',admit,'rank',obs['rank'],flush=True)
    save('config/CAMERA_GATE_RESULTS.json',dict(Ring=rings,pairs=pairs,sources=qualifications,anchors=anchors,optimizer_calls=0,HERO_used_for_pose=False))
    table('metrics/CAMERA_QUALIFICATION.csv',qualifications)
    save('provenance/CAMERA_GATE_ACCESS.json',dict(read_files=sorted(ACCESSED),denials=DENIALS,HERO_used=False))
if __name__=='__main__':main()
