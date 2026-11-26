#!/usr/bin/env bash
set -euo pipefail
task_dir="$(cd "$(dirname "$0")" && pwd)"
cd "$task_dir/../.."
runner="$task_dir/run_python.sh"
# Use a fresh checkout/worktree: existing RUN_001 is rejected, never overwritten.
test ! -e "$task_dir/runs/RUN_001"
bash "$runner" "$task_dir/code/test_contracts.py"
bash "$runner" "$task_dir/code/v6_adapter.py" audit
bash "$runner" "$task_dir/code/check_v6_interface.py"
bash "$runner" "$task_dir/code/generate.py"
bash "$runner" "$task_dir/code/v6_adapter.py" track
bash "$runner" "$task_dir/code/registration.py" V0 V1
bash "$runner" "$task_dir/code/evaluate.py" V0 V1
bash "$runner" "$task_dir/code/gate_v01.py"
# Coordinate contract assertions are enforced in generate; scientific negatives remain outputs.
bash "$runner" "$task_dir/code/registration.py" V2_20261117 V2_20261118 V2_20261119 V2_20261120 V2_20261121
bash "$runner" "$task_dir/code/evaluate.py" V2_20261117 V2_20261118 V2_20261119 V2_20261120 V2_20261121
bash "$runner" "$task_dir/code/export_prediction.py"
bash "$runner" "$task_dir/code/context_v6.py"
bash "$runner" "$task_dir/code/audit_delivery.py"
bash "$runner" "$task_dir/code/visualize.py"
bash "$runner" "$task_dir/code/write_report.py"
