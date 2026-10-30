> 以下为P0静态审计快照，先于清理、隔离安装与模型运行。当前实际结果见 [技术报告](../TECHNICAL_REPORT.md)、[最终运行表](../metrics/ARM_FINAL_STATUS.csv)。

# 官方路线、实际依赖及最小 adapter

2026-10-30官方资源实查；文件与Git blob SHA见 `OFFICIAL_SOURCE_REVISIONS.json`，本地读取副本在 `official_sources/`（LOCAL_ONLY，不安装）。读取不等于模型导入或运行成功。

|路线|冻结官方commit|许可/实际状态|最小改造及阻塞|
|---|---|---|---|
|MapAnything v1.1.4|`3d10cf7a3016fc0f9bb13a071ee66c47b10be0d9`|代码Apache2；优先apache权重；模型NOT_RUN|只新增格式/单位适配。缺hydra-core/uniception等；权重4.914GB大于磁盘可用；6GiB显存尚未实测|
|MonoSDF（首选候选）|`12513009cd20a08b35ddc2c55a7e42da2c7baf43`|官方MIT；NOT_RUN，未完成本机依赖闭包|原生MonoSDFNetwork、ErrorBoundSampler、MonoSDFLoss复用；绝对HERO Z监督不能沿用默认scale/shift不变损失；接真实Mask和有正下界不确定权。network.py模块级导入hashencoder，MLP配置也不能假定免编译；缺pyhocon/scikit-image/tensorboard/nvcc|
|NeuS2（次选候选）|`081b8191d049158a8296bfcb15c7d9cf065540df`|NVIDIA Source Code License for instant neural graphics primitives，不能写成MIT；NOT_RUN|CUDA/CMake/子模块与pybind构建；额外depth/uncertainty适配；无nvcc，磁盘不足。许可仅记录，不作法律结论|
|SparseRecon（本轮不选）|`50e11d660bf51d1ea61c271c10c70c698ca30988`|官方MIT；NOT_RUN|官方Python3.9/Torch2.0.1+cu118、VisMVSNet/Omnidata预处理闭包；不替换现有Torch2.7.1+cu128，不额外训练基础模型|

来源：[Map官方](https://github.com/facebookresearch/map-anything/tree/3d10cf7a3016fc0f9bb13a071ee66c47b10be0d9)、[MonoSDF官方](https://github.com/autonomousvision/monosdf/tree/12513009cd20a08b35ddc2c55a7e42da2c7baf43)、[NeuS2官方](https://github.com/19reborn/NeuS2/tree/081b8191d049158a8296bfcb15c7d9cf065540df)、[SparseRecon官方](https://github.com/hanl2010/SparseRecon/tree/50e11d660bf51d1ea61c271c10c70c698ca30988)。候选排序基于工程改造量，未以GT或图像误差选基座；没有声称任一候选已能在6GiB运行。

## Map输入与输出契约

`preprocess_inputs`原始输入 `img=(H,W,3)`，uint8或[0,255]，K=(3,3)，depth_z=(H,W)，camera_poses=(4,4)。`infer`输入为官方处理后的img=(B,3,H,W)、data_norm_type、K=(B,3,3)、depth_z=(B,H,W,1)、camera_poses=(B,4,4)。pose遵循OpenCV右X、下Y、前Z的cam2world；首视角有pose才能在其他视角提供pose，K与rays互斥，depth必须伴K/rays。

M0只RGB，M1加有效K，M2加同视频冻结条件pose，M3再加合法HERO光轴Z。Mask不属于上述核心推理几何字段：不能冒充官方新增mask输入；保留源Polyp/Ring标签作为独立输出域限制和评价分母，官方内部mask不是Polyp标签。预处理K和depth必须交官方预处理统一resize/crop，Polyp标签须按同一变换用最近邻映射，不能只缩放RGB。当前仅测试历史契约的像素中心K缩放，不声称已完成官方crop集成。

内部mm→模型m：depth和pose的平移均乘0.001，旋转不变；pts3d/depth/translation返回乘1000。输出pts3d、pts3d_cam、depth_z、depth_along_ray、camera_poses、intrinsics、conf、mask分别保存。World坐标若相对首相机规范化，adapter必须使用官方实际输出参考约定恢复Ring局部系，不能默认原坐标无变化。M0/M1绝不用GT或历史几何ICP补尺度；若无法独立与固定CAD坐标对应，CAD穿插写NOT_EVALUABLE。

两种官方checkpoint的revision、发布端LFS SHA256和size见 `OFFICIAL_WEIGHT_METADATA.json`：apache版SHA `fa06c0fdccefc5048e072c85935d5789b1e36b307f3859033c17f9dcb9fd5201`；研究版SHA `981f060c64664dff3272b5f5a823d350abe71a2f144444db4cfc325f3ed5a3a0`。均为4,914,062,480bytes。**这是发布端摘要，不是本地下载核验**；两版均未下载，不混用。

## P1未执行的具体计划

仅G01_005两份参考，固定相机/真实RGB、Polyp Mask与已核验HERO光轴Z；target00860和00611不进入拟合。Map按M0→M1→合法M2/M3必要少量前向，官方memory_efficient_inference、minibatch_size=1、AMP，不能事先保证峰值显存。SDF仅一次单场景优化≤1800秒，固定相机、鲁棒RGB/轮廓、绝对Z稳健残差与成熟Eikonal，深度权重设正下界且禁止学习归零。未冻结实际训练配置或注册正式竞争阈值，因资源门禁在模型启动前停止。不执行三组消融、四组批量优化或跨视频联合优化。
