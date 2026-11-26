import tempfile,unittest,os
from pathlib import Path
from audit import identity,sha,save
from protected_delete import validate,unlink_leaf,open_inodes,verify_static
from unittest.mock import patch
class ProtectionTests(unittest.TestCase):
 def setUp(self):self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.p=self.root/'cache.npz';self.p.write_bytes(b'x'*8192)
 def tearDown(self):self.temp.cleanup()
 def row(self,p=None):
  p=p or self.p;return dict(identity(p),root=str(self.root),sha256=sha(p))
 def test_protected_prefix(self):
  with self.assertRaises(ValueError):validate(self.row(),[str(self.root)],{str(self.root)},set())
 def test_identity_drift(self):
  r=self.row();self.p.write_bytes(b'y'*8192)
  with self.assertRaises(ValueError):validate(r,[str(self.root)],set(),set())
 def test_symlink(self):
  q=self.root/'link.npz';q.symlink_to(self.p);r=self.row();r['path']=str(q)
  with self.assertRaises(ValueError):validate(r,[str(self.root)],set(),set())
 def test_open_inode(self):
  r=self.row()
  with self.assertRaises(ValueError):validate(r,[str(self.root)],set(),{(r['device'],r['inode'])})
 def test_outside_allowlist(self):
  with self.assertRaises(ValueError):validate(self.row(),[],set(),set())
 def test_hardlink_only_last_counts(self):
  q=self.root/'copy.npz';os.link(self.p,q);a,b=self.row(),self.row(q)
  first=unlink_leaf(a,[str(self.root)],set(),set());last=unlink_leaf(b,[str(self.root)],set(),set())
  self.assertEqual(first['reclaimed_allocated_bytes'],0);self.assertEqual(last['reclaimed_allocated_bytes'],a['blocks']);self.assertFalse(q.exists())
 def test_protected_sibling_does_not_block_safe_leaf(self):
  q=self.root/'keep';q.mkdir();self.assertEqual(validate(self.row(),[str(self.root)],{str(q)},set()),self.p)
 def test_mmap_survives_closed_fd(self):
  proc=self.root/'proc';task=proc/'123';(task/'fd').mkdir(parents=True);s=self.p.stat()
  (task/'maps').write_text(f'0000-1000 r--p 0 {os.major(s.st_dev):02x}:{os.minor(s.st_dev):02x} {s.st_ino} {self.p}\n')
  self.assertIn((s.st_dev,s.st_ino),open_inodes(proc))
 def test_identical_atomic_protocol_only(self):
  r=self.row();r['allow_identical_atomic_rewrite']=True;save(self.root/'STATIC_BEFORE.json',dict(files=[r]))
  q=self.root/'new';q.write_bytes(self.p.read_bytes());q.replace(self.p)
  with patch('protected_delete.O',self.root):
   self.assertEqual(verify_static(),1)
   self.p.write_bytes(b'z'*8192)
   with self.assertRaises(ValueError):verify_static()
if __name__=='__main__':unittest.main()
