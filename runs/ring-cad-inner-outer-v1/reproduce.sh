#!/usr/bin/env bash
set -euo pipefail
ROOT=/home/liu/ring_first_3d_workspace
TASK=$ROOT/experiments/TASK-E4-RING-RGB-JOINT-BA-011
PKG=$ROOT/runs/ring-cad-inner-outer-v1
PY=/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python
echo "[1/4] git commit: $(git -C $ROOT rev-parse HEAD)"
echo "[2/4] module provenance:"
$PY $ROOT/tools/check_module_provenance.py $TASK || true
echo "[3/4] run fixture"
PYTHONPATH=$ROOT/src:$TASK/code $PY $TASK/code/reproduce_fixture.py --pkg $PKG
echo "[4/4] done"
