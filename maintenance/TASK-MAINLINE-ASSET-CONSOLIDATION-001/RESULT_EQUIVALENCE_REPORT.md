# 结果一致性

|模块|状态|与冻结结果比较|
|---|---|---|
|ring-first|PASS|相机矩阵max abs=0；分支身份相同|
|hero|PASS|新官方原生推理；深度逐bit一致，Raw FaceID/PixelID/顶点一致|
|body-initialization|PASS|G01/G03原始013容器SHA相同，V/F/F_solid/cap/boundary逐元素一致|
|body-update|PASS|保存的32节点变换经原Graph真实生成Mesh；最大误差1.7763568394002505e-15mm|
|stalk-growth-g01|PASS|新Boolean并集顶点误差0、面索引相同、投影变化误差0；自动门禁仍通过|
|stalk-growth-g03|PASS|新Boolean并集及投影同历史；PER_VIEW_PROTECTION仍拒绝，正式柄长NaN|
|a-to-b|PASS|RGBA、轴向深度、FaceID、重心、CAD深度和有效域逐bit一致|
|depth-supervised-pytorch|PASS|实际T30加权loss差0；梯度相对误差7.89843173677e-08|

全部容差在重放前冻结，见mainline/configs/REPLAY_TOLERANCES.json。前两次工程接线失败和源码/配置快照保存在REPLAY_PROTOCOL_REVISIONS；没有放宽容差。共享ARM.json的G03视图不能替代G01历史逐病例记录；重序列化INITIAL缓存与原始013 ZIP分别保存。

本轮是工程重放，Graph使用实际保存的节点参数、Sweep使用保存参数；没有重跑36轮/80轮训练，也没有根据HERO或GT新增Body更新。旧实验源码执行被audit guard拒绝，官方外部代码及原始数据通过清单管理。
