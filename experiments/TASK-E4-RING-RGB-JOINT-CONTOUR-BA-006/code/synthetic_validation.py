"""P2: synthetic validation of the flexible Ring constraint + tau/lambda trade-off."""
import sys, json
from pathlib import Path
import numpy as np, cv2, pandas as pd
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation as Rot
sys.path.insert(0, str(Path(__file__).resolve().parent))
import joint_loss as JL, cad_contour_correspondence as CC

T = Path(__file__).resolve().parents[1]
K = np.array([[490.,0,319.5],[0,490.,179.5],[0,0,1]])
from ring_first_3d.mainline.native.camera import torus_contours

def make_pose(d=45., tilt=0., yaw=0., shift=(0,0)):
    M = np.eye(4); M[:3,:3] = Rot.from_euler('z', yaw, degrees=True).as_matrix() @ Rot.from_euler('x', tilt, degrees=True).as_matrix()
    M[:3,3] = [shift[0], shift[1], d]; return M

def dxy_from(cad_curve, scale=1.0, offset=(0.,0.)):
    (cx,cy),(d1,d2),ang = cv2.fitEllipse(np.asarray(cad_curve,np.float32).reshape(-1,1,2))
    t = np.linspace(0,2*np.pi,360,endpoint=False)
    c,s = np.cos(np.deg2rad(ang)), np.sin(np.deg2rad(ang))
    x = scale*d1/2*np.cos(t); y = scale*d2/2*np.sin(t)
    return np.c_[c*x - s*y + cx+offset[0], s*x + c*y + cy+offset[1]]

def synth_pts(M, n=40, noise=0.5, seed=0):
    th = np.linspace(0,2*np.pi,n,endpoint=False)
    R, r = 5.6, 0.6
    X = np.c_[ (R + r*np.cos(th))*np.cos(th), (R + r*np.cos(th))*np.sin(th), r*np.sin(th)]
    uv, z = __import__('ring_first_3d.mainline.native.geometry', fromlist=['project']).project(X, M, K)
    rng = np.random.default_rng(seed)
    return X, uv + rng.normal(0, noise, uv.shape), z

def param_err(M, Mhat):
    R = Mhat[:3,:3] @ M[:3,:3].T
    ang = np.degrees(np.linalg.norm(Rot.from_matrix(R).as_rotvec()))
    return float(ang), float(np.linalg.norm(Mhat[:3,3]-M[:3,3]))

def solve(obs, X, uv, M0, tau, lam_rgb, sigma_rgb=0.7):
    def res(p):
        M = np.eye(4); M[:3,:3] = Rot.from_rotvec(p[:3]).as_matrix(); M[:3,3] = p[3:]
        rb = JL.ring_block(M, K, obs, tau=tau)
        uvhat, z = __import__('ring_first_3d.mainline.native.geometry', fromlist=['project']).project(X, M, K)
        rp = np.clip((uvhat-uv)/sigma_rgb, -3, 3).ravel()
        return np.r_[rb, lam_rgb*rp]
    p0 = np.r_[Rot.from_matrix(M0[:3,:3]).as_rotvec(), M0[:3,3]]
    out = least_squares(res, p0, loss='huber', f_scale=1.0, max_nfev=300)
    M = np.eye(4); M[:3,:3] = Rot.from_rotvec(out.x[:3]).as_matrix(); M[:3,3] = out.x[3:]
    return M, float(out.cost)

def main():
    rows = []
    cases = [('front',0,1.0,0.0),('tilt',25,1.0,0.0),('model_err',15,1.04,0.0)]
    for name, tilt, scale, occ in cases:
        M = make_pose(45., tilt)
        ci, co = CC.split(torus_contours(M, K))
        off = (1.5,0.0) if name=='offset' else (0.0,0.0)
        pin = dxy_from(ci, scale, off); pout = dxy_from(co, scale, off)
        n = len(pin)
        vin = np.ones(n, bool); vout = np.ones(n, bool)
        if occ > 0:
            k = int(occ*n); vin[:k] = False; vout[:k] = False
        ob = dict(inner=pin, outer=pout, inner_vis=vin, outer_vis=vout, quality={})
        X, uv, _ = synth_pts(M)
        M0 = M.copy(); M0[:3,3] += [6., -4, 8]; M0[:3,:3] = Rot.from_euler('y',12,degrees=True).as_matrix() @ M0[:3,:3]
        for tau in (0.0, 1.0, 2.0):
            for lam in (0.0, 1.0):
                if lam == 0.0 and tau != 1.0: continue
                Mh, cost = solve(ob, X, uv, M0, tau, lam)
                ang, tr = param_err(M, Mh)
                rb = float(np.sum(JL.ring_block(Mh, K, ob, tau=tau)))
                from ring_first_3d.mainline.native.geometry import project
                uvhat,_ = project(X, Mh, K)
                rgb = float(np.mean(np.linalg.norm(uvhat-uv, axis=1)))
                rows.append(dict(case=name, tau=tau, lam=lam, rot_deg=ang, trans_mm=tr,
                                 E_ring=rb, E_rgb_train=rgb))
    df = pd.DataFrame(rows); df.to_csv(T/'metrics/SYNTHETIC_SWEEP.csv', index=False)
    # figure C
    fig, ax = plt.subplots(figsize=(7,5))
    for tau, g in df[df.lam==1.0].groupby('tau'):
        ax.plot(g.E_ring, g.E_rgb_train, 'o', label=f'tau={tau}')
    for case, g in df[(df.lam==1.0)&(df.tau==1.0)].groupby('case'):
        pass
    ax.set_xlabel('E_ring (flexible contour residual)'); ax.set_ylabel('E_rgb train (px)')
    ax.set_title('Synthetic Ring-RGB trade-off (lam_rgb=1)', fontsize=9); ax.legend(fontsize=7); ax.grid(alpha=.3)
    fig.tight_layout(); fig.savefig(T/'visualization/C_loss_tradeoff/figC_tradeoff.png', dpi=130); plt.close(fig)
    # figure A synthetic
    M = make_pose(45., 15); ci, co = CC.split(torus_contours(M,K))
    pin = dxy_from(ci, 1.04); pout = dxy_from(co, 1.04)
    fig, ax = plt.subplots(1,3, figsize=(13,4))
    ax[0].plot(np.asarray(ci)[:,0], np.asarray(ci)[:,1], '-', c='yellow'); ax[0].plot(np.asarray(co)[:,0], np.asarray(co)[:,1], '-', c='orange')
    ax[0].set_title('CAD projection (true pose)', fontsize=9)
    ax[1].plot(pin[:,0], pin[:,1], '-', c='cyan'); ax[1].plot(pout[:,0], pout[:,1], '-', c='magenta')
    ax[1].set_title('DXY-like fit (4% scale error)', fontsize=9)
    ax[2].plot(np.asarray(ci)[:,0], np.asarray(ci)[:,1], '-', c='yellow'); ax[2].plot(pin[:,0], pin[:,1], '--', c='cyan')
    ax[2].set_title('overlay: CAD vs fit', fontsize=9)
    for a in ax: a.set_aspect('equal'); a.grid(alpha=.3); a.invert_yaxis()
    fig.suptitle('Figure A  Synthetic model-error case used for tau calibration', fontsize=11)
    fig.tight_layout(); fig.savefig(T/'visualization/A_method_comparison/figA_synthetic.png', dpi=130); plt.close(fig)
    print(df.to_string(index=False))
if __name__=='__main__': main()
