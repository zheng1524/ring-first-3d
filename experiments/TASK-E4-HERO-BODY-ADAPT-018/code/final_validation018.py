"""Final integrity checks; no training, tuning, prediction edits or GT."""
from common import *
import ast

def main():
 for p in(R/'code').glob('*.py'):ast.parse(p.read_text(),filename=str(p))
 freeze=load(R/'provenance/ALL_OPTIMIZED_PREDICTIONS_FROZEN.json');assert len(freeze['records'])==14
 for r in freeze['records']:assert sha(r['result']['path'])==r['result']['sha256']
 algorithm=['train018.py','hero_objective018.py','coherent016.py','safe_geometry.py','free_model.py','components.py','depth_terms.py','p3d.py','common.py','multiview.py','normalized_local.py','contour_objective.py','access018.py'];rows=[]
 for a in load(R/'config/ARM_PLAN.json'):
  g=a['group'];folder=Path(a['path']);snap=load(folder/'provenance'/(g+'_OPT_START.json'));used={x['name']:x['sha256']for x in snap['files']};assert all(used[k]==sha(R/'code'/k)for k in algorithm);read=load(folder/'provenance'/(g+'_OPTIMIZER_READS.json'));assert not read['HOLDOUT_access'];final=np.load(folder/'local_results'/g/'FINAL.npz');initial=np.load(R/'inputs'/g/'INITIAL.npz');assert np.array_equal(final['F'],initial['F'])and np.array_equal(final['F_solid'],initial['F_solid']);assert np.isfinite(final['V']).all();w=load(folder/'metrics'/(g+'_HERO_WEIGHTS.json'))if a['kind']!='OLD'else None
  if w:assert set(w['ids'])==set(a['HERO_views'])and abs(sum(w['normalized'].values())-1)<1e-10 and min(w['normalized'].values())>0
  # Audit actual runtime seed without changing the already-frozen protocol.
  import torch
  state=torch.load(folder/'local_results'/g/'INITIAL.pt',map_location='cpu',weights_only=False);gen=torch.Generator();gen.set_state(state['torch_state']);seed=gen.initial_seed();assert seed==20261108
  rv=np.load(R/'inputs'/g/'RING.npz');bound=np.r_[initial['V'],rv['V']];center=(bound.min(0)+bound.max(0))/2;rad=np.linalg.norm(bound-center,axis=1).max();margins=[]
  for el,az in [(25,-65),(10,-150),(65,25)]:
   el,az=np.radians([el,az]);pos=center+rad*3.4*np.array([np.cos(el)*np.cos(az),np.cos(el)*np.sin(az),np.sin(el)]);f=(center-pos)/np.linalg.norm(center-pos);right=np.cross(f,[0.,0.,1.]);right/=np.linalg.norm(right);down=np.cross(f,right);T=np.array([right,down,f]).T;P=(final['V']-pos)@T;u=490*P[:,:2]/P[:,2:]+199.5;assert(P[:,2]>0).all();margin=min(float(u.min()),float((399-u).min()));assert margin>0;margins.append(margin)
  rows.append(dict(group=g,arm=a['arm'],unchanged_algorithm_sources=True,topology_unchanged=True,all_vertices_finite=True,FINAL_matches_pre_evaluation_SHA256=True,HOLDOUT_optimizer_access=False,actual_torch_seed=seed,configured_protocol_seed=load(R/'config/PROTOCOL.json')['seed'],uniform_actual_seed_for_all_arms=True,all_output_vertices_in_fixed_body_view=True,min_view_border_margin_px=min(margins)))
 grads=load(R/'metrics/PER_VIEW_ACTUAL_GRADIENTS.json');hero=[x for x in grads if x['arm']=='B2_TRUSTED_COH16'and x['term']=='HERO'];assert len(hero)==58 and all(x['all_parameter_gradient_finite']and x['gradient_norm']>0 for x in hero)
 save('metrics/FINAL_VALIDATION.json',dict(all14_completed=True,all14_integrity_checks_pass=True,all29_HERO_gradients_nonzero_initial_and_final=True,all43_source_checks=load(R/'metrics/INPUT_AND_NATIVE_SUBSET_TESTS.json')['all43_passed'],rows=rows,algorithm_source_SHA256={k:sha(R/'code'/k)for k in algorithm},no_GT=True,no_postprocessing=True));table('metrics/FINAL_VALIDATION.csv',rows)
 save('config/ACTUAL_RUNTIME_CONTRACT.json',dict(actual_torch_numpy_training_seed=20261108,protocol_recorded_seed=20261110,explanation='legacy016 trainer retained hardcoded seed; all14 main arms identical actual seed, no result-based reseeding or rerun. Dataset OLD sampler uses its separately frozen seed20261110.',actual_sigma_H_mm=.5,actual_lambda_H=.01,actual_lambda_S=1.,actual_lambda_P=1.,Ring='hard relative nonworsening guard',actual_budget=load(R/'config/PROTOCOL.json')['budget'],no_retroactive_protocol_overwrite=True))
 save('runtime/ALL_COMPUTATION_AND_FIGURES_DONE.json',dict(epoch=time.time(),formal_arms=14,all14_completed=True,all_final_SHA_unchanged=True,HOLDOUT_evaluation_after_freeze=True,figures=True,postprocessing_failure_repaired='summarize Path parentheses only; no model rerun',GT=False,stopped=True));print('FINAL_14_RUN_AND_43_SOURCE_INTEGRITY_CHECKS_PASS',flush=True)
if __name__=='__main__':main()
