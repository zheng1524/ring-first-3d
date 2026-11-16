"""T24 unchanged Case core, with explicit input/units and no historical common imports."""
import json
from pathlib import Path
import numpy as np
from .._legacy import definitions
from ..contracts.coordinates import validate_c2w, validate_ring


def legacy_namespace(case_root, device="cuda:0"):
    import cv2
    import torch
    from pytorch3d.structures import Meshes
    from pytorch3d.renderer import MeshRenderer, MeshRasterizer, SoftSilhouetteShader, RasterizationSettings, BlendParams
    from pytorch3d.utils import cameras_from_opencv_projection
    root = Path(case_root)
    load = lambda p: json.loads(Path(p).read_text())
    ns = dict(np=np, cv2=cv2, torch=torch, device=torch.device(device), R=root,
              getcase=lambda name: load(root / "inputs" / name / "CASE.json"), load=load,
              Meshes=Meshes, MeshRenderer=MeshRenderer, MeshRasterizer=MeshRasterizer,
              SoftSilhouetteShader=SoftSilhouetteShader, RasterizationSettings=RasterizationSettings,
              BlendParams=BlendParams, cameras_from_opencv_projection=cameras_from_opencv_projection)
    return definitions("T24", ["tensor", "mesh", "renderer", "Case"], ns)


class MetricRenderer:
    """Frozen 014 input pack: V/Ring/T translations in mm, native RGB/K pixels.

    Original normalization, half-pixel transport, raster compensation, face capacity,
    Ring-aware negative supervision and detached z-buffer visibility are untouched.
    """
    def __init__(self, case_root, case, device="cuda:0"):
        root = Path(case_root) / "inputs" / case
        meta = json.loads((root / "CASE.json").read_text())
        if meta["unit"] != "mm":
            raise ValueError("T24 pack must explicitly declare mm units")
        ids = [v["id"] for v in meta["views"]]
        if len(set(ids)) != len(ids) or not any(v["role"] == "FIT" for v in meta["views"]):
            raise ValueError("Unique camera identities and explicit FIT split required")
        for v in meta["views"]:
            with np.load(root / (v["id"] + ".npz")) as a:
                validate_c2w(a["T"])
                if a["RGB"].shape[:2] != a["labels"].shape or a["K"].shape != (3, 3):
                    raise ValueError("Aligned native image/mask/K required")
        with np.load(root / "RING.npz") as a:
            validate_ring(a["V"], 2 * (meta["R_mid_mm"] - meta["wire_mm"]), 2 * meta["wire_mm"])
        self.namespace = legacy_namespace(case_root, device)
        self.case = self.namespace["Case"](case)

    def render(self, view_id, vertices_mm=None):
        import torch
        c = self.case
        if view_id not in c.views:
            raise ValueError("Unknown frozen camera identity")
        V = self.namespace["tensor"](c.V) if vertices_mm is None else self.namespace["tensor"](vertices_mm)
        if tuple(V.shape) != tuple(c.V.shape) or not torch.isfinite(V).all():
            raise ValueError("Finite metric vertices with frozen topology required")
        m = self.namespace["mesh"]((V - self.namespace["tensor"](c.center)) / c.scale, c.F)
        fr = c.fragments(m, view_id)
        loss, alpha, w, visibility, p = c.aware(fr, view_id, True)
        return dict(loss=loss, alpha=alpha, weights=w, visibility=visibility,
                    probabilities=p, fragments=fr, mesh=m, units="mm", view_id=view_id)

    def contour_loss(self):
        """T31 compatibility; accepts world-mm vertex tensor and FIT view id."""
        from scipy.ndimage import distance_transform_edt
        from scipy.spatial import cKDTree
        import torch.nn.functional as tf
        ns = dict(self.namespace, distance_transform_edt=distance_transform_edt, cKDTree=cKDTree, tf=tf)
        definitions("common", ["scene", "contour"], ns)
        return definitions("T31", ["ContourDistance"], ns)["ContourDistance"](self.case)

    def geometry_guard(self, chart):
        """T34 compatibility; chart must supply plane/tau/D/cap, no optimizer migration."""
        import open3d as o3d
        import trimesh
        ns = dict(self.namespace, o3d=o3d, trimesh=trimesh)
        definitions("common", ["scene"], ns)
        definitions("T34", ["self_intersections", "dense_face_distance", "points", "GeometryGuard"], ns)
        return ns["GeometryGuard"](self.case, chart)
