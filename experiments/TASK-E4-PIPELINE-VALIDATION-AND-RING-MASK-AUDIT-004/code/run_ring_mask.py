"""Task C: offline Ring observation comparison M0/M1/M2/M3 on frozen inputs and fixed cameras.

Nothing is re-solved. Cameras come from CAMERA_RESULT.json (the cameras actually
used downstream). Original labels are never written back; all variants are copies.

M0 baseline          : native observe() on the raw Ring mask
M1 main component    : largest Ring connected component only (others kept in labels, not used for observation)
M2 DXY hole fill + M1: re-implemented DXY small-hole rule on a copy, then main component
M3 fit-level (2D only): M2 + 5x5 close/open + RANSAC ellipse; CAD residual marked N/A by design
"""
import numpy as np
import pandas as pd
import cv2
import audit_common as A


def classify_discarded(labels, cc, main, comps):
    """Heuristic, explicitly allowed to return UNKNOWN. Never asserts 'wrong'."""
    pm = labels == 1
    near_polyp = cv2.dilate(pm.astype(np.uint8), np.ones((9, 9), np.uint8)) > 0
    out = []
    for c in comps:
        if c['index'] == main:
            continue
        m = cc == c['index']
        ys, xs = np.nonzero(m)
        touch_border = (xs.min() <= 1 or ys.min() <= 1 or xs.max() >= labels.shape[1] - 2 or ys.max() >= labels.shape[0] - 2)
        npolyp = int(near_polyp[m].sum())
        if touch_border:
            k = 'POSSIBLE_REAL_ARC_FRAME_TRUNCATED'
        elif npolyp >= max(3, int(0.5 * m.sum())):
            k = 'POSSIBLE_REAL_ARC_OCCLUSION_SPLIT'
        elif c['area_px'] < 30:
            k = 'LIKELY_NOISE_TINY'
        else:
            k = 'UNKNOWN'
        out.append(dict(index=c['index'], area_px=c['area_px'], classification=k, near_polyp_px=npolyp))
    return out


def elliptic_ransac(pts, iters=200, rng_seed=42):
    rng = np.random.default_rng(rng_seed)
    pts = np.asarray(pts, float)
    if len(pts) < 5:
        return None
    best = None
    for _ in range(iters):
        idx = rng.choice(len(pts), size=min(20, len(pts)), replace=False)
        try:
            e = cv2.fitEllipseDirect(pts[idx].astype(np.float32))
        except cv2.error:
            continue
        (cx, cy), (d1, d2), ang = e
        thr = max(2.5, 0.015 * 2 * max(d1, d2))
        # radial residual in normalized ellipse frame
        th = np.deg2rad(ang)
        R = np.array([[np.cos(th), np.sin(th)], [-np.sin(th), np.cos(th)]])
        q = (pts - [cx, cy]) @ R.T
        r = (q[:, 0] / (d1 / 2)) ** 2 + (q[:, 1] / (d2 / 2)) ** 2
        res = np.abs(np.sqrt(np.maximum(r, 1e-12)) - 1) * min(d1, d2) / 2
        inl = res <= thr
        score = (int(inl.sum()), -float(res[inl].mean()) if inl.any() else -1e9)
        if best is None or score > best[0]:
            best = (score, e, inl, res)
    if best is None:
        return None
    _, e, inl, res = best
    if inl.sum() >= 5:
        try:
            e = cv2.fitEllipseDirect(pts[inl].astype(np.float32))
            (cx, cy), (d1, d2), ang = e
            th = np.deg2rad(ang); R = np.array([[np.cos(th), np.sin(th)], [-np.sin(th), np.cos(th)]])
            q = (pts - [cx, cy]) @ R.T
            r = (q[:, 0] / (d1 / 2)) ** 2 + (q[:, 1] / (d2 / 2)) ** 2
            res = np.abs(np.sqrt(np.maximum(r, 1e-12)) - 1) * min(d1, d2) / 2
            inl = res <= max(2.5, 0.015 * 2 * max(d1, d2))
        except cv2.error:
            pass
    # 36-bin angular coverage around centroid
    ang_pts = np.arctan2(pts[:, 1] - e[0][1], pts[:, 0] - e[0][0])
    bins = np.unique(((ang_pts + np.pi) / (2 * np.pi) * 36).astype(int) % 36)
    # 4-sector stability of axis lengths
    st = []
    for s in range(4):
        m = ((ang_pts + np.pi) / (2 * np.pi) * 4).astype(int) % 4 == s
        if m.sum() >= 5:
            try:
                ee = cv2.fitEllipseDirect(pts[m].astype(np.float32))
                st.append(max(ee[1]))
            except cv2.error:
                pass
    stab = float(np.ptp(st) / np.mean(st)) if len(st) >= 2 and np.mean(st) > 0 else float('nan')
    return dict(ellipse=e, inlier_ratio=float(inl.mean()), residual_mean=float(res.mean()),
                arc_coverage=len(bins) / 36.0, sector_stability=stab, n_points=len(pts))


def variant_stats(C, K, q):
    s = A.torus_mae(C, K, q)
    from ring_first_3d.mainline.native.camera import torus_contours
    from scipy.spatial import cKDTree
    d = cKDTree(torus_contours(np.asarray(C), K).reshape(-1, 2)).query(np.asarray(q))[0]
    s['within3'] = float(np.mean(np.asarray(d) <= 3.0))
    return s


def main():
    rows = []
    for g in A.GROUPS:
        for v in A.VIDEOS:
            for x in A.instance_views(g, v):
                cid = x['meta']['id']
                cam = A.final_camera(g, v, cid)
                if not cam or not cam.get('c2w_mm'):
                    continue
                C = np.asarray(cam['c2w_mm'], float)
                cache = A.load_cache(x); labels = cache['labels']; K = cache['K']
                ring = labels == 2
                if ring.sum() == 0:
                    continue
                ncomp, comps, cc = A.components(labels)
                main = comps[0]['index']
                # ---- M0
                q0, _ = A.observe_train(labels)
                s0 = variant_stats(C, K, q0)
                # ---- M1
                l1 = A.keep_only(labels, cc, main)
                q1, _ = A.observe_train(l1)
                s1 = variant_stats(C, K, q1) if len(q1) >= 20 else dict(N=len(q1), MAE=np.nan, p95=np.nan, within3=np.nan)
                # ---- M2
                l2f, fill, info = A.dxy_hole_fill(labels)
                _, comps2, cc2 = A.components(l2f)
                l2 = A.keep_only(l2f, cc2, comps2[0]['index']) if comps2 else l2f
                q2, _ = A.observe_train(l2)
                s2 = variant_stats(C, K, q2) if len(q2) >= 20 else dict(N=len(q2), MAE=np.nan, p95=np.nan, within3=np.nan)
                # ---- M3 (fit level only)
                m3 = None
                if comps2:
                    mo = A.close_open(l2f)
                    pts = A.edge_pts(mo)
                    m3 = elliptic_ransac(pts) if len(pts) >= 5 else None
                # ---- same-point-set decomposition of M0
                main_mask = cc == main
                bd = A.observed_boundary(labels)
                # edge() emits half-pixel coordinates; a rounded label lookup misclassifies ~half
                # of them. Assign each boundary point to the nearest RING pixel instead
                # (this reproduces 002's RING_COMPONENT_DIAGNOSTICS split 113/15).
                from scipy.spatial import cKDTree
                mpix = np.c_[np.nonzero(main_mask)[1], np.nonzero(main_mask)[0]]
                opix = np.c_[np.nonzero(ring & ~main_mask)[1], np.nonzero(ring & ~main_mask)[0]]
                dm = cKDTree(mpix).query(bd)[0]
                do = cKDTree(opix).query(bd)[0] if len(opix) else np.full(len(bd), np.inf)
                is_main = dm <= do
                idx = np.linspace(0, len(bd) - 1, min(128, len(bd)), dtype=int)
                sel = is_main[idx]
                q0a, q0b = q0[sel], q0[~sel]
                sa = variant_stats(C, K, q0a) if len(q0a) >= 5 else dict(MAE=np.nan, p95=np.nan)
                sb = variant_stats(C, K, q0b) if len(q0b) >= 5 else dict(MAE=np.nan, p95=np.nan)
                fb = bd; fmain = is_main
                r_all_main = variant_stats(C, K, fb[fmain]) if fmain.sum() >= 5 else dict(MAE=np.nan, N=0)
                r_all_disc = variant_stats(C, K, fb[~fmain]) if (~fmain).sum() >= 5 else dict(MAE=np.nan, N=0)
                disc = classify_discarded(labels, cc, main, comps)
                rows.append(dict(
                    group=g, video=v, view=cid,
                    ring_px_total=int(ring.sum()), n_components=ncomp,
                    main_area_px=int(comps[0]['area_px']),
                    r_main=float(comps[0]['area_px'] / ring.sum()),
                    r_discarded=float(1 - comps[0]['area_px'] / ring.sum()),
                    discarded_area_px=int(ring.sum() - comps[0]['area_px']),
                    discarded_detail=';'.join(f"{d['index']}:{d['area_px']}:{d['classification']}" for d in disc),
                    M0_qN=s0['N'], M0_ring_MAE_px=s0['MAE'], M0_ring_p95_px=s0['p95'], M0_within3px=s0['within3'],
                    M1_qN=s1['N'], M1_ring_MAE_px=s1['MAE'], M1_ring_p95_px=s1['p95'], M1_within3px=s1['within3'],
                    M2_filled_px=info.get('filled_area_px', 0),
                    M2_qN=s2['N'], M2_ring_MAE_px=s2['MAE'], M2_ring_p95_px=s2['p95'], M2_within3px=s2['within3'],
                    M3_inlier_ratio=m3['inlier_ratio'] if m3 else np.nan,
                    M3_arc_coverage=m3['arc_coverage'] if m3 else np.nan,
                    M3_sector_stability=m3['sector_stability'] if m3 else np.nan,
                    M3_CAD_ring_MAE_px=np.nan,   # by design: ellipse is not a CAD projection
                    M3_note='ELLIPSE_IS_2D_DIAGNOSTIC_ONLY',
                    fullbound_main_N=int(fmain.sum()), fullbound_main_MAE_px=r_all_main.get('MAE', np.nan),
                    fullbound_discarded_N=int((~fmain).sum()), fullbound_discarded_MAE_px=r_all_disc.get('MAE', np.nan),
                    same_set_main_N=len(q0a), same_set_main_MAE_px=sa.get('MAE', np.nan),
                    same_set_discarded_N=len(q0b), same_set_discarded_MAE_px=sb.get('MAE', np.nan),
                    camera_ring_MAE_px=cam.get('ring_boundary_MAE_px'),
                    camera_source=cam.get('candidate_source'),
                ))
    df = pd.DataFrame(rows)
    df.to_csv(A.AUD / 'RING_COMPONENT_COMPARISON.csv', index=False)
    print('rows', len(df))
    print(df[['group', 'video', 'view', 'n_components', 'r_discarded', 'M0_ring_MAE_px', 'M1_ring_MAE_px', 'M2_ring_MAE_px']]
          .sort_values('r_discarded', ascending=False).head(12).round(4).to_string())


if __name__ == '__main__':
    main()
