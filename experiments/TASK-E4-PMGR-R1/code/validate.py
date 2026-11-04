"""Independent numerical calibration, before the sole registered P0 solve."""
from run import *
from collision import fcl_object
import fcl,ast
def main():
    rows=[]
    def check(name,passed,**kw):rows.append(dict(name=name,passed=bool(passed),**kw));save('metrics/NUMERICAL_VALIDATION.json',rows);assert passed,name
    for gap in [.05,-.05]:
        a=trimesh.creation.box([2,2,2]);b=trimesh.creation.box([2,2,2]);b.apply_translation([2+gap,0,0]);dr=fcl.DistanceResult();d=fcl.distance(fcl_object(a.vertices,a.faces),fcl_object(b.vertices,b.faces),fcl.DistanceRequest(enable_nearest_points=True),dr);co=fcl.CollisionResult();n=fcl.collide(fcl_object(a.vertices,a.faces),fcl_object(b.vertices,b.faces),fcl.CollisionRequest(),co)
        name='CONTROL_GAP_'+('POSITIVE'if gap>0 else'NEGATIVE');inp=R/'local_results'/(name+'.npz');out=R/'metrics'/(name+'_BLENDER.json');np.savez_compressed(inp,V=a.vertices,F=a.faces,CAD_V=b.vertices,CAD_F=b.faces);proc=subprocess.run([str(BLENDER),'--factory-startup','--background','--threads','2','--python-exit-code','2','--python',str(R/'code/blender_check.py'),'--',str(inp),str(out)],capture_output=True,text=True,timeout=120);(R/'runtime'/(name+'.log')).write_text(proc.stdout+proc.stderr);assert proc.returncode==0,proc.stderr;bl=load(out)
        check(name+'_FCL',n>0 if gap<0 else abs(d-gap)<1e-8,minimum_distance=d,triangle_collision_N=n)
        check(name+'_BLENDER',bl['EXACT_intersection_volume_mm3']>.19 if gap<0 else bl['EXACT_intersection_volume_mm3']<1e-8,**bl)
    row=p0('G01_004','E2');m=Model(row);q=np.array(row['p']);V,J=m.vertices(q,True);direction=np.array([.2,-.1,.3,.02,-.03,.01,.01,.02,-.02]);h=1e-5;fd=(m.vertices(q+h*direction)-m.vertices(q-h*direction))/(2*h);ana=np.einsum('ijk,k->ij',J,direction);check('LIVE_NINE_VERTEX_JACOBIAN',abs(fd-ana).max()<1e-6,max_error_mm=float(abs(fd-ana).max()))
    rt=mesh_scene(V,m.F);center=q[:3];sd=rt.compute_signed_distance(o3d.core.Tensor(np.array([center,center+[100,0,0]],np.float32))).numpy();mesh=trimesh.Trimesh(V,m.F,process=False);check('CLOSED_OUTWARD_AND_CORRECT_SIGN',mesh.is_watertight and mesh.is_winding_consistent and volume(V,m.F)>0 and sd[0]<0 and sd[1]>0,signed_inside_outside_mm=sd)
    ob=Observations('G01_004',m);z=ob.linearize(q,protocol()['scenes']['G01_004']['P1']);fda=(ob.linearize(q+h*direction,protocol()['scenes']['G01_004']['P1'])['E']-ob.linearize(q-h*direction,protocol()['scenes']['G01_004']['P1'])['E'])/(2*h);ga=float(z['g']@direction);check('REAL_CONTOUR_DEPTH_GEOMETRIC_GRADIENT',np.isfinite(ga)and abs(ga)>1e-8 and abs(ga-fda)<max(.05,.1*abs(fda)),gradient=ga,FD=fda,relative_difference=abs(ga-fda)/max(abs(fda),1e-12))
    stop=Counter()
    try:
        for k in range(10):stop.add(dict(accepted=k>=6,synthetic_stop_control=True))
        worked=False
    except MajorityStop:worked=True
    check('SIX_OF_TEN_REJECTED_GLOBAL_STOP',worked)
    # The control ledger is segregated; it is never counted as real proposals.
    (R/'metrics/ALL_UPDATE_PROPOSALS.json').rename(R/'metrics/SYNTHETIC_STOP_CONTROL.json')
    save('metrics/NUMERICAL_VALIDATION.json',rows);print('VALIDATION',len(rows),'PASS',flush=True)
if __name__=='__main__':main()
