"""Fixed-input-denominator diagnostics; no geometry changes or GT."""
from hero_tsdf_adapter import *
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

def topology(m):
    adj=m.face_adjacency;n=len(m.faces);graph=coo_matrix((np.ones(len(adj)*2),(np.r_[adj[:,0],adj[:,1]],np.r_[adj[:,1],adj[:,0]])),shape=(n,n)).tocsr();nc,comp=connected_components(graph,directed=False)
    area=np.asarray(m.area_faces);ca=np.bincount(comp,weights=area);edges=np.sort(np.asarray(m.edges),axis=1);unique,first,count=np.unique(edges,axis=0,return_index=True,return_counts=True);boundary=count==1;bc=np.bincount(comp[np.asarray(m.edges_face)[first[boundary]]],minlength=nc);closed=bc==0
    return dict(vertices=len(m.vertices),faces=n,area_mm2=float(area.sum()),components=nc,components_area_gt_1mm2=int((ca>1).sum()),largest_component_area_fraction=float(ca.max()/ca.sum()),boundary_edges=int(boundary.sum()),nonmanifold_edges=int((count>2).sum()),closed_components=int(closed.sum()),closed_components_area_mm2=float(ca[closed].sum()),watertight=bool(m.is_watertight),bounds_mm=m.bounds.tolist()),comp

def support(X,ids):
    counts=np.zeros(len(X),int);validcount=np.zeros(len(X),int);cadcount=np.zeros(len(X),int);front=np.zeros(len(X),int);back=np.zeros(len(X),int)
    for cid in ids:
        s=source(cid);uv,z=vis.project_camera(X,s['Kn'],s['T']);h,w=s['depth'].shape;ok=np.isfinite(uv).all(1)&(z>0)&(uv[:,0]>=-.5)&(uv[:,0]<w-.5)&(uv[:,1]>=-.5)&(uv[:,1]<h-.5);ii=np.flatnonzero(ok);pix=np.floor(uv[ii]+.5).astype(int)
        labels=cv2.resize(s['labels'],(w,h),interpolation=cv2.INTER_NEAREST);dh=s['depth'][pix[:,1],pix[:,0]];good=(labels[pix[:,1],pix[:,0]]==1)&np.isfinite(dh)&(dh>0)
        ringz,_=cast(ringscene(),uv[ii],s['Kn'],s['T']);blocked=np.isfinite(ringz)&(z[ii]>ringz+.002);cadcount[ii]+=blocked
        good&=~blocked;validcount[ii]+=good;res=z[ii]-dh;counts[ii]+=good&(abs(res)<=.25);front[ii]+=good&(res<-.25);back[ii]+=good&(res>.25)
    return dict(support_count=counts,valid_source_count=validcount,CAD_blocked_source_count=cadcount,front_of_HERO_count=front,behind_HERO_count=back)

def main():
    assert(R/'local_results/G1/mesh_mm.ply').exists(),'diagnostic evidence is post-fusion only'
    c=cfg();meshes={n:output_mesh(n)for n in ['SINGLE','SINGLE_RESOLUTION_CONTROL','G0','G1']};scenes={n:mesh_scene(m.vertices,m.faces)for n,m in meshes.items()}
    rows=[];surface_rows=[];topos={};Dout=R/'local_results/EVALUATION';Dout.mkdir(exist_ok=True)
    for name,m in meshes.items():
        topos[name],comp=topology(m);X=np.asarray(m.triangles_center);sp=support(X,c['G1']);ar=np.asarray(m.area_faces);supported=sp['support_count']>0
        np.savez_compressed(Dout/(name+'_output_observation_support.npz'),face_id=np.arange(len(X)),XYZ_mm=X,area_mm2=ar,component=comp,**sp)
        topos[name].update(observed_proxy_area_mm2=float(ar[supported].sum()),unknown_proxy_area_mm2=float(ar[~supported].sum()),unknown_area_fraction=float(ar[~supported].sum()/ar.sum()),two_source_support_area_fraction=float(ar[sp['support_count']>=2].sum()/ar.sum()),support_reference_set=c['G1'])
        rows.append(dict(record='topology',mesh=name,source='ALL',**{k:v for k,v in topos[name].items()if k!='bounds_mm'}))
        for cid in c['G1']:
            s=source(cid);X0=s['P'][s['F']].mean(1);dd=distance(scenes[name],X0);ret=dd<=.25;area=s['area'];rf=np.flatnonzero(ret)
            r=dict(record='original_surface_fixed_denominator',mesh=name,source=cid,original_face_N=len(dd),original_area_mm2=float(area.sum()),retained_face_N=int(ret.sum()),retained_face_fraction=float(ret.mean()),retained_area_mm2=float(area[ret].sum()),retained_area_fraction=float(area[ret].sum()/area.sum()),lost_area_mm2=float(area[~ret].sum()),distance_median_mm=float(np.median(dd)),distance_MAE_mm=float(dd.mean()),distance_p95_mm=float(np.quantile(dd,.95)),distance_max_mm=float(dd.max()))
            rows.append(r);surface_rows.append(r);np.savez_compressed(Dout/(name+'_'+cid+'_original_faces.npz'),face_id=np.arange(len(dd)),distance_mm=dd,retained_at_0p25_mm=ret,area_mm2=area)
            # Every fixed stride2 real pixel, not only hits. All mask pixels kept in denominator.
            vv,uu=np.mgrid[0:s['labels'].shape[0]:2,0:s['labels'].shape[1]:2];uv=np.c_[uu.ravel(),vv.ravel()];labels=s['labels'][vv,uu].ravel();zz=np.load(s['c']['pack'])['depth_mm'][vv,uu].ravel();ringz,_=cast(ringscene(),uv,s['K'],s['T']);hit,fid=cast(scenes[name],uv,s['K'],s['T']);visible=np.isfinite(hit)&((~np.isfinite(ringz))|(hit<=ringz+.002));polyp=labels==1
            eligible=polyp&np.isfinite(zz)&(zz>0)&((~np.isfinite(ringz))|(zz<=ringz+.002))
            agree=visible&eligible&(abs(hit-zz)<=.25);outside=visible&(labels==0);good=visible&polyp;err=abs(hit[eligible&visible]-zz[eligible&visible]);censored=np.full(eligible.sum(),np.inf);censored[visible[eligible]]=abs(hit[eligible&visible]-zz[eligible&visible]);k=int(np.ceil(.95*len(censored)))-1;fullp95=float(np.sort(censored)[k])
            r=dict(record='real_Mask_fixed_denominator',mesh=name,source=cid,Polyp_Mask_pixel_N=int(polyp.sum()),visible_hit_on_Mask_N=int(good.sum()),Mask_coverage=float(good.sum()/polyp.sum()),eligible_HERO_pixel_N=int(eligible.sum()),eligible_HERO_hit_N=int((eligible&visible).sum()),eligible_HERO_agree_N=int(agree.sum()),eligible_HERO_depth_agree_fraction=float(agree.sum()/eligible.sum()),eligible_HERO_miss_N=int((eligible&~visible).sum()),outside_Mask_predicted_pixel_N=int(outside.sum()),outside_Mask_fraction_of_visible_output=float(outside.sum()/max(1,visible.sum())),CAD_hidden_output_N=int((np.isfinite(hit)&~visible).sum()),CAD_hidden_HERO_N=int((polyp&~eligible).sum()),finite_hit_depth_median_mm=float(np.median(err))if len(err)else np.nan,finite_hit_depth_p95_mm=float(np.quantile(err,.95))if len(err)else np.nan,full_denominator_depth_p95_mm=fullp95,full_denominator_depth_p95_infinite=not np.isfinite(fullp95))
            rows.append(r);np.savez_compressed(Dout/(name+'_'+cid+'_real_projection.npz'),uv=uv,original_depth_mm=zz,predicted_depth_mm=hit,ring_depth_mm=ringz,labels=labels,visible=visible,eligible=eligible,agree=agree,output_face_id=fid)
        print('EVALUATED',name,topos[name],flush=True)
    table('G0_G1_METRICS.csv',rows);save('config/TOPOLOGY_AND_SUPPORT.json',topos)
    # Diagnose earlier E3C labels after fusion only, never use them as input or filters.
    cp=REPO/'experiments/TASK-E3-C-VISIBILITY-CONSENSUS-001/VISIBILITY_EVIDENCE.csv';evidence=[r for r in csv.DictReader(cp.open())if r['source_id']in CORE];clrows=[]
    for name in ['G0','G1']:
        for cid in CORE:
            ss=[r for r in evidence if r['source_id']==cid];F=np.array([int(r['original_face_id'])for r in ss]);X=source(cid)['P'][source(cid)['F'][F]].mean(1);dd=distance(scenes[name],X)
            for cl in sorted({r['evidence_class']for r in ss}):
                keep=np.array([r['evidence_class']==cl for r in ss]);clrows.append(dict(mesh=name,source=cid,E3C_evidence_class=cl,fixed_candidate_N=int(keep.sum()),retention_at_0p25mm=float((dd[keep]<=.25).mean()),distance_median_mm=float(np.median(dd[keep])),evidence_is_physical_truth=False,used_to_filter_input=False))
    table('E3C_POSTHOC_DIAGNOSTICS.csv',clrows)
    # Predeclared case selection uses full per-source preservation change, then original faces.
    S={(r['mesh'],r['source']):r for r in surface_rows}
    a=max(CORE,key=lambda x:1-S['G0',x]['retained_area_fraction']);b=min(G1,key=lambda x:S['G1',x]['retained_area_fraction']-S['G0',x]['retained_area_fraction']);d=max(G1,key=lambda x:S['G1',x]['retained_area_fraction']-S['G0',x]['retained_area_fraction']);cases=[]
    for i,(cid,rule)in enumerate([(a,'largest CORE loss in G0'),(b,'largest G1 minus G0 decrease'),(d,'largest G1 minus G0 increase')]):
        s=source(cid);dd0=np.load(Dout/('G0_'+cid+'_original_faces.npz'))['distance_mm'];dd1=np.load(Dout/('G1_'+cid+'_original_faces.npz'))['distance_mm'];score=dd0 if i==0 else (dd1-dd0 if i==1 else dd0-dd1)
        # Deterministic representative: fixed 95th percentile of relevant original-face score.
        order=np.argsort(score,kind='stable');fid=int(order[int(.95*(len(order)-1))]);X=s['P'][s['F'][fid]].mean(0);uv,z=vis.project_camera(X[None],s['K'],s['T'])
        cases.append(dict(case_id='F'+str(i+1),source_id=cid,original_face_id=fid,X_mm=X[0],Y_mm=X[1],Z_mm=X[2],pixel_u=uv[0,0],pixel_v=uv[0,1],selection_rule=rule+';95th percentile original face score',G0_distance_mm=dd0[fid],G1_distance_mm=dd1[fid],status='OBSERVED',cause_status='HYPOTHESIS_UNRESOLVED',observation='input surface loss/disagreement'if i<2 else 'additional direction recovers input-proximate surface',hypothesis='B camera / C HERO / D uniform projective integration inseparable without independent geometry; no GT',evidence='figures/Fig4_failure_mechanisms.png'))
    table('TSDF_FAILURE_CASES.csv',cases);save('config/FAILURE_CASES.json',cases)
    # Lightweight full extracted actual surfaces (no simplification) plus opaque black CAD.
    preview=[]
    for name,m in meshes.items():
        scene=trimesh.Scene();scene.add_geometry(m,geom_name=name+'_actual_unmodified_TSDF_mm');cad=ringmesh().copy();cad.visual.face_colors=[8,8,8,255];scene.add_geometry(cad,geom_name='FROZEN_RING_CAD_BLACK_mm');p=R/'previews'/(name+'_mm.glb');scene.export(str(p));preview.append(asset(p))
    save('PREVIEW_INDEX.json',dict(unit='mm; GLB does not impose SI conversion, use numeric mm coordinates',Mesh_postprocessing='none; normals only; Ring separate black CAD',files=preview))
    print('FIXED_DENOMINATOR_EVALUATION_DONE',flush=True)
if __name__=='__main__':main()
