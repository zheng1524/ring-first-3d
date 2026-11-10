# METHOD_AND_INPUT_AUDIT

## 实际复用与差异

| 历史实现 | 复用方式 | 不能继承的含义 |
|---|---|---|
| Phase-C density.py::features | AST逐字提取，原k12/normal16、r0.4mm、入射/非平面性定义；适配source pixel数据 | 未运行D0/D1旧删点；密度不是错误概率 |
| Phase-C sparse run.py::face_components/edge_counts | AST逐字提取原共享边连通定义 | 未继承3px薄结构硬门槛或旧清理标签 |
| ring_first_v1 common.py::unproject | AST逐字提取原公制反投影 | 未重新恢复相机，未更改K或尺度 |
| E3-B MeshLocalField | 复用相机定向、面积加权法向一致性、原边界、k32非共享顶点竞争机制 | 这些原来决定局部场符号，不是表面物理真假；竞争筛查有限 |
| E4原真实Mesh renderer | AST提取原O3D实体光线追踪函数，仅接逐面色；主图读取原Raw数组 | 不用点云/解析几何替代原面，不平滑，不通过模型变形改善图像 |

## 明确公式和变量

固定：所有原深度、RGB/Mask、K/c2w、CAD和原顶点/面。没有可学习参数、optimizer、GT、HERO推理。新变量仅为原面状态与保留布尔值。

透视采样尺度：邻接i,j的预期边长 `(Zi+Zj)/2 * ||K^-1 pi-K^-1 pj||`。切平面尺度用原PCA法向与同射线的平面交点外推，从两端预期距离取平均。面上记录相关顶点八邻接最大值，不把它伪称仅本三角形最长边比；另列三角形真实最长边和面积。针状品质 `4sqrt(3)*area/sum(edge_length^2)`，等边为1。

法向一致性沿用E3-B：各面先朝源相机，按两倍面积在顶点累加；合向量长度/权重和，面取三个顶点最小。邻面最大夹角是曲率/折棱代理，不是标定曲率或错误真值。密度按预期透视面积归一；PCA可能受异常自身污染。边界EDT是前景采样中心到背景采样中心的欧氏距离，最近原Mask映射到native后计算，不减半像素；不能冒称原360-Mask的直接EDT。

初始联合规则及数值在config/PROTOCOL.json。补充规则为`1/Z=alpha du+beta dv+gamma`；端点之外8个半侧样本至少6有效，逆深度线性拟合（不是三维SDF/表面重建），预测深度RMS及端点误差<=0.125mm；两侧各自支持且跨端点预测差>0.5mm、原边长相对两平面预期>4、入射>=0.2。只给跨边原面添加证据，最终仍需shape和2px边界或CAD上下文。不把SDF/GT引入判断。

原定最终规则与实际gap017.py逐项相符；但追加的上下文条件使内部已确认断层仍无法拒绝，是方法局限。没有为得到更好结果偷偷移除此项。两侧源像素可分离，但HERO预测共享上游，不声称统计独立。

## 数值控制

CONTROL_TESTS.json 17项，TWO_SIDED_CONTROL_TESTS.json 5项：连续前向/65°/80°平面无误删和假断层；台阶识别44条断层；单像素无支持尖刺保留；Ring近距本身不入删除规则。台阶是解析控制，不是项目GT；未用这些数值搜索项目阈值。

## 输入与图像身份

SOURCE_LOCK锁定18来源，SHA在PREANALYSIS_FREEZE。原native K、pose与pack一致，原Mask与pack labels逐像素一致；camera_metadata存储姿态匹配差0，逐源CAMERA_METADATA_BINDING_AUDIT。G01旧原始视频帧顺序身份仍继承档案的条件性，不把这些匹配冒充新的相机认证。各组不混用世界坐标；只用video004各自产物。

## 原生离散化的忠实性限制

ARCHIVE_RAW是输入真实单参考Mesh，其历史构建已处理过深度尺寸和跳变。没有把它当完全未处理的网络深度。NATIVE_GRID是同深度的源像素局部诊断载体，新增的lattice编号与Raw原面编号严格分开，不能把诊断格导出当成新增或补好的HERO预测。适配候选只指ARCHIVE_RAW原面子集，不新增任何面。保留全部原顶点，包括未被原面引用的点。

## 工具与来源

距离变换定义参照[SciPy官方distance_transform_edt](https://docs.scipy.org/doc/scipy/reference/generated/scipy.ndimage.distance_transform_edt.html)。CAD符号距离使用现有Open3D CPU RaycastingScene，前提是闭合、一致绕序；有限样本仅作证据，不保证无碰撞。依赖沿用既有venv，无新增大型框架。
