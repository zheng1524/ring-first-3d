# 本轮实际入口与复核

工作树：`/home/liu/.config/superpowers/worktrees/ring_first_3d_workspace/TASK-M2F13`。
任务代码：本目录`code/`；本地大产物：`/home/liu/ring_first_3d_workspace/runs/m2f13_hero_all`。

使用`/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python`，`PYTHONDONTWRITEBYTECODE=1`，`OMP_NUM_THREADS=4`、`OPENBLAS_NUM_THREADS=4`；PYTHONPATH含`/home/liu/ring_first_3d_workspace/.runtime/extra_packages`及`/home/liu/polyp_research/ring_anchor_3d/experiments/surface_fusion_v3/vendor`。common.py读取已有CORE site_config.local.json的只读依赖路径，cache仅写M2F13 runtime。

实际阶段顺序：

1. prepare_cleanup/refine_cleanup→已审阅逐文件清单/归档→cleanup_execute→deduplicate_open3d→report_cleanup。这些是已执行的破坏性阶段，回执完整；不得把整个目录脚本无条件重跑。精确归档成员与删除journal见CLEANUP_FINAL引用。
2. freeze_hero.py先写PLANS_FROZEN及69次预算，run_hero.py在执行commit c08ef3d2下逐组合运行官方模型。已有开始标记/预算保护阻止重复花费；无需重跑已有深度。
3. collect_v6.py只读收集M2F10与M2F12诊断，evaluate_sources.py复用原评价/转换内核；evaluate_sources.py --aliases使用同一评价处理30条重复来源的原输出。初次别名运行使用等价的单独入口，交付版本evaluate_aliases.py已收敛为同一实现的薄入口，不维护第二套算法。
4. render_all.py复用actual_mesh_image，render_supplements.py补近景/别名原输出，label_membership.py将正式成员图标题写明自身Target资格；package_gallery.py输出CSV/HTML/配置/日志。绘图适配在c08ef3d2基础工作树执行，最终代码归档于9975762d；不能把9975762d倒称为之前的HERO执行commit。
5. verify_delivery.py只读复核输入/输出/科学源码/已有工作SHA、预算、别名深度逐元素一致、HTML引用与分母。完成后publish.py沿现有Git-data渠道上传已提交的任务文件、核验blob/tree/commit并以force:false更新分支。

本轮官方HERO推理与Mesh转换内核未改。V6缺Mesh的32项仅执行原函数转换；H004旧七项符号链接复用。可视化合并顶点/面数组仅用于射线绘图，不写融合Mesh。五条M2F12别名保留原生Mesh，与V6的历史360行Mesh分别展示。

源码、完整配置、stdout日志、173张PNG与小表上传。RAW/模型、大Mesh及完整退役证据归档留本地，路径与SHA见SOURCE_MANIFEST和归档回执。原始相机/地标/Support来源保持冻结M2F12路径，无外部成品补齐。
