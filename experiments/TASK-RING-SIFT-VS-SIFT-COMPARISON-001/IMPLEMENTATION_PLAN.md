# Comparison Implementation Plan

Goal: Run the authorized two-video feasibility comparison with honest denominators.
Architecture: Reuse frozen HIST kernels and snapshots; add only COLMAP interchange and task-specific evaluation adapters. Keep each arm isolated.
Tech stack: existing Python 3.12 environment, NumPy/SciPy/OpenCV, pycolmap 4.2.1, native HERO, matplotlib.

- [x] Freeze input hashes, train/validation/test IDs, fixed query support IDs and four-frame tuples in `runs/ring_sift_comparison_001/<case>/common` before camera solving.
- [x] Add `tests/test_sift_comparison.py`: split disjointness; query cannot enter triangulation; missing query/support stays counted; reflection-free positive Sim(3); imported pixel-center projection equivalence; exact original match-edge identity.
- [x] Add `src/ring_first_3d/sift_comparison/colmap_arm.py`: public `solve(common_dir, output_dir)` reads only common tracks, pairs, ledger, split. Use official database verification and mapper, no R references. Export cameras.npz (c2w, K, component, points, point_track_ids) and receipt.json, preserve all model outputs.
- [x] Add `core.py` for fixed splits/tuples/query manifests, call existing triangle/project, and normalize with one global training-point similarity.
- [x] Add `run.py` and `tools/ring_sift_comparison.py`: snapshot/hash, invoke locked R kernel, independent S, validation/test summaries, freeze HERO inputs, native inference under shared lock, raw mesh and directed overlap evaluation.
- [x] Add `report.py` for PILOT_RESULTS.csv and two Chinese comparison pages from real RGB/projections/raw meshes; write TECHNICAL_REPORT.md with failure/NOT_EXECUTED distinctions.
- [x] Run `PYTHONPATH=src /home/liu/polyp_research/ring_anchor_3d/.venv/bin/python -m unittest discover -s tests -p 'test_sift_comparison*.py' -v`; run existing V6 policy regression; invoke `tools/ring_sift_comparison.py --stage prepare`, then camera/evaluate/hero/report in that order. Record actual commands/versions/hashes.
- [x] Review scientific denominators, test isolation, camera conventions, inference count and A immutability. Explicit git add, commit and incremental push; verify remote branch SHA before claiming synchronization.

Execution evidence: 15 comparison checks + 7 baseline checks pass; 2 videos, 8/8 native inference successes. Review corrections and initial source hashes retained in evidence. Paired perturbation stability deliberately NOT_EXECUTED. Final remote SHA receipt follows the evidence push.
