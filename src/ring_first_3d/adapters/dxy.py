"""T01/T03 API adapter. Only pixel geometry and nonmetric quality leave this interface."""
import hashlib
import importlib
from pathlib import Path
import subprocess
import sys
import numpy as np
from .._legacy import LOCK
from ..contracts.identities import sha256

QUALITY = ("version", "Geometry", "ring_valid", "ring_reason", "normal_Gate_pass",
           "Q_conflict_recovery", "strict_stable", "accepted", "candidate_generated",
           "stability_review_pass", "geometry_state", "quality_class", "reason",
           "stability_flags", "P_count", "Q_count", "X_count", "body", "branch",
           "P_zero_occlusion_inference", "coordinate_system", "GT_read",
           "history_prediction_fallback", "processed_mask_sha256")


def verify_dxy(root):
    root = Path(root).resolve()
    head = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
    if head != LOCK["dxy_commit"]:
        raise ValueError("Official DXY commit differs from frozen V9.1")
    for p, digest in LOCK["dxy_sources"].items():
        if sha256(root / p) != digest:
            raise ValueError("Official DXY source changed: " + p)
    return head


def measure_pixels(rgb, labels, *, inner_diameter_mm, source_id, dxy_root):
    root = Path(dxy_root).resolve()
    head = verify_dxy(root)
    rgb, labels = np.asarray(rgb), np.asarray(labels)
    if rgb.dtype != np.uint8 or labels.dtype != np.uint8 or rgb.shape != (*labels.shape, 3) or not set(np.unique(labels)) <= {0, 1, 2}:
        raise ValueError("Aligned native RGB uint8 HxWx3 and class mask uint8 HxW required")
    if not source_id:
        raise ValueError("Frozen source_id is required")
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(root / "src"))
    api = importlib.import_module("dxy_mid.pipeline")
    if Path(api.__file__).resolve() != root / "src/dxy_mid/pipeline.py" or api.VERSION != LOCK["dxy_version"]:
        raise ValueError("Wrong DXY module already imported")
    rh = hashlib.sha256(rgb.tobytes()).hexdigest()
    mh = hashlib.sha256(labels.tobytes()).hexdigest()
    result = api.measure_frame(np.ascontiguousarray(rgb[:, :, ::-1]), labels.copy(),
        inner_diameter_mm=inner_diameter_mm, source_id=source_id, image_sha256=rh, mask_sha256=mh)
    rec = dict(available=result.candidate is not None, quality={k: result.audit.get(k) for k in QUALITY},
        source=dict(id=source_id, RGB_content_SHA256=rh, Mask_content_SHA256=mh,
                    DXY_commit=head, version=api.VERSION, image_wh=[rgb.shape[1], rgb.shape[0]],
                    coordinates="native_image_px", adapter="T01/T03", history_prediction_fallback=0, GT_read=False))
    if result.candidate is None:
        rec.update(status="NOT_EVALUABLE_DXY_NO_SELECTED_GEOMETRY", center_px=None, basis_px=None)
    else:
        rec.update(status="NUMERIC_GEOMETRY_ONLY", shape=result.candidate.shape,
                   center_px=np.asarray(result.candidate.center_native).copy(),
                   basis_px=np.asarray(result.candidate.basis_native).copy(),
                   candidate_provenance=result.candidate.provenance)
    return rec
