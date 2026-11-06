# 失败台账

本轮所有18条件均入组，不因历史Gate拒绝。十个未完成条件的FINAL300为NaN，最后安全状态仅诊断；八个完成条件也按真实物理检查保留失败。

| 条件 | 拒绝候选步 / 最后安全步 | 单步最大位移mm | 候选/初值体积比，仅诊断 | 原因 |
|---|---|---|---|---|
| G01 S | 66 / 65 | 2.2558 | 1.112634 | SINGLE_STEP_OVER_2MM |
| G03 P | 4 / 3 | 2.0973 | 0.777516 | SINGLE_STEP_OVER_2MM |
| G03 S | 1 / 0 | 2.2349 | 0.835760 | SINGLE_STEP_OVER_2MM |
| G07 S | 97 / 96 | 2.0008 | 0.978141 | SINGLE_STEP_OVER_2MM |
| G05 P | 44 / 43 | 2.1294 | 0.659558 | SINGLE_STEP_OVER_2MM |
| G05 S | 8 / 7 | 2.6617 | 0.890285 | SINGLE_STEP_OVER_2MM |
| G06 P | 50 / 49 | 1.8710 | 0.001712 | VOLUME_EMERGENCY_RANGE |
| G08 P | 18 / 17 | 2.6112 | 1.579634 | SINGLE_STEP_OVER_2MM |
| G08 S | 1 / 0 | 3.0000 | 0.706792 | SINGLE_STEP_OVER_2MM |
| G09 P | 40 / 39 | 0.1797 | 0.069949 | VOLUME_EMERGENCY_RANGE |

全部10次中断都在GLOBAL6阶段：8次超过固定2mm单步紧急线，2次体积跌出0.1–10紧急范围。该范围不是体积守恒目标，更不是真值；它阻止继续生成极端退化候选。不能把中断称为充分300步后的科学失败。没有改门槛重跑或把旧B/S替换失败路线。

冻结后零optimizer.step的只读回放用真实UNSAFE参数/动量重建失败前状态，位置最大差约几微米以下，逐项重算轮廓/形状/深度梯度。[失败提案回放](metrics/FAILED_PROPOSAL_GRADIENT_REPLAY.json)

- G03-S首步选中的两个FIT无HERO，轮廓梯度本身就产生2.235mm候选；不能把所有中断归咎HERO。
- G08-S首步约3.000mm，轮廓与深度全局参数梯度夹角余弦约0.59；G01-S、G07-S等失败提案中二者也大致同向。因此“梯度互相冲突”不是普遍必要原因，固定步长/动量和尺度响应更直接。
- G09-P拒绝时当前全局梯度范数约0.005，而实际动量缓冲约0.077；仍在推动已很薄的保留体收缩，候选体积比0.070。G06-P候选体积比约0.0017。仅靠轮廓与单面深度不足以阻止此类退化。

独立Blender/FCL/Open3D检查发现：8个完成输出中，P全部有几何失败：G01-P约0.0011mm CAD样本穿入；G02-P有5对非邻接自交；G07-P约0.444mm样本穿入且自交；G04-P有69对自交。S中G06有约0.0445mm CAD样本穿入，G02/G04/G09未检出CAD/自交/非流形问题。通过筛查的三个S仍不等于真实组织：大量球体顶点在估计基底下方，隐藏闭合没有真实观测认证。

G04-P第25步、G02-P第75步已检出自交，均早于释放顶点；G07-P第150步出现自交。G01-P中间有自交、最终消失但仍穿Ring，不能只看最终漂亮程度。基底边界投影与其余主体自由更新并不构成全网格非穿透/不自交保证，Ring遮挡损失也不是3D碰撞屏障。[首次保存自交阶段](metrics/FIRST_SAVED_SELF_INTERSECTION.json)


## 额外实施记录

- 平面单元测试第一版arccos对完全同向向量产生约1.2e-6°的数值伪角，未通过1e-6°测试。改用atan2叉积/点积稳定公式，未放宽阈值；旧源码/测试保留assets_index/PLANES_V1_ARCCOS.py.txt和PREFLIGHT_V1_ARCCOS_ZERO.json。发生在优化前。
- 初版阶段绘图的后缀匹配误把P50/P100/P200加载为P0，目视审阅发现后改为仅P0/S0精确匹配，重新从真实STEP文件画图。旧源码及坏图SHA见assets_index/VISUALIZATION_FAILURE.json；没有修改任何预测/指标或重跑优化。交付验证单独检查阶段路径与内容。
- G05基底仍WEAK；G09虽然数值稳定，但内部点相对平面高度低且只有约62%在正侧，不能称真实解剖基底已恢复。
- 所有原生球体都没有截断，因此估计基底以下闭合与P的推断底盖/边界条件不同。这是初始化策略比较的已知混杂，不隐藏为完全同拓扑实验。
- 未检出NaN/OOM/坏文件；十个中断不能称工具链无法运行，也不能称完成了全部预定步数。

逐例完整图：

- [G01](figures/full/G01_Detailed.png)
- [G02](figures/full/G02_Detailed.png)
- [G03](figures/full/G03_Detailed.png)
- [G07](figures/full/G07_Detailed.png)
- [G04](figures/full/G04_Detailed.png)
- [G05](figures/full/G05_Detailed.png)
- [G06](figures/full/G06_Detailed.png)
- [G08](figures/full/G08_Detailed.png)
- [G09](figures/full/G09_Detailed.png)
