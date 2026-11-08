from common import *
import torch

def main():
 checks=[]
 def test(k,ok,**a):checks.append(dict(test=k,passed=bool(ok),**a))
 for fn in ['PREREGISTRATION.json','AMENDMENT_FREEZE.json','PREDICTIONS_FROZEN_BEFORE_GT.json','SCALE_LOCK_BEFORE_GT.json']:
  data=load(R/'assets_index'/fn);bad=[x['path']for x in data['files']if sha(x['path'])!=x['sha256']];test(fn+'_hashes_unchanged',not bad,bad=bad)
 old=load(R/'assets_index/HISTORY_012_PROTECTION.json');old=old['files']if isinstance(old,dict)and'files'in old else old
 bad=[x['path']for x in old if sha(x['path'])!=x['sha256']];test('012_history_unchanged',not bad,bad=bad)
 cases=load(R/'config/CASE_LOCK.json');test('eleven_independent_source_identities',len(cases)==11 and len({x['physical_specimen']for x in cases})==11)
 for c in cases:
  n=c['name'];p=R/'local_results'/n/'FINAL.pt';t=torch.load(p,map_location='cpu',weights_only=False);z=np.load(R/'local_results'/n/'FINAL.npz');test(n+'_checkpoint_parameters_optimizer_rng_config',all(k in t for k in ['parameters','optimizer','torch_state','cuda_state','numpy_state','config','accepted','attempt'])and np.array_equal(t['parameters'].numpy(),z['parameters'])and np.isfinite(z['V']).all());test(n+'_uniform_frozen_method',t['config']['loss_arm']=='A3'and t['config']['optimizer_arm']=='O3N'and t['config']['total_trust_D']==1.)
 for a in load(R/'metrics/BLENDER_RIGID_ALIGNMENT.json'):test(a['case']+'_'+a['label']+'_proper_fixedscale_SE3',a['scale']==1. and np.linalg.det(np.asarray(a['R']))>.999999 and np.allclose(np.asarray(a['R']).T@np.asarray(a['R']),np.eye(3),atol=1e-8))
 gt=load(R/'metrics/BLENDER_GEOMETRIC_METRICS.json');test('same_evaluator_33_rows_full11_denominator',len(gt)==33 and all(len([x for x in gt if x['case']==c['name']])==3 for c in cases));test('every_scale_already_metric',all(x['applied_scale']==1 for x in load(R/'metrics/RING_SCALE_VALIDATION.json')))
 for i in range(1,5):test('coreFigure'+str(i),len(list((R/'figures').glob('Fig'+str(i)+'_*.png')))==1)
 save('metrics/DELIVERY_VALIDATION.json',dict(passed=all(x['passed']for x in checks),tests=checks,scientific_anatomical_PASS_not_implied=True));print('DELIVERY',len(checks),[x for x in checks if not x['passed']]);assert all(x['passed']for x in checks)
if __name__=='__main__':main()
