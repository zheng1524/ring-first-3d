"""Acceptance checks and fixed-observation metrics, without modifying fits."""
from run import *
def main():
    checks=[]
    def ck(name,passed,**extra):checks.append(dict(name=name,passed=bool(passed),**extra))
    rr=load(R/'metrics/S2_PRIMARY.json');allr=load(R/'metrics/S2_ALL_STARTS.json');fixed=[]
    ck('60_fits_20_models_fixed_budget',len(allr)==60 and len(rr)==20)
    ck('S1_contracts',load(R/'metrics/S1_CONTROLS.json')['all_pass'])
    ck('frozen_scientific_code_inputs_and_original_metadata',load(R/'provenance/FREEZE_INTEGRITY.json')['all_pass'])
    for x in load(R/'provenance/INPUT_MANIFEST.json'):ck('source_SHA_'+Path(x['path']).name,sha(x['path'])==x['sha256'])
    for m in allr:
        sc=protocol()['scenes'][m['scene']];ck(key(m['scene'],m['arm'])+'_A_ONLY_'+str(m['start']),m['source_ids']==sc['A']and not set(m['source_ids'])&set(sc['B']))
        ck(key(m['scene'],m['arm'])+'_finite_'+str(m['start']),np.isfinite(m['p']).all()and np.isfinite(m['objective'])and m['nfev']<=60)
    for m in rr:
        candidates=[x for x in allr if(x['scene'],x['arm'])==(m['scene'],m['arm'])];ck(key(m['scene'],m['arm'])+'_A_OBJECTIVE_SELECTION',m['objective']==min(x['objective']for x in candidates))
        P,F=mesh(np.array(m['p']),np.array(m['R0']),m['family'],True);export=trimesh.load(R/'local_results'/(key(m['scene'],m['arm'])+'.ply'),process=False);ck(key(m['scene'],m['arm'])+'_actual_export_identity',np.array_equal(F,export.faces)and np.max(abs(P-export.vertices))<2e-6)
        for cid in protocol()['scenes'][m['scene']]['B']:
            z=np.load(R/'local_results'/(key(m['scene'],m['arm'])+'__'+cid+'.npz'));o=observation(cid);pred=z['predicted_mask'];obs=o['head'];N=int(obs.sum());fp=int((pred&~obs).sum());fn=int((obs&~pred).sum());hit=int((pred&obs).sum());q=contour(obs);b=contour(pred);dist=cKDTree(b).query(q)[0]if len(b)else np.full(len(q),np.nan)
            ck(key(m['scene'],m['arm'])+'_fixed_mask_denominator',N==m['B_metrics'][0]['head_denominator']and hit+fn==N and pred.shape==(360,640))
            row=dict(scene=m['scene'],arm=m['arm'],B=cid,head_denominator=N,canvas_denominator=230400,hit_N=hit,miss_N=fn,outside_N=fp,hit_per_fixed_head=hit/N,miss_per_fixed_head=fn/N,outside_per_fixed_head=fp/N,outside_per_fixed_canvas=fp/230400,source_contour_fixed_N=len(q),source_to_prediction_boundary_px=stats(dist),legacy_outside_per_prediction_N=m['B_metrics'][0]['outside_fraction'],note='Legacy precision-style FP/predN preserved; formal fixed-observation reporting adds FP/headN and FP/230400. No threshold, parameters, selection or historical results changed.')
            fixed.append(row)
    # H identity and fixed input budgets.
    for scene,sc in protocol()['scenes'].items():
        for cid in sc['A']+sc['B']:
            o=observation(cid);original_=original(cid);ck(cid+'_H_original_vertex_IDs',np.array_equal(o['HERO_X_mm'],original_['P'][o['HERO_original_vertex_id']]))
            ck(cid+'_fixed_input_budget',len(o['depth_native_uv'])==32 and len(o['pairs'])==16 and len(o['HERO_X_mm'])==96)
    # Stable soft_l1 mapping, including infinitesimal gradient regime.
    x=np.array([1e-12,1e-8,.1,1,10.]);g=robustify(x);ck('soft_l1_stable_small_residual',np.allclose(g[:2]/x[:2],1,atol=1e-12)and np.allclose(g[2:]**2,2*(np.sqrt(1+x[2:]**2)-1)))
    table('metrics/FIXED_OBSERVATION_B_METRICS.csv',fixed);save('metrics/FIXED_OBSERVATION_B_METRICS.json',fixed)
    # Add explicit fixed denominator columns to complete all-start CSV as well.
    with (R/'04_ABLATION_METRICS.csv').open()as f:rows=list(csv.DictReader(f))
    for row in rows:
        candidates=[x for x in allr if x['scene']==row['scene']and x['arm']==row['arm']and str(x['start'])==str(row.get('start',''))]
        if candidates:
            b=candidates[0]['B_metrics'][0];row['B_outside_per_fixed_head']=b['outside_N']/b['head_denominator'];row['B_outside_per_fixed_canvas']=b['outside_N']/230400;row['B_outside_legacy_denominator']='predicted_N'
        else:row['B_outside_per_fixed_head']='NaN';row['B_outside_per_fixed_canvas']='NaN'
    table('04_ABLATION_METRICS.csv',rows)
    save('metrics/VALIDATION.json',dict(all_pass=all(x['passed']for x in checks),engineering_checks=checks,scientific_gate='G1_NOT_PASSED; engineering test PASS does not confer scientific qualification',formal_prediction_success=False))
    print('VALIDATION',len(checks),'checks',sum(x['passed']for x in checks),'passed',flush=True)
    assert all(x['passed']for x in checks)
if __name__=='__main__':main()
