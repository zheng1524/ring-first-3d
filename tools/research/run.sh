#!/usr/bin/env bash
# Explicit existing environment; override every local path for a different machine.
set -euo pipefail
repo_dir="$(cd "$(dirname "$0")/../.." && pwd)"
p3d_runtime="${RING_FIRST_P3D_RUNTIME:-/home/liu/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/runtime}"
runtime_python="${RING_FIRST_PYTHON:-/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python}"
export PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2
export PYTHONPATH="$repo_dir/src:$p3d_runtime/packages:$p3d_runtime/pytorch3d:${RING_FIRST_EXTRA_PACKAGES:-/home/liu/ring_first_3d_e4_sdf_evolution/experiments/E4-SDF-EVOLUTION-001/runtime/packages}:${RING_FIRST_FCL_PACKAGES:-/home/liu/ring_first_3d_e4_pmgr_r1/experiments/TASK-E4-PMGR-R1/runtime/packages}:${RING_FIRST_OPEN3D_VENDOR:-/home/liu/polyp_research/ring_anchor_3d/experiments/surface_fusion_v3/vendor}${PYTHONPATH:+:$PYTHONPATH}"
exec "$runtime_python" "$@"
