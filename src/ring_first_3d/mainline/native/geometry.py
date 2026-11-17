"""Frozen integer-index pixel geometry and original native-grid triangulation."""
import types
import builtins
import numpy as np
import trimesh
from . import _kernels

RING_MAJOR_MM = 5.6
RING_TUBE_MM = 0.6
RING_INNER_MM = 10.0
MAX_DEPTH_JUMP_MM = 0.75

def validate_camera(c2w, K):
    C = np.asarray(c2w, float); K = np.asarray(K, float)
    if C.shape != (4, 4) or K.shape != (3, 3):
        raise ValueError("Expected 4x4 c2w and 3x3 K")
    if not np.isfinite(C).all() or not np.isfinite(K).all():
        raise ValueError("Non-finite camera")
    if not np.allclose(C[3], [0, 0, 0, 1]) or not np.allclose(C[:3,:3].T @ C[:3,:3], np.eye(3), atol=1e-6) or not np.isclose(np.linalg.det(C[:3,:3]), 1, atol=1e-6):
        raise ValueError("c2w must be a proper rigid transform")
    if K[0,0] <= 0 or K[1,1] <= 0:
        raise ValueError("Non-positive focal length")
    return C, K

def project(X, c2w, K):
    C, K = validate_camera(c2w, K)
    q = (np.asarray(X) - C[:3,3]) @ C[:3,:3]
    p = q @ K.T
    return p[..., :2] / p[..., 2:], q[..., 2]

def unproject(z_mm, c2w, uv_index, K):
    C, K = validate_camera(c2w, K)
    return types.FunctionType(_kernels.unproject.__code__, {"np": np,"__builtins__":vars(builtins)})(np.asarray(z_mm), C, np.asarray(uv_index), K)

def resize_index_intrinsics(K, old_hw=(360,640), new_hw=(352,640)):
    """Half-pixel resize of index-centred K. This is resizing RGB, not cropping depth."""
    sy, sx = np.asarray(new_hw, float) / np.asarray(old_hw, float)
    A = np.array([[sx, 0, .5*sx-.5], [0, sy, .5*sy-.5], [0,0,1]])
    return A @ np.asarray(K)

def native_rgb_labels(rgb, labels, K, native_hw=(352,640)):
    Kn = resize_index_intrinsics(K, labels.shape, native_hw)
    yy, xx = np.mgrid[:native_hw[0], :native_hw[1]]
    p = np.c_[xx.ravel(), yy.ravel(), np.ones(xx.size)] @ np.linalg.inv(Kn).T @ np.asarray(K).T
    p = np.floor(p[:,:2]/p[:,2:]+.5).astype(int)
    if (p < 0).any() or (p[:,0]>=labels.shape[1]).any() or (p[:,1]>=labels.shape[0]).any():
        raise ValueError("Native pixel mapping outside RGB/Mask")
    return rgb[p[:,1],p[:,0]].reshape(*native_hw,3), labels[p[:,1],p[:,0]].reshape(native_hw), Kn

def depth_mesh(depth_mm, labels, c2w, K, rgb):
    C, K = validate_camera(c2w, K)
    ns = {"np": np,"__builtins__":vars(builtins), "unproject": unproject, "cfg": lambda: {"mesh_max_depth_jump_mm": MAX_DEPTH_JUMP_MM}}
    fn = types.FunctionType(_kernels.depth_mesh.__code__, ns)
    mesh = fn(np.asarray(depth_mm), np.asarray(labels)==1, C, K, rgb)
    y, x = np.nonzero((labels==1) & np.isfinite(depth_mm) & (depth_mm>0))
    return mesh, np.c_[x,y], y*depth_mm.shape[1]+x

def ring_mesh(n_major=128, n_tube=32):
    """Known R10 CAD torus; black solid, not a reconstructed point cloud."""
    th, ph = np.meshgrid(np.arange(n_major)*2*np.pi/n_major, np.arange(n_tube)*2*np.pi/n_tube, indexing="ij")
    V = np.stack([(RING_MAJOR_MM+RING_TUBE_MM*np.cos(ph))*np.cos(th), (RING_MAJOR_MM+RING_TUBE_MM*np.cos(ph))*np.sin(th), RING_TUBE_MM*np.sin(ph)], -1).reshape(-1,3)
    a = np.arange(n_major*n_tube).reshape(n_major,n_tube); b=np.roll(a,-1,axis=0); c=np.roll(a,-1,axis=1); d=np.roll(b,-1,axis=1)
    F=np.r_[np.stack([a,b,c],-1).reshape(-1,3), np.stack([b,d,c],-1).reshape(-1,3)]
    return trimesh.Trimesh(V,F,vertex_colors=np.tile([0,0,0,255],(len(V),1)),process=False)
