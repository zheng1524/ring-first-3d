# 复现

环境：既有Python3.12、Open3D0.19旧vendor、Matplotlib及原项目renderer，不安装环境或运行模型。原输入和所有参数SHA见provenance。当前目录只作已交付验证，不覆盖重放。

```bash
cd /home/liu/ring_first_3d_ab_scene
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=2 /home/liu/polyp_research/ring_anchor_3d/.venv/bin/python experiments/TASK-AB-FULL-SCENE-VIS-002/code/validate.py
```

重新生成请将本任务源码/配置放在新空实验目录：prepare.py（冻结11配对与输入）→test_small.py→render_cases.py→deliver.py→validate.py。所有R由脚本位置派生；没有GT、HERO或完整重建入口。正式renderer和旧缓存均只读。最终显示配置已包含灰点.08/关闭抗锯齿，RGB点.8；redraw_geometry.py仅为首次展示审查后的灰点显示修订，不改变任何数值预测/支持。

本轮实际还先单独渲染22.60°样图检查，保留初始样图后完成批量；其余阶段与上面一致。没有声称做了第二次完整重放。旧四配对预测直接复用并逐字段等同，其余7使用同一原内核。
