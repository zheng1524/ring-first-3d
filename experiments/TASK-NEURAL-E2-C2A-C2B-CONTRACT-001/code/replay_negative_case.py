"""Diagnostic counterexample; initial exact failed grouping was not archived."""
from context import *

def main():
    z=np.load(R/'local_results/C2A_synthetic.npz');K=z['K'];T=z['c2w'];n=96
    u,v=np.meshgrid(np.arange(n),np.arange(n));uv=np.c_[u.ravel(),v.ravel()]
    ray=vis.camera_rays(uv,K,T);factor=np.linalg.norm(ray[:,3:],axis=1)
    mesh=trimesh.Trimesh(z['plane_vertices'],z['plane_faces'],process=False)
    hit=SameCameraScene(mesh,K,T,(n,n),str(VENDOR)).cast(uv);t=hit['t_hit'].numpy()*factor;face=hit['primitive_ids'].numpy()
    wrong=np.isfinite(t)&(t>25);correct=(face>=2)&(face<4)
    wrong_err=abs(t[wrong]-(18-T[2,3])*factor[wrong]);correct_err=abs(t[correct]-(18-T[2,3])*factor[correct])
    d=dict(status='DIAGNOSTIC_COUNTEREXAMPLE_PASS',historical_exact_replay=False,
        original_expression_status='NOT_ARCHIVED; do not claim exact reproduction',demonstration_bad_length_threshold_mm=25,
        original_test_status='FAILED_ASSERTION_PRESERVED',unchanged_tolerance_mm=.002,
        wrong_group_front_plane_ray_N=int((wrong&(face<2)).sum()),wrong_max_error_mm=float(wrong_err.max()),correct_max_error_mm=float(correct_err.max()),
        correction='select actual rear triangles by primitive_id2/3, rather than thresholding Euclidean ray length',
        scientific_geometry_changed=False,acceptance_tolerance_changed=False,original_log='runtime/C2A_attempt001.log')
    assert d['wrong_max_error_mm']>.002 and d['correct_max_error_mm']<.002
    save('metrics/REPLAY_FIRST_TEST_FAILURE.json',d);print('DIAGNOSTIC_COUNTEREXAMPLE',d['wrong_group_front_plane_ray_N'],'misclassified rays; tolerance unchanged; not exact historical replay')

if __name__=='__main__':main()
