#!/usr/bin/env python3
"""R5 experiments: H candidates (Ring-only / +epipolar), joint triangulation under H,
C-group landmark recovery with correct H, old-vs-new pipeline, B/E camera perturbations."""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
WS = Path('/home/liu/ring_first_3d_workspace')
R5 = WS/'experiments/TASK-E4-W0-CROSSVIDEO-027-CORRECTIVE-R5'
sys.path.insert(0, str(R5/'core')); sys.path.insert(0, str(R5/'replay')); sys.path.insert(0, str(WS/'src'))
import r5_core as C
import ba_core_r4 as BA
from se3 import exp_se3
OUT = R5/'runs'; OUT.mkdir(parents=True, exist_ok=True)
F = None


def save(tag, **kw):
    d = OUT/tag; d.mkdir(parents=True, exist_ok=True)
    (d/'METRICS.json').write_text(json.dumps({k: v for k, v in kw.items() if k != 'H'}, indent=1, default=str))
    if 'H' in kw: np.savez(d/'RESULT.npz', H=np.asarray(kw['H']), **{k: np.asarray(v) for k, v in kw.items() if k in ('X', 'X_init')})


def main():
    global F
    F = C.build_fixed(sub=8)
    sc = F['sc']
    all_ids = list(range(len(F['X0'])))
    fit_ids = all_ids[:8]; ho_ids = all_ids[8:]
    cams0 = {c: np.asarray(sc['cams'][c][1], float) for c in sc['cams']}
    rows = []
    # ---------- H candidates ----------
    allc, keep = C.ring_candidates(F, yaw_step=15, n_refine=12, fit_ids=fit_ids)
    pd.DataFrame([dict(yaw=v['yaw_init'], ring=v['ring'], epi=v['epi'], score=v['score'],
                       H_rot=C.gt_metrics(F, v['H'], np.zeros((0, 3)), [])['H_rot'])
                  for v in keep]).to_csv(OUT/'H_CANDIDATES.csv', index=False)
    best_ring = min(keep, key=lambda d: d['ring'])
    best_full = min(keep, key=lambda d: d['score'])
    gtH = sc['H']
    Hs = dict(H0=np.eye(4), H1=best_ring['H'], H2=best_full['H'], H3=gtH)
    for name, H in Hs.items():
        X, ids = C.triangulate_under_H(F, H, min_views=3)
        m = C.gt_metrics(F, H, X, ids)
        # T2: X-only refinement with this H (cameras fixed)
        camsH = {c: (H @ np.asarray(sc['cams'][c][1], float) if sc['cams'][c][0] == '004'
                     else np.asarray(sc['cams'][c][1], float)) for c in sc['cams']}
        P = C.make_problem(F, camsH)
        Hf, Xr, info = C.solve(P, X, 'M1', H0=np.eye(4), budget=60)
        mr = C.gt_metrics(F, H, Xr, ids)
        rows.append(dict(stage='T1_T2', init=name, H_rot=m['H_rot'], H_trans=m['H_trans'],
                         lm_T1=m['lm_med'], lm_T2=mr['lm_med'], n=len(ids),
                         epi=best_full['epi'] if name == 'H2' else (best_ring['epi'] if name == 'H1' else None),
                         ring=(best_ring['ring'] if name == 'H1' else (best_full['ring'] if name == 'H2' else None)),
                         success=info['success'], nfev=info['nfev']))
        save(f'T_{name}', H=H, X=X, X_init=X)
        print('T', name, round(m['H_rot'], 4), round(m['lm_med'], 3), '->', round(mr['lm_med'], 3), flush=True)
    pd.DataFrame(rows).to_csv(OUT/'TRIANGULATION_BY_H.csv', index=False)
    # ---------- C group: correct H, X perturbed ----------
    crows = []
    camsH_gt = {c: (gtH @ np.asarray(sc['cams'][c][1], float) if sc['cams'][c][0] == '004'
                    else np.asarray(sc['cams'][c][1], float)) for c in sc['cams']}
    Pgt = C.make_problem(F, camsH_gt)
    Xbase, ids0 = C.triangulate_under_H(F, gtH)
    for tag, mm, kind, Huse in (('C0', 0.0, 'random', gtH), ('C1', 1.0, 'random', gtH), ('C3', 3.0, 'random', gtH),
                                ('C3d', 3.0, 'depth', gtH), ('C3p', 3.0, 'perp', gtH),
                                ('C3w', 3.0, 'random', Hs['H0']), ('C3h2', 3.0, 'random', Hs['H2'])):
        rng = np.random.default_rng(0)
        if mm:
            if kind == 'depth':
                d = np.tile([0., 0., 1.], (len(Xbase), 1))*np.sign(rng.normal(size=(len(Xbase), 1)))
            elif kind == 'perp':
                dd = rng.normal(size=(len(Xbase), 2)); dd /= np.linalg.norm(dd, axis=1, keepdims=True)
                d = np.c_[dd*mm, np.zeros(len(Xbase))]; mm_use = 1.0
            else:
                d = rng.normal(size=Xbase.shape); d /= np.linalg.norm(d, axis=1, keepdims=True)
            Xp = Xbase + d*(1.0 if kind == 'perp' else mm)
        else:
            Xp = Xbase.copy()
        cams_use = {c: (Huse @ np.asarray(sc['cams'][c][1], float) if sc['cams'][c][0] == '004'
                        else np.asarray(sc['cams'][c][1], float)) for c in sc['cams']}
        P = C.make_problem(F, cams_use)
        Hf, Xr, info = C.solve(P, Xp, 'M1', H0=np.eye(4), budget=80)
        e0 = float(np.median(np.linalg.norm(Xp - sc['X'][ids0], axis=1)))
        e1 = float(np.median(np.linalg.norm(Xr - sc['X'][ids0], axis=1)))
        crows.append(dict(tag=tag, mm=mm, kind=kind, H_init_rot=C.gt_metrics(F, Huse, Xp, ids0)['H_rot'],
                          lm_init=e0, lm_final=e1, success=info['success'], nfev=info['nfev']))
        save(f'{tag}', H=Huse, X=Xr, X_init=Xp)
        print('C', tag, round(e0, 3), '->', round(e1, 3), info['success'], flush=True)
    pd.DataFrame(crows).to_csv(OUT/'C_GROUP.csv', index=False)
    # ---------- pipelines old vs new ----------
    prows = []
    for tag, H_init in (('old_H0', np.eye(4)), ('old_H1ring', Hs['H1']), ('new_H2', Hs['H2'])):
        P = C.make_problem(F, cams0)
        H_m2, X0f, i2 = C.solve(P, F['X0'], 'M2', H0=H_init, budget=100)
        Xt, idt = C.triangulate_under_H(F, H_m2)
        camsH = {c: (H_m2 @ np.asarray(sc['cams'][c][1], float) if sc['cams'][c][0] == '004'
                     else np.asarray(sc['cams'][c][1], float)) for c in sc['cams']}
        Pj = C.make_problem(F, camsH)
        H_m3, X3, i3 = C.solve(Pj, Xt, 'M3b', H0=H_m2, budget=60)
        m = C.gt_metrics(F, H_m3, X3, np.arange(len(X3)))
        prows.append(dict(pipe=tag, H_init_rot=C.gt_metrics(F, H_init, np.zeros((0, 3)), [])['H_rot'],
                          H_M2=m['H_rot'], H_M3=m['H_rot'], H_trans=m['H_trans'], lm=m['lm_med'],
                          nfev=i2['nfev']+i3['nfev'], success=bool(i2['success'] and i3['success'])))
        print('PIPE', tag, round(prows[-1]['H_M2'], 4), '->', round(m['H_rot'], 4), round(m['lm_med'], 3), flush=True)
    pd.DataFrame(prows).to_csv(OUT/'PIPELINES.csv', index=False)
    # ---------- B: 0.5 deg camera perturb, then M2/M3b/M4 ----------
    brows = []
    for deg, mm in ((0.25, 0.0), (0.5, 0.0), (0.0, 0.25)):
        cams_p, info = C.perturb_cams(sc, C.S.C4, np.deg2rad(deg), mm, seed=1)
        for mode, rel in (('M2', ()), ('M3b', ()), ('M4', (C.S.C4[1], C.S.C4[2]))):
            P = C.make_problem(F, cams_p, released=rel)
            Hf, Xf, inf = C.solve(P, F['X0'], mode, H0=np.eye(4), budget=80)
            m = C.gt_metrics(F, Hf, Xf, np.arange(len(Xf)))
            brows.append(dict(deg=deg, mm=mm, mode=mode, H_rot=m['H_rot'], lm=m['lm_med'],
                              n_params=inf['n_params'], success=inf['success'], nfev=inf['nfev']))
            print('B', deg, mm, mode, round(m['H_rot'], 4), round(m['lm_med'], 3), inf['n_params'], flush=True)
    pd.DataFrame(brows).to_csv(OUT/'B_CAMERA.csv', index=False)
    print('DONE')


if __name__ == '__main__':
    main()
