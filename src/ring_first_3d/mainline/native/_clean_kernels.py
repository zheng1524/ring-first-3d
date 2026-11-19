# Exact project-owned 017/Phase-C functions; no new cleaning thresholds.

def face_components(faces):
    if not len(faces):return np.empty(0,int)
    edges=np.sort(faces[:,[[0,1],[1,2],[2,0]]].reshape(-1,2),axis=1);ids=np.repeat(np.arange(len(faces)),3);order=np.lexsort((edges[:,1],edges[:,0]));e=edges[order];f=ids[order];same=np.all(e[1:]==e[:-1],axis=1);a,b=f[:-1][same],f[1:][same]
    graph=coo_matrix((np.ones(2*len(a)),(np.r_[a,b],np.r_[b,a])),shape=(len(faces),len(faces))).tocsr()
    return connected_components(graph,directed=False)[1]

def edge_counts(faces):
    e=np.sort(faces[:,[[0,1],[1,2],[2,0]]].reshape(-1,2),axis=1)
    return np.unique(e,axis=0,return_counts=True)

def features(pack,raw):
    conf=cfg();P=raw['XYZ_mm'];uv=raw['pixel_uv'];n=len(P);valid=raw['numeric_valid'];assert valid.all(),'invalid source points require explicit input branch stop'
    tree=cKDTree(P);distance,neighbors=tree.query(P,k=max(conf['normal_k'],conf['knn_k'])+1,workers=1)
    k=conf['knn_k'];rk=distance[:,k];knn_density=k/(np.pi*np.maximum(rk,1e-12)**2)
    count=tree.query_ball_point(P,conf['radius_mm'],return_length=True,workers=1)-1
    rho=count/(np.pi*conf['radius_mm']**2);rho3=count/((4/3)*np.pi*conf['radius_mm']**3)
    Q=P[neighbors[:,1:conf['normal_k']+1]];Q=Q-Q.mean(1,keepdims=True);cov=np.einsum('nki,nkj->nij',Q,Q)/conf['normal_k'];ev,vec=np.linalg.eigh(cov);normal=vec[:,:,0]
    nc=normal@pack['pose'][:3,:3];ray=np.c_[uv,np.ones(n)]@np.linalg.inv(pack['K']).T;raynorm=np.linalg.norm(ray,axis=1);dot=np.abs(np.sum(nc*ray,axis=1));cos=dot/raynorm
    nonplanarity=np.maximum(ev[:,0],0)/np.maximum(ev.sum(1),1e-18);tangent_ratio=np.maximum(ev[:,1],0)/np.maximum(ev[:,2],1e-18)
    reliable=(cos>=conf['minimum_cos_incidence'])&(nonplanarity<=conf['maximum_nonplanarity'])&(tangent_ratio>=conf['minimum_tangent_eigen_ratio'])
    z=raw['raw_depth_mm'];expected=pack['K'][0,0]*pack['K'][1,1]*dot/z**2
    norm_radius=np.where(reliable,rho/expected,np.nan);norm_knn=np.where(reliable,knn_density/expected,np.nan);norm=np.minimum(norm_radius,norm_knn)
    lookup=np.full(pack['labels'].shape,-1,int);lookup[uv[:,1],uv[:,0]]=np.arange(n);edge_i=[];edge_j=[];edge_px=[]
    for dx,dy in conf['source_neighbors']:
        xy=uv+[dx,dy];inside=(xy[:,0]>=0)&(xy[:,0]<lookup.shape[1])&(xy[:,1]>=0)&(xy[:,1]<lookup.shape[0]);ii=np.flatnonzero(inside);jj=lookup[xy[ii,1],xy[ii,0]];ok=jj>=0;edge_i.append(ii[ok]);edge_j.append(jj[ok]);edge_px.append(np.full(ok.sum(),np.hypot(dx,dy)))
    i=np.concatenate(edge_i);j=np.concatenate(edge_j);px=np.concatenate(edge_px);length=np.linalg.norm(P[i]-P[j],axis=1)
    ray_step=np.linalg.norm(ray[i]-ray[j],axis=1);perspective_length=.5*(z[i]+z[j])*ray_step
    ni_ri=np.sum(nc[i]*ray[i],axis=1);ni_rj=np.sum(nc[i]*ray[j],axis=1);nj_rj=np.sum(nc[j]*ray[j],axis=1);nj_ri=np.sum(nc[j]*ray[i],axis=1)
    with np.errstate(divide='ignore',invalid='ignore'):
        zj=z[i]*ni_ri/ni_rj;zi=z[j]*nj_rj/nj_ri
        e1=np.linalg.norm(zj[:,None]*ray[j]-z[i,None]*ray[i],axis=1);e2=np.linalg.norm(zi[:,None]*ray[i]-z[j,None]*ray[j],axis=1);expect=.5*(e1+e2)
        stretch=length/expect
    edge_good=reliable[i]&reliable[j]&np.isfinite(stretch)&(expect>1e-10)&(zj>0)&(zi>0)
    gradient=np.abs(np.log(np.maximum(norm[i],1e-9))-np.log(np.maximum(norm[j],1e-9)))/px
    grad_phys=gradient*px/np.maximum(length,1e-9)
    def maximum(values,mask):
        result=np.zeros(n);degree=np.zeros(n,int)
        for ids in [i,j]:np.maximum.at(result,ids[mask],values[mask]);np.add.at(degree,ids[mask],1)
        result[degree==0]=np.nan;return result,degree
    edge_max,_degree=maximum(length,np.ones(len(i),bool));persp_max,_=maximum(length/np.maximum(perspective_length,1e-12),np.ones(len(i),bool));stretch_max,degree=maximum(stretch,edge_good);grad,_=maximum(gradient,edge_good&np.isfinite(gradient));grad_m,_=maximum(grad_phys,edge_good&np.isfinite(grad_phys))
    d0=np.clip(norm,0,1);continuity=1/(1+np.maximum(stretch_max-1,0)+grad/np.log(2));d1=np.maximum(d0,continuity)
    # D0 requires reliable normal; D1 additionally requires usable source adjacency.
    d0[~reliable]=np.nan;d1[(~reliable)|(degree==0)]=np.nan
    return dict(XYZ_mm=P,source_u=uv[:,0],source_v=uv[:,1],radius_neighbor_count=count,rho_surface_radius=rho,rho_volume_radius=rho3,knn_nearest_mm=distance[:,1],knn_median_mm=np.median(distance[:,1:k+1],axis=1),knn_k_distance_mm=rk,rho_knn=knn_density,normal_world=normal,cos_incidence=cos,nonplanarity=nonplanarity,tangent_eigen_ratio=tangent_ratio,rho_expected=expected,pixel_area_expected_mm2=1/expected,normalization_reliable=reliable,rho_normalized_radius=norm_radius,rho_normalized_knn=norm_knn,rho_normalized=norm,adjacency_length_max_mm=edge_max,adjacency_perspective_stretch_max=persp_max,adjacency_tangent_stretch_max=stretch_max,gradient_log_per_pixel=grad,gradient_log_per_mm=grad_m,valid_adjacency_degree=degree,D0=d0,D1=d1,D0_candidate=np.isfinite(d0)&(d0<conf['score_threshold']),D1_candidate=np.isfinite(d1)&(d1<conf['score_threshold']),boundary=raw['distance_Polyp_boundary_px']<=conf['mask_boundary_px'],Ring_near=raw['distance_Ring_px']<=conf['Ring_neighbor_px'])

def native_grid(z,lab,K,T):
    valid=np.isfinite(z)&(z>0)&(lab==1);y,x=np.nonzero(valid);uv=np.c_[x,y];P=unproject(z[y,x],T,uv,K)
    ids=np.full(z.shape,-1,int);ids[y,x]=np.arange(len(x));a=ids[:-1,:-1];b=ids[:-1,1:];c=ids[1:,:-1];d=ids[1:,1:]
    fs=[];lattice=[];q=np.arange((z.shape[0]-1)*(z.shape[1]-1)).reshape(a.shape)
    for side,t in enumerate([np.stack([a,b,c],-1),np.stack([b,d,c],-1)]):
        good=(t>=0).all(-1);fs.append(t[good]);lattice.append(2*q[good]+side)
    return P,np.concatenate(fs),uv,np.concatenate(lattice)

def mapped_labels(labels,K,Kn,shape):
    y,x=np.mgrid[:shape[0],:shape[1]];uv=np.c_[x.ravel(),y.ravel()];q=np.c_[uv,np.ones(len(uv))]@np.linalg.inv(Kn).T@K.T;q=q[:,:2]/q[:,2:];px=np.floor(q+.5).astype(int);inside=(px[:,0]>=0)&(px[:,0]<labels.shape[1])&(px[:,1]>=0)&(px[:,1]<labels.shape[0]);lab=np.full(len(uv),255,np.uint8);lab[inside]=labels[px[inside,1],px[inside,0]]
    return lab.reshape(shape),px.reshape(*shape,2)

def topology(P,F,T):
    tri=P[F];cross=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);twice=np.linalg.norm(cross,axis=1);N=cross/np.maximum(twice[:,None],1e-30);cent=tri.mean(1);N[((T[:3,3]-cent)*N).sum(1)<0]*=-1
    acc=np.zeros_like(P);w=np.zeros(len(P))
    for j in range(3):np.add.at(acc,F[:,j],N*twice[:,None]);np.add.at(w,F[:,j],twice)
    coherence=(np.linalg.norm(acc,axis=1)/np.maximum(w,1e-30))[F].min(1)
    ed=np.sort(F[:,[[0,1],[1,2],[2,0]]].reshape(-1,2),1);ids=np.repeat(np.arange(len(F)),3);order=np.lexsort((ed[:,1],ed[:,0]));e=ed[order];ii=ids[order];same=(e[1:]==e[:-1]).all(1);a=ii[:-1][same];b=ii[1:][same];angle=np.degrees(np.arccos(np.clip((N[a]*N[b]).sum(1),-1,1)));maxangle=np.zeros(len(F));np.maximum.at(maxangle,a,angle);np.maximum.at(maxangle,b,angle)
    edges,counts=edge_counts(F);boundary=np.unique(edges[counts==1]);nonmanifold=np.unique(edges[counts>2]);bf=np.isin(F,boundary).any(1)
    lengths=np.linalg.norm(tri[:,[1,2,0]]-tri,axis=2);quality=2*np.sqrt(3)*twice/np.maximum((lengths**2).sum(1),1e-30)
    return dict(area=twice*.5,normal=N,centroid=cent,coherence=coherence,normal_angle=maxangle,quality=quality,edge_max=lengths.max(1),boundary_face=bf,degenerate=twice<2e-12,component=face_components(F),edges=edges,edge_count=counts,neighbor_a=a,neighbor_b=b,nonmanifold_face=np.isin(F,nonmanifold).any(1))

def classify(f,t):
    # Only this function can assign REJECTED. No group ID, GT or deletion quota.
    severe=(f['perspective_stretch']>t['stretch_perspective'])&(f['tangent_stretch']>t['stretch_tangent'])&f['tangent_reliable']
    depth=f['native_depth_jump_mm']>t['native_depth_jump_mm']
    shape=(f['triangle_quality']<t['needle_quality'])|(f['normal_coherence']<t['normal_coherence'])|(f['normal_angle_deg']>t['neighbor_angle_deg'])
    context=f['boundary_distance_native_px']<=t['edge_native_px']
    cad=f['CAD_inside_samples']>=t['ring_inside_samples_min']
    unbound=~f['native_mask_supported']
    # A surface behind CAD is legitimate unknown; a sample strictly INSIDE CAD
    # is a distinct geometric contradiction, not merely a hidden surface.
    unknown=unbound|(~f['tangent_reliable'])|(f['incidence_min']<t['incidence_min'])|(f['CAD_occluded']&~cad)
    reject_rim=severe&depth&shape&context&~unknown
    reject_cad=cad&depth&shape&~unknown
    rejected=reject_rim|reject_cad
    signs=(f['perspective_stretch']>t['stretch_perspective'])|depth|shape|(f['density_normalized']<t['density_warning'])|cad|f['nearest_competition']|f['boundary_face']|f['minor_component']|f['nonmanifold']
    state=np.zeros(len(rejected),np.uint8);state[signs]=1;state[unknown]=3;state[rejected]=2
    reason=np.zeros(len(state),np.uint16)
    for bit,flag in enumerate([severe,depth,shape,context,cad,f['nearest_competition'],f['boundary_face'],f['minor_component'],unbound,unknown,reject_rim,reject_cad,f['nonmanifold']]):reason[flag]|=1<<bit
    return state,reason

def analyze(s,ring,t):
    P,F=s['P'],s['F'];pack=s['pack'];T=s['T'];tri=P[F];n=len(F)
    uv0=s['uv'];dp=distance_transform_edt(pack['labels']==1);dr=distance_transform_edt(pack['labels']!=2)
    raw=dict(XYZ_mm=P,pixel_uv=uv0,numeric_valid=np.isfinite(P).all(1),raw_depth_mm=((P-T[:3,3])@T[:3,:3])[:,2],distance_Polyp_boundary_px=dp[uv0[:,1],uv0[:,0]],distance_Ring_px=dr[uv0[:,1],uv0[:,0]])
    vf=features(pack,raw);top=topology(P,F,T)
    perspective=vf['adjacency_perspective_stretch_max'][F].max(1);tangent=vf['adjacency_tangent_stretch_max'][F];good=np.isfinite(tangent).all(1)&vf['normalization_reliable'][F].all(1);tangent=np.where(np.isfinite(tangent),tangent,-np.inf).max(1);tangent[~good]=np.nan
    localdensity=vf['rho_normalized'][F];density=np.where(np.isfinite(localdensity),localdensity,np.inf).min(1);density[~np.isfinite(density)]=np.nan
    sd=ring.compute_signed_distance(o3d.core.Tensor(P.astype(np.float32)),nsamples=3).numpy()
    bary=np.array([[.5,.5,0],[0,.5,.5],[.5,0,.5],[1/3,1/3,1/3]])
    sample=np.einsum('sk,nkj->nsj',bary,tri);other=ring.compute_signed_distance(o3d.core.Tensor(sample.reshape(-1,3).astype(np.float32)),nsamples=3).numpy().reshape(n,4);all_sd=np.c_[sd[F],other];negative=(all_sd < -t['ring_inside_mm']).sum(1)
    C=top['centroid'];cam=(C-T[:3,3])@T[:3,:3];q=cam@s['K'].T;uv=q[:,:2]/q[:,2:];cad_z=cast(ring,uv,s['K'],T)['t_hit'].numpy();occluded=np.isfinite(cad_z)&(cam[:,2]>cad_z+.05)
    view=T[:3,3]-C;view/=np.maximum(np.linalg.norm(view,axis=1,keepdims=True),1e-20);faceinc=abs((view*top['normal']).sum(1))
    # Exact historical limited k-centroid competition screen, diagnostic only.
    competition=np.zeros(n,bool);nearest=np.full(n,np.inf);competitor=np.full(n,-1,int);tree=cKDTree(C);k=min(t['competition_k'],n)
    for start in range(0,n,512):
        ix=np.arange(start,min(n,start+512));_,candidate=tree.query(C[ix],k=k);candidate=np.asarray(candidate).reshape(len(ix),k)
        near=trimesh.triangles.closest_point(P[F[candidate.ravel()]],np.repeat(C[ix],k,axis=0)).reshape(len(ix),k,3);dist=np.linalg.norm(near-C[ix,None,:],axis=2);shares=(F[candidate][:,:,:,None]==F[ix][:,None,None,:]).any((2,3));dist[shares]=np.inf;j=dist.argmin(1);dd=dist[np.arange(len(ix)),j];nearest[ix]=dd;competitor[ix]=candidate[np.arange(len(ix)),j];competition[ix]=dd<=t['competition_mm']
    component=top['component'];ca=np.bincount(component,weights=top['area']);minor=ca[component]<t['small_component_area_fraction']*ca.max()
    f=dict(area_mm2=top['area'],edge_max_mm=top['edge_max'],perspective_stretch=perspective,tangent_stretch=tangent,tangent_reliable=good,triangle_quality=top['quality'],native_depth_jump_mm=np.ptp(s['nativez'][F],axis=1),normal_coherence=top['coherence'],normal_angle_deg=top['normal_angle'],density_normalized=density,
        boundary_distance_native_px=s['boundary_distance_native'][F].min(1),incidence_min=np.minimum(vf['cos_incidence'][F].min(1),faceinc),CAD_min_signed_mm=all_sd.min(1),CAD_nearest_sample_mm=abs(all_sd).min(1),CAD_inside_samples=negative,CAD_occluded=occluded,native_mask_supported=s['mask_ok'][F].all(1),boundary_face=top['boundary_face'],minor_component=minor,nonmanifold=top['nonmanifold_face'],nearest_competition=competition,competition_distance_mm=nearest,competitor_face_index=competitor,component=component)
    state,reason=classify(f,t)
    return f,state,reason,top

def patch_plane(z,lab,uv,direction,t):
    # Eight samples in the outward half-patch, excluding the tested endpoint.
    u,v=uv;dx,dy=direction;perp=np.array([-dy,dx]);offs=np.array([-a*np.array([dx,dy])+b*perp for a in [0,1,2]for b in [-1,0,1]if a!=0 or b!=0],int);p=uv+offs
    ok=(p[:,0]>=0)&(p[:,0]<z.shape[1])&(p[:,1]>=0)&(p[:,1]<z.shape[0]);pp=np.clip(p,[0,0],[z.shape[1]-1,z.shape[0]-1]);zz=z[pp[:,1],pp[:,0]];ok&=(lab[pp[:,1],pp[:,0]]==1)&np.isfinite(zz)&(zz>0)
    if ok.sum()<6:return None
    A=np.c_[offs[ok],np.ones(ok.sum())]
    if np.linalg.matrix_rank(A)<3:return None
    coef=np.linalg.lstsq(A,1/zz[ok],rcond=None)[0];pred=A@coef
    if (pred<=0).any():return None
    error=np.sqrt(np.mean((1/pred-zz[ok])**2))
    if error>t['native_depth_jump_mm']/4:return None
    # Endpoint was not used in plane fit: require independently supported endpoint.
    endpoint=1/coef[2]if coef[2]>0 else np.inf
    if abs(endpoint-z[v,u])>t['native_depth_jump_mm']/4:return None
    return coef,error,int(ok.sum())

def gap_edges(z,lab,K,T,P,F,uv,t):
    edge,_=edge_counts(F);a,b=edge.T;depth=z[uv[:,1],uv[:,0]];ray=np.c_[uv,np.ones(len(uv))]@np.linalg.inv(K).T
    length=np.linalg.norm(P[a]-P[b],axis=1);expected=(depth[a]+depth[b])/2*np.linalg.norm(ray[a]-ray[b],axis=1)
    candidate=(abs(depth[a]-depth[b])>t['native_depth_jump_mm'])&(length/np.maximum(expected,1e-20)>t['stretch_perspective'])
    rows=[];confirmed=[]
    for ix in np.flatnonzero(candidate):
        i,j=edge[ix];ui,uj=uv[i],uv[j];di=uj-ui
        if np.max(abs(di))!=1:continue
        q1=patch_plane(z,lab,ui,di,t);q2=patch_plane(z,lab,uj,-di,t);row=dict(vertex_i=int(i),vertex_j=int(j),pixel_i=int(ui[1]*z.shape[1]+ui[0]),pixel_j=int(uj[1]*z.shape[1]+uj[0]),u_i=int(ui[0]),v_i=int(ui[1]),u_j=int(uj[0]),v_j=int(uj[1]),depth_jump_mm=float(abs(depth[i]-depth[j])),raw_length_mm=float(length[ix]),confirmed=False,reason='INSUFFICIENT_ONE_SIDED_SUPPORT')
        if q1 is not None and q2 is not None:
            c1,e1,n1=q1;c2,e2,n2=q2;pzj=1/(c1[:2]@di+c1[2])if c1[:2]@di+c1[2]>0 else np.nan;pzi=1/(c2[:2]@(-di)+c2[2])if c2[:2]@(-di)+c2[2]>0 else np.nan
            L1=np.linalg.norm(pzj*ray[j]-depth[i]*ray[i]);L2=np.linalg.norm(pzi*ray[i]-depth[j]*ray[j]);ratio=length[ix]/max((L1+L2)/2,1e-20)
            inc=[]
            for c,u,k in [(c1,ui,i),(c2,uj,j)]:
                co=np.r_[c[:2],c[2]-c[:2]@u];normal=K.T@co;inc.append(abs(normal@ray[k])/(np.linalg.norm(normal)*np.linalg.norm(ray[k])))
            supported=np.isfinite(ratio)and ratio>t['stretch_tangent']and min(inc)>=t['incidence_min']and abs(pzj-depth[j])>t['native_depth_jump_mm']and abs(pzi-depth[i])>t['native_depth_jump_mm']
            row.update(plane_i_RMS_mm=e1,plane_j_RMS_mm=e2,plane_i_N=n1,plane_j_N=n2,predicted_j_mm=pzj,predicted_i_mm=pzi,two_sided_tangent_stretch=ratio,min_patch_incidence=min(inc),confirmed=bool(supported),reason='TWO_SUPPORTED_SURFACES_WITH_GAP'if supported else'EXTRAPOLATION_OR_INCIDENCE_NOT_CONCLUSIVE')
            if supported:confirmed.append(tuple(sorted([row['pixel_i'],row['pixel_j']])))
        rows.append(row)
    return set(confirmed),rows
