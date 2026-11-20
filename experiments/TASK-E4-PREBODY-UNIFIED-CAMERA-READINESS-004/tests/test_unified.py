"""Static + contract tests for the unified pre-body entry point."""
import json, re, unittest
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
CFG = json.loads((CODE / 'configs/unified_config.json').read_text())


class TestUnity(unittest.TestCase):
    def test_no_per_case_branching(self):
        src = (CODE / 'code/unified_prebody.py').read_text()
        self.assertEqual(re.findall(r"if\s+group\s*==|elif\s+group\s*==", src), [])

    def test_single_config_no_group_keys(self):
        txt = json.dumps(CFG)
        for g in ('G01', 'G02', 'G03', 'G05', 'G06'):
            self.assertNotIn(g, txt, f'config must not contain per-group key {g}')

    def test_cad_sizes_frozen(self):
        self.assertEqual(CFG['ring_cad']['R_mm'], 5.6)
        self.assertEqual(CFG['ring_cad']['r_mm'], 0.6)
        self.assertEqual(CFG['gates']['ring_mae_px'], 3.0)

    def test_no_body_used_for_optimization(self):
        src = (CODE / 'code/unified_prebody.py').read_text().lower()
        for tok in ['body/camera', 'solve_body', 'optimize_body']:
            self.assertNotIn(tok, src)

    def test_prepare_stage_is_explicitly_blocked(self):
        src = (CODE / 'code/unified_prebody.py').read_text()
        self.assertIn('BLOCKED_RESTRICTED_WEIGHTS', src)


if __name__ == '__main__':
    unittest.main(verbosity=2)
