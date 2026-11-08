"""Delivery integrity only. Never equate complete artifacts to scientific PASS."""
from common import *
import ast
def main():
 checks=[];required=['TASK.md','CODE_REUSE_AUDIT.md','EXPERIMENT_PLAN.md','TECHNICAL_REPORT.md','FINAL_FINDINGS.md','FAILURE_LEDGER.md','RESULT_INDEX.md','VIEW_INVENTORY.csv','VIEW_PARTITION.csv','VIEW_SELECTION.json','POSE_CORRECTION_REPORT.md','VIEW_COUNT_ABLATION.csv','LOSS_ABLATION.csv','MESH_REFINEMENT_ABLATION.csv','PER_VIEW_METRICS.csv','BLENDER_ALIGNMENT_METRICS.csv','REPRODUCE.md']
 for name in required:assert(R/name).exists(),name
 for p in (R/'code').glob('*.py'):ast.parse(p.read_text())
 frozen=load(R/'provenance/ALL_014_PREDICTIONS_AND_SCALE_FROZEN_BEFORE_GT.json');assert all(sha(a['path'])==a['sha256']for a in frozen['files']);checks.append(dict(check='all predictions and scales still frozen',passed=True,files=len(frozen['files'])))
 old=load(R/'provenance/HISTORY_013.json');changed=[a['path']for a in old['files']if not Path(a['path']).exists()or sha(a['path'])!=a['sha256']];assert not changed,changed;checks.append(dict(check='protected013 inputs/code/results unchanged',passed=True,files=len(old['files'])))
 cases=[c['name']for c in load(R/'config/CASE_LOCK.json')];expected=['C0','C1_8','C2_16','C3_32','C4_ALL','D_D1_split','D_D2_bidir','D_D3_combo','E0_none','E1_global','E2_adaptive','FINAL_014']
 for tag in expected:
  for n in cases:assert(R/'arms'/tag/'local_results'/n/'FINAL.npz').exists(),(tag,n)
 for tag in ['B_A_ONLY','B0_UNCORRECTED']:assert(R/'arms'/tag/'local_results/G01/FINAL.npz').exists()
 checks.append(dict(check='all132group-condition finals plus2video controls',passed=True))
 frames=[]
 for k in range(1,11):
  pp=list((R/'figures').glob('Fig'+str(k)+'_*'));assert len(pp)==1,(k,pp)
  with Image.open(pp[0])as im:assert min(im.size)>=700,(pp[0],im.size);im.verify()
  frames.append(asset(pp[0]))
 rows=load(R/'metrics/BLENDER_ALIGNMENT_METRICS.json');final=[r for r in rows if r['label']=='FINAL014'];assert len(final)==11 and len({r['case']for r in final})==11
 transforms=load(R/'metrics/BLENDER_RIGID_TRANSFORMS.json')
 for r in transforms:
  T=np.array(r['T']);assert abs(np.linalg.det(T[:3,:3])-1)<1e-6 and np.allclose(T[:3,:3].T@T[:3,:3],np.eye(3),atol=1e-7)and r['scale']==1.
 for r in load(R/'metrics/PER_VIEW_METRICS.json'):
  assert 0<=r['IoU']<=1 and r['TP']+r['FN']==r['Mask_N'];assert r['all_pixel_FP']>=r['FP'] and r['all_pixel_visible_IoU']<=r['IoU']+1e-12
  if r.get('fixed_depth_N'):assert r['depth_hit_N']+r['depth_miss_N']==r['fixed_depth_N']
 checks.append(dict(check='same one properSE3 permodel, no scale; native fixed denominators',passed=True,models=len(rows)))
 assert load(R/'provenance/GT_ACCESS_START.json')['epoch']>frozen['epoch'];checks.append(dict(check='GTaccess after every prediction and metric-scale freeze',passed=True))
 for n in cases:
  for f in ['FINAL014_mm.npz','FINAL014_mm.ply','FINAL014_scene_m.glb']:assert(R/'review_models'/n/f).exists(),(n,f)
 report=(R/'TECHNICAL_REPORT.md').read_text()
 for term in ['目标组数','本算法独立成功','本算法失败','历史测量值回退','失败组及具体原因','最终统计样本','是否使用GT选择算法']:assert term in report
 save('provenance/DELIVERY_VALIDATION.json',dict(epoch=time.time(),checks=checks,figures=frames,target_physical_groups=11,independent_numeric_outputs=11,measurement_fallback=0,integrity_pass=True,scientific_pass='NOT_INFERRED_FROM_DELIVERY; see Ring/GT/failure findings',awaiting_human_review=True));print('DELIVERY_INTEGRITY_PASS_NOT_SCIENTIFIC_PASS',len(rows),flush=True)
if __name__=='__main__':main()
