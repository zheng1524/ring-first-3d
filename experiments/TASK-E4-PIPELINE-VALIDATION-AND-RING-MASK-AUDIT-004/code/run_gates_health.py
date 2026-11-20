"""Tasks D/E/F: gate sensitivity, view coverage, camera-body gauge, HERO health, Body health."""
import json
import numpy as np
import pandas as pd
import audit_common as A

MATURE = [(g, v) for g in A.GROUPS for v in A.VIDEOS if A.ba_cameras(g, v) is not None]


# ------------------------------------------------------------------ D: gates + coverage
def gates():
    rows, cov = [], []
    cam = pd.read_csv(A.T002 / 'metrics/CAMERA_METRICS.csv')
    fail = pd.read_csv(A.T002 / 'metrics/CAMERA_FAILURE_DIAGNOSTICS.csv')
    fail = fail.drop_duplicates(subset=['group', 'video', 'id'], keep='first')
    for g in A.GROUPS:
        for v in A.VIDEOS:
            fit = A.instance_views(g, v)
            expected = len(fit)
            got = 0
            for x in fit:
                cid = x['meta']['id']
                c = A.final_camera(g, v, cid)
                st = 'MISSING'
                mae = np.nan
                if c:
                    st = 'ACCEPTED'
                    mae = c.get('ring_boundary_MAE_px', np.nan)
                    got += 1
                f = fail[(fail.group == g) & (fail.video == v) & (fail.id == cid)]
                if len(f):
                    f = f.iloc[0]
                    inl = f.get('RGB_PnP_input_inliers', np.nan)
                    feat = f.get('RGB_features', np.nan)
                    reasons = str(f.get('reasons'))
                else:
                    inl = feat = np.nan; reasons = ''
                rows.append(dict(group=g, video=v, view=cid, status=st, ring_MAE_px=mae,
                                 ring_pass_3px=(mae <= 3.0) if np.isfinite(mae) else False,
                                 ring_pass_5px=(mae <= 5.0) if np.isfinite(mae) else False,
                                 ring_pass_10px=(mae <= 10.0) if np.isfinite(mae) else False,
                                 rgb_inliers=inl, rgb_features=feat, rejection_reasons=reasons,
                                 camera_available=bool(c is not None)))
            hero = sum(1 for x in fit if (A.RUNS / g / v / 'hero' / x['meta']['id'] / 'ADMISSION.json').exists())
            body = sum(1 for x in fit if (A.RUNS / g / v / 'body/B1/TASK_PREDICTION_FROZEN.json').exists())
            hold = A.instance_views(g, v, 'UPDATE_HOLDOUT')
            hold_ok = sum(1 for x in hold if A.final_camera(g, v, x['meta']['id']))
            cov.append(dict(group=g, video=v, fit_expected=expected, camera_accepted=got,
                            camera_coverage=got / expected, hero_instances=hero,
                            body_instances=body, holdout_expected=len(hold),
                            holdout_camera_ok=hold_ok,
                            holdout_complete=(hold_ok == len(hold) and len(hold) > 0)))
    pd.DataFrame(rows).to_csv(A.AUD / 'GATE_SENSITIVITY.csv', index=False)
    pd.DataFrame(cov).to_csv(A.AUD / 'VIEW_COVERAGE_MATRIX.csv', index=False)
    return pd.DataFrame(rows), pd.DataFrame(cov)


# ------------------------------------------------------------------ E: camera-body gauge
def gauge():
    out = []
    for g, v in MATURE:
        ba = A.ba_cameras(g, v); ids = ba['ids']
        body = A.load_body(g, v, 'B1', 'INITIAL')
        if body is None:
            continue
        fit = {x['meta']['id']: x for x in A.instance_views(g, v)}
        for cid in ids:
            if cid not in fit:
                continue
            cache = A.load_cache(fit[cid]); K = cache['K']; labels = cache['labels']
            rec = dict(group=g, video=v, view=cid)
            for tag, C in [('init_v0', ba.get(0, [None] * len(ids))[ids.index(cid)] if 0 in ba else None),
                           ('init_v1', ba.get(1, [None] * len(ids))[ids.index(cid)] if 1 in ba else None)]:
                if C is None:
                    rec[f'{tag}_IoU'] = np.nan
                    continue
                rec[f'{tag}_IoU'] = A.silhouette_iou(C, K, body['V'], body['F'], labels)['IoU']
            c = A.final_camera(g, v, cid)
            if c and c.get('c2w_mm'):
                rec['final_IoU'] = A.silhouette_iou(np.asarray(c['c2w_mm'], float), K,
                                                    body['V'], body['F'], labels)['IoU']
                bf = A.load_body(g, v, 'B1', 'FINAL')
                if bf is not None:
                    rec['final_body_final_camera_IoU'] = A.silhouette_iou(
                        np.asarray(c['c2w_mm'], float), K, bf['V'], bf['F'], labels)['IoU']
            out.append(rec)
    pd.DataFrame(out).to_csv(A.AUD / 'CAMERA_BODY_GAUGE_DIAGNOSTICS.csv', index=False)
    return pd.DataFrame(out)


# ------------------------------------------------------------------ F1: HERO health
def hero():
    rows = []
    for g in A.GROUPS:
        for v in A.VIDEOS:
            for hp in sorted((A.RUNS / g / v / 'hero').glob('*/HERO_native.npz')) if (A.RUNS / g / v / 'hero').exists() else []:
                cid = hp.parent.name
                d = np.load(hp)['depth_mm']
                valid = np.isfinite(d) & (d > 0)
                if not valid.any():
                    continue
                c = A.final_camera(g, v, cid)
                dist = float(np.linalg.norm(np.asarray(c['c2w_mm'])[:3, 3])) if c else np.nan
                med = float(np.median(d[valid]))
                ratio = med / dist if np.isfinite(dist) and dist > 0 else np.nan
                rows.append(dict(group=g, video=v, view=cid,
                                 valid_fraction=float(valid.mean()),
                                 depth_p10_mm=float(np.percentile(d[valid], 10)),
                                 depth_median_mm=med,
                                 depth_p90_mm=float(np.percentile(d[valid], 90)),
                                 camera_distance_mm=dist, depth_over_distance=ratio,
                                 health=('SUSPECT' if np.isfinite(ratio) and ratio > 3 else 'WITHIN_3X')))
    pd.DataFrame(rows).to_csv(A.AUD / 'HERO_HEALTH.csv', index=False)
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ F2: Body update health
def body_health():
    rows = []
    bm = pd.read_csv(A.T002 / 'metrics/BODY_METRICS.csv')
    bm['video'] = bm['video'].astype(str).str.zfill(3)
    for g in A.GROUPS:
        for v in A.VIDEOS:
            for arm in ('B1', 'B2'):
                d = A.RUNS / g / v / 'body' / arm
                fi, ff = d / 'INITIAL.npz', d / 'FINAL.npz'
                if not (fi.exists() and ff.exists()):
                    continue
                Vi = np.load(fi)['V']; Vf = np.load(ff)['V']
                disp = np.linalg.norm(Vi - Vf, axis=1)
                acc = rej = 0; node_t = np.nan
                up = d / 'UPDATES.json'
                if up.exists():
                    it = json.loads(up.read_text()).get('iterations', [])
                    acc = sum(1 for x in it if x.get('accepted'))
                    rej = len(it) - acc
                    tr = [np.abs(np.asarray(x.get('graph_translation_mm') or [0], float)).max() for x in it]
                    node_t = float(np.nanmax(tr)) if tr else np.nan
                sub = bm[(bm.group == g) & (bm.video == v) & (bm.arm == arm)]
                r = sub.iloc[0] if len(sub) else None
                rows.append(dict(group=g, video=v, arm=arm,
                                 max_vertex_disp_mm=float(disp.max()), mean_vertex_disp_mm=float(disp.mean()),
                                 p95_vertex_disp_mm=float(np.percentile(disp, 95)),
                                 max_graph_node_translation_mm=node_t,
                                 accepted_steps=acc, rejected_steps=rej,
                                 FIT_IoU=float(r['FIT_IoU_admitted_subset']) if r is not None and pd.notna(r.get('FIT_IoU_admitted_subset')) else np.nan,
                                 HOLDOUT_IoU=float(r['HOLDOUT_IoU_admitted_subset']) if r is not None and pd.notna(r.get('HOLDOUT_IoU_admitted_subset')) else np.nan,
                                 GT_MAE_mm=float(r['GT_MAE_mm']) if r is not None and pd.notna(r.get('GT_MAE_mm')) else np.nan,
                                 stagnation=('STAGNATION' if disp.max() < 1e-3 else 'EFFECTIVE_UPDATE')))
    pd.DataFrame(rows).to_csv(A.AUD / 'BODY_UPDATE_HEALTH.csv', index=False)
    return pd.DataFrame(rows)


if __name__ == '__main__':
    g, c = gates()
    ga = gauge(); h = hero(); b = body_health()
    print('gates', len(g), '| coverage', len(c), '| gauge', len(ga), '| hero', len(h), '| body', len(b))
    print(c.to_string(index=False))
    print(h.sort_values('depth_over_distance', ascending=False).head(4).round(2).to_string(index=False))
    print(b.round(5).to_string(index=False))
