# 失败台账与未解决问题

本轮保留全部九例、所有拒绝候选和额外工程试跑，不通过改权重/评价分母/挑checkpoint制造PASS。

- **G01**：18/300接受，最终22个活动变量；候选拒绝主要为[('FULL_FIT_OBJECTIVE', 4610)]。保留视角IoU变化+0.0158，固定深度覆盖变化-0.0299。原有/最终CAD抽样穿入0.000000/0.000000mm；[完整图](figures/full/G01_Optimization_Detail.png)。
- **G02**：100/300接受，最终54个活动变量；候选拒绝主要为[('FULL_FIT_OBJECTIVE', 3407), ('STEP_TRUST', 4)]。保留视角IoU变化+0.1907，固定深度覆盖变化+0.0000。原有/最终CAD抽样穿入0.000000/0.000000mm；[完整图](figures/full/G02_Optimization_Detail.png)。
- **G03**：21/300接受，最终22个活动变量；候选拒绝主要为[('FULL_FIT_OBJECTIVE', 3962), ('RING_WORSENING', 674), ('STEP_TRUST', 5), ('RING_CONTAINMENT_WORSENING', 3)]。保留视角IoU变化-0.0006，固定深度覆盖变化+0.0000。原有/最终CAD抽样穿入0.019953/0.000000mm；[完整图](figures/full/G03_Optimization_Detail.png)。
- **G07**：111/300接受，最终54个活动变量；候选拒绝主要为[('RING_WORSENING', 5403), ('FULL_FIT_OBJECTIVE', 148), ('RING_CONTAINMENT_WORSENING', 46), ('STEP_TRUST', 39)]。保留视角IoU变化+0.0253，固定深度覆盖变化+0.0527。原有/最终CAD抽样穿入0.008739/0.000010mm；[完整图](figures/full/G07_Optimization_Detail.png)。
- **G04**：4/300接受，最终6个活动变量；候选拒绝主要为[('FULL_FIT_OBJECTIVE', 4767), ('STEP_TRUST', 2)]。保留视角IoU变化+0.0002，固定深度覆盖变化+0.0000。原有/最终CAD抽样穿入0.000000/0.000000mm；[完整图](figures/full/G04_Optimization_Detail.png)。
- **G05**：114/300接受，最终54个活动变量；候选拒绝主要为[('RING_WORSENING', 4363), ('FULL_FIT_OBJECTIVE', 903), ('STEP_TRUST', 20), ('RING_CONTAINMENT_WORSENING', 6)]。保留视角IoU变化+0.0522，固定深度覆盖变化+0.0117。原有/最终CAD抽样穿入0.010718/0.000010mm；[完整图](figures/full/G05_Optimization_Detail.png)。
- **G06**：32/300接受，最终22个活动变量；候选拒绝主要为[('RING_WORSENING', 5732), ('FULL_FIT_OBJECTIVE', 1079), ('STEP_TRUST', 10), ('RING_CONTAINMENT_WORSENING', 9)]。保留视角IoU变化+0.0193，固定深度覆盖变化+0.0039。原有/最终CAD抽样穿入0.015711/0.000010mm；[完整图](figures/full/G06_Optimization_Detail.png)。
- **G08**：13/300接受，最终22个活动变量；候选拒绝主要为[('NEW_CAD_COLLISION', 7030), ('RING_WORSENING', 60), ('STEP_TRUST', 15), ('RING_CONTAINMENT_WORSENING', 8)]。保留视角IoU变化+0.0063，固定深度覆盖变化+0.0098。原有/最终CAD抽样穿入0.000000/0.000000mm；[完整图](figures/full/G08_Optimization_Detail.png)。
- **G09**：35/300接受，最终22个活动变量；候选拒绝主要为[('FULL_FIT_OBJECTIVE', 4399), ('STEP_TRUST', 5)]。保留视角IoU变化-0.0912，固定深度覆盖变化+0.0000。原有/最终CAD抽样穿入0.000000/0.000000mm；[完整图](figures/full/G09_Optimization_Detail.png)。

## 工程记录

1. 初始化预检查首次缺少self_intersections导入，发生在任何正式更新前，补导入后所有检查通过；没有改变评价阈值。
2. 原始RelativePrior保留孤立底盖中心的弱顶点先验；底盖面从不参与真实观测。协议“底盖不进正则”的概述须按面/顶点区分，详细审计已说明，没有秘密改损失。
3. V1已知G01额外300提案/12接受，G02中断真实步数仅以已存checkpoint/log为下界，不捏造。源码、配置、模型和原路径映射完整保留。
4. 最初动量上升猜测不成立；ASCENT_DIRECTION_DIAGNOSIS和DIRECTION_FD_DIAGNOSIS保留了负方向导数及真实active-set损失跳变。统一纯梯度重启是一次工程修复，不是对某组单独调参或额外科学对照。
5. 继承JSON有未执行的旧mode/stop/reuse_B字段，实际以stages/trust/optimizer和冻结代码为准，原字节保留；CONFIG_IMPLEMENTATION_AUDIT独立说明，不用旧volume范围冒充本轮守卫。
6. 真实相机/原生深度和组织基底仍有不确定性，历史资格标签只记录，不阻塞。有限预算/局部约束下的停滞不是物理不可行的证明。
7. 冻结后分量回放首次在G02严格1e-7重放断言中止，原日志保留；后续只完成九例诊断并逐项保留FAIL，不改阈值。G02差异1.64844e-6全部在轮廓项，原因未完全定位。初次回放调用旧RelativePrior的同内容support缓存写入，所有冻结文件SHA核对完全一致；当前诊断入口只对照原缓存，不再写入。预测/输入/历史文件内容未改变。
8. G09硬Mask评价明显倒退，G02深度代价上升，G01深度覆盖下降，G04几乎无实质位移；这些结果不被总损失下降或全部模型有输出所抵消。

完整候选原因计数、覆盖变化和独立几何见FAILURES、NINE_CASE_RESULTS与逐参考表；每个病例的原图与模型证据均链接在上文。
