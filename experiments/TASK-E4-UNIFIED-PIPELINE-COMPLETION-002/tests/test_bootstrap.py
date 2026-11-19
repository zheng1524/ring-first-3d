from pathlib import Path
import sys,unittest,numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'code'))
import pipeline as p
from bootstrap_references import namespace
from ring_first_3d.mainline.native.io import sha256

class BootstrapContract(unittest.TestCase):
    def setUp(self):
        self.fit=[v for v in p.instance_views('G02','005') if v['meta']['role']=='FIT'];self.ns,self.ordered,self.ref=namespace(p.TASK/'audit/BOOTSTRAP_TEST_SCOPE',self.fit)
    def test_exact_mature_source_copy(self):
        for r in p.read(p.TASK/'audit/MATURE_CALIBRATION_SOURCE_LOCK.json')['files']:self.assertEqual(sha256(r['copy']),r['sha256'])
    def test_only_frozen_FIT_and_fixed_anchor(self):
        self.assertEqual({v['meta']['id'] for v in self.ordered},{v['meta']['id'] for v in self.fit});self.assertEqual(self.ordered[self.ref]['meta']['id'],self.fit[4]['meta']['id']);self.assertTrue(all(v['meta']['role']=='FIT' for v in self.ordered))
    def test_original_calibration_parameters(self):
        self.assertEqual(self.ns['cfg']()['BA_max_nfev'],60);self.assertEqual(self.ns['cfg']()['pose_initializations'],2);self.assertEqual(self.ns['cfg']()['yaw_grid'],72)
    def test_proper_positive_gauge(self):
        C=np.eye(4);C[:3,3]=[1,2,-30];U=self.ns['positive_gauge'](C);self.assertGreater(U[2,3],0);self.assertAlmostEqual(np.linalg.det(U[:3,:3]),1);self.assertAlmostEqual(np.linalg.norm(U[:3,3]),np.linalg.norm(C[:3,3]))
    def test_no_old_camera_in_ledger(self):
        self.assertTrue(all('T' not in r and 'c2w' not in r and 'pose_source' not in r for r in self.ns['ledger']()))
    def test_tracking_namespace_has_Path(self):
        self.assertIs(self.ns['Path'],Path)

if __name__=='__main__':unittest.main()
