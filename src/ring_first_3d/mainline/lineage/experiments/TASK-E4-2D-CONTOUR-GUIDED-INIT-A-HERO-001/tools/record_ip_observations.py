"""Manual-review evidence on exact frozen aligned Meshes, not a morphology repair."""
from pathlib import Path
import json,hashlib,numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
TD=Path.cwd()/'experiments/TASK-E4-2D-CONTOUR-GUIDED-INIT-A-HERO-001';VIS=TD/'visualization';source=json.loads((TD/'inputs/SOURCES.json').read_text());by={r['case']:r for r in source['cases']};metrics=json.loads((VIS/'BODY_SHAPE_METRICS.json').read_text())['rows'];mr={(r['case'],r['arm']):r for r in metrics};fig=plt.figure(figsize=(18,10),layout='constrained')
for row,g in enumerate(['G02','G03']):
 gt=np.load(by[g]['GT']['path']);pred={a:np.load(VIS/'meshes'/(g+'_'+a+'_ALIGNED.npz'))for a in ['A0','A2','A3']};V=np.concatenate([gt['V']]+[p['V']for p in pred.values()]);c=(V.max(0)+V.min(0))/2;r=np.ptp(V,axis=0).max()*.55
 for col,arm in enumerate(['A0','A2','A3','GT']):
  ax=fig.add_subplot(2,4,row*4+col+1,projection='3d');ax.add_collection3d(Poly3DCollection(gt['V'][gt['F']],facecolors=(.5,.5,.5,.3 if arm!='GT'else .8),edgecolors='none'));title=g+' '+arm
  if arm!='GT':
   p=pred[arm];ax.add_collection3d(Poly3DCollection(p['V'][p['F']],facecolors=(.5,.15,.7,.83),edgecolors='none'));m=mr[g,arm];title+='\nstrict IoU NA; conditional %.5f\nCD %.4f / p95 %.4f mm'%(m['conditional_occupancy_IoU'],m['Chamfer_MAE_mm'],m['Chamfer_P95_mm'])
  ax.set(xlim=(c[0]-r,c[0]+r),ylim=(c[1]-r,c[1]+r),zlim=(c[2]-r,c[2]+r),xlabel='X [mm]',ylabel='Y [mm]',zlabel='Z [mm]');ax.set_box_aspect((1,1,1));ax.view_init(15,-65);ax.set_title(title,fontsize=9);ax.tick_params(labelsize=7)
fig.suptitle('Verified Ip negatives | Actual scale1 best_rigid015 aligned copies, gray GT / purple prediction\nG02 remains an incomplete half body; G03 head genuinely overlaps GT head but long stalk remains missing. No morphology-specific patch.',fontsize=12);figpath=VIS/'figures/Fig2_G02_G03_IP_DETAIL.png';fig.savefig(figpath,dpi=125);plt.close(fig)
para='\n## G02/G03实际Mesh专项审阅\n\nG02 的 A3 相对 A2 的条件占据 IoU由 %.6f 提高至 %.6f，Chamfer由 %.6f 降至 %.6f mm，但实际对齐图仍为缺失半体，未恢复完整头部；不能将数值小幅提高认作错误初始化已修复。G02 GT有自交，严格实体IoU仍不可评价。\n\nG03 的预测头部在真正SE(3)评价副本中与GT头部空间重合，长柄仍缺失。A2→A3的Chamfer %.6f→%.6f mm 恶化，而P95 %.6f→%.6f mm下降；不能仅挑一个改善指标宣布恢复。当前固定初值、可见性、基底保护和预算的各自因果贡献未被分离；没有特殊形态补丁或GT选checkpoint。\n\n![Actual aligned Ip failure evidence](visualization/figures/Fig2_G02_G03_IP_DETAIL.png)\n'%(mr['G02','A2']['conditional_occupancy_IoU'],mr['G02','A3']['conditional_occupancy_IoU'],mr['G02','A2']['Chamfer_MAE_mm'],mr['G02','A3']['Chamfer_MAE_mm'],mr['G03','A2']['Chamfer_MAE_mm'],mr['G03','A3']['Chamfer_MAE_mm'],mr['G03','A2']['Chamfer_P95_mm'],mr['G03','A3']['Chamfer_P95_mm'])
p=TD/'TECHNICAL_REPORT.md';assert'## G02/G03实际Mesh专项审阅'not in p.read_text();p.write_text(p.read_text()+para);p=TD/'RESULT_CARD.md';p.write_text(p.read_text()+'\nG02半体初始化与G03长柄缺失均未解决；G03头部已在真实GT刚体评价副本中重合。[专项PNG](visualization/figures/Fig2_G02_G03_IP_DETAIL.png)。\n')
p=VIS/'FAILURE_LEDGER.json';d=json.loads(p.read_text());d['failures'].extend([dict(case='G02',category='scientific_negative',reason='Wrong half-body initialization remains morphologically incomplete despite partial metric improvement',evidence='figures/Fig2_G02_G03_IP_DETAIL.png',cause_status='observed_only'),dict(case='G03',category='scientific_negative',reason='Long stalk missing despite genuine aligned head overlap; MAE/P95 directions disagree',evidence='figures/Fig2_G02_G03_IP_DETAIL.png',cause_status='observed_only')]);p.write_text(json.dumps(d,indent=2)+'\n');digest=hashlib.sha256(p.read_bytes()).hexdigest();reg=TD/'FAILURE_REGISTRY.json';m=json.loads(reg.read_text())
for fact in m['failures']:
 for e in fact['evidence']:
  if isinstance(e,dict)and e['path'].endswith('/visualization/FAILURE_LEDGER.json'):e['sha256']=digest
m['failures'].append(dict(id='CG-IP-MORPH-004',category='scientific_negative',modules=['CG01','CG02'],symptom='G02 remains half body; G03 still lacks stalk although its evaluated head is genuinely GT-aligned',cause='Observed retained whole-Mesh morphology; no unique optimizer/topology/visibility cause established',cause_status='observed_only',repair='Preserve failure; no case-specific morphology or GT-selected checkpoint',regression=['test_no_new_initial_body','FINAL_DELIVERY_VERIFICATION'],evidence=[dict(path=str(figpath.relative_to(Path.cwd())),sha256=hashlib.sha256(figpath.read_bytes()).hexdigest())],rule_status='candidate',review=dict(status='unreviewed')));reg.write_text(json.dumps(m,indent=2,ensure_ascii=False)+'\n');print('Recorded exact frozen Ip morphology evidence')
