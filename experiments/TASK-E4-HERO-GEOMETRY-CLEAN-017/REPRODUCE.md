# REPRODUCE

CPU only，使用现有环境 `/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python -B`。不需要GPU、模型权重或GT。原始输入通过config/SOURCE_LOCK.json及SHA索引读取，不复制大型数据。

为保护现有结果，在同一仓库experiments下建立新的空复现副本；原009、015、016输入必须保留在本地原路径。

```bash
cd /home/liu/ring_first_3d_e4_sdf_localization
SRC=experiments/TASK-E4-HERO-GEOMETRY-CLEAN-017
DST=experiments/TASK-E4-HERO-GEOMETRY-CLEAN-017-REPRO
test ! -e "$DST"
mkdir -p "$DST/code" "$DST/config"
cp "$SRC"/code/*.py "$DST/code/"
cp "$SRC/config/FINAL_CLEANING_RULE.json" "$DST/config/"
PY=/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python
"$PY" -B "$DST/code/prepare017.py"
"$PY" -B "$DST/code/test017.py"
"$PY" -B "$DST/code/test_gap017.py"
"$PY" -B "$DST/code/analyze017.py"
"$PY" -B "$DST/code/freeze_final017.py"
"$PY" -B "$DST/code/gap017.py"
"$PY" -B "$DST/code/diagnose017.py"
"$PY" -B "$DST/code/figures017.py"
"$PY" -B "$DST/code/local_figures017.py"
"$PY" -B "$DST/code/deliver017.py"
"$PY" -B "$DST/code/validate017.py"
```

主清理输入/输出只用ARCHIVE_RAW；NATIVE_GRID为诊断，不当作补面重建。repro的固定FINAL_CLEANING_RULE来自已提供配置，不重新搜索参数。各统计与npz数值应一致；gzip时间戳、日志、JSON冻结时间和PNG软件渲染元数据不要求字节一致。

原阶段文档和源码sha见provenance/PREANALYSIS_FREEZE_INITIAL.json、PREANALYSIS_FREEZE.json、BEFORE_FINAL_CLEANING.json。补充规则在初始负结果之后且最终处理之前冻结；不是声称从任务起只运行过一条规则。
