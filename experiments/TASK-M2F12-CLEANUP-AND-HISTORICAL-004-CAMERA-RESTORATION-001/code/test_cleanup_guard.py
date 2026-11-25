import unittest,tempfile,hashlib
from pathlib import Path
from cleanup_guard import validate
class GuardTest(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.p=self.root/'mesh.ply';self.p.write_bytes(b'abc');s=self.p.stat();self.row=dict(path=str(self.p),root=str(self.root),sha256=hashlib.sha256(b'abc').hexdigest(),size=3,inode=s.st_ino)
 def tearDown(self):self.tmp.cleanup()
 def test_valid(self):self.assertEqual(validate(self.row,[str(self.root)],set()),self.p)
 def test_hash_change(self):
  self.p.write_bytes(b'xyz')
  with self.assertRaises(ValueError):validate(self.row,[str(self.root)],set())
 def test_protected(self):
  with self.assertRaises(ValueError):validate(self.row,[str(self.root)],{str(self.p)})
 def test_outside(self):
  with self.assertRaises(ValueError):validate(self.row,[str(self.root/'sub')],set())
 def test_symlink(self):
  p=self.root/'link';p.symlink_to(self.p);self.row['path']=str(p)
  with self.assertRaises(ValueError):validate(self.row,[str(self.root)],set())
if __name__=='__main__':unittest.main()
