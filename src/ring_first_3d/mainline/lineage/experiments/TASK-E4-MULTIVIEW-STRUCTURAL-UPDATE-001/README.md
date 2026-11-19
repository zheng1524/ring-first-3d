# TASK-E4-MULTIVIEW-STRUCTURAL-UPDATE-001

Baseline: `418c96f87ba06458be5bb082813cad6e20127a19`.

Use the existing environment via `bash tools/research/run.sh`; no installation needed.

```bash
bash tools/research/run.sh tools/research/policy.py check --task experiments/TASK-E4-MULTIVIEW-STRUCTURAL-UPDATE-001/TASK.yaml
bash tools/research/run.sh tools/research/policy.py status --task experiments/TASK-E4-MULTIVIEW-STRUCTURAL-UPDATE-001/TASK.yaml --run-dir /home/liu/ring_first_3d_structural_update/experiments/TASK-E4-MULTIVIEW-STRUCTURAL-UPDATE-001/runs/STRUCTURAL_004
```

Final run `STRUCTURAL_004` completed all 13 stages and passed Runner acceptance;
186 regression tests passed. Scientific results and failures are in
`TECHNICAL_REPORT.md`, `RESULT_CARD.md`, and `FAILURE_REGISTRY.json`.
Open `visualization/index.html` as a plain local file list; PNGs are the primary
visual deliverables. Full GLBs retain source meshes and node identities.

For a genuinely new authorized execution use a new run directory and the same
`policy.py run --stage all` entry; never reuse a historical run with a different
freeze. The active contract explicitly restores valid noncap predictions from
this task's accepted `STRUCTURAL_003`; it does not rerun C0, relax any scientific
gate, or adopt capped outputs. Source and cache proofs are in
`inputs/CAP_REPAIR_CACHE.json`. Original attempts remain local and immutable.

`G4_C0_gate` requires genuine GT/heldout/geometry/accepted-growth validation before real execution. Failure stops the runner, retaining the measured C0 PNGs and every raw update. Do not skip/force this gate or tune parameters after reading GT. Real groups remain NOT_RUN/NaN if C0 fails. Engineering completion is separate from scientific success.

`code/body_update.py` is the only body updater and exact013 loader for both domains. Mature metric ray/triangle renderer, PyTorch3D sparse Laplacian, PyTorch Adam and exact historical GeometryGuard are reused. This task explicitly permits topology growth: it adds a minimal connected patch extrusion subject to multi-view evidence and quality checks. No E1/E2 initialization, DXY change, HERO training, camera optimization, per-view Body or global fusion.

Original assets and all previous experiment directories are read-only. Initial pre-execution drafts remain in inputs; none had scientific predictions. Active TASK.yaml, configuration and code hashes were frozen before execution.
