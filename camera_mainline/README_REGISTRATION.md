# Cross-video registration stage (W0 native)

```bash
PYTHONPATH=src:. python tools/run_w0_registration.py --iters 80 --holdout
```

- Seed: the validated 1-DoF yaw solver (`camera_mainline/code/yaw_1dof.py`).
- Refinement: shared SE(3) with the historical 020 schedule (`camera_mainline/code/shared_se3.py`).
- Output: `experiments/TASK-E4-W0-REGISTRATION-STAGE-020/metrics/*.json` (research candidate only).
- Production cameras in `camera_mainline/G03/*` are never modified by this stage.
