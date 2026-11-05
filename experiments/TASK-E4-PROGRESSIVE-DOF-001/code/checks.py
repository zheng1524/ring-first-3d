"""Zero-set/parameter contracts and diagnostics of the ACTUAL Powell objective."""
import os
os.environ['E4_OPTIMIZER_ONLY']='1'
from model import *
from continuous import *
from physics import physical
def gradient_norm(body,q):
    a=body.a;h=float(a['h']);g=np.stack(np.gradient(a['phi'].reshape(a['shape']),h),axis=-1).reshape(-1,3);s=np.exp(q[3:6]);G=g*np.exp(np.mean(q[3:6]))/s;X=body.points(q)
    if len(q)>6:
        centers=body.kernel_centers(q)
        for j in range(2):
            d=X-centers[j];r=np.linalg.norm(d,axis=1)/body.radius;t=np.maximum(1-r,0)
            G+=q[6+j]*(-56/(3*body.radius**2))*(5*r+1)[:,None]*t[:,None]**5*d
    near=abs(body.values(q))<.15
    return dict(near_zero_nodes_N=int(near.sum()),gradient_norm=stats(np.linalg.norm(G[near],axis=1)),strict_distance_field=False,anisotropic_field_is_implicit_not_unit_gradient=True)
def sensitivity(body,renderer,q,name):
    q=np.asarray(q);fixed=FixedResidual(renderer);V,F=body.mesh(q);res,_=fixed.evaluate(V,F);L,parts=objective(body,renderer,q,False);cfg=protocol();bounds=np.array(cfg['global_bounds']+([]if len(q)==6 else cfg['amplitude_bounds_mm'])+([[-cfg['center_offset_limit_mm'],cfg['center_offset_limit_mm']]]*(len(q)-8) if len(q)>8 else[]));D=np.ones(len(q));D[3:6]=1/(body.a0*np.exp(q[3:6]));rows=[];jac=[]
    for eps in [.02,.01]:
        cols=[];scalar=[];per=[]
        for j in range(len(q)):
            plus=q.copy();minus=q.copy();plus[j]=min(q[j]+eps*D[j],bounds[j,1]);minus[j]=max(q[j]-eps*D[j],bounds[j,0]);den=(plus[j]-minus[j])/D[j]
            vp,fp=body.mesh(plus);vm,fm=body.mesh(minus);rp,_=fixed.evaluate(vp,fp);rm,_=fixed.evaluate(vm,fm);lp,pp=objective(body,renderer,plus,False);lm,pm=objective(body,renderer,minus,False)
            cols.append((rp-rm)/den);scalar.append((lp-lm)/den);per.append(dict(parameter=j,plus_loss=lp,minus_loss=lm,plus_parts=pp,minus_parts=pm,physical_denominator_mm=den,tessellation_changed=not np.array_equal(fp,fm),geometric_topology_plus=normals_quality(vp,fp),geometric_topology_minus=normals_quality(vm,fm)))
        J=np.array(cols).T;g=np.array(scalar);diag=J.T@res;sing=np.linalg.svd(J,compute_uv=False);cos=float(g@diag/(max(np.linalg.norm(g)*np.linalg.norm(diag),1e-15)))
        rows.append(dict(epsilon_physical_mm=eps,actual_Powell_scalar_gradient=g,fixed_residual_square_gradient=diag,gradient_cosine=cos,opposite_component_signs=int(((g*diag<0)&(abs(g)>1e-8)).sum()),fixed_residual_SVD=sing,columns=per));jac.append(J)
    save('metrics/'+name+'_SENSITIVITY.json',dict(q=q,actual_objective=L,actual_parts=parts,rows=rows,actual_gradient_epsilon_relative_difference=float(np.linalg.norm(np.array(rows[0]['actual_Powell_scalar_gradient'])-rows[1]['actual_Powell_scalar_gradient'])/max(np.linalg.norm(rows[1]['actual_Powell_scalar_gradient']),1e-15)),fixed_J_relative_difference=float(np.linalg.norm(jac[0]-jac[1])/max(np.linalg.norm(jac[1]),1e-15)),fixed_residual_not_used_by_optimizer=True,GT_access=False,field_gradient=gradient_norm(body,q)))
    np.savez_compressed(R/'audit_only'/(name+'_DIAGNOSTIC_J.npz'),J_epsilon=jac[0],J_half=jac[1],q=q,residual=res)
    print('SENSITIVITY_DONE',name,'actual loss',L,'gradient cosines',[x['gradient_cosine']for x in rows],flush=True)
def main():
    import sys
    phase=sys.argv[1];body=Body();renderer=Renderer()
    if phase=='P0':
        old=np.load(R/'inputs/BASE_SOURCE_MESH.npz');q=np.zeros(6);V,F=body.mesh(q);assert np.array_equal(V,old['V'])and np.array_equal(F,old['F']),'P0_ZERO_SET_NOT_IDENTICAL';rows=[]
        for j in range(6):
            t=q.copy();t[j]=.02 if j<3 else .02/body.a0[j-3];v,f=body.mesh(t);s=np.exp(t[3:6]);expected=V*s+body.c0*(1-s)+t[:3];error=float(np.max(abs(v-expected)))
            assert np.array_equal(f,F)and error<1e-6
            rows.append(dict(parameter=j,expected_affine_max_error_mm=error,physical=physical(v,f)))
        blocked=[]
        for path in [REPO/'experiments/TASK-E4-2D3D-OBSERVABILITY-001/audit_only/NATIVE_CAD_GT.npz',R/'audit_only/nonexistent_GT.npz']:
            try:open(path,'rb');raise AssertionError('GT_FIREWALL_BYPASS')
            except PermissionError:blocked.append(str(path))
        save('metrics/P0_ZERO_AND_FIREWALL.json',dict(passed=True,P0_VF_identical=True,rows=rows,GT_blocked=blocked,source_initial_physical=physical(V,F),field_gradient=gradient_norm(body,q)))
        sensitivity(body,renderer,q,'P0_GLOBAL6')
    elif phase=='LOCAL':
        q6=np.array(load(R/'metrics/S1_FINISHED.json')['q']);q=np.r_[q6,0.,0.];V,F=body.mesh(q);baseVol=trimesh.Trimesh(V,F,process=False).volume;ref=scene(V,F);rows=[]
        for k,amp in [(0,-.02),(1,.02)]:
            qq=q.copy();qq[6+k]=amp;v,f=body.mesh(qq);vol=trimesh.Trimesh(v,f,process=False).volume;d=-signed(scene(v,f),V)+signed(ref,V);shift=body.values(qq)-body.values(q)
            sign_ok=bool(np.all(shift<=1e-12))if amp<0 else bool(np.all(shift>=-1e-12));volume_ok=vol>baseVol if amp<0 else vol<baseVol
            assert sign_ok and volume_ok,'KERNEL_GEOMETRY_DIRECTION_CONTRACT_FAILED'
            rows.append(dict(kernel=k,amplitude=amp,node_sign_ok=sign_ok,volume_direction_ok=bool(volume_ok),volume_change_mm3=float(vol-baseVol),actual_Eulerian_motion_mm=stats(d),physical=physical(v,f)))
        save('metrics/LOCAL_ZERO_CONTRACT.json',dict(passed=True,rows=rows,center_sensitivity_at_zero_amplitude='exactly zero; do not release centers on this alone'))
        sensitivity(body,renderer,q,'S1_LOCAL8')
    elif phase=='CENTERS':
        q=np.r_[np.array(load(R/'metrics/S2_FINISHED.json')['q']),np.zeros(3*len(load(R/'metrics/CENTER_RELEASE_GATE.json')['active_kernel_ids']))];assert load(R/'metrics/CENTER_RELEASE_GATE.json')['released'];sensitivity(body,renderer,q,'S2_ACTIVE_CENTERS')
if __name__=='__main__':main()
