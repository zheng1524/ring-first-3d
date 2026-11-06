# 010失败机制只读复核

来源为010冻结报告、原始RUN/失败诊断表；本轮不重跑P/S，不覆盖历史。

010共有18条路线，仅8条完成300步，10条GLOBAL6阶段被紧急检查中断；8次单步超过2mm，2次体积数值塌缩。无OOM/NaN/Inf或输入缺失。2729次SGD更新中2719次通过原紧急检查，不能将其写成18条均完成。

旧优化器SGD(lr=1,momentum=0.9)，100步GLOBAL6后200步局部更新。未把候选实际毫米变化放入回溯接受机制，初始化不同、形状参数与毫米梯度尺度不同可造成危险大位移。该结论是优化器适配不足的工程证据，不证明完整PyTorch3D路线被否定。

|病例/路线|实际尝试/接受|失败候选最大位移mm|候选体积比（仅诊断）|原始原因|
|---|---:|---:|---:|---|
|G01/S|66/65|2.255776|1.112634|SINGLE_STEP_OVER_2MM|
|G03/P|4/3|2.097303|0.777516|SINGLE_STEP_OVER_2MM|
|G03/S|1/0|2.234944|0.835760|SINGLE_STEP_OVER_2MM|
|G07/S|97/96|2.000817|0.978141|SINGLE_STEP_OVER_2MM|
|G05/P|44/43|2.129412|0.659558|SINGLE_STEP_OVER_2MM|
|G05/S|8/7|2.661674|0.890285|SINGLE_STEP_OVER_2MM|
|G06/P|50/49|1.870959|0.001712|VOLUME_EMERGENCY_RANGE|
|G08/P|18/17|2.611236|1.579634|SINGLE_STEP_OVER_2MM|
|G08/S|1/0|2.999956|0.706792|SINGLE_STEP_OVER_2MM|
|G09/P|40/39|0.179733|0.069949|VOLUME_EMERGENCY_RANGE|

旧P的四个完整输出仍有CAD相交或自交；S的四个完整输出仅G02/G04/G09通过当轮几何筛查，仍不能称未知球体底面是真实表面。严格留出与固定观测分母不足以证明完整3D精度。

011对应修复：参数化C继承替代B直接裁切；正高度图约束指定半空间；受控Adam/回溯按实际mm位移与几何守卫接受；不可接受则恢复参数/动量时钟；局部谱自由度按固定门槛释放。保留旧2mm紧急线，不提高以允许危险候选；实际信赖域更小，不增加体积守恒目标。

011也可能因真实目标的硬命中/遮挡集合切换停滞，这与旧010危险大步是不同机制。二者均须保留，不用新模型漂亮程度倒推失败原因。

源文件SHA256：

- `/home/liu/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/runs/BODY_BASE_PYTORCH3D_010/TECHNICAL_REPORT.md`：`69783bdffe251a084ce62b293ab63e22432b12c86365c3e66262f159fcf98657`
- `/home/liu/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/runs/BODY_BASE_PYTORCH3D_010/metrics/FAILURE_DIAGNOSIS.json`：`cf1f2a486d6311170f86d6774382691acfdf49670a5d94937518407e695e5275`
- `/home/liu/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/runs/BODY_BASE_PYTORCH3D_010/metrics/RESULT.json`：`bf852b8f17ff9c1ce2ae0347a184eb9e4d8f1fbcac447e67d8aef7292c187be3`
