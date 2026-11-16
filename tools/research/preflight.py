from _bootstrap import args, emit, ROOT
import importlib
import json
import platform
from pathlib import Path
import sys
import time
import numpy as np
from ring_first_3d import __version__
from ring_first_3d.adapters.dxy import verify_dxy
from ring_first_3d.contracts.coordinates import validate_c2w, validate_ring
from ring_first_3d.contracts.identities import verify_assets, validate_split
from ring_first_3d.evaluation.validation import timed_test


def run(fixture, dxy_root):
    f = json.loads(Path(fixture).read_text());env = dict(python=sys.version, executable=sys.executable,
        platform=platform.platform(), module_version=__version__)
    def dependencies():
        if sys.version_info < (3, 10):raise RuntimeError("Python >=3.10 required")
        for name in ["numpy", "scipy", "cv2", "skimage", "torch", "pytorch3d", "open3d", "trimesh", "fcl"]:
            m = importlib.import_module(name);env[name] = dict(version=getattr(m, "__version__", "not exported"), file=m.__file__)
        import torch
        from pytorch3d import _C
        if not torch.cuda.is_available():raise FileNotFoundError("Real CUDA GPU required for the registered renderer smoke")
        env.update(cuda=torch.version.cuda, GPU=torch.cuda.get_device_name(), pytorch3d_extension=_C.__file__)
        return env
    def sources():
        from audit_reuse import run as audit
        return dict(DXY_commit=verify_dxy(dxy_root), historical_sources=len(audit()["sources"]))
    def inputs():
        count = verify_assets(f["assets"])
        support=json.loads(Path(fixture).with_name("support_fixture.json").read_text())
        count+=verify_assets(support["assets"])
        validate_split(support["views"])
        for key in ["selection_015","selection_016"]:
            item=f[key]
            validate_split([dict(v,id=v["view"]) for v in item["views"]],item["holdout_ids"])
        root = Path(f["real_case_root"])/"inputs"/f["case"]
        meta = json.loads((root/"CASE.json").read_text())
        if meta["unit"] != "mm":raise ValueError("Explicit mm required")
        held = [v["id"] for v in meta["views"] if v["role"] != "FIT"]
        fit = [v for v in meta["views"] if v["role"] == "FIT"]
        validate_split(fit, held)
        for v in meta["views"]:
            with np.load(root/(v["id"]+".npz")) as a:
                validate_c2w(a["T"])
                if a["labels"].shape != (360, 640) or a["RGB"].shape != (360, 640, 3) or a["K"].shape != (3, 3):
                    raise ValueError("Frozen native 640x360 identity mismatch")
        with np.load(root/"RING.npz") as a:
            ring = validate_ring(a["V"], 2*(meta["R_mid_mm"]-meta["wire_mm"]), 2*meta["wire_mm"])
        return dict(verified_assets=count, native_wh=[640, 360], metric_unit="mm", camera="OpenCV c2w; +Z axial depth",
                    FIT=len(fit), HOLDOUT=len(held), ring=ring, GT_read=False)
    tests = [timed_test("dependencies", dependencies), timed_test("versions_and_sources", sources), timed_test("identities_and_contracts", inputs)]
    return dict(status="PASS" if all(t["status"]=="PASS" for t in tests) else "NOT_READY", environment=env, checks=tests)


if __name__ == "__main__":
    a = args("Research input/environment preflight")
    result=run(a.fixture, a.dxy_root);emit(result, a.output)
    raise SystemExit(0 if result["status"]=="PASS" else 1)
