"""Fail closed input binding for W0 and downstream HERO tuples."""
import hashlib
import json
from pathlib import Path

import numpy as np


def sha256_file(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _path(value, workspace):
    path = Path(value)
    return path if path.is_absolute() else Path(workspace) / path


def _verified_file(path, expected, label):
    if not path.is_file() or sha256_file(path) != expected:
        raise ValueError(f"{label}_HASH: {path}")


def verify_w0_packet(packet_dir, workspace):
    """Bind the W0 arrays to the exact manifest, prepared views and tracks."""
    packet_dir = Path(packet_dir)
    manifest = json.loads((packet_dir / "manifest.json").read_text())
    prepared = manifest["prepared"]
    prepared_path = _path(prepared["path"], workspace)
    _verified_file(prepared_path, prepared["sha256"], "PREPARED")
    metadata = json.loads(prepared_path.read_text())
    entries = sorted(metadata["views"], key=lambda x: (x["raw_frame"], x["view"]))
    ids = [str(v["view"]) for v in entries]
    if len(ids) != len(set(ids)) or ids != list(map(str, manifest["ids"])):
        raise ValueError("PREPARED_W0_IDS_MISMATCH")
    if [int(v["raw_frame"]) for v in entries] != list(map(int, manifest["raw_frames"])):
        raise ValueError("PREPARED_W0_FRAME_MISMATCH")
    if set(prepared["views_sha256"]) != set(ids):
        raise ValueError("PREPARED_CACHE_MAPPING_MISMATCH")
    views = {}
    for view in entries:
        cache = _path(view["cache"], workspace)
        _verified_file(cache, prepared["views_sha256"][view["view"]], "CACHE")
        views[view["view"]] = dict(view, cache=str(cache))
    source = _path(manifest["source_video"], workspace)
    _verified_file(source, manifest["source_video_sha256"], "SOURCE_VIDEO")
    tracks_path = _path(manifest["tracks"]["path"], workspace)
    _verified_file(tracks_path, manifest["tracks"]["sha256"], "TRACK")
    pairs_path = tracks_path.with_name("pairs005.npz")
    pairs_sha256 = sha256_file(pairs_path) if pairs_path.is_file() else None
    w0_path = packet_dir / "W0.npz"
    _verified_file(w0_path, manifest["artifacts"]["W0.npz"]["sha256"], "W0")
    with np.load(w0_path) as w0, np.load(tracks_path) as tracks:
        if list(map(str, w0["ids"])) != ids:
            raise ValueError("W0_IDS_MISMATCH")
        poses = np.asarray(w0["c2w"], float)
        points = np.asarray(w0["points"], float)
        point_track_ids = np.asarray(w0["point_track_ids"], int)
        K = np.asarray(w0["K"], float)
        ring = np.asarray(w0["ring_cad_mm"], float)
        track_count = int(len(tracks["xy"]))
        if (len(points) != len(point_track_ids) or
                (len(point_track_ids) and (point_track_ids.min() < 0 or point_track_ids.max() >= track_count))):
            raise ValueError("TRACK_ID_RANGE")
        if poses.shape != (len(ids), 4, 4) or points.ndim != 2 or points.shape[1] != 3:
            raise ValueError("W0_GEOMETRY_SHAPE")
        if not np.isfinite(poses).all() or not np.isfinite(points).all() or not np.isfinite(K).all():
            raise ValueError("W0_NONFINITE_GEOMETRY")
        if not np.allclose(poses[:, 3], [0, 0, 0, 1], atol=1e-5) or not np.allclose(
                poses[:, :3, :3] @ poses[:, :3, :3].transpose(0, 2, 1), np.eye(3), atol=1e-2):
            raise ValueError("W0_INVALID_POSE")
        expected_ring = [3.1, .6] if "R5" in manifest["group"] else [5.6, .6]
        if not np.allclose(ring, expected_ring, atol=1e-8) or not np.allclose(
                manifest["ring_cad_mm"], expected_ring, atol=1e-8):
            raise ValueError("RING_CAD_CONTRACT")
        if K.shape != (3, 3) or K[0, 0] <= 0 or K[1, 1] <= 0:
            raise ValueError("W0_INVALID_K")
        for view in views.values():
            with np.load(view["cache"]) as cache:
                if not np.allclose(cache["K"], K, atol=1e-8):
                    raise ValueError("CACHE_K_W0_MISMATCH")
        cameras = {cid: poses[i].copy() for i, cid in enumerate(ids)}
    return dict(verified=True, group=manifest["group"], video=str(manifest["video"]),
                views=views, cameras=cameras, K=K, points=points,
                track_count=track_count, manifest=manifest, w0_path=str(w0_path),
                pairs_sha256=pairs_sha256,
                source_video_sha256=manifest["source_video_sha256"])


def tuple_receipt(identity_verified, frames, run_id, code_version):
    """Hash actual arrays passed to the frozen HERO inference call."""
    if identity_verified is not True:
        raise ValueError("IDENTITY_NOT_VERIFIED")
    if len(frames) != 4 or len({f["id"] for f in frames}) != 4:
        raise ValueError("HERO_TUPLE_REQUIRES_FOUR_DISTINCT_FRAMES")
    rows = []
    for frame in frames:
        row = {"id": frame["id"]}
        for name, key in (("RGB", "RGB"), ("Mask", "labels"),
                          ("K", "K"), ("c2w", "c2w_mm")):
            array = np.ascontiguousarray(frame[key])
            if not np.isfinite(array).all():
                raise ValueError("HERO_NONFINITE_INPUT")
            row[name + "_sha256"] = hashlib.sha256(array.tobytes()).hexdigest()
            row[name + "_shape"] = list(array.shape)
        rows.append(row)
    encoded = json.dumps(rows, sort_keys=True).encode()
    return dict(run_id=run_id, code_version=code_version,
                tuple_sha256=hashlib.sha256(encoded).hexdigest(), frames=rows,
                input_identity_verified=True)
