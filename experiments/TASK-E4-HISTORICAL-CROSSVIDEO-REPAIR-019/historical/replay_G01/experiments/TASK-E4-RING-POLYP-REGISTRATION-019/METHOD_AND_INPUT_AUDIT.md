# 019 方法与输入实现审计

冻结输入：004沿用018实际8FIT+5HOLDOUT；005使用014全部55份相机/RGB/Mask，恢复`EXISTING_VIEWS`/`DERIVED_VIEWS`中的原生c2w，并逐项验证等于`ALL_VIEWS.T_original`，**排除014已叠加的跨视频修正**。输入保持条件资格；INSUFFICIENT_EVIDENCE等历史标签不被升级。005逐帧解码验证55/55真实像素；004读取018原帧/JPEG95完整链，声明帧号与实际帧号差异保留。8个HOLDOUT在搜索前固定；018主体和历史相机祖先可能使用部分评价图像，故仅本轮更新/选择独立，不宣称端到端完全独立。

R10实体CAD中心线半径5.6mm、线材半径.6mm。DXY只读调用`ring_component.recover`提取真实内/外弧，68/68输出有效；不调用DXY最终测量来填补019结果。Ring规范为中心0、法向±Z，负法向使用det=+1的180°旋转而非镜像。`X004=R X005+t`，列向量，OpenCV c2w，单位mm，尺度1。

| 原定组件 | 实际实现与代码 |
| --- | --- |
| 共享视频级SE(3)，冻结主体/相机 | `renderer019.py:FrozenRenderer`、`objective019.py:PoseObjective`；仅6个q可微，原K/c2w、主体顶点和HERO均固定 |
| 官方PyTorch3D | `Meshes/MeshRasterizer/SoftSilhouetteShader/cameras_from_opencv_projection/se3_exp_map`；沿用018 Ring-Aware A/B/C/D及detach深度次序；未实现新光栅器 |
| 公制与像素映射 | 原640×360评价；优化180×320，沿用验证过的像素中心映射，固定018归一化；O3D/P3D轴向深度p95≤7.63e−6mm（3帧门禁） |
| Ring yaw不提供信息 | `canonical_ring_camera`消除离散CAD绕轴锯齿；仍渲染实体CAD；三帧pure-yaw梯度0，loss浮动≤1.94e−7 |
| 多视角权重 | Mask/Ring按原生方向范围的4等宽分区均衡总权重；004方向跨度54.47°、00595.44°，不是全周相机覆盖；SIFT按有效帧/帧对归一，并未用方向权重 |
| 真实SIFT及地标 | `features019.py`：6000/ratio.72/双向、独立RGB-MAGSAC1.5px；Ring膨胀2px、高光/暗部/边框排除；至少3帧、已知相机4px、重投影<2px、视差>.5°；固定相机三角化+3D点鲁棒精修；不读取HERO |
| SIFT候选 | OpenCV EPNP-RANSAC+LM，成功至少6内点；正深度检查和空间覆盖独立记录；Sigma为unit-pixel几何代理，没有伪称已校准，也未用于白化损失 |
| 全360°与联合 | `search019.py`：两规范×72角，对所有52FIT帧；连续标量精修±5°；几何只提候选，SIFT/历史候选分别标记，不算术平均 |
| A1/A3独立范围 | `refine019.py:correct_scope`在读任何HOLDOUT前纠正A1仅轮廓grid/continuous、A3仅feature/grid/PnP；旧共享候选池选择另存RAW_POOL，A4不变 |
| 精修目标 | `Lpose=Lpolyp+Lring+.05Lfeature+.01mean(q²)`；`Lsearch=Lpolyp+.05Lfeature`。q按.6mm/5°归一，H=exp(qscale)Hseed；固定分母/鲁棒Huber归一3px |
| Ring损失 | 正Ring与已知非Polyp背景概率MSE各半，加.25×真实DXY弧上的(alpha−.5)²；**无量纲**。独立O3D可见内/外边界距离才是px；JSON旧`ring_sigma_px=3`未使用，不冒称像素距离项 |
| 80候选/3初值 | Adam.01，8级回溯；左平移≤1.2mm、旋转≤10°，FIT目标不增容差1e−9、Ring相对初值最多+.001；拒绝恢复q+Adam，全部终点保留 |
| 初值选取偏差 | 预注册文字称“局部极小”，实际是分数排序+20°角距离NMS，**非严格局部极小枚举**。不补写预注册，也不宣称全局唯一最优 |
| 正深度门禁偏差 | 原协议描述候选相机在前，实际迭代未单独对全部body顶点作硬cheirality拒绝；特征含behind常数惩罚，最终68帧另查全部body正深度。最终通过不能追认所有中间候选都通过 |
| 特征Ring可见性 | 训练用真实Ring Mask排除特征；未加入逐点CAD硬可见性筛选。预测冻结后全部成功PnP观测独立CAD检查为0个Ring遮挡点，未回流筛选 |
| 性能兼容修复 | 原hardRing bin0改官方bin32，104帧—位姿组合mask相等/z差为0，并验证3个loss/gradient；保留原代码/冻结证据。数值目标未换，未少用任何FIT像素 |
| 中断恢复 | CROSS seed0从第40步q+Adam恢复；保存RESUME说明，未声称全RNG bitwise无缝；FINAL.seconds仅恢复段，不能冒充全部任务耗时 |
| 数值抖动限制 | soft Ring bin32重入梯度相对差最大8.32e−5；负对照有约1e−6前向浮动，大于接受容差1e−9。77/80和3/80为实际执行记录，不能视为高精度严格单调证明；未据留出重调 |
| P1/H2 | `ring_depth019.py`固定材料/纹理/CAD与扇区检验，0稳定偏差；`hero_diagnosis019.py`在原native局部坐标比较同视频，避免共同H制造虚假内部改善；H2条件未触发 |

HERO的“TRUSTED”是017/018可解释规则标签，不是物理GT。004复用13份既有标签，005在8份原始来源上复用同一清理规则生成派生标签；`reused=False`表示本轮重建标签，不是重新HERO推理。005另1份new_r04仅有原生深度，未伪造TRUSTED曲面；其他46帧无原生HERO，可正常参与RGB/Mask配准。

原生子集NPZ保留完整原始V数组及子集F。初次交付诊断错误地把不被F引用的旧顶点计入显示范围和CAD内部计数，已纠正为**仅引用顶点+实际面片中心**；原计数保存在`provenance/UNREFERENCED_VERTEX_DIAGNOSTIC_SUPERSEDED.json`。没有删掉任何TRUSTED面片，也未改变配准。GLB仅紧凑重编号未引用顶点，原V/F/面ID保存在NPZ。

HOLDOUT SIFT在预测冻结后才提取，只供评价。所有三维深度比较使用轴向Z，正确投影、CAD首次表面与自遮挡区分；比目标表面更深不算可靠自由空间错误；前方分歧仅为含相机/HERO误差的几何代理。没有GT测量或ICP选取。H0指未统一原生坐标，非历史最佳配准。
