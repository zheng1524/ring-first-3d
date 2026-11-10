"""Consistency contracts, explicitly not scientific success gates."""
from common import *
import ast
def main():
 while not(R/'provenance/DELIVERED_SOURCE_MANIFEST.json').exists():time.sleep(5)
 checks=[]
 def check(name,ok):checks.append(dict(check=name,passed=bool(ok)));assert ok,name
 v=load(R/'config/VIEWS.json');check('all68_frozen_view_ids',len(v)==68 and sha(R/'config/VIEWS.json')==sha(REPO/'experiments/TASK-E4-RING-POLYP-REGISTRATION-019/config/VIEWS.json'))
 check('68_Ring_evidence_rows',len(load(R/'metrics/RING_VISIBLE_EVIDENCE_COUNTS.json'))==68)
 check('actual_nonzero_curve_gradient_gate',load(R/'metrics/RING_CURVE_PROJECTION_GRADIENT_GATE.json')['all_passed'])
 check('independent_landmark_sets153_980',len(np.load(R/'landmarks/CROSS_004.npz')['X'])==153 and len(np.load(R/'landmarks/INDEPENDENT_005.npz')['X'])==980)
 check('named_landmarks_not_spatial_nearest',len(load(R/'features/CROSS_NAMED_3D_TRACK_PAIRS.json')['matches'])==18)
 r0=np.asarray(load(R/'results/R0.json')['T']);hist=load(R/'config/HISTORICAL_CANDIDATES.json');roma=np.asarray(next(x['T']for x in hist if x['tag']=='HISTORICAL_FULL_RoMa'));check('R0_exact_full_RoMa',np.array_equal(r0,roma)and np.linalg.norm(r0[:3,3])>0)
 for arm in ['R1','R2','R3','R3_MASK_ONLY','R3_INNER_OUTER','R4','NEGATIVE_R3']:
  a=load(R/'results'/(arm+'.json'));H=np.asarray(a['T']);check(arm+'_80_iterations',a['iterations']==len(load(R/'optimization'/arm/'HISTORY.json'))==80);check(arm+'_fixed_scale_proper_SE3',np.allclose(H[:3,:3].T@H[:3,:3],np.eye(3),atol=1e-6)and abs(np.linalg.det(H[:3,:3])-1)<1e-6);check(arm+'_same_full_initialization',np.array_equal(np.asarray(a['seed_T']),np.eye(4)if arm=='NEGATIVE_R3'else r0));check(arm+'_body_contract',a['body_in_loss']==(arm=='R4'))
 f=load(R/'provenance/NO_BODY_PREDICTIONS_FROZEN.json');af=load(R/'provenance/ALL_POSES_FROZEN_BEFORE_EVALUATION.json')
 check('no_body_before_R4_freeze',f['epoch']<af['epoch'])
 check('no_body_pose_hashes_unchanged',all(sha(x['path'])==x['sha256']for x in f['files']))
 check('all_poses_unchanged_after_evaluation',all(sha(x['path'])==x['sha256']for x in af['files']))
 check('protected_features_only_after_freeze',all((R/'features'/s).stat().st_mtime>=af['epoch']for s in ['REVERSE_HOLDOUT_PNP.json','CROSS_HOLDOUT_PNP.json']))
 reg=load(R/'metrics/REGISTRATION_COMPARISON.json');check('same005_denominator_all10_methods',len(reg)==10 and all(x['FIT_N']==52 and x['HOLDOUT_N']==3 for x in reg));check('all550_method_frame_rows',len(load(R/'metrics/ALL005_FRAME_METRICS.json'))==550)
 hh=load(R/'metrics/HERO_INDEPENDENT_AGGREGATE.json');check('predeclared21_HERO_sources_all_methods',len(hh)==10 and all(x['source_count']==21 and x['ordered_cross_source_target_pairs']==208 for x in hh));check('same_HERO_fixed_denominator',len({x['fixed_source_target_observation_denominator']for x in hh})==1)
 check('upstream_and_original_assets_unchanged',load(R/'provenance/FINAL_INTEGRITY.json')['all_unchanged'])
 for p in(R/'code').glob('*.py'):ast.parse(p.read_text())
 check('all_source_parses',True);check('6_actual_core_figures',len(list((R/'figures').glob('Fig*.png')))==6)
 check('all55_target_view_detail_pages',len(list((R/'figures/details').glob('All005_*.png')))==8)
 check('no_declared_GT',not load(R/'config/PROTOCOL.json')['GT'])
 save('metrics/DELIVERY_CONTRACT_CHECKS.json',dict(all_passed=True,checks=checks,scope='engineering/provenance consistency only; NOT scientific pose accuracy',source=asset(Path(__file__))));print('020_CONTRACTS_COMPLETE',len(checks),flush=True)
if __name__=='__main__':main()
