"""One-time raw official/historical baseline, independently of the public adapters.

Never overwrites an existing reference. Not part of normal test execution.
"""
from _bootstrap import args, emit, ROOT
import ast
import hashlib
import json
from pathlib import Path
import sys
import time
import numpy as np
from ring_first_3d._legacy import LOCK, source


def main():
    a = args(__doc__)
    output = a.output or ROOT / "tools/research/frozen_reference.json"
    if output.exists():
        raise FileExistsError("Reference is frozen; refusing overwrite")
    f = json.loads(a.fixture.read_text())
    import cv2
    import torch
    from pytorch3d.structures import Meshes
    from pytorch3d.renderer import MeshRenderer, MeshRasterizer, SoftSilhouetteShader, RasterizationSettings, BlendParams
    from pytorch3d.utils import cameras_from_opencv_projection
    root = Path(f["real_case_root"])
    load = lambda p: json.loads(Path(p).read_text())
    ns = dict(np=np, cv2=cv2, torch=torch, device=torch.device("cuda:0"), R=root,
              getcase=lambda name: load(root / "inputs" / name / "CASE.json"), load=load,
              Meshes=Meshes, MeshRenderer=MeshRenderer, MeshRasterizer=MeshRasterizer,
              SoftSilhouetteShader=SoftSilhouetteShader, RasterizationSettings=RasterizationSettings,
              BlendParams=BlendParams, cameras_from_opencv_projection=cameras_from_opencv_projection)
    nodes = [n for n in source("T24").body if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name in ["tensor", "mesh", "renderer", "Case"]]
    exec(compile(ast.Module(body=nodes, type_ignores=[]), "raw_frozen_p3d.py", "exec"), ns)
    t = time.monotonic();c = ns["Case"](f["case"]);cid = f["sample_view"]
    fr = c.fragments(c.base, cid);loss, alpha, w, vis, p = c.aware(fr, cid, True)
    result = dict(generator="Direct official API and SHA-locked historical AST; no public adapter calls",
                  source_lock_SHA256=hashlib.sha256((ROOT / "src/ring_first_3d/source_lock.json").read_bytes()).hexdigest(),
                  fixture_SHA256=hashlib.sha256(a.fixture.read_bytes()).hexdigest(),
                  renderer=dict(loss=float(loss), alpha_sum=float(alpha.sum()), alpha_square_sum=float((alpha**2).sum()),
                                weights_sum=float(w.sum()), visible=float(vis.sum()),
                                alpha_sha256=hashlib.sha256(alpha.detach().cpu().numpy().tobytes()).hexdigest(),
                                seconds=time.monotonic()-t, device=torch.cuda.get_device_name()))
    del c,fr,alpha,w,vis,p,loss
    torch.cuda.empty_cache()
    sys.path.insert(0, str(a.dxy_root / "src"))
    from dxy_mid.pipeline import measure_frame, VERSION
    data = np.load(root / "inputs" / f["case"] / (cid + ".npz"))
    rgb,lab = data["RGB"],data["labels"]
    t = time.monotonic()
    d = measure_frame(np.ascontiguousarray(rgb[:,:,::-1]), lab.copy(), inner_diameter_mm=f["inner_diameter_mm"],
                      source_id=f["dxy_source_id"], image_sha256=hashlib.sha256(rgb.tobytes()).hexdigest(), mask_sha256=hashlib.sha256(lab.tobytes()).hexdigest())
    result["dxy"] = dict(available=d.candidate is not None, version=VERSION, Geometry=d.audit["Geometry"],
        quality_class=d.audit["quality_class"], center_px=None if d.candidate is None else d.candidate.center_native,
        basis_px=None if d.candidate is None else d.candidate.basis_native, seconds=time.monotonic()-t)
    emit(result, output)

if __name__ == "__main__":
    main()
