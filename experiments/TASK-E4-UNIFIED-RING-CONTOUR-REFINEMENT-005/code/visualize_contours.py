"""Groups A (3x3 extraction), C (local zooms), D (residual distribution)."""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
import cv2
sys.path.insert(0, str(Path(__file__).resolve().parent))
import dxy_adapter as D
import contour_refinement as CR

T = Path(__file__).resolve().parents[1]
V = T/'visualization'
from ring_first_3d.mainline.native.camera import torus_contours
K = np.array([[490.,0,319.5],[0,490.,179.5],[0,0,1]])

C_IN, C_OUT, C_MID = 'cyan', 'magenta', 'white'
C_CAD_I, C_CAD_O = 'yellow', 'orange'

def load_prep(g, v):
    d = T/'runs/prepared'/f'{g}_{v}'
    if not d.exists(): return None
    return json.loads((d/'PREPARED.json').read_text())

def cam(g, v, view):
    p = T/'runs'/f'{g}_{v}'/'camera'/view/'CAMERA_RESULT.json'
    if p.exists(): return np.asarray(json.loads(p.read_text())['c2w_mm'])
    q = Path('/home/liu/ring_first_3d_workspace/experiments/TASK-E4-PREBODY-UNIFIED-CAMERA-READINESS-004/runs/N16')/g/v/'camera'/view/'CAMERA_RESULT.json'
    return np.asarray(json.loads(q.read_text())['c2w_mm']) if q.exists() else None

def panel_A(g, v, view, out):
    prep = load_prep(g, v); rec = D.load(view)
    if not prep or not rec: return None
    c = np.load(T/'runs/prepared'/f'{g}_{v}'/(view+'.npz'))
    rgb, lab = c['RGB'], c['labels']
    C = cam(g, v, view)
    fig, ax = plt.subplots(3, 3, figsize=(15, 13))
    ax[0,0].imshow(rgb); ax[0,0].set_title('A1 real RGB', fontsize=9)
    vis = np.zeros((*lab.shape,3), np.uint8)
    vis[lab==2] = [0,80,255]; vis[lab==1] = [0,200,0]
    ax[0,1].imshow(vis); ax[0,1].set_title('A2 mask (blue=ring, green=polyp)', fontsize=9)
    ax[0,2].imshow(rgb)
    edge = cv2.Canny((lab==2).astype(np.uint8)*255, 50, 150)
    ys, xs = np.nonzero(edge); ax[0,2].scatter(xs, ys, s=0.4, c='red')
    ax[0,2].set_title('A3 raw ring boundary (red)', fontsize=9)
    ax[1,0].imshow(rgb)
    for k, col in (('inner',C_IN),('outer',C_OUT),('centerline',C_MID)):
        if rec.get(k): p = D.sample(rec[k]); ax[1,0].plot(p[:,0],p[:,1],'-',lw=1.2,c=col,ls='--' if k=='centerline' else '-')
    ax[1,0].set_title('A4 DXY inner/outer/mid ellipses', fontsize=9)
    ax[1,1].imshow(rgb)
    for k, col in (('inner',C_IN),('outer',C_OUT)):
        if not rec.get(k): continue
        p = D.sample(rec[k]); m = D.visible_mask(rec[k], lab)
        ax[1,1].plot(p[m,0],p[m,1],'-',lw=1.6,c=col); ax[1,1].plot(p[~m,0],p[~m,1],'--',lw=.9,c=col,alpha=.45)
    ax[1,1].set_title('A5 visible (solid) vs inferred (dashed)', fontsize=9)
    ax[1,2].imshow(rgb)
    if C is not None:
        for cu in torus_contours(C, K): ax[1,2].plot(np.asarray(cu)[:,0], np.asarray(cu)[:,1], ':', lw=1.2, c='yellow')
    ax[1,2].set_title('A6 CAD projection vs real edge', fontsize=9)
    ax[2,0].imshow(rgb)
    deltas = {}
    for k, col in (('inner',C_IN),('outer',C_OUT)):
        if not rec.get(k): continue
        cur, d, vis = CR.refine(rgb, rec[k], lab)
        deltas[k] = (cur, d, vis)
        ax[2,0].plot(cur[:,0],cur[:,1],'-',lw=1.4,c=col)
        p0 = D.sample(rec[k]); ax[2,0].plot(p0[:,0],p0[:,1],':',lw=.9,c=col,alpha=.6)
    ax[2,0].set_title('A7 B2 curves (solid) vs DXY (dotted)', fontsize=9)
    for k, col in deltas.items():
        ax[2,1].plot(np.linspace(0,1,len(col[1])), col[1], lw=1.2, c=C_IN if k=='inner' else C_OUT, label=k)
    ax[2,1].set_xlabel('normalised arc length'); ax[2,1].set_ylabel('normal offset $\\delta$(s) [px]')
    ax[2,1].legend(fontsize=8); ax[2,1].grid(alpha=.3); ax[2,1].set_title('A8 displacement field', fontsize=9)
    ax[2,2].imshow(rgb)
    for k, val in deltas.items():
        cur = val[0]
        ax[2,2].plot(cur[:,0], cur[:,1], '-', lw=1.6, c=C_IN if k=='inner' else C_OUT)
    ax[2,2].set_title('A9 final continuous contours', fontsize=9)
    for a in ax.ravel(): a.axis('off')
    fig.suptitle(f'{g}/{v}/{view} — 2D ring contour extraction', fontsize=12)
    fig.tight_layout(); fig.savefig(out, dpi=150); plt.close(fig)
    return deltas

def panel_C(g, v, view, deltas, rec, c, out):
    rgb, lab = c['RGB'], c['labels']
    boxes = [('top outer',(0.30,0.05,0.40,0.30)),('bottom outer',(0.30,0.62,0.40,0.33)),
             ('inner',(0.36,0.36,0.28,0.28)),('polyp contact',(0.60,0.35,0.35,0.35))]
    fig, ax = plt.subplots(1, 4, figsize=(18,4.6))
    for a,(name,(x0,y0,w,h)) in zip(ax, boxes):
        x1,y1 = int(x0*640), int(y0*360); x2,y2 = int((x0+w)*640), int((y0+h)*360)
        a.imshow(rgb[y1:y2, x1:x2])
        for k,col in (('inner',C_IN),('outer',C_OUT)):
            if not rec.get(k): continue
            p = D.sample(rec[k]); m = (p[:,0]>=x1)&(p[:,0]<x2)&(p[:,1]>=y1)&(p[:,1]<y2)
            a.plot(p[m,0]-x1,p[m,1]-y1,':',lw=1.0,c=col)
            if k in deltas:
                q = deltas[k][0]; m2=(q[:,0]>=x1)&(q[:,0]<x2)&(q[:,1]>=y1)&(q[:,1]<y2)
                a.plot(q[m2,0]-x1,q[m2,1]-y1,'-',lw=1.4,c=col)
        e = cv2.Canny((lab==2).astype(np.uint8)*255,50,150)[y1:y2,x1:x2]
        ys,xs = np.nonzero(e); a.scatter(xs,ys,s=0.5,c='red')
        a.set_title(name, fontsize=9); a.axis('off')
    fig.suptitle(f'{g}/{v}/{view} — local zoom: mask edge (red) vs DXY (dotted) vs B2 (solid)', fontsize=11)
    fig.tight_layout(); fig.savefig(out, dpi=170); plt.close(fig)

def main():
    targets = [('G06','005'),('G05','005'),('G03','005'),('G03','004')]
    rows = []
    for g, v in targets:
        prep = load_prep(g, v)
        if not prep: continue
        for q in prep['views'][:2]:
            view = q['view']; rec = D.load(view)
            if not rec or not rec.get('valid'): continue
            c = np.load(T/'runs/prepared'/f'{g}_{v}'/(view+'.npz'))
            rgb, lab = c['RGB'], c['labels']
            deltas = {}
            for k in ('inner','outer'):
                if rec.get(k):
                    cur,d,vis = CR.refine(rgb, rec[k], lab)
                    deltas[k]=(cur,d,vis)
                    base = D.sample(rec[k])
                    ed = cv2.Canny((lab==2).astype(np.uint8)*255,50,150)
                    ys,xs=np.nonzero(ed)
                    from scipy.spatial import cKDTree
                    tr=cKDTree(np.c_[xs,ys].astype(float))
                    db,_=tr.query(base,k=1); dc,_=tr.query(cur,k=1)
                    rows.append(dict(group=g,video=v,view=view,contour=k,
                                     n=len(base),visible=int(vis.sum()),
                                     mae_DXY_to_maskedge=float(db.mean()),
                                     mae_B2_to_maskedge=float(dc.mean()),
                                     mean_abs_delta=float(np.abs(d).mean())))
            panel_A(g,v,view, V/'A_2d_contour_extraction'/f'{g}_{v}_{view}_A.png')
            panel_C(g,v,view,deltas,rec,c, V/'C_local_zoom'/f'{g}_{v}_{view}_C.png')
    pd.DataFrame(rows).to_csv(T/'metrics/CONTOUR_QUALITY.csv', index=False)
    if rows:
        df = pd.DataFrame(rows)
        fig, ax = plt.subplots(1,2,figsize=(12,4))
        ax[0].hist(df.mae_DXY_to_maskedge, bins=20, alpha=.6, label='DXY ellipse')
        ax[0].hist(df.mae_B2_to_maskedge, bins=20, alpha=.6, label='B2 refined')
        ax[0].set_xlabel('mean distance to real mask edge (px)'); ax[0].legend(); ax[0].set_title('contour-to-edge error', fontsize=9)
        ax[1].scatter(df.mae_DXY_to_maskedge, df.mean_abs_delta, s=18)
        ax[1].set_xlabel('DXY error (px)'); ax[1].set_ylabel('mean |delta| (px)')
        fig.suptitle('Figure D  contour residual distribution: DXY vs B2', fontsize=11)
        fig.tight_layout(); fig.savefig(V/'D_residual_distribution'/'figD_distribution.png', dpi=130); plt.close(fig)
    print('done', len(rows))
if __name__ == '__main__':
    main()
