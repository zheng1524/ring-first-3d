#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
while [[ ! -f evidence/FULL_BATCH.json ]]; do sleep 10; done
bash run_python.sh code/visibility_revision.py > runtime/final_visibility.log 2>&1
bash run_python.sh code/visualize_revision.py > runtime/final_visualize_first.log 2>&1
while [[ ! -f evidence/DXY_BATCH_RECEIPT.json ]]; do sleep 10; done
bash run_python.sh code/verify_dxy_full.py > runtime/final_dxy_verify.log 2>&1
bash run_python.sh code/visualize_revision.py > runtime/final_visualize.log 2>&1
bash run_python.sh code/verify_revision.py > runtime/final_verify.log 2>&1
bash run_python.sh code/report_revision.py > runtime/final_report.log 2>&1
bash run_python.sh code/package_revision.py > runtime/final_package.log 2>&1
