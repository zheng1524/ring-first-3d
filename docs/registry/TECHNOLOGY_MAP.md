# TECHNOLOGY_MAP

实现新技术前必须先完成现有资产检索，并在报告中留下简短复用决策。

| component | 功能 | 当前推荐实现 | 入口 | 是否可改 |
|---|---|---|---|---|
| `ring_cad_projection` | Ring CAD 透视轮廓 | `native/camera.py::torus_contours` | `torus_contours(c2w,K)` | 仅修复 |
| `init_segmentation` | 3 类分割 | 冻结权重 sha256 `981aa596…` + bilinear logits | `polypseg`/DXY 数学 | 只读 |
| `dxy_ring_observation` | inner/outer 椭圆 | `ring_component.recover` | 只读调用 | 只读 |
| `camera_ring_first` | 5-DoF 相机候选 | `native/camera.py::recover` | — | 复用 |
| `rgb_feature_tracks` | SIFT 轨迹 + held | 冻结 `track005.py` | `ns['main']()` | 复用 |
| `camera_ring_rgb` | Ring+Ring BA | 冻结 `local_ring_sfm.py::BA` | 只加适配层 | 适配层可改 |
| `camera_evaluation` | Ring/RGB 评价 | 005 `unified_camera` | — | 复用 |

## 复用规则（强制）

1. 不得另写 Torus 投影器、椭圆拟合器、SfM/BA。
2. DXY 与 INIT 只读。
3. 新的 Ring 观测只能作为**适配层**接入冻结 BA。
4. 若必须修改公共评价函数：单独记录、重评历史基线。
