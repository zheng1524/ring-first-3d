"""Bounded post-evaluation interpretation, no prediction changes or GT selection."""
from common import *
import ast
MARK='\n## 实际追踪补充与统计口径\n'
def main():
 pairs=load(R/'metrics/SAMPLING_PAIRED_COMPARISON.json');total=sum(x['old_Chamfer_mm']-x['new_Chamfer_mm']for x in pairs);g=next(x for x in pairs if x['case']=='G03');contribution=(g['old_Chamfer_mm']-g['new_Chamfer_mm'])/total;full=load(R/'arms/DIAGNOSTIC/metrics/G03_OLD_A_REJECTED_FULL_OBJECTIVE_ACTUAL_TRACE.json');stats_=load(R/'metrics/GT_ROUTE_SUMMARIES.json')
 text='''
## 实际追踪补充与统计口径

采样方案平均Chamfer下降的约 %.1f%% 来自G03；其余10例合计略升。这是全11组配对分解，不删除G03或其他失败组，也不宣称均衡选帧普遍提高三维精度。S1的Dxy MAE略升、其中位相对误差略降，同样属于MIXED。

复核真实的G03 `REJECTED_FULL_FIT_OBJECTIVE`：候选通过几何检查，但完整目标增加 %.9f。加权silhouette增加约 %.9f，而prior仅增加约 %.3g；这个拒绝样例不能归咎于形状先验过强。实际attempt/ramp、加权与原始分量均保存；不把未加系数的parts直接相加。G03旧B及新方案关键快照的重算梯度与记录梯度相对差约1e-7，完整因果链可在固定实际状态复核。

G03共享起点的HERO缓存为256条，其中28条未命中或被CAD截断，对相应深度分支梯度严格为零；旧B最终18条、新方案17条仍未命中，且两者各有5条已命中观测处于鲁棒饱和。扩展候选覆盖不能自动给缺失表面提供新的可靠深度约束。

独立64阶复核：G03 S1相对共同原起点新增1个采样穿入面；015 S0也有1个。机制对照从已冻结S0 FINAL起步，没有继续增加采样穿入。不能将最大穿入深度基本不变、原32阶Guard通过，概括为完全无碰撞。所有新输出的独立非邻接自交检查为0，仍不能把片状柄称为正确结构。

当前缓存相机中心的数值秩没有被一概判为2；不声称所有视频轨迹共面。`VIEW_DIRECTION_GAPS.json` 提供实际特征值和方向锥。新增方向需求首先是离开窄视角簇；若进一步证明运动近共面，再寻找离面视角。本轮不使用未经认证的第二视频位姿。

| 路线 | 独立/共同评价N | Dxy MAE mm | 中位绝对相对误差 | Dxy p95 mm | 最大Dxy误差mm |
|---|---:|---:|---:|---:|---:|
'''%(100*contribution,full['actual_component_change']['total'],full['weighted_actual_component_change']['silhouette'],full['weighted_actual_component_change']['prior'])
 for x in stats_:
  d=x['Dxy_AE_mm'];text+='|%s|%d/%d|%.4f|%.2f%%|%.4f|%.4f|\n'%(x['tag'],x['evaluable_N'],x['target_N'],d['MAE'],100*x['median_absolute_relative_error'],d['p95'],d['maximum'])
 text+='\n以上仅为Ring尺度固定、各预测最佳SE3后的形状比较；输入本身和原相机下的Mask指标仍在原公制坐标计算。不是对真实高度/体积测量的认证。数值成功组分母与几何失败全部保留。\n\n虚拟控制暴露的目标重采样差异也提示应独立审查真实320监督。本轮为公平性未改变真实Mask路径，尚未量化它对真实柄部的影响，不能断言它是G03片状延伸的主因。\n'
 for name in ['TECHNICAL_REPORT_SUMMARY.md','TECHNICAL_REPORT.md']:
  p=R/name;p.write_text(p.read_text().split(MARK)[0].rstrip()+'\n'+text)
 positions=[]
 for p in(R/'code').glob('*.py'):
  for node in ast.walk(ast.parse(p.read_text())):
   if isinstance(node,(ast.FunctionDef,ast.ClassDef)):positions.append(dict(file=str(p.relative_to(R)),symbol=node.name,line=node.lineno))
 table('metrics/IMPLEMENTATION_CODE_POSITIONS.csv',positions)
 print('INTERPRETATION_APPENDED',flush=True)
if __name__=='__main__':main()
