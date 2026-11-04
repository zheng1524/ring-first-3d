"""S1 controls: generated truth only, never used to select real-data settings."""
from models import *
from scipy.optimize import least_squares

def rays_for(C,target,uv,K):
    Q=camera_frame(np.asarray(target)-C,np.array([1.,0,0]));T=np.eye(4);T[:3,:3]=Q;T[:3,3]=C
    return vis.camera_rays(uv,K,T),T

def jac(fun,p,h=1e-4):
    scale=np.r_[np.ones(3),np.full(3,.1),np.full(len(p)-6,.2)]
    return np.column_stack([(fun(p+np.eye(len(p))[j]*h*scale[j])-fun(p-np.eye(len(p))[j]*h*scale[j]))/(2*h)for j in range(len(p))])

def main():
    K=np.array([[180.,0,160],[0,180,120],[0,0,1.]])
    uv=np.array([[x,y]for y in range(90,151,10)for x in range(130,191,10)])
    R0=np.eye(3);base=np.r_[np.zeros(6),np.log([3.,2.,1.5])];rows=[];controls={}
    families=['ellipsoid','star','cap','height']
    for family in families:
        p=np.r_[base,np.zeros(size(family)-9)]
        if family=='star':p[9:]=[.1,-.1,.05,0,.04,0,-.08]
        if family=='cap':p[9]=-.2
        if family=='height':p[8]=np.log(.8);p[9:]=[.1,-.1]
        rays,T=rays_for(np.array([0.,0,20]),np.zeros(3),uv,K);t=first_depth(p,R0,family,rays)
        P,F=mesh(p,R0,family,True);tz=cast(mesh_scene(P,F),uv,K,T)[0];both=np.isfinite(t)&np.isfinite(tz)
        error=np.max(abs(t[both]-tz[both]))if both.any()else np.inf
        X=rays[both,:3]+t[both,None]*rays[both,3:];xc=(X-T[:3,3])@T[:3,:3];axial=np.max(abs(xc[:,2]-t[both]))
        g=geometry_diagnostics(p,R0,family)
        passed=bool(both.sum()>5 and error<.04 and axial<1e-10 and not g['degenerate_faces'] and g['components']==1)
        rows.append(dict(test=family+'_actual_first_hit_vs_exported_mesh',passed=passed,common_hit_N=int(both.sum()),max_error_mm=error,axial_coordinate_error_mm=axial,watertight=g['watertight']))
        trimesh.Trimesh(P,F,process=False).export(R/'local_results'/('S1_'+family+'.ply'))
        controls[family]=dict(p=p,R0=R0,geometry=g)
    # A single frontal silhouette cannot determine hidden thickness; relative depth
    # also cannot distinguish an arbitrary changed hidden underside.
    pairs=[]
    for az in [0,35,70]:
        a=np.deg2rad(az);r,T=rays_for(np.array([20*np.sin(a),0.,20*np.cos(a)]),np.zeros(3),uv,K);pairs.append((r,T))
    truth=base.copy();truth[3:6]=[.08,.12,.04];truth[6:9]=np.log([3,2,1.4])
    def residual(p,n):
        rr=[]
        for rays,T in pairs[:n]:
            z=first_depth(p,R0,'ellipsoid',rays);gt=first_depth(truth,R0,'ellipsoid',rays);valid=np.isfinite(gt)
            # Absolute source depth offset intentionally removed: the D contract.
            v=z[valid];ref=gt[valid]
            if not np.isfinite(v).all():return np.full(sum(np.isfinite(first_depth(truth,R0,'ellipsoid',r)) .sum()for r,t in pairs[:n]),100.)
            rr.extend((v-v.mean()-(ref-ref.mean()))/.25)
        return np.asarray(rr)
    for n in [1,3]:
        J=jac(lambda p:residual(p,n),truth);s=np.linalg.svd(J,compute_uv=False)
        init=truth.copy();init[:3]+=[.03,-.02,.03];init[6:9]+=[.01,-.01,.01]
        fit=least_squares(lambda p:residual(p,n),init,jac='3-point',max_nfev=40,ftol=1e-9,gtol=1e-9,xtol=1e-9)
        controls['relative_depth_'+str(n)+'views']=dict(singular_values=s,effective_rank_1e_3=int((s>s[0]*1e-3).sum()),parameters=fit.x,truth=truth,parameter_error_norm=float(np.linalg.norm(fit.x-truth)),objective=float(fit.fun@fit.fun/2),solver_status=fit.status)
    p2=base.copy();p2[8]=np.log(2.5)
    P1,F1=mesh(base,R0,'ellipsoid',True);P2,F2=mesh(p2,R0,'ellipsoid',True)
    # Orthographic frontal control explicitly labeled; this is not real perspective data.
    rows.append(dict(test='different_hidden_thickness_identical_frontal_xy_support_ORTHOGRAPHIC_CONTROL',passed=bool(np.allclose(P1[:,:2],P2[:,:2])),max_xy_difference_mm=float(abs(P1[:,:2]-P2[:,:2]).max()),hidden_thickness_change_mm=2.))
    back=P1.copy();back[back[:,2]<0,2]*=2
    t1=cast(mesh_scene(P1,F1),uv,K,pairs[0][1])[0];t2=cast(mesh_scene(back,F1),uv,K,pairs[0][1])[0];ok=np.isfinite(t1)&np.isfinite(t2)
    rows.append(dict(test='different_hidden_underside_identical_front_first_depth_PERSPECTIVE_CONTROL',passed=bool(np.allclose(t1[ok],t2[ok])),max_first_depth_difference_mm=float(abs(t1[ok]-t2[ok]).max()),common_hit_N=int(ok.sum())))
    # Head+stalk counterexample: a long thin stalk affects full-mask extents, whereas
    # head-only boundary has its own identity. It is not a generated real stalk.
    xx,yy=np.meshgrid(np.arange(240),np.arange(240));head=((xx-120)/45)**2+((yy-85)/38)**2<=1;stalk=(abs(xx-120)<=6)&(yy>=85)&(yy<=210);labels=(head|stalk).astype(np.uint8)
    cue,meta=head_cue(labels,'Ip');rows.append(dict(test='synthetic_head_stalk_separation',passed=bool(cue.sum()<labels.sum()and (cue&head).sum()/head.sum()>.8),full_pixels=int(labels.sum()),cue_pixels=int(cue.sum()),head_retention=float((cue&head).sum()/head.sum()),stalk_only_retained=int((cue&stalk&~head).sum())))
    np.savez_compressed(R/'local_results/S1_head_stalk.npz',head=head,stalk=stalk,cue=cue)
    table('metrics/S1_NUMERICAL_TESTS.csv',rows);save('metrics/S1_CONTROLS.json',dict(tests=rows,controls=controls,all_pass=all(r['passed']for r in rows),real_data_parameter_selection=False))
    print(json.dumps(clean(rows),indent=2),flush=True)
    assert all(r['passed']for r in rows),'S1 numerical contract failed; do not start real fits'
if __name__=='__main__':main()
