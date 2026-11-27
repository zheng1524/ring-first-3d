#!/usr/bin/env bash
set -euo pipefail
REG_TASK="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
if [[ -e "$REG_TASK/runs/R1_001" ]]; then
  echo 'Frozen batch exists. Use a new independent worktree; no overwrite.' >&2
  exit 2
fi
run_stage() { bash "$REG_TASK/run_python.sh" "$REG_TASK/code/$1" "${@:2}"; }
run_stage test_registration.py
run_stage audit.py
run_stage predict.py
run_stage replay_check.py
run_stage clean_after.py
run_stage evaluate.py
run_stage candidate_clean.py
run_stage visualize.py
run_stage deliver.py
