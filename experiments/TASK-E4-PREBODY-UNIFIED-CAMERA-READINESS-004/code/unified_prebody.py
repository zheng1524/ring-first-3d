"""TASK-E4-PREBODY-UNIFIED-CAMERA-READINESS-004 — single entry point.

    python unified_prebody.py --group G01 --video 004
    python unified_prebody.py --all

Stages
  1 prepare  : raw video -> frames -> INIT mask -> quality -> FIT/HOLDOUT
               BLOCKED in this environment: INIT weights are restricted and the raw
               videos are not present. The stage is implemented as an explicit gate
               that records the blocker instead of silently substituting caches.
  2 camera   : frozen 005 Ring+RGB solver output is consumed read-only (no re-solve).
  3 diagnose : per-view outlier classification A-E + camera network metrics.
  4 readiness: CORE / SUPPORT / QUARANTINE + BODY_READINESS card.

There is no per-video branching: every instance runs this same file with the same
config (configs/unified_config.json). Group/video only select input paths.
"""
import argparse, hashlib, json, sys
from pathlib import Path
import numpy as np
import pandas as pd

WS = Path('/home/liu/ring_first_3d_workspace')
T005 = WS / 'experiments/TASK-E4-UNIFIED-RING-RGB-CAMERA-MAINLINE-005'
T002 = WS / 'experiments/TASK-E4-UNIFIED-PIPELINE-COMPLETION-002'
T001 = WS / 'experiments/TASK-E4-DXY-CONIC-RING-OBSERVATION-REUSE-001'
T003 = WS / 'experiments/TASK-E4-VIEW-DENSITY-SWEEP-003'
TASK = WS / 'experiments/TASK-E4-PREBODY-UNIFIED-CAMERA-READINESS-004'
CFG = json.loads((TASK / 'configs/unified_config.json').read_text())

GROUPS = ['G01', 'G02', 'G03', 'G05', 'G06']
VIDEOS = ['004', '005']
DXY = T001 / 'metrics/DXY_OBSERVATIONS'


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


# ---------------------------------------------------------------- stage 1
def stage_prepare(g, v):
    """Honest gate: records why the raw-video front-end cannot run here."""
    vids = sorted(WS.glob('assets/**/*.mp4')) + sorted(WS.glob('assets/**/*.zip'))
    inits = sorted(Path('/home/liu/new-polyp-dxy').glob('**/INIT*.pth')) + \
            sorted(Path('/home/liu/new-polyp-dxy').glob('**/*.pt'))
    return dict(stage='prepare', group=g, video=v,
                status='BLOCKED_RESTRICTED_WEIGHTS',
                raw_video_candidates=len(vids), init_weight_candidates=len(inits),
                reason='MAINLINE_MANIFEST states model weights are restricted; raw videos absent',
                fallback='frozen masks from SELECTED_VIEWS (documented deviation, not a silent substitute)')


# ---------------------------------------------------------------- stage 2/3
def load_cameras(g, v):
    out = {}
    for p in sorted((T005 / 'runs' / g / v / 'camera').glob('*/CAMERA_RESULT.json')):
        out[p.parent.name] = np.asarray(json.loads(p.read_text())['c2w_mm'], float)
    return out


def held_table():
    q = pd.read_csv(T005 / 'CAMERA_QUALITY_MATRIX.csv')
    q['video'] = q['video'].astype(str).str.zfill(3)
    return q


def track_support(g, v):
    """Visible tracks per view and co-visibility, from the frozen tracks."""
    p = T005 / 'runs' / g / v / 'observations/tracks005.npz'
    if not p.exists():
        return {}, {}
    tr = dict(np.load(p)); xy = tr['xy']; ids = [str(s) for s in tr['ids']]
    vis = {ids[i]: int(np.isfinite(xy[:, i, 0]).sum()) for i in range(len(ids))}
    co = {}
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            n = int((np.isfinite(xy[:, i, 0]) & np.isfinite(xy[:, j, 0])).sum())
            if n >= CFG['network']['min_covisible_tracks']:
                co[(ids[i], ids[j])] = n
    return vis, co


def dxy_quality(cid):
    p = DXY / (cid + '.json')
    if not p.exists():
        return {}
    r = json.loads(p.read_text())
    d = r.get('diagnostics') or {}
    return dict(dxy_valid=bool(r.get('valid')), dxy_branch=r.get('branch'),
                dxy_coverage=d.get('inner_arc_coverage'),
                dxy_residual=d.get('inner_normalized_residual'),
                dxy_instability=d.get('inner_sector_instability'))


def classify(row, vis_n, covis_n, rot_out, center_out, cfg):
    """A-E classification; rules are global and use training-side evidence + independent held."""
    c = cfg['classify']
    if not row['camera_admission_pass']:
        return 'A_RING_OBSERVATION', 'ring gate failed (%.2f px)' % row['ring_MAE_px']
    if row['held_N'] < c['min_held_tracks'] or vis_n < c['min_visible_tracks']:
        return 'E_INSUFFICIENT_OBSERVATION', f'held_N={row["held_N"]} visible={vis_n}'
    if row['held_MAE_px'] > c['rgb_held_bad_px']:
        if covis_n >= c['min_covisible_views'] and vis_n >= c['min_visible_tracks']:
            if rot_out > c['axis_misalign_deg'] or center_out > c['radial_dev_mm']:
                return 'C_INIT_OR_GAUGE', f'held={row["held_MAE_px"]:.1f} axis_off={rot_out:.1f}'
            return 'D_BA_CONFLICT', f'held={row["held_MAE_px"]:.1f} with covis={covis_n}'
        return 'B_RGB_MATCHING', f'held={row["held_MAE_px"]:.1f} covis={covis_n}'
    if rot_out > c['axis_misalign_deg'] or center_out > c['radial_dev_mm']:
        return 'C_INIT_OR_GAUGE', f'axis_off={rot_out:.1f} radial_dev={center_out:.1f}'
    return 'OK', ''


def run_instance(g, v, cfg):
    cam = load_cameras(g, v)
    q = held_table()
    q = q[(q.group == g) & (q.video == v)]
    vis, co = track_support(g, v)
    rows = []
    center = np.array([0., 0., 0.])
    for _, r in q.iterrows():
        cid = r['view']
        if cid not in cam:
            continue
        C = cam[cid]
        R = C[:3, :3]; t = C[:3, 3]
        # physically meaningful outlier measures (a ring-camera rig looks inward from
        # all azimuths, so comparing rotations to a median is meaningless):
        #   axis_misalign_deg : angle between optical axis and the direction to the Ring centre
        #   radial_dev_mm     : deviation of the ring distance from the instance median
        axis = R @ np.array([0.0, 0.0, 1.0])
        to_c = -t / max(np.linalg.norm(t), 1e-9)
        rot_out = float(np.degrees(np.arccos(np.clip(abs(axis @ to_c), -1, 1))))
        dists = np.array([np.linalg.norm(np.asarray(C2[:3, 3])) for C2 in cam.values()])
        center_out = float(abs(np.linalg.norm(t) - np.median(dists)))
        covis_n = sum(1 for (a, b) in co if cid in (a, b))
        vis_n = vis.get(cid, 0)
        dxy = dxy_quality(cid)
        cls, why = classify(dict(r, held_N=r['held_N'], held_MAE_px=r['held_MAE_px']),
                            vis_n, covis_n, rot_out, center_out, cfg)
        core = bool(r['camera_admission_pass'] and r['held_MAE_px'] <= cfg['readiness']['core_held_px']
                    and r['held_p95_px'] <= cfg['readiness']['core_held_p95_px'] and r['held_N'] >= cfg['classify']['min_held_tracks'])
        support = bool(r['camera_admission_pass'] and r['held_MAE_px'] <= cfg['readiness']['support_held_px'] and not core)
        rows.append(dict(group=g, video=v, view=cid, ring_MAE_px=r['ring_MAE_px'], ring_p95_px=r['ring_p95_px'],
                         held_N=r['held_N'], held_MAE_px=r['held_MAE_px'], held_p95_px=r['held_p95_px'],
                         held_positive=r['held_positive'], admission=bool(r['camera_admission_pass']),
                         visible_tracks=vis_n, covisible_views=covis_n,
                         axis_misalign_deg=round(rot_out, 3), radial_dev_mm=round(center_out, 2),
                         dxy_coverage=dxy.get('dxy_coverage'), dxy_residual=dxy.get('dxy_residual'),
                         outlier_class=cls, reason=why,
                         usage='CORE' if core else ('SUPPORT' if support else 'QUARANTINE'),
                         per_view_status=r['per_view_status']))
    return rows


def instance_summary(g, v, rows, cfg):
    df = pd.DataFrame(rows)
    if df.empty:
        return dict(group=g, video=v, views=0, core=0, support=0, quarantine=0,
                    ring_median=np.nan, held_median=np.nan, held_p95=np.nan,
                    coverage_deg=0.0, network_components=0, body_ready='NO_CAMERAS')
    az = []
    for p in sorted((T005 / 'runs' / g / v / 'camera').glob('*/CAMERA_RESULT.json')):
        C = np.asarray(json.loads(p.read_text())['c2w_mm'], float)
        xyz = C[:3, 3]
        az.append(np.degrees(np.arctan2(xyz[1], xyz[0])))
    coverage = float(np.ptp(az)) if az else 0.0
    core = int((df.usage == 'CORE').sum()); sup = int((df.usage == 'SUPPORT').sum())
    quar = int((df.usage == 'QUARANTINE').sum())
    rw = cfg['readiness']
    if core >= rw['ready_min_core'] and coverage >= rw['ready_min_coverage_deg']:
        ready = 'READY_FOR_BODY_INIT'
    elif core + sup >= rw['caution_min_core_plus_support']:
        ready = 'READY_WITH_CAUTION'
    else:
        ready = 'CAMERA_REPAIR_REQUIRED'
    return dict(group=g, video=v, views=len(df), core=core, support=sup, quarantine=quar,
                ring_median=float(np.nanmedian(df.ring_MAE_px)),
                held_median=float(np.nanmedian(df.held_MAE_px)),
                held_p95=float(np.nanpercentile(df.held_MAE_px, 95)),
                coverage_deg=round(coverage, 1), body_ready=ready)


def card(g, v, rows, summ):
    df = pd.DataFrame(rows)
    lines = [f'# BODY_READINESS_CARD — {g}/{v}', '',
             '`BODY_NOT_USED_FOR_CAMERA_OPTIMIZATION`', '', '```text',
             f'实例：{g}/{v}', f'总候选视角：{summ["views"]}',
             f'成功恢复相机：{summ["views"]}',
             f'Ring 门禁通过：{int(df.admission.sum()) if len(df) else 0}',
             f'RGB 几何验证通过：{int(df.held_MAE_px.le(3).sum()) if len(df) else 0}', '',
             f'CORE：{summ["core"]}', f'SUPPORT：{summ["support"]}', f'QUARANTINE：{summ["quarantine"]}', '',
             f'可靠方向覆盖：{summ["coverage_deg"]} deg',
             f'Ring 中位：{summ["ring_median"]:.2f} px',
             f'RGB held 中位：{summ["held_median"]:.2f} px', f'RGB held p95：{summ["held_p95"]:.2f} px', '```', '']
    if len(df):
        worst = df.sort_values('held_MAE_px', ascending=False).head(3)
        lines += ['## 严重异常（按 held 排序）', '', '| view | held | Ring | class | reason |', '|---|---:|---:|---|---|']
        for _, r in worst.iterrows():
            lines.append(f'| {r["view"]} | {r["held_MAE_px"]:.1f} | {r["ring_MAE_px"]:.2f} | {r["outlier_class"]} | {r["reason"]} |')
        lines += ['', '## 建议用于 Body 初始化的相机', '']
        for u in ('CORE', 'SUPPORT'):
            s = df[df.usage == u].view.tolist()
            lines.append(f'- {u}: ' + (', '.join(s) if s else '(none)'))
        q_ = df[df.usage == 'QUARANTINE'].view.tolist()
        lines.append(f'- QUARANTINE: ' + (', '.join(q_) if q_ else '(none)'))
    lines += ['', f'## 准入结论：**{summ["body_ready"]}**', '',
              '对应可视化：`visualization/ring_projection/`, `visualization/camera_network/`',
              '', '> 说明：Ring 合格不等于相机可靠；QUARANTINE 视角保留原始观测与相机，仅暂停参与优化。']
    return '\n'.join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--group'); ap.add_argument('--video'); ap.add_argument('--all', action='store_true')
    a = ap.parse_args()
    targets = [(g, v) for g in GROUPS for v in VIDEOS] if a.all else [(a.group, a.video)]
    all_rows, summ = [], []
    prep = []
    for g, v in targets:
        prep.append(stage_prepare(g, v))
        rows = run_instance(g, v, CFG)
        all_rows += rows
        s = instance_summary(g, v, rows, CFG); summ.append(s)
        d = TASK / 'reports' / f'{g}_{v}'; d.mkdir(parents=True, exist_ok=True)
        (d / 'BODY_READINESS_CARD.md').write_text(card(g, v, rows, s))
        print(f'{g}/{v} core={s["core"]} support={s["support"]} quar={s["quarantine"]} '
              f'held={s["held_median"]:.2f} -> {s["body_ready"]}', flush=True)
    pd.DataFrame(all_rows).to_csv(TASK / 'metrics/CAMERA_QUALITY_MATRIX.csv', index=False)
    pd.DataFrame(summ).to_csv(TASK / 'metrics/BODY_READINESS_MATRIX.csv', index=False)
    pd.DataFrame(prep).to_csv(TASK / 'metrics/PREPARE_STAGE_STATUS.csv', index=False)
    print('done', len(all_rows), 'views')


if __name__ == '__main__':
    main()
