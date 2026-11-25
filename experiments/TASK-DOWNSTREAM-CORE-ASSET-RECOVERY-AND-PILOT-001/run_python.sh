#!/usr/bin/env bash
set -euo pipefail
task_root="$(cd "$(dirname "$0")" && pwd)"
repo_root="$(cd "$task_root/../.." && pwd)"
runtime_root="${DOWNSTREAM_RUNTIME_ROOT:-/home/liu/ring_first_3d_workspace/.runtime}"
export PYTHONPATH="$task_root/code:$repo_root/src:$runtime_root/p3d:$runtime_root/p3d_packages:$runtime_root/extra_packages:$runtime_root/fcl_packages:/home/liu/polyp_research/ring_anchor_3d/experiments/surface_fusion_v3/vendor"
export RING_FIRST_SOURCE_ROOT="$repo_root/src/ring_first_3d/mainline/frozen_registry"
export PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2
export MPLCONFIGDIR="$task_root/runtime/mpl" E4_RUN_DIR="$task_root/runtime/legacy" TMPDIR=/dev/shm
exec /home/liu/polyp_research/ring_anchor_3d/.venv/bin/python "$@"
