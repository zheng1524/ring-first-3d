"""Known-solid CAD penetration diagnostic; no filtering or optimization."""
from evaluate import *
def main():
    rows=[]
    for sid,cid in load(R/'provenance/MAIN_SURFACES_SELECTED.json')['selections'].items():
        ring=source(cid)['ring']
        if not ring.is_watertight:rows.append(dict(scene=sid,status='NOT_EVALUABLE_CAD_NOT_WATERTIGHT'));continue
        sc=camera(target_source(cid));o=o3d();signed=lambda P:sc.scene.compute_signed_distance(o.core.Tensor(np.asarray(P,np.float32)),nthreads=2,nsamples=3).numpy();s0=unique_points(load_scene(sid,0));final=unique_points(load_scene(sid));lookup={(r,int(i)):P for r,i,P in zip(final['references'],final['original_ids'],final['P'])};old_final=np.array([lookup[(r,int(i))]for r,i in zip(s0['references'],s0['original_ids'])]);old0=signed(s0['P']);old1=signed(old_final);tol=.02
        for method,a in [('Initial_S0',s0),('F3_PreJoint_SameFaces',unique_points(no_joint(load_scene(sid)))),('F3_Joint',final),('AllAvailable_Cleaned_F1',f1_points(sid))]:
            d=signed(a['P']);inside=d<-tol;rows.append(dict(scene=sid,method=method,status='KNOWN_CAD_DIAGNOSTIC_NOT_POLYP_GT',point_exposure_denominator=len(d),CAD_inside_point_N=int(inside.sum()),CAD_inside_fraction=float(inside.mean()),maximum_inside_depth_mm=float(max(0,-d.min())),diagnostic_tolerance_mm=tol,old_initial_point_denominator=len(old0),old_initial_inside_N=int((old0<-tol).sum()),old_initial_after_joint_inside_N=int((old1<-tol).sum()),new_old_point_penetrations_after_joint_N=int(((old0>=-tol)&(old1<-tol)).sum()),source_coordinate_and_CAD_pose_conditional=True,action='audit only; no points removed'))
            folder=R/'local_results/CAD_penetration';folder.mkdir(exist_ok=True);np.savez_compressed(folder/(sid+'_'+method+'.npz'),signed_distance_to_fixed_CAD_mm=d,inside_material=inside,diagnostic_tolerance_mm=tol)
        print('CAD AUDIT',sid,flush=True)
    both('CAD_penetration_diagnostic',rows)
if __name__=='__main__':main()
