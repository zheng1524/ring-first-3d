"""M2F6 behavior at the observation and rendering boundaries."""
from pathlib import Path
import json
import hashlib

import numpy as np
import pandas as pd

from tools import m2f5_hero_eval
from tools import run_w0_camera
from tools import m2f6_observations
from tools import m2f5_unified
import pytest


def _triangle(x):
    return np.array([[x, 0., 0.], [x, 1., 0.], [x, 0., 1.]], float)


def test_existing_mesh_render_uses_each_groups_cad_and_six_metric_views(tmp_path):
    source = tmp_path / "baseline"
    rows = []
    for group, kind in (("sample_R5", "R5"), ("sample_R10", "R10")):
        video = "004"
        packet = source / "w0" / f"{group}_{video}"
        packet.mkdir(parents=True)
        ids = np.array(["target", "support1", "support2", "support3"])
        poses = np.tile(np.eye(4), (4, 1, 1))
        poses[:, :3, 3] = [[0, -8, 2], [8, 0, 2], [0, 8, 2], [-8, 0, 2]]
        np.savez_compressed(packet / "W0.npz", ids=ids, c2w=poses)
        cad = source / "cad" / f"{kind}.npz"
        cad.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(cad, V=_triangle(-3 if kind == "R5" else 3), F=[[0, 1, 2]])
        for i in range(2):
            mesh = source / "hero" / group / video / f"target{i}"
            mesh.mkdir(parents=True)
            np.savez_compressed(mesh / "RAW_NATIVE_MESH.npz", V=_triangle(float(i)), F=[[0, 1, 2]])
            rows.append(dict(group_id=group, video_id=video, target_id="target",
                             support_ids="support1;support2;support3", output_dir=str(mesh),
                             status="PASS"))
    (source / "hero").mkdir(exist_ok=True)
    pd.DataFrame(rows).to_csv(source / "hero/HERO_EXECUTION_RESULTS.csv", index=False)

    output = tmp_path / "rendered"
    r5 = m2f5_hero_eval.render_existing_video(source, output, "sample_R5", "004")
    r10 = m2f5_hero_eval.render_existing_video(source, output, "sample_R10", "004")

    for result, kind in ((r5, "R5"), (r10, "R10")):
        assert result["cad_kind"] == kind
        assert result["cad_sha256"]
        assert result["view_labels"] == ["target", "support1", "support2", "World X", "World Y", "World Z"]
        assert result["scale_bar_mm"] == 5.0
        assert result["surface_count"] == 2
        assert Path(result["image"]).is_file()
    assert r5["cad_sha256"] != r10["cad_sha256"]


def test_reference_uses_current_ring_and_train_graph_not_frame_459():
    rings = [dict(candidates=[dict(loss=x)]) for x in (.5, .1, .3, .4)]
    edges = [dict(i=i, j=j, rows=np.zeros((count, 5))) for i, j, count in
             ((0, 1, 30), (0, 2, 25), (0, 3, 20), (1, 2, 12))]
    ref, evidence = run_w0_camera.select_reference(
        [100, 459, 700, 900], rings, edges, [40, 40, 40, 40])
    assert ref == 0
    assert evidence["selected_raw_frame"] == 100
    assert evidence["scores"][0]["graph_degree"] == 3
    assert evidence["scores"][1]["graph_degree"] == 2


def test_reference_fails_when_train_graph_is_disconnected():
    rings = [dict(candidates=[dict(loss=.2)]) for _ in range(3)]
    edges = [dict(i=0, j=1, rows=np.zeros((20, 5)))]
    with pytest.raises(RuntimeError, match="REFERENCE_GRAPH_DISCONNECTED"):
        run_w0_camera.select_reference([100, 459, 700], rings, edges, [30, 30, 30])


def test_reference_prioritizes_ring_fit_with_equally_connected_rgb_graph():
    rings = [dict(candidates=[dict(loss=x)]) for x in (.4, .1, .2)]
    edges = [dict(i=i, j=j, rows=np.zeros((count, 5))) for i, j, count in
             ((0, 1, 100), (0, 2, 100), (1, 2, 20))]
    ref, _ = run_w0_camera.select_reference([100, 459, 700], rings, edges, [40] * 3)
    assert ref == 1


def test_historical_initialization_versions_use_training_score_and_one_selection():
    calls = []
    def initialize(rings, tracks, edges, ref, version):
        calls.append(("initialize", version))
        return np.full((2, 4, 4), version, float), {"branches": np.array([version, 0])}
    def triangulate(poses, tracks):
        calls.append(("triangulate", int(poses[0, 0, 0])))
        return np.zeros((1, 3)), np.array([0]), [np.array([0, 1])]
    def ba(poses, points, tids, support, tracks, ref):
        version = int(poses[0, 0, 0]); calls.append(("BA", version))
        return poses, points, {"success": True, "nfev": 2}
    def score(ns, poses, tracks, ref, ba):
        version = int(poses[0, 0, 0]); calls.append(("version_score", version))
        return {"score": float(1 - version)}
    ns = dict(initialize=initialize, triangulate_training=triangulate, BA=ba)
    chosen, receipts = run_w0_camera.run_initialization_versions(
        ns, [], {}, [], 0, score)
    assert chosen["version"] == 1
    assert receipts["selected_version"] == 1
    assert json.dumps(receipts)
    assert [x for x in calls if x[0] == "initialize"] == [
        ("initialize", 0), ("initialize", 1)]
    assert [x for x in calls if x[0] == "version_score"] == [
        ("version_score", 0), ("version_score", 1)]


def test_2d_quality_uses_locked_pixel_terms_without_any_pose():
    rgb = np.zeros((80, 100, 3), np.uint8)
    rgb[20:60, 20:80] = 150
    labels = np.zeros((80, 100), np.uint8)
    labels[24:55, 30:70] = 1
    labels[55:65, 30:70] = 2
    result = m2f6_observations.quality_2d({"RGB": rgb, "labels": labels})
    assert set(result) == {"sharpness", "mask_complete_proxy",
                           "thin_structure_visibility_proxy", "Ring_free_fraction"}
    assert result["sharpness"] > 0


def test_2d_sampling_has_variable_size_and_connected_selected_graph():
    assert len(m2f6_observations.candidate_frames(1200)) > len(
        m2f6_observations.candidate_frames(400)) > 16
    candidates = [dict(frame=i * 20, quality=1.0 if i % 3 else 2.0,
                       proxy=[float(i // 3), 0.0, 0.0], ring_train_points=30)
                  for i in range(12)]
    edges = {(i, i + 1): 40 for i in range(11)}
    selected, receipt = m2f6_observations.select_observations(candidates, edges)
    assert 4 <= len(selected) < len(candidates)
    assert receipt["component_size"] == 12
    assert all("c2w" not in item and "direction" not in item for item in receipt["selected"])
    selected_indices = {item["index"] for item in receipt["selected"]}
    reachable = {next(iter(selected_indices))}
    while True:
        nxt = reachable | {j for (i, j), count in edges.items()
                           if count >= 12 and i in reachable and j in selected_indices}
        nxt |= {i for (i, j), count in edges.items()
                if count >= 12 and j in reachable and i in selected_indices}
        if nxt == reachable:
            break
        reachable = nxt
    assert reachable == selected_indices


def test_2d_selection_retains_real_overlap_without_temporal_overfilling():
    # Alternating 24/25-frame candidate intervals make two steps 49 frames.
    # The old 2*median(24) threshold incorrectly inserted redundant frames.
    candidates = [dict(frame=int(round(i * 24.5)), quality=2.0 if i % 3 == 0 else 1.0,
                       proxy=[0.0, 0.0], ring_train_points=30) for i in range(40)]
    edges = {(i, j): 40 for i in range(40) for j in range(i + 1, min(40, i + 4))}
    selected, receipt = m2f6_observations.select_observations(candidates, edges)
    assert 12 <= len(selected) <= 17
    ids = [row["index"] for row in receipt["selected"]]
    assert all((a, b) in edges for a, b in zip(ids, ids[1:]))
    assert max(np.diff([row["frame"] for row in selected])) > 49


def test_real_supplement_bridges_rgb_components_and_excludes_ring_poor_frames():
    candidates = [dict(view="bridge", frame=25, quality=4., proxy=[0., 0.], ring_train_points=50),
                  dict(view="ring_poor", frame=35, quality=10., proxy=[1., 0.], ring_train_points=8),
                  dict(view="one_side", frame=45, quality=5., proxy=[2., 0.], ring_train_points=50)]
    hits = {("bridge", "left"): 25, ("bridge", "right"): 22,
            ("ring_poor", "left"): 40, ("ring_poor", "right"): 40,
            ("one_side", "left"): 30, ("one_side", "right"): 0}
    added, receipt = m2f6_observations.choose_real_supplements(
        candidates, ["left", "right"], [["left"], ["right"]], hits,
        reason="RGB_GRAPH_DISCONNECTED", budget=4)
    assert [row["view"] for row in added] == ["bridge"]
    assert receipt["budget"] == 4
    assert receipt["reason"] == "RGB_GRAPH_DISCONNECTED"


def test_bounded_recovery_reruns_full_attempt_and_preserves_failure():
    calls = []
    def run(prepared, attempt):
        calls.append(("run_w0_and_select", attempt, tuple(prepared)))
        return {"recovery_reason": "NO_ACCEPT_CAMERAS", "status": "FAIL"}
    def add(prepared, reason, attempt):
        calls.append(("add_real_frame", attempt, reason))
        return prepared + [f"real_{attempt}"], {"added": [f"real_{attempt}"]}
    outcome = m2f6_observations.bounded_recovery(["raw0"], run, add, max_rounds=2)
    assert outcome["status"] == "RECOVERY_BUDGET_EXHAUSTED"
    assert [x[1] for x in calls if x[0] == "run_w0_and_select"] == [0, 1, 2]
    assert [x[1] for x in calls if x[0] == "add_real_frame"] == [1, 2]
    assert calls[-1][2] == ("raw0", "real_1", "real_2")


def test_recovery_reasons_use_existing_ring_camera_and_t13_evidence():
    classify = m2f6_observations.recovery_reason_from_evidence
    assert classify(error_type="REFERENCE_GRAPH_DISCONNECTED") == "RGB_GRAPH_DISCONNECTED"
    assert classify(error_type="INSUFFICIENT_RING_OBSERVATION") == "RING_OBSERVATION_INSUFFICIENT"
    assert classify(error_type="NO_BA_VERSION") == "INITIALIZATION_INSUFFICIENT"
    assert classify(quality={"n_accept": 3}, rows=[{"ready": True}, {"ready": False}]) == "SUPPORT_INSUFFICIENT"
    assert classify(quality={"n_accept": 0}, rows=[{"ready": True}]) is None
    assert classify(quality={"n_accept": 3}, rows=[{"ready": True}]) is None


def test_ring_center_is_fixed_world_cad_origin_and_scene_proxy_is_diagnostic():
    packet = {"points": np.array([[10., 0., 0.], [12., 2., 0.]])}
    assert np.array_equal(m2f5_unified.resolve_center(packet, "ring"), [0., 0., 0.])
    assert np.array_equal(m2f5_unified.resolve_center(packet, "scene"), [11., 1., 0.])
    with pytest.raises(ValueError, match="UNKNOWN_CENTER_MODE"):
        m2f5_unified.resolve_center(packet, "body")


def test_selection_views_use_current_clean_mask_rgb_k_and_w0_camera(tmp_path, monkeypatch):
    monkeypatch.setattr(m2f5_unified, "O", tmp_path)
    ids = ["current_a", "current_b"]
    packet = {"group": "sample_R10", "video": "004", "w0_path": str(tmp_path / "w0/W0.npz"),
              "points": np.array([[8., 1., 2.], [9., 1., 3.]]), "views": {}, "cameras": {}}
    (tmp_path / "w0").mkdir()
    K = np.array([[490., 0., 319.5], [0., 490., 179.5], [0., 0., 1.]])
    rows = []
    for i, name in enumerate(ids):
        rgb = np.zeros((360, 640, 3), np.uint8); rgb[:, :, 0] = i + 20
        raw = np.zeros((360, 640), np.uint8)
        clean = raw.copy(); clean[130:210, 260:370] = 1; clean[220:245, 280:350] = 2
        cache = tmp_path / f"{name}.npz"; np.savez_compressed(cache, RGB=rgb, labels=raw, K=K)
        cp = tmp_path / "clean_labels/sample_R10_004"; cp.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(cp / f"{name}.npz", labels=clean)
        C = np.eye(4); C[:3, 3] = [10 + i, 2 + i, 20]
        packet["cameras"][name] = C
        packet["views"][name] = {"cache": str(cache), "raw_frame": 100 + i}
        rows.append(dict(view=name, pose_valid=True, cad_valid=True,
                         admission_status="QUARANTINE" if i == 0 else "REJECT",
                         positive_depth=.99, ring_raw_mae=1., held_n=30,
                         held_median=1., held_p95=2., big_error_fraction=0.))
    pd.DataFrame(rows).to_csv(tmp_path / "w0/admission.csv", index=False)
    monkeypatch.setattr(m2f5_unified, "graph_counts", lambda packet: {x: 2 for x in ids})
    views, center = m2f5_unified.build_views(packet, "ring")
    assert np.array_equal(center, [0., 0., 0.])
    assert np.array_equal(views[0]["labels"], clean)
    assert np.array_equal(views[0]["RGB"], np.load(packet["views"][ids[0]]["cache"])["RGB"])
    assert np.array_equal(views[0]["K"], K)
    assert np.array_equal(views[0]["C"], packet["cameras"][ids[0]])
    assert views[0]["s2"] is True
    assert views[1]["s2"] is False


def test_hero_resolves_recovery_selected_w0_and_refuses_failed_route(tmp_path):
    group, video = "sample_R10", "004"
    selected = tmp_path / "recovery/round1/w0" / f"{group}_{video}"
    selected.mkdir(parents=True)
    (selected / "W0.npz").write_bytes(b"selected")
    receipt = tmp_path / "recovery" / f"{group}_{video}_RESULT.json"
    receipt.write_text(json.dumps({"status": "OBSERVATION_READY",
                                   "final_w0_path": str(selected)}))
    assert m2f5_hero_eval.final_packet_path(tmp_path, group, video) == selected
    receipt.write_text(json.dumps({"status": "RECOVERY_BUDGET_EXHAUSTED",
                                   "final_w0_path": str(selected)}))
    with pytest.raises(ValueError, match="OBSERVATION_NOT_READY"):
        m2f5_hero_eval.final_packet_path(tmp_path, group, video)


def test_exhausted_accept_count_uses_existing_s2_selection_without_rewriting_failure(tmp_path):
    group, video = "sample_R10", "004"
    selected = tmp_path / "recovery/round2/w0" / f"{group}_{video}"
    selected.mkdir(parents=True)
    (selected / "W0.npz").write_bytes(b"current W0")
    table = tmp_path / "recovery/round2/selection" / f"{group}_{video}.csv"
    table.parent.mkdir(parents=True)
    pd.DataFrame([dict(target_id="real_1", ready=True,
                       support_ids="real_2;real_3;real_4")]).to_csv(table, index=False)
    result = tmp_path / "recovery" / f"{group}_{video}_RESULT.json"
    status = dict(status="RECOVERY_BUDGET_EXHAUSTED", failure_reason="NO_ACCEPT_CAMERAS",
                  final_w0_path=str(selected), final_selection_path=str(table))
    result.write_text(json.dumps(status))
    assert m2f5_hero_eval.final_packet_path(tmp_path, group, video) == selected
    assert m2f5_hero_eval.final_selection_path(tmp_path, group, video) == table
    assert json.loads(result.read_text())["status"] == "RECOVERY_BUDGET_EXHAUSTED"
    pd.DataFrame([dict(target_id="real_1", ready=False,
                       support_ids="")]).to_csv(table, index=False)
    with pytest.raises(ValueError, match="S2_SELECTION_INCOMPLETE"):
        m2f5_hero_eval.final_packet_path(tmp_path, group, video)


def test_tuple_receipt_exists_before_actual_hero_call(tmp_path, monkeypatch):
    monkeypatch.setattr(m2f5_hero_eval, "O", tmp_path)
    frames = []
    for i in range(4):
        C = np.eye(4); C[0, 3] = i + 1
        frames.append(dict(id=f"real_{i}", RGB=np.full((2, 2, 3), i, np.uint8),
                           labels=np.full((2, 2), i % 3, np.uint8), K=np.eye(3),
                           c2w_mm=C))
    out = tmp_path / "hero" / "tuple"
    def fake_infer(model, actual_frames, actual_out):
        assert actual_frames is frames
        assert (actual_out / "TUPLE_INPUT_RECEIPT.json").is_file()
        saved = json.loads((actual_out / "TUPLE_INPUT_RECEIPT.json").read_text())
        assert saved["frames"][0]["Mask_sha256"] == m2f5_hero_eval.array_sha(frames[0]["labels"])
        return {"seconds": 0.1}
    monkeypatch.setattr(m2f5_hero_eval, "infer", fake_infer)
    result, receipt = m2f5_hero_eval.infer_with_receipt(
        object(), frames, out, "test-run", "test-code", "sample_R10", "004")
    assert result["seconds"] == .1
    assert receipt["input_identity_verified"] is True
    assert len((tmp_path / "RUN_TRACE/sample_R10_004.jsonl").read_text().splitlines()) == 1


def test_hero_current_clean_mask_identity_rejects_tampering(tmp_path, monkeypatch):
    monkeypatch.setattr(m2f5_hero_eval, "O", tmp_path)
    group, video = "sample_R10", "004"
    candidates = []
    views, cameras = {}, {}
    K = np.eye(3)
    for i in range(4):
        vid = f"real_{i}"
        rgb = np.full((2, 2, 3), i + 1, np.uint8)
        clean = np.full((2, 2), 1, np.uint8)
        cache = tmp_path / f"{vid}.npz"
        np.savez_compressed(cache, RGB=rgb, K=K, labels=np.zeros((2, 2), np.uint8))
        cp = tmp_path / "clean_labels" / f"{group}_{video}" / f"{vid}.npz"
        cp.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(cp, labels=clean)
        candidates.append(dict(view=vid, RGB_sha256=m2f5_hero_eval.array_sha(rgb),
                               clean_mask_sha256=m2f5_hero_eval.array_sha(clean),
                               K_sha256=m2f5_hero_eval.array_sha(K),
                               clean_labels_sha256=hashlib.sha256(cp.read_bytes()).hexdigest()))
        views[vid] = dict(cache=str(cache))
        cameras[vid] = np.eye(4)
    manifest = tmp_path / "CANDIDATE_MANIFEST.json"
    manifest.write_text(json.dumps(dict(candidates=candidates)))
    prepared = tmp_path / "PREPARED.json"
    prepared.write_text(json.dumps(dict(candidate_manifest=str(manifest),
                                        candidate_manifest_sha256=hashlib.sha256(manifest.read_bytes()).hexdigest())))
    packet = dict(group=group, video=video, views=views, cameras=cameras, K=K,
                  manifest=dict(prepared=dict(path=str(prepared))))
    actual = m2f5_hero_eval.verified_m2f6_frames(packet, "real_0",
                                                  ["real_1", "real_2", "real_3"], tmp_path)
    assert len(actual) == 4
    bad = tmp_path / "clean_labels" / f"{group}_{video}" / "real_2.npz"
    np.savez_compressed(bad, labels=np.full((2, 2), 2, np.uint8))
    with pytest.raises(ValueError, match="CLEAN_LABEL_FILE_HASH"):
        m2f5_hero_eval.verified_m2f6_frames(packet, "real_0",
                                             ["real_1", "real_2", "real_3"], tmp_path)
