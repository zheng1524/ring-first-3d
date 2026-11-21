"""Level-1 numerical replay of historical 020 using its own saved artifacts."""
import json, sys
from pathlib import Path
import numpy as np

P = Path('/home/liu/polyp_research/ring-first-3d/experiments/TASK-E4-RING-SIFT-SYMMETRIC-REGISTRATION-020')
T = Path(__file__).resolve().parents[1]


def main():
    r = json.loads((P/'results'/'R3.json').read_text())
    H = np.asarray(r['T'], float)
    r0 = json.loads((P/'results'/'R0.json').read_text())
    H0 = np.asarray(r0['T'], float)
    nm = json.loads((P/'features'/'CROSS_NAMED_3D_TRACK_PAIRS.json').read_text())['matches']
    def resolve(name):
        p1 = P/'landmarks'/name
        p2 = P.parent/'TASK-E4-RING-POLYP-REGISTRATION-019'/'landmarks'/name
        if p1.exists():
            return p1
        if p2.exists():
            return p2
        raise SystemExit(f'MISSING_HISTORICAL_LANDMARKS {name}')
    pa_, pb_ = resolve('CROSS_004.npz'), resolve('INDEPENDENT_005.npz')
    A = np.load(pa_); B = np.load(pb_)
    XA, XB = np.asarray(A['X'], float), np.asarray(B['X'], float)
    out = []
    for tag, M in (('H_R3', H), ('inv_H_R3', np.linalg.inv(H)),
                   ('H_R0', H0), ('inv_H_R0', np.linalg.inv(H0))):
        d = []
        for p in nm:
            x4 = XA[p['landmark004']]; x5 = XB[p['landmark005']]
            y = (M @ np.r_[x4, 1.0])[:3]
            d.append(float(np.linalg.norm(y - x5)))
        d = np.array(d)
        out.append(dict(transform=tag, n=len(d), median_mm=float(np.median(d)),
                        mean_mm=float(np.mean(d)), max_mm=float(np.max(d)),
                        within_0_75mm=int((d < 0.75).sum()),
                        within_1mm=int((d < 1.0).sum()),
                        det=float(np.linalg.det(M[:3, :3])),
                        orth=float(np.abs(M[:3, :3] @ M[:3, :3].T - np.eye(3)).max())))
    import pandas as pd
    df = pd.DataFrame(out)
    (T/'metrics').mkdir(exist_ok=True)
    df.to_csv(T/'metrics'/'HISTORICAL_REPLAY_COMPARISON.csv', index=False)
    print(df.round(6).to_string(index=False))
    print('landmark sources:', pa_, pb_)
    # historical reference values (from 020 TECHNICAL_REPORT / metrics)
    ref = [
        dict(metric='holdout_polyp_iou', arm='R0', historical=0.893435),
        dict(metric='holdout_polyp_iou', arm='R3', historical=0.901429),
        dict(metric='holdout_ring_inner_mae_px', arm='R0', historical=1.238243),
        dict(metric='holdout_ring_inner_mae_px', arm='R3', historical=1.004331),
        dict(metric='holdout_ring_outer_mae_px', arm='R0', historical=1.334476),
        dict(metric='holdout_ring_outer_mae_px', arm='R3', historical=1.163742),
        dict(metric='hero_support_0p5mm', arm='R0', historical=0.345008),
        dict(metric='hero_support_0p5mm', arm='R3', historical=0.340757),
        dict(metric='hero_conditional_mae_mm', arm='R0', historical=0.825983),
        dict(metric='hero_conditional_mae_mm', arm='R3', historical=0.803390),
    ]
    (T/'metrics'/'HISTORICAL_REFERENCE_VALUES.csv').write_text(pd.DataFrame(ref).to_csv(index=False))
    return df, H, H0


if __name__ == '__main__':
    main()
