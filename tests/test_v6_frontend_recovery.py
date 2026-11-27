import unittest
import numpy as np
from ring_first_3d.v6_raw import frontend_policy as f

class FrontendTests(unittest.TestCase):
 def views(self):
  return [dict(view_id=f'v{i}',physical_view_id=f'p{i}',media_type='video',raw_frame=i*10,video_id='video',original_index=i) for i in range(6)]
 def test_anchor_component_not_largest_or_new_anchor(self):
  v=self.views();self.assertEqual(f.anchor_component(6,[(0,1),(2,3),(3,4),(4,5)],0),[0,1])
 def test_temporal_edges_do_not_bridge_removed_frame(self):
  v=self.views();self.assertEqual(f.temporal_edges(v,[0,1,3,4,5]),[(0,1),(2,3),(3,4)])
 def test_photos_have_no_temporal_edges(self):
  v=self.views();v.append(dict(view_id='photo',physical_view_id='photo',media_type='photo',raw_frame=None,photo_id='001'))
  self.assertEqual(f.temporal_edges(v,[0,1,6]),[(0,1)])
 def test_diagnostic_and_physical_duplicates_not_support(self):
  v=self.views();v[4]['physical_view_id']='p3'
  self.assertEqual(f.unique_eligible(v,[0,1,2,3,4,5],2),[0,1,3,5])
 def test_three_numeric_qualifications_not_recovery(self):
  self.assertEqual(f.select_plan_version({0:{'budget':0},1:{'budget':0}},0),0)
 def test_existing_legal_plan_retained(self):
  self.assertEqual(f.select_plan_version({0:{'budget':1},1:{'budget':20}},0),0)
 def test_zero_plan_can_fall_back(self):
  self.assertEqual(f.select_plan_version({0:{'budget':0},1:{'budget':2}},0),1)
 def test_none_is_not_evaluable_not_zero(self):
  self.assertFalse(f.finite_le(None,3));self.assertFalse(f.finite_le(np.nan,3));self.assertTrue(f.finite_le(3,3))
 def test_region_scale_empty_q_retains_evidence_nonempty_unchanged(self):
  self.assertGreater(f.region_scale(0,512),0);self.assertEqual(f.region_scale(20,100),np.sqrt(20/100))
 def test_static_view_has_explicit_nonvideo_identity(self):
  self.assertEqual(f.view_tag(dict(media_type='photo',photo_id='abc',raw_frame=None)),'photo_abc')
 def test_video_and_photo_pairing_no_offset_synthetic_time(self):
  v=self.views()+[dict(media_type='photo',photo_id='001'),dict(media_type='photo',photo_id='002')]
  self.assertEqual(f.match_partners(0,v,[1,2,4]),[1,2,4,6,7]);self.assertEqual(f.match_partners(6,v,[1,2,4]),[7])
 def test_contact_ring_is_real_observation(self):
  from ring_first_3d.v6_raw.frontend_kernels import corrected_observation
  labels=np.ones((360,640),np.uint8);labels[150:170,300:340]=2
  ob,diagnostic=corrected_observation(labels,{'ring_train':np.empty((0,2)),'ring_heldout':np.empty((0,2))})
  self.assertGreater(len(ob['ring_train']),0);self.assertGreater(len(ob['ring_heldout']),0)
  a=set(map(tuple,ob['ring_train']));b=set(map(tuple,ob['ring_heldout']));self.assertFalse(a&b)
  self.assertEqual(diagnostic['excluded_for_polyp_adjacency'],0)
 def test_candidate_binding_moves_its_own_center_to_legacy_slot(self):
  original={'primary':0,'coverage':[{'version':0,'P_estimate_mm':[0,0,0]},{'version':1,'P_estimate_mm':[10,20,30]}]}
  bound=f.bind_validation(original,1)
  self.assertEqual(bound['coverage'][0]['P_estimate_mm'],[10,20,30]);self.assertEqual(bound['primary'],1);self.assertEqual(original['primary'],0)
 def test_actual_module_inventory_accepts_kernel_namespace_dict(self):
  from pathlib import Path
  from types import SimpleNamespace
  from ring_first_3d.v6_raw.frontend import record_kernels
  saved=[];r=SimpleNamespace(save=lambda p,x:saved.append(x),head=lambda:'test',FULL_CONFIG={'frontend':{}},sha=lambda p:'hash')
  record_kernels(r,Path('/not_written'),{'ns':{}})
  self.assertTrue(saved)
 def test_absent_diagnostic_lookup_preserves_minus_one(self):
  import ast
  from ring_first_3d.v6_raw.frontend_kernels import Tags
  tree=Tags().visit(ast.parse("held=next(i for i,a in enumerate(L) if i==_M2F9_HELDOUT_INDEX)"));ast.fix_missing_locations(tree)
  ns={'L':[1,2],'_M2F9_HELDOUT_INDEX':-1};exec(compile(tree,'test','exec'),ns);self.assertEqual(ns['held'],-1)
 def test_absent_diagnostic_never_indexes_last_view(self):
  import ast
  from ring_first_3d.v6_raw.frontend_kernels import package_transform
  tree=package_transform(ast.parse("ts=np.flatnonzero(tr['held'] & np.isfinite(tr['xy'][:,held,0]))\nr=dict(heldout_frame=L[held]['id'])"));ast.fix_missing_locations(tree)
  ns={'np':np,'held':-1};exec(compile(tree,'test','exec'),ns)
  self.assertEqual(len(ns['ts']),0);self.assertIsNone(ns['r']['heldout_frame'])
 def test_photo_extension_preserves_old_tracks_and_rejects_ambiguous_merge(self):
  old=np.array([[[1.,1.],[2,2]],[[3,3],[4,4]]]);mix=np.array([[[1.,1.],[2,2],[5,5]],[[3,3],[4,4],[6,6]]])
  xy,cat,held,mapping,diagnostic=f.extend_video_tracks(old,[0,1],[True,False],mix,[0,1])
  np.testing.assert_equal(xy[:,:2],old);np.testing.assert_equal(held,[True,False]);self.assertEqual(mapping,{0:0,1:1})
  mix[0,1]=[4,4]
  xy,cat,held,mapping,diagnostic=f.extend_video_tracks(old,[0,1],[True,False],mix,[0,1])
  np.testing.assert_equal(xy[:,:2],old);self.assertTrue(np.isnan(xy[0,2]).all());self.assertEqual(diagnostic['ambiguous_old_track_merges'],1)
 def test_duplicate_sift_coordinates_never_overwrite_held_identity(self):
  old=np.array([[[1.,1.],[2,2]],[[1.,1.],[2,2]]]);mix=np.array([[[1.,1.],[2,2],[5,5]]])
  xy,cat,held,mapping,diagnostic=f.extend_video_tracks(old,[0,0],[True,False],mix,[0])
  self.assertEqual(mapping,{});self.assertTrue(np.isnan(xy[:,2]).all());np.testing.assert_equal(held,[True,False]);self.assertEqual(diagnostic['ambiguous_old_track_merges'],1)
 def test_unapproved_full_run_stops_before_creating_output(self):
  import tempfile,json
  from pathlib import Path
  from ring_first_3d.v6_raw.full_run import run
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);config=p/'config.json';config.write_text(json.dumps({'approval_required':True,'run_root':str(p/'not_started')}))
   with self.assertRaisesRegex(RuntimeError,'PILOT_REVIEW_REQUIRED'):run(config)
   self.assertFalse((p/'not_started').exists())
if __name__=='__main__':unittest.main()
