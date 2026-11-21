"""Level-1 offline reproduction of the historical 020 3D-RANSAC result (no legacy paths)."""
import json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import historical_ransac as HR

R = Path(__file__).resolve().parents[1]


def main():
    nm = json.loads((R/'fixtures'/'CROSS_NAMED_3D_TRACK_PAIRS.json').read_text())['matches']
    X4 = np.array([x['X004'] for x in nm]); X5 = np.array([x['X005'] for x in nm])
    out = HR.run(X4, X5)
    ref = json.loads((R/'fixtures'/'NAMED_LANDMARK_RIGID_PROPOSAL.json').read_text())
    res = dict(named_pairs=out['named_pairs'], within_075mm=out['within_075mm'],
               median_mm=out['residual_mm']['median'], center_mm=out['center_mm'], tilt_deg=out['tilt_deg'],
               historical_within_075mm=ref['within_075mm'],
               match=bool(out['within_075mm'] == ref['within_075mm']))
    for tag, f in (('R0', 'R0.json'), ('R3', 'R3.json')):
        H = np.array(json.loads((R/'fixtures'/f).read_text())['T'])
        d = np.linalg.norm(X4 - (X5 @ H[:3, :3].T + H[:3, 3]), axis=1)
        res[tag] = dict(within_075mm=int((d <= 0.75).sum()), median_mm=float(np.median(d)))
    print(json.dumps(res, indent=1))
    (R/'metrics'/'OFFLINE_REPRODUCTION.json').write_text(json.dumps(res, indent=1))


if __name__ == '__main__':
    main()
