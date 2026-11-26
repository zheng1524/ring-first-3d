# Expansion Implementation Plan

Goal: Expand the approved comparison from two to ten videos and quantify pose disagreement.
Architecture: Reuse all existing solvers and fixed inputs, add cohort orchestration and post-solve metrics only. Existing pilot identities remain frozen.
Tech Stack: retained Python3.12, NumPy/SciPy, COLMAP4.2.1, native HERO.

- [ ] Audit10 completed HIST input receipts and shared resource state; snapshot original2 output hashes.
- [ ] Tests first: zero pose disagreement, known translation/rotation, missing cameras and no alignment, relative-pose invariance to common world transform, fractional baseline denominator and role identity.
- [ ] Add pose_metrics.py, read-only with respect to cameras; write per-case POSE_DIFFERENCES.json and ROLE_POSE_DIFFERENCES.json, raw frame IDs preserved.
- [ ] Extend run.py with ALL_CASES and --cohort expanded; retain pilot default. Freeze v2 protocol for new inputs; verified cached S reuse only when exact inputs/outputs unchanged. CPU stages run in fresh subprocesses per case to avoid module-global state crossing videos.
- [ ] Extend HERO authorization to explicit expanded total40 budget, preserve original8. Detect active A full-run scheduler before GPU work; freeze tuples/plan and record queue status while A has priority.
- [ ] Commit implementation after tests; run prepare, R/S/evaluate/pose for8 new videos; compute pose summaries for original2 without changing their frozen inputs/outputs.
- [ ] Produce expanded_report.py: all10-video coverage/query/pose/HERO status,5 physical-group summaries, small pose plots and real-data pages only where applicable. Explicit failures/NOT_EXECUTED remain in denominator.
- [ ] Review source/denominator/coordinate metrics; run remaining permitted HERO when available or retain concrete queue; verify original2 and A hashes, inference count, report links, and git remote SHA after push.
