#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
while [[ ! -f evidence/BATCH_RECEIPTS.json || ! -f evidence/EXTRA_BATCH_RECEIPTS.json ]]; do sleep 5; done
bash run_python.sh code/test_contracts.py > runtime/final_tests.log 2>&1
bash run_python.sh code/visualize.py > runtime/final_visualize.log 2>&1
bash run_python.sh code/visibility.py > runtime/final_visibility.log 2>&1
bash run_python.sh code/verify.py > runtime/final_verify.log 2>&1
bash run_python.sh code/diagnose.py > runtime/final_diagnose.log 2>&1
bash run_python.sh code/report.py > runtime/final_report.log 2>&1
bash run_python.sh code/package.py > runtime/final_package.log 2>&1
