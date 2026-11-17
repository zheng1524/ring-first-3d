#!/usr/bin/env bash
set -euo pipefail
mainline_script_dir="$(cd "$(dirname "$0")" && pwd)"
exec bash "$mainline_script_dir/python.sh" -m ring_first_3d.mainline.cli body-initialization "$@"
