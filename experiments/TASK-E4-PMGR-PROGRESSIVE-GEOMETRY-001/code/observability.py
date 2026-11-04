"""Whitened residual FD, censored-row intersection, compact SVD projection."""
from losses import *
import time
def decompose(J,rtol=1e-3):
    U,s,_=np.linalg.svd(J,full_matrices=False);rank=int((s>max(float(s[0])*rtol,1e-10)).sum())if len(s)else 0
    return U[:,:rank],s,rank
@torch.no_grad()
def jacobian(p,a):
    cache=R/'runtime'/f'P0_J_{p.scene}_{p.initial}.npz';meta=cache.with_suffix('.json')
    if np.max(abs(a))==0 and cache.exists():
        data=dict(np.load(cache));info=load(meta);assert info['code_sha256']==sha(Path(__file__))
        return dict(data,rank=info['rank'],condition=info['condition'],row_count=info['row_count'],valid_row_N=info['valid_row_N'],censored_row_N=info['censored_row_N'],seconds=0.,render_calls=0,fd_controls=info['fd_controls'],shared_P0_cache=True)
    start=time.monotonic();calls=p.renderer.calls;V=p.vertices(tensor(a));r,parts=p.parts(V,return_vector=True);cols=[];valids=[np.isfinite(r)];h=.01
    directions=[p.b['G'][:,:,j]/max(1e-10,np.linalg.norm(p.b['G'][:,:,j],axis=1).max())for j in range(9)]+[p.b['n']*p.b['phi'][:,j,None]for j in range(128)]
    fd_controls=[]
    for k,d in enumerate(directions):
        rp,_=p.parts(V+tensor(d)*h,return_vector=True);rm,_=p.parts(V-tensor(d)*h,return_vector=True);valid=np.isfinite(rp)&np.isfinite(rm);cols.append((rp-rm)/(2*h));valids.append(valid)
        if k in [9,21,53,136]:
            r2p,_=p.parts(V+tensor(d)*.005,return_vector=True);r2m,_=p.parts(V-tensor(d)*.005,return_vector=True);v=valid&np.isfinite(r2p)&np.isfinite(r2m);d2=(r2p-r2m)/.01;d1=cols[-1];fd_controls.append(dict(column=k,valid_N=int(v.sum()),relative_norm_disagreement=float(np.linalg.norm((d2-d1)[v])/max(np.linalg.norm(d1[v]),1e-12))))
    keep=np.logical_and.reduce(valids);J=np.stack(cols,1)[keep];rr=r[keep];nview=len(parts);fullrows=len(r)//nview;view_index=(np.flatnonzero(keep)//fullrows)
    Q,sv,rank=decompose(J);visible=p.visibility(V.cpu().numpy())
    result=dict(J=J,r=rr,view_index=view_index,singular_values=sv,rank=rank,condition=float(sv[0]/sv[rank-1])if rank else None,row_count=len(r),valid_row_N=int(keep.sum()),censored_row_N=int((~keep).sum()),seconds=time.monotonic()-start,render_calls=p.renderer.calls-calls,fd_controls=fd_controls,visible=visible)
    if np.max(abs(a))==0:
        np.savez_compressed(cache,**{k:result[k]for k in ['J','r','view_index','singular_values','visible']});meta.write_text(json.dumps(clean({k:result[k]for k in ['rank','condition','row_count','valid_row_N','censored_row_N','fd_controls']}|dict(code_sha256=sha(Path(__file__)))),indent=2))
    return result
def analyze(p,jac,active,budget):
    J=jac['J'];r=jac['r'];Ji=J[:,9:];old=np.r_[np.arange(9),9+np.asarray(active,int)];Q,_,_=decompose(J[:,old]);rows=[];mass=p.b['mass'];energy=(p.b['phi']**2)*mass[:,None]
    vg=np.array([Ji[jac['view_index']==i].T@r[jac['view_index']==i]for i in range(len(p.ids))]);norm=np.linalg.norm(vg,axis=1);cos=vg@vg.T/np.maximum(norm[:,None]*norm[None,:],1e-15)
    released=list(active);view_energy=np.array([(e[:,None]*energy).sum(0)/energy.sum(0)for e in jac['visible']])
    for k in range(128):
        v=Ji[:,k];vn=np.linalg.norm(v);proj=v-Q@(Q.T@v);ratio=np.linalg.norm(proj)/max(vn,1e-15);support=np.flatnonzero(view_energy[:,k]>=.05);blocks={GATE[p.ids[i]]['block']for i in support};g=vg[support,k];pos=g[g>0].sum();neg=-g[g<0].sum();conflict=float(min(pos,neg)/max(pos+neg,1e-15));why=[]
        if k in active:status='RETAINED'
        elif k>=budget:status='OUTSIDE_STAGE_BUDGET'
        else:
            if vn<.01:why.append('UNOBSERVABLE_J')
            if not len(support):why.append('NO_VISIBLE_SUPPORT')
            if ratio<.05:why.append('REDUNDANT_INFORMATION')
            if conflict>.35:why.append('CROSS_VIEW_CONFLICT')
            status='REJECTED'if why else'RELEASED'
            if not why:
                released.append(k)
                if np.linalg.norm(proj)>1e-10:Q=np.c_[Q,proj/np.linalg.norm(proj)]
        label='MULTI_INDEPENDENT_CONSISTENT'if len(blocks)>=2 and conflict<=.35 else'SINGLE_PARTITION_LOW_CONFIDENCE'if len(blocks)==1 else'UNOBSERVED_OR_CONFLICTED'
        rows.append(dict(mode=k,frequency=float(p.b['lam'][k]),status=status,reasons=why,J_norm=float(vn),independent_ratio=float(ratio),source_support_N=len(support),partition_support_N=len(blocks),support_sources=[p.ids[i]for i in support],support_energy=view_energy[:,k],view_gradients=vg[:,k],gradient_conflict_fraction=conflict,classification=label,camera_qualified_statistical_independence=False))
    return released,rows,dict(cosine=cos,view_gradient_norm=norm,rank=jac['rank'],condition=jac['condition'],singular_values=jac['singular_values'],valid_row_N=jac['valid_row_N'],censored_row_N=jac['censored_row_N'],fd_controls=jac['fd_controls'])
