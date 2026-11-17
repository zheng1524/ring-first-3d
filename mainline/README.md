# 主线科研资产

这是统一入口和可运行资产闭包。状态ACTIVE_RESEARCH_MAINLINE，工程通过不认证三维科学精度。

活动实现位于src/ring_first_3d/mainline/lineage，按原任务版本隔离，避免混合014旧深度、018原生HERO、E1/E2和当前Init-A。既有src的契约、相机变换、Renderer、对应及评价API继续复用。frozen_registry保存原SHA源码供既有AST适配器直接读取，无需执行旧工作区脚本。

配置与身份：[资产表](manifests/MAINLINE_ASSET_MAP.json)、[来源](manifests/SOURCE_PROVENANCE.json)、[依赖锁](manifests/DEPENDENCY_LOCK.json)、[外部数据](manifests/EXTERNAL_INPUTS.json)、[工程状态](manifests/REPRODUCIBILITY_STATUS.json)。[流水线](PIPELINE.md)列出实际调用。

默认脚本是**固定输入工程重放**，不是新的科学优化任务。Body Update重放已保存Graph节点变换，Growth重建保存的样条并重新做Boolean/投影；真实HERO命令执行一次新的官方原生推理。原优化器源代码完整保留，未来科研执行须新TASK、数据/源码冻结和Policy门禁，不直接重跑历史协议。

保留G01的数值改善及根部缺陷、G03正式NaN和全部关键失败证据。原始RGB/Mask/GT/深度/权重留原位；旧目录仍有唯一资产及LOCAL_ONLY绑定，所以本轮没有整体删除工作区。临时环境依赖已复制到本项目.runtime并逐文件锁定，不创建新虚拟环境。

同机首次检出需要按manifests/RUNTIME_FILES.json恢复LOCAL_ONLY运行库，并从SITE.example.json配置SITE.local.json；受控数据和官方checkpoint必须事先存在。跨机器尚未认证，尤其Python/CUDA ABI、绝对数据路径和原生二进制需重新核验。

固定重放入口：run_ring_first.sh、run_hero.sh、run_body_initialization.sh、run_body_update.sh、run_stalk_growth.sh、run_a_to_b.sh、run_depth_supervised.sh。全部要求新--out目录，拒绝覆盖。

[可视化](visualization/index.html)保留实际Mesh与图像。完整盘点平面CSV/JSON为LOCAL_ONLY，Git中inventory/*.gz是其逐字节压缩副本，可用unpack_inventory.py还原并核验哈希。

同机检出后的明确准备步骤：

```bash
cp mainline/configs/SITE.example.json mainline/configs/SITE.local.json
/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python mainline/scripts/materialize_runtime.py
/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python mainline/scripts/unpack_inventory.py
bash mainline/scripts/run_pipeline.sh --out /tmp/mainline-checkpoint-replay
```

运行库来源路径缺失会明确返回NOT_EVALUABLE_EXTERNAL_DEPENDENCY；跨机器须按manifest重新提供数据和依赖，不能直接照搬本机绝对路径。上述命令不新建环境、不安装包、不复制权重。
