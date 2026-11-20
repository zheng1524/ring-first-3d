"""Task A/E: replay camera validation from frozen artifacts; no solver is run.

Outputs (audit root):
  CAMERA_VALIDATION_REPLAY.csv
  CAMERA_BRANCH_DIAGNOSTICS.csv
"""
import numpy as np
import pandas as pd
import audit_common as A

MATURE = [(g, v) for g in A.GROUPS for v in A.VIDEOS
          if A.ba_cameras(g, v) is not None and A.tracks_path(g, v) is not None]


def held_reprojection(cams, nv, tr, K):
    """Leave-one-view-out triangulation on held tracks (spirit of v6 validate_select.py)."""
    xy = tr['xy']; held = np.asarray(tr['held']).astype(bool)
    errs = {i: [] for i in range(nv)}; pos = {i: [] for i in range(nv)}
    for i in range(nv):
        if cams.get(i) is None:
            continue
        for t in np.flatnonzero(held):
            u = xy[t, i]
            if not np.isfinite(u[0]):
                continue
            others = [j for j in range(nv)
                      if j != i and np.isfinite(xy[t, j, 0]) and cams.get(j) is not None]
            if len(others) < 2:
                continue
            best, bd = None, -1.0
            for a in range(len(others)):
                for b in range(a + 1, len(others)):
                    j, k = others[a], others[b]
                    d = float(np.linalg.norm(cams[j][:3, 3] - cams[k][:3, 3]))
                    if d > bd:
                        bd, best = d, (j, k)
            X = A.triangulate(xy[t, best[0]], xy[t, best[1]], cams[best[0]], cams[best[1]], K)
            if X is None:
                continue
            uv, z = A.project(X[None], cams[i], K)
            if not np.isfinite(uv).all() or not np.isfinite(z[0]):
                continue
            errs[i].append(float(np.linalg.norm(uv[0] - u)))
            pos[i].append(bool(z[0] > 0))
    return errs, pos


def main():
    rows, diag = [], []
    for g, v in MATURE:
        ba = A.ba_cameras(g, v); ids = ba['ids']; nv = len(ids)
        trf = np.load(A.tracks_path(g, v))
        tr = dict(xy=trf['xy'][:, :nv], held=trf['held'])
        runs = {}
        rp = A.ba_dir(g, v).parent / 'metrics/LOCAL_CALIBRATION_RUNS.json'
        if rp.exists():
            for r in A.jread(rp):
                ba_rec = r.get('local_BA') or {}
                runs[r['version']] = dict(success=ba_rec.get('success'),
                                          nfev=ba_rec.get('nfev'),
                                          obj=ba_rec.get('training_soft_l1_objective'),
                                          status=r.get('status'))
        fit = A.instance_views(g, v)
        byid = {x['meta']['id']: x for x in fit}
        caches = {cid: A.load_cache(byid[cid]) for cid in ids if cid in byid}
        final = {}
        for cid in ids:
            c = A.final_camera(g, v, cid)
            if c and c.get('c2w_mm'):
                final[cid] = np.asarray(c['c2w_mm'], float)
        Ks = {cid: caches[cid]['K'] for cid in caches}
        K0 = Ks[ids[0]] if ids and ids[0] in Ks else next(iter(Ks.values()))

        for i, cid in enumerate(ids):
            rec = dict(group=g, video=v, view=cid,
                       rot_v0_v1_deg=np.nan, center_v0_v1_mm=np.nan,
                       rot_final_v0_deg=np.nan, rot_final_v1_deg=np.nan,
                       center_final_v0_mm=np.nan, center_final_v1_mm=np.nan,
                       ring_mae_final_px=np.nan, ring_mae_v0_px=np.nan, ring_mae_v1_px=np.nan,
                       ba_success_v0=runs.get(0, {}).get('success'),
                       ba_success_v1=runs.get(1, {}).get('success'),
                       ba_obj_v0=runs.get(0, {}).get('obj'),
                       ba_obj_v1=runs.get(1, {}).get('obj'),
                       final_camera_present=cid in final)
            if 0 in ba and 1 in ba:
                rec['rot_v0_v1_deg'] = A.rot_deg(ba[0][i][:3, :3], ba[1][i][:3, :3])
                rec['center_v0_v1_mm'] = float(np.linalg.norm(ba[0][i][:3, 3] - ba[1][i][:3, 3]))
            x = byid.get(cid)
            if x is not None and cid in caches:
                K = caches[cid]['K']; op = A.obs_path(g, v, cid)
                if op and op.exists():
                    q = np.load(op)['q_train']
                    if cid in final:
                        rec['ring_mae_final_px'] = A.torus_mae(final[cid], K, q)['MAE']
                    if 0 in ba:
                        rec['ring_mae_v0_px'] = A.torus_mae(ba[0][i], K, q)['MAE']
                    if 1 in ba:
                        rec['ring_mae_v1_px'] = A.torus_mae(ba[1][i], K, q)['MAE']
            if cid in final:
                if 0 in ba:
                    rec['rot_final_v0_deg'] = A.rot_deg(final[cid][:3, :3], ba[0][i][:3, :3])
                    rec['center_final_v0_mm'] = float(np.linalg.norm(final[cid][:3, 3] - ba[0][i][:3, 3]))
                if 1 in ba:
                    rec['rot_final_v1_deg'] = A.rot_deg(final[cid][:3, :3], ba[1][i][:3, :3])
                    rec['center_final_v1_mm'] = float(np.linalg.norm(final[cid][:3, 3] - ba[1][i][:3, 3]))
            diag.append(rec)

        sets = {}
        for ver in (0, 1):
            if ver in ba:
                sets[f'NATIVE_CALIBRATION_{ver}'] = {i: ba[ver][i] for i in range(nv)}
        if final:
            sets['FINAL_CAMERA_RESULT'] = {i: final.get(cid) for i, cid in enumerate(ids)}
        for name, cams in sets.items():
            errs, poss = held_reprojection(cams, nv, tr, K0)
            for i, cid in enumerate(ids):
                if cams.get(i) is None or cid not in caches or not A.obs_path(g, v, cid):
                    continue
                K = caches[cid]['K']; q = np.load(A.obs_path(g, v, cid))['q_train']
                hm = np.arange(len(q)) % 5 == 0
                rtr = A.torus_mae(cams[i], K, q[~hm]); rhe = A.torus_mae(cams[i], K, q[hm])
                e = errs.get(i, []); pp = poss.get(i, [])
                rows.append(dict(group=g, video=v, view=cid, camera_set=name,
                                 ring_MAE_train_px=rtr['MAE'], ring_P95_train_px=rtr['p95'],
                                 ring_MAE_held_audit_px=rhe['MAE'], ring_P95_held_audit_px=rhe['p95'],
                                 ring_points_train=int((~hm).sum()), ring_points_held=int(hm.sum()),
                                 held_reproj_N=len(e),
                                 held_reproj_MAE_px=float(np.mean(np.abs(e))) if e else np.nan,
                                 held_reproj_p95_px=float(np.percentile(np.abs(e), 95)) if e else np.nan,
                                 held_positive_fraction=float(np.mean(pp)) if pp else np.nan,
                                 visible_tracks=int(np.isfinite(tr['xy'][:, i, 0]).sum()),
                                 held_tracks_total=int(np.asarray(tr['held']).sum())))
    pd.DataFrame(rows).to_csv(A.AUD / 'CAMERA_VALIDATION_REPLAY.csv', index=False)
    pd.DataFrame(diag).to_csv(A.AUD / 'CAMERA_BRANCH_DIAGNOSTICS.csv', index=False)
    print('replay rows', len(rows), '| branch rows', len(diag), '| mature', MATURE)


if __name__ == '__main__':
    main()
