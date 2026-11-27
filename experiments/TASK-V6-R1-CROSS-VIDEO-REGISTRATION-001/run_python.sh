#!/usr/bin/env bash
set -euo pipefail
task_root="$(cd "$(dirname "$0")" && pwd)"
repo_root="$(cd "$task_root/../.." && pwd)"
export PYTHONPATH="$task_root/code:$repo_root/src:/home/liu/ring_first_3d_workspace/.runtime/extra_packages:/home/liu/polyp_research/ring_anchor_3d/experiments/surface_fusion_v3/vendor"
export RING_FIRST_SOURCE_ROOT="$repo_root/src/ring_first_3d/mainline/frozen_registry"
export PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES="" OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 BLIS_NUM_THREADS=1
export MPLCONFIGDIR="$task_root/runtime/mpl" E4_RUN_DIR="$task_root/runtime/legacy" TMPDIR=/dev/shm
exec nice -n 19 ionice -c 3 /home/liu/polyp_research/ring_anchor_3d/.venv/bin/python /home/liu/.config/superpowers/worktrees/ring_first_3d_workspace/TASK-V6-REG-CLEAN-002/experiments/TASK-V6-REGISTRATION-NOISE-AND-RAW-CLEAN-002/code/worker.py "$@"
