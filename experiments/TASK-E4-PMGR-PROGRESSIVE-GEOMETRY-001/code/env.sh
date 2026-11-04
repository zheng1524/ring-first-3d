#!/usr/bin/env bash
# Source before all experiment commands; never modifies historical environments.
export PMGR_ROOT=/home/liu/ring_first_3d_e4_pmgr/experiments/TASK-E4-PMGR-PROGRESSIVE-GEOMETRY-001
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="$PMGR_ROOT/runtime/packages${PYTHONPATH:+:$PYTHONPATH}"
export PATH="$PMGR_ROOT/runtime/packages/bin:/usr/local/cuda-12.8/bin:$PATH"
export CUDA_HOME=/usr/local/cuda-12.8
export TORCH_EXTENSIONS_DIR="$PMGR_ROOT/runtime/torch_extensions"
export PMGR_PYTHON=/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python
export OMP_NUM_THREADS=2
export OPENBLAS_NUM_THREADS=1
