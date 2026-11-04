"""Bounded joint-view BFGS trust-region and collision-feasible directions."""
from inputs import *
from shape import Body,construct_basis
from objective import Objective
from physical import *
from scipy.optimize import minimize
import time

def project_jac(V,J,K,T):
    P=(V-T[:3,3])@T[:3,:3];H=P@K.T;z=H[:,2];uv=H[:,:2]/z[:,None];D=(K[None,:2,:]*z[:,None,None]-H[:,:2,None]*K[None,2,None,:])/z[:,None,None]**2;return uv,np.einsum('nij,njk->nik',D,np.einsum('ij,njk->nik',T[:3,:3].T,J))

def image_trust(ob,V,J,images):
    rows=[];errors=[]
    for cid,d in ob.data.views.items():
        uv,ij=project_jac(V,J,d['K'],d['s']['T']);z=vis.project_camera(V,d['K'],d['s']['T'])[1];inside=(z>0)&(uv[:,0]>=0)&(uv[:,0]<320)&(uv[:,1]>=0)&(uv[:,1]<180);rows.append(ij[inside].reshape(-1,J.shape[-1]))
        pred=images[cid]['hard'];b=contour(pred)
        if len(b):
            x=b[:,0].astype(int);y=b[:,1].astype(int);ok=d['known_np'][y,x];errors.extend(abs(d['sdf'].cpu().numpy()[y[ok],x[ok]])*5)
    IJ=np.vstack(rows);IJ=IJ[::max(1,len(IJ)//512)];radius=max(1.,float(np.quantile(errors,.75)))if errors else 1.
    return IJ,radius

def observable(body,q,ob):
    V,J=body.vertices(q,True);rt=mesh_scene(V,body.F);rows=[];source_rows=[]
    for cid,d in ob.data.views.items():
        uv,ij=project_jac(V,J,d['K'],d['s']['T']);_,z=vis.project_camera(V,d['K'],d['s']['T']);hit=cast(rt,uv,d['K'],d['s']['T'])[0];cad=cast(ringscene(ob.scene),uv,d['K'],d['s']['T'])[0];px=np.clip(np.rint(uv).astype(int),[0,0],[319,179]);good=(z>0)&(uv[:,0]>=0)&(uv[:,0]<320)&(uv[:,1]>=0)&(uv[:,1]<180)&d['known_np'][px[:,1],px[:,0]]&~(np.isfinite(hit)&(hit<z-.05))&(z<=cad+.05);A=ij[good].reshape(-1,len(q));rows.append(A);source_rows.append(dict(source=cid,visible_fixed_vertices_N=int(good.sum()),proxy_column_norm=np.linalg.norm(A,axis=0)))
    A=np.vstack(rows);s=np.linalg.svd(A,compute_uv=False);norm=np.linalg.norm(A,axis=0);gradients=np.stack([ob.evaluate(q,gradient=True,mask_only=True,source_subset=[c])['g']for c in ob.data.ids]);eps=np.maximum(np.max(abs(gradients),axis=0)*.01,1e-7);conflict=(gradients>eps).any(0)&(gradients<-eps).any(0)
    return dict(proxy='visible-vertex projected geometry Jacobian and per-source Mask gradient signs, not independent statistical certification',singular_values=s,rank=int((s>s[0]*1e-6).sum())if len(s)else 0,column_status=['UNOBSERVABLE'if n<=1e-4 else('CONFLICT_PROXY'if c else'OBSERVABLE_PROXY')for n,c in zip(norm,conflict)],column_norm=norm,Mask_gradient_by_source=gradients,sources=source_rows,conflicting_modes_not_deleted=True)

def save_stage(scene,arm,stage,body,q,ob,status,extra=None):
    folder=R/'local_results'/scene/arm;folder.mkdir(parents=True,exist_ok=True);V=body.vertices(q);np.savez_compressed(folder/(stage+'.npz'),V=V,F=body.F,q=q);trimesh.Trimesh(V,body.F,process=False).export(folder/(stage+'.ply'));ev=ob.evaluate(q,stage='P2',gradient=False,return_images=True)
    for cid,im in ev['images'].items():np.savez_compressed(folder/(stage+'__'+cid+'.npz'),**im)
    col=endpoint(ob.col,V,body.F,scene+'_'+arm+'_'+stage+'_CONTACT');bl=blender_check(scene+'_'+arm+'_'+stage,scene,V,body.F);assert not col['collision']and bl['EXACT_intersection_volume_mm3']<=1e-8
    q0=np.r_[body.p,np.zeros(len(q)-9)];delta=np.linalg.norm(V-body.vertices(q0),axis=1);total=np.linalg.norm(V-body.vertices(body.p),axis=1);qr,qa=quality(V,body.F,body.vertices(body.p));assert not qr
    result=dict(case=scene,arm=arm,stage=stage,status=status,active_detail_N=len(q)-9,fixed_common_objective=ev['E'],data_objective=ev['data_E'],reg=ev['reg'],barrier=ev['barrier'],per_view=ev['per_view'],collision=col,Blender=bl,quality=qa,maximum_P0_move_mm=float(total.max()),median_P0_move_mm=float(np.median(total)),maximum_nonellipsoid_displacement_mm=float(delta.max()),median_nonellipsoid_displacement_mm=float(np.median(delta)),q=q,extra=extra)
    save('metrics/'+scene+'_'+arm+'_'+stage+'.json',result);return result

def run_stage(scene,arm,stage,body,q,ob,B,damping,budget,records):
    V,J=body.vertices(q,True);M=np.einsum('nci,ncj->ij',J,J)/len(V);diag=np.maximum(np.diag(M),1e-6)
    if B is None:B=.05*M+np.diag(diag*.001)
    elif B.shape[0]<len(q):
        BB=.05*M+np.diag(diag*.001);n=B.shape[0];BB[:n,:n]=B;B=BB
    current=ob.evaluate(q,stage,True,return_images=True);accepted_N=0;rejected_N=0;converged=False;start=time.perf_counter();failure_saved=set();num_fault=None
    for iteration in range(budget):
        if not current['finite']:num_fault='NONFINITE_CURRENT_OBJECTIVE';break
        V,J=body.vertices(q,True);IJ,radius=image_trust(ob,V,J,current['images']);gs,G,info=ob.col.constraints(V,body.F,J,activation_distance=.25);activation=.25;accepted=False;g=current['g'];scale=np.maximum(np.diag(np.einsum('nci,ncj->ij',J,J)/len(V)),1e-6)
        for trial in range(protocol()['trials_per_iteration']):
            A=(B+B.T)/2+damping*np.diag(scale);val=np.linalg.eigvalsh(A).min()
            if val<=0:A+=np.diag(scale)*(abs(val)/scale.min()+.001)
            linear=dict(type='ineq',fun=lambda d:gs-ob.col.eps+G@d,jac=lambda d:G);pixel=dict(type='ineq',fun=lambda d:np.r_[radius-IJ@d,radius+IJ@d],jac=lambda d:np.vstack([-IJ,IJ]));sol=minimize(lambda d:.5*d@A@d+g@d,np.zeros(len(q)),jac=lambda d:A@d+g,method='SLSQP',constraints=[linear,pixel],options=dict(maxiter=60,ftol=1e-9,disp=False));d=sol.x;qp=q+d;proposed=body.vertices(qp);move=float(np.linalg.norm(proposed-V,axis=1).max());reason=[];phys=None;qa=None;candidate=None;path=None
            if not sol.success:reason.append('FEASIBLE_QP:'+str(sol.message))
            if not np.isfinite(proposed).all():reason.append('NUMERICAL_NONFINITE')
            if not reason:
                phys=endpoint(ob.col,proposed,body.F,scene+'_'+arm+'_'+stage+'_CONTACT')
                if phys['collision']:reason.append('RING_SOLID_INTERSECTION')
                qr,qa=quality(proposed,body.F,ob.V0);reason+=qr
            if not reason:
                okay,path=ob.col.path(V,proposed,body.F)
                if not okay:reason.append('CONTINUOUS_CLEARANCE_UNRESOLVED_OR_INTERSECTION')
            if not reason:
                candidate=ob.evaluate(qp,stage,False)
                if not candidate['finite']:reason.append('NUMERICAL_NONFINITE_OBJECTIVE')
            prediction=float(-g@d-.5*d@B@d);actual=current['E']-(candidate['E']if candidate else current['E']);rho=actual/max(prediction,1e-15)
            if candidate and(actual<=0 or prediction<=0):reason.append('JOINT_ACTUAL_OBJECTIVE_NOT_IMPROVED')
            if move<ob.col.eps:reason.append('BELOW_NUMERICAL_GEOMETRY_RESOLUTION')
            key=f'{scene}_{arm}_{stage}_{iteration:03d}_{trial}';entry=dict(case=scene,arm=arm,stage=stage,iteration=iteration,trial=trial,accepted=not reason,reasons=reason,before_E=current['E'],proposed_E=candidate['E']if candidate else None,predicted_reduction=prediction,actual_reduction=actual,rho=rho,damping=damping,pixel_radius=radius,maximum_vertex_move_mm=move,median_vertex_move_mm=float(np.median(np.linalg.norm(proposed-V,axis=1))),active_Ring_constraints=info['active_constraints_N'],activation_distance_mm=activation,physical=phys,path=path,quality=qa,per_view=candidate['per_view']if candidate else None,QP_iterations=int(sol.nit))
            records.append(entry)
            # Stream compact records; only one diagnostic candidate per reason.
            if reason:
                tag=reason[0].split(':')[0]
                if tag not in failure_saved and len(failure_saved)<4:
                    np.savez_compressed(R/'local_results'/scene/arm/(stage+'_FAIL_'+tag+'.npz'),before_V=V,proposed_V=proposed,F=body.F,q_before=q,q_proposed=qp);failure_saved.add(tag)
            if not reason:
                old_g=g;new=ob.evaluate(qp,stage,True,return_images=True);y=new['g']-old_g;s=d;ys=float(y@s);Bs=B@s;sBs=float(s@Bs)
                if ys>1e-9 and sBs>1e-12:B=B+np.outer(y,y)/ys-np.outer(Bs,Bs)/sBs
                q=qp;current=new;accepted=True;accepted_N+=1;damping=max(1e-7,damping*(.5 if rho>.75 else(4 if rho<.25 else 1)))
            else:
                rejected_N+=1;damping=min(1e8,damping*4)
                if phys and phys['collision']:
                    activation=max(activation,move+.1);gs,G,info=ob.col.constraints(V,body.F,J,activation_distance=activation)
            save('metrics/'+scene+'_'+arm+'_UPDATE_LOG.json',records)
            print('STEP',scene,arm,stage,iteration,trial,'A'if accepted else'R',reason,'mm',round(move,4),'E',round(current['E'],6),'rho',round(rho,3),flush=True)
            if accepted:break
        # Exhausted proposals block this iteration, not all future stages/cases.
        if not accepted and damping>=1e8:break
        if accepted and actual<1e-7 and np.linalg.norm(current['g'])<1e-4:converged=True;break
    status='NUMERICAL_FAULT'if num_fault else('CONVERGED'if converged else('STAGE_BLOCKED_NO_ACCEPTABLE_UPDATE'if accepted_N==0 else'BUDGET_COMPLETED'))
    return q,B,damping,dict(status=status,accepted_N=accepted_N,rejected_N=rejected_N,elapsed_seconds=time.perf_counter()-start,fault=num_fault,budget_iterations=budget,attempted_iterations=iteration+1)
