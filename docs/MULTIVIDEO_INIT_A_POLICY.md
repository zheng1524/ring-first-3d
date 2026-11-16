# Historical Init-A multivideo / HERO profile

Schema 7 is additive. Its exact 015 code is stored under the task's `legacy015/` with the source commit and SHA table. `train_mesh.main`, renderer, RingAware, free vertex update, optimizer rollback and dense geometry guard are unchanged. A short entry wrapper only balances available depth observations by video; the historical silhouette video/direction/view weighting is already suitable.

TASK.yaml freezes the exact 013 initial meshes, A0 immutable finals, A1/A2 cohorts, 80/40/30 budgets, HOLDOUT, shared-005 FIT trigger, GT evaluator scope and HERO adapter parameters. A2S is a distinct arm; no automatic replacement of A2. GT source metadata is isolated in an evaluator-only asset. The pre-execution draft is preserved, with a revision record; no predictions existed during that change.

```bash
bash tools/research/run.sh tools/research/policy.py check --task experiments/TASK-E4-MULTIVIDEO-INIT-A-HERO-ALIGN-001/TASK.yaml
bash tools/research/run.sh tools/research/policy.py run --task experiments/TASK-E4-MULTIVIDEO-INIT-A-HERO-ALIGN-001/TASK.yaml --run-dir experiments/TASK-E4-MULTIVIDEO-INIT-A-HERO-ALIGN-001/runs/INIT_A_001 --stage all
```

The authorized order completes both parts for G01/G03/G05 before all-eleven expansion. The exact smoke predictions are copied into the all-case cohort, not refitted after GT evaluation. Parameters/inputs/code cannot drift across stages. Stages are atomic and append-only; original trainer checkpoints remain in each case directory. `status` and `accept` verify execution artifacts; scientific accuracy is independent.

Every shape is truly scale1 SE3-aligned using the historical 96-start/top8 evaluator. Only evaluation copies move. IoU uses a common per-case 3D sampling population across arms; strict solid validity, inferred base limitations and conditional occupancy diagnostics are distinct. Original world models exclusively feed real HERO registration. Full original HERO topology is preserved, and unavailable source-bound multimesh interfaces remain NOT_EVALUABLE without blocking other physical cases.
