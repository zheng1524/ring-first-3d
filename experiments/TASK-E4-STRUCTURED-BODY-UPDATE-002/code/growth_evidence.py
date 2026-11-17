"""Adapt frozen Jacobian initialization with explicit rejection/identifiability ledger."""
import numpy as np
from common import legacy

def candidates(body,views,pairs,cfg):
    V,F=body['V'],body['F'];evidence=[]
    for v in views:
        p=pairs[v['id']];ok=p['accepted']&p['missing_support']
        for f,b,uv,q in zip(p['face'][ok],p['bary'][ok],p['projected_uv'][ok],p['target_uv'][ok]):
            P=b@V[F[f]];evidence.append(dict(vertex=int(F[f][b.argmax()]),view=v['id'],video=v['video'],J=legacy.projection_jacobian(P,v['K'],v['C']),residual=q-uv))
    adj=[set()for _ in V]
    for f in F:
        for a in f:adj[a].update(int(b)for b in f if b!=a)
    out=[];records=[];seen=set()
    for seed in sorted({e['vertex']for e in evidence}):
        nodes={seed};front={seed}
        for _ in range(cfg['growth_patch_rings']):front=set().union(*(adj[x]for x in front))-nodes;nodes|=front
        patch=np.flatnonzero(np.isin(F,list(nodes)).all(1));key=tuple(patch)
        if key in seen:continue
        seen.add(key);reason=[];ev=[e for e in evidence if e['vertex']in nodes];groups={}
        for e in ev:groups.setdefault(e['view'],[]).append(e)
        videos=sorted({e['video']for e in ev});record=dict(seed=seed,views=sorted(groups),videos=videos,patch_faces=len(patch))
        if not len(patch)or len(patch)>cfg['growth_max_patch_faces']:reason.append('ATTACHMENT_PATCH_SIZE')
        if len(groups)<3 or len(videos)<2:reason.append('INSUFFICIENT_MULTIVIEW_SUPPORT')
        if not reason:
            J=np.concatenate([np.mean([e['J']for e in es],0)for es in groups.values()]);r=np.concatenate([np.mean([e['residual']for e in es],0)for es in groups.values()]);s=np.linalg.svd(J,compute_uv=False);ratio=float(s[-1]/max(s[0],1e-12));record['singular_ratio']=ratio
            if ratio<cfg['growth_min_singular_ratio']:reason.append('UNDERCONSTRAINED_GROWTH')
            d=np.linalg.lstsq(J,r,rcond=None)[0];fit=float(np.linalg.norm(J@d-r)/max(np.linalg.norm(r),1e-12));record.update(inconsistency=fit,linearized_length_mm=float(np.linalg.norm(d)))
            if fit>cfg['growth_max_inconsistency']:reason.append('CONFLICTING_MULTIVIEW_RESIDUALS')
            if np.linalg.norm(d)<cfg['growth_min_mm']:reason.append('NO_SIGNIFICANT_MISSING_LENGTH')
            tri=V[F[patch]];n=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]).sum(0)
            if n@d<=0:reason.append('INWARD_GROWTH')
            if body['inferred_base_faces'][patch].any()or body['boundary_vertex'][np.unique(F[patch])].any():reason.append('FROZEN_BASE_ATTACHMENT')
            if not reason:
                out.append(dict(seed=seed,patch=patch,delta=d,support_views=sorted(groups),support_videos=videos,singular_ratio=ratio,inconsistency=fit,predicted_pixel_improvement=float(np.linalg.norm(r)-np.linalg.norm(J@d-r))))
        record['rejections']=reason;records.append(record)
    out.sort(key=lambda e:(-e['predicted_pixel_improvement'],e['seed']))
    return out[:cfg['growth_candidates']],dict(support_rows=len(evidence),eligible_patches=len(out),seed_diagnostics=records)
