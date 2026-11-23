#!/usr/bin/env python3
"""M2A visual audit: Ring CAD overlays, 3D camera/Ring, pose graphs, contact sheet."""
import ast
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch
import cv2

WS = Path('/home/liu/ring_first_3d_workspace')
OUT = WS / 'runs/m2a_w0_recovery'
VIS = OUT / 'visualization'
M1 = WS / 'runs/m1_final_39'
FROZEN = WS / 'experiments/TASK-E4-UNIFIED-PIPELINE-COMPLETION-002/code/frozen_calibration'
sys_path = [WS / 'src', WS / 'camera_mainline/code', WS / 'tools']
import sys
for p in sys_path: sys.path.insert(0, str(p))
from ring_first_3d.mainline.native.camera import observe, torus_contours
from ring_first_3d.mainline.native.geometry import project

DF = pd.read_csv(OUT / 'W0_79_VIDEO_RESULTS.csv')
DF['video_id'] = DF['video_id'].astype(int)
DIAG = pd.read_csv(OUT / 'RING_FRAME_DIAGNOSTICS.csv')
EDGES = pd.read_csv(OUT / 'POSE_GRAPH_EDGES.csv')
GRAPH = pd.read_csv(OUT / 'POSE_GRAPH_DIAGNOSTICS.csv')
ACT = pd.read_csv(OUT / 'ACTUAL_GRAPH_COMPONENTS.csv') if (OUT / 'ACTUAL_GRAPH_COMPONENTS.csv').exists() else pd.DataFrame()

COL = {'ACCEPT': '#2ca02c', 'QUARANTINE': '#ff7f0e', 'INSUFFICIENT_EVIDENCE': '#1f77b4', 'REJECT': '#d62728'}


def row_of(g, v):
    return DF[(DF.group_id == g) & (DF.video_id == int(v))].iloc[0]


def packet(g, v):
    r = row_of(g, v)
    if not isinstance(r.get('w0_file'), str) or not Path(r.w0_file).exists():
        return r, None, None, None
    w = np.load(r.w0_file)
    cr = np.load(Path(r.w0_file).parent / 'camera_result.npz')
    adm = pd.read_csv(Path(r.w0_file).parent / 'admission.csv')
    return r, w, cr, adm


def choose(cr, adm, prep):
    ids = [str(x) for x in cr['ids']]
    acc = adm[adm.admission_status == 'ACCEPT'].view.tolist()
    if acc:
        return acc[0]
    for q in prep['views']:
        if q['view'] in ids:
            return q['view']
    return ids[0]


def ring_overlay(g, v, cat):
    r, w, cr, adm = packet(g, v)
    prep = json.loads((M1 / 'prepared' / f'{g}_{v}' / 'PREPARED.json').read_text())
    rid = choose(cr, adm, prep) if cr is not None else prep['views'][0]['view']
    q = next(q for q in prep['views'] if q['view'] == rid)
    a = np.load(q['cache']); rgb = a['RGB']; labels = a['labels']; K = np.asarray(a['K'], float)
    ob = observe(labels)
    ring_mm = float(prep.get('ring_mm', 10.0)); R = ring_mm / 2 + 0.6; wire = 0.6
    fig, ax = plt.subplots(figsize=(11, 6.2)); ax.imshow(rgb)
    m = labels == 2
    ov = np.zeros_like(rgb); ov[m] = [120, 120, 120]
    ax.imshow(ov, alpha=0.28)
    if len(ob['q_train']): ax.scatter(ob['q_train'][:, 0], ob['q_train'][:, 1], s=10, c='#00e676', label=f'q_train {len(ob["q_train"])}')
    if len(ob['unknown_boundary']): ax.scatter(ob['unknown_boundary'][:, 0], ob['unknown_boundary'][:, 1], s=6, c='#d500f9', alpha=.7, label='occluded/unknown')
    if cr is not None:
        ids = [str(x) for x in cr['ids']]; i = ids.index(rid); C = np.asarray(cr['c2w'][i], float)
        cs = torus_contours(C, K, ring_radius=R, ring_wire=wire)
        for k, c in enumerate(cs):
            c = np.asarray(c, float); ax.plot(c[:, 0], c[:, 1], color='#00e5ff' if k == 0 else '#ff9800', lw=1.8,
                                            label='CAD inner' if k == 0 else 'CAD outer')
        th = np.linspace(0, 2*np.pi, 720); P = np.c_[R*np.cos(th), R*np.sin(th), np.zeros(720)]
        uv, z = project(P, C, K); ok = z > 0
        ax.plot(uv[ok, 0], uv[ok, 1], color='#ffd600', lw=1.5, label='CAD centerline')
        admrow = adm[adm.view == rid].iloc[0]
        st = admrow.admission_status
    else:
        st = 'NO_W0'
    txt = (f'{g}\n{v}  frame {q["raw_frame"]}  {r.ring_type}  {r.recovery_method}\n'
           f'ring MAE {r.new_ring_mae if pd.notna(r.new_ring_mae) else "NOT_EVALUABLE"}\n'
           f'held med/p95 {r.new_held_median if pd.notna(r.new_held_median) else "NA"} / {r.new_held_p95 if pd.notna(r.new_held_p95) else "NA"}\n'
           f'accept {r.new_accept if pd.notna(r.new_accept) else "NA"}  status {r.new_status}\n'
           f'admission {st}  {r.geometry_diagnostic_status}')
    ax.text(6, 16, txt, fontsize=7.4, va='top', bbox=dict(fc='white', alpha=.82, ec='none'))
    ax.set_xlim(0, 640); ax.set_ylim(360, 0); ax.axis('off'); ax.legend(loc='lower right', fontsize=6, framealpha=.8)
    d = VIS / 'D_ring_projection' / cat; d.mkdir(parents=True, exist_ok=True)
    p = d / f'{g}__{v}__{rid}.png'; fig.tight_layout(); fig.savefig(p, dpi=150); plt.close(fig)
    return p


def torus_surface(R=5.6, r=.6):
    u = np.linspace(0, 2*np.pi, 90); v = np.linspace(0, 2*np.pi, 40)
    U, V = np.meshgrid(u, v)
    X = (R + r*np.cos(V))*np.cos(U); Y = (R + r*np.cos(V))*np.sin(U); Z = r*np.sin(V)
    return X, Y, Z


def camera3d(g, v, cat):
    r, w, cr, adm = packet(g, v)
    if cr is None:
        return None
    C = np.asarray(cr['c2w'], float); ids = [str(x) for x in cr['ids']]
    prep = json.loads((M1 / 'prepared' / f'{g}_{v}' / 'PREPARED.json').read_text())
    ad = dict(zip(adm.view.astype(str), adm.admission_status.astype(str)))
    views = np.linspace(0, 2*np.pi, 4, endpoint=False)
    fig, axes = plt.subplots(2, 2, figsize=(12, 10), subplot_kw={'projection': '3d'})
    X, Y, Z = torus_surface(float(prep.get('ring_mm', 10.0))/2 + .6, .6)
    lim = max(15, float(np.abs(C[:, :3, 3]).max())*1.15)
    for ax, (elev, azim, name) in zip(axes.ravel(), [(22, -62, 'Perspective'), (90, -90, 'Top'), (0, -90, 'Side'), (0, 0, 'Front')]):
        ax.plot_surface(X, Y, Z, color='#9e9e9e', alpha=.35, linewidth=0)
        ax.plot([0, 8], [0, 0], [0, 0], c='r', lw=1); ax.plot([0, 0], [0, 8], [0, 0], c='g', lw=1); ax.plot([0, 0], [0, 0], [0, 8], c='b', lw=1)
        for i, T in enumerate(C):
            c = T[:3, 3]; col = COL.get(ad.get(ids[i], ''), '#777')
            ax.scatter(*c, c=col, s=28, depthshade=False)
            f = T[:3, 2] * 3.0
            ax.quiver(*c, *f, color=col, arrow_length_ratio=.3, lw=1)
        ax.plot(C[:, 0, 3], C[:, 1, 3], C[:, 2, 3], c='#444', lw=1, alpha=.7)
        for i in range(len(C)-1):
            dR = np.degrees(np.arccos(np.clip((np.trace(C[i, :3, :3].T @ C[i+1, :3, :3])-1)/2, -1, 1)))
            dt = np.linalg.norm(C[i+1, :3, 3]-C[i, :3, 3])
            if dR > 10 or dt > 5:
                ax.plot(C[i:i+2, 0, 3], C[i:i+2, 1, 3], C[i:i+2, 2, 3], c='red', lw=2.5)
                ax.text(*(C[i, :3, 3]), f'{dR:.0f}deg/{dt:.1f}mm', fontsize=5.5, color='red')
        ax.set_xlim(-lim, lim); ax.set_ylim(-lim, lim); ax.set_zlim(-lim, lim)
        ax.set_box_aspect((1, 1, 1)); ax.view_init(elev=elev, azim=azim); ax.set_title(name, fontsize=8)
        ax.tick_params(labelsize=5); ax.set_xlabel('x mm', fontsize=6); ax.set_ylabel('y mm', fontsize=6); ax.set_zlabel('z mm', fontsize=6)
    fig.suptitle(f'{g} / {v}  {r.ring_type}  {r.recovery_method}  status {r.new_status}  accept {r.new_accept}  maxJump {r.trajectory_jump_count}', fontsize=8)
    d = VIS / 'E_camera_3d' / cat; d.mkdir(parents=True, exist_ok=True)
    p = d / f'{g}__{v}.png'; fig.tight_layout(); fig.savefig(p, dpi=150); plt.close(fig)
    return p


def actual_graph(work):
    tr = dict(np.load(Path(work)/'observations/tracks005.npz'))
    pack = dict(np.load(Path(work)/'observations/pairs005.npz'))
    cfg = json.loads((Path(work)/'config.json').read_text())
    src = (FROZEN/'local_ring_sfm.py').read_text()
    node = next(n for n in ast.parse(src).body if isinstance(n, ast.FunctionDef) and n.name == 'pair_data')
    ns = dict(np=np, cv2=cv2, cfg=lambda: cfg)
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(FROZEN/'local_ring_sfm.py'), 'exec'), ns)
    edges = ns['pair_data'](tr, pack)
    n = len(tr['frame_raw']); parent = list(range(n))
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x
    for e in edges:
        a, b = find(int(e['i'])), find(int(e['j']))
        if a != b: parent[b] = a
    comp = {}
    for i in range(n): comp.setdefault(find(i), []).append(i)
    members = sorted(comp.values(), key=len, reverse=True)
    membership = {i: k for k, mem in enumerate(members) for i in mem}
    return tr, edges, members, membership


def pose_graph_actual(g, v, stage, work):
    if not (Path(work)/'observations/tracks005.npz').exists():
        return None
    tr, edges, members, membership = actual_graph(work)
    n = len(tr['frame_raw']); ang = np.linspace(0, 2*np.pi, n, endpoint=False); xy = np.c_[np.cos(ang), np.sin(ang)]
    fig, ax = plt.subplots(figsize=(6.0, 5.0))
    for e in edges:
        a, b = int(e['i']), int(e['j'])
        ax.plot([xy[a, 0], xy[b, 0]], [xy[a, 1], xy[b, 1]], c='#555', lw=1 + min(4, len(e['rows'])/20), alpha=.7)
    palette = ['#1f77b4', '#d62728', '#9467bd', '#2ca02c', '#8c564b']
    for i in range(n):
        ax.scatter(*xy[i], s=230, c=palette[membership[i] % len(palette)], edgecolors='k', zorder=3)
        ax.text(xy[i, 0]*1.20, xy[i, 1]*1.20, str(int(tr['frame_raw'][i])), ha='center', va='center', fontsize=7)
    ax.set_aspect('equal'); ax.axis('off')
    ax.set_title(f'{g}/{v}  {stage}  components {len(members)}  sizes {[len(x) for x in members]}',
                 fontsize=7.2, pad=4)
    d = VIS/'C_pose_graph'/stage; d.mkdir(parents=True, exist_ok=True)
    p = d/f'{g}__{v}.png'; fig.tight_layout(); fig.savefig(p, dpi=150); plt.close(fig)
    return p


def observation_plot():
    d = DIAG.groupby(['group_id', 'video_id']).agg(ok=('observation_status', lambda x: int((x == 'OK').sum())), total=('observation_status', 'size')).reset_index()
    fig, ax = plt.subplots(figsize=(9, 3.8)); x = np.arange(len(d))
    ax.bar(x, d.ok, color='#2ca02c', label='q_train >= 20'); ax.bar(x, d.total-d.ok, bottom=d.ok, color='#d62728', label='insufficient')
    ax.set_xticks(x); ax.set_xticklabels([f'{r.group_id.split("_")[1]}/{r.video_id}' for _, r in d.iterrows()], rotation=45, ha='right', fontsize=6)
    ax.set_ylabel('frames'); ax.legend(fontsize=7); ax.set_title('Ring observation by frame (4 failed videos)', fontsize=8)
    p = VIS/'A_ring_observation'/'observation_counts.png'; p.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout(); fig.savefig(p, dpi=150); plt.close(fig); return p


def contact_sheet(cases):
    rows = []
    for g, v, cat, label in cases:
        ov = ring_overlay(g, v, cat); c3 = camera3d(g, v, cat)
        rows.append((ov, c3, label))
    fig, axes = plt.subplots(len(rows), 2, figsize=(16, 4.0*len(rows)))
    for i, (ov, c3, label) in enumerate(rows):
        axes[i, 0].imshow(plt.imread(ov)); axes[i, 0].axis('off'); axes[i, 0].set_title(label + ' — Ring CAD overlay', fontsize=8)
        if c3:
            axes[i, 1].imshow(plt.imread(c3)); axes[i, 1].axis('off'); axes[i, 1].set_title(label + ' — 3D camera/Ring', fontsize=8)
        else:
            axes[i, 1].text(.5, .5, 'NO W0 / NOT_COMPUTABLE', ha='center', va='center'); axes[i, 1].axis('off')
    p = VIS/'F_summary'/'representative_contact_sheet.png'; p.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout(); fig.savefig(p, dpi=130); plt.close(fig); return p


def main():
    for d in ['A_ring_observation', 'C_pose_graph', 'D_ring_projection', 'E_camera_3d', 'F_summary', 'B_inner_outer/ring_cad_overlay', 'B_inner_outer/j2_comparison']:
        (VIS/d).mkdir(parents=True, exist_ok=True)
    observation_plot()
    cases = [
        ('GP_Ip_20.0mm_closed_R10_single_refY', '005', 'accepted', 'SUCCESS R10 G03/005'),
        ('GP_Ip_10.3mm_closed_R5_single_refY', '005', 'accepted', 'SUCCESS R5'),
        ('GP_IIa_14.0mm_closed_R5_single_refY', '005', 'quarantine', 'PARTIAL Ring recovery'),
        ('GP_Ip_20.0mm_closed_R10_single_refY', '004', 'branch_risk', 'ACCEPT but branch jump'),
        ('GP_Is_10.5mm_closed_R5_single_refY', '005', 'quarantine', 'C2B bridge recovery'),
        ('GP_Is_18.0mm_closed_R5_single_refY', '005', 'failed', 'NO W0 / Ring insufficient'),
    ]
    for g, v, cat, label in cases:
        ring_overlay(g, v, cat); camera3d(g, v, cat)
    for _, r in GRAPH[GRAPH.stage == 'C0'].iterrows():
        g, v = r.group_id, f'{int(r.video_id):03d}'
        pose_graph_actual(g, v, 'C0', M1/'work'/g/v)
        pose_graph_actual(g, v, 'C1', OUT/'work'/'C1'/g/v)
    for g, v, stage, method in [('GP_Is_10.5mm_closed_R5_single_refY', '005', 'C2', 'C2'),
                                 ('GP_Is_10.5mm_closed_R5_single_refY', '005', 'C2B', 'C2B'),
                                 ('GP_Is_9.79mm_closed_R10_single_refY', '004', 'C2', 'C2')]:
        pose_graph_actual(g, v, stage, OUT/'work'/method/g/v)
    print(contact_sheet(cases))

if __name__ == '__main__':
    main()
