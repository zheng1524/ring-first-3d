"""Surface-only video/frame rigid localization with outer rebuilt candidates."""
import json,time
import numpy as np
import cv2
from scipy.optimize import least_squares
from ..synthetic.io import fetch,save_json,outputs
from ..contracts.identities import sha256
from ..policy.contracts import require,PolicyError
from ..sim.legacy import namespace
from ..sim.mapping import candidates
from ..sim.registration import robust_icp
from .geometry import transform,se3,parameters,scene,closest,choose,vertex_normals,rotation_about_camera


def model_namespace(task):return namespace(dict(sim=dict(assets=dict(reuse_lock=task['fusion']['assets']['reuse_lock']))))


def load_case(root,cond):
    index=json.loads(fetch(root,'G0_views_noise','public/FRAME_INDEX.json').read_text());frames=[r for r in index if r['role']=='FIT'];cams=json.loads(fetch(root,'G0_views_noise','public/conditions/'+cond+'/ESTIMATED_POSES.json').read_text());by={c['id']:c for c in cams};data=[]
    for r in frames:
        cid=r['id'];m=dict(np.load(fetch(root,'G0_views_noise','public/conditions/'+cond+'/'+cid+'.npz')));cam=by[cid];obs=np.load(fetch(root,'G0_views_noise','public/observations/'+cid+'.npz'))
        data.append(dict(**r,**m,C=np.asarray(cam['estimated_C']),sigma=np.r_[np.full(3,np.deg2rad(cam['sigma_rotation_deg'])),np.full(3,cam['sigma_translation_mm'])],normals=vertex_normals(m['V'],m['F']),labels=obs['labels']))
    return data


def graph(data):
    edges=set();directions=np.array([d['C'][:3,2]for d in data])
    for i,d in enumerate(data):
        for family in ['same','other']:
            options=[j for j,e in enumerate(data)if i!=j and((d['video']==e['video'])==(family=='same'))]
            options.sort(key=lambda j:(-float(directions[i]@directions[j]),data[j]['id']))
            for j in options[:2]:edges.add(tuple(sorted([i,j])))
    return sorted(edges)


def transforms(data,g,e):return [se3(g[0 if d['video']=='004'else 1])@rotation_about_camera(e[i],d['C'])for i,d in enumerate(data)]


def mapping_constraints(task,data,body,fits,X,ns):
    cfg=task['fusion'];c,Q,a=ns['decode'](body['p'],body['R0']);rows=[]
    for i,d in enumerate(data):
        take=np.linspace(0,len(d['V'])-1,min(cfg['registration_samples_per_view'],len(d['V'])),dtype=int);uv=d['uv'][take];Pi=d['V'][take];inverse=np.linalg.inv(X[i]);preV=transform(body['V'],inverse)
        prebody=dict(V=preV,F=body['F'],p=np.r_[transform(c[None],inverse)[0],np.zeros(3),np.log(a)],R0=inverse[:3,:3]@Q)
        # Pull Body into the immutable source measurement chart. Camera arrays
        # are never variables or outputs; only Mesh transforms are optimized.
        m=candidates(uv,fits[d['id']],prebody,np.asarray(d['K']),d['C'],ns,.97,True,scene(preV,body['F']))
        target=transform(m['points'],X[i]);distance=np.linalg.norm(transform(Pi,X[i])-target,axis=1)
        contact=cv2.dilate((d['labels']==2).astype(np.uint8),np.ones((3,3),np.uint8))[uv[:,1].astype(int),uv[:,0].astype(int)]>0
        keep=m['valid']&~contact&(m['confidence']>=cfg['candidate_confidence_min'])&(distance<=cfg['candidate_reject_distance_mm'])
        quality=1. if fits[d['id']]['formal']['quality'].get('strict_stable',False)else .5
        rows.append(dict(i=i,P=Pi[keep],Q=target[keep],weight=m['confidence'][keep]*quality,target_N=len(Pi),accepted_N=int(keep.sum()),contact_unknown_N=int(contact.sum()),
            original_uv=uv,mapped_uv=m['mapped_uv'],face=m['face'],bary=m['bary'],confidence=m['confidence'],accepted=keep,raw_source_points=Pi,candidate_points=target))
    return rows


def pair_constraints(task,data,X,edges):
    cfg=task['fusion'];world=[transform(d['V'],T)for d,T in zip(data,X)];scenes=[scene(V,d['F'])for V,d in zip(world,data)];out=[]
    for i,j in edges:
        for a,b in [(i,j),(j,i)]:
            d=data[a];take=np.linspace(0,len(d['V'])-1,min(cfg['overlap_samples_per_edge'],len(d['V'])),dtype=int);P=d['V'][take];Pnow=transform(P,X[a]);Q,n,_=closest(scenes[b],Pnow)
            normal=d['normals'][take]@X[a][:3,:3].T;agree=abs((normal*n).sum(1));distance=np.linalg.norm(Pnow-Q,axis=1)
            good=(distance<cfg['pair_max_distance_mm'])&(agree>cfg['normal_agreement_min'])
            inv=np.linalg.inv(X[b]);out.append(dict(i=a,j=b,P=P[good],Q=transform(Q[good],inv),n=n[good]@X[b][:3,:3],target_N=len(P),accepted_N=int(good.sum())))
    return out


def body_residual(delta,tolerance):
    norm=np.linalg.norm(delta,axis=1);return delta*(np.maximum(0,norm-tolerance)/np.maximum(norm,1e-12))[:,None]


def optimize(task,data,body,fits,hierarchical,tolerance,ns):
    cfg=task['fusion'];n=len(data);g=np.zeros((2,6));e=np.zeros((n,6));edges=graph(data);trace=[];weights=cfg['weights'];lastmaps=[]
    for outer in range(cfg['registration_outer_iterations']):
        X=transforms(data,g,e);maps=mapping_constraints(task,data,body,fits,X,ns);pairs=pair_constraints(task,data,X,edges);lastmaps=maps
        def data_residual(T,only=None):
            parts=[];MM=maps if only is None else[maps[only]]
            for a in MM:
                if a['accepted_N']:
                    delta=transform(a['P'],T[a['i']])-a['Q'];r=body_residual(delta,tolerance)*np.sqrt(a['weight'][:,None]*weights['body_region']/max(1,len(a['P'])));parts.append(r.ravel()/np.sqrt(n if only is None else 1))
            pp=pairs if only is None else[p for p in pairs if only in [p['i'],p['j']]]
            for a in pp:
                if a['accepted_N']:
                    delta=transform(a['P'],T[a['i']])-transform(a['Q'],T[a['j']]);normal=a['n']@T[a['j']][:3,:3].T
                    parts.append(np.einsum('ni,ni->n',delta,normal)*np.sqrt(weights['overlap']/max(1,len(a['P']))/max(1,len(pp))))
            return parts
        def video_residual(q):
            gg=q.reshape(2,6);T=transforms(data,gg,e);rr=data_residual(T)
            scale=np.r_[np.full(3,np.deg2rad(cfg['video_rotation_bound_deg'])),np.full(3,cfg['video_translation_bound_mm'])]
            rr.append((gg/scale*np.sqrt(weights['video_prior']/12)).ravel());return np.concatenate(rr)
        bound=np.tile(np.r_[np.full(3,np.deg2rad(cfg['video_rotation_bound_deg'])),np.full(3,cfg['video_translation_bound_mm'])],2)
        initial=video_residual(g.ravel());result=least_squares(video_residual,g.ravel(),bounds=(-bound,bound),method='trf',loss='soft_l1',f_scale=.1,max_nfev=cfg['registration_nfev'],x_scale=np.tile([.05,.05,.05,.5,.5,.5],2),ftol=1e-5,xtol=1e-5,gtol=1e-5);g=result.x.reshape(2,6)
        frame_trace=[]
        if hierarchical:
            for i,d in enumerate(data):
                sigma=d['sigma']
                if not np.any(sigma):continue
                bound=cfg['residual_sigma_bound']*sigma;members=[j for j,a in enumerate(data)if a['video']==d['video']]
                def local_residual(q):
                    ee=e.copy();ee[i]=q;T=transforms(data,g,ee);rr=data_residual(T,i)
                    rr.append(q/sigma*np.sqrt(weights['frame_prior']/6));rr.append(ee[members].mean(0)/sigma*np.sqrt(weights['frame_mean']/6));return np.concatenate(rr)
                before=local_residual(e[i]);fit=least_squares(local_residual,e[i],bounds=(-bound,bound),loss='soft_l1',f_scale=.1,max_nfev=cfg['registration_nfev'],x_scale=np.maximum(sigma,1e-8),ftol=1e-5,xtol=1e-5,gtol=1e-5);e[i]=fit.x
                frame_trace.append(dict(id=d['id'],nfev=fit.nfev,optimizer_success=bool(fit.success),initial_objective=float(before@before/2),objective=float(fit.fun@fit.fun/2),local_surface_parameters=fit.x.tolist(),prior_sigma=sigma.tolist()))
        trace.append(dict(outer=outer,shared_video_nfev=result.nfev,shared_optimizer_success=bool(result.success),shared_initial_objective=float(initial@initial/2),shared_final_objective=float(result.fun@result.fun/2),
            candidates=[{k:a[k]for k in ['i','target_N','accepted_N','contact_unknown_N']}for a in maps],overlap_pairs=[{k:a[k]for k in ['i','j','target_N','accepted_N']}for a in pairs],frame_updates=frame_trace))
    X=transforms(data,g,e);return X,dict(shared_video_parameters=g.tolist(),frame_residual_parameters=e.tolist(),trace=trace,hierarchical=hierarchical,
        candidate_rebuilt_each_outer=True,body_tolerance_mm=tolerance,camera_optimization=False,optimizer_success=all(t['shared_optimizer_success']and all(z['optimizer_success']for z in t['frame_updates'])for t in trace)),lastmaps


def icp(task,data):
    cfg=task['fusion'];X=[np.eye(4)for _ in data];edges=graph(data);trace=[]
    for outer in range(cfg['ICP_outer_iterations']):
        for i,d in enumerate(data):
            if i==0:continue # explicit fixed surface gauge; never GT aligned
            neighbors=sorted({b if a==i else a for a,b in edges if i in [a,b]});Vs=[];Fs=[];offset=0
            for j in neighbors:
                Vs.append(transform(data[j]['V'],X[j]));Fs.append(data[j]['F']+offset);offset+=len(data[j]['V'])
            target=(np.concatenate(Vs),np.concatenate(Fs));source=(transform(d['V'],X[i]),d['F'])
            correction,record=robust_icp(source,target,cfg['ICP_distance_mm'],cfg['ICP_iterations']);X[i]=correction@X[i];trace.append(dict(outer=outer,id=d['id'],**record))
    return X,dict(trace=trace,anchor_surface=data[0]['id'],GT_alignment=False,optimizer_success=all(r['correspondences']>0 for r in trace),camera_optimization=False)


def candidates_stage(task,attempt):
    root=attempt.parents[1];ns=model_namespace(task);fits={r['id']:r for r in json.loads(fetch(root,'G1_body','IMAGE_FITS.json').read_text())};summary=[];(attempt/'maps').mkdir()
    for arm in task['fusion']['body_arms']:
        body=dict(np.load(fetch(root,'G1_body',arm+'_BODY.npz')))
        for cond in task['fusion']['condition_order']:
            data=load_case(root,cond);maps=mapping_constraints(task,data,body,fits,[np.eye(4)for _ in data],ns)
            for a in maps:
                key=arm+'__'+cond+'__'+data[a['i']]['id'];np.savez_compressed(attempt/'maps'/(key+'.npz'),**{k:v for k,v in a.items()if isinstance(v,np.ndarray)})
                summary.append(dict(key=key,id=data[a['i']]['id'],video=data[a['i']]['video'],arm=arm,condition=cond,target_N=a['target_N'],accepted_N=a['accepted_N'],contact_unknown_N=a['contact_unknown_N']))
    save_json(attempt/'CANDIDATES_FROZEN.json',dict(rows=summary,GT_read_by_predictor=False,candidates_are_regions_not_pose_updates=True));return outputs(attempt,dict(status='PASS',role='predictor',rows=summary,GT_read_by_predictor=False))


def run(task,attempt,smoke=False):
    root=attempt.parents[1];cfg=task['fusion'];ns=model_namespace(task);fits={r['id']:r for r in json.loads(fetch(root,'G1_body','IMAGE_FITS.json').read_text())};records=[];conditions=['C0','C1']if smoke else cfg['condition_order'];icp_cache={}
    frozen_bodies={a:sha256(fetch(root,'G1_body',a+'_BODY.npz'))for a in cfg['body_arms']}
    for cond in conditions:
        data=load_case(root,cond)
        for arm in cfg['body_arms']:
            body=dict(np.load(fetch(root,'G1_body',arm+'_BODY.npz')))
            variants=[(m,cfg['tolerance_mm'],'MAIN')for m in cfg['methods']]
            if not smoke and cond=='C3':variants.extend([('BODY_HIER',tol,'TOLERANCE_ABLATION')for tol in cfg['tolerance_ablation_mm']])
            for method,tol,kind in variants:
                key=f'{cond}__{arm}__{method}__tol{tol:g}';out=attempt/key;out.mkdir();started=time.monotonic()
                try:
                    maps=[]
                    if method=='M0':X=[np.eye(4)for _ in data];details=dict(optimizer_success=True,method='No surface correction')
                    elif method=='ICP':
                        if cond not in icp_cache:icp_cache[cond]=icp(task,data)
                        X,details=icp_cache[cond]
                    else:X,details,maps=optimize(task,data,body,fits,method=='BODY_HIER',tol,ns)
                    matrices={};motions={}
                    for i,d in enumerate(data):
                        V=transform(d['V'],X[i]);F=d['F'];np.savez_compressed(out/(d['id']+'.npz'),V=V,F=F)
                        edges=F[:,[0,1]];before=np.linalg.norm(d['V'][edges[:,0]]-d['V'][edges[:,1]],axis=1);after=np.linalg.norm(V[edges[:,0]]-V[edges[:,1]],axis=1)
                        require(np.max(abs(before-after))<1e-8,'MESH_RIGIDITY','Surface correction must preserve every triangle edge')
                        matrices[d['id']]=X[i].tolist();motions[d['id']]=float(np.linalg.norm(V-d['V'],axis=1).max())
                    for a in maps:
                        np.savez_compressed(out/(data[a['i']]['id']+'_FINAL_CANDIDATES.npz'),**{k:v for k,v in a.items()if isinstance(v,np.ndarray)})
                    record=dict(key=key,condition=cond,arm=arm,method=method,kind=kind,tolerance_mm=tol,status='NUMERIC',surface_corrections=matrices,maximum_surface_motion_mm=motions,details=details,
                        camera_optimization=False,camera_files_modified=False,body_sha256=frozen_bodies[arm],Body_frozen=True,vertices_replaced_by_Body=False,seconds=time.monotonic()-started)
                except PolicyError:raise
                except(ValueError,RuntimeError,np.linalg.LinAlgError)as error:
                    record=dict(key=key,condition=cond,arm=arm,method=method,kind=kind,tolerance_mm=tol,status='FAILED_NAN',reason=str(error),surface_corrections=None,seconds=time.monotonic()-started)
                save_json(out/'PREDICTION.json',record);records.append(record);print('MULTISURFACE',key,record['status'],record['seconds'],flush=True)
    for arm,digest in frozen_bodies.items():require(sha256(fetch(root,'G1_body',arm+'_BODY.npz'))==digest,'BODY_IMMUTABLE',arm)
    save_json(attempt/'PREDICTIONS_FROZEN.json',dict(rows=records,GT_read_by_predictor=False,camera_optimization=False,smoke=smoke,history_measurement_fallback=0))
    return outputs(attempt,dict(status='PASS',role='predictor',records=len(records),numeric=sum(r['status']=='NUMERIC'for r in records),scientific_failures=[r for r in records if r['status']!='NUMERIC'],GT_read_by_predictor=False))
