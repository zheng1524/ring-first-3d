import tempfile,unittest
from pathlib import Path
from hero_check import inference_state
class BudgetTests(unittest.TestCase):
 def test_new_case(self):
  with tempfile.TemporaryDirectory()as d:self.assertEqual(inference_state(Path(d)),'NEW')
 def test_interrupted_call_has_spent_budget(self):
  with tempfile.TemporaryDirectory()as d:
   p=Path(d);(p/'INFERENCE_STARTED.json').write_text('{}');self.assertEqual(inference_state(p),'SPENT')
 def test_completed_call_can_only_be_reused(self):
  with tempfile.TemporaryDirectory()as d:
   p=Path(d);(p/'INFERENCE.json').write_text('{}');(p/'HERO_native.npz').write_bytes(b'prediction');self.assertEqual(inference_state(p),'REUSE')
 def test_missing_completed_prediction_is_not_a_new_budget(self):
  with tempfile.TemporaryDirectory()as d:
   p=Path(d);(p/'INFERENCE.json').write_text('{}');self.assertEqual(inference_state(p),'SPENT')
if __name__=='__main__':unittest.main()
