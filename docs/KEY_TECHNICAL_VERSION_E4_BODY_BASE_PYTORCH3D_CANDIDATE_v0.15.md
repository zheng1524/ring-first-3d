# E4关键技术候选v0.15：基底裁切与双初始化PyTorch3D

状态：AWAITING_HUMAN_REVIEW，未升级正式主线。

任务：[TASK-E4-BODY-BASE-PYTORCH3D-010报告](../experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/runs/BODY_BASE_PYTORCH3D_010/TECHNICAL_REPORT.md)，预注册5aeec8b，继承009冻结九例和原Ring-First/HERO/Mask/CAD坐标，不读取GT、不改DXY。

修复ROI平面的正负等价与共同锚点距离，G09 176.042→3.958度；G05仍WEAK。七例广接触统一精确裁切冻结B，上部原顶点逐位不变；推断盖与观测面隔离。球体使用官方ico_sphere3，由原始观测独立定位和等比缩放，不复制B半轴。

统一Ring-Aware+D2E3深度/边界权重/相对形状保护与100global6+200local日程，P/S共享观测和物理归一。18条件均执行，P/S各4/9完成300步，10条件工程保护停机，最终NaN。八次超过2mm单步、两次体积紧急退化；未调参重跑。物理安全筛查只有S的G02/G04/G09通过，P完成输出仍有Ring相交或自交。球体仍有估计基底下的未知闭合，不能称三维真实恢复。

重要限制：切平面边界约束不保证上部整个网格保持半空间或无自交，GLOBAL6无约束SGD/动量对不同初始化不够稳定。仅G02/G04共同完成，不足以宣称P或S全九例更优。代码/图/失败和所有本地网格状态保留。18/18完整更新目标未达成，停止等待人工审查，不替换任何正式主线，不自动进入SDF或相机优化。
