"""Geometry-only visibility responses; no V-FUSE CNN, no geometry edits."""
from sampling import *
from scipy.special import expit
from scipy.ndimage import distance_transform_edt
@lru_cache(None)
def image_safety(cid):
    lab=source(cid)['labels'];return distance_transform_edt(lab==1),distance_transform_edt(lab!=2)
def width(cid,z):return np.maximum(protocol()['depth_halfwidth_mm'],protocol()['depth_footprints']*np.asarray(z)/min(source(cid)['K'][0,0],source(cid)['K'][1,1]))
@lru_cache(None)
def parent_hashes(cid):return frozenset(v['sha256']for v in source(cid)['row']['HERO_upstream_RGB'])
@lru_cache(None)
def jaccard(a,b):
    x,y=parent_hashes(a),parent_hashes(b);return len(x&y)/len(x|y)
def correlation_weights(origin,observers):
    return {b:1/(1+jaccard(origin,b)+sum(jaccard(b,k)for k in observers if k!=b))for b in observers}
def peer_evidence(origin,observer,X,N,own_visible,origin_anchor=None,origin_align=None):
    p=protocol();a=source(origin);b=source(observer);m=model(observer);X=np.asarray(X,float);q=pf(observer).query(X);mesh=model(observer).query(X)
    z=q['source_Z_mm'];D=q['native_Z_mm'];M=q['original_mesh_Z_mm'];delta=D-z;raw_delta=M-z
    anchor=X if origin_anchor is None else np.broadcast_to(origin_anchor,X.shape);_,za=vis.project_camera(anchor,a['K'],a['T']);rayA=(anchor-a['T'][:3,3])/za[:,None]
    tauA=width(origin,za);factor=abs(rayA@b['T'][:3,2]);tauB=width(observer,D);tau=tauB+tauA*factor
    numeric=np.isfinite(delta)&(D>0)&(z>0);safe_tau=np.where(numeric,tau,1.);S=np.zeros(len(X));O=np.zeros(len(X));F=np.zeros(len(X));S[numeric]=np.exp(-.5*(delta[numeric]/safe_tau[numeric])**2);O[numeric]=expit((-delta[numeric]-safe_tau[numeric])/(.25*safe_tau[numeric]));F[numeric]=expit((delta[numeric]-safe_tau[numeric])/(.25*safe_tau[numeric]))
    flags=q['reliability_factors'];minimum=numeric&flags['Mask_Polyp']&~q['cad_occluded']&~flags['CAD_depth_contradiction']
    behind=minimum&(delta < -tau);native_free=minimum&(delta>tau);raw_numeric=np.isfinite(M)&(M>0);raw_free=raw_numeric&(raw_delta>tau)
    align=raw_numeric&(abs(D-M)<=p['native_Raw_alignment_mm']);fid=q['original_face_id'];goodfid=(fid>=0)&(fid<len(b['F']));ff=np.clip(fid,0,len(b['F'])-1)
    target_quality=goodfid&(~m.boundary_face[ff])&(~m.stretch[ff])&(m.coherence[ff]>=p['normal_coherence_min'])
    uv=q['source_pixel'];inside=(uv[:,0]>=0)&(uv[:,0]<640)&(uv[:,1]>=0)&(uv[:,1]<360);mask_safe=np.zeros(len(X),bool);ids=np.flatnonzero(inside)
    dt,dr=image_safety(observer);mask_safe[ids]=(dt[uv[ids,1],uv[ids,0]]>=p['mask_inner_distance_px'])&(dr[uv[ids,1],uv[ids,0]]>=p['Ring_mask_distance_px'])
    first_before_cad=raw_numeric&(M<=q['CAD_Z_mm']+p['ordering_epsilon_mm']);rayB=(X-b['T'][:3,3])/np.maximum(z[:,None],1e-20);unitB=rayB/np.maximum(np.linalg.norm(rayB,axis=1,keepdims=True),1e-20)
    incidence=abs((unitB*m.N[ff]).sum(1));target_quality&=incidence>=p['incidence_abs_min']
    normal_agree=abs((N*model(observer).N[mesh['original_face_id']]).sum(1))
    if origin_align is None:
        qa=pf(origin).query(anchor);origin_align=np.isfinite(qa['native_Z_mm'])&np.isfinite(qa['original_mesh_Z_mm'])&(abs(qa['native_Z_mm']-qa['original_mesh_Z_mm'])<=p['native_Raw_alignment_mm'])
    # Axial interval converts to a conservative Euclidean ray-displacement gate;
    # no UDF/projective scalar values are averaged.
    raw_near=mesh['raw_udf_mm']<=tau*np.linalg.norm(rayB,axis=1)
    support1=(S>=p['support_count_response_min'])&minimum
    support_eligible3=minimum&align&origin_align&first_before_cad&mask_safe&raw_near&(normal_agree>=p['support_abs_normal_cos_min'])&~mesh['ambiguous']
    support3=(S>=p['support_count_response_min'])&support_eligible3
    free3=native_free&raw_free&align&origin_align&first_before_cad&target_quality&mask_safe&own_visible
    qcam=.5 if b['row']['parent_camera_candidate_N']else 1.
    reason=np.zeros(len(X),np.uint32);reason[~numeric]|=1;reason[numeric&~flags['Mask_Polyp']]|=2;reason[q['cad_occluded']]|=4;reason[flags['CAD_depth_contradiction']]|=8
    reason[~align&numeric]|=16;reason[native_free&~raw_free]|=32;reason[~target_quality]|=64;reason[~mask_safe]|=128;reason[~own_visible]|=256;reason[mesh['ambiguous']]|=512;reason[normal_agree<p['support_abs_normal_cos_min']]|=1024;reason[~origin_align]|=2048
    return dict(S=S,O=O,F=F,numeric=numeric,minimum=minimum,behind=behind,cad=q['cad_occluded'],ambiguous=q['ambiguous']|mesh['ambiguous'],native_free=native_free,raw_free=raw_free,free3=free3,
        support0=(S>=p['support_count_response_min'])&numeric,support1=support1,support3=support3,support_eligible3=support_eligible3,align=align,native_only=native_free&~raw_free,mask_safe=mask_safe,target_quality=target_quality,
        delta=delta,raw_delta=raw_delta,tau=tau,D=D,M=M,z=z,reason=reason,raw_udf=mesh['raw_udf_mm'],normal_agree=normal_agree,observer_first_face_id=fid,
        origin_align=origin_align,qcam=np.full(len(X),qcam),strict_chain=np.full(len(X),a['row']['parent_camera_candidate_N']==0 and b['row']['parent_camera_candidate_N']==0))
def observer_file(a,b):return R/'local_results/pairs'/f'{a}__{b}.npz'
def calculate_stage(stage):
    p=R/'local_results/pairs';p.mkdir(exist_ok=True);total=0
    for sid in scene_ids():
        active=stages(sid)[stage]
        for origin in ordered_sources(sid):
            c=candidates(origin)
            for observer in active:
                if observer==origin:continue
                path=observer_file(origin,observer)
                if path.exists():continue
                t=peer_evidence(origin,observer,c['XYZ'],c['normal'],c['own_visible'],origin_align=c['origin_native_Raw_alignment']);np.savez_compressed(path,**t);total+=len(c['XYZ'])
            print('OBSERVATIONS',stage,origin,'candidate_N',len(c['XYZ']),flush=True)
    return total
def classify(c,support,free,cad,unknown,unresolved):
    n=len(c['face_id']);label=np.full(n,'UNKNOWN',dtype='<U40');label[c['own_visible']]='SINGLE_SUPPORTED_UNVERIFIED'
    total_support=support+c['own_visible'];label[(total_support==1)&(free==0)]='SINGLE_SUPPORTED_UNVERIFIED';label[(total_support>=2)&(free==0)]='MULTI_SUPPORTED';label[(support==0)&(free==0)&~c['own_visible']&(cad>0)]='CAD_OCCLUDED'
    label[unresolved&(support==0)&(free==0)]='CORRESPONDENCE_UNRESOLVED';label[free>0]='FREE_SPACE_CONFLICT';return label
def reduce(origin,stage,variant,matched_support=False):
    c=candidates(origin);active=[b for b in stages(CC[origin]['scene_id'])[stage]if b!=origin];n=len(c['XYZ']);support=np.zeros(n,int);free=np.zeros(n,int);cad=np.zeros(n,int);occluded=np.zeros(n,int);valid=np.zeros(n,int);unknown=np.zeros(n,int);rawS=np.zeros(n);rawO=np.zeros(n);rawF=np.zeros(n);normS=np.zeros(n);normO=np.zeros(n);normF=np.zeros(n);unresolved=np.zeros(n,bool);native_only=np.zeros(n,int);discret=np.zeros(n,int);strictfree=np.zeros(n,int)
    weights=correlation_weights(origin,active)
    for b in active:
        q=np.load(observer_file(origin,b));S=q['S'];O=q['O'];F=q['F'];v3=variant==3;sc=q['support0']if variant==0 and not matched_support else q['support3']if v3 else q['support1'];fc=q['free3']if v3 else q['native_free']if variant==2 else np.zeros(n,bool)
        sg=q['numeric']if variant==0 and not matched_support else(q['support_eligible3']if v3 else q['minimum']);og=q['minimum']if variant>0 else np.zeros(n,bool);fg=q['minimum']if variant==2 else q['free3']if v3 else np.zeros(n,bool)
        support+=sc;free+=fc;cad+=q['cad']if variant>0 else 0;occluded+=q['behind']if variant>0 else 0;valid+=q['minimum'];unknown+=~(q['minimum']|q['cad'])
        if variant>0:unresolved|=q['ambiguous']
        if v3:unresolved|=(q['native_free']&~q['free3'])|(~q['origin_align']&q['minimum'])
        rawS+=S*sg;rawO+=O*og;rawF+=F*fg;w=weights[b]*q['qcam'];normS+=w*S*sg;normO+=w*O*og;normF+=w*F*fg;native_only+=q['native_only'];discret+=q['native_free']&~q['align'];strictfree+=fc&q['strict_chain']
    label=classify(c,support,free,cad,unknown,unresolved)
    return dict(label=label,support=support,free=free,cad=cad,occluded=occluded,valid=valid,unknown=unknown,rawS=rawS,rawO=rawO,rawF=rawF,normS=normS,normO=normO,normF=normF,
        unresolved=unresolved,native_only=native_only,discret=discret,strictfree=strictfree,observer_N=len(active),vote_mass=sum(weights[b]*(.5 if source(b)['row']['parent_camera_candidate_N']else 1)for b in active))
