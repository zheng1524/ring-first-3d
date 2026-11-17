#!/usr/bin/env bash
set -euo pipefail
mainline_script_dir="$(cd "$(dirname "$0")" && pwd)"
exec bash "$mainline_script_dir/python.sh" "$mainline_script_dir/run_pipeline.py" "$@"
