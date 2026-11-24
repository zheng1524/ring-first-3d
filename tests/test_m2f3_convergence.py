import numpy as np
from ring_first_3d.views.pipeline_adapter import admission_tiers, validate_t13
from tools.m2f2_unified import groups_from_arg

def row(**kw):
 d=dict(pose_valid=True,cad_valid=True,ring_raw_mae=1.,held_n=30,held_median=1.,held_p95=3.,big_error_fraction=.01,positive_depth=1.,rotation_to_previous_deg=2.,center_to_previous_mm=1.,admission_status='ACCEPT');d.update(kw);return d

def test_s0_uses_095_not_099_and_s2_local():
 assert admission_tiers(row(positive_depth=.96),2,'T1_SAMPLING_GAP')[0] is True
 assert admission_tiers(row(positive_depth=.94),2,'T1_SAMPLING_GAP')[0] is False
 # S2 is local: low ring/held evidence but pose/cad/positive and graph support
 s0,s1,s2=admission_tiers(row(ring_raw_mae=8.,held_n=0,held_median=40.,held_p95=100.,positive_depth=.92),1,'T4_UNRESOLVED')
 assert (s0,s1,s2)==(False,False,True)

def test_s2_independent_of_s1_and_rejects_branch():
 assert admission_tiers(row(),1,'T0_CONTINUOUS')[2] is True
 assert admission_tiers(row(),1,'T2_ISOLATED_BRANCH')==(False,False,False)

def test_t13_baseline_zero_rejected():
 C=np.eye(4);target=dict(id='t',C=C);sups=[];cand=[]
 for i,x in enumerate(([3,0,0],[0,3,0],[-3,0,0])):
  P=np.eye(4);P[:3,3]=x;sups.append(dict(id=str(i),C=P));cand.append(dict(id=str(i),geometric_inliers=20,direction_deg=20.,epipolar_px={'median':1.},parallax_deg={'median':4.}))
 assert validate_t13(target,sups,cand)[0] is True
 sups[0]['C']=C.copy();assert validate_t13(target,sups,cand)[0] is False

def test_generic_group_discovery():
 g=groups_from_arg('GP_Ip_20.0mm_closed_R10_single_refY')
 assert g==[('GP_Ip_20.0mm_closed_R10_single_refY','GP_Ip_20.0mm_closed_R10_single_refY')]
