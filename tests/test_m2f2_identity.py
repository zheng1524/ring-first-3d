"""M2F2 input gates: a receipt must identify the actual W0 inputs."""
import hashlib
import json

import numpy as np
import pytest

from ring_first_3d.mainline.input_identity import verify_w0_packet, tuple_receipt


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture
def packet(tmp_path):
    group, video = "sample_R10", "004"
    source = tmp_path / "source.mp4"
    source.write_bytes(b"real source identity")
    views = []
    for i in range(2):
        cache = tmp_path / f"frame{i}.npz"
        np.savez_compressed(cache, RGB=np.zeros((4, 4, 3), np.uint8),
                            labels=np.ones((4, 4), np.uint8), K=np.eye(3))
        views.append(dict(view=f"frame{i}", raw_frame=i, cache=str(cache)))
    prepared = tmp_path / "PREPARED.json"
    prepared.write_text(json.dumps(dict(views=views, ring_mm=10)))
    tracks = tmp_path / "tracks005.npz"
    np.savez_compressed(tracks, xy=np.zeros((2, 2, 2)))
    out = tmp_path / "W0"
    out.mkdir()
    c2w = np.tile(np.eye(4), (2, 1, 1))
    np.savez_compressed(out / "W0.npz", ids=["frame0", "frame1"], c2w=c2w,
                        points=np.array([[0., 0., 2.]]), point_track_ids=[1],
                        K=np.eye(3), ring_cad_mm=[5.6, .6])
    manifest = dict(group=group, video=video, ids=["frame0", "frame1"],
                    raw_frames=[0, 1], ring_cad_mm=[5.6, .6],
                    source_video=str(source), source_video_sha256=digest(source),
                    prepared=dict(path=str(prepared), sha256=digest(prepared),
                                  views_sha256={v["view"]: digest(tmp_path / v["cache"].split("/")[-1]) for v in views}),
                    tracks=dict(path=str(tracks), sha256=digest(tracks)),
                    artifacts={"W0.npz": dict(sha256=digest(out / "W0.npz"))})
    (out / "manifest.json").write_text(json.dumps(manifest))
    return out


def test_verified_packet_returns_exact_view_mapping(packet):
    result = verify_w0_packet(packet, packet.parent)
    assert result["verified"] is True
    assert list(result["views"]) == ["frame0", "frame1"]
    assert result["track_count"] == 2


def test_wrong_prepared_mapping_is_rejected(packet):
    p = packet / "manifest.json"
    m = json.loads(p.read_text())
    m["prepared"]["views_sha256"]["frame1"] = "0" * 64
    p.write_text(json.dumps(m))
    with pytest.raises(ValueError, match="CACHE_HASH"):
        verify_w0_packet(packet, packet.parent)


def test_track_identity_uses_manifest_source_not_work_a1(packet):
    p = packet / "manifest.json"
    m = json.loads(p.read_text())
    bad = packet.parent / "work_A1_tracks005.npz"
    np.savez_compressed(bad, xy=np.zeros((1, 2, 2)))
    m["tracks"]["path"] = str(bad)
    m["tracks"]["sha256"] = digest(bad)
    p.write_text(json.dumps(m))
    with pytest.raises(ValueError, match="TRACK_ID_RANGE"):
        verify_w0_packet(packet, packet.parent)


def test_tuple_gate_rejects_false_identity(packet):
    with pytest.raises(ValueError, match="IDENTITY_NOT_VERIFIED"):
        tuple_receipt(False, [], "run-1", "abc123")
