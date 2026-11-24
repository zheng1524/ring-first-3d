"""M2F6 behavior at the observation and rendering boundaries."""
from pathlib import Path

import numpy as np
import pandas as pd

from tools import m2f5_hero_eval


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
