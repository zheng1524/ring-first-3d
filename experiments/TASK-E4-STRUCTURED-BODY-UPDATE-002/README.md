Run using existing environment and Policy Runner:

```bash
bash tools/research/run.sh tools/research/policy.py check --task experiments/TASK-E4-STRUCTURED-BODY-UPDATE-002/TASK.yaml
bash tools/research/run.sh tools/research/policy.py run --task experiments/TASK-E4-STRUCTURED-BODY-UPDATE-002/TASK.yaml --run-dir experiments/TASK-E4-STRUCTURED-BODY-UPDATE-002/runs/PILOT_001 --stage all
bash tools/research/run.sh tools/research/policy.py accept --task experiments/TASK-E4-STRUCTURED-BODY-UPDATE-002/TASK.yaml --run-dir experiments/TASK-E4-STRUCTURED-BODY-UPDATE-002/runs/PILOT_001
```
Immutable stages and hashes; no HERO stage. Inputs reference existing local frozen assets. Do not regenerate a historical TASK_FREEZE.
