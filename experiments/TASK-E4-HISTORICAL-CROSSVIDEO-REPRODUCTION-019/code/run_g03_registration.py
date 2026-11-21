"""Stage G: evaluate historical-style candidates on current G03 W0 (bounded, no new BA)."""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'adapters'))
sys.path.insert(0, '/home/liu/ring_first_3d_workspace/experiments/TASK-E4-RING-CROSS-VIDEO-018-REPAIR/code')
import coordinate_adapter as CA
import geometry as G, yaw_solver as YS

T = Path(__file__).resolve().parents[1]
FIX = Path('/home/liu/ring_first_3d_workspace/experiments/TASK-E4-RING-CROSS-VIDEO-018-REPAIR/fixtures')
K = np.array([[490., 0, 319.5], [0, 490., 179.5], [0, 0, 1.]])


def load_cams(name):
    d = np.load(FIX/name)
    return {str(i): d['c2w'][k] for k, i in enumerate(d['ids'])}, d


def load_matches(name):
    d = np.load(FIX/name)
    return [(str(d['a'][k]), str(d['b'][k]), d['pa'][int(d['off'][k]):int(d['off'][k+1])],
             d['pb'][int(d['off'][k]):int(d['off'][k+1])]) for k in range(len(d['a']))]


def directed(pa, pb, F):
    a = np.c_[pa, np.ones(len(pa))]; b = np.c_[pb, np.ones(len(pb))]
    Fa = (F @ a.T).T; Ftb = (F.T @ b.T).T
    d_f = np.abs(np.einsum('ij,ij->i', b, Fa)) / (np.hypot(Fa[:, 0], Fa[:, 1]) + 1e-12)
    d_r = np.abs(np.einsum('ij,ij->i', b, Fa)) / (np.hypot(Ftb[:, 0], Ftb[:, 1]) + 1e-12)
    return d_f, d_r


def eval_pairs(pairs, theta):
    f, r = [], []
    for (Ca, Cb, pa, pb, Ka, Kb) in pairs:
        F, _ = G.fundamental(G.rot_about_ring(Ca, np.deg2rad(theta)), Cb, Ka, Kb)
        a, b = directed(pa, pb, F)
        f.append(a); r.append(b)
    return np.concatenate(f), np.concatenate(r)


def main():
    c4, d4 = load_cams('camera_004.npz'); c5, d5 = load_cams('camera_005.npz')
    out = {}
    for tag in ('B', 'A'):
        ms = load_matches(('CROSS_VIDEO_B_ACCEPT_matches.npz' if tag=='B' else 'CROSS_VIDEO_A_QUARANTINE_matches.npz'))
        pairs = [(c4[a], c5[b], pa, pb, K, K) for a, b, pa, pb in ms]
        s = YS.solve(pairs)
        th47 = 47.24387768097719
        rows = []
        for name, theta in (('B0_yaw0', 0.0), ('B1_yaw47', th47), ('B2_search', s['theta'])):
            df_, dr_ = eval_pairs(pairs, theta)
            rows.append(dict(group=tag, candidate=name, theta=theta, n=len(df_),
                             fwd_median=float(np.median(df_)), fwd_mae=float(np.mean(df_)),
                             rev_median=float(np.median(dr_)), rev_mae=float(np.mean(dr_)),
                             fwd_inlier3=float(np.mean(df_ < 3)), rev_inlier3=float(np.mean(dr_ < 3))))
        out[tag] = rows
    pd.DataFrame(out['B'] + out['A']).to_csv(T/'metrics'/'G03_CROSS_VIDEO_CANDIDATES.csv', index=False)
    print(pd.DataFrame(out['B'] + out['A']).round(3).to_string(index=False))
    # holdout by 005 view: train on half of the 005 views, evaluate on the other half
    ms = load_matches('CROSS_VIDEO_B_ACCEPT_matches.npz')
    v5 = sorted({b for _, b, _, _ in ms})
    tr5, ho5 = set(v5[::2]), set(v5[1::2])
    P = lambda sel: [(c4[a], c5[b], pa, pb, K, K) for a, b, pa, pb in ms if b in sel]
    otr = YS.solve(P(tr5))
    df_, dr_ = eval_pairs(P(ho5), otr['theta'])
    pd.DataFrame([dict(train_views=len(tr5), holdout_views=len(ho5), theta_train=otr['theta'],
                       holdout_fwd_median=float(np.median(df_)), holdout_rev_median=float(np.median(dr_)),
                       holdout_n=len(df_), holdout_inlier3=float(np.mean(df_ < 3)))]).to_csv(
        T/'metrics'/'G03_HOLDOUT.csv', index=False)
    print('holdout:', round(otr['theta'], 2), round(float(np.median(df_)), 2), round(float(np.median(dr_)), 2))
    # negatives
    rng = np.random.default_rng(0)
    sh = [(c4[a], c5[b], pa, pb[rng.permutation(len(pb))], K, K) for a, b, pa, pb in ms]
    o_sh = YS.solve(sh)
    o_bad = YS.solve([(c4[a], c5[b], pa, pb, K, K) for a, b, pa, pb in ms[:20]])
    pd.DataFrame([dict(control='shuffle', theta=o_sh['theta'], status=o_sh['status'],
                       median_px=o_sh['median_px']),
                  dict(control='anti_shuffle', theta=o_bad['theta'], status=o_bad['status'],
                       median_px=o_bad['median_px'])]).to_csv(T/'metrics'/'G03_NEGATIVES.csv', index=False)
    print('negatives:', o_sh['status'], o_sh['theta'], '|', o_bad['status'], o_bad['theta'])
    # coordinate audit
    H = CA.yaw_about_axis(47.24387768097719)
    json.dump(dict(scene='G03 004/005', transforms=[CA.audit_transform(H, 'H_005<-004_yaw47')],
                   ring_center=[0, 0, 0], ring_normal=[0, 0, 1], ring_cad_mm=dict(R=5.6, r=0.6),
                   note='004 and 005 are both already expressed in the Ring CAD frame; the only free DoF is yaw about z.'),
              open(T/'metrics'/'COORDINATE_CONVENTION_AUDIT.json', 'w'), indent=1)
    # camera input audit
    rows = []
    for v, d, kind in (('004', d4, 'G03/004'), ('005', d5, 'G03/005')):
        for k, i in enumerate([str(x) for x in d['ids']]):
            Tk = np.asarray(d['c2w'][k]); chk = CA.check_pose(Tk)
            rows.append(dict(video=v, view=i, det=chk['det'], orth=chk['orth'], valid=chk['valid'],
                             admitted=str(d['admission'][k]) if 'admission' in d else 'ACCEPT'))
    pd.DataFrame(rows).to_csv(T/'metrics'/'G03_CAMERA_INPUT_AUDIT.csv', index=False)
    print('audit rows', len(rows))


if __name__ == '__main__':
    main()
