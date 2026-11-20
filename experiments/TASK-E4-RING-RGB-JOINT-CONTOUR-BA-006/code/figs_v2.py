import sys, json
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa
sys.path.insert(0, str(Path(__file__).resolve().parent))
import synth_v2 as S, joint_loss as JL
T = Path(__file__).resolve().parents[1]; K = S.K
V = T/'visualization'; [ (V/d).mkdir(parents=True, exist_ok=True) for d in ('A_method_comparison','B_ring_only_vs_joint','C_loss_tradeoff','F_local_zoom') ]

# 1) synthetic 3D layout
poses = [S.make_pose(45.,0.,-25.), S.make_pose(42.,12.,0.), S.make_pose(48.,8.,25.)]
X = S.scene_points(poses[0], 70, 7)
fig = plt.figure(figsize=(6.5,5.5)); ax = fig.add_subplot(111, projection='3d')
th = np.linspace(0,2*np.pi,120)
ax.plot(5.6*np.cos(th),5.6*np.sin(th),np.zeros_like(th),'k-',lw=1.6)
ax.scatter(X[:,0],X[:,1],X[:,2],s=4,c='#357')
for i,M in enumerate(poses):
    c = M[:3,3]; ax.scatter(*c,s=70,c=['#c33','#2a7','#e8a'][i],depthshade=False)
    d = M[:3,:3] @ np.array([0,0,-1.]); ax.quiver(*c,*(d*12),color=['#c33','#2a7','#e8a'][i],arrow_length_ratio=.2)
ax.set_xlabel('X'); ax.set_ylabel('Y'); ax.set_zlabel('Z')
ax.set_title('synthetic rig: cameras look at Ring origin (all depths > 0)', fontsize=9)
fig.tight_layout(); fig.savefig(V/'E_camera_network/fig_synthetic_layout.png', dpi=130); plt.close(fig)

# 2) reprojection before/after (Test A, noise 0.7, pert 15)
M = S.make_pose(45.,20.,15.); Xs = S.scene_points(M); S.check_pose(M, Xs)
uv,_ = S.project(Xs, M, K); rng = np.random.default_rng(1); uvn = uv + rng.normal(0,.7,uv.shape)
obs = S.ring_obs(M)
M0 = M.copy(); M0[:3,3] += [8,-6,12]; M0[:3,:3] = S.Rot.from_euler('y',15,degrees=True).as_matrix() @ M0[:3,:3]
res = S.make_res(obs, Xs, uvn, lam_rgb=1.0); Mh,_ = S.solve(res, M0)
fig, ax = plt.subplots(1,2, figsize=(11,4.4))
for a,(P,t) in zip(ax,[(M0,'before (init)'),(Mh,'after joint solve')]):
    u,_ = S.project(Xs,P,K); a.scatter(uvn[:,0],uvn[:,1],s=10,c='k',label='observed'); a.scatter(u[:,0],u[:,1],s=10,c='r',label='projected')
    err = np.mean(np.linalg.norm(u-uvn,axis=1)); a.set_title(f'{t}: mean {err:.2f} px',fontsize=9)
    a.invert_yaxis(); a.legend(fontsize=7); a.grid(alpha=.3)
fig.suptitle('Figure 3  RGB reprojection before/after joint optimisation (Test A, noise 0.7 px)', fontsize=11)
fig.tight_layout(); fig.savefig(V/'A_method_comparison/fig_reprojection.png', dpi=130); plt.close(fig)

# 3) Test A / B metrics
a = pd.read_csv(T/'metrics/SYNTHETIC_V2.csv'); A = a[a.test=='A']; B = a[a.test=='B']
fig, ax = plt.subplots(1,3, figsize=(15,4))
lbl = [f"{r.arm}\nnoise={r.noise} pert={r.pert_rot}" for r in A.itertuples()]
order = np.arange(len(A))
ax[0].bar(order, A.normal_err_deg, color='#468'); ax[0].set_xticks(order); ax[0].set_xticklabels(lbl, rotation=80, fontsize=6)
ax[0].set_ylabel('ring-plane normal error (deg)'); ax[0].set_title('Test A: normal error', fontsize=9)
ax[1].bar(order, A.center_err_mm, color='#a35'); ax[1].set_xticks(order); ax[1].set_xticklabels(lbl, rotation=80, fontsize=6)
ax[1].set_ylabel('camera centre error (mm)'); ax[1].set_title('Test A: centre error', fontsize=9)
ax[2].bar(range(len(B)), B.held_reproj_px, color='#2a7'); ax[2].set_xticks(range(len(B))); ax[2].set_xticklabels(B.arm, fontsize=8)
ax[2].set_ylabel('held-out reprojection (px)'); ax[2].set_title('Test B: holdout (3 cams, unknown points)', fontsize=9)
fig.suptitle('Figure 4  Two-level synthetic validation after the fixes', fontsize=11)
fig.tight_layout(); fig.savefig(V/'B_ring_only_vs_joint/fig_synth_metrics.png', dpi=130); plt.close(fig)
print('figs done')
