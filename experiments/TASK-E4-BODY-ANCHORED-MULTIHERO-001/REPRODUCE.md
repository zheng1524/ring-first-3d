# Reproduction

Worktree: `/home/liu/ring_first_3d_e4_sdf_localization`.
Python: `/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python -B`.
Set `E4_RUN_DIR` to this task directory **before importing any reused module**. `code/common.py` points to the already installed PyTorch3D/Open3D environments; no downloads or network inference required.

Use an empty independent output directory for a new run; never overwrite this frozen run. Copy `code/`, `config/PROTOCOL.json`, `01_PROTOCOL.md` there. Input manifests reference local read-only upstream assets and are SHA indexed; they are intentionally not copied into Git. See `provenance/INPUT_SHA.json` and `REUSED018_CODE.json`.

```bash
export E4_RUN_DIR=/absolute/path/to/new-output
PY=/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python
$PY -B "$E4_RUN_DIR/code/prepare_multi.py"
$PY -B "$E4_RUN_DIR/code/synthetic_tests.py"
$PY -B "$E4_RUN_DIR/code/preflight_multi.py"
$PY -B "$E4_RUN_DIR/code/test_strong_gate.py"
$PY -B "$E4_RUN_DIR/code/run_all.py"
$PY -B "$E4_RUN_DIR/code/evaluate_multi.py"
$PY -B "$E4_RUN_DIR/code/check_real_gradients.py"
$PY -B "$E4_RUN_DIR/code/visualize_multi.py"
$PY -B "$E4_RUN_DIR/code/detail_figures_multi.py"
$PY -B "$E4_RUN_DIR/code/redraw_correspondence.py"
$PY -B "$E4_RUN_DIR/code/connected_branch_control.py"
$PY -B "$E4_RUN_DIR/code/report_multi.py"
$PY -B "$E4_RUN_DIR/code/post_metrics_multi.py"
```

`run_all.py` sequentially runs the four groups and freezes all16 finals before independent evaluation. Only one GPU training process runs at a time. `run_multi.py G03 B3` can run an isolated arm if its FINAL does not already exist. Body/Bias arrays, full source IDs, optimizer/RNG and every round are saved. `LATEST.pt` is an exact state archive; automatic recovery of the entire outer control flow is not implemented, so do not label a manually resumed run as seamless without restoring all recorded guard/source states.

The archived engineering attempts are **not formal results**: `runtime/ENGINEERING_PILOT_BEFORE_UNIT_FIX/`, `runtime/ANCHOR_SNAPSHOT_FIX_R1/`. Final R3 only reuses static B0; all B1/B2/B3 were rerun after the MATCHED-only strong-depth contract repair. Earlier R1/R2 outputs remain archived. No model or checkpoint is chosen from HOLDOUT or GT.

Inspect interactive layers by serving the task directory:

```bash
$PY -m http.server 8898 --bind 127.0.0.1 --directory "$E4_RUN_DIR"
```

Open `http://127.0.0.1:8898/figures/G03_viewer.html` (or G01/G05/G06). Viewer JS uses pinned Three.js0.169 CDN; GLB itself is local and can also be opened in another viewer. Native and derived source layers, Body rounds and inferred caps are independently switchable. Root .001 converts stored mm geometry to glTF metres; no new scale fit.

Large GLBs, detailed source arrays and optimizer states stay local; exact absolute paths and SHA are in `RESULT_INDEX.md` / `assets_index/`. Small reports, code, metrics and selected review figures are committed. Upload claims refer only to git-tracked files.

`connected_branch_control.py` is a post-freeze strengthening of the two-branch visibility test, not a new real-data arm. Browser validation in post_metrics is MISSING until an actual headless capture is made; it does not fabricate a PASS.
