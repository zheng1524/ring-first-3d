# E3 来源组织提案（非优化执行授权）

来源和阈值在下游方法输出之前固定。全来源清单为40份 native HERO、3张照片及51条主派生记录，共94条；其中36份主目录原始面身份已验证，另外4份目录来源仅做筛查。家族按全部真实上游 RGB SHA 的共享连通分量归并；每视频主源同属一个相关家族，不意味着几何完全相同或没有互补信息。派生结果不能多票。

| 视频 | 全部 / 参考筛查 / 代表 | 方向格 代表/全筛查 | 法向格 | 0.5mm空间格 | 共视组件 |
| --- | --- | --- | --- | --- | --- |
| G01_004 | 11/3/3 | 3/3 | 33/33 | 1706/1706 | 1/1 |
| G01_005 | 9/8/4 | 4/7 | 38/38 | 1620/1873 | 1/1 |
| G06_004 | 5/4/3 | 3/4 | 15/15 | 680/684 | 1/1 |
| G07_004 | 5/0/0 | 0/0 | 0/0 | 0/0 | 0/0 |
| G08_005 | 6/2/2 | 1/1 | 20/20 | 1627/1627 | 1/1 |

相机方向为 `(camera_center - frozen_ROI_center)/norm`，不是光轴；ROI中心是完整包络中心，长尾会影响该规约，不是解剖中心。另报光轴角、平移基线和共投影。方向10°分格；原面法向12×6方向格，非长边原面面积达到源总合格代理面积1%才记格；空间格为非长边原面重心0.5mm格。相机格不能代替实际几何法向/空间格，后两者仍是 raw HERO 支持代理。

## G01_004

- `G01_004_ref03`：CORE
- `G01_004_ref08`：CORE
- `G01_004_ref13`：CORE
- `G01_004_new_r00`：UNQUALIFIED
- `G01_004_growth_r04`：UNQUALIFIED
- `G01_004_growth_r10`：UNQUALIFIED
- `G01_004_growth_r07`：UNQUALIFIED
- `G01_004_growth_r14`：UNQUALIFIED
- `G01_004_growth_r12`：UNQUALIFIED
- `G01_004_growth_r06`：UNQUALIFIED
- `G01_004_growth_r01`：UNQUALIFIED

筛查参考对 ROI 方向夹角 8.50–21.07°，共视图组件=1。边需双向各≥10%固定采样原顶点在对方原面/Mask内且不被CAD挡住；每源最多2048个均匀原索引点。连通仅是几何候选，不认证物理对应。

## G01_005

- `G01_005_raw00057`：CORE
- `G01_005_raw00459`：CORE
- `G01_005_raw00745`：CORE
- `G01_005_new_r04`：UNQUALIFIED
- `G01_005_growth_r03`：RESERVED
- `G01_005_growth_r20`：BRIDGE
- `G01_005_growth_r12`：RESERVED
- `G01_005_growth_r15`：RESERVED
- `G01_005_growth_r11`：RESERVED

筛查参考对 ROI 方向夹角 2.77–36.70°，共视图组件=1。边需双向各≥10%固定采样原顶点在对方原面/Mask内且不被CAD挡住；每源最多2048个均匀原索引点。连通仅是几何候选，不认证物理对应。

## G06_004

- `G06_004_ref04`：CORE
- `G06_004_new_r00`：BRIDGE
- `G06_004_growth_r06`：UNQUALIFIED
- `G06_004_growth_r01`：RESERVED
- `G06_004_growth_r03`：BRIDGE

筛查参考对 ROI 方向夹角 3.30–16.69°，共视图组件=1。边需双向各≥10%固定采样原顶点在对方原面/Mask内且不被CAD挡住；每源最多2048个均匀原索引点。连通仅是几何候选，不认证物理对应。

## G07_004

- `G07_004_ref04`：UNQUALIFIED
- `G07_004_new_r06`：UNQUALIFIED
- `G07_004_growth_r00`：UNQUALIFIED
- `G07_004_growth_r02`：UNQUALIFIED
- `G07_004_growth_r01`：UNQUALIFIED

## G08_005

- `G08_005_ref04`：CORE
- `G08_005_new_r00`：UNQUALIFIED
- `G08_005_growth_r03`：BRIDGE
- `G08_005_growth_r01`：UNQUALIFIED
- `G08_005_growth_r02`：UNQUALIFIED
- `G08_005_growth_r05`：UNQUALIFIED

筛查参考对 ROI 方向夹角 5.89–5.89°，共视图组件=1。边需双向各≥10%固定采样原顶点在对方原面/Mask内且不被CAD挡住；每源最多2048个均匀原索引点。连通仅是几何候选，不认证物理对应。

G01_004 只保留既有三参考作为条件性 CORE，没有合格新增桥。G01_005 在三 CORE 外按冻结贪心增加 growth_r20，仍有其他合法 RESERVED；代表集保留全部38个法向格，但只覆盖1620/1873空间格，不能声称无损替代8份参考。G06增加new_r00与growth_r03；G08两筛查源仅占同一个相机格，几何仍需分别看来源；G07无CORE，全部UNQUALIFIED。

规则保留既有 G01 三参考及其他已筛查旧主参考，再在G01最多4源/其他最多3源预算内，以新增空间格/法向格/相机格的全筛查集合归一化边际比例等权和贪心选桥，要求与已选源共视连通，同分按source_id排序。边际数见 `E3_MARGINAL_SOURCE_COVERAGE.csv`；没有读取SDF输出、GT或误差选择角色。

额外有界检索覆盖 G02–G05 四份旧 native HERO。G04/G05为Is/R10；G07为Is/R5但未合格。该目录中额外合格Is/R5=0，不把有界检索写成全磁盘不存在。G02参考曾筛查但上游链和原索引未获E1级认证，四份均未加入正式源集合。三张照片K候选/c2w空，METRIC_GEOMETRY_NOT_QUALIFIED，不使用历史候选配准。
