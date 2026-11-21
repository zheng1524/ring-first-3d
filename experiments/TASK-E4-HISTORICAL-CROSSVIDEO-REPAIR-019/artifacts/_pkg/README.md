# CODE AUDIT — TASK-E4-HISTORICAL-CROSSVIDEO-019-REPAIR
Level 1: `PYTHONPATH=code python code/reproduce_offline.py` -> 5/18 (matches the historical output), R0/R3 -> 2/18.
Tests: `PYTHONPATH=code python -m unittest discover -s tests` -> 5/5 (2 skipped when the full replay tree is absent).
Blocked: gate020/objective020/optimize020 need pytorch3d (absent on this machine).
