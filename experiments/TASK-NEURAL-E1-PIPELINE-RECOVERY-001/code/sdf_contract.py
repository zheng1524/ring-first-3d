"""C1.2 official-source-driven NumPy geometry; never creates a neural model."""
from common import *

def sphere_interval(o,d,center,r):
    q=o-center;b=np.sum(q*d,axis=-1);disc=b*b-(np.sum(q*q,axis=-1)-r*r)
    s=np.sqrt(np.maximum(disc,0));return np.where(disc>=0,-b-s,np.nan),np.where(disc>=0,-b+s,np.nan)

def cube_far(o,d,r,near,far):
    # Exact NumPy counterpart of UniformSampler.near_far_from_cube, including
    # the official +1e-15 denominator and the later global far endpoint.
    a=(-r-o)/(d+1e-15);b=(r-o)/(d+1e-15)
    lo=np.minimum(a,b).max(-1);hi=np.maximum(a,b).min(-1)
    miss=hi<lo;lo=np.where(miss,1e9,lo);hi=np.where(miss,1e9,hi)
    return np.maximum(lo,near),np.minimum(hi,far)

def density(sdf,beta=.1001):
    return (0.5+0.5*np.sign(sdf)*np.expm1(-abs(sdf)/beta))/beta

def main():
    D=load(R/'provenance/INPUT_ELIGIBILITY.json');C={c['id']:c for c in D['references']}
    prop=load(R/'provenance/G01_PROPOSED_INPUTS.json')['proposals'];gn=legacy_geometry_namespace(D)
    src=[C[x]for ids in prop.values()for x in ids];cfg=conventions();proof=[]
    specs=[(SDF/'code/model/ray_sampler.py',['UniformSampler','ErrorBoundSampler']),
           (SDF/'code/model/density.py',['LaplaceDensity']),
           (SDF/'code/model/network.py',['ImplicitNetwork','MonoSDFNetwork'])]
    for p,names in specs:
        tree=ast.parse(p.read_text())
        for n in tree.body:
            if isinstance(n,ast.ClassDef) and n.name in names:
                proof.append(dict(path=str(p),SHA256=sha(p),component=n.name,first_line=n.lineno,last_line=n.end_lineno,
                    actual_component_status='BLOCKED_STATIC_ANALYSIS_ONLY',reason='CUDA calls and/or neural forward required; not instantiated',
                    source=ast.get_source_segment(p.read_text(),n)))
    save('provenance/SDF_OFFICIAL_SOURCE_BEHAVIOR.json',proof)
    byscene={}
    for sid,ids in prop.items():
        observed=np.concatenate([gn['points'](cid)[0]for cid in ids]);cam=np.array([C[cid]['c2w_mm']for cid in ids])[:,:3,3]
        center=(observed.min(0)+observed.max(0))/2
        # Two predeclared gauges: CAD origin vs measured visible ROI center.
        # A 10-beta margin from the absorbing wall is derived explicitly.
        candidates=[]
        for name,origin in [('RING_CENTER_ENVELOPE',np.zeros(3)),('VISIBLE_ROI_CENTER_ENVELOPE',center)]:
            maxnorm=np.linalg.norm(np.r_[cam,observed]-origin,axis=1).max()
            scale=float(maxnorm/(2.5-10*cfg['analytic_beta_network']))
            candidates.append(dict(id=name,center_mm=origin,mm_per_unit=scale,radius_units=2.5,near_units=.05,
                far_units=8.75,physical_radius_mm=2.5*scale,physical_reason='Enclose actual frozen camera+visible source ROI with 10 beta free-space clearance; no error search',
                mask_contract='ROI-truncated finite opacity; official full-ray weight sum is invalid for Polyp silhouette',
                ROI_center_mm=center,ROI_radius_mm=float(np.linalg.norm(observed-center,axis=1).max()+1.),
                official_sampler_executed=False,neural_forward=False))
        byscene[sid]=candidates
    save('config/SDF_DOMAIN_CANDIDATES.json',dict(frozen_before_ray_tests=True,designs_per_scene=2,candidates=byscene,
        source_driven_geometry_only=True,optimizer_cameras=False,source_K_c2w_unchanged=True))
    save('provenance/SDF_BEFORE_TEST_FREEZE.json',dict(code=asset(Path(__file__)),common=asset(R/'code/common.py'),
        candidates=asset(R/'config/SDF_DOMAIN_CANDIDATES.json'),tolerances=asset(R/'config/CPU_CONTRACT.json')))
    rng=np.random.default_rng(cfg['seed']);rows=[];summary=[];plots={};analytic=[]
    for c in src:
        cid=c['id'];sid=c['scene_id'];p=np.load(c['pack']);K=p['K'].copy();T=p['pose'].copy();m=p['labels'];z=p['depth_mm']
        sc=SameCameraScene(ring(c['ring']),K,T,(640,360),str(VENDOR))
        fg=(m==1)&np.isfinite(z)&(z>0);bg=(cv2.dilate((m==1).astype(np.uint8),np.ones((41,41),np.uint8))>0)&(m==0)
        classes={'FOREGROUND':np.argwhere(fg),'NEAR_BACKGROUND':np.argwhere(bg),'RING_MASK':np.argwhere(m==2),
                 'IMAGE_CORNERS':np.array([[0,0],[0,639],[359,0],[359,639]])}
        selected=[]
        for kind,yx in classes.items():
            n=min(len(yx),cfg['ray_per_class']);yx=yx[np.linspace(0,len(yx)-1,n,dtype=int)] if n else yx
            for y,x in yx:selected.append((kind,int(x),int(y)))
        uv=np.array([[x,y]for _,x,y in selected]);rays=vis.camera_rays(uv,K,T)
        length_factor=np.linalg.norm(rays[:,3:],axis=1);d=rays[:,3:]/length_factor[:,None]
        depth=z[uv[:,1],uv[:,0]];target_mm=depth*length_factor
        trueP=unproject(depth,T,uv,K);intersection_error=np.max(abs(T[:3,3]+d*target_mm[:,None]-trueP),axis=1)
        cadz=sc.cast(uv)['t_hit'].numpy();cad_t=cadz*length_factor
        old=dict(id='E0_OLD',center_mm=[0,0,0],mm_per_unit=10.,radius_units=2.5,near_units=.05,far_units=8.75,
                 ROI_center_mm=byscene[sid][0]['ROI_center_mm'],ROI_radius_mm=byscene[sid][0]['ROI_radius_mm'])
        for q in [old]+byscene[sid]:
            origin=np.asarray(q['center_mm']);scale=q['mm_per_unit'];o=np.broadcast_to((T[:3,3]-origin)/scale,d.shape)
            en,ex=sphere_interval(o,d,np.zeros(3),2.5);cn,cf=cube_far(o,d,2.5,.05,8.75)
            target=target_mm/scale;rn,rx=sphere_interval(np.broadcast_to(T[:3,3],d.shape),d,np.asarray(q['ROI_center_mm']),q['ROI_radius_mm'])
            sam=.05+(cf-.05)[:,None]*np.linspace(0,1,64)[None,:]
            position=o[:,None,:]+sam[:,:,None]*d[:,None,:]
            valid_fraction=(np.linalg.norm(position,axis=-1)<2.5).mean(1)
            # Clamp-only optical depth BEFORE actual source depth, not camera norm.
            end=np.where(np.isfinite(en)&(en>.05),en,.05)
            ts=.05+(end-.05)[:,None]*np.linspace(0,1,256)[None,:]
            sph=2.5-np.linalg.norm(o[:,None,:]+ts[:,:,None]*d[:,None,:],axis=-1)
            optical=np.trapz(density(np.minimum(10.,sph)),ts,axis=1)
            entry_trans=np.exp(-optical)
            near_clear=(np.linalg.norm(o+.05*d,axis=1)<2.5)
            target_valid=np.isfinite(target)&(target>=.05)&(target<=cf)&(target>=en)&(target<=ex)
            # Real-ray analytic controls. Empty-space +10 SDF is clamped by the
            # official sphere. Integrate a finite pre-ROI segment separately
            # from the forced far terminator. This is math, not an SDF prediction.
            roi_end=np.where(np.isfinite(rx)&(rx>0),rx/scale,np.minimum(cf,np.linalg.norm(np.asarray(q['ROI_center_mm'])-T[:3,3])/scale))
            roi_end=np.maximum(.05,np.minimum(roi_end,cf))
            rt=.05+(roi_end-.05)[:,None]*np.linspace(0,1,1024)[None,:]
            wall=2.5-np.linalg.norm(o[:,None,:]+rt[:,:,None]*d[:,None,:],axis=-1)
            empty_opacity=1-np.exp(-np.trapz(density(np.minimum(10.,wall)),rt,axis=1))
            terminal_wall=2.5-np.linalg.norm(o+8.75*d,axis=1)
            full_opacity=1-np.exp(-1e10*density(np.minimum(10.,terminal_wall)))
            # Plane at the independently sourced foreground depth: exact 0 at
            # target, positive before and negative after. It is a local control.
            plane_zero=intersection_error/scale
            for i,(kind,x,y) in enumerate(selected):
                rows.append(dict(scene=sid,source=cid,domain=q['id'],ray_class=kind,u=x,v=y,
                    entry_t=en[i],exit_t=ex[i],foreground_target_t=target[i] if kind=='FOREGROUND' else np.nan,
                    source_axial_Z_mm=depth[i],source_ray_length_mm=target_mm[i],ray_Z_point_error_mm=intersection_error[i],
                    near=.05,uniform_cube_far=cf[i],official_extra_far=8.75,
                    valid_sampling_fraction=valid_fraction[i],near_inside_absorber=bool(near_clear[i]),
                    pre_entry_absorber_transmittance=entry_trans[i],target_in_sampling_domain=bool(target_valid[i]),
                    analytic_empty_finite_opacity=empty_opacity[i],official_terminal_opacity=full_opacity[i],
                    analytic_plane_zero_error_network=plane_zero[i] if kind=='FOREGROUND' else np.nan,
                    trusted_ROI_entry_mm=rn[i],trusted_ROI_exit_mm=rx[i],CAD_target_t_mm=cad_t[i],
                    Ring_occluded=bool(np.isfinite(cad_t[i]) and target_mm[i]>cad_t[i]+.05),
                    source_pose_roundtrip_max_mm=float(np.max(abs(o[i]*scale+origin-T[:3,3]))),
                    status='CPU_EQUIVALENT_GEOMETRY_NOT_NETWORK'))
            for kind in classes:
                ix=np.array([x[0]==kind for x in selected]);fi=ix&(np.array([x[0]for x in selected])=='FOREGROUND')
                summary.append(dict(scene=sid,source=cid,domain=q['id'],ray_class=kind,N=int(ix.sum()),
                    target_valid_N=int((target_valid&ix).sum()) if kind=='FOREGROUND' else None,
                    near_clear_N=int((near_clear&ix).sum()),valid_sampling_fraction_median=float(np.median(valid_fraction[ix])) if ix.any() else None,
                    pre_entry_transmittance_median=float(np.median(entry_trans[ix])) if ix.any() else None,
                    empty_space_finite_opacity_median=float(np.median(empty_opacity[ix])) if ix.any() else None,
                    full_ray_terminal_opacity_median=float(np.median(full_opacity[ix])) if ix.any() else None,
                    predeclared_sampling_fraction_threshold=cfg['domain_min_class_sampling_fraction'],
                    strict_uniform_sample_fraction_pass=bool(np.median(valid_fraction[ix])>=cfg['domain_min_class_sampling_fraction']) if ix.any() else False,
                    official_components='BLOCKED_STATIC_ANALYSIS_ONLY',
                    geometry_status='EXPECTED_FAIL_E0' if q['id']=='E0_OLD' and not near_clear[ix].all() else 'CPU_GEOMETRY_PASS' if target_valid[fi].all() and near_clear[ix].all() else 'ADAPTER_INVALID'))
            if cid==prop[sid][0]:
                plots[sid+'_'+q['id']]=dict(camera_mm=T[:3,3],directions=d[:12],target_mm=trueP[:12],
                    origin_mm=origin,physical_radius_mm=2.5*scale,ROI_center_mm=q['ROI_center_mm'],ROI_radius_mm=q['ROI_radius_mm'])
        # Artificial analytic sphere and planar sign/zero-crossing controls in mm.
        center=np.array([0.,0.,0.]);rr=2.;oo=np.array([[0.,0.,-8.],[4.,0.,-8.]])
        dd=np.array([[0.,0.,1.],[0.,0.,1.]])
        near,far=sphere_interval(oo,dd,center,rr)
        for j,name in enumerate(['analytic_foreground','analytic_background']):
            ts=np.linspace(0,16,8193);s=np.linalg.norm(oo[j]+ts[:,None]*dd[j],axis=1)-rr
            rho=density(s,.1);opacity=1-np.exp(-np.trapz(rho,ts))
            # Full official-tail opacity vs finite trusted ROI distinguishes a
            # forced absorbing boundary from a foreground silhouette.
            far_sphere_sdf=2.5-np.linalg.norm((oo[j]+16*dd[j])/10.)
            # Independent fixed terminal negative SDF illustrates clamp tail.
            full_tail=1-np.exp(-1e10*density(np.array([-1.]),.1))[0]
            analytic.append(dict(source=cid,test=name,entry_mm=near[j],exit_mm=far[j],
                analytic_finite_opacity=opacity,forced_terminal_opacity=full_tail,
                sphere_zero_crossing_error_mm=abs(np.linalg.norm(oo[j]+near[j]*dd[j])-rr) if j==0 else np.nan,
                pass_test=bool(opacity>.99) if j==0 else bool(opacity<1e-4),
                computation='analytic mathematical SDF, NOT learned SDF'))
    # Positive SDF is exterior; planar negative-to-positive crossing is exact.
    plane_o=np.array([2.,1.,-7.]);plane_d=np.array([.1,.2,1.]);plane_d/=np.linalg.norm(plane_d)
    root=-plane_o[2]/plane_d[2]; plane_zero=(plane_o+root*plane_d)[2]
    signs=[float((plane_o+(root+t)*plane_d)[2])for t in [-1.,0.,1.]]
    analytic.append(dict(test='plane_sign_zero',negative=signs[0],zero=signs[1],positive=signs[2],zero_crossing_error_mm=abs(plane_zero),pass_test=bool(signs[0]<0 and signs[2]>0 and abs(plane_zero)<1e-5)))
    table('metrics/SDF_RAY_DOMAIN_TESTS.csv',rows);table('metrics/SDF_RAY_DOMAIN_SUMMARY.csv',summary)
    table('metrics/SDF_ANALYTIC_TESTS.csv',analytic);save('provenance/SDF_FIGURE_DATA.json',plots)
    failures=[r for r in summary if r['domain']=='E0_OLD' and r['geometry_status']=='EXPECTED_FAIL_E0']
    candidate_invalid=[r for r in summary if r['domain']!='E0_OLD' and r['geometry_status']=='ADAPTER_INVALID']
    acc=np.float32(1-1e-5);expected_bce=float(-(128*np.log(acc)+64*np.log(np.float32(1)-acc))/192)
    trace=load(E0/'metrics/SDF_LOSS_TRACE.json');old_loss=[r['silhouette']for r in trace]
    save('metrics/SDF_GATE_STATUS.json',dict(old_expected_failure_detected=bool(failures),old_failing_class_rows=len(failures),
        saturated_mask_BCE_expected=expected_bce,E0_recorded_silhouette_min=min(old_loss),E0_recorded_silhouette_max=max(old_loss),
        candidate_invalid_class_rows=len(candidate_invalid),analytic_tests_pass=all(r['pass_test'] for r in analytic),
        ray_Z_max_error_mm=max(r['ray_Z_point_error_mm'] for r in rows if np.isfinite(r['ray_Z_point_error_mm'])),
        official_sampler_execution='BLOCKED_STATIC_ANALYSIS_ONLY',
        E0_full_ray_mask_loss='ADAPTER_INVALID_FOR_ALL_DOMAINS: forced terminal absorption is not foreground opacity',
        candidate_geometry='CPU_GEOMETRY_PASS' if not candidate_invalid else 'ADAPTER_INVALID',
        candidate_mask_adapter='Synthetic finite opacity and real-ray empty-space controls only; FUTURE_REQUIRED, not wired into neural loss',
        candidate_strict_uniform_sampling_fail_N=sum(not r['strict_uniform_sample_fraction_pass']for r in summary if r['domain']!='E0_OLD'),
        C1_SDF='ADAPTER_INVALID',
        reason='E0 full-ray weights.sum mask is saturated by the official terminal absorber even after camera-envelope gauge repair. No runnable SDF loss adapter is certified here.',
        next_SDF_branch='STOP_SDF_BRANCH; no training. Submit CPU evidence and future finite-ROI mask design for separate review.',model_run_N=0))
    table('metrics/SDF_FUTURE_LOSS_CONTRACT.csv',[dict(loss=k,status=v) for k,v in [
        ('RGB','FUTURE_REQUIRED'),('Mask finite-ROI opacity','CPU_GEOMETRY_READY_NOT_WIRED'),('HERO_multi','CPU_GEOMETRY_READY_NOT_WIRED'),
        ('source_conflict_weight','FUTURE_REQUIRED'),('Eikonal','FUTURE_REQUIRED'),('MASt3R_anchor','NOT_IMPLEMENTED'),('CAD','CPU_GEOMETRY_READY_OUTPUT_GATE_ONLY')]])
    save('provenance/SDF_EXECUTED_REUSE.json',REUSE)
    print('SDF_CONTRACT_COMPLETE',len(rows),'ray rows; EXPECTED_FAIL_E0',len(failures),'candidate invalid',len(candidate_invalid),flush=True)

if __name__=='__main__':main()
