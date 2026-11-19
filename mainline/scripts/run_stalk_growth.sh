#!/usr/bin/env bash
set -euo pipefail
mainline_script_dir="$(cd "$(dirname "$0")" && pwd)"
mainline_case="${1:-G01}"; if [ "$#" -gt 0 ]; then shift; fi
case "$mainline_case" in G01) mainline_module=stalk-growth-g01;; G03) mainline_module=stalk-growth-g03;; *) exit 2;; esac
exec bash "$mainline_script_dir/python.sh" -m ring_first_3d.mainline.cli "$mainline_module" "$@"
