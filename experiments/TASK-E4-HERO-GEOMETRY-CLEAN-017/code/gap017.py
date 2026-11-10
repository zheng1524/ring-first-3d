"""Source-pixel one-sided plane extrapolation. No GT, group identity or fitted mesh."""
from common017 import *
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

def main():
    from analyze017 import get_source,components_summary,coverage,STATE_NAMES
    conf=load(R/'config/PROTOCOL.json');t=conf['thresholds'];summaries=[];evidence=[];output=[]
    for r in load(R/'config/SOURCE_LOCK.json'):
        n=get_source(r,'NATIVE_GRID');z=np.load(r['native_depth'])['depth_mm'];gaps,erows=gap_edges(z,n['native_labels'],n['Kn'],n['T'],n['P'],n['F'],n['uv'],t);table('metrics/TWO_SIDED_GAP/'+r['source_id']+'.csv',erows);evidence.append(dict(source=r['source_id'],tested_candidate_edges=len(erows),confirmed_native_gap_edges=len(gaps),unsupported_edges=sum(e['reason']=='INSUFFICIENT_ONE_SIDED_SUPPORT'for e in erows)))
        ringm=trimesh.load(r['ring'],process=False);ring=scene(ringm.vertices,ringm.faces)
        for rep in ['ARCHIVE_RAW','NATIVE_GRID']:
            s=get_source(r,rep);old=R/'local_results'/r['source_id']/rep;a=dict(np.load(old/'FACE_EVIDENCE.npz'));state=a['state'].copy();reason=a['reason_bits'].copy();F=a['F'];px=a['native_pixel_id'];confirmed=np.zeros(len(F),bool)
            for ii,jj in [(0,1),(1,2),(2,0)]:confirmed|=np.array([tuple(sorted(p))in gaps for p in px[F[:,[ii,jj]]]])
            shape=(a['triangle_quality']<t['needle_quality'])|(a['normal_angle_deg']>t['neighbor_angle_deg'])|(a['normal_coherence']<t['normal_coherence'])
            material=a['CAD_inside_samples']>=t['ring_inside_samples_min'];context=(a['boundary_distance_native_px']<=t['edge_native_px'])|material
            reject=confirmed&shape&context&a['native_mask_supported']&(~a['CAD_occluded']|material)&(a['native_depth_jump_mm']>t['native_depth_jump_mm'])&(a['perspective_stretch']>t['stretch_perspective'])
            # A confirmed gap invalidates interpolating triangles, NOT either endpoint surface.
            state[reject]=2;reason[confirmed]|=1<<13;reason[reject]|=1<<14;keep=state!=2;counts=np.zeros((len(F),4),int)
            top_edges=np.sort(F[:,[[0,1],[1,2],[2,0]]].reshape(-1,2),1);ids=np.repeat(np.arange(len(F)),3);order=np.lexsort((top_edges[:,1],top_edges[:,0]));ee=top_edges[order];ii=ids[order];same=(ee[1:]==ee[:-1]).all(1);aa=ii[:-1][same];bb=ii[1:][same]
            for i in range(4):np.add.at(counts[:,i],aa,state[bb]==i);np.add.at(counts[:,i],bb,state[aa]==i)
            a.update(state=state,reason_bits=reason,neighbor_state_counts=counts,two_sided_gap_face=confirmed,two_sided_gap_rejected=reject)
            out=R/'final_results'/r['source_id']/rep;out.mkdir(parents=True,exist_ok=True);np.savez_compressed(out/'FACE_EVIDENCE.npz',**a);np.savez_compressed(out/'CLEANED_SUBSET.npz',V=a['V'],F=F[keep],original_face_id=a['original_face_id'][keep],original_face_index=np.flatnonzero(keep),original_vertex_id=a['original_vertex_id'],native_pixel_id=px)
            colors=np.array([[45,180,65],[235,185,35],[215,40,45],[145,145,145]],np.uint8)[state]
            for name,sel in [('RAW',np.ones(len(F),bool)),('CLEANED',keep),('REJECTED',~keep)]:
                if sel.any():trimesh.Trimesh(a['V'],F[sel],face_colors=colors[sel],process=False).export(out/(name+'.ply'))
            row=load(R/'metrics/source_summaries'/(r['source_id']+'_'+rep+'.json'));area=a['area_mm2'];row.update(rejected_faces=int((~keep).sum()),retained_faces=int(keep.sum()),deleted_area_fraction=float(area[~keep].sum()/area.sum()),two_sided_gap_face_count=int(confirmed.sum()),two_sided_gap_rejected_count=int(reject.sum()))
            for i,key in enumerate(STATE_NAMES):row[key+'_faces']=int((state==i).sum());row[key+'_area_mm2']=float(area[state==i].sum())
            row.update(components_summary(a['V'],F,keep,area));row.update(coverage(s,keep,ring))
            for key in ['perspective_stretch','tangent_stretch','edge_max_mm','normal_angle_deg','density_normalized']:row[key+'_clean']=stats(a[key][keep])
            near=a['CAD_nearest_sample_mm']<t['ring_near_mm'];row.update(Ring_near_deleted_faces=int((near&~keep).sum()),CAD_inside_retained_faces=int((material&keep).sum()),boundary_faces_removed=int((a['boundary_face']&~keep).sum()),interior_compact_faces_removed=int((~a['boundary_face']&(a['perspective_stretch']<2)&~keep).sum()))
            summaries.append(row)
            # Final per-face decisions complement unchanged full metric CSV in local_results.
            table('face_decisions/'+r['source_id']+'_'+rep+'.csv',[dict(original_face_id=int(a['original_face_id'][j]),original_face_index=j,state=STATE_NAMES[state[j]],reason_bits=int(reason[j]),native_pixel_IDs=px[F[j]],original_vertex_IDs=a['original_vertex_id'][F[j]],two_sided_gap=bool(confirmed[j]),neighbor_state_counts=counts[j])for j in range(len(F))])
            output.append(dict(source=r['source_id'],representation=rep,files=[asset(p)for p in sorted(out.iterdir())]));print('FINAL',r['source_id'],rep,'removed',int((~keep).sum()),'area',round(row['deleted_area_fraction'],6),'visible',round(row['first_surface_retention_fraction'],6),flush=True)
    save('metrics/TWO_SIDED_GAP_SUMMARY.json',evidence);table('metrics/TWO_SIDED_GAP_SUMMARY.csv',evidence);save('metrics/FINAL_SOURCE_SUMMARIES.json',summaries);table('metrics/FINAL_SOURCE_SUMMARIES.csv',summaries);save('provenance/FINAL_OUTPUT_FREEZE.json',dict(epoch=time.time(),files=output,GT_used=False,cleaning='one final bridge-face subset after retained initial negative diagnosis; no sequential deletion or threshold search'))
if __name__=='__main__':main()
