#!/usr/bin/env bash
set -euo pipefail
TASK_DIR=$(cd "$(dirname "$0")" && pwd)
export PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export PYTHONPATH="$TASK_DIR/code:/home/liu/ring_first_3d_workspace/src:/home/liu/ring_first_3d_workspace/.runtime/extra_packages:/home/liu/polyp_research/ring_anchor_3d/experiments/surface_fusion_v3/vendor"
export MPLCONFIGDIR="$TASK_DIR/runtime/mpl" TMPDIR=/dev/shm
mkdir -p "$MPLCONFIGDIR"
exec nice -n 19 ionice -c 3 /home/liu/polyp_research/ring_anchor_3d/.venv/bin/python "$TASK_DIR/code/worker.py" "$@"
