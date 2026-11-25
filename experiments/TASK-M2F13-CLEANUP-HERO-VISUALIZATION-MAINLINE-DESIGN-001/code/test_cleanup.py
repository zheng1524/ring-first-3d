import unittest,tempfile,os
from pathlib import Path
from cleanup_execute import validate,sha
class CleanupBoundary(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.r=Path(self.tmp.name);self.p=self.r/'derived.npz';self.p.write_bytes(b'evidence');s=self.p.stat();self.row=dict(path=str(self.p),root=str(self.r),size=s.st_size,inode=s.st_ino,device=s.st_dev,nlink=s.st_nlink,sha256=sha(self.p))
 def tearDown(self):self.tmp.cleanup()
 def test_valid(self):self.assertEqual(validate(self.row,[str(self.r)],[]),self.p)
 def test_protected(self):
  with self.assertRaises(ValueError):validate(self.row,[str(self.r)],[str(self.p)])
 def test_drift(self):
  self.p.write_bytes(b'new work')
  with self.assertRaises(ValueError):validate(self.row,[str(self.r)],[])
 def test_outside(self):
  with self.assertRaises(ValueError):validate(self.row,[],[])
 def test_symlink(self):
  self.p.unlink();self.p.symlink_to('/etc/hosts')
  with self.assertRaises(ValueError):validate(self.row,[str(self.r)],[])
 def test_hardlink_preserves_other_name(self):
  other=self.r/'kept.npz';os.link(self.p,other);self.row['nlink']=2;validate(self.row,[str(self.r)],[]).unlink();self.assertEqual(other.read_bytes(),b'evidence')
if __name__=='__main__':unittest.main()
