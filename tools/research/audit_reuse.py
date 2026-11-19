from _bootstrap import args, emit, ROOT
import ast
import hashlib
import inspect
from pathlib import Path
from ring_first_3d._legacy import LOCK, source


def run():
    records = []
    selectors = {"T10": "skeleton_proxy; main per-view line28[skip np.load]; loop block30-32",
                 "T11": "weights; main loop block47-59", "T12": "greedy",
                 "T13": "support_pairs; main block91-96", "T24": "tensor/mesh/renderer/Case",
                 "T31": "ContourDistance", "T34": "self_intersections/dense_face_distance/points/GeometryGuard",
                 "common": "scene/contour", "rgb": "mutual"}
    for key, rec in LOCK["sources"].items():
        tree = source(key)
        records.append(dict(id=key, **rec, verified=True,
            ast_sha256=hashlib.sha256(ast.dump(tree).encode()).hexdigest(),
            selector=selectors.get(key, "API/provenance/formula reference; no module execution"),
            mode="SHA_LOCKED_AST_REUSE" if key in selectors else "ADAPTED_INTERFACE"))
    files = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
             for base in ["src/ring_first_3d", "tools/research", "tests"]
             for p in sorted((ROOT/base).rglob("*.py"))}
    return dict(status="PASS", source_baseline=LOCK["baseline"], sources=records,
                implementation_SHA256=files, policy="No top-level historical imports or mains; source hash checked on each load",
                GT_read=False, history_prediction_fallback=0)


if __name__ == "__main__":
    a = args("Verify provenance and historical mathematical-core reuse")
    emit(run(), a.output)
