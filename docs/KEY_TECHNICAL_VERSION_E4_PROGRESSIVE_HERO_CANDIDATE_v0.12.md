# E4 PyTorch3D 渐进形变与HERO深度候选 v0.12

状态：一次固定预算试验完成；6/6新增运行各完成300次SGD，最终几何门禁0/6通过，等待人工审核。不替换v0.11或任何已批准主线，不实施SDFStudio/BundleSDF。

同分支、同原实验目录下新增 `runs/PROGRESSIVE_HERO_001`，复用VISIBILITY_ORDER_REPAIR_001离散次序修复版；p3d.py字节一致。原P0、相机/K、Mask、Ring实体、三拟合及留出角色不变。A直接引用原修复版RingAware，未重复优化。B相对P0边长/Laplacian坐标和未知区软位移保护；C为100步平移/三轴尺度、200步局部顶点；D在C上加固定鲁棒深度项。统一SGD、种子和视角序列，无搜索、GT选模、体积守恒或后处理。

HERO可靠观测来自已冻结512点/视角原生缓存，逐点复核清理valid、Pixel ID、原HERO深度及352高深度/360高RGB相机映射。真实拟合1536点，留出1533点；仅三个FIT参考进入深度loss。虚拟D是独立GT渲染理想深度上限，不能冒称HERO结果。新增梯度为离散首次面+FP64解析射线交点，避开不稳定zbuf反向；最大分量及全顶点方向FD通过。

- B：真实体积/P0从A的60.1%改善到100.4%，留出IoU 0.8961→0.9073，隐藏P0顶点内缩明显减少；但有约0.0055mm穿环。虚拟B粗糙度更高且确认21对自交。
- C：真实不优于B；虚拟留出IoU 0.9020但体积约2.10倍，GT曲面/占据误差更差。仅六参数阶段100步已膨胀约2.12倍；现配置不作为默认渐进策略。
- D：真实相对C，HERO拟合/留出条件MAE 0.777/0.950降至0.335/0.627mm，固定分母深度loss同降且HERO命中率未降；但Mask覆盖小幅下降，穿环约0.0533mm。虚拟理想深度改善C的曲面误差，仍约1.95倍体积且有7对自交，不认定几何正确。

全部新增真实条件Ring相交28/134/212面对应，最大顶点穿透0.0055/0.0412/0.0533mm；虚拟自交21/5/7对经Blender与FCL确认。自交体积积分仅诊断代理，不冒称认证实体Boolean误差。未通过删面/平滑或选中间轮制造PASS。真实无完整GT，相机仍INSUFFICIENT_EVIDENCE，留出仅针对更新阶段。

候选保留B形状保护及D深度适配模块，停止发布当前B/C/D几何结果；下一步优先对现有框架的非穿透/自交与全局参数动态作有限验证，须另行授权。没有证据仅靠换SDFStudio即可解决这些约束缺口。

[技术报告](../experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/runs/PROGRESSIVE_HERO_001/TECHNICAL_REPORT.md) · [终点指标](../experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/runs/PROGRESSIVE_HERO_001/metrics/ENDPOINTS.csv) · [失败记录](../experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/runs/PROGRESSIVE_HERO_001/FAILURE_LEDGER.md) · [复现](../experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/runs/PROGRESSIVE_HERO_001/REPRODUCE.md)
