"""Render the single final report from measured A2 artifacts."""
from common import *

def write(name,text): (R/name).write_text(text.strip()+'\n')

def main():
    sm=load(R/'CLEANUP_SUMMARY.json');dis=load(R/'CANDIDATE_DISCOVERY_SUMMARY.json');dom=load(R/'MODEL_DOMAIN_COMPARISON.json')['cohorts'];gg=read_csv(R/'INCREMENTAL_GEOMETRY_VALIDATION.csv');tests=read_csv(R/'A2_CONTRACT_TESTS.csv');protect=load(R/'config/FINAL_PROTECTION_CHECK.json');thin=load(R/'R14_THIN_STRUCTURE_DIAGNOSIS.json');replay=load(R/'runtime/replay_verification/REPLAY_VERIFY.json')
    per='\n'.join(f"| {r['source'].split('004_')[1]} | {r['original_N']:,} | {r['baseline_N']:,} | {d['anomaly_discovery_N']} / {d['review_pool_N']} / {d['not_reviewed_anomaly_N']} | {r['incremental_excluded_N']} ({r['incremental_fraction_of_baseline']*100:.4f}%) | {r['final_N']:,} | {r['projected_ray_area_proxy_fraction']*100:.4f}% |" for r,d in zip(sm['per_source'],dis['per_source']))
    domains='\n'.join(f"| {d['cohort']} | {d['total_retained_N']:,} | {d['L_mm']:.3f} | {d['voxel_mm']:.8f} | {d['ring_outer_diameter_voxels']:.3f} | 0 |" for d in dom)
    geometry='\n'.join(f"| {r['source'].split('004_')[1]} | {float(r['analytic_max_mm']):.3e} | {float(r['actual_NN_ray_shift_max_mm']):.5f} | {float(r['forward_pair_max_mm']):.5f} | {r['output_sub3px_ridge_N']} |" for r in gg)
    current=dom[-1];d=current;L=d['L_mm'];O=d['O_mm'];maxerr=max(float(r['analytic_max_mm']) for r in gg)
    write('TECHNICAL_REPORT.md',f'''# TASK-E3-N0-GATE-A2-PROJECTIVE-CLEANUP-001

日期：2026-11-02（Asia/Shanghai）。父提交`4b60db5d9402c2bb87692ba3b2b7819f3c7c1423`；独立分支`exp/TASK-E3-N0-GATE-A2-PROJECTIVE-CLEANUP-001`。

本轮复用Gate A相机、投影/CAD、等比例裁剪与公制域规则，在106,098点派生基线上冻结六源候选协议。共发现4,451个异常标记，预算内审查2,810点，形成14,050条观察证据；新增223点只在新副本无效化，原9个未决点全部保留。全包候选域由29.641缩至27.959mm，128³对应0.21843mm/格，全部105,875保留点均在域内。CORE主连通域及已有支持得到保护，但r04/r00有效域出现碎片及新窄ridge代理。r14旧2px门槛仍失败，三个极端重采样已定位为相邻原像素跨深度层，采样本身未造值，输入竞争仍存在。最终GATE_A2_FAIL，不将较小框当作验收通过，不替换历史基线，不启动Gate B。

## 范围、来源与冻结

人工转交的[批准任务](docs/APPROVED_TASK.md)是本轮授权。开始前实测上一轮HEAD为`4b60db5`、完整Git工作树clean；从该提交创建新工作树`/home/liu/ring_first_3d_e3n0_a2`。旧Gate A、其他历史工作树、正式相机、原HERO/Raw面、RGB/Mask、Ring CAD不写入。GPU/神经前向/训练/新HERO/新TSDF/位姿优化/GT/Oracle均未执行。

只核对任务必要六源及旧交付SHA，不重审17源、不重跑旧Gate A。官方ShapeNet主权重严格CPU加载、三CORE六对及18条件性对的解析投影证明直接继承旧结果，不重新构造模型。旧投影CSV的全部原点分母与SHA保留；A/K/c2w逐数组未变，本轮输入只是原ID子集，所以旧24对代数合同仍适用。[CODE_REUSE_MATRIX.md](CODE_REUSE_MATRIX.md)逐项说明真实路径、精确函数和未执行入口。

全部五个Camera Gate pilot状态继续为`INSUFFICIENT_EVIDENCE`；CORE仍按历史**条件性**使用。r14未完成独立Camera Gate，禁止其否定其他来源。8px轮廓余量只能缓冲已知像素偏差，不能认证完整相机正确。真实背景首次表面未独立认证；所有轮廓反证仍是工程代理，**223点不能宣称为物理错误真值**，A2副本没有升级为正式输入。

原106,144点、上轮106,098点和本轮105,875点分母分别保存；原坐标/源索引/Native Pixel ID在LOCAL_ONLY的`local_results/ALL_ORIGINAL_IDENTITIES.npz`中完整保留，SHA见[DERIVED_INPUT_LINEAGE.json](DERIVED_INPUT_LINEAGE.json)。原点数据未被小框裁掉。

## 固定候选池

[A2_PREREGISTERED.json](config/A2_PREREGISTERED.json)在发现候选前冻结，SHA=`8edf9e9d0a255d0b47d120323cd52fa6d8c4d417b9834f08ad0399b3eb7b51b3`；决策代码亦有运行前SHA。候选包括：上一轮9点、每源六轴极值、距当前全体原点轴界≤0.25mm、合法4邻域跳深≥1mm、或距自身原始Raw面>1mm且Mask边缘≤2px。0.25/1mm沿用既有支持和Raw诊断尺度，跳深取4×0.25mm；这些只提出候选，不作删除依据。

每源最多512点，按上述优先级、同级Pixel ID排序，不按最终效果调整。9点和每源极值强制纳入。原生4邻域明确排除图像wraparound和无效邻居。审查2810/106098=2.6485%，另1641个已标记异常未进入预算，全部保留；未标记点也全部保留。完整发现表[CANDIDATE_DISCOVERY_ALL_FLAGS.csv](CANDIDATE_DISCOVERY_ALL_FLAGS.csv)保留未选标记；[CLEANUP_CANDIDATES.csv](CLEANUP_CANDIDATES.csv)为实际审查池。

| 来源 | 原始N | 上轮基线N | 发现 / 审查 / 未审查 | 新增排除N及基线比例 | 本轮保留N | 射线面积代理排除比例 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
{per}

面积代理为各原生像素`Z²/(fx fy)`的求和，只是局部相机射线脚印，不是真实曲面面积、组织体积或物理覆盖率。新增排除223/106098=0.21018%；CORE排除49/50265=0.09748%，新增方向排除174/55833=0.31164%。不把高像素保留率当作真实表面完整性的充分证据。

## 投影证据与保留机制

实际调用原`unproject`、`vis.project_camera`、D0 `cast(ringscene())`和冻结K/c2w。毫米轴向Z直接与CAD首次命中轴向参数比较，epsilon=0.002mm。原生352×640与归档360×640使用冻结半像素K映射，原Mask按既有语义查询。

每个候选投到其他5源：图内、正Z、BG且在Polyp轮廓外>8归档像素、无CAD首交遮挡，方可给条件性轮廓反证。合法深度支持容差0.25mm；沿用原归档深度，同时要求当前原生有效域仍合法，**原生或归档任一近深度均保护**，减少离散化导致的假反证。r14近深度可否决排除，但不认证其相机。

先保留近深度支持D；没有D但任何合格观察源有Polyp内部层竞争，归B保留；其后才允许两个不同View Partition块的轮廓反证形成A派生排除；其他C/Unknown保留。ref08/r04共享B3只计一方向；共享RGB不代表统计独立。CORE内部>2px且距自身Raw≤1mm的连续主体也强制保护。Ring/CAD、图外、边界不确定、无效深度和层竞争都不能作为否定票。

| 分类（候选分母2810） | 数量 | 动作 |
| --- | ---: | --- |
| A 条件性强轮廓代理 | 223 | 新派生副本depth=0、valid=False；Mask不变，输入为Unknown |
| B 深度层竞争 | 1929 | 全保留，不平均成一层 |
| C Unknown | 300 | 全保留 |
| D 有近深度支持 | 358 | 全保留 |

[逐观察证据](PROJECTIVE_CLEANUP_EVIDENCE.csv)有14,050行；[逐点决策](PROJECTIVE_CLEANUP_DECISIONS.csv)保留原ID、资格、CAD、反对块和支持/竞争来源。223个排除点均无近深度支持和内部层竞争；不使用E3-C FREE_SPACE标签删点，不运行历史融合。9个P47–P55全部为B保留；其中P48/native78442的Y=17.098526mm仍决定当前Y上界，P50/native79722还是r00极端重采样所选原像素。没有因它们妨碍缩框而删除。

## 三阶段统一模型域

精确复用`make_domain`：全部保留XYZ加原CAD，边距`max(2mm,10%最大跨度)`，立方边长向上取整至0.001mm；统一128³，不按视角缩放。25.735mm只是旧诊断框，不是目标。

| 输入阶段 | 合法保留N | L mm | 体素mm | Ring外径格数 | 保留点出界N |
| --- | ---: | ---: | ---: | ---: | ---: |
{domains}

本轮候选`O_mm={O}`，`L_mm={L}`，`X_model=(X_mm-O_mm)/L_mm`；全部源旋转不变，中心和深度按同一L变换。Ring逆变换最大{d['ring_inverse_max_mm']:.3e}mm，恢复外径{d['ring_inverse_outer_mm']:.8f}mm。全部保留点及9点未决都在域内。旧模型域、上轮派生域均原样保存；新候选未正式冻结。[MODEL_DOMAIN_COMPARISON.json](MODEL_DOMAIN_COMPARISON.json)含全部矩阵；[FINAL_BOUNDARY_POINTS.csv](FINAL_BOUNDARY_POINTS.csv)明确记录新边界锚点，包括未经本轮审查但继续保留的新极值。没有第二轮搜索边界点。

## 有效表面保护与清理副作用

全部未排除深度/valid值逐数组bitwise未变；已识别支持、内部层竞争、1641个未审查异常及9点全保留。三个CORE原生/裁后主连通区域大小保持不变；原生分量数均2→2。该工程检查证明未破坏已保护主体连通区域，不能认证所有边缘组织物理正确或所有独有侧面完整。

**副作用不能隐藏：**r04原生分量2→4，增加两个<10px碎片，裁后2→3；r00原生2→3，增加一个小碎片，裁后仍2。有效域sub3px ridge代理从r04的0→5、r00的0→65。它们来自局部无效化后的有效域边缘/碎片，原Mask没改；这些不自动证明真实细柄被损害，但冻结门槛确实不满足。未二次删除碎片、闭运算补洞或改标签制造PASS。[VALIDITY_TOPOLOGY_COMPARISON.csv](VALIDITY_TOPOLOGY_COMPARISON.csv)保留全部前后值，Fig4最后一行展示新失败。

## r14薄结构

逐旧数据身份核对：真实失败像素为crop **(99,144)**，映射native **(282,215)**、archive(282,219.8977)。旧报告叙述写(99,143)有1行偏差；旧JSON/NPZ身份及2px数值正确，历史结果不覆盖。本轮最初诊断也沿用了文字坐标，发现它无效后仅修正诊断读取，不动清理/裁剪/阈值；初值和错误记录在[INITIAL_THIN_DIAGNOSTIC_ISSUE.json](config/INITIAL_THIN_DIAGNOSTIC_ISSUE.json)。

真实RGB显示该点邻近Ring与Polyp边缘；原生Mask存在单像素边界凸出，选中点自身宽度代理2px但不是原生局部ridge，裁后变成局部ridge。它仍在输入中，原深度=裁后深度 **39.080193mm**，本轮未排除。原生9×9有效29点、裁后9×9有效23点；两个窗对应不同尺度，不能直接用29−23推导真实表面丢失。原生9×9深度38.13247–47.78245mm，存在边缘深度变化。

证据更符合离散角点代理，但不能据此断言真实细柄不存在；保留`THIN_STRUCTURE_UNRESOLVED_BY_CROP`及旧3px FAIL。提出v0.2候选：区分“所有有效域距离变换角点”与“经原生身份、真实RGB/人工确认的解剖细结构”，后者才应用解剖宽度标准，同时单独报告采样拓扑/源身份保留。**仅提议，不替代现有标准，未用它制造PASS。**

## 最近邻深度：三个极值已解释、竞争未消失

| 来源 | 原(native u,v,Z) | 实际选中原像素(u,v,Z) | 轴向跳变mm | 原点到最近输出配对XYZ误差mm | 输出射线对所选原点偏移mm |
| --- | --- | --- | ---: | ---: | ---: |
| ref03 | (508,203,30.1083) | (509,203,42.6002) | 12.4919 | 13.4207 | 0.0510 |
| r04 | (282,183,32.7542) | (281,183,44.3544) | 11.6002 | 11.6390 | 0.0471 |
| r00 | (363,124,32.9416) | (362,124,52.3146) | 19.3731 | 19.5574 | 0.0529 |

三者都来自相邻1原像素的大深度跳变，原点ID没有被输出格点直接取到；正向将这个未采到点配给邻近输出格点时，该格点的逆最近邻却取了另一真实原像素。这解释了巨大正向配对误差。实际逆采样身份完全正确、深度与被选原生像素精确相同，没有双线性混合；相对于所选源点，输出射线离散位置只移动约0.05mm。**13–20mm不是坐标仿射错误，也不能据此当作采样无风险。**

竞争层仍可能被NeuralFusion当成合法输入表面，近邻层会在当前分辨率漏采。本轮没有足够证据认证所选远层一定错误；尤其r00所选点就是保留的P50。三处极值在A2后仍完全存在，不能以删除少量别的点宣称解决。

| 来源 | 解析XYZ最大mm | 实际逆NN射线偏移最大mm | 正向配对最大mm | 裁后sub3px ridge N |
| --- | ---: | ---: | ---: | ---: |
{geometry}

六源解析最大{maxerr:.3e}mm，原A/K完全相同，非法语义深度非零数均0。有限修订建议只是**给原生1mm跳变采样脚印输出不确定性与两源ID记录**，交PM决定是否需要Unknown门控或分层策略。没有改变当前采样器、没有新增深度、没有自动屏蔽争议层；深度竞争未解决是诊断开放问题，**不是新增的正式硬门槛**。

## 验证、失败与复现

[A2_CONTRACT_TESTS.csv](A2_CONTRACT_TESTS.csv)：37项工程/保护检查PASS，旧3px硬门槛FAIL，竞争层消失这一诊断问题FAIL（非新增正式门槛）。决策代码/参数冻结SHA保持；source DAG、K/c2w、Ring CAD、原文件及历史Gate A交付SHA保持；{protect['worktree_N']}个历史工作树未变，{protect['asset_checks_N']}项源/旧交付/旧本地资产SHA核对通过。没有模型权重读取或神经模块import。

安全重放在新`runtime/replay_verification`目录完成，**7份关键CSV逐字节一致**，没有覆盖正式或历史输出。详见[REPRODUCE.md](REPRODUCE.md)。大NPZ只留本地并列SHA；四核心PNG、小表、源码/配置上传独立分支。构建过程的稀疏工作树目录缺失、错误系统Python、过严守卫对GT审计Markdown的误拒绝、r14文字坐标差1行均记录在[FAILURE_LEDGER.md](FAILURE_LEDGER.md)，不以修改科学标准处理。

## 四张核心图

![六来源异常候选](figures/Fig1_Six_Source_Candidates.png)
![逐点跨视角证据](figures/Fig2_Projective_Evidence.png)
![模型域及分辨率](figures/Fig3_Domain_Resolution.png)
![保留失败与未决](figures/Fig4_Residual_Engineering.png)

所有RGB为真实源图并叠加冻结Mask/CAD；三维点均由原HERO恢复。二维图中黑色CAD是明确的遮挡覆盖层，三维为原实体三角面；没有纹理平面、补面或NeuralFusion输出。点云为显示预算确定性抽样，全部数字使用完整对应分母。

## 七个结论与停止

1. 新增**223点**符合预冻结的条件性跨视角轮廓反证代理；这是派生工程清理，不是223个物理真错点认证。
2. 全包候选域**27.959mm**，体素**0.2184296875mm**，Ring约56.769格；全部105875保留点包围，9点未决保留。不追25.735mm。
3. 已识别支持、层竞争、未审查和CORE连续主体得到工程保护；**无法认证所有真实独有侧面**。r04/r00有效域出现副作用，已报失败，未藏掉。
4. r14的2px问题**仍未决**，真实旧点已按身份复核；不把它直接称为细柄，也不豁免旧3px门槛。
5. 极端误差由跨1px原生深度跳变及正向身份配对造成；逆NN取值正确，但**原始竞争层仍影响未来输入**，未用平滑或删争议层解决。
6. **Gate A不具备整体PASS条件。** 旧硬门槛仍失败，A2候选不会自动替换106098点基线。
7. **当前不建议直接申请正式Gate B运行。** 先交PM审阅r14标准是否需版本化、有效域碎片副作用和深度竞争的可接受性，再决定是否接受带限制输入/另行批准有限修订。即便未来获准探索，也应保留三阶段输入对照和这些失败，不能宣称本轮已经PASS。

最终状态：**GATE_A2_FAIL**。[机器验收](GATE_A2_ACCEPTANCE.json)同时区分任务执行完成和工程门槛未达成。本轮停止，等待PM/研究者审计；Gate B没有自动启动。

## 固定审计表

| 审计项目 | 必须汇报 |
| --- | --- |
| 目标组数 | 1物理组，G01_004单视频，固定6来源 |
| 本算法独立成功 | 1/1组产生独立A2派生候选/诊断；整体GateA2通过0/1；测量/神经重建NOT_RUN |
| 本算法失败 | G01_004：旧薄结构硬门槛不满足、新有效域碎片/窄ridge；深度竞争未消失。测量误差NaN |
| 历史测量值回退 | 0；无S0、V2预测、旧直径或融合结果填补 |
| 失败组及具体原因 | FAILURE_LEDGER、Fig4、逐点决策、R14/重采样/拓扑CSV；科学失败均保留 |
| 最终统计样本 | 原106144、上轮106098、A2候选105875分列；候选审查2810/106098、未审查异常1641；真实物理GT评价样本0 |
| 是否使用GT选择算法 | 否；先冻结统一规则与源码SHA；不读取GT/Oracle/Dxy。条件性代理不冒称物理准确性 |
''')
    write('FAILURE_LEDGER.md','''# FAILURE_LEDGER

| ID | 类型/范围 | 实际发现 | 处理及证据 |
| --- | --- | --- | --- |
| F01 | 旧硬门槛 / r14 | crop(99,144)宽代理2px<3；解剖身份未认证 | 原ID/深度保留，旧FAIL不变；R14_THIN_STRUCTURE_DIAGNOSIS.json、Fig4第一行 |
| F02 | 清理副作用 / r04,r00 | 原生小分量增加；裁后新增5/65个sub3px ridge | 不二次删点或补洞；VALIDITY_TOPOLOGY_COMPARISON.csv、Fig4末行；A2未提升基线 |
| F03 | 输入竞争 / ref03,r04,r00 | 相邻原像素跨11.6–19.4mm深度层，正向配对13.42/11.64/19.56mm仍存在 | 逆NN身份/深度正确；保留层、不平滑；RESAMPLING_FAILURE_DIAGNOSIS.csv、Fig4。诊断开放问题，不新增硬门槛 |
| F04 | 未决 / P47–P55 | 其他视角落于Polyp内部且存在层竞争 | 9点全保留；P48仍决定Y界，P50仍为r00采样极值；PROJECTIVE_CLEANUP_DECISIONS.csv |
| F05 | 审查预算 | 4451个发现标记只审2810，1641未审 | 全保留；CANDIDATE_DISCOVERY_ALL_FLAGS.csv；不扩大阈值搜索 |
| F06 | 可见性资格 | CORE条件性；pilot仍INSUFFICIENT_EVIDENCE；真实BG表面未独立认证 | 轮廓票为代理，不认证物理真错；r14不否定其他源；不做相机优化 |
| F07 | 真实表面保护未能认证 | 高保留率/CORE连通域不等于独有侧面物理完整 | 区分工程保护与物理认证，无GT/Oracle；GATE_A2_FAIL，不建议直接GateB |
| E01 | 工作树初始化 | --no-checkout后sparse-checkout缺新worktree/info，命令退出128 | 只建新工作树info目录后完成；旧工作树未变 |
| E02 | 解释器 | shell python没有pathlib，元数据读取立即失败 | 后续固定复用既有.venv/bin/python；无数据计算/环境修改 |
| E03 | 守卫误拒绝 | 旧规则把GT_ISOLATION_AUDIT.md报告名当GT | 文件读取前拒绝；只对白名单该Markdown的只读访问放行，其余GT和写保护仍生效；common.py |
| E04 | 诊断坐标 | 旧叙述r14(99,143)差1行，最初A2诊断复用了该文字 | 从旧JSON/NPZ身份修正为(99,144)/native(282,215)，仅重做该诊断；config/INITIAL_THIN_DIAGNOSTIC_ISSUE.json |

没有参数搜索、第二轮清理、GPU、神经前向或正式推理失败被隐藏。原始Gate A结果没有覆盖。
''')
    write('CODE_REUSE_MATRIX.md','''# Executed code reuse

| 历史资产/函数 | 真实路径（相对新repo或绝对只读路径） | 本轮复用 | 未执行/保护 |
| --- | --- | --- | --- |
| Gate A common / guard / native | /home/liu/ring_first_3d_e3n0/experiments/TASK-E3-N0-GATE-A-COMPAT-CROP-METRIC-001/code/common.py | 精确AST绑定新R/REPO；只给该历史GT审计Markdown只读例外 | 不执行旧main；不写旧R；无神经import |
| Gate A baseline及清理证据 | 同上ROOT的DERIVED_INPUT_LINEAGE、PROJECTIVE_CLEANUP_EVIDENCE/DECISIONS、config/PROJECTIVE_CLEANUP_PREREGISTERED、POST_REVIEW_DOMAIN_SELECTION | SHA继承106098基线和46历史排除，保留9点身份 | 不重复删除46点 |
| make_crop / ridge_proxy | 同上code/crop.py | 精确函数、不改20%/16px ROI、nearest、K'=AK | 无双线性或新Mask |
| make_domain / wire_box | 同上code/metric_domain.py、human_review_figures.py | 精确域规则及线框可视化 | 不以25.735mm设目标 |
| source / mesh_scene / cast / ringscene / ringmesh | experiments/TASK-E3-D0-OPEN3D-TSDF-BASELINE-001/code/common.py | 通过Gate A精确AST复用；冻结CAD首交/相机 | 不调用TSDF integrate/体积接口 |
| HEROToTSDFAdapter | D0/code/hero_tsdf_adapter.py | 原生合法深度身份和公制转换检查 | 无新TSDF |
| unproject | /home/liu/polyp_research/ring_anchor_3d/experiments/ring_first_v1/scripts/common.py | 原K/c2w的精确历史反投影 | 不改相机 |
| scaled_intrinsics / project_camera / camera_rays / configure | visualization/real_p0_renderer.py | 直接导入、实际调用；含native/archive半像素关系 | 只读CPU |
| SameCameraScene | visualization/same_camera_scene.py | 原黑色CAD实体raycast/ring_image | 无合成纹理或补面 |
| View Partition、来源DAG、E3-A/B身份 | D0/HERO_TSDF_INPUT_MANIFEST.json、VIEW_COVERAGE_SELECTION.csv；E1/provenance/INPUT_ELIGIBILITY.json | 直接继承已审六源、上游RGB SHA与block，不重审全17源 | ref08/r04共享B3；Raw面只作原身份/距离候选 |
| Camera Gate资格 | experiments/TASK-CAMERA-GATE-G01-004-PILOT-001/CAMERA_QUALIFICATION.csv | 五pilot历史INSUFFICIENT_EVIDENCE原样输出 | r14不可否定他源；不优化位姿 |
| E3-C可见性设计 | /home/liu/ring_first_3d_e3c/experiments/TASK-E3-C-VISIBILITY-CONSENSUS-001/code/visibility.py | 沿用CAD/层竞争/Unknown不作否定的既有语义；实际cast由同源D0路径执行 | 不导入其17源main/资格，不消费FREE_SPACE_CONFLICT删除标签 |

所有实际抽取函数的源码SHA、AST SHA和行号见config/VALIDATION_REUSE.json。新增仅为候选枚举、保守证据归约、派生副本、诊断及组合图，不重新发明投影/反投影/射线。
''')
    write('REPRODUCE.md','''# Reproduce A2

基准：父提交4b60db5d9402c2bb87692ba3b2b7819f3c7c1423；六源顺序固定。必须拥有DERIVED_INPUT_LINEAGE列出的原文件和旧Gate A本地派生缓存，按config/PROTECTED_START.json核对SHA；不下载模型、不从Raw面或其他预测补深度。固定Python=/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python，复用历史Open3D vendor。主环境不改。

从新任务repo根目录执行；output必须是尚不存在的本任务runtime子目录：

```bash
/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python -B experiments/TASK-E3-N0-GATE-A2-PROJECTIVE-CLEANUP-001/code/replay.py --output /home/liu/ring_first_3d_e3n0_a2/experiments/TASK-E3-N0-GATE-A2-PROJECTIVE-CLEANUP-001/runtime/replay_new
```

入口原样复制已冻结协议；仅依次执行discover、cleanup、validate_inputs，拒绝覆盖已有输出。不重新执行旧Gate A或模型加载。复现本轮2,810候选、223新排除、9保留、105875输入、27.959mm域及诊断。7份CSV和正式结果逐字节SHA对照。已实测runtime/replay_verification/REPLAY_VERIFY.json全部一致。

原始执行次序为preregister.py → discover.py → cleanup.py → validate_inputs.py → figures.py → audit.py；preregister只在父HEAD且无协议时运行一次，禁止在最终HEAD重写历史冻结记录。审计/报告入口不会启动推理，但无需为复现数值而再次运行。r14诊断从旧HUMAN_REVIEW_CONTEXT读取真实(99,144)，不依赖旧叙述笔误。

LOCAL_ONLY：原始/基线/本轮派生深度、全部原ID世界坐标、crop NPZ、重放缓存。LOCAL_RESULTS_INDEX记录路径/bytes/SHA。上传只有任务代码、配置、CSV/JSON、报告和四PNG。没有神经网络前向、GPU、GT、相机拟合或新TSDF。所有失败是预期保留结果，复现成功不意味着Gate A通过。
''')
    save('config/EXECUTION_ISSUES.json',dict(worktree_sparse_info='missing new worktree info folder; created only new metadata directory',default_python='pathlib ImportError before data read; fixed interpreter path',isolation_markdown='inherited GT_ filename rule blocked literal audit report; explicit read-only exception only',r14_coordinate_issue=asset(R/'config/INITIAL_THIN_DIAGNOSTIC_ISSUE.json'),parameters_changed_after_results=False,cleanup_repeated=False))
    print('REPORTS_WRITTEN',flush=True)

if __name__=='__main__':main()
