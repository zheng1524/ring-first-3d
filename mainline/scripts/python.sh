#!/usr/bin/env bash
set -euo pipefail
mainline_repo="$(cd "$(dirname "$0")/../.." && pwd)"
export RING_FIRST_P3D_RUNTIME="$mainline_repo/.runtime/p3d"
export RING_FIRST_EXTRA_PACKAGES="$mainline_repo/.runtime/extra_packages"
export RING_FIRST_FCL_PACKAGES="$mainline_repo/.runtime/fcl_packages"
export RING_FIRST_SOURCE_ROOT="$mainline_repo/src/ring_first_3d/mainline/frozen_registry"
export PYTHONDONTWRITEBYTECODE=1 TMPDIR="${TMPDIR:-/dev/shm}"
export MPLCONFIGDIR="${MPLCONFIGDIR:-$mainline_repo/mainline/validation/mpl}"
export PYTHONPATH="$mainline_repo/src:$mainline_repo/.runtime/p3d:$mainline_repo/.runtime/p3d_packages:$mainline_repo/.runtime/extra_packages:$mainline_repo/.runtime/fcl_packages:${RING_FIRST_OPEN3D_VENDOR:-/home/liu/polyp_research/ring_anchor_3d/experiments/surface_fusion_v3/vendor}${PYTHONPATH:+:$PYTHONPATH}"
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2
exec "${RING_FIRST_PYTHON:-/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python}" "$@"
