import unittest,tempfile
from pathlib import Path
import numpy as np
from ring_first_3d.v6_raw import stage_cache as c

class CacheTests(unittest.TestCase):
 def test_miss_hit_and_corrupt_rebuild(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'entry';calls=[]
   def build(root):
    calls.append(1);np.savez_compressed(root/'a.npz',x=np.array([1.,np.nan]));return {'views':['a']}
   first=c.ensure(p,{'science':1},build);second=c.ensure(p,{'science':1},build)
   self.assertEqual(first['content_id'],second['content_id']);self.assertEqual(len(calls),1)
   (p/'a.npz').write_bytes(b'broken');third=c.ensure(p,{'science':1},build)
   self.assertEqual(len(calls),2);self.assertEqual(first['content_id'],third['content_id'])
   self.assertTrue(list(p.parent.glob('entry.CORRUPT.*')))
 def test_stale_identity_rebuilds(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'e';calls=[]
   def build(q):calls.append(1);(q/'a.json').write_text('{"x":1}');return {}
   c.ensure(p,{'science':1},build);c.ensure(p,{'science':2},build)
   self.assertEqual(len(calls),2)
 def test_npz_container_does_not_define_content(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);a=np.array([[1.,np.nan]],dtype=np.float64)
   np.savez(p/'a.npz',xy=a,held=np.array([True]));np.savez_compressed(p/'b.npz',held=np.array([True]),xy=a)
   self.assertEqual(c.content_identity(p/'a.npz'),c.content_identity(p/'b.npz'))
   np.savez(p/'b.npz',xy=a.astype(np.float32),held=np.array([True]))
   self.assertNotEqual(c.content_identity(p/'a.npz'),c.content_identity(p/'b.npz'))
 def test_incomplete_directory_is_not_hit(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'e';p.mkdir();(p/'partial').write_text('x');calls=[]
   def build(q):calls.append(1);(q/'ok').write_text('done');return {}
   c.ensure(p,{},build);self.assertEqual(len(calls),1);self.assertTrue((p/'COMPLETE.json').exists())

class CacheIdentityTests(unittest.TestCase):
 def test_provenance_and_storage_location_do_not_change_science(self):
  import json
  with tempfile.TemporaryDirectory() as d:
   def build(root):
    (root/'data.json').write_text('{"x":1}');(root/'PROVENANCE.json').write_text(json.dumps({'path':str(root)}));return {}
   a=c.ensure(Path(d)/'a',{'s':1},build);b=c.ensure(Path(d)/'b',{'s':1},build)
   self.assertEqual(a['content_id'],b['content_id'])
 def test_json_materialization_does_not_share_writes(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'source.json').write_text('{}');c.link_or_copy(p/'source.json',p/'target.json');(p/'target.json').write_text('{"x":1}')
   self.assertEqual((p/'source.json').read_text(),'{}')
 def test_tampered_receipt_is_not_cache_hit(self):
  import json
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'e';calls=[]
   def build(root):calls.append(1);(root/'x').write_text('x');return {}
   c.ensure(p,{},build);a=json.loads((p/'COMPLETE.json').read_text());a['content_id']='fake';(p/'COMPLETE.json').write_text(json.dumps(a));c.ensure(p,{},build)
   self.assertEqual(len(calls),2)

if __name__=='__main__':unittest.main()
