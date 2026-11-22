# 复现命令（只读，不改 021 源码）

```bash
cd /home/liu/ring_first_3d_workspace
export PYTHONPATH=$PWD/src:.:/home/liu/ring_first_3d_workspace/runtime/p3d
PY=/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python

# S0 源码收集（29/29 校验）
python3 /tmp/audit022/TASK_E4_W0_CROSSVIDEO_022_INDEPENDENT_AUDIT/tools/collect_pinned_sources.py \
  --repo /home/liu/ring_first_3d_workspace --out /tmp/PINNED_SOURCES

# S2/S4 审计测试
$PY experiments/TASK-E4-W0-CROSSVIDEO-022-INDEPENDENT-AUDIT/audit_tests/t1_objective_mismatch.py
$PY experiments/TASK-E4-W0-CROSSVIDEO-022-INDEPENDENT-AUDIT/audit_tests/t2_formal_gradient.py
$PY experiments/TASK-E4-W0-CROSSVIDEO-022-INDEPENDENT-AUDIT/audit_tests/t3_optimizer_state.py
$PY experiments/TASK-E4-W0-CROSSVIDEO-022-INDEPENDENT-AUDIT/audit_tests/t4_input_provenance.py
$PY experiments/TASK-E4-W0-CROSSVIDEO-022-INDEPENDENT-AUDIT/audit_tests/t5_controlled_validity.py
$PY experiments/TASK-E4-W0-CROSSVIDEO-022-INDEPENDENT-AUDIT/audit_tests/t6_provenance_leakage.py
```
