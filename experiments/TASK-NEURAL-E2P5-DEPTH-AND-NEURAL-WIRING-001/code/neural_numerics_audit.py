"""Explain observed empty-field gradients using saved actual-network SDF traces."""
from common import *
import torch

def main():
    rows=[]
    for r in csv.DictReader((R/'metrics/NEURAL_INITIALIZATION_AND_HITS.csv').open()):
        z=np.load(R/f'local_results/neural/{r["scene"]}_{r["candidate"]}_{r["source"]}.npz');sdf=torch.tensor(z['trace_raw_SDF_mm'],dtype=torch.float64)
        beta=float(r['beta_mm']);official=opacity.official_density_func(None,sdf,beta=torch.tensor(beta,dtype=torch.float64))
        f=sdf.numpy();reference=np.where(f>=0,.5*np.exp(-np.maximum(f,0)/beta),1-.5*np.exp(np.minimum(f,0)/beta))/beta
        discrepancy=(official.detach().numpy()==0)&(reference>0)
        rows.append(dict(scene=r['scene'],candidate=r['candidate'],source=r['source'],trace_sample_N=len(f),
            positive_tail_sample_N=int((f>0).sum()),official_zero_but_positive_stable_tail_N=int(discrepancy.sum()),
            beta_mm=beta,raw_min_mm=float(f.min()),raw_max_mm=float(f.max()),
            largest_missed_density_per_mm=float(reference[discrepancy].max()) if discrepancy.any() else 0.,
            reason='0.5+0.5*expm1(-f/beta) cancels in positive tail; epsilon-clamped BCE additionally kills opacity gradients',
            evidence='one preselected actual-network ray trace; not a new Sphere test',density_modified_in_main_adapter=False))
    table('metrics/LAPLACE_TAIL_CANCELLATION.csv',rows)
    degen=list(csv.DictReader((R/'metrics/DEGENERACY_TESTS.csv').open()))
    stable=next(x for x in degen if x['scene']=='G01_005' and x['diagnostic_offset_mm']=='0.0')
    sel=list(csv.DictReader((R/'metrics/DEGENERACY_SELECTION_COUNTEREXAMPLE.csv').open()))
    known=[x for x in sel if x['scene']=='G01_004' and x['current_joint_total']]
    assert float(known[-1]['hit_coverage'])<float(known[0]['hit_coverage'])
    assert float(known[-1]['Depth_loss'])<float(known[0]['Depth_loss']) and float(known[-1]['current_joint_total'])<float(known[0]['current_joint_total'])
    assert float(stable['current_Mask_dLoss_dOffset'])==0 and float(stable['stable_Mask_dLoss_dOffset'])>0
    save('metrics/DEGENERACY_EXPLICIT_CONCLUSION.json',dict(current_joint_loss_has_potential_coverage_error_tradeoff=True,
        selection_control=dict(scene='G01_004',candidate='A_LEGACY_INIT_CONTROL',
            baseline_coverage=float(known[0]['hit_coverage']),reduced_coverage=float(known[-1]['hit_coverage']),
            baseline_hit_depth_loss=float(known[0]['Depth_loss']),reduced_hit_depth_loss=float(known[-1]['Depth_loss']),
            baseline_joint_total=float(known[0]['current_joint_total']),reduced_joint_total=float(known[-1]['current_joint_total']),
            caveat='selection-only structural counterexample, not a claimed physically attainable field'),
        actual_neural_empty_field=dict(scene='G01_005',candidate='B_SOURCE_ROI_PHYSICAL',observed_N=18,hit_N=0,
            old_clamped_Mask_offset_gradient=0.,stable_log_Mask_offset_gradient=float(stable['stable_Mask_dLoss_dOffset']),
            caveat='continuous output-offset derivative; not a neural optimizer step or recovered geometry'),
        required_actions=['fixed observed denominator and all source coverage in monitoring','reject missing reference; add partial-coverage floor as a stop rule, never as fake gradient',
            'validate log-optical BCE candidate on actual neural parameter gradients before future adoption','calibrate source-geometric initialization in separately approved bounded CPU gate'],
        not_eliminated_by_current_joint_gate=True,GPU='NOT_AUTHORIZED'))
    print('DEGENERACY_CONFIRMED: coverage1 ->1/3; joint objective falls; no update; original BCE loses recovery gradient')

if __name__=='__main__':main()
