"""Charter B0 evidence, not a post-hoc accuracy threshold or GT classifier."""
from common import *

def main():
 A=load(R/'metrics/PHASE_A_ALL_METRICS.json');B=load(R/'metrics/PHASE_B_ALL_METRICS.json');bodies=load(R/'provenance/FROZEN_FINAL_BODIES_FIT_ONLY.json')['bodies'];cases={q['name']:q for q in load(R/'config/CASE_LOCK.json')};rows=[];lines=['# B0_REVIEW','','本轮不把数值输出、Mask IoU或刚性对齐后的全体尺寸等同于B0通过。章程要求Ip具有合理头柄连接与空间延伸，且几何不能有严重自交/薄片/拓扑错误。以下是全部11组的原始证据。判定不使用GT选择预测。','','| 病例 | 冻结路线 | FIT/HOLDOUT IoU | HERO覆盖 | 自交/连通分量 | Ring密集穿透mm | B0证据状态 |','|---|---|---|---|---|---|---|']
 for q in bodies:
  n,t=q['case'],q['arm'];rec=next(v for v in B if v['case']==n and v['arm']==t)if t.startswith('Stalk')else next(v for v in A if v['case']==n and v['arm']==t and v['stage']=='FINAL');g=rec['geometry'];status='REQUIRES_VISUAL_STRUCTURE_AND_STABILITY_REVIEW'
  if g['self_intersections_N']or g['components']!=1 or g['degenerate_faces_N']:status='GEOMETRY_FAILURE'
  elif not g['dense_nonworsening_vs_common013']:status='ADDED_RING_PENETRATION_FLAG_REQUIRES_REVIEW'
  elif cases[n]['morphology']=='Ip':status='STALK_SPATIAL_SKELETON_REQUIRES_VERIFICATION'
  row=dict(case=n,arm=t,morphology=cases[n]['morphology'],status=status,FIT_IoU=rec['FIT']['IoU'],HOLDOUT_IoU=rec['HOLDOUT']['IoU'],fixed_depth=rec['HERO_FIT'],geometry=g,absolute_measurement_certified=False,GT_used_to_select=False);rows.append(row);rate=rec['HERO_FIT']['hit_rate'];lines.append('|%s|%s|%.4f / %.4f|%s|%s / %s|%.6f|%s|'%(n,t,row['FIT_IoU'],row['HOLDOUT_IoU'],'NOT_EVALUABLE'if rate is None else'%.4f'%rate,g['self_intersections_N'],g['components'],g['dense_Ring_penetration_mm'],status))
 lines+=['','**全11组B0：尚未证明通过（NOT_CONFIRMED）**。这是保守的证据判断，不代表整条路线科学失败。Ip的中心线种子是轮廓代理，不能自动当作真实柄部；需要结合保存的三维和留出轮廓检查。非Ip若形态、尺寸与初始化稳定性已足够，不继续增加局部更新复杂度。可提出单视频HERO—主体适配候选，但本轮不自动执行。','','数值细节、三种方法全部失败与成功输出均保留。对已有微小CAD接触与新增穿透分开解释；一个密集采样标记不能自动冒充严重物理错误真值。真实坐标的绝对GT误差缺独立标定，ICP后指标只能描述形状。人工审阅后可对具体组确认B0，不用再无限延长主体优化。']
 save('metrics/B0_EVIDENCE.json',rows);table('metrics/B0_EVIDENCE.csv',rows);(R/'B0_REVIEW.md').write_text('\n'.join(lines)+'\n');print('B0_EVIDENCE_WRITTEN',len(rows),flush=True)
if __name__=='__main__':main()
