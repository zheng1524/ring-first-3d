import copy,sys,unittest,yaml
from pathlib import Path
TD=Path(__file__).resolve().parents[1];sys.path.insert(0,str(TD/'code'))
from ring_first_3d.policy.recovery_contracts import validate,RECOVERY_STAGES,permissions
from ring_first_3d.policy.contracts import PolicyError

class RecoveryPolicyTests(unittest.TestCase):
    def setUp(self):self.t=yaml.safe_load((TD/'TASK.yaml').read_text())
    def check_rejected(self,t):
        with self.assertRaises(PolicyError):validate(t,TD/'TASK.yaml')
    def test_scope_pass(self):self.assertEqual(validate(self.t,TD/'TASK.yaml')['schema'],11)
    def test_G05_rejected(self):self.t['recovery']['cases'].append('G05');self.check_rejected(self.t)
    def test_GT_selection_rejected(self):self.t['recovery']['GT_selects_prediction']=True;self.check_rejected(self.t)
    def test_camera_optimization_rejected(self):self.t['recovery']['camera_optimization']=True;self.check_rejected(self.t)
    def test_HERO_rejected(self):self.t['recovery']['HERO_read']=True;self.check_rejected(self.t)
    def test_Body_retraining_rejected(self):self.t['recovery']['Body_fixed']=False;self.check_rejected(self.t)
    def test_new_candidate_search_rejected(self):self.t['recovery']['max_candidates_per_case']=3;self.check_rejected(self.t)
    def test_iteration12_rejected(self):self.t['recovery']['iteration']=12;self.check_rejected(self.t)
    def test_prediction_precedes_GT(self):
        self.assertLess(RECOVERY_STAGES.index('G1_G03'),RECOVERY_STAGES.index('G2_evaluate'))
    def test_predictor_denies_HOLDOUT_and_GT(self):
        p=permissions(self.t,'G1_G01',TD/'runs/TEST');self.assertFalse(p['allow_GT']);self.assertTrue(p['denied_read_prefixes']);self.assertEqual(len(p['gt_paths']),2)

if __name__=='__main__':unittest.main()
