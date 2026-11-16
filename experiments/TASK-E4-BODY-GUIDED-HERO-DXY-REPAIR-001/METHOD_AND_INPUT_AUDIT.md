# 方法与输入审计（更正并完成）

原Phase0误将RAW initial_pose缺失当成无相机；正式FINAL_CAMERA_POOL在原资产目录中存在。旧报告/代码归档于provenance/SUPERSEDED_PHASE0，不能继续引用其“32缺位姿”结论。

| group | total | v004 | v005 | photos | native_pose | pool_formal |
| --- | --- | --- | --- | --- | --- | --- |
| G03 | 18 | 12 | 6 | 0 | 18 | 18 |
| G05 | 16 | 14 | 1 | 1 | 16 | 15 |
| G01 | 26 | 17 | 8 | 1 | 26 | 26 |
| G06 | 15 | 15 | 0 | 0 | 15 | 14 |

46个MAX源以view ID+target SHA精确匹配，29个OLD018使用其显式target_cache并验证RGB/Mask。75原生T均有效；18个与最终池C版本差异在VIEW_INVENTORY.csv逐源列明。原生352×640到360×640的K映射严格沿用半像素公式；从未用HERO XYZ/深度决定Body。全部Mask uint8类别0/1/2。DXY73文件接口+2照片缓存帧接口；所有输入、实际RGB/Mask字节SHA、K/T与Ring CAD见config/SOURCE_BINDING.json。

正式DXY与底层源码SHA已冻结；对照DT/AMS和Body-U均在全部预测冻结后读取。2个上游探索性相机仅作诊断，重复RGB不进入独立留出。跨视频不合并，照片单列。完整公平性/输入冻结检查见metrics/VALIDATION.json，数值一致性见metrics/NUMERICAL_CONTRACTS.json。

## 固定审计表

| 审计项目 | 必须汇报 |
| --- | --- |
| 目标组数 | 4独立物理组；75来源（74唯一RGB）；主分析每方案4组，附加005有2池 |
| 本算法独立成功 | E1=4/4、E2=4/4主组独立数值输出；附加各2/2池；完整科研验收0/4组每方案，不能当作测量正确 |
| 本算法失败 | 主组无数值输出失败；完整验收8/8主组方案失败；3单视角池×2方案为null/NaN；36初值有2个未收敛且排除主解 |
| 历史测量值回退 | 0；Body-U和旧DT+AMS只在预测冻结后作对照 |
| 失败组及具体原因 | [逐组失败台账](FAILURE_LEDGER.md)，关联候选、逐帧投影和图集 |
| 最终统计样本 | 仅独立成功主分析4组每方案；23张相同HOLDOUT（各池9/4/5/5）；全部75来源始终登记；不把来源数当独立组数 |
| 是否使用 GT 选择算法 | 否；GT未读，协议→DXY→视角/源码冻结→全部预测冻结→独立评价的SHA回执见provenance |
