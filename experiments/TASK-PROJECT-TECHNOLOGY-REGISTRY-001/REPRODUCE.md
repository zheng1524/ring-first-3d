# 复核本次文档审计

本轮复核仅使用git、Python标准库与文本/AST读取，不安装模型、不导入实验代码、不运行重建/推理/拟合/训练。以下为只读检查，不能以复核名义运行历史main。

1. 在独立checkout检查git status、origin、当前branch及parent；读取docs/registry/BASELINE_AUDIT.md和REMOTE_REFS.json。远程ref为2026-11-16快照，今后推进不要求回退。
2. 打开docs/registry/MODULE_REGISTRY.json：按source_commit用git show读取源码；DXY路径去只读new-polyp-dxy独立repo。对每份文件算hashlib.sha256、ast.parse核对symbols；复用类型/输入约束回读对应卡。
3. 打开EVIDENCE_MANIFEST.json，以commit:path读取git对象核验bytes/SHA；不加载原始GT。旧审计分支通过git对象读取，禁止合并覆盖。
4. 用csv.DictReader检查EXPERIMENT_INDEX.csv规定字段、唯一TASK_ID、双状态枚举、报告与失败路径、主题顺序；与REUSABLE_MODULES及MODULE_REGISTRY的T01–T43对应。
5. 校验新增Markdown相对文件链接，忽略代码块内路径示例；对GitHub /blob/<SHA>/ 链接检查对应本地repo git对象。HTTP/权限可随时间变化，不能声称这等于网页全量联网检查。
6. LOCAL_ARTIFACTS仅列代表资产，原路径不存在应标MISSING而非补造；hash_verification=INHERITED的checkpoint不要误报为本轮重算。不得下载/复制大资产以完成文档检查。
7. git diff --name-status <parent> 应仅包含README文档入口、docs/PROJECT_HOME、docs/architecture、docs/registry及本任务报告/回执；不得有旧.py/metrics/输入变化。DXY git status保持干净；外层工作区不提交。

本轮验证机器回执在AUDIT_VALIDATION.json，不提交可执行审计脚本，以保持DOCS-ONLY。以PROJECT_HOME和12问表进行新人理解验收，引用指标时继续保留原分母与科学限制。所有实验复现说明只是索引，实际执行须另行任务，不属于本轮操作。
