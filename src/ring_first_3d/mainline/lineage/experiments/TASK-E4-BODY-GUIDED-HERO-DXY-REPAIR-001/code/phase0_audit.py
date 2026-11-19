#!/usr/bin/env python3
"""Phase 0 only: bind and audit the 75 frozen Body-E input sources.

This is deliberately an input/provenance utility.  It does not import DXY,
fit a body, inspect GT, or read historical Body-U values.
"""
from ring_first_3d.mainline.paths import historical_path as _mainline_path
from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

import cv2
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
OLD = REPO / "experiments/TASK-E4-BODY-GUIDED-HERO-RELOCALIZATION-001"
MAX = REPO / "experiments/TASK-E4-RING-FIRST-MAX-COVERAGE-VIEWS-001"
SOURCES_PATH = OLD / "config/SOURCES.json"
RAW_POOL_PATH = MAX / "config/RAW_CAMERA_CANDIDATES.json"
CASE_ROOT = Path(str(_mainline_path('/home/liu/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-BODY-ANCHORED-MULTIHERO-001/inputs')))
DXY = Path("/home/liu/new-polyp-dxy")


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def asset(path: Path) -> dict:
    return {"path": str(path), "sha256": sha256(path), "bytes": path.stat().st_size}


def write_json(relative: str, payload) -> None:
    path = ROOT / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def pose_status(candidate: dict) -> str:
    pose = candidate.get("initial_pose")
    if pose is None:
        return "NO_METRIC_POSE_IN_POOL"
    a = np.asarray(pose, dtype=np.float64)
    if a.shape != (4, 4) or not np.isfinite(a).all():
        return "INVALID_METRIC_POSE"
    r = a[:3, :3]
    if not np.allclose(r.T @ r, np.eye(3), atol=1e-5) or not np.isclose(np.linalg.det(r), 1.0, atol=1e-5):
        return "NON_RIGID_POSE_MATRIX"
    return "FROZEN_METRIC_POSE"


def input_shape_and_classes(rgb_path: Path, mask_path: Path) -> tuple[str, str, str, str]:
    rgb = cv2.imread(str(rgb_path), cv2.IMREAD_COLOR)
    mask = cv2.imread(str(mask_path), cv2.IMREAD_UNCHANGED)
    if rgb is None or mask is None:
        raise RuntimeError(f"IMAGE_DECODE_FAILED rgb={rgb_path} mask={mask_path}")
    if mask.ndim == 3:
        if mask.shape[2] != 1:
            raise RuntimeError(f"MASK_NOT_SINGLE_CHANNEL {mask_path}: {mask.shape}")
        mask = mask[..., 0]
    classes = sorted(map(int, np.unique(mask)))
    required = {0, 1, 2}
    state = "VALID_0_1_2" if set(classes).issubset(required) and required.issubset(set(classes)) else "INVALID_CLASS_ENCODING"
    return f"{rgb.shape[1]}x{rgb.shape[0]}", f"{mask.shape[1]}x{mask.shape[0]}", ";".join(map(str, classes)), state


def main() -> None:
    if not DXY.is_dir() or not (DXY / ".git").is_dir():
        raise RuntimeError("OFFICIAL_DXY_CHECKOUT_MISSING")
    commit = (DXY / ".git/HEAD").read_text().strip()
    # Resolve a symbolic HEAD without shelling out; the expected revision must be exact.
    if commit.startswith("ref: "):
        commit = (DXY / ".git" / commit.split(" ", 1)[1]).read_text().strip()
    expected = "75d58ca5b643fb4d8e0eb887b45ad0f056b0bb95"
    if commit != expected:
        raise RuntimeError(f"DXY_COMMIT_MISMATCH expected={expected} actual={commit}")

    pipeline_path = DXY / "src/dxy_mid/pipeline.py"
    version_match = re.search(r"^VERSION\s*=\s*['\"]([^'\"]+)['\"]", pipeline_path.read_text(encoding="utf-8"), re.MULTILINE)
    if version_match is None:
        raise RuntimeError("DXY_VERSION_CONSTANT_NOT_FOUND")
    sources = load(SOURCES_PATH)
    pool = load(RAW_POOL_PATH)
    if len(sources) != 75:
        raise RuntimeError(f"EXPECTED_75_SOURCES got={len(sources)}")
    by_id = {}
    for c in pool:
        for name in {c["id"], *c.get("aliases", [])}:
            by_id.setdefault(name, []).append(c)

    case = {g: load(CASE_ROOT / g / "CASE.json") for g in ("G03", "G05", "G01", "G06")}
    rows, source_audit = [], []
    status_counts = Counter()
    for source in sorted(sources, key=lambda x: (x["group"], x["id"])):
        meta = load(Path(source["source"]))
        candidates = by_id.get(source["view_id"], [])
        target_sha = meta.get("target_SHA")
        exact = [x for x in candidates if target_sha and x.get("RGB_SHA256") == target_sha]
        if exact:
            bound, binding = exact[0], "VIEW_ID_AND_METADATA_RGB_SHA256"
        elif len(candidates) == 1:
            bound, binding = candidates[0], "UNIQUE_VIEW_ID_ARCHIVE_BINDING_NO_TARGET_SHA"
        else:
            raise RuntimeError(f"AMBIGUOUS_OR_MISSING_BINDING {source['id']} candidates={len(candidates)}")

        rgb_path, mask_path, cache_path = map(Path, (bound["RGB_source"], bound["Mask_source"], bound["cache"]))
        for p in (rgb_path, mask_path, cache_path, Path(source["source"]), Path(source["obs"]), Path(source["mesh"])):
            if not p.is_file():
                raise RuntimeError(f"MISSING_REQUIRED_INPUT {source['id']} {p}")
        rgb_sha, mask_sha = sha256(rgb_path), sha256(mask_path)
        if rgb_sha != bound["RGB_SHA256"]:
            raise RuntimeError(f"RGB_SHA_MISMATCH {source['id']}")
        if bound.get("Mask_SHA256") and mask_sha != bound["Mask_SHA256"]:
            raise RuntimeError(f"MASK_SHA_MISMATCH {source['id']}")
        rgb_shape, mask_shape, mask_classes, mask_state = input_shape_and_classes(rgb_path, mask_path)
        ring = case[source["group"]]
        inner_diameter = {"R5": 5.0, "R10": 10.0}.get(ring["ring"])
        if inner_diameter is None:
            raise RuntimeError(f"UNSUPPORTED_RING {source['group']} {ring['ring']}")
        pstate = pose_status(bound)
        coordinate_pool = f"VIDEO_{bound['video']}" if bound["video"] in ("004", "005") else "INDEPENDENT_PHOTO"
        joint_policy = (
            "SEPARATE_PENDING_021_STYLE_EVIDENCE" if bound["video"] == "005" and source["group"] == "G01"
            else "SEPARATE_NO_CROSS_VIDEO_EVIDENCE" if bound["video"] == "005"
            else "PHOTO_SEPARATE_NO_METRIC_POSE" if bound["video"] == "PHOTO"
            else "SAME_VIDEO_004_CANDIDATE_ONLY"
        )
        row = {
            "source_id": source["id"], "group": source["group"], "source_origin": source["origin"],
            "source_role": source["role"], "view_id": source["view_id"], "video": bound["video"],
            "capture_type": bound.get("capture_type"), "coordinate_pool": coordinate_pool,
            "cross_video_joint_policy_phase0": joint_policy, "bound_camera_id": bound["id"],
            "binding": binding, "rgb_path": str(rgb_path), "mask_path": str(mask_path), "cache_path": str(cache_path),
            "rgb_sha256": rgb_sha, "mask_sha256": mask_sha, "cache_sha256": sha256(cache_path),
            "rgb_shape": rgb_shape, "mask_shape": mask_shape, "mask_classes": mask_classes, "mask_encoding": mask_state,
            "ring_id": ring["ring"], "ring_inner_diameter_mm_for_dxy": inner_diameter,
            "ring_mid_radius_mm_not_used": ring["R_mid_mm"], "ring_wire_mm_not_used": ring["wire_mm"],
            "K": bound["K"], "camera_pose": bound.get("initial_pose"), "camera_pose_status": pstate,
            "camera_pose_source": bound.get("initial_pose_source"), "sharpness": bound.get("sharpness"),
            "glare_fraction": bound.get("glare_fraction"), "polyp_pixels": bound.get("polyp_pixels"),
            "ring_pixels": bound.get("ring_pixels"), "raw_status": bound.get("raw_status"),
            "source_metadata_sha256": sha256(Path(source["source"])), "observation_sha256": sha256(Path(source["obs"])),
            "trusted_mesh_sha256": sha256(Path(source["mesh"])), "gt_read": False,
        }
        rows.append(row)
        source_audit.append({"source": source, "bound_camera": bound, "row": row})
        status_counts[(row["video"], row["camera_pose_status"], row["mask_encoding"])] += 1

    fields = list(rows[0])
    out_csv = ROOT / "VIEW_INVENTORY.csv"
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v for k, v in row.items()})

    write_json("provenance/PHASE0_SOURCE_BINDING.json", source_audit)
    write_json("provenance/PHASE0_INPUT_FILES.json", {
        "sources": asset(SOURCES_PATH), "raw_camera_candidates": asset(RAW_POOL_PATH),
        "requested_final_camera_pool": str(MAX / "config/FINAL_CAMERA_POOL.json"),
        "requested_final_camera_pool_exists": False,
        "substitution": "RAW_CAMERA_CANDIDATES.json is the extant frozen pool; no claim it is an identical file",
        "official_dxy_commit": commit, "official_dxy_VERSION": version_match.group(1), "official_dxy_src_pipeline": asset(pipeline_path),
        "rows": len(rows), "counts": {"|".join(k): v for k, v in sorted(status_counts.items())}, "GT_read": False,
    })
    print(f"PHASE0_AUDIT_OK rows={len(rows)} dxy={commit} status={dict(status_counts)}")


if __name__ == "__main__":
    main()
