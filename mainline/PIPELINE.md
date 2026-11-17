# 固定输入主线运行与数据流

1. run_ring_first.sh：真实Ring Mask + RGB地图 → 原RF5DoF/SIFT-PnP/yaw → OpenCV c2w/mm。数值解不当作pose GT。
2. run_hero.sh：真实四帧、冻结公制相机 → 官方MVSAnywhere/HERO → 352×640原生轴向Z → 真实Raw Mesh/FaceID/PixelID。checkpoint仅加载，不训练。
3. run_body_initialization.sh：原始EXACT013容器 → 同一initialize函数 → 固定拓扑/公制Body；E1/E2只保留独立参考，不能替换。
4. run_body_update.sh：同一初始Body + 保存的32节点旋转/平移 → 原Graph.mesh；同时检查Smooth ARAP能量。重放不是重新优化36轮。
5. run_stalk_growth.sh G01/G03：冻结STEP024、保存的5控制点/双轴 → 16站×16角RMF Sweep → Blender EXACT Union → 新投影/对应/Ring及完整几何验收。
6. G01保持自动接受；G03必须重现PER_VIEW_PROTECTION。内部弧不计柄长，正式G03仍NaN。根截面缺陷保持披露。
7. run_a_to_b.sh：原A三角面+原A RGB → 冻结B相机，B颜色/Mask仅在预测保存后评价。输出RGBA、FaceID、重心、深度和完整未匹配域。
8. run_depth_supervised.sh：原018真实native观测与初始Mesh → 原PyTorch3D首次命中/barycentric损失及梯度；与历史实际梯度数组比较，T28旧块另存。

以上是两个已验证区块：相机/HERO真实固定样本，以及EXACT013→保存Graph状态→保存Sweep→新几何/投影验收的checkpoint continuation。尚未将HERO反馈接入当前Body优化，也未执行新的从原图到训练收敛的科研全链。各区块身份与实际输入在清单中，不能将旧checkpoint重放说成重新训练。

运行脚本统一调用mainline/scripts/python.sh与ring_first_3d.mainline.cli。每次先校验源码、输入及运行库哈希，并禁止执行旧实验目录Python代码；输出不可覆盖。原Policy Preflight、Contracts、Reuse Audit、Smoke和247项回归已在此入口环境实际执行。
