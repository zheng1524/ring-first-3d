from field import *
from data import Data
from collision import Collision
from scipy.spatial import cKDTree
from scipy.sparse.linalg import lsmr
from solver import Evolution
import subprocess
def blender(name,V,F):
    cad=ringmesh('G01_004');inp=R/'runtime'/(name+'.npz');out=R/'metrics'/(name+'_BLENDER.json');np.savez_compressed(inp,V=V,F=F,CAD_V=cad.vertices,CAD_F=cad.faces)
    proc=subprocess.run(['/home/liu/blender/blender-5.0.1-linux-x64/blender','--factory-startup','--background','--threads','2','--python-exit-code','2','--python',str(R/'code/blender_check.py'),'--',str(inp),str(out)],capture_output=True,text=True,timeout=120)
    (R/'runtime'/(name+'_Blender.log')).write_text(proc.stdout+proc.stderr);assert proc.returncode==0;return load(out)
def main():
    a=np.load(R/'inputs/INITIAL_FIELD.npz');g=Field(a['origin'],a['shape'],float(a['h']));phi=a['phi'];V,F=g.mesh(phi);rt=mesh_scene(V,F);rows=[]
    def record(test,passed,**kw):rows.append(dict(test=test,passed=bool(passed),**kw));print(test,passed,flush=True)
    rng=np.random.default_rng(20261105);P=g.origin+(np.array(g.shape)-1)*g.h*(.05+.9*rng.random((100,3)));B,valid=g.basis(P);plane=g.points@np.array([.2,-.7,.3])+1
    err=max(abs(B@plane-(P@np.array([.2,-.7,.3])+1)));record('trilinear_metric_axis_and_partition',err<1e-10 and max(abs(B.sum(1).A.ravel()-1))<1e-12,max_error_mm=err)
    # Actual field derivative on real, interior-cell points; not just camera Jacobian.
    P=g.origin+(np.array(g.shape)-2)*g.h*(.05+.9*rng.random((100,3)))+.00123
    exact=g.query_gradient(phi,P);fd=np.column_stack([(g.value(phi,P+np.eye(3)[k]*1e-6)-g.value(phi,P-np.eye(3)[k]*1e-6))/2e-6 for k in range(3)]);err=np.max(abs(exact-fd));record('actual_trilinear_field_gradient',err<1e-7,max_component_error=err,at_grid_planes='positive side, C0 field not C1')
    P=V[::max(1,len(V)//50)];s=source(protocol()['fit'][0]);J=project_jacobian(P,s['K'],s['T']);fd=np.empty_like(J)
    for k in range(3):
        off=np.eye(3)[k]*1e-5;fd[:,:,k]=(vis.project_camera(P+off,s['K'],s['T'])[0]-vis.project_camera(P-off,s['K'],s['T'])[0])/2e-5
    rel=np.linalg.norm(J-fd)/np.linalg.norm(fd);record('real_camera_projection_Jacobian',rel<1e-7,relative_error=rel)
    orig=mesh_scene(a['V'],a['F']);drift=np.r_[abs(signed(orig,V)),abs(signed(rt,a['V']))];col=Collision('G01_004');physical=col.check(V,F);m=trimesh.Trimesh(V,F,process=False);center=m.center_mass;signs=signed(rt,np.array([center,center+[100,0,0]]))
    record('P0_to_metric_SDF_roundtrip',drift.max()<.04 and m.is_watertight and m.is_winding_consistent and signs[0]<0<signs[1] and not physical['collision'],roundtrip_surface_error_mm=stats(drift),signs_mm=signs,Ring=physical,closed=m.is_watertight,V=len(V),F=len(F))
    bb=blender('INITIAL_SDF',V,F);record('initial_independent_Blender',bb['EXACT_intersection_volume_mm3']<=1e-8,Blender=bb)
    gs=Field([-3,-3,7],[25,25,25],.25);c=np.array([0,0,10.]);sp=np.linalg.norm(gs.points-c,axis=1)-2;SV,SF=gs.mesh(sp)
    for off,label,sign in [(-.05,'expansion',1),(.05,'contraction',-1)]:
        vv,ff=gs.mesh(sp+off);dv=volume(vv,ff)-volume(SV,SF);record('level_set_'+label,sign*dv>0,volume_delta_mm3=dv)
    # Actual common contour builder and a nonconstant grid LS update in a labelled control experiment.
    K=np.array([[120.,0,160],[0,120,90],[0,0,1]]);T=np.eye(4);u,v=np.meshgrid(np.arange(320),np.arange(180));uv=np.c_[u.ravel(),v.ravel()]
    for radius,label,sgn in [(2.35,'underprediction_expand',1),(1.65,'overprediction_shrink',-1)]:
        tv,tf=gs.mesh(np.linalg.norm(gs.points-c,axis=1)-radius);z,_=cast(mesh_scene(tv,tf),uv,K,T);target=np.isfinite(z).reshape(180,320);di=Data.__new__(Data);di.fit=['CONTROL'];di.cad_rt=o3d.t.geometry.RaycastingScene(nthreads=2);co=contour(target);sd=cv2.distanceTransform((~target).astype(np.uint8),cv2.DIST_L2,cv2.DIST_MASK_PRECISE)-cv2.distanceTransform(target.astype(np.uint8),cv2.DIST_L2,cv2.DIST_MASK_PRECISE);di.views={'CONTROL':dict(K=K,c2w=T,known=np.ones((180,320),bool),target=target,contour=co,tree=cKDTree(co),sd=sd)}
        rr=di.contour_rows(SV,SF,gs,sp);vel=np.array([r['normal_velocity_mm']for r in rr]);B,_=gs.basis(np.array([r['P']for r in rr]));w=np.array([r['w']/r['grad_norm']for r in rr]);r=np.array([r['residual']for r in rr]);A=sparse.vstack([sparse.diags(w[:,k])@B for k in range(2)],format='csr');b=np.r_[r[:,0],r[:,1]];sol=lsmr(A,b,damp=.1,maxiter=120,atol=1e-7,btol=1e-7)[0];sol=np.clip(sol,-.03,.03);vv,ff=gs.mesh(sp+sol);dv=volume(vv,ff)-volume(SV,SF)
        record('common_contour_pipeline_'+label,len(rr)>10 and sgn*np.median(vel)>0 and sgn*dv>0,correspondences_N=len(rr),normal_velocity_median_mm=float(np.median(vel)),actual_volume_delta_mm3=dv,control_only=True)
    data=Data();e=Evolution(g,phi,data);record('initial_constraint_box_feasibility',np.min(e.C@phi)>.025 and e.protect.sum()>0,CAD_min_field_mm=float(np.min(e.C@phi)),protected_HERO_N=int(e.protect.sum()),qualified_HERO_N=int(e.eligible.sum()),all_fit_fixed_N=4*512)
    # Force-free identity is exact because no distance reinitialization or mesh smoothing is applied.
    VV,FF=g.mesh(phi+np.zeros_like(phi));record('zero_force_identity',np.array_equal(V,VV)and np.array_equal(F,FF),reinitialization=False)
    save('metrics/NUMERICAL_PREFLIGHT.json',dict(passed=all(x['passed']for x in rows),checks=rows));table('metrics/NUMERICAL_PREFLIGHT.csv',rows)
    assert all(x['passed']for x in rows),'PREFLIGHT_FAILED_NO_REAL_OPTIMIZATION'
    snapshot('INITIAL',g,phi,status='FROZEN_SDF_INITIAL')
if __name__=='__main__':main()
