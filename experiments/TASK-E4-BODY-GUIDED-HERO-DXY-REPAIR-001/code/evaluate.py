"""Post-freeze full-mask evaluation and observation-only identifiability."""
from fitting import *
from itertools import combinations,product
reuse(A1/'analyze.py',['geom','sample_mesh','surface_distance','canonical_orientation','difference'],globals())

def projection_metrics(m,cid):
    s=source(cid);p=np.array(m['p']);R0=np.array(m['R0']);y,x=np.mgrid[:360,:640];uv=np.c_[x.ravel(),y.ravel()]
    z=first_depth(p,R0,camera_rays(uv,s['K'],s['T']));cad=cast(ringscene(m['pool'][:3]),uv,s['K'],s['T'])[0]
    pred=(np.isfinite(z)&(z>0)&(z<=cad+.05)).reshape(360,640);full=s['labels']==1;ring=s['labels']==2;known=~ring
    inter=int((pred&full).sum());fp=int((pred&~full&known).sum());fn=int((full&~pred).sum());union=int((full|(pred&known)).sum())
    ob=contour(full);pb=contour(pred&known);adj=cv2.dilate(ring.astype(np.uint8),np.ones((3,3),np.uint8)).astype(bool)
    ob=ob[~adj[ob[:,1].astype(int),ob[:,0].astype(int)]];pb=pb[~adj[pb[:,1].astype(int),pb[:,0].astype(int)]]
    d1=cKDTree(pb).query(ob)[0] if len(pb) and len(ob) else np.full(len(ob),np.hypot(640,360))
    d2=cKDTree(ob).query(pb)[0] if len(pb) and len(ob) else np.full(len(pb),np.hypot(640,360))
    return dict(source=cid,pool=m['pool'],arm=m['arm'],available=True,full_mask_N=int(full.sum()),canvas_N=230400,intersection_N=inter,FN=fn,FP=fp,IoU=inter/max(1,union),FN_fraction=fn/max(1,int(full.sum())),FP_per_fixed_mask=fp/max(1,int(full.sum())),FP_per_canvas=fp/230400,boundary_bidir_px=stats(np.r_[d1,d2]),fixed_source_boundary_px=stats(d1),Ring_unknown_N=int(ring.sum()),predicted_Ring_unknown_N=int((pred&ring).sum())),pred

def identifiability(problem,p):
    scales=np.r_[np.ones(3),np.full(3,.1),np.full(3,.2)];eps=1e-4;columns=[]
    for j in range(9):
        step=np.zeros(9);step[j]=eps*scales[j]
        columns.append((problem.data_residual(p+step)-problem.data_residual(p-step))/(2*eps))
    J=np.array(columns).T;s=np.linalg.svd(J,compute_uv=False);_,_,vh=np.linalg.svd(J,full_matrices=False);tol=s[0]*1e-6
    # Independent conic-only diagnostic: one silhouette has just five conic
    # coefficients. CAD visibility/float32 raycast discontinuities must not be
    # mistaken for nine independent image-shape constraints in one view.
    def conics(theta):
        out=[]
        for cam in problem.cameras:
            center,M,axes,curve=ellipse_projection(theta,problem.R0,cam['K'],cam['T'])
            out.extend([center[0]/100,center[1]/100,M[0,0]*10000,M[0,1]*10000,M[1,1]*10000])
        return np.array(out)
    cj=[]
    for j in range(9):
        step=np.zeros(9);step[j]=eps*scales[j];cj.append((conics(p+step)-conics(p-step))/(2*eps))
    cs=np.linalg.svd(np.array(cj).T,compute_uv=False)
    return dict(rank=int((s>tol).sum()),singular_values=s,condition_number=float(s[0]/max(s[-1],1e-30)),parameter_sensitivity=np.linalg.norm(J,axis=0),weakest_parameter_combination_scaled=vh[-1],parameter_order=['cx','cy','cz','rx','ry','rz','log_a','log_b','log_c'],scales=scales,rank_tolerance=tol,prior_rows_included=False,rows=J.shape[0],operator='A1 robust 2D residual finite difference, no priors, no HERO',conic_only_rank=int((cs>cs[0]*1e-6).sum()),conic_only_singular_values=cs,conic_only_condition_number=float(cs[0]/max(cs[-1],1e-30)) if len(cs)==9 else None,warning='robust/CAD Jacobian rank can reflect soft visibility and float32 raycast discretization; conic-only single-view rank is at most5, numerical full rank does not certify accuracy'),J

def main():
    freeze=load(R/'provenance/ALL_PREDICTIONS_FROZEN.json')
    for f in freeze['files']:assert sha(f['path'])==f['sha256']
    guard('evaluation');plan=load(R/'config/BODY_FIT_VIEWS.json');ss={s['source_id']:s for s in load(R/'config/SOURCE_BINDING.json')}
    metrics=[];stabilities=[];jacobians=[];geometry=[];view_metrics=[];releases=[];bodyu=[]
    for name,sc in plan.items():
        for arm in ['E1','E2']:
            path=R/'local_results'/name/arm;m=load(path/'SELECTION.json');allfits=[load(p) for p in sorted(path.glob('START_*.json'))]
            diffs=[dict(starts=[a['start'],b['start']],**difference(a,b)) for a,b in combinations(allfits,2)]
            stab=dict(pool=name,arm=arm,starts=len(allfits),eligible_N=sum(x['eligible'] for x in allfits),converged_N=sum(x['optimizer_success'] for x in allfits),pairwise=diffs,center_max_mm=max([x['center_mm'] for x in diffs],default=None),surface_max_p95_mm=max([x['surface_distance_mm']['p95'] for x in diffs],default=None))
            stabilities.append(stab)
            for r in allfits:
                axes=np.exp(r['p'][6:]);metrics.append(dict(pool=name,group=sc['group'],arm=arm,start=r['start'],selected=m['available'] and r['start']==m['start'],eligible=r['eligible'],optimizer_success=r['optimizer_success'],nfev=r['nfev'],actual_residual_calls=r['actual_residual_calls'],FIT_objective=r['objective'],initial=r['initial'],R0=r['R0'],source_ids=r['source_ids'],weights=r['weights'],axes_mm=axes,center_mm=r['p'][:3],axis_ratio=float(axes.max()/axes.min()),active_bounds=r['active_bounds'],ineligible_reasons=r['ineligible_reasons'],seconds=r['seconds']))
            if not m['available']:
                for cid in sc['raw_sources']:view_metrics.append(dict(pool=name,arm=arm,source=cid,role='NOT_EVALUABLE',available=False,IoU=None,reason=m['status']))
                releases.append(dict(pool=name,arm=arm,numerical_available=False,advance_to_HERO=False,reasons=[m['status']]))
                continue
            p=np.array(m['p']);R0=np.array(m['R0']);problem=Problem(name,arm);ident,J=identifiability(problem,p);ident.update(pool=name,arm=arm)
            single=[]
            for cid in sc['FIT']:
                q=Problem(name,arm,only_ids=[cid]);iv,_=identifiability(q,p);single.append(dict(source=cid,**iv))
            ident['single_view_at_same_solution']=single;jacobians.append(ident)
            np.savez_compressed(path/'OBSERVATION_JACOBIAN.npz',J=J)
            c,Q,a=decode(p,R0);V,F=mesh(p,R0);ring=np.load(ASSETS/'TASK-E4-BODY-ANCHORED-MULTIHERO-001/inputs'/sc['group']/'RING.npz')
            samples=np.r_[sample_mesh(m,2048),V];sd=ringscene(sc['group']).compute_signed_distance(o3d.core.Tensor(samples.astype(np.float32)),nsamples=11).numpy()
            reverse=mesh_scene(V,F).compute_signed_distance(o3d.core.Tensor(ring['V'].astype(np.float32)),nsamples=11).numpy()
            geom=dict(pool=name,arm=arm,center_mm=c,semiaxes_mm=a,rotation_matrix=Q,volume_mm3=float(4*np.pi/3*np.prod(a)),axis_ratio=float(max(a)/min(a)),max_axis_near_15=bool(max(a)>=14.85),min_axis_near_point25=bool(min(a)<=.2525),active_bounds=m['active_bounds'],Ring_signed_min_mm=float(sd.min()),Ring_surface_samples_N=len(samples),Ring_penetrating_samples_N=int((sd<-.05).sum()),Ring_vertices_inside_body_N=int((reverse<-.05).sum()),backside='PRIOR_INFERRED_NOT_OBSERVED',watertight=bool(trimesh.Trimesh(V,F,process=False).is_watertight))
            geometry.append(geom)
            for cid in sc['raw_sources']:
                met,pred=projection_metrics(m,cid);met['role']='FIT' if cid in sc['FIT'] else 'HOLDOUT' if cid in sc['HOLDOUT'] else 'EXCLUDED_DIAGNOSTIC';view_metrics.append(met)
                np.savez_compressed(path/(cid+'_PROJECTION.npz'),predicted_mask=pred)
            held=[x for x in view_metrics if x['pool']==name and x['arm']==arm and x['role']=='HOLDOUT' and x['available']]
            why=[]
            if stab['eligible_N']!=3:why.append('NOT_ALL_THREE_STARTS_ELIGIBLE')
            if geom['max_axis_near_15'] or geom['min_axis_near_point25'] or np.any(m['active_bounds']) or geom['axis_ratio']>20:why.append('PARAMETER_BOUND_OR_AXIS_RATIO_RISK')
            if (stab['center_max_mm'] or 0)>2 or (stab['surface_max_p95_mm'] or 0)>2:why.append('MULTISTART_UNSTABLE')
            if ident['rank']<9 or ident['condition_number']>1e6:why.append('OBSERVATION_IDENTIFIABILITY_WEAK')
            if not held or np.median([x['IoU'] for x in held])<.5 or min(x['IoU'] for x in held)<.35 or np.mean([x['fixed_source_boundary_px']['MAE'] for x in held])>10:why.append('HELDOUT_PROJECTION_INCONSISTENT')
            if geom['Ring_penetrating_samples_N']>0:why.append('RING_BODY_SURFACE_PENETRATION')
            releases.append(dict(pool=name,arm=arm,numerical_available=True,advance_to_HERO=not why,reasons=why,holdout_N=len(held),holdout_median_IoU=float(np.median([x['IoU'] for x in held])),holdout_mean_fixed_boundary_px=float(np.mean([x['fixed_source_boundary_px']['MAE'] for x in held]))))
            if sc['video']=='004':
                up=ASSETS/'TASK-E4-BODY-GUIDED-HERO-RELOCALIZATION-001/local_results'/sc['group']/'Body-U.npz'
                if up.exists():
                    u=np.load(up);us=mesh_scene(u['V'],u['F']);dist=us.compute_distance(o3d.core.Tensor(sample_mesh(m).astype(np.float32))).numpy()
                    bodyu.append(dict(pool=name,arm=arm,Body_U=asset(up),new_surface_to_Body_U_mm=stats(dist),comparison_only=True,historical_fusion='Body-U inherited formal R3 B3 FINAL, contains historical multiple-HERO fitting, not GT'))
            print('EVALUATED',name,arm,'holdoutIoU',releases[-1]['holdout_median_IoU'],'gate',not why,why,flush=True)
    table('metrics/BODY_FIT_METRICS.csv',metrics);save('metrics/MULTISTART_STABILITY.json',stabilities);save('metrics/JACOBIAN_IDENTIFIABILITY.json',jacobians);save('metrics/GEOMETRY_AUDIT.json',geometry)
    save('metrics/ALL_VIEW_EVALUATION.json',view_metrics)
    flat=[]
    for x in view_metrics:
        row={k:v for k,v in x.items() if k not in ['boundary_bidir_px','fixed_source_boundary_px']}
        for kind in ['boundary_bidir_px','fixed_source_boundary_px']:
            row.update({kind+'_'+k:v for k,v in x.get(kind,{}).items()})
        flat.append(row)
    table('metrics/HELDOUT_VIEW_EVALUATION.csv',[x for x in flat if x['role']!='FIT']);table('metrics/ALL_VIEW_EVALUATION.csv',flat)
    save('metrics/NEXT_STAGE_ELIGIBILITY.json',releases);save('metrics/BODY_U_COMPARISON.json',bodyu)
    pairs=[]
    for name in plan:
        a={x['source']:x for x in view_metrics if x['pool']==name and x['arm']=='E1' and x['available'] and x['role']=='HOLDOUT'};b={x['source']:x for x in view_metrics if x['pool']==name and x['arm']=='E2' and x['available'] and x['role']=='HOLDOUT'}
        for cid in sorted(a.keys()&b.keys()):pairs.append(dict(pool=name,source=cid,E1_IoU=a[cid]['IoU'],E2_IoU=b[cid]['IoU'],delta_E2_minus_E1_IoU=b[cid]['IoU']-a[cid]['IoU'],E1_boundary=a[cid]['fixed_source_boundary_px']['MAE'],E2_boundary=b[cid]['fixed_source_boundary_px']['MAE']))
    table('metrics/PAIRED_HOLDOUT_COMPARISON.csv',pairs)
    save('provenance/EVALUATION_COMPLETED.json',dict(epoch=time.time(),predictions_freeze=asset(R/'provenance/ALL_PREDICTIONS_FROZEN.json'),GT_read=False,Body_U_after_prediction_freeze=True,source_reuse=REUSE))
if __name__=='__main__':main()
