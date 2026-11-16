# Code map

| file | SHA256 | purpose |
| --- | --- | --- |
| common.py | c3655801237ec59c232f9d87f99b1394efbc362c4649c0539bde55d86dcdb228 | """Task-local adapters; mature geometry is compiled unchanged from frozen ASTs.""" |
| contracts.py | 34e3dd759cd4618ac3b7102114c559c0ebc5027c31b68352cc99329ccc3e6cc2 | """Numerical source/geometry contracts before fitting and fairness after fitting.""" |
| evaluate.py | 61bfa908cbd2ba6deffecf30f19a0075275f24b29cec6e99598d0b3b10b15abc | """Post-freeze full-mask evaluation and observation-only identifiability.""" |
| fitting.py | 2e9af7fa5952b56e65c43376cbb6faf78e0b19dbaedeb8e366a0a598b91ca6d9 | """A1 nine-parameter TRF solver with exact 2D blocks, no HERO/depth block.""" |
| generate_dxy.py | 6073bd0050afdd092fa5a68d510fab72dca2b61bee9cfa8c301b766df43302b1 | """A1 official API/provenance adapter extended to the 75 current sources.""" |
| legacy_compare.py | 23ea08fddd27a97a4cd4e0b5a7863097582541f77cb3554f4751afd46dc2c6ab | """Post-freeze DT+AMS comparison ONLY; no output may enter E1/E2 fitting.""" |
| package_delivery.py | 0b8c952ab5abca53ba7805ae75d780ad49b2cf2452c2f31c280ea197fbb69806 | """Explicit curated Git delivery; no source images/video/depth/Jacobian cache.""" |
| phase0_audit.py | 2c4ecbedf78140618596311e6c89b74d357888204cc8f482c4b76158a644370a | #!/usr/bin/env python3 |
| prepare_inputs.py | dbae0e7d2d20eda1d63da865b7b8f36fee14f29febcb49b06878b43a79a01a0a | """Correct Phase 0: exact predecessor source/cache binding and native K transport.""" |
| qualify_views.py | 64368ae2725488ca76637bade0c98204396f71af03b786854d34ae5683331ca3 | """Freeze image-only greedy selection; audit CAD and cross-video lineage.""" |
| report.py | 76d9eb4b314b9ba2ce0a263f2cb8ab3a853d9d0d2f3c26214f29b7feff69ab50 | """Generate reports from frozen predictions and measured evaluation only.""" |
| run_dxy.py | 6fec1c15c6ff914a8dc1d5af09f0be3b8acf4985efeb3b3d03562343b6ecf1a2 | """CPU process batch, preserving each official call's stdout and record.""" |
| run_fits.py | 81ab788f2f4f43e47876dde3b9271013848a95c3ff3de429c0c2000236955a4f | from common import * |
| validate.py | f13e626e52d0c80b6a3eb645de42069395bd811f69604cd2ae98caf04b5f25b0 | """A1 validate-style integrity, exact source ASTs, fairness and failure retention.""" |
| visualize.py | 491ceffd43b4385973d34dfef84efa0bc31b85c3be4770f51c212115cb228519 | """Actual image overlays and six orthographic metric mesh views, no model tuning.""" |


phase0_audit.py为旧错误审计，已停用；正式入口prepare_inputs.py。历史resection.py/validate_pose.py未复制、未修改或运行。
