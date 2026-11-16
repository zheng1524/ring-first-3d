# 坐标与数据契约

任何复用先检查[具体源码及哈希](../registry/REUSABLE_MODULES.md)，禁止凭字段名称推断坐标一致。

## 图像与像素

- RGB 缓存为 RGB；OpenCV 与 DXY `measure_frame` 的 image 为 BGR，转换必须记录。labels 为 uint8：0 background、1 polyp、2 ring，不是任意灰度前景。
- 工作归档常为 H×W=360×640；HERO 原生 H×W=352×640。API 中 `target_image_size=[352,640]` 按 H,W，图像宽高常写 640×360，不得混淆。
- 整数像素中心；缩放映射 `u'=(u+0.5)*sx-0.5`，`v'=(v+0.5)*sy-0.5`，`K'=A K`，A 对角为 sx,sy,1，平移为 (sx−1)/2,(sy−1)/2。labels 最近邻映射，不用深度插值冒充原生观测。
- 018 原生 Z 有旧 360 高 mesher 适配；MAX 原生 352 格点建面、不插值深度；两者不是同一资产。PyTorch3D 的 K 主点额外 +0.5 是栅格半整数补偿，不能反写 native K，也不能与缩放平移重复相加。

## Camera、Ring、Body、HERO

以行向量表达，c2w=`T=[R C;0 1]`：
`X_camera=(X_world-C)@R`；
`X_world=(K^-1 [u,v,1]^T * Z)@R.T+C`（实现按行转置）。
Z 是相机轴向 mm 深度，不是单位射线的欧氏距离。射线若保持相机 z 分量=1，raycast t 才对应轴向 Z；单位方向 t 则为范围，须显式换算。

Ring-local world 以 CAD 为公制参考；Body/HERO 要在同一经核验的 frame 下才能求距离。Body 网格和 HERO 原始 XYZ 以 mm 表达。PyTorch3D 可用 `(V-center)/scale` 数值归一化，相关相机也要同步；018 使用可微重心插值恢复世界坐标再计算轴向深度，不能直接用 normalized zbuf 当 mm。

mm→m 只在要求米的官方 HERO pose 接口、Open3D TSDF/GLB 边界显式一次转换，返回记逆转换，不通过拟合自由 scale 修错单位。公开显示固定等比例 mm。

## Ring CAD

R10 表示内径 10mm，不是半径；CAD 中心线半径 5.6mm、线截面半径 0.6mm，外径 12.4mm，Mid 直径 11.2mm、线径 1.2mm。R5 为内径 5mm；不能沿用 R10 数字。每份资产绑定真实 ring_kind 与 CAD SHA。
环有旋转对称和遮挡；已知单位不消除 yaw 和位姿歧义。Ring 点云不能替代 CAD，不改其形状以迎合 Body。

## DXY 像素几何与九参数体

官方候选 center=`c`、basis=`B` 定义二维区域：
`q=(p-c)@inv(B).T`，`sum(q*q)<=1`。
列/行与 basis 主轴缩放不得凭经验重写。A1 转换在 prepare.py 的 main 内，不存在一个已统一发布的“转换SDK”。当前继承解析 `ellipse_projection`、`signed_distance`、`two_d_parts` 及 `decode`、`sphere_mesh`。

九参数为中心 3、旋转增量 3、log 半轴 3；R0、bounds、starts 必须绑定任务。当前 repair 中心 (0,0,−2)，半轴 5/5/3，3 starts，TRF max_nfev=60；E1/E2 只换二维目标，无 HERO XYZ/depth block。参数稳定与旋转稳定不是同一回事，近球体旋转歧义不必然等于表面差异。

## 原始 ID、来源与观察类型

017 ARCHIVE_RAW 使用真实原 face ID；NATIVE_GRID 诊断 ID 形如 `2*(v*(W-1)+u)+side`。不可交叉套索引或将诊断 ID 当原始面编号。TRUSTED/CONFLICT/UNKNOWN/候选分类仅属证据层，缺独立真值时不能保证删掉的都是错面。原 raw 与清理后、融合后、先验体分开存。

跨视频 004/005、照片的世界 frame 默认独立。MAX 中部分 005 PnP 依赖 004 RGB 地图，照片共享 K 是假设；021 全背景共同地标只为 G01 提供条件证据，不推广其他组。原生 native T 与 FINAL_CAMERA_POOL 的 18 个 OLD018 来源有小幅版本差异；当前 repair 保留 native T 并登记，未改相机。不能把两份矩阵暗中替换。

## 可审查的契约证据

[repair 数值契约](https://github.com/zheng1524/ring-first-3d/blob/6d5d5684ce85bb2aa1f044e3ce8c45a578e07e33/experiments/TASK-E4-BODY-GUIDED-HERO-DXY-REPAIR-001/metrics/NUMERICAL_CONTRACTS.json)、
[MAX 几何测试](https://github.com/zheng1524/ring-first-3d/blob/6d5d5684ce85bb2aa1f044e3ce8c45a578e07e33/experiments/TASK-E4-RING-FIRST-MAX-COVERAGE-VIEWS-001/metrics/CONTRACT_AND_GEOMETRY_TESTS.json)、
[018 原生回路](https://github.com/zheng1524/ring-first-3d/blob/6d5d5684ce85bb2aa1f044e3ce8c45a578e07e33/experiments/TASK-E4-HERO-BODY-ADAPT-018/TECHNICAL_REPORT.md)、
[017 面身份](https://github.com/zheng1524/ring-first-3d/blob/6d5d5684ce85bb2aa1f044e3ce8c45a578e07e33/experiments/TASK-E4-HERO-GEOMETRY-CLEAN-017/TECHNICAL_REPORT.md)。
