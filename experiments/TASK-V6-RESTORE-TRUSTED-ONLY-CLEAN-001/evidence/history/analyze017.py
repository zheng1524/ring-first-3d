from common017 import *
from scipy.ndimage import distance_transform_edt
import gzip
STATE_NAMES=np.array(['TRUSTED','UNCERTAIN','REJECTED','UNKNOWN'])
def mapped_labels(labels,K,Kn,shape):
    y,x=np.mgrid[:shape[0],:shape[1]];uv=np.c_[x.ravel(),y.ravel()];q=np.c_[uv,np.ones(len(uv))]@np.linalg.inv(Kn).T@K.T;q=q[:,:2]/q[:,2:];px=np.floor(q+.5).astype(int);inside=(px[:,0]>=0)&(px[:,0]<labels.shape[1])&(px[:,1]>=0)&(px[:,1]<labels.shape[0]);lab=np.full(len(uv),255,np.uint8);lab[inside]=labels[px[inside,1],px[inside,0]]
    return lab.reshape(shape),px.reshape(*shape,2)
def get_source(r,representation):
    z=np.load(r['native_depth'])['depth_mm'];K=np.array(r['K']);Kn=np.array(r['Kn']);T=np.array(r['T']);labels=np.asarray(Image.open(r['Mask']));nlab,_=mapped_labels(labels,K,Kn,z.shape)
    if representation=='NATIVE_GRID':
        P,F,uv,lattice=native_grid(z,nlab,Kn,T);pack=dict(depth_mm=z,labels=nlab,K=Kn,pose=T);faceid=lattice;original_vertex_id=uv[:,1]*z.shape[1]+uv[:,0];identity_error=0.
    else:
        m=trimesh.load(r['archive_mesh'],process=False);P=np.asarray(m.vertices).copy();F=np.asarray(m.faces).copy();pack=dict(np.load(r['archive_pack']))
        pcam=(P-T[:3,3])@T[:3,:3];q=pcam@K.T;up=q[:,:2]/q[:,2:];uv=np.floor(up+.5).astype(int);identity_error=float(abs(up-uv).max());assert identity_error<.002
        assert ((uv>=0)&(uv<[labels.shape[1],labels.shape[0]])).all()
        pred=unproject(pack['depth_mm'][uv[:,1],uv[:,0]],T,uv,K);assert np.max(abs(pred-P))<1e-5
        if r.get('archive_points'):
            q=np.load(r['archive_points']);p=next(q[k]for k in ['XYZ_mm','points_mm']if k in q);u=next((q[k]for k in ['source_uv','pixel_uv','uv']if k in q),None)
            if u is None:u=np.c_[q['source_u'],q['source_v']]
            assert np.array_equal(uv,u)and np.max(abs(P-p))<1e-5
            if 'original_faces'in q:assert np.array_equal(F,q['original_faces'])
        faceid=np.arange(len(F));original_vertex_id=np.arange(len(P))
    # Physical projection maps archived pixels to original native sample centres.
    q=np.c_[uv,np.ones(len(uv))]@np.linalg.inv(pack['K']).T@Kn.T;nu=q[:,:2]/q[:,2:];px=np.floor(nu+.5).astype(int);in_native=(px[:,0]>=0)&(px[:,0]<z.shape[1])&(px[:,1]>=0)&(px[:,1]<z.shape[0]);safe=np.clip(px,[0,0],[z.shape[1]-1,z.shape[0]-1]);nativez=z[safe[:,1],safe[:,0]];nativeid=safe[:,1]*z.shape[1]+safe[:,0];nativeid[~in_native]=-1
    d=distance_transform_edt(np.pad(nlab==1,1))[1:-1,1:-1];edge=d[safe[:,1],safe[:,0]]
    ndvalid=in_native&np.isfinite(nativez)&(nativez>0);maskok=ndvalid&(nlab[safe[:,1],safe[:,0]]==1)
    return dict(P=P,F=F,uv=uv,pack=pack,T=T,K=pack['K'],Kn=Kn,native_uv=nu,native_pixel_id=nativeid,nativez=nativez,native_ok=ndvalid,mask_ok=maskok,boundary_distance_native=edge,face_id=faceid,original_vertex_id=original_vertex_id,native_shape=z.shape,native_labels=nlab,identity_error_px=identity_error)

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

def components_summary(P,F,keep,area):
    old=face_components(F);ca=np.bincount(old,weights=area);main=old==ca.argmax();kf=F[keep];new=face_components(kf)if len(kf)else np.array([],int);cnew=np.bincount(new,weights=area[keep])if len(new)else np.array([]);parts=np.bincount(new[main[keep]],weights=area[keep][main[keep]])if main[keep].any()else np.array([])
    oe,oc=edge_counts(F);ne,nc=edge_counts(kf)if len(kf)else(np.empty((0,2),int),np.array([],int));oldboundary=set(map(tuple,oe[oc==1]));newboundary=set(map(tuple,ne[nc==1]));removed=~keep;rc=face_components(F[removed])if removed.any()else np.array([],int);oldboundaryvertices=np.unique(oe[oc==1]);interior=0
    for j in np.unique(rc):
        if not np.isin(F[removed][rc==j],oldboundaryvertices).any():interior+=1
    return dict(raw_components=len(ca),clean_components=len(cnew),raw_largest_area_mm2=float(ca.max()),raw_largest_area_retained_fraction=float(area[keep&main].sum()/ca.max()),largest_remaining_piece_of_raw_main_fraction=float(parts.max()/ca.max())if len(parts)else 0.,new_boundary_edges=len(newboundary-oldboundary),interior_removed_patches=interior,raw_nonmanifold_edges=int((oc>2).sum()),clean_nonmanifold_edges=int((nc>2).sum()))

def coverage(s,keep,ring):
    h,w=s['native_shape'];y,x=np.nonzero((s['native_labels']==1));uv=np.c_[x,y];old=scene(s['P'],s['F']);new=scene(s['P'],s['F'][keep])if keep.any()else None
    a=cast(old,uv,s['Kn'],s['T'])['t_hit'].numpy();b=cast(new,uv,s['Kn'],s['T'])['t_hit'].numpy()if new else np.full(len(uv),np.inf);cad=cast(ring,uv,s['Kn'],s['T'])['t_hit'].numpy();valid=np.isfinite(a)&(a<cad-.002);ret=valid&np.isfinite(b)&(b<cad-.002);same=ret&(abs(a-b)<.01)
    return dict(original_mask_native_rays=len(uv),original_visible_mesh_hits=int(valid.sum()),retained_visible_hits=int(ret.sum()),original_first_surface_retained=int(same.sum()),first_surface_retention_fraction=float(same.sum()/max(1,valid.sum())),new_no_hit_count=int((valid&~ret).sum()),changed_first_surface_count=int((ret&~same).sum()))

def main():
    frozen=load(R/'provenance/PREANALYSIS_FREEZE.json')
    for p in frozen['files']:assert sha(p['path'])==p['sha256'],p['path']
    t=load(R/'config/PROTOCOL.json')['thresholds'];rows=[];audit=[]
    for r in load(R/'config/SOURCE_LOCK.json'):
        rm=trimesh.load(r['ring'],process=False);assert rm.is_watertight and rm.is_winding_consistent;ring=scene(rm.vertices,rm.faces)
        for rep in ['ARCHIVE_RAW','NATIVE_GRID']:
            start=time.time();s=get_source(r,rep);f,state,reason,top=analyze(s,ring,t);keep=state!=2;out=R/'local_results'/r['source_id']/rep;out.mkdir(parents=True,exist_ok=True)
            a,b=top['neighbor_a'],top['neighbor_b'];counts=np.zeros((len(state),4),int)
            for i in range(4):np.add.at(counts[:,i],a,state[b]==i);np.add.at(counts[:,i],b,state[a]==i)
            np.savez_compressed(out/'FACE_EVIDENCE.npz',V=s['P'],F=s['F'],uv=s['uv'],native_uv=s['native_uv'],native_pixel_id=s['native_pixel_id'],original_face_id=s['face_id'],original_vertex_id=s['original_vertex_id'],state=state,reason_bits=reason,neighbor_state_counts=counts,K=s['K'],Kn=s['Kn'],T=s['T'],**f)
            # All vertices stay byte-identical; only faces are selected, no repair.
            np.savez_compressed(out/'CLEANED_SUBSET.npz',V=s['P'],F=s['F'][keep],original_face_id=s['face_id'][keep],original_face_index=np.flatnonzero(keep),original_vertex_id=s['original_vertex_id'],native_pixel_id=s['native_pixel_id'])
            col=np.array([[45,180,65],[235,185,35],[215,40,45],[145,145,145]],np.uint8)[state]
            for name,sel in [('RAW',np.ones(len(state),bool)),('CLEANED',keep),('REJECTED',~keep)]:
                if sel.any():trimesh.Trimesh(s['P'],s['F'][sel],face_colors=col[sel],process=False).export(out/(name+'.ply'))
            summary=dict(group=r['group'],source=r['source_id'],representation=rep,vertices=len(s['P']),original_faces=len(state),original_area_mm2=float(f['area_mm2'].sum()),retained_faces=int(keep.sum()),rejected_faces=int((~keep).sum()),deleted_area_fraction=float(f['area_mm2'][~keep].sum()/f['area_mm2'].sum()),native_binding_error_px=s['identity_error_px'],retained_coordinates_exact=True,nearest_competition_is_incomplete=True)
            for i,key in enumerate(STATE_NAMES):summary[key+'_faces']=int((state==i).sum());summary[key+'_area_mm2']=float(f['area_mm2'][state==i].sum())
            summary.update(components_summary(s['P'],s['F'],keep,f['area_mm2']));summary.update(coverage(s,keep,ring))
            for k in ['perspective_stretch','tangent_stretch','edge_max_mm','normal_angle_deg','density_normalized']:
                summary[k+'_raw']=stats(f[k]);summary[k+'_clean']=stats(f[k][keep])
            ringnear=f['CAD_nearest_sample_mm']<t['ring_near_mm'];summary.update(Ring_near_faces=int(ringnear.sum()),Ring_near_deleted_faces=int((ringnear&~keep).sum()),CAD_inside_raw_faces=int((f['CAD_inside_samples']>=2).sum()),CAD_inside_retained_faces=int(((f['CAD_inside_samples']>=2)&keep).sum()),boundary_faces_removed=int((f['boundary_face']&~keep).sum()),interior_compact_faces_removed=int((~f['boundary_face']&(f['perspective_stretch']<2)&~keep).sum()),rejected_area_truth='NOT_EVALUABLE_NO_FACE_TRUTH',seconds=time.time()-start)
            rows.append(summary);save('metrics/source_summaries/'+r['source_id']+'_'+rep+'.json',summary)
            # Complete per-face audit in compressed CSV; raw ID/XYZ and all metrics in NPZ.
            keys=['original_face_id','state','reason_bits','original_vertex_ids','native_pixel_ids','source_uv','centroid_mm','neighbor_state_counts']+list(f)
            with gzip.open(out/'FACE_DECISIONS.csv.gz','wt',newline='')as stream:
                wri=csv.writer(stream);wri.writerow(keys)
                for j in range(len(state)):
                    vals=[int(s['face_id'][j]),STATE_NAMES[state[j]],int(reason[j]),s['original_vertex_id'][s['F'][j]].tolist(),s['native_pixel_id'][s['F'][j]].tolist(),s['uv'][s['F'][j]].tolist(),top['centroid'][j].tolist(),counts[j].tolist()]+[clean(v[j])for v in f.values()]
                    wri.writerow([json.dumps(v)if isinstance(v,(list,dict))else v for v in vals])
            audit.append(dict(source=r['source_id'],representation=rep,files=[asset(p)for p in sorted(out.iterdir())],input_arrays_unchanged=True))
            print(r['source_id'],rep,'faces',len(state),'reject',int((~keep).sum()),'area',round(summary['deleted_area_fraction'],6),'visible',round(summary['first_surface_retention_fraction'],6),'sec',round(time.time()-start,1),flush=True)
    save('metrics/SOURCE_SUMMARIES.json',rows);table('metrics/SOURCE_SUMMARIES.csv',rows);save('provenance/OUTPUT_FREEZE.json',dict(epoch=time.time(),outputs=audit,GT_opened=False,vertex_updates=0,interpolation=0,additional_cleaning_rounds=0))
if __name__=='__main__':main()
