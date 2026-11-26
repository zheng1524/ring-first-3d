#!/usr/bin/env bash
set -euo pipefail
TASK_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
if [[ -e "$TASK_DIR/runs/R002_001" ]]; then
  echo 'Frozen run exists; use a fresh independent worktree. No overwrite.' >&2
  exit 2
fi
run_stage() { bash "$TASK_DIR/run_python.sh" "$TASK_DIR/code/$1" "${@:2}"; }
run_stage test_contracts2.py
run_stage control2.py prepare
run_stage control2.py predict
run_stage control2.py evaluate
run_stage run_real_stage.py track
run_stage run_real_stage.py clean
run_stage predict_real2.py
run_stage evaluate_real2.py
run_stage visualize2.py
run_stage deliver2.py
