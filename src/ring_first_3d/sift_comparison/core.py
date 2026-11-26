"""Task-specific, camera-independent manifests and predictive evaluation adapters."""
import numpy as np


def split_tracks(held):
    ids=np.arange(len(held))
    return dict(train=ids[~held].tolist(), validation=ids[held & ((ids//5)%2==0)].tolist(), test=ids[held & ((ids//5)%2==1)].tolist())


def query_manifest(xy, ids):
    records=[]
    for t in ids:
        frames=np.flatnonzero(np.isfinite(xy[t]).all(axis=1))
        for q in frames:
            other=frames[frames!=q]
            selected=other[np.rint(np.linspace(0,len(other)-1,min(3,len(other)))).astype(int)] if len(other) else []
            records.append(dict(track=int(t),query=int(q),support=list(map(int,selected))))
    return records


def select_tuples(xy, train):
    present=np.isfinite(xy[train]).all(axis=2).astype(int)
    counts=present.T@present
    ranking=sorted(range(counts.shape[0]),key=lambda i:(-int(counts[i].sum()-counts[i,i]),i))
    eligible={i:sorted([j for j in ranking if j!=i and counts[i,j]>=15],key=lambda j:(-int(counts[i,j]),j)) for i in ranking}
    valid=[i for i in ranking if len(eligible[i])>=3]
    tuples=[]
    if valid:
        first=valid[0]
        second=sorted([i for i in valid if i!=first and counts[first,i]>=15],key=lambda i:(i not in eligible[first][:3],ranking.index(i)))
        for i in [first]+second[:1]:
            tuples.append(dict(reference=i,sources=eligible[i][:3],overlap=[int(counts[i,j]) for j in eligible[i][:3]]))
    return dict(tuples=tuples,train_overlap=counts.tolist(),graph_eligible_targets=valid)


def predict_queries(tr, poses, queries, triangle, project, K):
    out=[]
    for row in queries:
        t,q,s=row['track'],row['query'],row['support']
        rec=dict(row,category=int(tr['category'][t]),status='NOT_EVALUABLE',error_px=None,predicted_xy=None,positive=False)
        if not np.isfinite(poses[q]).all():rec['reason']='QUERY_CAMERA_MISSING'
        elif len(s)<2:rec['reason']='FEWER_THAN_TWO_SUPPORT_OBSERVATIONS'
        elif not np.isfinite(poses[s]).all():rec['reason']='FIXED_SUPPORT_CAMERA_MISSING'
        elif np.max(np.linalg.norm(poses[s,:3,3]-poses[s[0],:3,3],axis=1))<1e-10:rec['reason']='ZERO_SUPPORT_BASELINE'
        else:
            try:
                point=triangle(poses[s],tr['xy'][t,s])
                if not np.isfinite(point).all():raise ValueError('NONFINITE_TRIANGULATION')
                uv,z=project(point[None],poses[q],K)
                support_z=[float(project(point[None],poses[i],K)[1][0]) for i in s]
                if float(z[0])<=0 or min(support_z)<=0:rec['reason']='NONPOSITIVE_DEPTH'
                elif not np.isfinite(uv).all():rec['reason']='NONFINITE_PROJECTION'
                else:
                    rec.update(status='OK',reason='',positive=True,predicted_xy=uv[0].tolist(),error_px=float(np.linalg.norm(uv[0]-tr['xy'][t,q])))
            except (ValueError,np.linalg.LinAlgError) as e:rec['reason']=str(e)
        out.append(rec)
    return out


def summary(rows):
    ok=[r for r in rows if r['status']=='OK']; errors=np.array([r['error_px'] for r in ok]); n=len(rows)
    reasons={r['reason']:sum(x['reason']==r['reason'] for x in rows) for r in rows if r['reason']}
    return dict(status='EVALUABLE' if len(ok) else 'NOT_EVALUABLE',total=n,predicted=len(ok),success_3px=int((errors<=3).sum()),predicted_fraction=len(ok)/n if n else None,success_fraction=float((errors<=3).sum()/n) if n else None,median_px=float(np.median(errors)) if len(ok) else None,P95_px=float(np.quantile(errors,.95)) if len(ok) else None,MAE_px=float(errors.mean()) if len(ok) else None,reasons=reasons)


def rgb_checks(rows,n):
    records=[]
    for i in range(n):
        s=summary([r for r in rows if r['query']==i])
        passed=s['predicted']>=8 and s['MAE_px']<=3 and s['P95_px']<=6 and s['predicted_fraction']>=.95
        records.append(dict(frame=i,passed=bool(passed),**s))
    return records


def positive_similarity(source,target):
    x,y=np.asarray(source,float),np.asarray(target,float)
    if len(x)<6 or x.shape!=y.shape or not(np.isfinite(x).all() and np.isfinite(y).all()):raise ValueError('INSUFFICIENT_COMMON_TRAIN_POINTS')
    xc,yc=x-x.mean(0),y-y.mean(0)
    if np.linalg.matrix_rank(xc)<2 or np.linalg.matrix_rank(yc)<2:raise ValueError('DEGENERATE_COMMON_TRAIN_POINTS')
    u,d,vt=np.linalg.svd(yc.T@xc/len(x));sign=np.ones(3);sign[-1]=np.linalg.det(u@vt)
    rot=(u*sign)@vt;scale=float((d*sign).sum()/np.mean(np.sum(xc*xc,axis=1)))
    if not scale>0:raise ValueError('NONPOSITIVE_SCALE')
    shift=y.mean(0)-scale*rot@x.mean(0)
    residual=np.linalg.norm(scale*x@rot.T+shift-y,axis=1)
    return dict(scale=scale,rotation=rot.tolist(),translation=shift.tolist(),common_training_points=len(x),determinant=float(np.linalg.det(rot)),training_alignment_residual_median=float(np.median(residual)),not_GT=True)


def transform_cameras(poses,sim):
    out=poses.copy();rot=np.array(sim['rotation']);shift=np.array(sim['translation'])
    out[:,:3,:3]=rot@poses[:,:3,:3]
    out[:,:3,3]=sim['scale']*poses[:,:3,3]@rot.T+shift
    return out


def validate_frozen_similarity(sim,camera_hashes,original,normalized):
    if sim.get('status')!='FROZEN':raise ValueError('NORMALIZATION_NOT_FROZEN')
    if sim['camera_hashes']!=camera_hashes:raise ValueError('NORMALIZATION_CAMERA_DRIFT')
    expected=transform_cameras(original,sim)
    if not np.allclose(expected,normalized,rtol=0,atol=1e-12,equal_nan=True):raise ValueError('NORMALIZED_CAMERA_DRIFT')
