"""Single canonical CAD-contour metric: exact point-to-segment distance."""
import numpy as np


def dist_pts_to_polyline(pts, poly):
    a = np.asarray(poly, float); b = np.roll(a, -1, axis=0)
    d = b - a; L2 = np.maximum((d*d).sum(1), 1e-12); P = np.asarray(pts, float)
    ap = P[:, None, :] - a[None, :, :]
    t = np.clip((ap*d[None]).sum(2)/L2[None], 0.0, 1.0)
    proj = a[None] + t[..., None]*d[None]
    return np.linalg.norm(P[:, None, :] - proj, axis=2).min(1)


def split_by_area(curves):
    import cv2
    ar = [abs(cv2.contourArea(np.asarray(c, np.float32).reshape(-1, 1, 2))) for c in curves]
    return curves[int(np.argmin(ar))], curves[int(np.argmax(ar))]


def ring_raw_mae(pose, q_train, K, ring_radius=5.6, ring_wire=.6):
    """min over the two CAD curves, per observation point (the frozen definition)."""
    from ring_first_3d.mainline.native.camera import torus_contours
    cs = torus_contours(np.asarray(pose), np.asarray(K),
                        ring_radius=ring_radius, ring_wire=ring_wire)
    return float(np.minimum(dist_pts_to_polyline(q_train, np.asarray(cs[0], float)),
                            dist_pts_to_polyline(q_train, np.asarray(cs[1], float))).mean())
