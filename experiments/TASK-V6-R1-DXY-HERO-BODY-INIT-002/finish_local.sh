#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
bash run_python.sh code/compare_selection_refit.py > runtime/refit_compare.log 2>&1
bash run_python.sh code/visibility_revision.py > runtime/final_visibility.log 2>&1
bash run_python.sh code/visualize_revision.py > runtime/final_visualize.log 2>&1
bash run_python.sh code/visualize_revision.py --dxy-frame GP_Ip_10.3mm_closed_R5_single_refY_004/raw_000135 > runtime/final_pixel_figure.log 2>&1
bash run_python.sh code/visualize_revision.py --frame GP_Ip_4.0mm_closed_R5_single_refY_005/raw_000038 > runtime/final_failure_figure.log 2>&1
bash run_python.sh - <<'PY'
import sys,shutil
sys.path.insert(0,'code')
from common import *
for label,case,frame,kind in [('DXY_PIXEL_ONLY','GP_Ip_10.3mm_closed_R5_single_refY_004','raw_000135','DXY_PROCESS'),('DXY_NO_CURVE','GP_Ip_4.0mm_closed_R5_single_refY_005','raw_000038','BODY_COMPARISON')]:
 root=T/'runs/review/frames'/case/frame;dst=T/'figures'/(label+'.png');shutil.copyfile(root/(kind+'.png'),dst);r=read(root/(kind+'.json'));r.update(selected_figure=str(dst.relative_to(T)),selected_figure_sha256=sha(dst),source_review=str((root/(kind+'.png')).relative_to(T)));save(T/'figures'/(label+'.json'),r)
PY
bash run_python.sh code/verify_revision.py > runtime/final_verify.log 2>&1
bash run_python.sh code/report_revision.py > runtime/final_report.log 2>&1
bash run_python.sh code/package_revision.py > runtime/final_package.log 2>&1
