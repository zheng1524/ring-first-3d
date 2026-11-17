"""Human review reports, from all frozen-budget outcomes; no model selection."""
from common import *
def f(x,n=3):return 'NaN'if x is None else f'{x:.{n}f}'
def tab(h,rows):return '| '+' | '.join(h)+' |\n| '+' | '.join(['---']*len(h))+' |\n'+''.join('| '+' | '.join(str(x)for x in row)+' |\n'for row in rows)+'\n'
AUDIT='''
| 审计项目 | 必须汇报 / 本轮结果 |
| --- | --- |
| 目标组数 | 4个独立物理组：G01_004、G06_004、G07_004、G08_005；004/005不混合 |
| 本算法独立成功 | E1数值主体4/4，E2数值主体4/4；8模型不是8个息肉，数值输出不代表测量正确 |
| 本算法失败 | 正式72次求解中3次预算耗尽；保留有限诊断候选，但接受状态失败/NaN；完整A主模型8/8数值收敛，严格独立相机/真值资格成功0/4 |
| 历史测量值回退 | 0；最终预测来自各自本轮9参数拟合；官方DXY仅提供本轮独立生成的2D像素几何 |
| 失败组及具体原因 | [逐组失败与来源](05_FAILURE_LEDGER.md)、[全部初值与扰动](03_E1_E2_METRICS.csv)、[Fig4](figures/Fig4_Stability_And_Failure.png) |
| 最终统计样本 | 配对4物理组/目标4；条件性2组G01/G06、压力2组G07/G08；无全流程独立B，不能按72个模型计算样本量 |
| 是否使用GT选择算法 | 否；真实GT/Oracle读取0；[协议](01_PROTOCOL.md)和[首轮冻结](provenance/PREOPTIMIZATION_FREEZE.json)先于首轮优化；[一次数值修正](PROTOCOL_CORRECTION_v0.2.md)及[再冻结](provenance/PREOPTIMIZATION_CORRECTION_v0.2.json)先于正式重跑 |

真实3D/直径 MARE、MAE、p95和最大GT误差均 NOT_EVALUABLE。本报告相对D残差是相对于HERO内部轴向深度差，不能冒充独立真实深度精度。
'''
def write(name,text):(R/name).write_text(text)
def main():
    P=load(R/'metrics/PRIMARY_A_ONLY.json');D=load(R/'provenance/DXY_GENERATED.json');S=load(R/'metrics/MULTISTART_STABILITY.json');V=load(R/'metrics/VARIANT_STABILITY.json');summary=load(R/'metrics/SUMMARY.json');fits=load(R/'metrics/ALL_FITS.json');validation=load(R/'metrics/VALIDATION.json');mainP=[m for m in P if m['variant']=='full']
    metrics_table=tab(['物理组/输入','全Mask IoU','固定D命中/32','相对D MAE/p95/max mm','边界 median/MAE/p95/max px','FP/原Polyp数','FN/原Polyp数'],[[m['scene']+' '+m['arm'],f(m['B'][0]['full_mask_IoU'],4),str(m['B'][0]['depth_hit_N'])+'/32',' / '.join(f(m['B'][0]['relative_depth_mm'][k])for k in ['MAE','p95','maximum']),' / '.join(f(m['B'][0]['boundary_bidir_px'][k],2)for k in ['median','MAE','p95','maximum']),f(m['B'][0]['outside_per_fixed_mask'],4),f(m['B'][0]['miss_per_fixed_mask'],4)]for m in mainP])
    stability_table=tab(['实例/输入','中心三初值最大差 mm','半轴最大跨度 mm','表面两两MAE均值 mm','旋转最大差 °','方向歧义'],[[x['scene']+' '+x['arm'],f(x['center_pairwise_mm']['maximum']),f(x['max_semiaxis_spread_mm']),f(x['surface_pairwise_MAE_mm']['MAE']),f(x['rotation_pairwise_deg']['maximum'],1),x['rotation_ambiguous']]for x in S])
    variant_table=tab(['实例/输入/扰动','中心变化 mm','半轴最大变化 mm','表面MAE/p95/max mm','B IoU变化','状态'],[[x['scene']+' '+x['arm']+' '+x['variant'],f(x['center_mm']),f(x['maximum_semiaxis_change_mm']),' / '.join(f(x['surface_distance_mm'][k])for k in ['MAE','p95','maximum']),f(x['B_IoU_change']),('CONVERGED'if next(m['optimizer_success']for m in P if(m['scene'],m['arm'],m['variant'])==(x['scene'],x['arm'],x['variant']))else'NONCONVERGED_DIAGNOSTIC')]for x in V])
    input_table=tab(['源图/质量','形状','中心 px','半轴 px','角度 rad','Strict'],[[x['source']+' / '+x['quality']['quality_class'],x.get('shape','NOT_EVALUABLE'),', '.join(f(v,2)for v in x.get('center_px',[])),', '.join(f(v,2)for v in x.get('semiaxes_px',[])),f(x.get('angle_rad'),4),x['quality'].get('strict_stable')]for x in D])
    geometry_table=tab(['实例/输入','中心 xyz mm','半轴 mm','CAD遮挡比例','原Ring像素上的可见Polyp预测数'],[[m['scene']+' '+m['arm'],', '.join(f(v)for v in m['B'][0]['center_mm']),', '.join(f(v)for v in m['B'][0]['semiaxes_mm']),f(m['B'][0]['CAD_occluded_fraction'],4),m['B'][0]['unknown_ring_prediction_N']]for m in mainP])
    text='''# 双输入统一主体拟合：技术报告

**最终判断：MIXED。** 本轮4组配对观测不能支持“完整Mask普遍更稳定”，也不能支持“椭圆必然更好”。G01的完整Mask改善投影覆盖，但相对深度更差；G08椭圆的留出轮廓/深度较好；G06与G07在不同稳定性维度上方向相反。**目前不建议取消椭圆预处理并将完整Mask升级为唯一标准输入。** 这不是对完整Mask本身的否定，也不是对统一重建路线的否定。

两臂只使用同一个9参数可旋转椭球，源数据、D样本、相机、初值、R0、界、权重和求解预算一致。类别不进入拟合。没有头部/柄提取、Is球冠、IIa高度场或类型专用补丁。A2/B1/B2、神经/融合实验执行0；历史任务未覆盖。

## 执行与版本

父提交 `1d5e36a46af93eb0d896e8d3710303dcab685878`。新分支 `exp/TASK-E4-A1-ELLIPSE-VS-FULLMASK-001`。预注册提交10f70a1，Ring混合池化数值修正冻结提交64bc0b0。原始72次诊断保留，正式报告只使用修正后原预算重跑的72次，不根据两轮效果挑输出。

研究者追加授权用最终DXY生成E1。GitHub `main` 和本机均核实为 **75d58ca5b643fb4d8e0eb887b45ad0f056b0bb95**，机器主线为OFFICIAL_MAINLINE V9.1 Geometry + Mid，API `dxy_mid.pipeline.measure_files`。DXY原Python3.10环境运行，代码只读；13份当前冻结640×360 RGB/Mask均独立生成选中圆/椭圆，累计'''+f(sum(x['seconds']for x in D),2)+'''秒。仅像素中心、basis、轴、角及质量进入本任务，不采用DXY毫米输出，也不使用旧缓存补值。具体SHA、坐标和版本见[02输入审计](02_INPUT_AUDIT.md)。

重要资格：G01四份DXY结果均为Q_conflict_recovery、Strict=false，不能称严格可信的真实头部椭圆。G06/G08当前DXY结果Normal且Strict；G07部分Strict未通过。DXY二维质量与Ring-First相机资格是不同判断，不互相替代。G01当前CORE相机仍INSUFFICIENT_EVIDENCE；G06的A条件性可用；G07历史HERO链未合格、G08保留压力身份。所有B保持历史依赖CONDITIONAL。
'''+AUDIT+'''
## 方法和公平性

原A/B逐源保持不变，见[01_PROTOCOL](01_PROTOCOL.md)。D从完整原始Mask及冻结原生有效性缓存选择每源32条可靠射线、16个固定对，两臂完全相同，不使用旧Ip头部射线集合。移除最后A后，其余D点不重采样。没有HERO绝对XYZ软锚点或额外H损失。

E1把实际DXY圆/椭圆转为解析二维目标；E2直接以完整原始Mask为目标。两臂随后使用完全相同的双向轮廓和区域损失：预测投影曲线128点到观测边界距离场、所有可靠原边界到投影conic的Sampson距离、完整原像素4×4已知区域面积池化。原Mask中的柄/侧面/凹陷/断续区域全部保留，不用24方向支撑替代完整Mask。E1上游通用DXY规则可能筛选主体/弱Q，但不是本轮按类型另做3D处理。

Ring原标签为未知，不能作为Polyp不存在的负证据；Ring接触边界不作解剖轮廓。实际CAD用于遮挡；soft CAD仅用于可微二维可见性，D和正式评价使用解析椭球真实首相交轴向Z，单位mm。区域四分块为固定数值求积近似，不是精确可微光栅化。

C各子项先噪声白化、soft_l1，再按行数/质量归一；三项各1/3，前/背景质量平衡。两臂λC=λD=1、λR=.05，轮廓σ3px、相对Dσ.25mm。D无交点对不伪造深度，保留删失和共同ray/body可行性惩罚；仍按固定32射线/16对报告未命中。

每组每臂3初值×full/drop/camera三条件，共72次。正式求解累计'''+f(summary['fit_seconds'],2)+'''秒，实际残差调用'''+str(summary['actual_residual_calls'])+'''次（不含I/O/逐像素评价/制图）。69/72优化器收敛，3个预算耗尽，22/24 A-only主条件收敛；完整A的8个主模型均数值收敛。未收敛的扰动候选不删除，也不能当成可靠最终预测。全部初值见[03指标](03_E1_E2_METRICS.csv)、[原始参数](metrics/ALL_FITS.json)。

## 真实B：共同完整Mask分母

'''+metrics_table+'''
G01 B完整Polyp分母12,424，绝不是上轮的7,523头部像素；因此新旧IoU不能直接对比。其他组B分别G06 13,047、G07 17,590、G08 19,631。Ring未知像素不作FP，另报“预测可见Polyp落在原Ring标签内”的数量，以免掩盖CAD/Mask/相机次序矛盾。

G01：E2 IoU .847→.867、D命中25→29，但相对D MAE .524→1.162mm，FP/Polyp .0008→.0227；是“轮廓/覆盖较好但深度较差”的明确取舍。不能仅据IoU宣布改进。

G06：两臂IoU约.942，E2比E1低.000675，边界MAE减少.612px、FP略少，但D .164→.190mm。不能因四舍五入相同就说两个模型等价。

G08压力组：E2 IoU .882→.852、边界MAE增加1.415px、D .426→.510mm；命中26→27增加，但不是误差改善。E1对这份留出更好，两臂均存在严重多初值分支。

G07压力组：E2 IoU .850→.868、边界MAE略降、D .800→.786mm、命中同为28；但相机微扰稳定性更差，且HERO链资格不足，不能升级正式Is成功。

所有组E2相对E1的正式B命中没有下降，但仍存在未命中；不能据此宣称已解决所有覆盖退化。完整A主模型相对统一初值未出现固定D覆盖下降，只是本配置的诊断结果，没有另做可行性项消融，不能单独证明该项必然有效。[覆盖记录](metrics/A_COVERAGE_DEGENERACY.csv)。

'''+geometry_table+'''
CAD遮挡比例的分母是该模型原始投影命中数，属于可见性描述；正式命中/漏射仍用固定原观测分母。G07在原Ring标签内出现大量可见Polyp前层（E1 3599、E2 2001像素），是CAD/Mask/相机/主体不一致的诊断，不能因该处按未知排除负监督而掩盖。CAD在本轮只提供可见性，不构成已验证的组织—环碰撞/接触约束。

## 稳定性

'''+stability_table+'''
表面差来自实际椭球Mesh的2048面积样本、双向三角面距离，不是两组HERO之间的对齐；mm表示模型变化，不是真实误差。方向做了半轴排序与proper符号等价处理；半轴近等（5%）时方向本来就不唯一。G01近球，不能把旋转角降低几度解释为物理方向更准；G07 E2中心/表面更稳定而旋转最大差更大，也不能声称方向全面更稳。

'''+variant_table+'''
G06 E2删视角中心变化.848mm，优于E1 1.914mm，但其三初值表面散布1.074mm大于E1 .713mm。G07 E2三初值/删视角较好，却对相机副本变化.911mm大于E1 .131mm，后者主扰动候选未收敛，只能作失败诊断。G08两臂都不稳定，E2相机副本变化2.671mm。

这里的微扰结果包含重新求解与A最优分支切换，不是线性误差传播系数。移除视角：G01由3变2，其余由2变1；跨组难度不同，不能按类型归因。初值/R0/先验均固定，修正了上轮LOO可能同时改变初始化的混杂。B从未选解。

## 几何与数值限制

统一椭球天然凸、闭合，不能同时表达窄连接部与较大的主体，也不能真实表达不同背面/多层/非凸区域。本轮没有新增第三种形状来补救。完整A选解轴比约1.02–6.76，所有72候选最大7.92，未触发预设>20异常拉伸门槛；这不等于形态已真实。8个主模型均单连通、无退化面；闭合背面属于先验推断。

8个合成/合同检查通过：同目标跨臂残差相同、类别标签更换残差相同；完整Mask能辨别24方向支撑完全相同但内部不同的控制；Ring混合单元条件比例正确；CAD次序与解析轴向根对三角面等。真实完整A主模型固定D射线上解析根/导出Mesh命中分歧0、A根在CAD后0、预测轮廓越画幅0。[实现检查](metrics/VALIDATION.json)、[根/CAD审计](metrics/ROOT_AND_VISIBILITY_AUDIT.json)。检查不等于真实3D GT验证。

已修正且保留的工程失败：Ring混合池化初稿违反未知语义；首轮72结果被明确拒收，作为诊断保留，未与正式结果混选。首次环境缺skimage，改用已验证DXY自身环境；没有下载模型或改变DXY数学。详见[失败账本](05_FAILURE_LEDGER.md)。

原始Polyp/Ring像素边界可能存在分割噪声，HERO和相机也有已知不确定性。G01的Mask不规则结构与椭球表达能力冲突是合理候选解释，但**无法用本轮数据唯一归因为Mask不可靠或模型不足**；G01的E1本身还是Q恢复弱证据。四组条件/压力统计不足以作普遍因果结论。

## 五个问题的回答

1. **完整Mask是否更解释B？** 不统一：G01/G07 IoU较高，G06近似持平但略低，G08较低；深度也有相反方向。
2. **中心/方向/尺度是否更稳？** 不统一。部分中心或表面散布减小，部分初值/相机/方向更差；不能只选一种稳定性指标。
3. **椭圆简化是否更稳定？** 部分成立，尤其G06三初值、G08留出及相机扰动；G07三初值和删视角则E2较好。简化不能保证稳定。
4. **失真来自输入还是模型？** 两者及相机/HERO误差耦合均可能。凸椭球表达复杂结构的能力有限，但没有独立证据把误差全归给Mask。不能据此恢复类型专用分割。
5. **能否取消椭圆成为统一标准？** 当前不建议。E2作为统一直接输入的工程通路已可运行，应继续保留两输入对照与资格/不确定性；没有证据支持全面替换。

最终 `MIXED` 的适用范围：这4个固定单视频、相同9参数椭球、有限60-nfev三初值预算下的条件性比较。不是统一重建方法的最终验收，也不支持按类别切换E1/E2。待人工审阅；本轮停止，不进入A2/B1/B2。

## 人工审阅材料

- [Fig1：两类真实二维输入](figures/Fig1_Two_Inputs.png)
- [Fig2：同一真实B及完整Mask](figures/Fig2_Frozen_B_Comparison.png)
- [Fig3：统一公制XYZ/主体/CAD](figures/Fig3_Metric_3D_Comparison.png)
- [Fig4：多初值/视角/相机稳定性与失败](figures/Fig4_Stability_And_Failure.png)

六视角、分离节点GLB和离线HTML在local_results/review；索引见[VISUALIZATION_INDEX](metrics/VISUALIZATION_INDEX.json)。PLY/图使用mm；GLB全部图层统一mm→m转换符合GLTF单位，实际物理尺度不变。原始HERO和学习/拟合推断主体分别标注，B RGB从未给模型重新上色，没有后处理平滑/补面。

[稳定性报告](04_STABILITY_ANALYSIS.md)、[复现命令](REPRODUCE.md)。
'''
    write('TECHNICAL_REPORT.md',text)
    write('02_INPUT_AUDIT.md','''# 二维输入与来源审计

研究者追加授权后，实际使用最终官方DXY代码独立生成全部13源的主体圆/椭圆。GitHub远端main与本机HEAD均为75d58ca5b643fb4d8e0eb887b45ad0f056b0bb95；[精确版本回执](provenance/DXY_VERSION_AUDIT.json)保留机器主线和源码SHA。官方路径 `dxy_mid.pipeline.measure_files`，配置V9.1，未调用旧实验拟合器替代。GitHub连接器暂不可用，使用只读git ls-remote核验origin/main；不更改DXY分支或文件。

初始查找：历史790帧回归缓存并不覆盖本轮源，同帧号可能是不同图像；另有dxy_original_fits及*_candidates只保存Ring几何/位姿。它们没有作为Polyp椭圆输入。本轮不会从错帧转移椭圆，也不根据文件名名义尺寸或旧测量值补齐。

生成输入为本轮冻结源RGB与原Mask，640×360，标签0背景/1Polyp/2Ring；与冻结K同坐标。内容SHA生成稳定RNG身份，不用类型/组名决定算法。已知Ring内径只用于官方接口，DXY毫米尺度输出被丢弃。记录完整像素center、basis、半轴和旋转，不再根据本轮3D效果重拟合。

官方DXY有通用A/B主体候选、Ring内外证据、通用开运算、短Q处理和Q恢复；这些规则对所有输入相同，没有Paris类型参数。本轮没有为Ip额外做头部/柄提取。E1仍是受该上游规则影响的主体近似，不能称真实解剖头部。E2完全不调用DXY候选Mask/开运算，直接使用全部原始Polyp像素。

'''+input_table+'''
圆的角度不唯一，列表中的角度只是basis的SVD表示；basis矩阵才是可复现的曲线定义。ellipse/circle不通过类型选择。G01均Q冲突恢复，不能冒充Strict椭圆；G07部分Strict=false。二维质量不等于相机认证。

每源RGB/Mask/HERO/K/c2w/CAD路径与SHA见[INPUT_ASSET_SHA](provenance/INPUT_ASSET_SHA.json)；原生/归档映射及D pixel ID、具体射线值在inputs/；两臂用同一份缓存。[逐源资格](metrics/INPUT_QUALIFICATION.csv)、[生成几何](provenance/DXY_GENERATED.json)。G01_005不入组、不跨视频合并；G07无当前合格清理缓存，保留Raw压力身份。源清理未重跑。

协议继承的G01 tier文字仍含旧HEAD_CUE字样，只是历史资格元数据；本轮没有任何旧头部Mask输入或操作，正式图/报告已明确采用全Mask。
'''+AUDIT)
    write('04_STABILITY_ANALYSIS.md','''# 稳定性：同一9参数模型的条件性配对

最终MIXED，不能仅凭损失下降或一张图选择标准输入。初值/R0/界在两臂和三条件之间完全相同。每个完整A条件有3个初值，所有结果保留，A-only选主解，B不参与选择。

'''+stability_table+'''
中心为同一Ring_world_mm里的欧氏距离；半轴按长度排序比较，不按参数索引误配。旋转消除proper轴符号等价后比较，近等轴方向不可唯一，angle不是独立物理误差。三初值表面差使用实际导出Mesh的面积样本与双向三角距离；报告的是模型间分歧，非真值误差或校准置信区间。

'''+variant_table+'''
扰动从相同预先冻结初值组重新求解，而不是每臂不同warm-start。删视角只删除最后A观测，R0/先验不重建；G01剩2视角，其余剩1视角。相机副本右乘tx .05mm/ry .1°，只动第一个A，原始相机不写回。变化包含局部极小分支切换，不是线性放大率。

G01 E2表面散布更小、微扰中心变化较小，但D误差大；G06 E2删参考稳定、三初值更差；G08两臂都有差解；G07 E2多初值较好但微扰较差。不存在全维度统一胜者。

69/72求解收敛；G08 E2删视角主解和G07 E1相机副本主解预算耗尽，其变化只作未收敛诊断。不可把该两项列为已收敛稳定性成功。[全部候选](metrics/ALL_FITS.json)、[配对比较](metrics/PAIRED_COMPARISON.csv)、[表面/初值详情](metrics/MULTISTART_STABILITY.json)、[扰动详情](metrics/VARIANT_STABILITY.json)。
'''+AUDIT)
    failed=[x for x in fits if not x['optimizer_success']]
    write('05_FAILURE_LEDGER.md','''# 失败账本

| ID | 步骤/范围 | 具体原因 | 处理与证据 |
| --- | --- | --- | --- |
| I01 | 旧椭圆缓存 | 同帧号不等于同图；部分文件实为Ring位姿 | 未用；研究者追加授权后按最终DXY源码重新生成 |
| E01 | DXY首启环境 | Ring工程Python3.12缺skimage | 使用DXY原Python3.10依赖；数学不改，不安装新模型 |
| E02 | DXY worker只读保护 | 初稿路径规则误拦cv2/data模块 | 只修正为DXY根下outputs/data/validation，未放开旧预测/GT读取 |
| E03 | 合成测试脚本解析 | 初稿多余括号 | 优化前语法修复，冻结后数学不因此改变 |
| M01 | 首轮Mask区域池化 | 混合Ring/已知像素单元的未知量混入比例 | 首轮72完整保留并标拒收；修正后再次冻结、同预算重跑，见[修正](PROTOCOL_CORRECTION_v0.2.md) |
| Q01 | G01_004 | CORE相机INSUFFICIENT_EVIDENCE；E1全为Q恢复/Strict=false | 只作条件性比较；E1全A主解B仅25/32射线，低覆盖 |
| Q02 | G06_004 | A条件性相机；B证据不足，且删参考变单视角 | 不认证真实形态/独立泛化；两臂多初值有差解 |
| Q03 | G08_005 | 压力身份；两初值可落入低IoU局部解，E2微扰位移2.671mm | 保留差解，不选B最好解；[Fig4](figures/Fig4_Stability_And_Failure.png) |
| Q04 | G07_004 | 部分最新单相机条件通过，历史HERO链未合格 | 压力测试，不升级Is正式成功；E1相机副本主解未收敛 |
| M02 | G01全Mask | E2 IoU/覆盖较好，但D MAE .524→1.162mm，FP增加 | 统一椭球表达/证据耦合风险，不恢复头柄分割 |
| M03 | G06稳定性 | E2删视角变化较小、初值表面散布却较大 | 不只挑稳定性有利指标 |
| M04 | G07稳定性 | E2初值/删参考较好，相机副本却较差 | 不宣布E2全面更稳定 |
| Q05 | 全部B | 历史上游/Gate/选帧依赖，且Ring标签处仍有预测可见前层 | CONDITIONAL；单独保留Ring重叠数，不作Polyp负监督掩盖 |
| S01 | 类型标签与GT | 无独立真实3D GT、样本仅4物理组 | MARE/真值MAE/p95/max NOT_EVALUABLE；不把72求解当72息肉 |

正式预算耗尽：

'''+tab(['实例','输入','条件','初值','nfev','终止'],[[x['scene'],x['arm'],x['variant'],x['start'],x['nfev'],x['termination']]for x in failed])+'''
保留其有限参数/损失/投影作为诊断，接受状态失败，accepted指标为NaN；不把预算耗尽自动算收敛，也不根据B换成另一个“好看”的初值。完整A8主模型均数值收敛，但不因此宣称真实准确。

没有主候选轴比>20（全72最大约7.92），未观察到模型家族意义上的自交/任意尖峰；闭合凸椭球仍可能错过细部或产生错误背面。本轮不增加第三种形状来消除失败。
'''+AUDIT)
    write('REPRODUCE.md','''# 复现

分支exp/TASK-E4-A1-ELLIPSE-VS-FULLMASK-001；Ring源码父提交1d5e36a，预注册10f70a1，数值修正冻结64bc0b0。原始数据保持原绝对路径和SHA，不复制视频/权重。

```bash
cd /home/liu/ring_first_3d_e4_e1e2
TASK_ROOT=experiments/TASK-E4-A1-ELLIPSE-VS-FULLMASK-001
PY=/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python
DXY_PY=/home/liu/new-polyp-dxy/.venv/bin/python
"$DXY_PY" -B "$TASK_ROOT/code/generate_dxy.py"
"$PY" -B "$TASK_ROOT/code/replay_inputs.py"
"$PY" -B "$TASK_ROOT/code/synthetic.py"
"$PY" -B "$TASK_ROOT/code/run.py"
"$PY" -B "$TASK_ROOT/code/analyze.py"
"$PY" -B "$TASK_ROOT/code/visualize.py"
"$PY" -B "$TASK_ROOT/code/validate.py"
"$PY" -B "$TASK_ROOT/code/write_report.py"
"$PY" -B "$TASK_ROOT/code/finalize.py"
```

输入缓存缺失的全新复现工作树先执行replay_inputs.py --rebuild，它复用冻结prepare科学语句，只将首次注册断言/写协议改为严格内容比较；现有结果目录只校验，不能覆盖历史结果。DXY和run.py逐源/求解恢复并跳过已有项。要独立重算DXY而非复用已生成像素几何，应在独立复现目录保留原JSON副本后从空DXY_GENERATED开始；用同一源SHA和content-seeded ID，不使用冻结毫米结果表。不要在现有人工结果目录删除文件强制重跑。

本地PLY、B首层/Mask NPZ、六视角、GLB和HTML在local_results，上传小型参数JSON、指标和4核心图即可。GLB各图层统一转为米，PLY和分析保持毫米。原始首轮在local_results/pre_ring_pool_fix和metrics/PRE_RING_POOL_FIX_*完整保留，不纳入正式比较。输入路径和哈希在provenance，环境在ENVIRONMENT.json。

generate_dxy用官方Python3.10（numpy1.26.4/scipy1.15.3/cv2 4.10.0/skimage .25.2），几何实验用原Ring Python3.12。两者只通过像素几何JSON交换，无网络/权重/GT。脚本只写新任务目录。正式源数据/科学代码由v0.2冻结校验，后续报告脚本单独索引。
''')
    print('REPORTS_WRITTEN_MIXED',flush=True)
if __name__=='__main__':main()
