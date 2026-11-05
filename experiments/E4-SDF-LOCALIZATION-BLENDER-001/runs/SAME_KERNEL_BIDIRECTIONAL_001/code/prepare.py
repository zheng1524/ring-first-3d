"""Generate both symmetric controls before fitting either case. GT stays private."""
from model import *
def main():
    assert not (R/'audit_only/TARGET_GT.npz').exists(),'DO_NOT_OVERWRITE_CONTROL'
    previous=np.load(PARENT/'audit_only/TARGET_GT.npz');center=previous['true_center_mm'].copy()
    # The old preregistered location is reused, never the old fitted center.
    amplitude=-.39 if R.name=='A_expansion'else .39
    body=Body();zero=np.r_[np.zeros(3),0.];V0,F0=body.mesh(zero);q=np.r_[center,amplitude];V,F=body.mesh(q)
    np.savez_compressed(R/'inputs/BASE_SOURCE_MESH.npz',V=V0,F=F0)
    np.savez_compressed(R/'audit_only/TARGET_GT.npz',V=V,F=F,true_center_mm=center,true_radius_mm=body.radius,true_sdf_amplitude_mm=amplitude,q=q)
    save('audit_only/GT_DESIGN.json',dict(q=q,kernel='the identical frozen model.wendland C4',radius_mm=body.radius,source_location=asset(PARENT/'audit_only/TARGET_GT.npz'),selection='previous preregistered control location; NOT previous fitted center',source_field=asset(R/'inputs/BASE_FIELD.npz'),same_DMTet_for_base_GT_prediction=True,physical_motion_not_assumed_equal_to_SDF_coefficient=True))
    source_files=[]
    for name in ['BASE_FIELD.npz','RING_CAD.npz','CAMERAS.json']:
        assert sha(R/'inputs'/name)==sha(PARENT/'inputs'/name)
        source_files.append(asset(R/'inputs'/name))
    # Exact extraction replay tests the forward model; it is not a fit/GT loss.
    v,f=body.mesh(q);assert np.array_equal(v,V)and np.array_equal(f,F)
    save('metrics/CONTROL_FORWARD_AUDIT.json',dict(base_quality=normals_quality(V0,F0),target_quality=normals_quality(V,F),source_files=source_files,GT_roundtrip_exact=True,initial_uses_same_grid=True,amplitude_abs_fixed_mm=.39,derivative_test_reused_from=asset(PARENT/'metrics/DMTET_DERIVATIVE_TEST.json')))
    print('CONTROL_GENERATED',R.name,normals_quality(V,F),flush=True)
if __name__=='__main__':main()
