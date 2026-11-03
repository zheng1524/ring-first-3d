"""Post-analysis checks, never changes the frozen A/B experiment or thresholds."""
from residuals import *
from experiment_b import spectrum
def main():
    tests=[]
    def check(name,passed,**kw):tests.append(dict(name=name,passed=bool(passed),**kw))
    old=Path('/home/liu/ring_first_3d_view_eval/experiments/TASK-VIEW-OBSERVABILITY-GT-EVAL-001/local_results/reprojection')
    primary='G01_004_ref08__G01_004_growth_r14_Raw_RF.npz';current=np.load(R/'local_results/A'/primary);original=np.load(old/'G01_004_ref08__to__004_14.npz')
    equal={k:bool(np.array_equal(current[k],original[k]))for k in current.files};check('historical_raw_reprojection_bitwise_exact',all(equal.values()),fields=equal)
    for pair in protocol()['pairs']:
        h=pair['historical_pair'];s=source(pair['B'])
        oldK=np.array(h['B_target']['K']if 'B_target'in h else h['B_K']);oldT=np.array(h['B_target']['c2w']if 'B_target'in h else h['B_c2w'])
        oldRGB=h['B_target']['RGB']if 'B_target'in h else h['B_RGB'];oldMask=h['B_target']['Mask']if 'B_target'in h else h['B_Mask']
        check('historical_pair_identity:'+pair['A'],np.array_equal(s['K'],oldK)and np.array_equal(s['T'],oldT)and sha(s['c']['RGB'])==sha(oldRGB)and sha(s['c']['Mask'])==sha(oldMask))
    K=np.array([[400.,0,320],[0,400.,180],[0,0,1]]);Ta=np.eye(4);Tb=np.eye(4);Tb[0,3]=2.;uv=np.array([[320.,180.]]);h=1e-4
    def point(b):return unproject(np.array([20.+b]),Ta,uv,K)
    f=lambda x,T:vis.project_camera(x,K,T)[0][0,0]
    depth_deriv=(f(point(h),Tb)-f(point(-h),Tb))/(2*h);x=np.zeros(6);x[0]=h;pose_deriv=(f(point(0),perturb(Tb,x))-f(point(0),perturb(Tb,-x)))/(2*h)
    check('axial_depth_and_body_translation_analytic_pixel_derivatives',abs(depth_deriv-2.)<1e-6 and abs(pose_deriv+20.)<1e-6,depth_px_per_mm=depth_deriv,tx_px_per_mm=pose_deriv)
    X=point(0);p=vis.project_camera(X,K,Ta)[0];q=vis.project_camera(X,K,Tb)[0];e=sampson(fundamental(K,Ta,K,Tb),p,q)
    check('relative_pose_epipolar_sign_and_camera_frame_contract',np.max(e)<1e-10,error_px=e)
    supplementary=[]
    for scene,order in protocol()['B_orders'].items():
        for count in protocol()['B_counts'][scene]:
            dest=R/'local_results/B'/(scene+'_'+str(count));z=np.load(dest/'C3_JACOBIAN_SVD.npz');J=z['J_scaled_balanced'];r=z['residual_at_zero'];names=z['parameter_names'].tolist()
            ref=next(a for a in load(R/'metrics/B_SVD_RESULTS.json')if a['scene']==scene and a['views']==count and a['constraint']=='C3');lens=ref['residual_counts'];offset={};start=0
            for k,n in lens.items():offset[k]=np.arange(start,start+n);start+=n
            for mode,parts in [('IMAGE_ONLY',['epipolar','reprojection']),('NO_SILHOUETTE_DEPTH',['epipolar','reprojection','depth']),('NO_SILHOUETTE_DEPTH_RING',['epipolar','reprojection','depth','ring']),('RING_ONLY',['ring'])]:
                idx=np.concatenate([offset[k]for k in parts]);sp,_,_=spectrum(J[idx],names,True);supplementary.append(dict(scene=scene,views=count,mode=mode,residual_counts={k:lens[k]for k in parts},**sp))
            # Exact zero depth columns in pure Ring rows; no hidden HERO dependence in Ring.
            ring_depth_max=float(abs(J[offset['ring'],6*(count-1):]).max());check(scene+f'_{count}_ring_independent_of_HERO_bias',ring_depth_max==0,max_derivative=ring_depth_max)
    # Retain outputs without silhouettes so proxy contour assumptions cannot silently certify rank.
    save('metrics/SUPPLEMENTARY_WITHOUT_SILHOUETTE.json',supplementary)
    save('provenance/SUPPLEMENTARY_SCOPE.json',dict(reason='C1/C3 can be full rank even with zero HERO-backed RGB correspondences in two-view data; remove heuristic silhouette block in an additive diagnostic, without altering preregistered results',original_protocol_unchanged=True,parameter_search=False,code=asset(Path(__file__))))
    for a in load(R/'provenance/INPUT_MANIFEST.json'):check('input_unchanged:'+a['path'],sha(a['path'])==a['sha256'])
    save('metrics/VALIDATION_TESTS.json',dict(passed=all(t['passed']for t in tests),tests=tests));print('VALIDATION',len(tests),'passed',sum(t['passed']for t in tests),flush=True)
    assert all(t['passed']for t in tests)
if __name__=='__main__':main()
