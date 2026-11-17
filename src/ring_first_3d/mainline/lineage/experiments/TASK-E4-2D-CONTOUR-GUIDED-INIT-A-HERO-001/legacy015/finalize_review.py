"""Post-freeze human-readable interpretation. Never changes predictions/selection."""
from common import *
from collections import Counter

MARKER = '\n## 完成后的综合判断（不改变冻结预测）\n'

def main():
    gt = load(R/'metrics/BLENDER_GEOMETRIC_METRICS.json')
    paired = list(csv.DictReader((R/'metrics/COMMON_SUCCESS_PAIRED_COMPARISONS.csv').open()))
    counts = []
    for right in ['Init-B_FINAL', 'Init-C_FINAL', 'Stalk-B', 'Stalk-C']:
        rr = [x for x in paired if x['right'] == right]
        counts.append(dict(right=right, common_N=len(rr),
            Chamfer_improved_N=sum(float(x['Chamfer_delta_right_minus_left_mm']) < 0 for x in rr)))
    save('metrics/PAIRED_INTERPRETATION.json', counts)
    text = '''
## 完成后的综合判断（不改变冻结预测）

**执行完成：11/11 个独立物理组，33/33 条初始化路线、15/15 条 Ip 路线，81/81 个初始/最终模型完成固定尺度刚性评价。全组 B0 本轮不通过；直接反例是 G03 仍未形成合理、连续的三维长柄骨架。** 这不是对 PyTorch3D 整条路线的否定。

分支：`exp/TASK-E4-MULTIVIEW-INIT-STALK-015`；预注册提交 `7dd0517`，Phase B 合同提交 `054f089`。最终交付提交包含本报告；精确源码与模型哈希见 provenance。

1. **初始化推荐保留 Init-A。** Init-B 的留出 IoU 中位数由 A 的 0.8800 提高到 0.8991，ICP 后 Chamfer 跨组均值由 0.4829 降至 0.4591 mm，但 B 有 4/11 组新增密集 Ring 穿入标记；C 同样有 4/11。不能用二维或 GT 平均收益豁免物理约束。初始化使用稀疏 CAD 软惩罚，后续约束又相对于各自初值“不恶化”，因此无法自动修复已经带入的碰撞。保留 A 是冻结前的统一 FIT/几何规则，不是 GT 后挑选。
2. **扩大更新覆盖有用，但尚不是可靠柄部恢复。** 当前 G03 的远轮廓关联顶点为 42，旧局部候选带覆盖 0，Stalk-B 覆盖 42/42，最大实际位移 4.8904 mm，留出 IoU 从 Stalk-A 的 0.8582 提高到 0.9056。三维结果却是扁平三角翼。Stalk-C 仅覆盖其中 13/42 个点，其他 29 点在局部表达中无更新自由度；它仍无明显长柄。G03 Stalk-A 为 0/30 接受、固定停滞终止，保存的是该路线最后有效状态，不是一次成功的几何更新。
3. **五例 Ip 没有共同的三维改善证据。** Stalk-B 相对 A 的双向 Chamfer 均值为 0.4816 vs 0.5191 mm，但五例中只有 2 例下降，其中 G11 仅约 0.000013 mm；收益主要来自 G03 的 0.2001 mm 降幅，另外三例略升。Stalk-C 为 0.5192 mm，整体并未优于 A。G03 的 C 误差由 1.2697 增至 1.2953 mm。不能仅依据全 Mask FIT 中位数或 Dxy 宣称柄部正确。
4. **冻结的 FIT-only 数值候选与科学推荐分开。** 事前规则选中 Stalk-C 作为五例 Ip 的统一交付候选，所有 A/B/C 结果均保留；本轮不将 C 提升为已验证柄部主线。报告没有依据后来的 GT 改选模型、停止点或超参数。
5. **B0 不作全组 PASS。** G03 的长柄骨架不满足章程；G01/G02/G10/G11 的头柄空间对应仍不足以认证。Is/IIa 的连续粗主体可以交人工审阅作为适配候选，不追加局部复杂度；既有微小 Ring 穿入、基底和稳定性限制仍逐组列出。后续 HERO—主体适配须待本轮审核，不自动执行。

### 关键诊断与实现边界

- Phase B 从选定 Phase A FINAL 重新建立优化器和相对形状先验，三条路线起点一致；不是恢复历史 013 的 Adam 状态。相对边长、Laplacian 之外，法向一致性仍是绝对项，不能称全部先验在初值严格为零。
- Stalk-C 是现有网格上的 11 个中心线/变截面参数加局部自由残差，不新增管状拓扑；中心线种子来自拟合轮廓反投影代理，不是可靠三维对应。代理长度不是解剖柄长。相同损失并不能弥补错误支持区域。
- G02 初始分量梯度加法误差 0.00038848，未通过冻结的 0.0001 门槛；最终 A/B/C 误差分别为 0.00199991 / 0.00012181 / 0.00026243，也全部 FAIL。其余 12/15 个最终状态通过加法复核；全部分量梯度有限。原因未完全归因，不改阈值或伪称全部验证通过；各路线 FINAL_COMPONENT_GRADIENTS.json 保留原值，不用不同参数单位的原始范数直接比较 A/B 与 C。
- FACE_ORIENTATION 是与起始法向的点积约束，会限制大角度转动；它不是实际翻面的充要判据。独立自交检查仍保留。新增穿入、初始已有穿入与严重物理错误不能混称。
- 视角子集诊断去掉最后一个新增 FIT，固定 8 nfev，而完整初始化为 20 nfev；因此差异混有求解预算影响，不能作为纯粹视角稳定性的因果结论。也未开展多随机初值大搜索。
- 目标轮廓权重随 attempt 递增；接受只比较同一次 attempt 的相同权重目标，跨 attempt 总损失不保证严格单调。实际位移与分量梯度分开保存。
- 有效 HERO 首层覆盖没有下降的路线为 48/48，不代表未命中问题已消失：G03 仍有未命中；不通过降低统计分母掩盖它们。

### GT 的使用和不可评价项

按研究者追加授权，每个预测独立旋转、平移后比较形状，Ring 尺度锁定，ICP scale=1；96 个旋转起点、8 个双向细化，不能证明数学全局最优。每个预测只有一组变换，Dxy/高度/距离共用；原始毫米坐标模型及真实相机下轮廓不改变。**这些是姿态对齐后的形状指标，不是端到端定位精度。**

所有 81 个模型均有 Chamfer 和 Dxy；没有头/柄独立作者语义的区域 Chamfer、柄长和截面半径精度为 NOT_EVALUABLE。G11 无作者基底，作者基底高度不可评价。其他高度也受作者与部署基底对应限制。实体不合法或底盖缺乏物理依据时，严格实体 IoU 不可评价；条件占据估计单列，不能以 F-score 代替体积 IoU。F-score 的毫米容差、8192 面积采样/方向及两个方向独立距离见 EVALUATION_PROTOCOL.md 和原表。

### Phase C 决策与下一步

本轮未另开 Blender 控制实验。当前已能由真实残差覆盖、局部参数的严格零支持区、几何保护拒绝和实际薄片结果定位具体失败，不需要仿真来判定“本次没有恢复可信长柄”。剩余拓扑分辨率、遮挡与错误三维对应的因果比例仍未分离，不宣称已解决；建议人工确认后在既有虚拟 Ip 做一次固定种子/可见性对照，而不是继续按 GT 调整本轮真实实验。现有真实数据尚不足以决定改换完整重建路线。

### 代码、复现与结果入口

算法合同见 PHASE_B_ALGORITHM_CONTRACT.md；实际入口为 initialize.py:Initializer、train_mesh.py:main、stalk.py、train_stalk.py:main，评价为 best_rigid015.py:align/main。代码与配置哈希、工程修复的原副本均在 provenance；运行方式见 REPRODUCE.md。第一次 GT 读取晚于 ALL_PREDICTIONS_AND_SCALE_FROZEN_BEFORE_GT，最终完整性检查见 metrics/DELIVERY_VERIFICATION.json。

核心四图在 figures/Fig1–Fig4；全部 11 组初始化图、5 组 Ip 多角度及留出投影、六方向细节保留。review_meshes 包含全部 81 个原始毫米网格的精确几何副本及 11 个 FIT-only 主体候选；完整优化器/RNG 检查点留本地，索引见 RESULT_INDEX.md。以上交付仅供审核，不替换正式主线。
'''
    for name in ['TECHNICAL_REPORT_SUMMARY.md', 'TECHNICAL_REPORT.md']:
        p=R/name
        p.write_text(p.read_text().split(MARKER)[0].rstrip()+'\n'+text)
    b0=R/'B0_REVIEW.md'
    addition='''
## 实际图片审核后的结论

全组结论为 **B0_NOT_PASSED_THIS_RUN**，而不只是等待自动指标。G03 是明确反例：Stalk-A 不更新，B 为扁平翼状突出，C 无可信长柄，均不能提供章程所需的头柄空间骨架。G01/G02/G10/G11 保留 STALK_SPATIAL_SKELETON_REQUIRES_VERIFICATION，未凭全体尺寸或 Mask 指标升级。六个 Is/IIa 为人工可审阅的连续粗主体候选，保留表中 Ring 与初始化稳定性限制，不追加本轮局部优化，也不声称获得测量认证。该判断不改变任何冻结输出或 FIT-only 选择。
'''
    b0.write_text(b0.read_text().split('\n## 实际图片审核后的结论')[0].rstrip()+'\n'+addition)
    save('metrics/B0_FINAL_DECISION.json',dict(status='B0_NOT_PASSED_THIS_RUN',
        decisive_case='G03',reason='No credible connected spatial stalk skeleton; B is a thin wing, C lacks extension',
        predictions_changed=False,GT_used_for_selection=False,formal_pipeline_promoted=False))
    runs=load(R/'metrics/FAILURE_LEDGER.json')
    lines=['# FAILURE_LEDGER','','缺失预测为 0；科学失败与数值输出分开。全部 48 条原始运行及拒绝计数仍保留在 metrics/FAILURE_LEDGER.json，不把成功运行列为算法失败。','','## 主要失败与证据','','| 范围 | 失败或限制 | 证据 |','|---|---|---|',
        '| Init-B：G03/G07/G05/G06；Init-C：G03/G07/G06/G10 | 相对共同起点新增密集 Ring 穿入标记；初始化软惩罚不足，下游未自动修复 | [逐路线几何表](metrics/PHASE_A_ALL_METRICS.csv)、[全组图](figures/Fig1_All11_Initializers_And_Updates.png) |',
        '| G03/Stalk-A | 0/30 接受，Ring 及全目标拒绝后固定停滞终止，无有效形变 | [候选日志](arms/Stalk-A/metrics/G03_CANDIDATES.json) |',
        '| G03/Stalk-B | 留出轮廓改善但生成薄片状突出，最大位移 4.8904mm，不能视为长柄恢复 | [多视图对照](figures/phase_B/G03_Stalk_Comparison.png)、[分辨率与拉伸](metrics/STALK_RESOLUTION_AND_COVERAGE.csv) |',
        '| G03/Stalk-C | 42 个远关联顶点仅 13 个在局部表达支持范围，未形成可信长柄 | [机制证据](figures/Fig3_Current_Coverage_Gradient_And_Motion.png)、[B0](B0_REVIEW.md) |',
        '| G02 初始及最终梯度诊断 | 初始 0.00038848；最终 A/B/C 为 0.00199991 / 0.00012181 / 0.00026243，均超过冻结 0.0001；梯度有限，原因未完全归因 | [初始 FAIL](arms/Stalk-A/metrics/G02_STALK_PROBE.json)、各路线 G02_FINAL_COMPONENT_GRADIENTS.json |',
        '| 全部 Ip 区域精度；G11 高度 | 无可靠作者头/柄标签，不能定量报告独立柄部 Chamfer/长度/半径；G11 无作者基底 | [GT 表](metrics/BLENDER_GEOMETRIC_METRICS.csv) |',
        '| 初始已有 Ring 接触/穿入 | 不恶化约束不等于物理无碰撞，不能以新增标记为零声称无穿入 | [B0 逐组表](B0_REVIEW.md) |',
        '| Phase B 驱动与产物生成 | 早期重复 case 关键字导致结果索引异常，未改变损失/优化器；保留已完成模型后恢复。图排版与评价视角字段独立修正 | provenance/PHASE_B_ENGINEERING_IO_FIX.json、OUTPUT_LAYOUT_FIX.json、EVAL_VIEW_METADATA_ADAPTER.json |',
        '', '## 全部路线：实际停止状态及拒绝原因', '', '拒绝计数是内层候选/回溯检查次数，可能超过外层 attempt，不能直接当作外层拒绝率。', '', '| 病例 | 路线 | 接受/attempt | 状态 | 主要拒绝原因及计数 | 原始日志 |','|---|---|---:|---|---|---|']
    for q in runs:
        run=q['run']; reason=', '.join(f'{k}:{v}' for k,v in Counter(q['rejection_counts']).most_common(3)) or '无'
        n,t=q['case'],q['arm']
        lines.append(f"|{n}|{t}|{run['accepted']}/{run['attempts']}|{run['status']}|{reason}|[候选](arms/{t}/metrics/{n}_CANDIDATES.json)|")
    (R/'FAILURE_LEDGER.md').write_text('\n'.join(lines)+'\n')
    (R/'RUN_STATE.md').write_text('''# 最终运行状态

Phase A 33/33、Phase B 15/15 已结束；81/81 个模型完成独立固定尺度刚性评价。核心四图、逐病例和六视图、参数与检查点索引已生成。预测、Ring 尺度及 FIT-only 选择均早于第一次 Blender 几何读取冻结。

全部组保留，历史测量值回退为 0。G03/Stalk-A 数值输出为最后有效状态但接受更新为 0；不能称为成功柄部恢复。全11组 B0 本轮不通过；其他失败见 FAILURE_LEDGER.md。当前已停止优化，等待人工审核，不推进 HERO 适配或追加调参。

本地权威状态 runtime/STATUS.json，交付完整性 metrics/DELIVERY_VERIFICATION.json，技术结论 TECHNICAL_REPORT_SUMMARY.md。
''')
    (R/'RESULT_INDEX.md').write_text('''# RESULT_INDEX

- [技术报告摘要](TECHNICAL_REPORT_SUMMARY.md)、[失败记录](FAILURE_LEDGER.md)、[B0 判断](B0_REVIEW.md)。
- [初始化全组图](figures/Fig1_All11_Initializers_And_Updates.png)、[五例 Ip 图](figures/Fig2_All5_Ip_Stalk_Comparison.png)、[真实机制图](figures/Fig3_Current_Coverage_Gradient_And_Motion.png)、[全组刚性评价图](figures/Fig4_All11_Rigid_Aligned_GT_Comparison.png)。
- `figures/phase_A/`：11例真实输入/三种初始化/更新/留出投影；`figures/phase_B/`：5例 Ip 三路线；`figures/details/`：六视图及真实执行位移箭头。
- `review_meshes/Gxx/`：全部 81 个原始毫米 Mesh 的精确 NPZ 几何副本；另有 11 个 `BODY_FINAL_mm.ply` FIT-only 候选，不据 GT 改选。原始几何身份核对见 [复制索引](metrics/REVIEW_MESH_COPY_INDEX.json)。
- [完整本地 Mesh、优化器检查点绝对路径](metrics/RESULT_INDEX.json)；每个 `arms/路线/local_results/Gxx/FINAL.pt` 保留优化器、参数和随机/采样状态；同目录 STEP/MECHANISM 保存中间状态。严格冻结后不在此目录恢复更新，迁移需派生新目录并校验哈希。
- [逐预测评价](metrics/BLENDER_GEOMETRIC_METRICS.csv)、[SE3 变换](metrics/BLENDER_RIGID_ALIGNMENT.csv)、[路线统计](metrics/GT_ROUTE_SUMMARIES.csv)、[配对比较](metrics/COMMON_SUCCESS_PAIRED_COMPARISONS.csv)、[原坐标观测指标](metrics/ALL_NATIVE_FLAT.csv)。
- 本地评价副本 `local_results/aligned/Gxx/`；源预测不改动。GT 原始资产和大型检查点不上传 GitHub，来源及 SHA 在 provenance/evaluation_only 索引中，复现见 REPRODUCE.md。
''')
    print('FINAL_REVIEW_WRITTEN',len(gt),flush=True)

if __name__=='__main__':main()
