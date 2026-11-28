import copy,unittest,json
from pathlib import Path
import numpy as np
from registration import qualify

def good():
 return dict(M4=dict(bidir=dict(A_to_B=dict(conditional_median=2.,conditional_P95=80.),B_to_A=dict(conditional_median=3.,conditional_P95=12.),denominators=dict(evidence_sufficient=True,two_sided_DLT_tracks=8,target_frames_A=2,target_frames_B=2)),ring=dict(by_side=dict(B=dict(conditional_MAE=2.)))),M0=dict(ring=dict(by_side=dict(B=dict(conditional_MAE=1.)))))
class Qualification(unittest.TestCase):
 def test_tail_does_not_reject(self):
  q=qualify(good(),dict(quality='UNASSESSED',candidate_only=False),True)
  self.assertEqual(q['status'],'PASS_FOR_JOINT');self.assertTrue(q['warnings'])
 def test_missing_is_not_zero(self):
  x=good();x['M4']['bidir']['A_to_B']['conditional_median']=None
  self.assertEqual(qualify(x,{},True)['status'],'INCONCLUSIVE_REGISTRATION')
 def test_wrong_rgb_fails(self):
  x=good();x['M4']['bidir']['B_to_A']['conditional_median']=6.01
  self.assertEqual(qualify(x,{},True)['status'],'FAIL_REGISTRATION')
 def test_insufficient_is_inconclusive(self):
  x=good();x['M4']['bidir']['denominators']['two_sided_DLT_tracks']=7;x['M4']['bidir']['A_to_B']['conditional_median']=100.
  self.assertEqual(qualify(x,{},True)['status'],'INCONCLUSIVE_REGISTRATION')
 def test_candidate_and_ring_conflicts_rejected(self):
  self.assertEqual(qualify(good(),dict(candidate_only=True),True)['status'],'FAIL_REGISTRATION')
  x=good();x['M4']['ring']['by_side']['B']['conditional_MAE']=2.001
  self.assertEqual(qualify(x,{},True)['status'],'FAIL_REGISTRATION')
class FrozenRouting(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  p=Path(__file__).resolve().parents[1]/'evidence/REGISTRATION_QUALIFICATION.json'
  if not p.exists():raise unittest.SkipTest('Full evidence not generated yet')
  cls.records=json.loads(p.read_text())['groups']
 def test_rejected_relationships_never_form_joint(self):
  for g in self.records:
   for component in g['joint_components']:
    nodes=set(component['videos']);seen={component['anchor']}
    while True:
     previous=set(seen)
     for e in g['edges']:
      pair={e['parent'],e['child']}
      if e['status']=='PASS_FOR_JOINT'and pair<=nodes and pair&seen:seen|=pair
     if seen==previous:break
    self.assertEqual(seen,nodes)
 def test_every_single_local_and_four_failures_excluded(self):
  focus=['GP_IIa_22.0mm_closed_R10_single_refY','GP_Is_7.0mm_closed_R5_single_refY','GP_IIa_9.5mm_closed_R5_single_refY','GP_Is_14.0mm_closed_R5_single_refY']
  for g in self.records:
   for r in g['single_routes']:
    self.assertTrue(np.array_equal(r['T_local_to_output'],np.eye(4)))
    self.assertEqual(r['coordinate_frame'],'LOCAL')
   if g['group']in focus:self.assertEqual(g['joint_components'],[])
if __name__=='__main__':unittest.main()
