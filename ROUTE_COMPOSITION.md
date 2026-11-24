# M2F5 — Route Composition Review (STOP GATE)

**Status: WAITING FOR HUMAN APPROVAL. No integration code and no 13-group run.**

Workspace: `/home/liu/ring_first_3d_workspace`  
Reviewed source head: `907076543a24fa78a45b57c9eab3452457d8eb42`  
Serena project: `ring_first_3d_workspace` (session `7572728a`)  
Registry: `docs/registry/routes.yaml` (existing registry verified; M2F5 proposals appended under `m2f5_pending_routes`, **not promoted**).

## 1. Composition table

| Stage | Existing route@version | Entrypoint / source | Inputs → outputs | Classification | Registry status | Smoke test |
|---|---|---|---|---|---|---|
| Raw video + INIT + raw mask | `rf-m1-input-39@1`; `rf-init-segmentation@1` | `tools/prepare_m1_inputs.py::prepare_one`; frozen INIT | raw video + frame rows → **fresh** PREPARED/RGB/labels/K | REUSE (code only; fresh output) | frozen | prepare one fresh video; labels ⊂ {0,1,2}, K 3×3 |
| Uniform real-frame densification | **none** | **no committed reusable entrypoint** | raw video + coverage gaps → new real frames + PREPARED identities | **GAP** | GAP | must be implemented and approved before use |
| Ring CAD | `rf-native-ring-cad@2` | `native/camera.py::torus_contours` | c2w/K/R5|R10 → inner/outer curves | REUSE | frozen | R5=3.1/0.6; R10=5.6/0.6 |
| Tracks + local Ring BA + W0 | `rf-frozen-tracks005@1`; `rf-frozen-ba-local-ring-sfm@1`; `rf-w0-camera@2` | `tools/run_w0_camera.py` | PREPARED/tracks/Ring → B0/W0/camera_result/admission | REUSE | frozen, coverage **NOT_MET** | G03/005 regression; W0 manifest |
| Camera admission / local pool | unregistered candidate | `src/ring_first_3d/views/pipeline_adapter.py::admission_tiers` | W0 metrics + graph + trajectory → local pool | ADAPT | candidate, **not approved** | `tests/test_m2f3_convergence.py` |
| Current-data anchor / geometric center | unregistered; M2F2 function uses historical INITIAL fallback | `tools/m2f2_unified.py::model_center` | frame geometry → anchor | **GAP** | exploring | requires a current-data-only proof |
| T10 target selection | unregistered | `views/selection.py::select_views(strategy='quality_diversity')` | admitted pool → targets | ADAPT | candidate | no fixed frame/anchor; full 8 |
| T11 direction quota | unregistered | `views/selection.py::select_views(strategy='direction_quota')` | same pool → control targets | ADAPT; **not formal** | candidate | T11 control only |
| T13 support selection | unregistered | `coverage.py::support_pairs` via `select_views(strategy='hero_support')` | target + pool + SIFT/K → 3 supports + scores | ADAPT | candidate | historical T13 + geometry gate |
| Official HERO | unregistered | `native/hero.py::infer` | target+3 supports → native depth/mesh | ADAPT | candidate; 4/4 bitwise historical | M2D historical regression |
| Raw metric mesh | unregistered | `native/geometry.py`/HERO native mesh | depth → metric axial-Z mesh | ADAPT | candidate | native K/units |
| Historical cleaning | unregistered | `native/cleaning.py::classify_native` | raw mesh + CAD → conservative labels | ADAPT | candidate | protocol SHA + raw preserved |
| Standard A→B | unregistered | `reprojection.py::render/evaluate/make_figure` | source mesh + B K/pose + Ring → five-panel/metrics | ADAPT | candidate | use **B** camera; M2D sample |
| Six-view | unregistered | `native/_mesh_renderer.py::actual_mesh_image` | mesh + CAD + fixed bounds → six-view | ADAPT | candidate | true target/support + X/Y/Z |

**Formal composability:** blocked. The two required GAPs are dense real-frame sampling and current-data anchor generation. In addition, T10/T11/T13/HERO/cleaning/A-to-B/six-view are not registered/confirmed; they cannot be silently promoted.

## 2. Actual behavior of the four successful videos (M2F3, same code)

| Video | W0 source | S0/S1/S2 camera count | HERO | Why it succeeds |
|---|---|---:|---:|---|
| G01-005 | original W0/005 | 0/0/10 | 7 | S2 local pool; no S0/S1; T10/T13; no special code |
| G03-004 | original W0/004 | 0/8/10 | 12 | S1/S2; stable W0 |
| G03-005 | original W0/005 | 6/10/10 | 8 | S0 strict path and S1/S2 |
| G06-004 | 14-view recovery W0 | 8/12/14 | 21 | **non-reusable ad-hoc 4-frame recovery**; not a confirmed route |

Needs improvement: G01-004 (0/5/10, 9 HERO; one −17.28 mm CAD-HERO outlier) and G06-005 (0/3/10, 5 HERO). These are observed, not used to alter the method.

## 3. Proposed single main line (requires approval)

```text
raw video + INIT + raw mask
→ uniform real-frame sampling/densification        [GAP]
→ fresh prepare/preprocess                           [frozen code, fresh output]
→ Ring-First + RGB + BA / W0                         [frozen]
→ ONE tolerant local candidate pool                  [candidate]
→ current-run geometric anchor                       [GAP]
→ T10 target selection                               [candidate]
→ T13 support selection + real four-camera check      [candidate]
→ official HERO                                      [candidate/unregistered]
→ native metric mesh                                 [candidate]
→ historical conservative cleaning                  [candidate]
→ six-view + standard B-camera A→B                   [candidate]
```

Not allowed in the main line: historical PREPARED, historical W0/poses, historical anchors/INITIAL, historical HERO/mesh, fixed 79 list, S0/S1/S2 parallel *formal* arms, T11 formal route, group-specific sampling.

## 4. Audits/branches to cancel

- S0/S1/S2 as three parallel formal reconstruction products; keep S0 only as a diagnostic baseline, not a formal output.
- T11 as a formal parallel target route; retain only as a control.
- Historical `VIEW_SELECTION_016` anchors and historical INITIAL-dependent center.
- Historical W0/PREPARED/HERO results as inputs (read-only comparison only).
- Any quality gate not required by the algorithm (complex trajectory-quality audit, duplicate acceptance metrics).
- Keep basic correctness: identity, K/c2w/units, finite SE(3), real inputs, required T13 geometry.

## 5. Proposed changes (NOT YET WRITTEN)

- **GAP-1**: add a single reusable real-frame densification entrypoint based on `prepare_view` + `run_w0_camera`; it must create fresh identities and distinguish `RAW_LABEL_NOT_DXY_CLEAN` from formal DXY clean. No algorithm substitution.
- **GAP-2**: add a current-run data-only geometric center/anchor implementation; no historical INITIAL dependency.
- **ADAPT**: one glue entrypoint around `prepare_m1_inputs`/`run_w0_camera`/`selection.select_views`/`hero.infer`/`cleaning.classify_native`/`reprojection`/`_mesh_renderer`.
- **REGISTER**: only after human approval and smoke tests; candidate routes promoted individually with evidence.
- No core HERO/geometry/cleaning/reprojection rewrite and no group-specific code.

## 6. Proposed 10 generalization groups

These are outside the M2F3 3 groups and exist in the 39-group manifest:

```text
GP_IIa_5.2mm_closed_R10_single_refY
GP_IIa_9.5mm_closed_R5_single_refY
GP_IIa_22.0mm_closed_R5_single_refY
GP_Ip_4.0mm_closed_R5_single_refY
GP_Ip_6.2mm_closed_R10_single_refY
GP_Ip_8.8mm_closed_R5_single_refY
GP_Ip_12.0mm_closed_R5_single_refY
GP_Is_10.5mm_closed_R10_single_refY
GP_Is_14.0mm_closed_R5_single_refY
GP_Is_18.0mm_closed_R5_single_refY
```

They cover Ip/Is/IIa, R5/R10 and multiple sizes. This list is frozen before any reconstruction; no post-result substitution.

## 7. Stop condition

No integration source, no new route promotion, no 13-group run was performed. Human decision required on:

1. approving the two GAPs and their implementation/validation;
2. promoting or rejecting each candidate route;
3. approving the one-pool main line (and retiring S0/S1/S2 parallel products and T11 formal route);
4. confirming the 10-group list.

Until then, this task is **BLOCKED AT ROUTE COMPOSITION**.
