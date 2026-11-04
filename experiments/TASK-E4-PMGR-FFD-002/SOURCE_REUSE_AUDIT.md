# 实际复用与安装决策

不安装PyTorch3D、PhysicsNeMo、PyGeM、IPC、libigl或CUDA FFD工程；不克隆大仓库。复用本地Torch/nvdiffrast/FCL/Open3D/Blender。下载内容仅本次任务书和小型官方网页阅读，无新权重。

| 来源、函数/机制 | 实际本轮位置与边界 | 许可/版本与兼容性 |
|---|---|---|
| [PyTorch3D教程](https://pytorch3d.org/tutorials/fit_textured_mesh)：共享球网格、view loss汇总、`offset_verts`及`mesh_edge_loss/mesh_laplacian_smoothing`组织 | `code/shape.py/objective.py/optimize.py`参照训练组织，自写低维FFD和信赖域；不使用其合成相机，不调用其运行库，不声称官方PyTorch3D输出 | [BSD许可](https://raw.githubusercontent.com/facebookresearch/pytorch3d/main/LICENSE)；仅阅读官方教程，未复制其代码块；本轮实际CUDA渲染为已有nvdiffrast |
| [nvdiffrast cube::render](https://github.com/NVlabs/nvdiffrast/blob/main/samples/torch/cube.py)：`rasterize→interpolate→antialias` | `code/renderer.py::Renderer.render`调用已安装库公共API；相机clip来自R1 `camera_renderer.py`，保留CV+Z、top-down、pixel-center。官方[文档](https://nvlabs.github.io/nvdiffrast/)说明局部覆盖及小三角形问题；4×/8×尝试仅作数值诊断 | [NVIDIA Source Code License](https://raw.githubusercontent.com/NVlabs/nvdiffrast/main/LICENSE.txt)，仅研究/评价使用。库留在旧PMGR/runtime/packages，不复制NVIDIA核心源码/二进制进新分支；安装目录与SHA另索引 |
| [PhysicsNeMo `free_form_deform_points`](https://docs.nvidia.com/physicsnemo/latest/physicsnemo/api/nn/functionals/geometry.html)、[Mesh.free_form_deform](https://docs.nvidia.com/physicsnemo/latest/physicsnemo/api/mesh/transformations.html) | `code/shape.py::lattice_weights/free_form_deform_points`按公开Bernstein/均匀cubic B-spline张量积数学公式自写小型Torch核，origin/extent固定，控制位移mm。正交残差与P3固定支持权重为项目适配，不冒称直接调用官方函数 | [Apache-2.0](https://raw.githubusercontent.com/NVIDIA/physicsnemo/main/LICENSE.txt)；未安装或拷贝PhysicsNeMo源码，仅公式/API接口参考，Float64 CPU单元测、Float32 CUDA反传 |
| [PyGeM球体教程](https://mathlab.github.io/PyGeM/tutorial-1-ffd.html)、[FFD API](https://mathlab.github.io/PyGeM/ffd.html) | `code/validate.py`独立手算单角点位移验证，不依赖PyGeM；将其按box_length归一位移换算到公制位移 | 仅阅读数学与示例，未安装/复制或分发PyGeM代码；不声称PyGeM运行结果 |
| R1 `inputs.py/collision.py/mesh_checks.py/blender_check.py`、P0Constraints；旧PMGR cotan `laplace` | 本任务小型受控复制/AST提取，独立R路径/写入Guard；`p0.py`只提取证书类，不导入旧优化器Guard。无旧0.5px veto/多数拒绝停止；`collision.py`整面FCL/Open3D路径复用 | 父执行432c8a9；原文件/输入SHA冻结；R1安全P0唯一结果只读，27MB FCL安装目录仍为共享依赖，未清理 |
| `visualization/real_p0_renderer.py` | `inputs.py::vis`读取相机射线/半像素内参/真实公制展示；原生Kn与轴向Z不变 | 本仓库版本及所有来源SHA随冻结清单；不加载Blender GT |

IPC Toolkit、libigl、Fast FFD仅保留任务书中的备选身份，本轮默认不调用；FCL路径不能认证时仍拒绝，不以缺少IPC为由接受穿透。代码中不存在按Ip/Is/IIa类别切换。

## 实际运行版本补记

已安装nvdiffrast0.4.0，本地既有源码commit253ac4fcea7de5f396371124af597e6cc957bfae，tracked源码无修改；build/egg-info为原环境构建产物，未清理。官方阅读HEAD：PhysicsNeMo30ecd227ffed3467cc9c17492c343fae55653145、PyTorch3D e4ad6e5687a360ccdc6ebd91348e8dbbac97bf31；它们不是本轮安装依赖。

G06真实Mask有限差分事后FAIL，库成熟不构成自动验收。当前case_gate.py按同规则逐组阻塞失败，原执行结果保留；见TECHNICAL_REPORT。
