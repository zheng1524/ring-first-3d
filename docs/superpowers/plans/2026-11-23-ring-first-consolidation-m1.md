# Ring-First 3D — M1 Freeze + Cross-Video Correctness Consolidation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the M1 provenance/contract gaps and apply only correctness fixes to the 028 cross-video candidate, then run the four-group matrix and freeze M1 only if every acceptance test passes and the human approves.

**Architecture:** Keep `tools/run_w0_camera.py` as the single M1 entry and `u028c.py` as the single cross-video candidate entry. Add boundary-only glue: admission filtering, pinned module paths, config wiring, explicit statuses, identity-keyed triangulation, and self-contained manifests. No Ring/BA/H objective changes.

**Tech Stack:** Python 3.12 (venv `/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python`), NumPy, SciPy, OpenCV, PyYAML, PyTorch/PyTorch3D/Open3D only through the existing Ring route, `unittest`.

**Approval precondition:** Tasks 1-10 are blocked until `docs/audit/ROUTE_COMPOSITION_PLAN.md` items A1-A7 are approved. Task 10 additionally requires a separate explicit freeze approval.

**Git note:** `.gitignore` line 9 ignores `/docs/`. New audit/registry/plan files are therefore untracked by default. Do not weaken `.gitignore`; commit them explicitly with `git add -f docs/...` only after approval.

---

## File structure

| File | Responsibility |
|---|---|
| `tools/run_w0_camera.py` | M1 single entry; add `--workdir`, prepared provenance, observation export, self-contained manifest |
| `tools/check_routes_v2.py` | new validator for `docs/registry/routes.yaml` (schema, IDs, statuses, source hashes) |
| `tests/test_w0_manifest_closure.py` | M1 manifest/export closure + G03 regression |
| `tests/test_routes_registry.py` | registry validator positive/negative cases |
| `tests/test_028_admission_gate.py` | admission helper + real G01/G05/G06 gate cases |
| `tests/test_028_config_status.py` | config wiring + geometry status matrix |
| `tests/test_028_triangulation.py` | finite/failure handling and identity-keyed output |
| `tests/test_028_ring_residual.py` | single-source Ring residual + consistency diagnostic |
| `tests/test_cross_group_matrix.py` | four-group matrix contract |
| `experiments/TASK-E4-W0-CROSSVIDEO-028-CORRECTIVE-FINAL/core/u028c.py` | candidate boundary fixes only |
| `experiments/TASK-E4-W0-CROSSVIDEO-028-CORRECTIVE-FINAL/core/ba_core_r4.py` | no objective change; pass `rgb_mode` through only |
| `experiments/TASK-E4-W0-CROSSVIDEO-027-CORRECTIVE-R6/core/fixed_track_tri.py` | **new pinned copy** in 028 core, failure handling; do not edit the historical copy |
| `docs/registry/modules.yaml` | frozen M1 module record (Task 10) |
| `docs/registry/pipeline.yaml` | formal/planned stage status (Task 10) |

**Important:** `fixed_track_tri.py` is historical 019 code. Do not edit `027-CORRECTIVE-R6/core/fixed_track_tri.py`. Copy it to `028-FINAL/core/fixed_track_tri_v2.py`, change only failure handling, and record the diff. The same rule applies to `features019.py`: pin a copy, do not edit the historical source.

---

## Task 1: Make the W0 export self-contained and close its manifest

**Files:**
- Modify: `tools/run_w0_camera.py`
- Test: `tests/test_w0_manifest_closure.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_w0_manifest_closure.py
import json, shutil, subprocess, sys, unittest
from pathlib import Path
import numpy as np

WS = Path('/home/liu/ring_first_3d_workspace')
PY = '/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python'


class W0ManifestClosure(unittest.TestCase):
    def test_manifest_has_prepared_tracks_and_observations(self):
        tmp = Path('/tmp/rf3d_w0_closure')
        shutil.rmtree(tmp, ignore_errors=True); tmp.mkdir(parents=True)
        out, work = tmp/'out', tmp/'work'
        cmd = [PY, str(WS/'tools/run_w0_camera.py'), '--group', 'G03', '--video', '005',
               '--stage', 'all', '--output', str(out), '--workdir', str(work)]
        r = subprocess.run(cmd, cwd=WS, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr[-2000:])
        man = json.loads((out/'manifest.json').read_text())
        self.assertIsInstance(man['prepared'], dict)
        self.assertEqual(len(man['prepared']['sha256']), 64)
        self.assertGreater(len(man['prepared']['views_sha256']), 0)
        self.assertTrue((out/'observations'/'tracks005.npz').exists())
        self.assertTrue((out/'observations'/'pairs005.npz').exists())
        self.assertTrue(man['tracks']['path'].startswith(str(out)))
        self.assertGreater(len(man['tracks']['observations']), 0)
        for rel in man['tracks']['observations']:
            self.assertTrue((out/'observations'/rel).exists(), rel)


if __name__ == '__main__':
    unittest.main(verbosity=2)
```

- [ ] **Step 2: Run the test and confirm it fails**

```bash
cd /home/liu/ring_first_3d_workspace
/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python tests/test_w0_manifest_closure.py -v
```

Expected: FAIL with `unrecognized arguments: --workdir` or `KeyError: 'prepared'`.

- [ ] **Step 3: Add prepared provenance to `load_prepared`**

```python
def load_prepared(g, v):
    p = T006/'runs/prepared'/f'{g}_{v}'/'PREPARED.json'
    if not p.exists():
        raise SystemExit(f'MISSING_PREPARED {p}')
    meta = json.loads(p.read_text())
    meta['views'] = sorted(meta['views'], key=lambda q: (q['raw_frame'], q['view']))
    meta['prepared_path'] = str(p)
    meta['prepared_sha256'] = sha(p)
    meta['views_sha256'] = {q['view']: sha(Path(q['cache'])) for q in meta['views']}
    return meta
```

- [ ] **Step 4: Add `--workdir` and observation export**

```python
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--group', required=True); ap.add_argument('--video', required=True)
    ap.add_argument('--stage', default='all', choices=['all', 'b0', 'w0', 'evaluate', 'admit', 'export'])
    ap.add_argument('--output', default=None); ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--resume', action='store_true')
    ap.add_argument('--workdir', default=None)
    a = ap.parse_args()
    g, v = a.group, a.video.zfill(3)
    out = Path(a.output) if a.output else WS/'camera_mainline'/g/f'video{v}'
    run = (Path(a.workdir) if a.workdir
           else WS/'experiments/TASK-E4-W0-MAINLINE-CONSOLIDATION-015'/'runs'/f'{g}_{v}')
    meta = load_prepared(g, v)


def export_observations(run, out):
    (out/'observations').mkdir(parents=True, exist_ok=True)
    names = []
    for p in sorted((run/'observations').glob('*')):
        if p.is_file():
            (out/'observations'/p.name).write_bytes(p.read_bytes())
            names.append(p.name)
    return names
```

- [ ] **Step 5: Replace the manifest block with the closed contract**

```python
    exported = export_observations(run, out)
    man = dict(
        group=g, video=v,
        source_video=meta.get('video_path'),
        source_video_sha256=meta.get('video_sha256'),
        prepared=dict(path=meta['prepared_path'], sha256=meta['prepared_sha256'],
                      views_sha256=meta['views_sha256']),
        ids=[x['meta']['id'] for x in ordered], raw_frames=rf, ref=ref,
        tracks=dict(path=str(out/'observations'/'tracks005.npz'),
                    sha256=sha(out/'observations'/'tracks005.npz'),
                    observations=exported),
        gate='camera_mainline/CAMERA_ADMISSION_POLICY.yaml',
        code=dict(entry=sha(Path(__file__)),
                  gate=sha(WS/'camera_mainline/code/camera_admission.py'),
                  held_eval=sha(WS/'camera_mainline/code/evaluate_held_geometry.py')),
        stages=a.stage)
    (out/'manifest.json').write_text(json.dumps(man, indent=1))
```

- [ ] **Step 6: Run the test and the G03 regression**

```bash
cd /home/liu/ring_first_3d_workspace
/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python tests/test_w0_manifest_closure.py -v
python3 - <<'EOF'
import json
q=json.load(open('/tmp/rf3d_w0_closure/out/manifest.json'))
print('prepared',q['prepared']['sha256'][:12],'tracks',q['tracks']['sha256'][:12],'obs',len(q['tracks']['observations']))
EOF
python3 - <<'EOF'
import json
q=json.load(open('/home/liu/ring_first_3d_workspace/camera_mainline/G03/video005/quality_summary.json'))
print(q['n_accepted'], q['ring_raw_mae_mean'], q['held_median_median'], q['held_p95_median'])
EOF
```

Expected: test PASS; manifest has prepared/tracks/observations; the existing G03/005 quality summary still shows 16, 0.828765110526794, 0.9801671148427384, 3.209368827748597.

- [ ] **Step 7: Commit**

```bash
git add tools/run_w0_camera.py tests/test_w0_manifest_closure.py
git commit -m "M1: self-contained W0 export (prepared hash, tracks/observations in output, --workdir)"
```

---

## Task 2: Validate the consolidated route registry

**Files:**
- Create: `tools/check_routes_v2.py`
- Test: `tests/test_routes_registry.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_routes_registry.py
import subprocess, tempfile, unittest, yaml
from pathlib import Path
WS = Path('/home/liu/ring_first_3d_workspace')
PY = '/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python'
TOOL = WS/'tools/check_routes_v2.py'


class RoutesRegistry(unittest.TestCase):
    def test_current_registry_passes(self):
        r = subprocess.run([PY, str(TOOL), str(WS/'docs/registry/routes.yaml')],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_bad_status_and_duplicate_fail(self):
        src = yaml.safe_load((WS/'docs/registry/routes.yaml').read_text())
        src['routes'][0]['status'] = 'bogus'
        src['routes'].append(dict(src['routes'][1]))
        p = Path(tempfile.mkdtemp())/'routes.yaml'; p.write_text(yaml.safe_dump(src))
        r = subprocess.run([PY, str(TOOL), str(p)], capture_output=True, text=True)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn('bad status', r.stdout + r.stderr)
        self.assertIn('duplicate route_id', r.stdout + r.stderr)


if __name__ == '__main__':
    unittest.main(verbosity=2)
```

- [ ] **Step 2: Run the test and confirm it fails**

```bash
cd /home/liu/ring_first_3d_workspace
/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python tests/test_routes_registry.py -v
```

Expected: FAIL because `tools/check_routes_v2.py` does not exist.

- [ ] **Step 3: Write the validator**

```python
#!/usr/bin/env python3
"""Validate docs/registry/routes.yaml: schema, unique IDs, statuses, source hashes."""
import hashlib, sys
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
STATUS = {'exploring', 'candidate', 'confirmed', 'frozen', 'rejected', 'deprecated'}
REQUIRED = ('route_id', 'version', 'component', 'status', 'entrypoint',
            'inputs', 'outputs', 'reuse_policy', 'smoke_test')


def sha256(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main(path):
    d = yaml.safe_load(Path(path).read_text())
    errs, seen = [], set()
    for r in d.get('routes', []):
        for k in REQUIRED:
            if k not in r or r[k] in (None, ''):
                errs.append(f"{r.get('route_id','?')}: missing {k}")
        key = f"{r.get('route_id')}@{r.get('version')}"
        if key in seen:
            errs.append(f"duplicate route_id {key}")
        seen.add(key)
        if r.get('status') not in STATUS:
            errs.append(f"{key}: bad status {r.get('status')}")
        if r.get('status') == 'frozen' and not r.get('human_approval'):
            errs.append(f"{key}: frozen without human_approval")
        src = r.get('source') or {}
        if isinstance(src.get('path'), str) and isinstance(src.get('sha256'), str):
            p = ROOT/src['path']
            if not p.exists():
                errs.append(f"{key}: source missing {p}")
            elif sha256(p) != src['sha256']:
                errs.append(f"{key}: source hash mismatch {p}")
    print({'routes': len(d.get('routes', [])), 'errors': errs})
    return 1 if errs else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else 'docs/registry/routes.yaml'))
```

- [ ] **Step 4: Run the test and confirm it passes**

```bash
cd /home/liu/ring_first_3d_workspace
/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python tests/test_routes_registry.py -v
```

Expected: 2 PASS.

- [ ] **Step 5: Commit**

```bash
git add tools/check_routes_v2.py tests/test_routes_registry.py
git commit -m "registry: validate docs/registry/routes.yaml (schema, IDs, statuses, source hashes)"
```

---

## Task 3: Enforce the frozen camera admission gate in the cross-video candidate

**Files:**
- Modify: `experiments/TASK-E4-W0-CROSSVIDEO-028-CORRECTIVE-FINAL/core/u028c.py`
- Test: `tests/test_028_admission_gate.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_028_admission_gate.py
import sys, unittest
from pathlib import Path
import numpy as np
WS = Path('/home/liu/ring_first_3d_workspace')
F = WS/'experiments/TASK-E4-W0-CROSSVIDEO-028-CORRECTIVE-FINAL'
sys.path.insert(0, str(F/'core'))
sys.path.insert(0, str(WS/'experiments/TASK-E4-W0-CROSSVIDEO-027-CORRECTIVE-R6/core'))
sys.path.insert(0, str(WS/'experiments/TASK-E4-W0-CROSSVIDEO-027-CORRECTIVE-R6/replay'))
sys.path.insert(0, str(WS/'camera_mainline/code'))
sys.path.insert(0, str(WS/'runtime/p3d'))
sys.path.insert(0, str(WS/'src'))
import u028c as U


class AdmissionGate(unittest.TestCase):
    def test_real_counts(self):
        cases = {'G01/004': 0, 'G01/005': 0, 'G05/004': 0, 'G05/005': 0, 'G06/005': 0}
        for arm, expected in cases.items():
            g, v = arm.split('/')
            p = (WS/'camera_mainline'/g/f'video{v}'/'camera_result.npz'
                 if (WS/'camera_mainline'/g/f'video{v}'/'camera_result.npz').exists()
                 else F/'runs'/g/'w0'/f'video{v}'/'camera_result.npz')
            _, acc = U.accepted_from_npz(p)
            self.assertEqual(len(acc), expected, arm)
        _, acc = U.accepted_from_npz(WS/'camera_mainline/G03/video005/camera_result.npz')
        self.assertEqual(len(acc), 16)

    def test_gate_blocks_if_any_video_has_zero_accept(self):
        st, counts, blocked = U.admission_gate({'004': {'ACCEPT': 8}, '005': {'ACCEPT': 0}})
        self.assertEqual(st, 'BLOCKED_BY_W0_ADMISSION')
        self.assertEqual(blocked, ['005'])
        st, _, _ = U.admission_gate({'004': {'ACCEPT': 8}, '005': {'ACCEPT': 2}})
        self.assertEqual(st, 'OK')


if __name__ == '__main__':
    unittest.main(verbosity=2)
```

- [ ] **Step 2: Run the test and confirm it fails**

```bash
cd /home/liu/ring_first_3d_workspace
/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python tests/test_028_admission_gate.py -v
```

Expected: FAIL with `AttributeError: module 'u028c' has no attribute 'accepted_from_npz'`.

- [ ] **Step 3: Add the gate helpers**

```python
STATUSES = ('ACCEPT', 'QUARANTINE', 'REJECT', 'INSUFFICIENT_EVIDENCE')


def accepted_from_npz(path):
    d = np.load(path)
    ids = [str(x) for x in d['ids']]
    st = ([str(x) for x in d['admission_status']] if 'admission_status' in d
          else ['UNKNOWN'] * len(ids))
    adm = dict(zip(ids, st))
    return adm, [i for i in ids if adm[i] == 'ACCEPT']


def admission_gate(adm_by_video):
    counts = {v: {s: sum(1 for x in adm.values() if x == s) for s in STATUSES}
              for v, adm in adm_by_video.items()}
    blocked = [v for v, c in counts.items() if c['ACCEPT'] == 0]
    return ('BLOCKED_BY_W0_ADMISSION' if blocked else 'OK'), counts, blocked
```

- [ ] **Step 4: Filter every geometry input to ACCEPT cameras**

In `main`, replace the W0-loading block with:

```python
    adm_by_video, acc_by_video = {}, {}
    for v in vids:
        p, how = w0_ensure(ctx, v)
        cam = np.load(p)
        adm, acc = accepted_from_npz(p)
        adm_by_video[v], acc_by_video[v] = adm, acc
        if not acc:
            continue
        prep = json.loads((PREP/f'{g}_{v}'/'PREPARED.json').read_text())
        meta = {x['view']: x for x in prep['views']}
        cams[v] = {i: np.asarray(cam['c2w'][k], float) for k, i in enumerate([str(x) for x in cam['ids']]) if i in set(acc)}
        K[v] = np.asarray(cam['K'], float); prep_all[v] = meta
        ring_valid.update(ring_evidence(ctx, meta, acc))
        ctx.manifest[f'w0_{v}'] = dict(path=str(p), how=how, sha256=sha256(p),
                                       n_views=len(acc), admission=dict(adm_by_video[v]))
    gate, gate_counts, blocked = admission_gate(adm_by_video)
    status = dict(group=g, videos=vids, admission=gate_counts,
                  n_accept={v: len(acc_by_video[v]) for v in vids})
    if gate != 'OK':
        status.update(status='BLOCKED_BY_W0_ADMISSION', reason=f'no ACCEPT cameras in {blocked}')
        (ctx.root/'SUMMARY.json').write_text(json.dumps(status, indent=1, default=int))
        print('BLOCKED', g, status['reason']); return
```

Also change `ref = max(vids, key=...)` to use `len(cams[v])` and `len(Lm[v]['X'])`; `admission` is no longer needed for the reference rule. Remove the `admission_of` call.

- [ ] **Step 5: Run the test and a fast blocked-group run**

```bash
cd /home/liu/ring_first_3d_workspace
/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python tests/test_028_admission_gate.py -v
PYTHONPATH=$PWD/experiments/TASK-E4-W0-CROSSVIDEO-028-CORRECTIVE-FINAL/core:$PWD/experiments/TASK-E4-W0-CROSSVIDEO-027-CORRECTIVE-R6/core:$PWD/experiments/TASK-E4-W0-CROSSVIDEO-027-CORRECTIVE-R6/replay:$PWD/runtime/p3d:$PWD/src \
  /home/liu/polyp_research/ring_anchor_3d/.venv/bin/python experiments/TASK-E4-W0-CROSSVIDEO-028-CORRECTIVE-FINAL/core/u028c.py --group G06 --max-views 4
cat experiments/TASK-E4-W0-CROSSVIDEO-028-CORRECTIVE-FINAL/runs/G06/SUMMARY.json
```

Expected: 2 PASS; G06 SUMMARY has `"status": "BLOCKED_BY_W0_ADMISSION"` and `005` ACCEPT count 0.

- [ ] **Step 6: Commit**

```bash
git add experiments/TASK-E4-W0-CROSSVIDEO-028-CORRECTIVE-FINAL/core/u028c.py tests/test_028_admission_gate.py
git commit -m "028: enforce frozen camera admission gate and emit BLOCKED_BY_W0_ADMISSION"
```

---

## Task 4: Wire the config that is currently decorative

**Files:**
- Modify: `.../028-CORRECTIVE-FINAL/core/u028c.py`
- Modify: `.../028-CORRECTIVE-FINAL/config/PIPELINE.json` (add `h_init.max_nfev`, `identity.min_view_pairs_multiview`)
- Test: `tests/test_028_config_status.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_028_config_status.py
import json, sys, tempfile, unittest
from pathlib import Path
WS = Path('/home/liu/ring_first_3d_workspace')
F = WS/'experiments/TASK-E4-W0-CROSSVIDEO-028-CORRECTIVE-FINAL'
sys.path.insert(0, str(F/'core'))
sys.path.insert(0, str(WS/'experiments/TASK-E4-W0-CROSSVIDEO-027-CORRECTIVE-R6/core'))
sys.path.insert(0, str(WS/'experiments/TASK-E4-W0-CROSSVIDEO-027-CORRECTIVE-R6/replay'))
sys.path.insert(0, str(WS/'runtime/p3d')); sys.path.insert(0, str(WS/'src'))
import u028c as U


class ConfigWiring(unittest.TestCase):
    def test_budgets_and_yaw_come_from_config(self):
        cfg = json.loads((F/'config/PIPELINE.json').read_text())
        self.assertEqual(cfg['ba']['budget_M2'], 60)
        self.assertEqual(cfg['ba']['budget_M3b'], 60)
        self.assertEqual(cfg['h_init']['yaw_step_deg'], 30)
        self.assertEqual(cfg['h_init']['max_nfev'], 30)
        self.assertEqual(U.ba_budget(cfg, 'M2'), 60)
        self.assertEqual(U.ba_budget(cfg, 'M3b'), 60)

    def test_geometry_status_matrix(self):
        self.assertEqual(U.geometry_status(False, [], [1.0]), 'BLOCKED_BY_W0_ADMISSION')
        self.assertEqual(U.geometry_status(True, [{'success': False}], [1.0]), 'OPTIMIZATION_NOT_CONVERGED')
        self.assertEqual(U.geometry_status(True, [{'success': True}], [1.0]), 'GEOMETRY_OK')
        self.assertEqual(U.geometry_status(True, [{'success': True}], [float('nan')]), 'GEOMETRY_INVALID')


if __name__ == '__main__':
    unittest.main(verbosity=2)
```

- [ ] **Step 2: Run the test and confirm it fails**

```bash
cd /home/liu/ring_first_3d_workspace
/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python tests/test_028_config_status.py -v
```

Expected: FAIL with `KeyError: 'max_nfev'` or missing `ba_budget`.

- [ ] **Step 3: Add config helpers and update the config file**

```python
CONFIG_PATH = U/'config'/'PIPELINE.json'


def load_config(path=None):
    return json.loads(Path(path or CONFIG_PATH).read_text())


def ba_budget(cfg, mode):
    return int(cfg['ba'][f'budget_{mode}'])


def geometry_status(admission_ok, infos, fit_medians):
    if not admission_ok:
        return 'BLOCKED_BY_W0_ADMISSION'
    if any(not bool(i.get('success')) for i in infos):
        return 'OPTIMIZATION_NOT_CONVERGED'
    if any(x is None or not np.isfinite(x) for x in fit_medians):
        return 'GEOMETRY_INVALID'
    return 'GEOMETRY_OK'
```

In `Ctx.__init__`, replace the inline read with `self.cfg = load_config()` so tests and the entry share one loader.

Update `config/PIPELINE.json`:

```json
"h_init": {"yaw_step_deg": 30, "max_nfev": 30, "ring_vector": "I/C/O exact energy mapping", "old": "H = I then H-only", "new": "Ring+epipolar best candidate"},
"ba": {"budget_M2": 60, "budget_M3b": 60, "rgb_mode": "huber", "released_cameras": []},
"identity": {"matcher": "features019.matches (ratio .72 + mutual + MAGSAC)", "min_view_pairs_multiview": 2, "one_to_one": true},
```

- [ ] **Step 4: Use the config everywhere**

```python
    cfg = load_config()
    yaw_step = float(cfg['h_init']['yaw_step_deg'])
    h_nfev = int(cfg['h_init']['max_nfev'])
    b2, b3 = ba_budget(cfg, 'M2'), ba_budget(cfg, 'M3b')
    rgb_mode = cfg['ba']['rgb_mode']
    seed = int(cfg['holdout']['seed'])
    min_pairs = int(cfg['identity']['min_view_pairs_multiview'])
```

Then:

```python
    cands, epi_ok = ring_candidates(..., yaw_step=yaw_step, max_nfev=h_nfev)
    H_old, _, i2 = solve_pipeline(..., 'M2', b2, rgb_mode)
    H_old3, X_old3, i3 = solve_pipeline(..., 'M3b', b3, rgb_mode, warmup_budget=b2)
    H_new3, X_new3, i4 = solve_pipeline(..., 'M3b', b3, rgb_mode, warmup_budget=b2)
    rng = np.random.default_rng(seed)
```

Also fix the M3b budget allocation inside `solve_pipeline`. The current code gives the H-only warmup half the budget and the joint stage the remainder, so `budget_M3b=60` becomes 30 + 30. Give the warmup the M2 budget and the joint stage the full M3b budget:

```python
def solve_pipeline(ctx, rr, ref, other, cams, K, ids_rows, L_ref, L_oth,
                   X0n, H_init, mode, budget, rgb_mode='huber', warmup_budget=None):
    ...
    info_warmup = dict(nfev=0, success=True, status=0)
    if mode == 'M2':
        ...
    elif mode == 'M3b':
        wb = int(warmup_budget if warmup_budget is not None else budget)
        r1 = least_squares(fh, np.zeros(6), method='trf', loss='linear',
                           x_scale='jac', max_nfev=wb)
        H1 = __import__('se3').exp_se3(r1.x) @ H_init
        fj = lambda t: P.residual_vector(__import__('se3').exp_se3(t[:6]) @ H1,
                                         dx0, t[6:].reshape(-1, 3), rgb_mode)[0]
        r = least_squares(fj, np.r_[np.zeros(6), X0n.ravel()], method='trf',
                          loss='linear', x_scale='jac', max_nfev=budget)
        H = __import__('se3').exp_se3(r.x[:6]) @ H1
        X = r.x[6:].reshape(-1, 3)
        info_warmup = dict(nfev=int(r1.nfev), success=bool(r1.success), status=int(r1.status))
    ...
    return H, X, dict(mode=mode, success=bool(r.success), status=int(r.status),
                      nfev=int(r.nfev), nfev_warmup=info_warmup['nfev'],
                      success_warmup=info_warmup['success'], cost=float(r.cost),
                      n_params=int(J.shape[1]), rank=int(np.linalg.matrix_rank(J)))
```

Pass `rgb_mode` through `P.residual_vector(..., rgb_mode)` instead of the hardcoded `'huber'`. Add `config_echo` to `SUMMARY.json`.

- [ ] **Step 5: Run the test and G03 with the full config**

```bash
cd /home/liu/ring_first_3d_workspace
/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python tests/test_028_config_status.py -v
PYTHONPATH=$PWD/experiments/TASK-E4-W0-CROSSVIDEO-028-CORRECTIVE-FINAL/core:$PWD/experiments/TASK-E4-W0-CROSSVIDEO-027-CORRECTIVE-R6/core:$PWD/experiments/TASK-E4-W0-CROSSVIDEO-027-CORRECTIVE-R6/replay:$PWD/runtime/p3d:$PWD/src \
  /home/liu/polyp_research/ring_anchor_3d/.venv/bin/python experiments/TASK-E4-W0-CROSSVIDEO-028-CORRECTIVE-FINAL/core/u028c.py --group G03 --max-views 4
python3 -c "import json;d=json.load(open('experiments/TASK-E4-W0-CROSSVIDEO-028-CORRECTIVE-FINAL/runs/G03/SUMMARY.json'));print(d['status'],d['config_echo'])"
```

Expected: 2 PASS; G03 status is `OPTIMIZATION_NOT_CONVERGED` (not `GEOMETRY_OK`), and `config_echo` reports 60/60/30/30.

- [ ] **Step 6: Commit**

```bash
git add experiments/TASK-E4-W0-CROSSVIDEO-028-CORRECTIVE-FINAL/core/u028c.py \
        experiments/TASK-E4-W0-CROSSVIDEO-028-CORRECTIVE-FINAL/config/PIPELINE.json \
        tests/test_028_config_status.py
git commit -m "028: execute PIPELINE.json budgets/yaw/rgb_mode/seed and stop reporting GEOMETRY_OK without convergence"
```

---

## Task 5: Fail closed on unidentifiable H and on triangulation failure

**Files:**
- Create: `.../028-CORRECTIVE-FINAL/core/fixed_track_tri_v2.py` (copy of 019 code + failure handling)
- Modify: `.../028-CORRECTIVE-FINAL/core/u028c.py`
- Test: `tests/test_028_triangulation.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_028_triangulation.py
import sys, unittest
from pathlib import Path
import numpy as np
WS = Path('/home/liu/ring_first_3d_workspace')
F = WS/'experiments/TASK-E4-W0-CROSSVIDEO-028-CORRECTIVE-FINAL'
sys.path.insert(0, str(F/'core'))
sys.path.insert(0, str(WS/'experiments/TASK-E4-W0-CROSSVIDEO-027-CORRECTIVE-R6/replay'))
sys.path.insert(0, str(WS/'runtime/p3d')); sys.path.insert(0, str(WS/'src'))
import fixed_track_tri_v2 as FT


class TriangulationFailure(unittest.TestCase):
    def test_degenerate_track_is_explicit(self):
        C = np.eye(4)
        views = {f'v{k}': dict(id=f'v{k}', T=C.copy(), K=np.eye(3)) for k in range(2)}
        res = FT.triangulate_tracks([[('v0', 0), ('v1', 0)]], views)[0]
        self.assertIsNone(res['X'])
        self.assertEqual(res['status'], 'TRIANGULATION_FAILED')

    def test_identity_keyed_output_does_not_shift(self):
        rows = [dict(identity='a'), dict(identity='b')]
        X = np.array([[0., 0., 10.], [1., 0., 10.]])
        out = FT.attach_identities(rows, X)
        self.assertEqual([r['identity'] for r in out], ['a', 'b'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
```

- [ ] **Step 2: Run the test and confirm it fails**

```bash
cd /home/liu/ring_first_3d_workspace
/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python tests/test_028_triangulation.py -v
```

Expected: FAIL because `fixed_track_tri_v2` does not exist.

- [ ] **Step 3: Create the v2 copy with failure handling**

```bash
cp experiments/TASK-E4-W0-CROSSVIDEO-027-CORRECTIVE-R6/core/fixed_track_tri.py \
   experiments/TASK-E4-W0-CROSSVIDEO-028-CORRECTIVE-FINAL/core/fixed_track_tri_v2.py
```

Wrap the body of the per-track loop:

```python
def triangulate_tracks(tracks, VIEWS):
    out = []
    for tr in tracks:
        try:
            if len(tr) < 3:
                raise ValueError('TRACK_LT3')
            vv = [VIEWS[v] for v, _ in tr]
            xy = np.array([F19.features(v)['xy'][j] for v, (_, j) in zip(vv, tr)])
            centers = np.array([np.asarray(v['T'])[:3, 3] for v in vv])
            i, j = max(itertools.combinations(range(len(tr)), 2),
                       key=lambda ij: np.linalg.norm(centers[ij[0]] - centers[ij[1]]))
            a, b = vv[i], vv[j]
            P1 = np.asarray(a['K']) @ np.linalg.inv(np.asarray(a['T']))[:3]
            P2 = np.asarray(b['K']) @ np.linalg.inv(np.asarray(b['T']))[:3]
            H = cv2.triangulatePoints(P1, P2, xy[i:i+1].T, xy[j:j+1].T)
            X = H[:3, 0] / H[3, 0]

            def res(x):
                return np.concatenate([project(x, v)[0] - p for v, p in zip(vv, xy)])

            sol = least_squares(res, X, loss='soft_l1', f_scale=1.5, max_nfev=30)
            X = sol.x
            if not np.isfinite(X).all():
                raise ValueError('NONFINITE_X')
            err = np.linalg.norm(res(X).reshape(-1, 2), axis=1)
            z = np.array([project(X, v)[1] for v in vv])
            rays = X - centers
            rays /= np.linalg.norm(rays, axis=1)[:, None]
            par = np.degrees(np.arccos(np.clip(rays @ rays.T, -1, 1))).max()
            out.append(dict(X=X, reproj=err, parallax=par, z=z, status='OK'))
        except Exception as e:
            out.append(dict(X=None, reproj=None, parallax=None, z=None,
                            status='TRIANGULATION_FAILED', error=type(e).__name__))
    return out


def attach_identities(rows, X):
    assert len(rows) == len(X), f'identity/X length mismatch {len(rows)} != {len(X)}'
    return [dict(r, X=X[k]) for k, r in enumerate(rows)]
```

- [ ] **Step 4: Make `u028c` pass only successfully triangulated identities to BA**

```python
import fixed_track_tri_v2 as FTT


def _tri_one(F19, FTT, pts, K):
    if len(pts) < 3:
        return None, None
    xy = np.array([p[1] for p in pts]); Cw = [p[2] for p in pts]
    shim = {f'v{k}': dict(id=f'v{k}', T=Cw[k], K=np.asarray(K, float)) for k in range(len(pts))}
    tr = [(f'v{k}', k) for k in range(len(pts))]
    def fake(v, _xy=xy):
        return dict(xy=_xy, des=np.zeros((len(_xy), 128), np.float32))
    old = F19.features; F19.features = fake
    try:
        r = FTT.triangulate_tracks([tr], shim)[0]
    finally:
        F19.features = old
    if r['X'] is None:
        return None, r
    return r['X'], r


def triangulate_ref_only(F19, FTT, rows, L_ref, ref, cams, K):
    X, meta, ok_rows = [], [], []
    for _, r in rows.iterrows():
        pts = [(o['view'], np.asarray(o['uv'], float), np.asarray(cams[ref][o['view']], float))
               for o in L_ref['obs'][int(r.ref_index)]['observations']]
        Xi, rr = _tri_one(F19, FTT, pts, K)
        if Xi is None:
            meta.append(dict(identity=r.identity, status='TRIANGULATION_FAILED',
                             reason=(rr or {}).get('error', 'LT3_OBS')))
            continue
        X.append(Xi); ok_rows.append(r)
        meta.append(dict(identity=r.identity, n_ref_obs=len(pts),
                         parallax_deg=float(rr['parallax']),
                         reproj_max=float(rr['reproj'].max()), status='REF_ONLY_OK'))
    return ok_rows, (np.array(X) if X else np.zeros((0, 3))), pd.DataFrame(meta)


def triangulate_identities(F19, FTT, X0n, ids_rows, L_ref, L_oth, ref, other, cams, H, K):
    obs_ref = {i: L_ref['obs'][i]['observations'] for i in range(len(L_ref['obs']))}
    obs_oth = {j: L_oth['obs'][j]['observations'] for j in range(len(L_oth['obs']))}
    X, meta, ok_rows = [], [], []
    for _, r in ids_rows.iterrows():
        pts = []
        for o in obs_ref[int(r.ref_index)]:
            pts.append((o['view'], np.asarray(o['uv'], float),
                        np.asarray(cams[ref][o['view']], float), ref))
        for o in obs_oth[int(r.other_index)]:
            pts.append((o['view'], np.asarray(o['uv'], float),
                        H @ np.asarray(cams[other][o['view']], float), other))
        if len(pts) < 3:
            meta.append(dict(identity=r.identity, status='TRIANGULATION_FAILED', reason='LT3_OBS'))
            continue
        xy = np.array([p[1] for p in pts]); Cw = [p[2] for p in pts]
        shim = {f'v{k}': dict(id=f'v{k}', T=Cw[k], K=np.asarray(K[pts[k][3]], float))
                for k in range(len(pts))}
        tr = [(f'v{k}', k) for k in range(len(pts))]
        def fake(v, _xy=xy, _n=len(xy)):
            return dict(xy=_xy, des=np.zeros((_n, 128), np.float32))
        old = F19.features; F19.features = fake
        try:
            res = FTT.triangulate_tracks([tr], shim)[0]
        finally:
            F19.features = old
        if res['X'] is None:
            meta.append(dict(identity=r.identity, status='TRIANGULATION_FAILED',
                             reason=res.get('error', 'UNKNOWN')))
            continue
        X.append(res['X']); ok_rows.append(r)
        meta.append(dict(identity=r.identity, n_obs=len(pts), view_pairs=int(r.n_view_pairs),
                         parallax_deg=float(res['parallax']),
                         reproj_max=float(res['reproj'].max()),
                         zmin=float(res['z'].min()), status=r.status))
    return ok_rows, (np.array(X) if X else np.zeros((0, 3))), pd.DataFrame(meta)
```

Update the call sites exactly:

```python
    rows_ref_ok, X_ref, meta_ref = triangulate_ref_only(
        F19, FTT, rows_fit, Lm[ref], ref, cams, K[ref])
    meta_ref.to_csv(ctx.dirs['triangulation']/'X_REF_ONLY.csv', index=False)
    H_old, _, i2 = solve_pipeline(
        ctx, rr, ref, other, cams, K, rows_ref_ok, Lm[ref], Lm[other],
        X_ref, np.eye(4), 'M2', b2, rgb_mode)
    rows_tri_old, Xn_old, m_old = triangulate_identities(
        F19, FTT, None, rows_fit, Lm[ref], Lm[other], ref, other, cams, H_old, K)
    m_old.to_csv(ctx.dirs['triangulation']/'TRI_old.csv', index=False)
    H_old3, X_old3, i3 = solve_pipeline(
        ctx, rr, ref, other, cams, K, rows_tri_old, Lm[ref], Lm[other],
        Xn_old, H_old, 'M3b', b3, rgb_mode)
    rows_tri_new, Xn_new, m_new = triangulate_identities(
        F19, FTT, None, rows_fit, Lm[ref], Lm[other], ref, other, cams, H_new, K)
    m_new.to_csv(ctx.dirs['triangulation']/'TRI_new.csv', index=False)
    H_new3, X_new3, i4 = solve_pipeline(
        ctx, rr, ref, other, cams, K, rows_tri_new, Lm[ref], Lm[other],
        Xn_new, H_new, 'M3b', b3, rgb_mode)
```

Use `rows_tri_*` for `reproj_stats` and `holdout_stats` accordingly. Add `TRIANGULATION_FAILED` rows to `TRI_new.csv` / `TRI_old.csv` with `X=None` and no silent drop.

- [ ] **Step 5: Add the H fail-closed path**

```python
    cands, epi_ok = ring_candidates(...)
    if not epi_ok or not cands:
        status.update(status='H_INIT_UNOBSERVABLE', reason='no candidate with a valid epipolar score')
        (ctx.root/'SUMMARY.json').write_text(json.dumps(status, indent=1, default=int))
        print('H_INIT_UNOBSERVABLE', g); return
```

- [ ] **Step 6: Run the tests**

```bash
cd /home/liu/ring_first_3d_workspace
/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python tests/test_028_triangulation.py -v
```

Expected: 2 PASS.

- [ ] **Step 7: Commit**

```bash
git add experiments/TASK-E4-W0-CROSSVIDEO-028-CORRECTIVE-FINAL/core/fixed_track_tri_v2.py \
        experiments/TASK-E4-W0-CROSSVIDEO-028-CORRECTIVE-FINAL/core/u028c.py \
        tests/test_028_triangulation.py
git commit -m "028: explicit TRIANGULATION_FAILED and identity-keyed X; fail closed on unobservable H"
```

---

## Task 6: Make the Ring residual single-source and add a consistency diagnostic

**Files:**
- Modify: `.../028-CORRECTIVE-FINAL/core/u028c.py`
- Test: `tests/test_028_ring_residual.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_028_ring_residual.py
import sys, unittest
import numpy as np
from pathlib import Path
WS = Path('/home/liu/ring_first_3d_workspace')
F = WS/'experiments/TASK-E4-W0-CROSSVIDEO-028-CORRECTIVE-FINAL'
sys.path.insert(0, str(F/'core'))
sys.path.insert(0, str(WS/'experiments/TASK-E4-W0-CROSSVIDEO-027-CORRECTIVE-R6/core'))
sys.path.insert(0, str(WS/'experiments/TASK-E4-W0-CROSSVIDEO-027-CORRECTIVE-R6/replay'))
sys.path.insert(0, str(WS/'runtime/p3d')); sys.path.insert(0, str(WS/'src'))
import u028c as U, ring_energy as RE


class RingResidualSingleSource(unittest.TestCase):
    def test_inline_formula_equals_ring_energy(self):
        d = np.array([0.0, 0.5, 2.9, 3.0, 7.5])
        for w in (0.35, 0.05):
            ref = RE.ring_residuals(d, 1.0, w)
            got = U.ring_residual_from_dists(d, w)
            np.testing.assert_allclose(got, ref, rtol=0, atol=1e-15)

    def test_consistency_diagnostic_contract(self):
        self.assertEqual(U.ring_geometry_consistency.__name__, 'ring_geometry_consistency')


if __name__ == '__main__':
    unittest.main(verbosity=2)
```

- [ ] **Step 2: Run the test and confirm it fails**

```bash
cd /home/liu/ring_first_3d_workspace
/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python tests/test_028_ring_residual.py -v
```

Expected: FAIL with missing `ring_residual_from_dists`.

- [ ] **Step 3: Replace the inline formula**

```python
import ring_energy as RE


def ring_residual_from_dists(d, w):
    """Single source: the same mapping used by ba_core_r4's Ring blocks."""
    return RE.ring_residuals(np.asarray(d, float), 1.0, w)
```

In `ring_vector`, replace:

```python
        out.append(np.sqrt(2.0*w*np.where(d/3 < 1, 0.5*(d/3)**2, np.abs(d/3)-0.5)/max(len(d), 1)))
```

with:

```python
        out.append(ring_residual_from_dists(d, w))
```

- [ ] **Step 4: Add the BA-vs-evaluation geometry diagnostic**

```python
def ring_geometry_consistency(rr, ref, other, cams, K, H_init, H_final):
    """Report how many views change CAD edge assignment between H_init and H_final."""
    rec = []
    for video in (ref, other):
        for v in cams[video]:
            C0 = (np.asarray(cams[video][v], float) if video == ref
                  else H_init @ np.asarray(cams[video][v], float))
            C1 = (np.asarray(cams[video][v], float) if video == ref
                  else H_final @ np.asarray(cams[video][v], float))
            Kk = K[ref] if video == ref else K[other]
            s0 = rr.curves.segments(C0, Kk)
            s1 = rr.curves.segments(C1, Kk)
            rec.append(dict(video=video, view=v,
                            inner_same=bool(np.array_equal(np.asarray(s0['inner']), np.asarray(s1['inner']))),
                            outer_same=bool(np.array_equal(np.asarray(s0['outer']), np.asarray(s1['outer'])))))
    return dict(n_views=len(rec),
                n_edge_mismatch=sum(1 for r in rec if not (r['inner_same'] and r['outer_same'])),
                per_view=rec)
```

In `main`, after the matrix loop:

```python
    (ctx.dirs['evaluation']/'RING_GEOMETRY_CONSISTENCY.json').write_text(json.dumps(
        {name: ring_geometry_consistency(rr, ref, other, cams, K, H0, Hf)
         for name, H0, Hf in (('old', H_old, H_old3), ('new', H_new, H_new3))}, indent=1))
```

- [ ] **Step 5: Run the test and the G03 run**

```bash
cd /home/liu/ring_first_3d_workspace
/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python tests/test_028_ring_residual.py -v
PYTHONPATH=$PWD/experiments/TASK-E4-W0-CROSSVIDEO-028-CORRECTIVE-FINAL/core:$PWD/experiments/TASK-E4-W0-CROSSVIDEO-027-CORRECTIVE-R6/core:$PWD/experiments/TASK-E4-W0-CROSSVIDEO-027-CORRECTIVE-R6/replay:$PWD/runtime/p3d:$PWD/src \
  /home/liu/polyp_research/ring_anchor_3d/.venv/bin/python experiments/TASK-E4-W0-CROSSVIDEO-028-CORRECTIVE-FINAL/core/u028c.py --group G03 --max-views 4
cat experiments/TASK-E4-W0-CROSSVIDEO-028-CORRECTIVE-FINAL/runs/G03/evaluation/RING_GEOMETRY_CONSISTENCY.json
```

Expected: 2 PASS; consistency JSON exists and reports `n_views` and `n_edge_mismatch`.

- [ ] **Step 6: Commit**

```bash
git add experiments/TASK-E4-W0-CROSSVIDEO-028-CORRECTIVE-FINAL/core/u028c.py tests/test_028_ring_residual.py
git commit -m "028: single-source Ring residual + BA/evaluation edge-assignment diagnostic (no objective change)"
```

---

## Task 7: Make every 028 run self-contained and stop writing into TASK-015

**Files:**
- Modify: `.../028-CORRECTIVE-FINAL/core/u028c.py`
- Test: `tests/test_028_manifest.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_028_manifest.py
import json, sys, unittest
from pathlib import Path
WS = Path('/home/liu/ring_first_3d_workspace')
F = WS/'experiments/TASK-E4-W0-CROSSVIDEO-028-CORRECTIVE-FINAL'
sys.path.insert(0, str(F/'core'))
sys.path.insert(0, str(WS/'experiments/TASK-E4-W0-CROSSVIDEO-027-CORRECTIVE-R6/core'))
sys.path.insert(0, str(WS/'experiments/TASK-E4-W0-CROSSVIDEO-027-CORRECTIVE-R6/replay'))
sys.path.insert(0, str(WS/'runtime/p3d')); sys.path.insert(0, str(WS/'src'))
import u028c as U


class ManifestSelfContained(unittest.TestCase):
    def test_blocked_run_writes_manifest(self):
        p = F/'runs/G06/input_manifest/MANIFEST.json'
        self.assertTrue(p.exists())
        d = json.loads(p.read_text())
        self.assertEqual(d['status'], 'BLOCKED_BY_W0_ADMISSION')
        self.assertIn('admission', d)
        self.assertIn('config_echo', d)


if __name__ == '__main__':
    unittest.main(verbosity=2)
```

- [ ] **Step 2: Run the test and confirm it fails**

```bash
cd /home/liu/ring_first_3d_workspace
/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python tests/test_028_manifest.py -v
```

Expected: FAIL because `runs/G06/input_manifest/MANIFEST.json` does not exist.

- [ ] **Step 3: Namespace the W0 workdir and write a manifest on every path**

In `w0_ensure`:

```python
    work = ctx.dirs['w0']/'work'/f'video{video}'
    cmd = [sys.executable, str(WS/'tools'/'run_w0_camera.py'), '--group', g, '--video', video,
           '--stage', 'all', '--output', str(out), '--workdir', str(work)]
```

Add a manifest writer:

```python
def write_manifest(ctx, status, extra=None):
    files = []
    for p in sorted(ctx.root.rglob('*')):
        if p.is_file() and p.name != 'MANIFEST.json':
            files.append(dict(path=str(p.relative_to(ctx.root)), sha256=sha256(p), bytes=p.stat().st_size))
    d = dict(group=ctx.g, status=status, config_echo=ctx.cfg,
             admission=extra or {}, code=dict(entry=sha256(U/'core'/'u028c.py')),
             files=files)
    (ctx.dirs['input_manifest']/'MANIFEST.json').write_text(json.dumps(d, indent=1))
```

Call it on the blocked path and the normal path:

```python
    if gate != 'OK':
        status.update(status='BLOCKED_BY_W0_ADMISSION', reason=f'no ACCEPT cameras in {blocked}')
        (ctx.root/'SUMMARY.json').write_text(json.dumps(status, indent=1, default=int))
        write_manifest(ctx, 'BLOCKED_BY_W0_ADMISSION', dict(admission=gate_counts))
        print('BLOCKED', g, status['reason']); return
```

and, at the end of the normal path:

```python
    (ctx.root/'SUMMARY.json').write_text(json.dumps(status, indent=1, default=int))
    ctx.save_manifest()
    write_manifest(ctx, status['status'], dict(admission=gate_counts, pipelines=rows))
```

- [ ] **Step 4: Run G06 and G03, then check manifests**

```bash
cd /home/liu/ring_first_3d_workspace
PYTHONPATH=$PWD/experiments/TASK-E4-W0-CROSSVIDEO-028-CORRECTIVE-FINAL/core:$PWD/experiments/TASK-E4-W0-CROSSVIDEO-027-CORRECTIVE-R6/core:$PWD/experiments/TASK-E4-W0-CROSSVIDEO-027-CORRECTIVE-R6/replay:$PWD/runtime/p3d:$PWD/src \
  /home/liu/polyp_research/ring_anchor_3d/.venv/bin/python experiments/TASK-E4-W0-CROSSVIDEO-028-CORRECTIVE-FINAL/core/u028c.py --group G06 --max-views 4
PYTHONPATH=$PWD/experiments/TASK-E4-W0-CROSSVIDEO-028-CORRECTIVE-FINAL/core:$PWD/experiments/TASK-E4-W0-CROSSVIDEO-027-CORRECTIVE-R6/core:$PWD/experiments/TASK-E4-W0-CROSSVIDEO-027-CORRECTIVE-R6/replay:$PWD/runtime/p3d:$PWD/src \
  /home/liu/polyp_research/ring_anchor_3d/.venv/bin/python experiments/TASK-E4-W0-CROSSVIDEO-028-CORRECTIVE-FINAL/core/u028c.py --group G03 --max-views 4
/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python tests/test_028_manifest.py -v
```

Expected: G06 blocked; G03 runs; both have `input_manifest/MANIFEST.json`; the G06 manifest lists only files under `runs/G06`.

- [ ] **Step 5: Commit**

```bash
git add experiments/TASK-E4-W0-CROSSVIDEO-028-CORRECTIVE-FINAL/core/u028c.py tests/test_028_manifest.py
git commit -m "028: per-run workdir + self-contained manifest on success and blocked paths"
```

---

## Task 8: Run the four-group matrix under one config

**Files:**
- Create: `tests/test_cross_group_matrix.py`
- Output: `.../028-CORRECTIVE-FINAL/runs/CROSS_GROUP.csv`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_cross_group_matrix.py
import unittest
from pathlib import Path
import pandas as pd
WS = Path('/home/liu/ring_first_3d_workspace')
CSV = WS/'experiments/TASK-E4-W0-CROSSVIDEO-028-CORRECTIVE-FINAL/runs/CROSS_GROUP.csv'


class CrossGroupMatrix(unittest.TestCase):
    def test_all_four_groups_have_one_row(self):
        d = pd.read_csv(CSV)
        self.assertEqual(sorted(d.group.tolist()), ['G01', 'G03', 'G05', 'G06'])
        blocked = d[d.status == 'BLOCKED_BY_W0_ADMISSION'].group.tolist()
        self.assertEqual(sorted(blocked), ['G01', 'G05', 'G06'])
        self.assertIn(d[d.group == 'G03'].status.iloc[0],
                      {'OPTIMIZATION_NOT_CONVERGED', 'GEOMETRY_OK'})


if __name__ == '__main__':
    unittest.main(verbosity=2)
```

- [ ] **Step 2: Run the test and confirm it fails**

```bash
cd /home/liu/ring_first_3d_workspace
/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python tests/test_cross_group_matrix.py -v
```

Expected: FAIL because `CROSS_GROUP.csv` is missing or has only G03/G06.

- [ ] **Step 3: Run the four groups with the same entry and config**

```bash
cd /home/liu/ring_first_3d_workspace
export RF_PY=/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python
export RF_PP=$PWD/experiments/TASK-E4-W0-CROSSVIDEO-028-CORRECTIVE-FINAL/core:$PWD/experiments/TASK-E4-W0-CROSSVIDEO-027-CORRECTIVE-R6/core:$PWD/experiments/TASK-E4-W0-CROSSVIDEO-027-CORRECTIVE-R6/replay:$PWD/runtime/p3d:$PWD/src
for g in G01 G03 G05 G06; do
  PYTHONPATH=$RF_PP $RF_PY experiments/TASK-E4-W0-CROSSVIDEO-028-CORRECTIVE-FINAL/core/u028c.py --group $g --max-views 4
done
```

Expected: G01/G05/G06 print `BLOCKED`; G03 runs and reports `OPTIMIZATION_NOT_CONVERGED`.

- [ ] **Step 4: Write the aggregator**

```python
# .../028-CORRECTIVE-FINAL/core/aggregate_cross_group.py
import json
from pathlib import Path
import pandas as pd

F = Path(__file__).resolve().parents[1]
rows = []
for g in ('G01', 'G03', 'G05', 'G06'):
    s = json.loads((F/'runs'/g/'SUMMARY.json').read_text())
    pipes = {p['pipeline']: p for p in s.get('pipelines', [])}
    rows.append(dict(group=g, status=s['status'],
                     admission_004=s.get('admission', {}).get('004', {}).get('ACCEPT'),
                     admission_005=s.get('admission', {}).get('005', {}).get('ACCEPT'),
                     n_identities=s.get('n_identities'),
                     n_fit=s.get('n_fit'), n_holdout=s.get('n_holdout'),
                     old_fit=pipes.get('old', {}).get('fit_median'),
                     old_hold=pipes.get('old', {}).get('ho_median'),
                     new_fit=pipes.get('new', {}).get('fit_median'),
                     new_hold=pipes.get('new', {}).get('ho_median'),
                     ba_success=pipes.get('new', {}).get('success')))
pd.DataFrame(rows).to_csv(F/'runs'/'CROSS_GROUP.csv', index=False)
print(pd.DataFrame(rows).to_string(index=False))
```

Run it, then the test:

```bash
/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python experiments/TASK-E4-W0-CROSSVIDEO-028-CORRECTIVE-FINAL/core/aggregate_cross_group.py
/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python tests/test_cross_group_matrix.py -v
```

Expected: 4 rows; G01/G05/G06 blocked; G03 `OPTIMIZATION_NOT_CONVERGED`.

- [ ] **Step 5: Commit**

```bash
git add experiments/TASK-E4-W0-CROSSVIDEO-028-CORRECTIVE-FINAL/core/aggregate_cross_group.py \
        experiments/TASK-E4-W0-CROSSVIDEO-028-CORRECTIVE-FINAL/runs/CROSS_GROUP.csv \
        tests/test_cross_group_matrix.py
git commit -m "028: four-group matrix under one config; gate-blocked groups reported explicitly"
```

---

## Task 9: Verification report

**Files:**
- Create: `docs/audit/CONSOLIDATION_ROUND1_REPORT.md`

- [ ] **Step 1: Run the full verification suite**

```bash
cd /home/liu/ring_first_3d_workspace
export RF_PY=/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python
$RF_PY tests/test_w0_manifest_closure.py -v
$RF_PY tests/test_routes_registry.py -v
$RF_PY tests/test_028_admission_gate.py -v
$RF_PY tests/test_028_config_status.py -v
$RF_PY tests/test_028_triangulation.py -v
$RF_PY tests/test_028_ring_residual.py -v
$RF_PY tests/test_028_manifest.py -v
$RF_PY tests/test_cross_group_matrix.py -v
$RF_PY tools/check_routes_v2.py docs/registry/routes.yaml
```

Expected: every command exits 0.

- [ ] **Step 2: Write the report with measured values**

Include:

- M1 regression: 16/16 ACCEPT, 0.828765110526794, 0.9801671148427384, 3.209368827748597.
- G03 cross-video: identities, FIT/HOLDOUT, BA success/nfev, H init, Ring consistency mismatch count.
- G01/G05/G06: `BLOCKED_BY_W0_ADMISSION` with admission counts.
- G05 explicitly: 0 ACCEPT both videos.
- Defects closed: D16-D29 status.
- Remaining defects: D19 (non-convergence), D21 (H method), D23 (if mismatch), G1-G5.
- Statement: no new algorithm added; no historical asset deleted.

- [ ] **Step 3: Commit**

```bash
git add -f docs/audit/CONSOLIDATION_ROUND1_REPORT.md
git commit -m "docs: round-1 consolidation verification report (measured values, blocked groups, remaining gaps)"
```

---

## Task 10: Freeze M1 only (human-gated)

**Precondition:** Tasks 1-9 pass, `verification-before-completion` is satisfied, and the human explicitly approves the freeze.

**Files:**
- Create: `docs/registry/modules.yaml`
- Create: `docs/registry/pipeline.yaml`
- Modify: `docs/registry/routes.yaml` (`rf-w0-camera` status → `frozen`, add `human_approval`)

- [ ] **Step 1: Compute the frozen hash**

```bash
cd /home/liu/ring_first_3d_workspace
sha256sum tools/run_w0_camera.py tests/test_w0_manifest_closure.py
```

- [ ] **Step 2: Write `modules.yaml`**

```yaml
schema_version: 1
modules:
  - module_id: M1-W0-CAMERA
    route: rf-w0-camera@1
    status: frozen
    entrypoint: tools/run_w0_camera.py
    sha256: <paste sha256>
    inputs:
      - prepared/<G>_<V>/PREPARED.json + view caches (sha256 in manifest)
      - frozen tracks005/pairs005 or generated by the same entry
    outputs:
      - B0.npz, W0.npz, observations/, admission.csv,
      - camera_result.npz, accepted_cameras.npz, manifest.json
    dependencies:
      - rf-native-ring-cad@1
      - rf-dxy-ring-observation@1
      - rf-frozen-tracks005@1
      - rf-frozen-ba-local-ring-sfm@1
      - rf-camera-admission@1
    tests:
      - tests/test_w0_manifest_closure.py
    frozen_at: "<ISO date>"
    human_approval: "<approval reference>"
    known_limitations:
      - G01/G05/G06 are blocked by the frozen admission gate; this is a data outcome, not a code failure.
```

- [ ] **Step 3: Write `pipeline.yaml`**

```yaml
schema_version: 1
pipeline: ring-first-3d
formal: false
stages:
  - id: input
    module: M1-W0-CAMERA
    status: frozen
  - id: cross_video_matching
    status: planned
  - id: view_selection
    status: planned
  - id: identity
    status: planned
  - id: h_initialization
    status: planned
  - id: joint_ba
    status: planned
  - id: evaluation
    status: planned
  - id: visualization
    status: planned
note: >
  Only M1 is frozen. formal=false because the cross-video stages are research
  candidates, not frozen modules. No formal pipeline may consume them.
```

- [ ] **Step 4: Update `routes.yaml`**

Set `rf-w0-camera` status and refresh its source hash (Task 1 changed the file):

```yaml
    status: frozen
    source:
      repo: ring-first-3d
      path: tools/run_w0_camera.py
      sha256: <paste sha256 from Step 1>
    human_approval: "<approval reference>"
    frozen_at: "<ISO date>"
```

Do not change any other route status. Do not mark `features019`, `ring020_026`, `ba_core_r4`, or `028` as frozen.

- [ ] **Step 5: Run the validator and the full suite again**

```bash
cd /home/liu/ring_first_3d_workspace
/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python tools/check_routes_v2.py docs/registry/routes.yaml
/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python tests/test_w0_manifest_closure.py -v
```

Expected: validator 0 errors; M1 smoke PASS.

- [ ] **Step 6: Commit**

```bash
git add -f docs/registry/modules.yaml docs/registry/pipeline.yaml docs/registry/routes.yaml
git commit -m "freeze M1: W0 camera module with self-contained manifest and verified G03 regression"
```

---

## Self-review

**Spec coverage**

- M1 correctness/provenance: Tasks 1, 9, 10.
- Ring/BA math consistency: Task 6 (diagnostic only; no objective change).
- Duplicate/implicit dependencies: Tasks 1, 3, 5, 6.
- Module interfaces: Tasks 1, 3, 4, 5, 7.
- Camera/H/identity data flow: Tasks 3, 5, 7, 8.
- Config vs execution: Task 4.
- Results vs manifest: Tasks 1, 7, 9.
- Minimal reproduction: Task 1 and Task 8.
- GAP registration: `docs/audit/ROUTE_COMPOSITION_PLAN.md` §3; no GAP implementation in this plan.

**Placeholder scan**

- No `TBD`/`TODO`; the only placeholders are `<paste sha256>` and `<ISO date>`/`<approval reference>` in Task 10, which are intentionally computed/recorded at freeze time.
- Every code step shows the code.
- Every test step shows the test code and the expected result.

**Type consistency**

- `accepted_from_npz` returns `(adm, acc)` and is used consistently.
- `admission_gate` returns `(status, counts, blocked)` and is used consistently.
- `geometry_status(admission_ok, infos, fit_medians)` is used consistently.
- `triangulate_identities` returns `(ok_rows, X, meta)` after Task 5; all call sites are updated in the same task.
- `ba_budget(cfg, mode)` uses `budget_M2`/`budget_M3b` matching `PIPELINE.json`.

**Explicit non-goals**

- No change to the Ring CAD definition, H objective, BA loss, view budget, thresholds, or matching strategy.
- No per-group branch or threshold.
- No deletion of historical assets.
- No second formal entry.
