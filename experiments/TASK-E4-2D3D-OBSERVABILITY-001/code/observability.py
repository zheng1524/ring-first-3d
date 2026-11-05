"""A2 only: fixed-row image residuals, no native 3D GT access or optimizer."""
import os
os.environ['E4_OPTIMIZER_ONLY']='1'
from continuous import *
from model import Body,normals_quality
from seed import seed
from physics import physical
def svd(J):
    _,s,v=np.linalg.svd(J,full_matrices=False)
    return dict(singular_values=s,condition=float(s[0]/s[-1])if s[-1]>1e-12 else None,rank=int((s>max(s[0]*1e-4,1e-8)).sum()),right_vectors=v)
def main():
    assert load(R/'metrics/PROJECTION_GATE.json')['passed']
    assert not (R/'metrics/OBSERVABILITY.json').exists()
    body=Body();renderer=Renderer();q=seed(body,renderer);fixed=FixedResidual(renderer);V0,F0=body.mesh(np.r_[q[:3],0.]);reference=signed(scene(V0,F0),V0)
    np.savez_compressed(R/'inputs/FIXED_RESIDUAL_QUERIES.npz',**{cid+'__uv':a[0]for cid,a in fixed.rows.items()})
    allrows=[];modes=[]
    for label,base in [('P0_amplitude_zero',np.r_[q[:3],0.]),('MASK_seed',q)]:
        V,F=body.mesh(base);res,info=fixed.evaluate(V,F);derivs=[];physical_scales=[];topology=[]
        for eps in [.02,.01]:
            J=[];scales=[]
            for j in range(4):
                delta=np.eye(4)[j]*eps;Vp,Fp=body.mesh(base+delta);Vm,Fm=body.mesh(base-delta);rp,ip=fixed.evaluate(Vp,Fp);rm,im=fixed.evaluate(Vm,Fm)
                J.append((rp-rm)/(2*eps));scales.append(float(np.max(abs((-signed(scene(Vp,Fp),V0)+signed(scene(Vm,Fm),V0))/(2*eps)))))
                topology.append(dict(epsilon_mm=eps,parameter=j,plus_vertices=len(Vp),minus_vertices=len(Vm),tessellation_changes=not np.array_equal(Fp,Fm),plus_physical_topology=normals_quality(Vp,Fp),minus_physical_topology=normals_quality(Vm,Fm),plus_segments=ip,minus_segments=im))
            derivs.append(np.array(J).T);physical_scales.append(np.array(scales))
        scales=physical_scales[1];D=np.divide(1.,scales,out=np.zeros(4),where=scales>1e-6);Jn=derivs[1]*D;deviation=float(np.linalg.norm((derivs[0]-derivs[1])*D)/max(np.linalg.norm(Jn),1e-15));s=svd(Jn)
        perview=[dict(view=cid,**svd(Jn[sl]))for cid,sl in fixed.slices.items()]
        row=dict(location=label,q=base,J_raw_epsilon=svd(derivs[0]),J_raw_half=svd(derivs[1]),physical_max_surface_mm_per_raw_parameter_mm=scales,raw_parameter_mm_per_unit_physical_column=D,whitened_physical_SVD=s,per_view=perview,epsilon_relative_J_difference=deviation,numerically_sensitive=deviation>.2,topology_checks=topology,residual_norm=float(np.linalg.norm(res)),residual_definition='same fixed image query indices and known mask; signed exact projected-segment distance in px, /0.5 noise /sqrt(N_view)')
        allrows.append(row)
        np.savez_compressed(R/'audit_only'/(label+'_JACOBIAN.npz'),J_epsilon=derivs[0],J_half=derivs[1],J_physical=Jn,D=D,q=base,residual=res)
        if label!='MASK_seed':continue
        ref=-signed(scene(V,F),V0)+reference;bounds=np.array(protocol()['center_bounds_mm']).T.tolist()+[protocol()['amplitude_bounds_mm']];bounds=np.array(bounds)
        for mode,k in [('weak',-1),('strong',0)]:
            raw=D*s['right_vectors'][k]
            for sign in [-1,1]:
                direction=sign*raw;tmax=min([(bounds[j,1]-base[j])/direction[j]if direction[j]>0 else(bounds[j,0]-base[j])/direction[j]for j in range(4)if abs(direction[j])>1e-12])
                def evaluate(t):
                    qq=base+t*direction;vv,ff=body.mesh(qq);delta=-signed(scene(vv,ff),V0)+reference-ref
                    return vv,ff,delta
                ve,fe,change=evaluate(tmax);maxend=float(max(abs(change)))
                if maxend>=.3:
                    lo=0.;hi=tmax
                    for _ in range(12):
                        mid=(lo+hi)/2;vv,ff,dd=evaluate(mid)
                        if max(abs(dd))<.3:lo=mid
                        else:hi=mid
                    t=(lo+hi)/2
                else:t=tmax
                vv,ff,dd=evaluate(t);qq=base+t*direction;name=mode+('_minus'if sign<0 else'_plus');body.save('A2_'+name,qq)
                rr,_=fixed.evaluate(vv,ff);per=[]
                for c in renderer.views:
                    cid=c['id'];S=surface_segments(renderer,V,F,cid);T=surface_segments(renderer,vv,ff,cid);dist=np.r_[distance_segments(S.mean(1),T),distance_segments(T.mean(1),S)];p=renderer.project(scene(V,F),cid)[0];p2=renderer.project(scene(vv,ff),cid)[0]
                    per.append(dict(view=cid,role=c['role'],Mask_mutual_IoU=float((p&p2).sum()/max(1,(p|p2).sum())),subpixel_change_px=stats(dist),target_metrics=subpixel_metrics(renderer,vv,ff,cid)))
                modes.append(dict(mode=name,q=qq,raw_direction=direction,scalar=t,available_scalar_max=tmax,target_displacement_mm=.3,achieved_displacement_mm=stats(dd),requested_range_reached=.2<=max(abs(dd))<=.5,bound_limited=t==tmax,residual_change_norm=float(np.linalg.norm(rr-res)),physical=physical(vv,ff),per_view=per,volume_delta_mm3=float(trimesh.Trimesh(vv,ff,process=False).volume-trimesh.Trimesh(V,F,process=False).volume)))
    save('metrics/OBSERVABILITY.json',dict(no_native_GT_read=True,fixed_residual_N=fixed.N,view_support=fixed.meta,locations=allrows,perturbations=modes,local_not_global_identifiability=True,GT_q_for_native_CAD='DOES_NOT_EXIST'))
    table('metrics/VIEW_SUPPORT.csv',fixed.meta);table('metrics/MODE_PERTURBATIONS.csv',modes)
    print('OBSERVABILITY_DONE',[(x['location'],x['whitened_physical_SVD']['singular_values'],x['epsilon_relative_J_difference'])for x in allrows],[(x['mode'],x['achieved_displacement_mm']['maximum'],x['requested_range_reached'])for x in modes],flush=True)
if __name__=='__main__':main()
