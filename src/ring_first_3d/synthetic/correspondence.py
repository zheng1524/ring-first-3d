"""Frozen correspondence operators; never update Body or read private GT."""
import numpy as np
from scipy.spatial.transform import Rotation
from ..contracts.coordinates import unproject,project,validate_c2w
from .raster import closest,rasterize

METHODS=("nearest_surface","pixel_face","pixel_face_ring")


def inject(uv,z,K,T,condition):
    """Depth bias is camera axial Z; pose perturbation is right-local SE(3)."""
    delta=np.eye(4);delta[:3,:3]=Rotation.from_euler("y",condition["rotation_y_deg"],degrees=True).as_matrix()
    delta[:3,3]=[condition["translation_x_mm"],0,0]
    estimated=T@delta;validate_c2w(estimated)
    biased=np.asarray(z)+condition["depth_bias_mm"]
    points=unproject(uv,biased,K,estimated)
    projected,actual_z=project(points,K,estimated)
    if not np.allclose(projected,uv,atol=1e-8) or not np.allclose(actual_z,biased,atol=1e-8):raise ValueError("Injection coordinate round trip failed")
    relative=np.linalg.inv(T)@estimated
    rotation=float(np.degrees(np.linalg.norm(Rotation.from_matrix(relative[:3,:3]).as_rotvec())))
    if not np.allclose(relative,delta,atol=1e-10) or not np.isclose(rotation,abs(condition["rotation_y_deg"]),atol=1e-8):raise ValueError("Actual pose injection differs")
    return points,estimated,dict(actual_depth_bias_min_mm=float((biased-z).min()),actual_depth_bias_max_mm=float((biased-z).max()),
        actual_rotation_deg=rotation,actual_local_translation_mm=relative[:3,3].tolist(),pose_delta_local=relative.tolist(),uv_roundtrip_max_px=float(abs(projected-uv).max()))


def correspond(V,F,ringV,ringF,uv,P,K,T,size):
    nearest=closest(V,F,P)
    body=rasterize(V,F,K,T,size);ring=rasterize(ringV,ringF,K,T,size)
    x,y=np.asarray(uv,int).T
    valid=body["valid"][y,x]
    pixel=dict(points=body["points"][y,x].copy(),face=body["face"][y,x].copy(),bary=body["bary"][y,x].copy(),valid=valid.copy())
    pixel["bary"][~valid]=np.nan
    ring_ok=valid & (body["z"][y,x]+1e-4<ring["z"][y,x])
    constrained={k:v.copy()for k,v in pixel.items()};constrained["valid"]=ring_ok
    for key in ["points","bary"]:constrained[key][~ring_ok]=np.nan
    constrained["face"][~ring_ok]=-1
    return dict(nearest_surface=nearest,pixel_face=pixel,pixel_face_ring=constrained),dict(body=body,ring=ring)
