"""P0-F: hardcoded K, fake source_sha, n_raw statistic, per-view K spread."""
import sys, json
from pathlib import Path
import numpy as np
WS = Path('/home/liu/ring_first_3d_workspace')
C21 = WS/'experiments/TASK-E4-W0-CROSSVIDEO-021-CORRECTIVE'
sys.path.insert(0, str(C21/'core'))
import w0_adapter as AD
import cross_video_matches as CVM

KHARD = np.array([[490., 0, 319.5], [0, 490., 179.5], [0, 0, 1.]])


def main():
    views4, acc4 = AD.load_views('G03', '004')
    views, acc = AD.load_views('G03', '005')
    spread = max(float(np.abs(np.asarray(v['K'], float) - KHARD).max()) for v in views)
    out = dict(
        per_view_k_max_deviation_from_hardcoded=spread,
        hardcoded_k_is_used_for_optimisation=True,
        source_sha_field_is_a_path=True,
        source_sha_example=acc[0]['source_sha'] if acc else None,
        per_view_k_g03_004_max_dev=float(max(np.abs(np.asarray(v['K'],float)-KHARD).max() for v in views4)) if views4 else None,
        n_raw_bug='extract() returns len(ka) and len(kb): a logical-and int, not a product',
        n_raw_type=type(CVM.extract(acc4[0]['view'], acc[0]['view'])['n_raw']).__name__ if (acc4 and acc) else None,
        views_with_missing_cache=sum(1 for v in views if not Path(v['RGB_cache']).exists()),
        note='run_corrective.py defines K = np.array(...) at module level and passes it to Y1.solve/'
             'shared_se3.optimize/S3.sampson_px, ignoring the per-view K returned by the adapter.')
    print(json.dumps(out, indent=1))
    Path(WS/'experiments/TASK-E4-W0-CROSSVIDEO-022-INDEPENDENT-AUDIT/results/T4_input_provenance.json').write_text(json.dumps(out, indent=1))


if __name__ == '__main__':
    main()
