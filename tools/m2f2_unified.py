#!/usr/bin/env python3
"""M2F2: verified W0 -> historical selectors -> frozen HERO -> evaluation.

Each stage consumes the previous stage's frozen receipts. Failed groups remain
in the result tables and never enter inference by implication.
"""
import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np
import pandas as pd

WS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WS / "src"))
from ring_first_3d.mainline.input_identity import sha256_file, tuple_receipt, verify_w0_packet
from ring_first_3d.views.pipeline_adapter import (
    admission_tiers, direction_blocks, select_target_sets, validate_t13)
from ring_first_3d.views.selection import quality_features, select_views

ALIASES = {
    "G01": "GP_Ip_12.0mm_closed_R10_single_refY",
    "G03": "GP_Ip_20.0mm_closed_R10_single_refY",
    "G06": "GP_IIa_14.0mm_closed_R10_single_refY",
}
DEFAULT_OUT = WS / "runs/m2f2_root_cause_corrective"
PYTHON = json.loads((WS / "mainline/configs/SITE.local.json").read_text())["python"]
HISTORICAL = WS / "assets/retained_sources/ring_first_3d_e4_sdf_localization/experiments"
CONFIG_016 = HISTORICAL / "TASK-E4-UPDATE-CAUSALITY-016/config/VIEW_SELECTION_016.json"
INVENTORY_016 = HISTORICAL / "TASK-E4-UPDATE-CAUSALITY-016/metrics/VIEW_SELECTION_AND_WEIGHTS.json"
CLEAN = WS / "runs/m2c_trajectory_admission/clean_labels"
CODE_VERSION = sha256_file(Path(__file__))


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, default=str) + "\n")


def write_csv(path, rows, columns):
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows, columns=columns).to_csv(path, index=False)


def _hash_array(array):
    return hashlib.sha256(np.ascontiguousarray(array).tobytes()).hexdigest()


def groups_from_arg(value):
    names = [x.strip() for x in value.split(",") if x.strip()]
    if not names or any(x not in ALIASES for x in names):
        raise ValueError("Only explicit G01,G03,G06 aliases are accepted before 39-group validation")
    return [(x, ALIASES[x]) for x in names]


def run_w0(groups, out):
    rows = []
    for alias, group in groups:
        for video in ("004", "005"):
            prepared = WS / "runs/m1_final_39/prepared" / f"{group}_{video}" / "PREPARED.json"
            if not prepared.exists():
                rows.append(dict(alias=alias, group_id=group, video_id=video,
                                 status="FAIL", reason="MISSING_PREPARED"))
                continue
            count = len(json.loads(prepared.read_text())["views"])
            offsets = ",".join(map(str, range(1, count)))
            packet = out / "w0_full_pairs" / group / video
            work = out / "work_full_pairs" / group / video
            command = [PYTHON, str(WS / "tools/run_w0_camera.py"), "--group", group,
                       "--video", video, "--stage", "all", "--output", str(packet),
                       "--workdir", str(work), "--prepared-root",
                       str(WS / "runs/m1_final_39/prepared"), "--clean-labels-root", str(CLEAN),
                       "--pair-offsets", offsets]
            log = out / "logs" / f"w0_full_pairs_{group}_{video}.log"
            log.parent.mkdir(parents=True, exist_ok=True)
            with log.open("w") as stream:
                result = subprocess.run(command, cwd=WS, stdout=stream,
                                        stderr=subprocess.STDOUT, check=False)
            rows.append(dict(alias=alias, group_id=group, video_id=video,
                             status="PASS" if result.returncode == 0 else "FAIL",
                             reason="" if result.returncode == 0 else f"EXIT_{result.returncode}",
                             command=command, log=str(log)))
    write_json(out / "w0/W0_RUN_COMMANDS.json", rows)
    failed = [row for row in rows if row["status"] != "PASS"]
    if failed:
        raise RuntimeError("W0_FAILED: " + json.dumps(failed, sort_keys=True))
    return rows


def packet_paths(groups, out):
    old = pd.read_csv(WS / "runs/m2c_corrective_completion/W0_79_VIDEO_RESULTS.csv")
    wanted = {g for _, g in groups}
    for row in old.itertuples():
        group, video = str(row.group_id), f"{int(row.video_id):03d}"
        packet = (out / "w0_full_pairs" / group / video if group in wanted
                  else Path(row.output_path))
        yield group, video, packet


def audit_registry(groups, out, run_id):
    rows, failures, packets = [], [], {}
    for group, video, path in packet_paths(groups, out):
        try:
            packet = verify_w0_packet(path, WS)
            if (packet["group"], packet["video"]) != (group, video):
                raise ValueError("PACKET_GROUP_VIDEO_MISMATCH")
            packets[(group, video)] = packet
            manifest = packet["manifest"]
            for view_id, entry in packet["views"].items():
                with np.load(entry["cache"]) as cache:
                    rgb, raw_mask, K = cache["RGB"], cache["labels"], cache["K"]
                clean_path = CLEAN / f"{group}_{video}" / (view_id + ".npz")
                clean_hash = sha256_file(clean_path) if clean_path.exists() else ""
                rows.append(dict(group_id=group, video_id=video, view_id=view_id,
                                 raw_frame=entry["raw_frame"], source_video_sha256=packet["source_video_sha256"],
                                 prepared_sha256=manifest["prepared"]["sha256"],
                                 cache_sha256=manifest["prepared"]["views_sha256"][view_id],
                                 track_sha256=manifest["tracks"]["sha256"],
                                 pairs_sha256=packet["pairs_sha256"],
                                 w0_sha256=manifest["artifacts"]["W0.npz"]["sha256"],
                                 RGB_sha256=_hash_array(rgb), raw_mask_sha256=_hash_array(raw_mask),
                                 clean_mask_file_sha256=clean_hash, K_sha256=_hash_array(K),
                                 c2w_sha256=_hash_array(packet["cameras"][view_id]),
                                 prepared_source=manifest["prepared"]["path"],
                                 track_source=manifest["tracks"]["path"],
                                 camera_source=str(path), run_id=run_id, code_version=CODE_VERSION))
        except Exception as exc:
            failures.append(dict(group_id=group, video_id=video, status="FAIL",
                                 reason=repr(exc), packet=str(path)))
    columns = ["group_id", "video_id", "view_id", "raw_frame", "source_video_sha256",
               "prepared_sha256", "cache_sha256", "track_sha256", "pairs_sha256", "w0_sha256",
               "RGB_sha256", "raw_mask_sha256", "clean_mask_file_sha256", "K_sha256",
               "c2w_sha256", "prepared_source", "track_source", "camera_source", "run_id", "code_version"]
    write_csv(out / "w0/FRAME_REGISTRY.csv", rows, columns)
    write_csv(out / "w0/W0_IDENTITY_FAILURES.csv", failures,
              ["group_id", "video_id", "status", "reason", "packet"])
    write_json(out / "w0/W0_IDENTITY_SUMMARY.json",
               dict(run_id=run_id, verified_videos=len(packets), expected_videos=79,
                    registry_rows=len(rows), expected_rows=766, failures=failures,
                    registry_sha256=sha256_file(out / "w0/FRAME_REGISTRY.csv")))
    return packets


def graph_support_counts(packet):
    if not packet["pairs_sha256"]:
        raise ValueError("MISSING_PAIRS_FOR_S2_GEOMETRY")
    path = Path(packet["manifest"]["tracks"]["path"]).with_name("pairs005.npz")
    if sha256_file(path) != packet["pairs_sha256"]:
        raise ValueError("PAIRS_CHANGED_AFTER_W0_VERIFICATION")
    with np.load(path) as pairs:
        counts = {view: set() for view in packet["views"]}
        ids = list(packet["views"])
        for k, (i, j) in enumerate(pairs["ij"]):
            if len(pairs[f"pair{k}"]) >= 12:
                counts[ids[int(i)]].add(ids[int(j)])
                counts[ids[int(j)]].add(ids[int(i)])
    return {key: len(value) for key, value in counts.items()}


def model_center(packet):
    points = np.asarray(packet["points"], float)
    if len(points) < 3:
        raise ValueError("INSUFFICIENT_W0_POINTS_FOR_MODEL_CENTER")
    # The historic INITIAL mesh is absent from the sparse new W0 view set.
    # This centre is an explicit input adapter, never represented as the old mesh.
    return points.mean(axis=0)


def historical_anchor_mapping(alias, video, pool, selection, inventory):
    anchors = selection[alias]["HERO_anchors"] if video == "004" else []
    old = {r["view"]: r for r in inventory if r["case"] == alias}
    result, used = [], set()
    for anchor in anchors:
        frame = old[anchor].get("raw_frame")
        if frame is None:
            continue
        candidates = [v for v in pool if v["id"] not in used]
        if not candidates:
            break
        closest = min(candidates, key=lambda v: (abs(v["raw_frame"] - frame), v["id"]))
        used.add(closest["id"])
        result.append(dict(historical_id=anchor, historical_raw_frame=frame,
                           selected_id=closest["id"], selected_raw_frame=closest["raw_frame"],
                           delta_raw_frame=abs(closest["raw_frame"] - frame),
                           exact=closest["raw_frame"] == frame,
                           status="EXACT" if closest["raw_frame"] == frame else "PROXY_NOT_HISTORICAL"))
    if not result and pool:
        closest = max(pool, key=lambda v: (v["sharpness"], v["id"]))
        result.append(dict(historical_id="", historical_raw_frame=None,
                           selected_id=closest["id"], selected_raw_frame=closest["raw_frame"],
                           delta_raw_frame=None, exact=False, status="NO_HISTORICAL_ANCHOR_PROXY"))
    return result


def build_views(packet, trajectory_class, graph_counts):
    group, video = packet["group"], packet["video"]
    admission = pd.read_csv(Path(packet["w0_path"]).parent / "admission.csv").set_index("view")
    center = model_center(packet)
    poses = list(packet["cameras"].values())
    blocks = direction_blocks(poses, center)
    views, features = [], {}
    sift = cv2.SIFT_create(nfeatures=6000, contrastThreshold=.01)
    for index, (view_id, entry) in enumerate(packet["views"].items()):
        with np.load(entry["cache"]) as cache:
            RGB, K = cache["RGB"], cache["K"]
        clean_path = CLEAN / f"{group}_{video}" / (view_id + ".npz")
        if not clean_path.is_file():
            raise ValueError("MISSING_CLEAN_MASK: " + str(clean_path))
        with np.load(clean_path) as clean:
            labels = clean["labels"]
        C = packet["cameras"][view_id]
        q = quality_features(dict(RGB=RGB, labels=labels, T=C, K=K), center)
        row = admission.loc[view_id].to_dict()
        if index == 0:
            row["rotation_to_previous_deg"] = 0.
            row["center_to_previous_mm"] = 0.
        s0, s1, s2 = admission_tiers(row, graph_counts[view_id], trajectory_class)
        views.append(dict(id=view_id, view=view_id, video=video, role="FIT", C=C, K=K,
                          RGB=RGB, labels=labels, raw_frame=int(entry["raw_frame"]),
                          direction_block=blocks[index], s0=s0, s1=s1, s2=s2,
                          legacy_status=row["admission_status"],
                          graph_support_count=graph_counts[view_id], **q))
        keypoints, descriptors = sift.detectAndCompute(
            cv2.cvtColor(RGB, cv2.COLOR_RGB2GRAY), None)
        features[view_id] = dict(des=descriptors if descriptors is not None
                                 else np.zeros((0, 128), np.float32),
                                 xy=np.asarray([x.pt for x in keypoints], np.float32),
                                 N=len(keypoints))
    return views, features, center


def select(groups, out, run_id):
    packets = audit_registry(groups, out, run_id)
    if len(packets) != 79:
        raise RuntimeError("GLOBAL_W0_IDENTITY_NOT_CLOSED")
    historical = json.loads(CONFIG_016.read_text())
    inventory = json.loads(INVENTORY_016.read_text())
    old_trajectory = pd.read_csv(WS / "runs/m2c_corrective_completion/CAMERA_ROLE_ADMISSION.csv")
    chosen_packets = {(group, video): packets[(group, video)]
                      for _, group in groups for video in ("004", "005")}
    admission_rows, target_rows, tuple_rows, anchor_rows = [], [], [], []
    for alias, group in groups:
        for video in ("004", "005"):
            packet = chosen_packets[(group, video)]
            prior = old_trajectory[(old_trajectory.group_id == group) &
                                   (old_trajectory.video_id == int(video))]
            classes = set(prior.trajectory_class)
            if len(classes) != 1:
                raise ValueError("TRAJECTORY_CLASS_IDENTITY: " + group + "/" + video)
            trajectory_class = classes.pop()
            adm = pd.read_csv(Path(packet["w0_path"]).parent / "admission.csv")
            if (adm.rotation_to_previous_deg.max() > 30 and
                    trajectory_class in ("T0_CONTINUOUS", "T1_SAMPLING_GAP")):
                trajectory_class = "T4_UNRESOLVED"
            graph = graph_support_counts(packet)
            views, features, center = build_views(packet, trajectory_class, graph)
            by_id = {v["id"]: v for v in views}
            for view in views:
                admission_rows.append(dict(alias=alias, group_id=group, video_id=video,
                                           view_id=view["id"], raw_frame=view["raw_frame"],
                                           legacy_status=view["legacy_status"],
                                           trajectory_class=trajectory_class,
                                           graph_support_count=view["graph_support_count"],
                                           s0_eligible=view["s0"], s1_eligible=view["s1"],
                                           s2_eligible=view["s2"],
                                           model_center_source="W0_SCENE_POINTS_MEAN",
                                           model_center_mm=json.dumps(center.tolist())))
            for arm in ("S0", "S1", "S2"):
                pool = [v for v in views if v[arm.lower()]]
                if not pool:
                    target_rows.append(dict(alias=alias, group_id=group, video_id=video,
                                            arm=arm, method="T10/T11", status="NO_ADMITTED_POOL",
                                            target_id="", rank=None))
                    continue
                mapping = historical_anchor_mapping(alias, video, pool, historical, inventory)
                for row in mapping:
                    anchor_rows.append(dict(alias=alias, group_id=group, video_id=video,
                                            arm=arm, **row))
                anchors = [row["selected_id"] for row in mapping]
                try:
                    selected = select_target_sets(pool, anchors, anchors)
                except Exception as exc:
                    target_rows.append(dict(alias=alias, group_id=group, video_id=video,
                                            arm=arm, method="T10/T11", status="SELECTION_FAIL",
                                            reason=repr(exc), target_id="", rank=None))
                    continue
                for method in ("T10", "T11"):
                    result = selected[method]
                    for rank, target_id in enumerate(result["ids"], 1):
                        target_rows.append(dict(alias=alias, group_id=group, video_id=video,
                                                arm=arm, method=method, status="SELECTED",
                                                target_id=target_id, rank=rank,
                                                anchor_exact=all(x["exact"] for x in mapping),
                                                model_center_source="W0_SCENE_POINTS_MEAN",
                                                direction_block=by_id[target_id]["direction_block"]))
                        target = by_id[target_id]
                        if len(pool) < 4:
                            tuple_rows.append(dict(alias=alias, group_id=group, video_id=video,
                                                   arm=arm, method=method, target_id=target_id,
                                                   support_ids="", ready=False,
                                                   reason="INSUFFICIENT_ADMITTED_POOL",
                                                   input_identity_verified=True))
                            continue
                        try:
                            result13 = select_views(
                                pool, strategy="hero_support", max_views=3, target=target,
                                features=lambda v: features[v["id"]], K=target["K"],
                                cache_root=out / "cache" / run_id /
                                packet["manifest"]["artifacts"]["W0.npz"]["sha256"][:16] /
                                group / video / arm)
                            support_ids = result13["ids"]
                            supports = [by_id[sid] for sid in support_ids]
                            okay, reason = validate_t13(target, supports,
                                                        result13["candidates"])
                            if not all(x[arm.lower()] for x in supports):
                                okay, reason = False, "SUPPORT_ADMISSION_FAIL"
                            candidate_receipt = json.dumps(result13["candidates"])
                        except Exception as exc:
                            support_ids, candidate_receipt = [], "[]"
                            okay, reason = False, repr(exc)
                        key = hashlib.sha256((group + "|" + video + "|" + target_id + "|" +
                                              ";".join(support_ids)).encode()).hexdigest()[:16]
                        selection_input_hash = ""
                        if okay:
                            frames = [dict(id=x["id"], RGB=x["RGB"], labels=x["labels"],
                                           K=x["K"], c2w_mm=x["C"])
                                      for x in [target] + supports]
                            selection_input_hash = tuple_receipt(True, frames, run_id,
                                                                 CODE_VERSION)["tuple_sha256"]
                        tuple_rows.append(dict(alias=alias, group_id=group, video_id=video,
                                               arm=arm, method=method, target_id=target_id,
                                               support_ids=";".join(support_ids),
                                               tuple_id=key, ready=bool(okay), reason=reason,
                                               input_identity_verified=True,
                                               candidate_evidence=candidate_receipt,
                                               anchor_exact=all(x["exact"] for x in mapping),
                                               w0_sha256=packet["manifest"]["artifacts"]["W0.npz"]["sha256"],
                                               pairs_sha256=packet["pairs_sha256"],
                                               selection_input_sha256=selection_input_hash,
                                               run_id=run_id, code_version=CODE_VERSION))
            print("SELECT", alias, video, "S0/S1/S2",
                  [sum(v[x] for v in views) for x in ("s0", "s1", "s2")], flush=True)
    write_csv(out / "admission/CAMERA_ADMISSION.csv", admission_rows,
              ["alias", "group_id", "video_id", "view_id", "raw_frame", "legacy_status",
               "trajectory_class", "graph_support_count", "s0_eligible", "s1_eligible",
               "s2_eligible", "model_center_source", "model_center_mm"])
    write_csv(out / "selection/ANCHOR_MAPPING.csv", anchor_rows,
              ["alias", "group_id", "video_id", "arm", "historical_id",
               "historical_raw_frame", "selected_id", "selected_raw_frame",
               "delta_raw_frame", "exact", "status"])
    write_csv(out / "selection/TARGET_SELECTION.csv", target_rows,
              ["alias", "group_id", "video_id", "arm", "method", "status",
               "target_id", "rank", "anchor_exact", "model_center_source", "direction_block", "reason"])
    tuple_columns = ["alias", "group_id", "video_id", "arm", "method", "target_id",
                     "support_ids", "tuple_id", "ready", "reason", "input_identity_verified",
                     "candidate_evidence", "anchor_exact", "w0_sha256", "pairs_sha256",
                     "selection_input_sha256", "run_id", "code_version"]
    write_csv(out / "selection/ALL_HERO_TUPLES.csv", tuple_rows, tuple_columns)
    seen = set(); unique = []
    for row in tuple_rows:
        if row["ready"] and row["tuple_id"] not in seen:
            seen.add(row["tuple_id"])
            unique.append(row)
    write_csv(out / "selection/UNIQUE_READY_TUPLES.csv", unique, tuple_columns)
    write_json(out / "selection/SELECTION_SUMMARY.json",
               dict(run_id=run_id, code_version=CODE_VERSION, target_rows=len(target_rows),
                    tuple_rows=len(tuple_rows), ready_rows=sum(x["ready"] for x in tuple_rows),
                    unique_ready_tuples=len(unique), rejected_rows=sum(not x["ready"] for x in tuple_rows),
                    historical_anchor_exact=bool(anchor_rows and all(x["exact"] for x in anchor_rows)),
                    model_center_source="W0_SCENE_POINTS_MEAN_NOT_HISTORICAL_INITIAL"))
    return unique


def read_frame(packet, view_id):
    entry = packet["views"][view_id]
    with np.load(entry["cache"]) as cache:
        RGB, K = cache["RGB"], np.asarray(cache["K"], float)
    clean_path = CLEAN / f'{packet["group"]}_{packet["video"]}' / (view_id + ".npz")
    with np.load(clean_path) as clean:
        labels = clean["labels"]
    return dict(id=view_id, RGB=RGB, labels=labels, K=K,
                c2w_mm=packet["cameras"][view_id])


def run_hero(groups, out, run_id):
    table = pd.read_csv(out / "selection/UNIQUE_READY_TUPLES.csv")
    if table.empty:
        write_csv(out / "hero/HERO_EXECUTION_RESULTS.csv", [],
                  ["group_id", "video_id", "target_id", "tuple_id", "status", "reason"])
        return []
    config = json.loads((WS / "mainline/configs/SITE.local.json").read_text())
    sys.path[:0] = [str(x) for x in config.get("readonly_dependency_paths", [])]
    from ring_first_3d.mainline.native.hero import load_official, infer
    from ring_first_3d.mainline.native.cleaning import classify_native
    from ring_first_3d.mainline.native.io import save_json
    lock = json.loads((WS / "src/ring_first_3d/mainline/native/upstream_source_lock.json").read_text())
    model, model_receipt = load_official(config["mvs_root"], config["checkpoint"],
                                         config["dino_root"], lock)
    save_json(out / "hero/MODEL_RECEIPT.json", model_receipt)
    rows = []
    for row in table.itertuples():
        group, video = str(row.group_id), f"{int(row.video_id):03d}"
        packet = verify_w0_packet(out / "w0_full_pairs" / group / video, WS)
        if row.input_identity_verified is not True:
            raise ValueError("IDENTITY_NOT_VERIFIED")
        if packet["manifest"]["artifacts"]["W0.npz"]["sha256"] != row.w0_sha256:
            raise ValueError("W0_CHANGED_AFTER_SELECTION")
        if packet["pairs_sha256"] != row.pairs_sha256:
            raise ValueError("PAIRS_CHANGED_AFTER_SELECTION")
        ids = [str(row.target_id)] + str(row.support_ids).split(";")
        frames = [read_frame(packet, cid) for cid in ids]
        if not all(np.array_equal(frame["c2w_mm"], packet["cameras"][frame["id"]])
                   for frame in frames):
            raise ValueError("HERO_CAMERA_BINDING")
        if not all(np.array_equal(frame["K"], packet["K"]) for frame in frames):
            raise ValueError("HERO_K_BINDING")
        candidates = json.loads(row.candidate_evidence)
        target = dict(id=ids[0], C=frames[0]["c2w_mm"])
        supports = [dict(id=f["id"], C=f["c2w_mm"]) for f in frames[1:]]
        okay, reason = validate_t13(target, supports, candidates)
        if not okay:
            raise ValueError("T13_GEOMETRY_CHANGED_AFTER_SELECTION: " + reason)
        receipt = tuple_receipt(True, frames, run_id, CODE_VERSION)
        if receipt["tuple_sha256"] != row.selection_input_sha256:
            raise ValueError("HERO_RGB_MASK_K_POSE_CHANGED_AFTER_SELECTION")
        receipt.update(group_id=group, video_id=video, tuple_id=row.tuple_id,
                       w0_sha256=row.w0_sha256,
                       pairs_sha256=row.pairs_sha256,
                       source_video_sha256=packet["source_video_sha256"],
                       prepared_sha256=packet["manifest"]["prepared"]["sha256"],
                       tracks_sha256=packet["manifest"]["tracks"]["sha256"],
                       clean_mask_files={cid: sha256_file(CLEAN / f"{group}_{video}" / (cid + ".npz"))
                                         for cid in ids})
        directory = out / "hero" / group / video / row.tuple_id
        write_json(directory / "INPUT_RECEIPT.json", receipt)
        try:
            inference = infer(model, frames, directory)
            cad = WS / "runs/m2e_historical_method_integration/cad" / (
                "R5.npz" if "R5" in group else "R10.npz")
            classify_native(directory, str(cad))
            status, failure = "PASS", ""
            print("HERO", group, video, ids[0], row.tuple_id, flush=True)
        except Exception as exc:
            inference = {}
            status, failure = "FAIL", repr(exc)
            print("HERO_FAIL", group, video, ids[0], failure, flush=True)
        rows.append(dict(group_id=group, video_id=video, alias=row.alias,
                         target_id=ids[0], support_ids=";".join(ids[1:]),
                         tuple_id=row.tuple_id, status=status, reason=failure,
                         output_dir=str(directory), run_id=run_id, code_version=CODE_VERSION,
                         w0_sha256=row.w0_sha256,
                         input_tuple_sha256=receipt["tuple_sha256"],
                         seconds=inference.get("seconds"), raw_faces=inference.get("raw_faces")))
        write_csv(out / "hero/HERO_EXECUTION_RESULTS.csv", rows,
                  ["group_id", "video_id", "alias", "target_id", "support_ids",
                   "tuple_id", "status", "reason", "output_dir", "run_id", "code_version",
                   "w0_sha256", "input_tuple_sha256", "seconds", "raw_faces"])
    return rows


def evaluate(groups, out, run_id):
    import open3d as o3d
    from ring_first_3d.mainline.native.geometry import native_rgb_labels

    sys.path.insert(0, str(WS / "src/ring_first_3d/mainline/lineage/experiments/TASK-VIEW-OBSERVABILITY-GT-EVAL-001/code"))
    sys.path.insert(0, str(WS / "src/ring_first_3d/mainline/frozen_registry"))
    import reprojection as rp

    scenes = {}
    def cad_scene(kind):
        if kind not in scenes:
            path = WS / "runs/m2e_historical_method_integration/cad" / (kind + ".npz")
            with np.load(path) as data:
                V, F = data["V"], data["F"]
            radius = 3.1 if kind == "R5" else 5.6
            rho = np.linalg.norm(V[:, :2], axis=1)
            if not np.isclose(np.median(rho), radius, atol=.01) or not np.isclose(
                    (V[:, 2].max() - V[:, 2].min()) / 2, .6, atol=.01):
                raise ValueError("CAD_RADIUS_OR_WIRE_MISMATCH")
            scene = o3d.t.geometry.RaycastingScene(nthreads=2)
            scene.add_triangles(o3d.core.Tensor(V.astype(np.float32)),
                                o3d.core.Tensor(F.astype(np.uint32)))
            scenes[kind] = (scene, sha256_file(path))
        return scenes[kind][0]

    rp.cad_scene = cad_scene
    hero = pd.read_csv(out / "hero/HERO_EXECUTION_RESULTS.csv")
    a2b_rows, cad_rows, failures = [], [], []
    for row in hero.itertuples():
        if row.status != "PASS":
            failures.append(dict(group_id=row.group_id, video_id=row.video_id,
                                 tuple_id=row.tuple_id, stage="HERO", reason=row.reason,
                                 run_id=run_id, code_version=CODE_VERSION))
            continue
        group, video = str(row.group_id), f"{int(row.video_id):03d}"
        packet = verify_w0_packet(out / "w0_full_pairs" / group / video, WS)
        directory = Path(row.output_dir)
        receipt = json.loads((directory / "INPUT_RECEIPT.json").read_text())
        ids = [str(row.target_id)] + str(row.support_ids).split(";")
        frames = [read_frame(packet, cid) for cid in ids]
        check = tuple_receipt(True, frames, run_id, CODE_VERSION)
        if check["tuple_sha256"] != receipt["tuple_sha256"]:
            raise ValueError("HERO_INPUT_CHANGED_BEFORE_EVALUATION")
        raw = np.load(directory / "RAW_NATIVE_MESH.npz")
        target = frames[0]
        Kn = np.asarray(np.load(directory / "HERO_native.npz")["K_index_native"], float)
        C = np.asarray(target["c2w_mm"], float)
        rgb_native, _, _ = native_rgb_labels(target["RGB"], target["labels"], target["K"])
        vertex_colors = rgb_native[raw["uv"][:, 1], raw["uv"][:, 0]] / 255.
        kind = "R5" if "R5" in group else "R10"
        for support in frames[1:]:
            key = (row.tuple_id, support["id"])
            try:
                pred = rp.render(raw["V"], raw["F"], vertex_colors,
                                 support["K"], support["c2w_mm"], np.eye(4), kind)
                metrics, _, _ = rp.evaluate(pred, support["RGB"], support["labels"])
                metrics.update(group_id=group, video_id=video, alias=row.alias,
                               tuple_id=row.tuple_id, target_id=ids[0], support_B_id=support["id"],
                               B_camera_sha256=_hash_array(support["c2w_mm"]),
                               B_K_sha256=_hash_array(support["K"]),
                               B_clean_mask_sha256=_hash_array(support["labels"]),
                               source_mesh_sha256=sha256_file(directory / "RAW_NATIVE_MESH.npz"),
                               unique_pair_id=hashlib.sha256(str(key).encode()).hexdigest()[:16],
                               target_B_camera_used=True, mask_protocol="CLEAN_B",
                               run_id=run_id, code_version=CODE_VERSION, status="PASS")
                a2b_rows.append(metrics)
            except Exception as exc:
                failures.append(dict(group_id=group, video_id=video, tuple_id=row.tuple_id,
                                     stage="A_TO_B", reason=repr(exc), support_B_id=support["id"],
                                     run_id=run_id, code_version=CODE_VERSION))
        try:
            native = np.load(directory / "HERO_native.npz")
            labels = np.load(directory / "NATIVE_RGB_LABELS.npz")["labels"]
            depth = np.asarray(native["depth_mm"], float)
            pose = np.asarray(native["reference_pose_mm"], float)
            if not np.array_equal(pose, C):
                raise ValueError("HERO_TARGET_POSE_NOT_W0")
            h, w = depth.shape
            yy, xx = np.mgrid[:h, :w]
            uv = np.c_[xx.ravel(), yy.ravel(), np.ones(h * w)]
            directions = (uv @ np.linalg.inv(Kn).T) @ pose[:3, :3].T
            rays = np.c_[np.broadcast_to(pose[:3, 3], directions.shape), directions]
            ring_depth = cad_scene(kind).cast_rays(o3d.core.Tensor(rays.astype(np.float32)))[
                "t_hit"].numpy().reshape(h, w)
            valid = np.isfinite(ring_depth) & (ring_depth > 0) & np.isfinite(depth) & (
                depth > 0) & (labels == 2)
            diff = depth[valid] - ring_depth[valid]
            cad_rows.append(dict(group_id=group, video_id=video, alias=row.alias,
                                 tuple_id=row.tuple_id, target_id=ids[0],
                                 ring_pixels=int((labels == 2).sum()), valid_ring_pixels=int(valid.sum()),
                                 ring_coverage=float(valid.sum() / max(1, (labels == 2).sum())),
                                 cad_hero_signed_median_mm=float(np.median(diff)) if len(diff) else np.nan,
                                 cad_hero_mae_mm=float(np.mean(np.abs(diff))) if len(diff) else np.nan,
                                 cad_hero_p95_abs_mm=float(np.quantile(np.abs(diff), .95)) if len(diff) else np.nan,
                                 cad_depth_median_mm=float(np.median(ring_depth[valid])) if len(diff) else np.nan,
                                 hero_depth_median_mm=float(np.median(depth[valid])) if len(diff) else np.nan,
                                 cad_sha256=scenes[kind][1], run_id=run_id,
                                 code_version=CODE_VERSION,
                                 status="PASS" if len(diff) else "NOT_EVALUABLE_NO_SHARED_RING_PIXELS"))
        except Exception as exc:
            failures.append(dict(group_id=group, video_id=video, tuple_id=row.tuple_id,
                                 stage="CAD_HERO", reason=repr(exc),
                                 run_id=run_id, code_version=CODE_VERSION))
        print("EVAL", group, video, row.tuple_id, flush=True)
    a2b_columns = ["group_id", "video_id", "alias", "tuple_id", "target_id", "support_B_id",
                   "target_Polyp_pixels", "prediction_valid_pixels", "common_pixels",
                   "target_coverage", "RGB_MAE_0_255", "predicted_outside_target_pixels",
                   "B_camera_sha256", "B_K_sha256", "B_clean_mask_sha256", "source_mesh_sha256",
                   "unique_pair_id", "target_B_camera_used", "mask_protocol", "run_id",
                   "code_version", "status"]
    write_csv(out / "evaluation/A_TO_B_METRICS.csv", a2b_rows, a2b_columns)
    write_csv(out / "evaluation/CAD_HERO_GEOMETRY.csv", cad_rows,
              ["group_id", "video_id", "alias", "tuple_id", "target_id", "ring_pixels",
               "valid_ring_pixels", "ring_coverage", "cad_hero_signed_median_mm",
               "cad_hero_mae_mm", "cad_hero_p95_abs_mm", "cad_depth_median_mm",
               "hero_depth_median_mm", "cad_sha256", "run_id", "code_version", "status"])
    write_csv(out / "evaluation/FAILURES.csv", failures,
              ["group_id", "video_id", "tuple_id", "stage", "reason", "support_B_id",
               "run_id", "code_version"])
    return a2b_rows, cad_rows, failures


def render_six_views(groups, out):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from ring_first_3d.mainline.native._mesh_renderer import actual_mesh_image

    table = pd.read_csv(out / "hero/HERO_EXECUTION_RESULTS.csv")
    table = table[table.status == "PASS"]
    images = []
    for alias, group in groups:
        for video in ("004", "005"):
            subset = table[(table.group_id == group) & (table.video_id == int(video))]
            if subset.empty:
                packet = verify_w0_packet(out / "w0_full_pairs" / group / video, WS)
                points = np.asarray(packet["points"], float)
                cad = np.load(WS / "runs/m2e_historical_method_integration/cad" /
                              ("R5.npz" if "R5" in group else "R10.npz"))
                ring = np.asarray(cad["V"], float)
                center = np.zeros(3)
                extent = max(10., float(np.quantile(np.linalg.norm(points, axis=1), .98)) * 1.15)
                cameras = list(packet["cameras"].values())
                camera_angles = []
                for C in (cameras[0], cameras[len(cameras) // 2], cameras[-1]):
                    direction = C[:3, 3] - center
                    direction /= np.linalg.norm(direction)
                    camera_angles.append((float(np.degrees(np.arcsin(direction[2]))),
                                          float(np.degrees(np.arctan2(direction[1], direction[0])))))
                angles = camera_angles + [(0., 0.), (0., 90.), (89.999, 0.)]
                fig = plt.figure(figsize=(18, 4.3))
                for i, (elevation, azimuth) in enumerate(angles):
                    axis = fig.add_subplot(1, 6, i + 1, projection="3d")
                    axis.scatter(points[:, 0], points[:, 1], points[:, 2], s=.5,
                                 c="#b66d6d", alpha=.35)
                    axis.scatter(ring[::10, 0], ring[::10, 1], ring[::10, 2],
                                 s=.5, c="black", alpha=.8)
                    axis.set(xlim=(-extent, extent), ylim=(-extent, extent),
                             zlim=(-extent, extent), xlabel="X mm", ylabel="Y mm", zlabel="Z mm")
                    axis.view_init(elev=elevation, azim=azimuth)
                    axis.set_title(("W0 camera " + str(i + 1)) if i < 3 else
                                   ("World X", "World Y", "World Z")[i - 3], fontsize=8)
                fig.suptitle(f"{alias} {video}: NO HERO SURFACE; W0 points + known Ring CAD; GT pose unknown")
                fig.tight_layout()
                path = out / "visualization/six_views" / f"{alias}_{video}_NO_HERO.png"
                path.parent.mkdir(parents=True, exist_ok=True)
                fig.savefig(path, dpi=110)
                plt.close(fig)
                images.append(str(path))
                continue
            packet = verify_w0_packet(out / "w0_full_pairs" / group / video, WS)
            meshes = [np.load(Path(row.output_dir) / "RAW_NATIVE_MESH.npz") for row in subset.itertuples()]
            all_vertices = np.concatenate([mesh["V"] for mesh in meshes], axis=0)
            kind = "R5" if "R5" in group else "R10"
            cad = np.load(WS / "runs/m2e_historical_method_integration/cad" / (kind + ".npz"))
            row = next(subset.itertuples()); mesh = meshes[0]
            center = np.asarray(mesh["V"]).mean(axis=0)
            ids = [str(row.target_id)] + str(row.support_ids).split(";")[:2]
            panels = []
            for cid in ids:
                direction = packet["cameras"][cid][:3, 3] - center
                direction /= np.linalg.norm(direction)
                elevation = np.degrees(np.arcsin(direction[2]))
                azimuth = np.degrees(np.arctan2(direction[1], direction[0]))
                panels.append((cid, elevation, azimuth))
            panels.extend([("World X", 0., 0.), ("World Y", 0., 90.), ("World Z", 89.999, 0.)])
            fig, axes = plt.subplots(1, 6, figsize=(18, 3.5))
            for axis, (name, elevation, azimuth) in zip(axes, panels):
                image, pixels_per_mm = actual_mesh_image(mesh["V"], mesh["F"], cad["V"], cad["F"],
                                             all_vertices, elevation, azimuth, "#d98989")
                axis.imshow(image); axis.set_title(name, fontsize=7); axis.axis("off")
                axis.plot([15, 15 + 5 * pixels_per_mm], [378, 378], color="black", lw=2)
                axis.text(15, 373, "~5 mm at view centre", fontsize=6)
            fig.suptitle(f"{alias} {video}: HERO surface + known Ring CAD; GT deployment pose unknown")
            fig.tight_layout()
            path = out / "visualization/six_views" / f"{alias}_{video}.png"
            path.parent.mkdir(parents=True, exist_ok=True)
            fig.savefig(path, dpi=110)
            plt.close(fig)
            images.append(str(path))
            palette = np.array([[.86, .36, .36], [.25, .55, .82], [.28, .72, .45],
                                [.86, .67, .15], [.55, .35, .75], [.75, .42, .55],
                                [.28, .65, .66], [.75, .55, .28]])
            combined_V, combined_F, colors = [], [], []
            offset = 0
            for i, item in enumerate(meshes):
                V, F = np.asarray(item["V"]), np.asarray(item["F"])
                combined_V.append(V); combined_F.append(F + offset)
                colors.append(np.tile(palette[i % len(palette)], (len(F), 1)))
                offset += len(V)
            V = np.concatenate(combined_V); F = np.concatenate(combined_F)
            face_colors = np.concatenate(colors)
            fig, axes = plt.subplots(1, 6, figsize=(18, 3.5))
            for axis, (name, elevation, azimuth) in zip(axes, panels):
                image, pixels_per_mm = actual_mesh_image(
                    V, F, cad["V"], cad["F"], V, elevation, azimuth,
                    "#d98989", face_colors=face_colors)
                axis.imshow(image); axis.set_title(name, fontsize=7); axis.axis("off")
                axis.plot([15, 15 + 5 * pixels_per_mm], [378, 378], color="black", lw=2)
                axis.text(15, 373, "~5 mm at view centre", fontsize=6)
            fig.suptitle(f"{alias} {video}: {len(meshes)} independent target surfaces; colour=target; GT pose unknown")
            fig.tight_layout()
            multi = out / "visualization/six_views" / f"{alias}_{video}_MULTISURFACE.png"
            fig.savefig(multi, dpi=110)
            plt.close(fig)
            images.append(str(multi))
    write_json(out / "visualization/SIX_VIEW_INDEX.json", images)
    return images


def diagnose_archived_g01(out, run_id):
    """Read-only attribution checks for the previous G01 depth outliers."""
    from ring_first_3d.mainline.native.geometry import resize_index_intrinsics
    old = WS / "runs/m2f1_w0_admission_restoration"
    execution = pd.read_csv(old / "hero/HERO_EXECUTION_RESULTS.csv")
    errors = pd.read_csv(old / "evaluation/CAD_HERO_NEW.csv")
    group = ALIASES["G01"]
    admission = pd.read_csv(out / "admission/CAMERA_ADMISSION.csv")
    eligibility = {(str(r.video_id).zfill(3), r.view_id): bool(r.s1_eligible)
                   for r in admission[admission.group_id == group].itertuples()}
    rows = []
    for row in execution[(execution.group_id == group) & (execution.status == "PASS")].itertuples():
        video = f"{int(row.video_id):03d}"
        packet = verify_w0_packet(out / "w0_full_pairs" / group / video, WS)
        native = np.load(Path(row.output_dir) / "HERO_native.npz")
        target = str(row.target_id)
        supports = str(row.support_ids).split(";")
        target_pose_diff = float(np.max(np.abs(native["reference_pose_mm"] -
                                           packet["cameras"][target])))
        support_pose_diff = max(float(np.max(np.abs(native["source_poses_mm"][i] -
                                                 packet["cameras"][cid])))
                                for i, cid in enumerate(supports))
        K_diff = float(np.max(np.abs(native["K_index_native"] -
                                     resize_index_intrinsics(packet["K"]))))
        error = errors[(errors.group_id == group) & (errors.video_id == int(video)) &
                       (errors.arm == row.arm) & (errors.target_id == target)]
        rows.append(dict(group_id=group, video_id=video, arm=row.arm,
                         target_id=target, support_ids=";".join(supports),
                         signed_median_mm=float(error.signed_median_mm.iloc[0]) if len(error) else np.nan,
                         target_pose_max_abs_diff_mm=target_pose_diff,
                         support_pose_max_abs_diff_mm=support_pose_diff,
                         K_native_max_abs_diff=K_diff,
                         depth_unit=str(native["unit"]),
                         depth_definition=str(native["depth_definition"]),
                         support_s1_eligible=sum(eligibility.get((video, cid), False)
                                                 for cid in supports),
                         all_four_s1_eligible=bool(eligibility.get((video, target), False) and
                                                   all(eligibility.get((video, cid), False)
                                                       for cid in supports)),
                         status="ARCHIVED_DIAGNOSTIC_NOT_NEW_ACCEPTED_HERO",
                         run_id=run_id, code_version=CODE_VERSION))
    write_csv(out / "evaluation/G01_ARCHIVED_DEPTH_DIAGNOSIS.csv", rows,
              ["group_id", "video_id", "arm", "target_id", "support_ids",
               "signed_median_mm", "target_pose_max_abs_diff_mm",
               "support_pose_max_abs_diff_mm", "K_native_max_abs_diff",
               "depth_unit", "depth_definition", "support_s1_eligible",
               "all_four_s1_eligible", "status", "run_id", "code_version"])
    write_json(out / "evaluation/G01_DEPTH_CONCLUSION.json",
               dict(run_id=run_id, code_version=CODE_VERSION, archived_rows=len(rows),
                    outlier_rows=sum(r["signed_median_mm"] < -10 for r in rows),
                    target_support_pose_binding_exact=all(r["target_pose_max_abs_diff_mm"] == 0 and
                                                          r["support_pose_max_abs_diff_mm"] == 0 for r in rows),
                    native_K_binding_exact=all(r["K_native_max_abs_diff"] == 0 for r in rows),
                    all_four_s1_eligible_rows=sum(r["all_four_s1_eligible"] for r in rows),
                    conclusion="Archived G01 outliers are target-dependent. Camera/K binding and units check; "
                               "the admitted T13 pool yields no new G01 tuple, so camera-versus-support "
                               "causality remains NOT_EVALUABLE. HERO depth is unchanged."))


def measure_multisurface_consistency(out, run_id):
    """World-space same-video surface disagreement; diagnostic, not GT accuracy."""
    from itertools import combinations
    from scipy.spatial import cKDTree

    hero = pd.read_csv(out / "hero/HERO_EXECUTION_RESULTS.csv")
    hero = hero[hero.status == "PASS"]
    rows = []
    for (group, video), subset in hero.groupby(["group_id", "video_id"]):
        samples = {}
        for row in subset.itertuples():
            with np.load(Path(row.output_dir) / "RAW_NATIVE_MESH.npz") as mesh:
                vertices = np.asarray(mesh["V"], float)
            if len(vertices) == 0:
                continue
            index = np.linspace(0, len(vertices) - 1, min(5000, len(vertices)), dtype=int)
            samples[row.tuple_id] = vertices[index]
        for (key_a, A), (key_b, B) in combinations(samples.items(), 2):
            da = cKDTree(B).query(A)[0]
            db = cKDTree(A).query(B)[0]
            distances = np.r_[da, db]
            rows.append(dict(group_id=group, video_id=f"{int(video):03d}",
                             tuple_A=key_a, tuple_B=key_b,
                             sample_points_A=len(A), sample_points_B=len(B),
                             centroid_distance_mm=float(np.linalg.norm(A.mean(axis=0) - B.mean(axis=0))),
                             symmetric_nn_median_mm=float(np.median(distances)),
                             symmetric_nn_p95_mm=float(np.quantile(distances, .95)),
                             interpretation="SAME_VIDEO_WORLD_SPACE_DIAGNOSTIC_NOT_GT",
                             run_id=run_id, code_version=CODE_VERSION))
    write_csv(out / "evaluation/MULTISURFACE_CONSISTENCY.csv", rows,
              ["group_id", "video_id", "tuple_A", "tuple_B", "sample_points_A",
               "sample_points_B", "centroid_distance_mm", "symmetric_nn_median_mm",
               "symmetric_nn_p95_mm", "interpretation", "run_id", "code_version"])
    return rows


def summarize(groups, out, run_id):
    admission = pd.read_csv(out / "admission/CAMERA_ADMISSION.csv")
    targets = pd.read_csv(out / "selection/TARGET_SELECTION.csv")
    tuples = pd.read_csv(out / "selection/UNIQUE_READY_TUPLES.csv")
    hero = pd.read_csv(out / "hero/HERO_EXECUTION_RESULTS.csv")
    a2b = pd.read_csv(out / "evaluation/A_TO_B_METRICS.csv")
    cad = pd.read_csv(out / "evaluation/CAD_HERO_GEOMETRY.csv")
    rows = []
    for alias, group in groups:
        A = admission[admission.group_id == group]
        T = targets[(targets.group_id == group) & (targets.status == "SELECTED")]
        U = tuples[tuples.group_id == group]
        H = hero[(hero.group_id == group) & (hero.status == "PASS")]
        B = a2b[a2b.group_id == group]
        C = cad[cad.group_id == group]
        rows.append(dict(alias=alias, group_id=group, videos=2,
                         w0_verified=2, s0_cameras=int(A.s0_eligible.sum()),
                         s1_cameras=int(A.s1_eligible.sum()), s2_cameras=int(A.s2_eligible.sum()),
                         T10_targets=int((T.method == "T10").sum()),
                         T11_targets=int((T.method == "T11").sum()),
                         unique_ready_tuples=len(U), hero_pass=len(H), a_to_b_pairs=len(B),
                         a_to_b_coverage_median=float(B.target_coverage.median()) if len(B) else np.nan,
                         a_to_b_rgb_mae_median=float(B.RGB_MAE_0_255.median()) if len(B) else np.nan,
                         cad_hero_signed_median_mm=float(C.cad_hero_signed_median_mm.median()) if len(C) else np.nan,
                         cad_hero_mae_median_mm=float(C.cad_hero_mae_mm.median()) if len(C) else np.nan,
                         status="CONDITIONAL_HERO_EXECUTED" if len(H) else
                         "NOT_EVALUABLE_NO_VALID_T13_TUPLE",
                         run_id=run_id, code_version=CODE_VERSION))
    write_csv(out / "evaluation/GROUP_STATUS.csv", rows,
              ["alias", "group_id", "videos", "w0_verified", "s0_cameras", "s1_cameras",
               "s2_cameras", "T10_targets", "T11_targets", "unique_ready_tuples",
               "hero_pass", "a_to_b_pairs", "a_to_b_coverage_median",
               "a_to_b_rgb_mae_median", "cad_hero_signed_median_mm",
               "cad_hero_mae_median_mm", "status", "run_id", "code_version"])
    write_json(out / "VALIDATION_39.json",
               dict(run_id=run_id, code_version=CODE_VERSION, three_groups_accepted=False,
                    historical_anchor_exact=False, all_39_attempted=False,
                    reason="G01/G06 have no legal T13 tuple under the recorded strict S0/S1/S2 policy; "
                           "historical exact anchors are absent from sparse W0 PREPARED input."))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=["w0", "select", "hero", "evaluate", "all"], default="all")
    parser.add_argument("--groups", default="G01,G03,G06")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--run-id", default="M2F2-20261124-001")
    args = parser.parse_args()
    groups = groups_from_arg(args.groups)
    out = args.output.resolve()
    run_id = args.run_id
    out.mkdir(parents=True, exist_ok=True)
    run_file = out / "RUN_ID.json"
    if args.stage in ("w0", "select", "all"):
        write_json(run_file, dict(run_id=run_id, code_version=CODE_VERSION,
                                  groups=groups, started_utc=datetime.now(timezone.utc).isoformat(),
                                  source_head=subprocess.check_output(
                                      ["git", "rev-parse", "HEAD"], cwd=WS, text=True).strip()))
    else:
        frozen = json.loads(run_file.read_text())
        if frozen["run_id"] != run_id or frozen["code_version"] != CODE_VERSION:
            raise ValueError("RUN_ID_OR_CODE_CHANGED_AFTER_SELECTION")
    if args.stage in ("w0", "all"):
        run_w0(groups, out)
    if args.stage in ("select", "all"):
        select(groups, out, run_id)
    if args.stage in ("hero", "all"):
        run_hero(groups, out, run_id)
    if args.stage in ("evaluate", "all"):
        evaluate(groups, out, run_id)
        render_six_views(groups, out)
        measure_multisurface_consistency(out, run_id)
        diagnose_archived_g01(out, run_id)
        summarize(groups, out, run_id)


if __name__ == "__main__":
    main()
