# M2F7 V6 BA First-Difference Audit

## Method

Historical V6 artifacts and the new RAW run were compared read-only, in this order:

`tracks/pairs → Ring observations → initial cameras → triangulated training points/IDs → BA initial residual → BA output → validation`

No solver, threshold, config or input was changed. `V6_STAGE_DIFFERENCES.csv` contains all 527 array-level comparisons.

## First difference

| Stage | Array | Max difference | Interpretation |
|---|---|---:|---|
| tracks/pairs | all arrays | **MATCH** | same feature identities/NaN pattern |
| Ring observations | all 22 × all keys | **MATCH** | same observations |
| initial cameras v0 | `c2w` | **3.128e-8** | first non-identical numeric stage |
| initial cameras v1 | `c2w` | **2.421e-8** | same |
| triangulated points v0 | `X` | **1.448e-6 mm** | propagates from initial float difference |
| BA initial residual v0 | norm | **3.10e-8** | effectively identical |
| BA initial residual v1 | norm | **1.55e-8** | effectively identical |
| BA output v0 | `c2w` / `points` | **0.01182 mm / 0.894 mm** | first material divergence |
| BA output v1 | `c2w` / `points` | **3.272 mm / 7.422 mm** | first material divergence |
| validation v0 | VALIDATED | **15 → 8** | downstream consequence |

**Earliest numeric difference:** `local005_initial_*:c2w`, at 3e-8.  
**Earliest material difference:** BA output, after an effectively identical initial residual.

## Solver evidence

| version | run | nfev | training_soft_l1_objective | VALIDATED |
|---|---:|---:|---:|---:|
| v0 | historical | 60 (budget limit) | 0.1485259255 | 15/22 |
| v0 | raw formal (threads unset) | 45 (converged) | 0.1494521492 | 8/22 |
| v0 | raw, `OPENBLAS/OMP=1` audit | 60 (budget limit) | 0.1484100458 | 8/22 |
| v1 | historical | 60 | 0.1939723934 | 0/22 |
| v1 | raw formal | 60 | 0.1938132225 | 0/22 |
| v1 | raw, `OPENBLAS/OMP=1` audit | 12 | 0.2580064943 | 0/22 |

Historical V6 reproduction instructions require `OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1`. Setting them changed v0 from 45 to 60 iterations and made the objective closer to historical, but **did not restore 15/22**; version 1 changed to 12 iterations. Therefore BLAS threading is a contributing environment difference, not a complete explanation.

## Current environment

`Python 3.12.13`, `scipy 1.15.3`, `numpy 2.4.6`, `opencv 4.11.0`. The historical run did not persist a complete package/environment manifest; this remains an unresolved environmental factor.

## Conclusion

The upstream data is exact. The first material divergence is the BA optimization path: version 0 hits 60 historical iterations versus 45 formal-run iterations; version 1 shows a different local optimization. The current evidence supports **BA numerical/environment sensitivity**, not a tracks/Ring/input difference. It is not sufficient to attribute the 15→8 change to a specific reproducible parameter; no parameter was tuned to force 15/22.
