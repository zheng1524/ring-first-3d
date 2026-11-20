import json, numpy as np, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
from pathlib import Path
import cv2
WS=Path('/home/liu/ring_first_3d_workspace'); T=WS/'experiments/TASK-E4-PREBODY-UNIFIED-CAMERA-READINESS-004'
T005=WS/'experiments/TASK-E4-UNIFIED-RING-RGB-CAMERA-MAINLINE-005'; T003=WS/'experiments/TASK-E4-VIEW-DENSITY-SWEEP-003'
DXY=WS/'experiments/TASK-E4-DXY-CONIC-RING-OBSERVATION-REUSE-001/metrics/DXY_OBSERVATIONS'
V={x['meta']['id']:x for x in json.loads((WS/'experiments/TASK-E4-UNIFIED-PIPELINE-COMPLETION-002/audit/SELECTED_VIEWS.json').read_text())}
K=np.array([[490.,0,319.5],[0,490.,179.5],[0,0,1]])
from ring_first_3d.mainline.native.camera import torus_contours
def cam(p): return np.asarray(json.loads(Path(p).read_text())['c2w_mm'],float)
def epts(e,n=220):
    t=np.linspace(0,2*np.pi,n); c,s=np.cos(np.deg2rad(e['angle_deg'])),np.sin(np.deg2rad(e['angle_deg']))
    x=e['major_radius']*np.cos(t); y=e['minor_radius']*np.sin(t)
    return np.c_[c*x-s*y+e['cx'], s*x+c*y+e['cy']]
sel=[('G06','005','G06_v005_raw00604','good'),('G01','004','G01_004_ref08','medium'),('G02','005','G02_v005_raw00104','bad')]
for g,v,cid,tag in sel:
    if cid not in V: continue
    cache=np.load(V[cid]['cache']['path']); rgb=cache['RGB']; lab=cache['labels']
    p=T005/'runs'/g/v/'camera'/cid/'CAMERA_RESULT.json'
    if not p.exists(): continue
    C=cam(p); rec=json.loads((DXY/(cid+'.json')).read_text()) if (DXY/(cid+'.json')).exists() else {}
    res=json.loads(p.read_text()); q=dict(np.load(T005/'runs'/g/v/'observations'/(cid+'_ring.npz')))
    fig,ax=plt.subplots(1,3,figsize=(16,4.2))
    ax[0].imshow(rgb); ax[0].set_title('real RGB',fontsize=8)
    ax[1].imshow(rgb)
    m=np.zeros_like(lab); m[lab==1]=1; m[lab==2]=1
    ax[1].imshow(np.dstack([m*0,m*255,m*60]).astype(np.uint8),alpha=.55)
    if rec.get('inner'): p1=epts(rec['inner']); ax[1].plot(p1[:,0],p1[:,1],'-',lw=1.1,c='cyan')
    if rec.get('outer'): p2=epts(rec['outer']); ax[1].plot(p2[:,0],p2[:,1],'-',lw=1.1,c='magenta')
    for cu in torus_contours(C,K): ax[1].plot(np.asarray(cu)[:,0],np.asarray(cu)[:,1],':',lw=1.1,c='yellow')
    ax[1].plot(q['q_train'][:,0],q['q_train'][:,1],'.',ms=1,c='red')
    ax[1].set_title('Ring mask + DXY ellipses + CAD projection',fontsize=8)
    ax[2].imshow(rgb); ax[2].plot(q['q_train'][:,0],q['q_train'][:,1],'.',ms=1,c='lime')
    ax[2].set_title(f"Ring MAE={res['ring_boundary_MAE_px']:.2f}px",fontsize=8)
    for a_ in ax: a_.axis('off')
    fig.suptitle(f'{g}/{v}/{cid}  [{tag}]  Ring={res["ring_boundary_MAE_px"]:.2f}px  held={res.get("held_MAE_px","?")}',fontsize=10)
    fig.tight_layout(); fig.savefig(T/'visualization/ring_projection'/f'{g}_{v}_{cid}.png',dpi=120); plt.close(fig)
for g,v in [('G03','005'),('G06','005')]:
    d=T005/'runs'/g/v/'camera'; fs=sorted(d.glob('*/CAMERA_RESULT.json'))
    if not fs: continue
    cs=np.array([cam(p) for p in fs])
    fig=plt.figure(figsize=(6.5,5.5)); ax=fig.add_subplot(111,projection='3d')
    ax.scatter(cs[:,0],cs[:,2],cs[:,1],c='#c33',s=28)
    th=np.linspace(0,2*np.pi,120)
    ax.plot(5.6*np.cos(th),5.6*np.sin(th),np.zeros_like(th),c='k',lw=1.5)
    for X in (cs[:,0],cs[:,2],cs[:,1]): pass
    ax.set_xlabel('X'); ax.set_ylabel('Z'); ax.set_zlabel('Y')
    ax.set_title(f'{g}/{v}: cameras + Ring CAD',fontsize=9)
    fig.tight_layout(); fig.savefig(T/'visualization/camera_network'/f'{g}_{v}_network.png',dpi=120); plt.close(fig)
fig,ax=plt.subplots(figsize=(6,5))
for tag,c in [('N8','k'),('N16','orange'),('N22','green')]:
    d=T003/'runs'/tag/'G02/005/camera'; fs=sorted(d.glob('*/CAMERA_RESULT.json'))
    if fs:
        cs=np.array([cam(p) for p in fs]); ax.scatter(cs[:,0],cs[:,2],s=24,c=c,label=f'{tag} n={len(cs)}')
ax.set_aspect('equal'); ax.grid(alpha=.3); ax.legend(fontsize=7); ax.set_xlabel('x (mm)'); ax.set_ylabel('z (mm)')
ax.set_title('G02/005 camera layout vs density',fontsize=9)
fig.tight_layout(); fig.savefig(T/'visualization/density_comparison'/'G02_005_density.png',dpi=120); plt.close(fig)
print('figs', len(list((T/'visualization').rglob('*.png'))))
