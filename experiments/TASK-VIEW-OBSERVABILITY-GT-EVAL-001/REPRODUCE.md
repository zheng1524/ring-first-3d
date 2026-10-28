# 复现与只读核验

环境：既有 `/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python`（Python3.12），Open3D0.19从旧surface_fusion_v3/vendor只读导入；无安装/模型推理。项目固定renderer未改。源码/输入/冻结规则SHA见provenance。

验证已交付结果（不重跑预测）：

```bash
cd /home/liu/ring_first_3d_view_eval
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=2 /home/liu/polyp_research/ring_anchor_3d/.venv/bin/python experiments/TASK-VIEW-OBSERVABILITY-GT-EVAL-001/code/validate.py
```

本轮实际分步执行：freeze.py → 独立Blender export_gt.py → gt_evaluate.py（表已保存后控制台序列化异常，后修打印，无再次计算）→ inventory.py →7项小测试→首阶段commit/push→reprojection.py（16）→photo_candidates.py（在照片误差前冻结6继承候选）→reprojection.py --photo-supplement→visualize.py→supplemental_sources.py→finish_evidence.py→write_reports.py→validate.py。

需要重放时必须复制本任务源码到新空实验目录，再依此顺序运行；所有 `R` 从脚本位置派生，旧输入绝对路径只读。freeze.py和GT协议拒绝覆盖既有冻结清单。不要在本次已冻结目录直接重放，也不要运行旧完整重建入口。无需更改清理、上游或正式Dxy。全部22配对在各自误差前冻结，独立复现应保留原来的首次16/后续6两个计划。

GT独立导出命令（仅在新任务目录中运行）：

```bash
/home/liu/blender/blender-5.0.1-linux-x64/blender --background --disable-autoexec -t 2 --python experiments/TASK-VIEW-OBSERVABILITY-GT-EVAL-001/code/export_gt.py
```

本轮没有声称进行了第二次完整重放。完整HTML/NPZ/GT/原图路径依赖本机冻结资产；public仓库不含原始科研数据。
