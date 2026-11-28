#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
export CUDA_VISIBLE_DEVICES="" OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
export MPLCONFIGDIR="$PWD/runtime/mpl"
exec nice -n 19 ionice -c 3 /home/liu/polyp_research/ring_anchor_3d/.venv/bin/python "$@"
