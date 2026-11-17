Run using existing environment and Policy Runner:

```bash
bash tools/research/run.sh tools/research/policy.py check --task experiments/TASK-E4-STRUCTURED-BODY-UPDATE-002/TASK.yaml
bash tools/research/run.sh tools/research/policy.py run --task experiments/TASK-E4-STRUCTURED-BODY-UPDATE-002/TASK.yaml --run-dir experiments/TASK-E4-STRUCTURED-BODY-UPDATE-002/runs/PILOT_002 --stage all
bash tools/research/run.sh tools/research/policy.py accept --task experiments/TASK-E4-STRUCTURED-BODY-UPDATE-002/TASK.yaml --run-dir experiments/TASK-E4-STRUCTURED-BODY-UPDATE-002/runs/PILOT_002
```
Immutable stages and hashes; no HERO stage. Inputs reference existing local frozen assets. Do not regenerate a historical TASK_FREEZE.

Completed canonical run: `runs/PILOT_002`, engineering-accepted, scientific conclusions awaiting human review. All 212 tests passed; 3 cases × 2 arms × 36 outer iterations completed. G01 improves mean surface error but worsens P95; G03 has no robust 3D gain; G05 stagnates. No Sweep was accepted. See `TECHNICAL_REPORT.md`, `RESULT_CARD.md`, `FAILURE_REGISTRY.json`, and `visualization/index.html`.

The root report and visualization are read-only post-acceptance review derivatives; the root `RUN_MANIFEST.json` explicitly points to the immutable canonical run. All final correspondences and compact intermediate meshes are in `review_assets/`; full step histories remain under `runs/`. `review_code/final_review.py` checks hashes, local HTML references, protected views, mesh validity, fixed Ring probes and budgets without changing predictions. `REVIEW_MANIFEST.json` binds the final review files to the accepted run.

PILOT_001 was stopped before GT following a deferred visualization syntax defect; all evidence remains. PILOT_002 repeats both arms from the unchanged exact013 initializer. Engineering repair and unchanged configuration proof: evidence/REPAIR_001.json and evidence/PILOT001_STOP.json.
