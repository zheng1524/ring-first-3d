"""Numerical source/geometry contracts before fitting and fairness after fitting."""
from fitting import *
def main():
    checks=[]
    def ck(name,p,**extra):checks.append(dict(name=name,passed=bool(p),**extra))
    guard('prepare');ss=load(R/'config/SOURCE_BINDING.json');dd=load(R/'provenance/DXY_GENERATED.json')
    for s in ss:
        a=source(s['source_id']);ck(s['source_id']+':mask_sha',hashlib.sha256(a['labels'].tobytes()).hexdigest()==s['Mask_content_SHA']);ck(s['source_id']+':rgb_sha',hashlib.sha256(a['RGB'].tobytes()).hexdigest()==s['RGB_content_SHA']);ck(s['source_id']+':K_halfpixel',np.allclose(np.array(s['native_to_cache'])@np.array(s['K_native']),a['K'],rtol=0,atol=1e-10))
    forbidden=['D_frame_mm','scale_mm_per_px','L_mid_px','D_mid_mm']
    text=json.dumps(dd);ck('DXY_no_mm_result_export',not any(k in text for k in forbidden));ck('DXY_75_current_calls',len(dd)==75 and len({x['source'] for x in dd})==75)
    selected=[x for x in dd if x['available']]
    for d in selected:
        B=np.array(d['basis_px']);c=np.array(d['center_px']);theta=np.arange(97)*2*np.pi/97;q=np.c_[np.cos(theta),np.sin(theta)];boundary=c+q@B.T
        coords=(boundary-c)@np.linalg.inv(B).T
        ck(d['source']+':DXY_basis_roundtrip',np.max(abs((coords*coords).sum(1)-1))<1e-10)
    p=np.r_[0.,0.,-2.,.1,-.05,.03,np.log([5.,4.,3.])];R0=np.eye(3);s=source(ss[0]['source_id']);uv,M,axes,curve=ellipse_projection(p,R0,s['K'],s['T']);ck('analytic_projected_curve_zero',np.max(abs(signed_distance(curve,uv,M,axes)))<1e-8)
    V,F=mesh(p,R0);analytic=first_depth(p,R0,camera_rays(curve*.99+uv*.01,s['K'],s['T']));numeric=cast(mesh_scene(V,F),curve*.99+uv*.01,s['K'],s['T'])[0];both=np.isfinite(analytic)&np.isfinite(numeric);ck('analytic_mesh_depth_contract',both.mean()>.9 and np.max(abs(analytic[both]-numeric[both]))<.15,error_mm=stats(analytic[both]-numeric[both]))
    # Eligibility must exclude a lower-cost solver failure.
    class Dummy:pass
    dummy=Dummy();dummy.R0=np.eye(3);dummy.lo=np.r_[np.full(3,-10),np.full(3,-.8),np.log([.25]*3)];dummy.hi=np.r_[np.full(3,10),np.full(3,.8),np.log([15]*3)];dummy.cameras=[dict(K=s['K'],T=s['T'])]
    failed=dict(p=p,objective=0.,optimizer_success=False);ok,why=qualified(dummy,failed);ck('failed_start_never_eligible',not ok and 'OPTIMIZER_NOT_CONVERGED' in why)
    for name,sc in load(R/'config/BODY_FIT_VIEWS.json').items():
        ck(name+':fit_holdout_disjoint',not (set(sc['FIT'])&set(sc['HOLDOUT'])))
        ck(name+':single_video_only',all(next(s for s in ss if s['source_id']==c)['video']==sc['video'] for c in sc['FIT']))
        if not sc['FIT']:continue
        a=Problem(name,'E2');ck(name+':E2_every_polyp_pixel',all(np.array_equal(t['mask'],source(c)['labels']==1) for c,t in zip(a.ids,a.targets)))
        if sc['E1_available']:
            b=Problem(name,'E1');ck(name+':E1_E2_same_setup',np.array_equal(a.R0,b.R0) and np.array_equal(a.base,b.base) and a.ids==b.ids and np.array_equal(a.weights,b.weights) and np.array_equal(a.lo,b.lo) and np.array_equal(a.hi,b.hi))
    save('metrics/NUMERICAL_CONTRACTS.json',dict(all_pass=all(c['passed'] for c in checks),checks=checks));save('provenance/CODE_REUSE_FUNCTIONS.json',REUSE)
    print('CONTRACTS',sum(x['passed'] for x in checks),'/',len(checks),flush=True)
    assert all(x['passed'] for x in checks)
if __name__=='__main__':main()
