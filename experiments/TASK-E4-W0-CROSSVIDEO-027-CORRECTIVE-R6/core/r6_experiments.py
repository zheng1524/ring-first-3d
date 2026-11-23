#!/usr/bin/env python3
"""R6: H0/H1/H2/H3 + end-to-end old/new pipelines + HOLDOUT + E1 reference-camera perturbation + F0/F1."""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
WS = Path('/home/liu/ring_first_3d_workspace')
R6 = WS/'experiments/TASK-E4-W0-CROSSVIDEO-027-CORRECTIVE-R6'
sys.path.insert(0, str(R6/'core')); sys.path.insert(0, str(R6/'replay')); sys.path.insert(0, str(WS/'src'))
import r6_core as C
OUT = R6/'runs'; OUT.mkdir(parents=True, exist_ok=True)


def save(tag, **kw):
    d = OUT/tag; d.mkdir(parents=True, exist_ok=True)
    (d/'METRICS.json').write_text(json.dumps({k: v for k, v in kw.items() if not isinstance(v, np.ndarray)}, indent=1, default=str))
    np.savez(d/'RESULT.npz', **{k: np.asarray(v) for k, v in kw.items() if isinstance(v, np.ndarray)})


def run_pipeline(F, tag, mode, H_init, cams=None, released=(), budget=(50, 50)):
    sc = F['sc']; cams = cams or {c: np.asarray(sc['cams'][c][1], float) for c in sc['cams']}
    H0 = np.eye(4) if H_init is None else H_init
    if mode == 'old':
        P = C.make_problem(F, np.eye(4), cams=cams)
        H1, X1, i1 = C.solve(P, C.F['X0'] if False else F['X0'], 'M2', H0=H0, budget=budget[0])
        Xt, idt = C.triangulate_under_H(F, H1, cams=cams)
        P2 = C.make_problem(F, H1, cams=cams)
        H2v, X2, i2 = C.solve(P2, Xt, 'M3b', H0=H1, budget=budget[1])
    else:
        Xt, idt = C.triangulate_under_H(F, H0, cams=cams)
        P2 = C.make_problem(F, H0, cams=cams)
        H2v, X2, i2 = C.solve(P2, Xt, 'M3b', H0=H0, budget=budget[1]); i1 = dict(nfev=0, success=None)
    m = C.gt_metrics(F, H2v, X2, np.arange(len(X2)))
    return dict(tag=tag, mode=mode, H_init_rot=C.gt_metrics(F, H0, np.zeros((0, 3)), [])['H_rot'],
                H_first=i1.get('nfev'), H_final=m['H_rot'], H_trans=m['H_trans'], lm=m['lm_med'],
                nfev=int(i1.get('nfev', 0)+i2['nfev']), success=bool(i2['success'])), H2v, X2


def main():
    F = C.build_fixed(sub=8)
    sc = F['sc']; cams = {c: np.asarray(sc['cams'][c][1], float) for c in sc['cams']}
    ids = list(range(len(F['X0'])))
    rng = np.random.default_rng(2026)
    fit_ids = sorted(rng.choice(ids, size=8, replace=False).tolist())
    ho_ids = [i for i in ids if i not in fit_ids]
    json.dump(dict(fit=fit_ids, holdout=ho_ids, seed=2026), open(OUT/'SPLIT.json', 'w'), indent=1)
    # ---- H1/H2 ----
    cands = C.ring_candidates(F, fit_ids, cams, yaw_step=15)
    rows = []
    for k, c in enumerate(cands):
        Hm = C.gt_metrics(F, c['H'], np.zeros((0, 3)), [])
        rows.append(dict(rank=k, yaw_initial=c['yaw_initial'], ring_init=c['ring_initial'], ring=c['ring'],
                         epi=c['epi'], score=c['score'], refine_rot=c['refine_rot_deg'], refine_trans=c['refine_trans_mm'],
                         H_rot=Hm['H_rot'], H_trans=Hm['H_trans'], nfev=c['nfev'], success=c['success']))
    pd.DataFrame(rows).to_csv(OUT/'H_CANDIDATES.csv', index=False)
    best = cands[0]
    Hs = dict(H0=np.eye(4), H1=sorted(cands, key=lambda d: d['ring'])[0]['H'], H2=best['H'], H3=sc['H'])
    # ---- triangulation under each H ----
    trows = []
    for name, H in Hs.items():
        X, idt = C.triangulate_under_H(F, H, cams=cams)
        m = C.gt_metrics(F, H, X, idt)
        trows.append(dict(init=name, H_rot=m['H_rot'], H_trans=m['H_trans'], lm=m['lm_med'], n=len(idt)))
        np.savez(OUT/(f'T_{name}.npz'), H=np.asarray(H), X=X, ids=idt)
    pd.DataFrame(trows).to_csv(OUT/'TRIANGULATION_BY_H.csv', index=False)
    # ---- end-to-end pipelines (fair local budget) ----
    prows = []
    for name, H_init in (('old_H0', np.eye(4)), ('new_H2', Hs['H2'])):
        r, Hf, Xf = run_pipeline(F, name, 'new' if name.startswith('new') else 'old', H_init, cams=cams)
        save(name, H=Hf, X=Xf); prows.append(r)
        print('PIPE', name, round(r['H_final'], 4), round(r['lm'], 4), r['nfev'], flush=True)
    pd.DataFrame(prows).to_csv(OUT/'PIPELINES.csv', index=False)
    # ---- HOLDOUT evaluation for the two pipelines ----
    hrows = []
    for name in ('old_H0', 'new_H2'):
        z = np.load(OUT/name/'RESULT.npz'); Hf, Xf = z['H'], z['X']
        for grp, gid in (('fit', fit_ids), ('holdout', ho_ids)):
            errs = []
            for c, i, uv in F['obs']:
                if i not in gid: continue
                idx = list(range(len(F['X0']))).index(i) if i < len(F['X0']) else None
                if idx is None: continue
                Cw = C.cam_world(cams[c], sc['cams'][c][0], Hf)
                p, zz = C.BA.project(Xf[idx], Cw, sc['K_of'][c])
                errs.append(np.linalg.norm(p - np.asarray(uv, float)))
            hrows.append(dict(pipe=name, group=grp, n=len(errs), rgb_med=float(np.median(errs)) if errs else None,
                              rgb_p90=float(np.percentile(errs, 90)) if errs else None))
    pd.DataFrame(hrows).to_csv(OUT/'HOLDOUT_RGB.csv', index=False)
    # ---- E1: perturb 005 cameras, redo H2 init + joint triangulation ----
    erows = []
    for deg, mm in ((0.25, 0.0), (0.5, 0.0), (0.0, 0.25)):
        cams_p, info = C.perturb_cams(sc, C.S.C5, np.deg2rad(deg), mm, seed=11, which=('005',))
        X0p, _ = C.S.triangulate([o for o in F['obs'] if sc['cams'][o[0]][0] == '005'],
                                 {c: ('x', cams_p[c]) for c in C.S.C5}, sc['K_of'], 12)
        Fp = dict(F); Fp['X0'] = X0p
        icands = C.ring_candidates(Fp, fit_ids, cams_p, yaw_step=30)
        H2p = icands[0]['H']
        Xp, idp = C.triangulate_under_H(Fp, H2p, cams=cams_p)
        m = C.gt_metrics(Fp, H2p, Xp, idp)
        X005err = float(np.median(np.linalg.norm(X0p - sc['X'][:len(X0p)], axis=1)))
        erows.append(dict(deg=deg, mm=mm, X0_err=X005err, H2_rot=m['H_rot'], lm=m['lm_med'],
                          epi=icands[0]['epi'], ring=icands[0]['ring']))
        print('E1', deg, mm, round(X005err, 3), round(m['H_rot'], 3), round(m['lm_med'], 3), flush=True)
    pd.DataFrame(erows).to_csv(OUT/'E1_REFERENCE_CAMERA.csv', index=False)
    print('DONE')


if __name__ == '__main__':
    main()
