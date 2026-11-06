"""Independent frozen-prediction evaluation. No training modules or selection of a winner."""
from common import *
from scipy.stats import qmc
import open3d as o3d

def pointcast(rt,P,K,T):
    pp=(P-T[:3,3])@T[:3,:3];q=pp@K.T;uv=q[:,:2]/q[:,2:];d=np.c_[uv,np.ones(len(uv))]@np.linalg.inv(K).T
    rays=np.c_[np.broadcast_to(T[:3,3],d.shape),d@T[:3,:3].T].astype(np.float32)
    hits=rt.cast_rays(o3d.core.Tensor(rays))['t_hit'].numpy();return uv,pp[:,2],hits
def area_samples(V,F,n=6000):
    rng=np.random.default_rng(20261106);a=trimesh.triangles.area(V[F]);inds=rng.choice(len(F),n,p=a/a.sum());b=rng.random((n,2));sq=np.sqrt(b[:,0]);w=np.c_[1-sq,sq*(1-b[:,1]),sq*b[:,1]];return (V[F[inds]]*w[:,:,None]).sum(1)
def distance(rt,P):return rt.compute_distance(o3d.core.Tensor(P.astype(np.float32))).numpy().astype(float)
def occupied(rt,P):return rt.compute_occupancy(o3d.core.Tensor(P.astype(np.float32)),nsamples=3).numpy()>.5
def save_npz(path,**data):
    p=R/path;p.parent.mkdir(parents=True,exist_ok=True);np.savez_compressed(p,**data)
def evaluate_case(name,gt=None):
    meta=getcase(name);init=np.load(R/'inputs'/name/'INITIAL.npz');V0,F0=init['V'],init['F'];r=np.load(R/'inputs'/name/'RING.npz');RV,RF=r['V'],r['F'];rs=scene(RV,RF);p0rt=scene(V0,F0)
    base=trimesh.Trimesh(V0,F0,process=False);lo=V0.min(0)-np.ptp(V0,axis=0);hi=V0.max(0)+np.ptp(V0,axis=0);X=lo+(hi-lo)*qmc.Sobol(3,scramble=True,seed=20261106).random_base2(18);weight=float(np.prod(hi-lo)/len(X));o0=occupied(p0rt,X)
    samples0=area_samples(V0,F0);fullviews={};ringmanager=trimesh.collision.CollisionManager();ringmanager.add_object('fixedRing',trimesh.Trimesh(RV,RF,process=False));per=[];geoms=[]
    for v in meta['views']:
        a=dict(np.load(R/'inputs'/name/(v['id']+'.npz')));a['meta']=v;a['cad_z']=cast(rs,a['K'],a['T'],360,640);fullviews[v['id']]=a
    if gt is not None:
        gV,gF=gt['V'],gt['F'];grt=scene(gV,gF);gs=area_samples(gV,gF);og=occupied(grt,X);gm=trimesh.Trimesh(gV,gF,process=False);occs=[];visgt=[]
        for cid,d in fullviews.items():
            uv,z,rz=pointcast(rs,gs,d['K'],d['T']);inframe=(z>0)&(uv[:,0]>=0)&(uv[:,0]<640)&(uv[:,1]>=0)&(uv[:,1]<360);occs.append(inframe&(rz<z-.05));visgt.append(inframe&(rz>=z-.05))
        fitidx=[i for i,v in enumerate(meta['views'])if v['role']=='FIT'];hidden_any=np.any(np.array(occs)[fitidx],axis=0);hidden_all=np.all(np.array(occs)[fitidx],axis=0)
        save_npz('audit_only/FIXED_GT_SAMPLES.npz',P=gs,hidden_any=hidden_any,hidden_all=hidden_all)
    else:gs=None
    states=[('P0',0,R/'inputs'/name/'INITIAL.npz')]+[(arm,step,R/'local_results'/name/arm/('STEP_%04d.npz'%step))for arm in['Baseline','RingAware']for step in[100,200,300]]
    for arm,step,path in states:
        a=np.load(path);V,F=a['V'],a['F'];m=trimesh.Trimesh(V,F,process=False);rt=scene(V,F);collision,names=ringmanager.in_collision_single(m,return_names=True)
        gap=ringmanager.min_distance_single(m);rd=rs.compute_signed_distance(o3d.core.Tensor(V.astype(np.float32)),nsamples=3).numpy();rough=np.degrees(m.face_adjacency_angles)
        row=dict(case=name,arm=arm,step=step,vertices=len(V),faces=len(F),watertight=bool(m.is_watertight),winding=bool(m.is_winding_consistent),components=int(len(m.split(only_watertight=False))),Euler=int(m.euler_number),volume_mm3=float(m.volume),volume_ratio_P0=float(m.volume/base.volume),Ring_collision=bool(collision),Ring_min_distance_mm=float(gap),vertices_inside_Ring=int((rd<-.001).sum()),roughness_normal_angle_deg=stats(rough),min_face_area_mm2=float(m.area_faces.min()),degenerate_faces_below_1e_12=int((m.area_faces<1e-12).sum()),material_vertex_displacement_mm=stats(np.linalg.norm(V-V0,axis=1)),GT='independent native Blender posterior'if gt is not None else'NOT_EVALUABLE')
        # Surface projection support is observation evidence, never accuracy ground truth.
        centers=m.triangles_center;support=np.zeros(len(centers),bool);cad_behind=np.zeros(len(centers),bool)
        for cid,d in fullviews.items():
            lab=d['labels'];target=lab==1;z=cast(rt,d['K'],d['T'],360,640);pred=np.isfinite(z)&(z<d['cad_z']);known=lab!=2
            union=int((pred|target).sum());hit=int((pred&target).sum());fp=int((pred&~target).sum());co=contour(pred);ct=contour(target);bd=stats(np.r_[cKDTree(co).query(ct)[0],cKDTree(ct).query(co)[0]])if len(co)and len(ct)else stats([])
            cr=np.isfinite(z)&np.isfinite(d['cad_z'])&(lab==2)&(z<d['cad_z']-.05)
            per.append(dict(case=name,arm=arm,step=step,view=cid,role=d['meta']['role'],qualification=d['meta']['qualification'],full_Mask_N=int(target.sum()),hit_N=hit,miss_N=int((target&~pred).sum()),FP_N=fp,full_Mask_IoU=hit/max(1,union),coverage=hit/max(1,int(target.sum())),outside_per_fixed_Mask=fp/max(1,int(target.sum())),contour_px=bd,CAD_front_conflict_N=int(cr.sum()),Ring_observed_N=int((lab==2).sum())))
            uv,zz,ringz=pointcast(rs,centers,d['K'],d['T']);_,_,selfz=pointcast(rt,centers,d['K'],d['T']);px=np.clip(np.rint(uv).astype(int),[0,0],[639,359]);inframe=(zz>0)&(uv[:,0]>=0)&(uv[:,0]<640)&(uv[:,1]>=0)&(uv[:,1]<360)
            support|=inframe&(lab[px[:,1],px[:,0]]==1)&(zz<ringz+.05)&(abs(zz-selfz)<.05);cad_behind|=inframe&(ringz<zz-.05)
            if step in[0,300]:save_npz('local_results/eval/'+name+'_'+arm+'_'+cid+'.npz',pred=pred,depth=np.where(np.isfinite(z),z,np.nan),visible_depth=np.where(pred,z,np.nan),front_conflict=cr,target=target)
        row.update(observed_supported_area_mm2=float(m.area_faces[support].sum()),inferred_or_unverified_area_mm2=float(m.area_faces[~support].sum()),Ring_behind_area_mm2=float(m.area_faces[cad_behind].sum()))
        save_npz('local_results/eval/'+name+'_'+arm+'_%04d_SUPPORT.npz'%step,face_supported=support,face_CAD_behind=cad_behind)
        if m.is_watertight:
            oc=occupied(rt,X);row.update(expanded_P0_mm3=float((oc&~o0).sum()*weight),removed_P0_mm3=float((o0&~oc).sum()*weight),outside_integration_domain_vertices=int(((V<lo)|(V>hi)).any(1).sum()),occupancy_sampling_weight_mm3=weight,occupancy_caveat='Watertight topology verified; self-intersection checked separately. Proxy integral, not exact polyhedral Boolean.')
            if gt is not None:
                ps=area_samples(V,F);dg=distance(rt,gs);dp=distance(grt,ps);ch=stats(np.r_[dg,dp]);row.update(Chamfer_mm=ch,GT_to_prediction_mm=stats(dg),prediction_to_GT_mm=stats(dp),symmetric_difference_mm3=float((og!=oc).sum()*weight),volume_error_signed_mm3=float(m.volume-gm.volume),volume_error_abs_mm3=float(abs(m.volume-gm.volume)),gt_surface_hidden_any_fit_N=int(hidden_any.sum()),gt_surface_hidden_all_fit_N=int(hidden_all.sum()),hidden_any_fit_error_mm=stats(dg[hidden_any])if hidden_any.any()else'NOT_EVALUABLE_NO_GT_OCCLUSION',hidden_all_fit_error_mm=stats(dg[hidden_all])if hidden_all.any()else'NOT_EVALUABLE_NO_GT_OCCLUSION')
                # Explicit false removal proxy relative to initial body, fixed voxel population.
                row.update(true_GT_P0_volume_removed_mm3=float((og&o0&~oc).sum()*weight),unsupported_added_volume_mm3=float((~og&~o0&oc).sum()*weight))
        geoms.append(row);print(name,arm,step,'volume',row['volume_mm3'],'Ring collision',row['Ring_collision'],flush=True)
    save('metrics/'+name+'_GEOMETRY.json',geoms);table('metrics/'+name+'_GEOMETRY.csv',geoms);table('metrics/'+name+'_PER_VIEW.csv',per)
    save('metrics/'+name+'_VOLUME_DOMAIN.json',dict(lo=lo,hi=hi,N=len(X),sample_weight_mm3=weight,seed=20261106,source='P0 only, predeclared extent padding',GT_used_to_define_domain=False))
    return geoms,per

def main():
    freeze=load(R/'assets_index/PREDICTIONS_FROZEN_BEFORE_GT.json')
    for a in freeze['files']:assert sha(a['path'])==a['sha256'],a['path']
    gt=dict(np.load(OLD/'audit_only/NATIVE_CAD_GT.npz'));save('assets_index/POSTERIOR_GT.json',dict(asset=asset(OLD/'audit_only/NATIVE_CAD_GT.npz'),prediction_freeze_sha=sha(R/'assets_index/PREDICTIONS_FROZEN_BEFORE_GT.json'),access_time_epoch=time.time(),GT_model_selection=False))
    allg=[];allp=[]
    for name in['virtual','real']:
        g,p=evaluate_case(name,gt if name=='virtual'else None);allg+=g;allp+=p
    table('metrics/ALL_GEOMETRY.csv',allg);table('metrics/PER_VIEW_METRICS.csv',allp)
    summary=[]
    for g in allg:
        pp=[p for p in allp if p['case']==g['case']and p['arm']==g['arm']and p['step']==g['step']]
        summary.append(dict(case=g['case'],arm=g['arm'],step=g['step'],fit_IoU=float(np.mean([p['full_Mask_IoU']for p in pp if p['role']=='FIT'])),holdout_IoU=float(np.mean([p['full_Mask_IoU']for p in pp if p['role']!='FIT'])),fit_coverage=float(np.mean([p['coverage']for p in pp if p['role']=='FIT'])),holdout_coverage=float(np.mean([p['coverage']for p in pp if p['role']!='FIT'])),Chamfer_MAE_mm=g.get('Chamfer_mm',{}).get('MAE'),Chamfer_p95_mm=g.get('Chamfer_mm',{}).get('p95'),symmetric_difference_mm3=g.get('symmetric_difference_mm3'),volume_mm3=g['volume_mm3'],Ring_collision=g['Ring_collision'],components=g['components'],watertight=g['watertight']))
    save('metrics/SUMMARY.json',summary);table('metrics/SUMMARY.csv',summary)
if __name__=='__main__':main()
