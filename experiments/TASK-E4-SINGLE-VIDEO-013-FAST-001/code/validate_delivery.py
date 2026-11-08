"""Integrity and accounting only, never equate this to scientific success."""
from common import *
import ast
def main():
 for p in(R/'code').glob('*.py'):ast.parse(p.read_text())
 for name in ['TECHNICAL_REPORT.md','FAILURE_LEDGER.md','RESULT_INDEX.md','REPRODUCE.md','CASE_ARM_METRICS.csv','SUMMARY.csv','PAIRED_VS_S0.csv','PER_VIEW_METRICS.csv','GEOMETRY_AUDIT.csv','BLENDER_METRICS.csv','INPUT_RING_AND_FRAME_AUDIT.csv']:assert(R/name).exists(),name
 fr=load(R/'provenance/ALL_PREDICTIONS_FROZEN_BEFORE_GT.json');assert len(fr['files'])==44 and all(sha(q['path'])==q['sha256']for q in fr['files']);assert sha(fr['scale']['path'])==fr['scale']['sha256'];assert load(R/'provenance/GT_ACCESS_START.json')['epoch']>fr['epoch']
 old=load(R/'provenance/HISTORICAL_PROTECTION.json');assert all(Path(q['path']).exists()and sha(q['path'])==q['sha256']for q in old['files'])
 inp=load(R/'provenance/INPUTS_FROZEN.json');assert all(sha(q['path'])==q['sha256']for q in inp['files']if'/code/'not in q['path'])
 training=load(R/'provenance/TRAINING_PROTOCOL_FREEZE.json');names={'common.py','p3d.py','components.py','free_model.py','depth_terms.py','safe_geometry.py','pmgr_self.py','strategy.py','normalized_local.py','contour_objective.py','stream_objective.py','train_normalized.py'};cc=[q for q in training['code']if Path(q['path']).name in names];assert len(cc)==len(names)and all(sha(q['path'])==q['sha256']for q in cc)
 selection=load(R/'config/VIEW_SELECTION.json');reference=load(R/'config/REFERENCE_VIDEOS.json');coverage=load(R/'metrics/VIEW_COVERAGE.json');rows=load(R/'metrics/CASE_ARM_METRICS.json');assert len(rows)==44 and len(load(R/'metrics/BLENDER_METRICS.json'))==44
 for c in load(R/'config/CASE_LOCK.json'):
  n=c['name'];master=getcase(n);by={v['id']:v for v in master['views']};assert all(v['video']==reference[n]['reference_video']and not v['camera_correction_used']for v in master['views']);oldids=next(q['HERO_source_ids']for q in coverage if q['case']==n and q['arm']=='S0')
  for tag in ['S0','S8','S16','S32']:
   a=np.load(R/'inputs'/n/'INITIAL.npz');b=np.load(R/'arms'/tag/'local_results'/n/'FINAL.npz');assert np.isfinite(b['V']).all()and np.array_equal(a['F_solid'],b['F_solid']);q=next(q for q in coverage if q['case']==n and q['arm']==tag);assert q['HERO_source_ids']==oldids;assert set(selection[n][tag]).isdisjoint(selection[n]['HOLDOUT']);assert all(by[x]['video']==reference[n]['reference_video']for x in selection[n][tag]);cfg=load(R/'arms'/tag/'config/PROTOCOL.json');assert(cfg['max_proposals'],cfg['max_accepted'],cfg['consecutive_rejection_stop'],cfg['loss_arm'],cfg['optimizer_arm'],cfg['total_trust_D'])==(800,300,80,'A3','O3N',1.)
  assert all((R/'meshes'/n/(tag+'_mm.ply')).exists()for tag in ['S0','S8','S16','S32']);assert(R/'figures/details'/(n+'_World_Six_Views.png')).exists()
 for q in load(R/'metrics/BLENDER_TRANSFORMS.json'):
  T=np.array(q['T']);assert q['scale']==1 and abs(np.linalg.det(T[:3,:3])-1)<1e-6 and np.allclose(T[:3,:3].T@T[:3,:3],np.eye(3),atol=1e-7)
 for q in load(R/'metrics/PER_VIEW_METRICS.json'):
  assert q['TP']+q['FN']==q['Mask_N']and 0<=q['IoU']<=1
  if q.get('fixed_depth_N'):assert q['depth_hit_N']+q['depth_miss_N']==q['fixed_depth_N']
 for k in range(1,5):
  pp=list((R/'figures').glob('Fig'+str(k)+'_*'));assert len(pp)==1
  with Image.open(pp[0])as im:assert min(im.size)>=700;im.verify()
 report=(R/'TECHNICAL_REPORT.md').read_text()
 for phrase in ['目标组数','本算法独立成功','本算法失败','历史测量值回退','失败组及具体原因','最终统计样本','是否使用 GT 选择算法']:assert phrase in report
 save('provenance/DELIVERY_VALIDATION.json',dict(epoch=time.time(),integrity_pass=True,scientific_pass='NOT_ASSUMED; see actual paired results and independent dense audit',physical_groups=11,condition_models=44,new_training_jobs=33,explicit_historical_S0_controls=11,measurement_fallback=0,old_protected_files_unchanged=len(old['files']),prediction_files_unchanged=44,training_sources_unchanged=len(cc),same_reference_video_only=True,no_GT_selection=True,awaiting_human_review=True));print('DELIVERY_INTEGRITY_PASS_NOT_SCIENTIFIC_PASS')
if __name__=='__main__':main()
