# G01/G03 rejected-candidate growth recovery

Existing environment and Research Policy Runner only:

```bash
bash tools/research/run.sh tools/research/policy.py check --task experiments/TASK-E4-G01-G03-GROWTH-RECOVERY-001/protocols/ENGINEERING_REPAIR_001/TASK.yaml
bash tools/research/run.sh tools/research/policy.py run --task experiments/TASK-E4-G01-G03-GROWTH-RECOVERY-001/protocols/ENGINEERING_REPAIR_001/TASK.yaml --run-dir experiments/TASK-E4-G01-G03-GROWTH-RECOVERY-001/runs/LOCAL_002 --stage all
bash tools/research/run.sh tools/research/policy.py accept --task experiments/TASK-E4-G01-G03-GROWTH-RECOVERY-001/protocols/ENGINEERING_REPAIR_001/TASK.yaml --run-dir experiments/TASK-E4-G01-G03-GROWTH-RECOVERY-001/runs/LOCAL_002
```

Only G01/G03, saved iteration24 preferred candidates; no candidate search or Body retraining. Adam is a fresh `REJECTED_CANDIDATE_WARM_START`. Frozen STEP024 Body and cameras; only the recovered cubic spline and elliptical radii optimize. Explicit embedded overlap is resolved by exact Boolean union; complete final self-intersection/topology and fresh 2D/Ring gates remain enforced. Failed growth outputs NaN and retains the actual last attempt.

`TASK.md` contains the complete user instruction; `TASK.yaml` and `TASK_FREEZE.json` bind parameters, assets and code. GT is read only after both prediction freezes. Exposed stalk length starts at the first exit of the cubic centerline from the original Body, and excludes its embedded arc. Final reports and all actual PNGs are available from `visualization/index.html` after completion.

Original root TASK.yaml/TASK_FREEZE.json and LOCAL_001 are preserved verbatim. The canonical executable protocol is protocols/ENGINEERING_REPAIR_001. It rejects empty Boolean candidates through the original backtracking budget, without changing scientific parameters. G03 is resumed from its SHA-bound completed same-task stage; it is not optimized twice. G01 replays only its engineering-invalid local stage.
