# FUTURE_STORAGE_BUDGET — M2-C continuation and downstream

No large inference was launched for this estimate. It uses existing HERO result sizes, current W0/output sizes and file counts.

## Current / after cleanup

| State | Free space |
|---|---:|
| Now | 4.25 GiB |
| After Plan A | 10.27 GiB |
| After Plan B | 23.90 GiB |
| After Plan C (high risk) | ~47.8 GiB |

## Estimated requirements

| Stage | Working estimate | Notes |
|---|---:|---|
| W0 A2 candidate search + local repair | 2–4 GiB | 79 videos, candidates/BA diagnostics; current A1 work is only 24 MiB, candidate search will be larger |
| RGB bridge frames + matching cache | 2–5 GiB | 79 videos; reuse `features019`/tracks where tuple hash matches |
| HERO-S, 3 arms | 10–20 GiB | 79 × 4 targets × 3 arms = 948 target tuples; unique target/support tuples can be shared; existing 5-group HERO output ~0.51 GiB |
| Raw/Cleaned XYZ + Mesh | 3–6 GiB | per-target depth/XYZ/mesh; large surfaces can be compressed/grouped |
| Body initialization/update | 2–4 GiB | 79 videos, per-video body checkpoints/meshes |
| Multi-view visualization | 2–5 GiB | full-video sheets + selected high-res |
| Final evidence packages | 2–4 GiB | tables + selected images + W0/HERO/body manifests |
| **Peak during 3-arm run** | **25–45 GiB** | before deleting intermediate depth/mesh |
| **Long-term retained** | **10–20 GiB** | W0 tables/cameras, representative HERO/body, evidence |

## Recommendation

- Do **Plan A immediately** after approval → ~10.3 GiB: enough for A2/W0 continuation, not HERO.
- Do **Plan B selectively** after dependency checks → ~23.9 GiB: minimum for a staged single-arm HERO, not comfortable for all three arms.
- Before full 3-arm HERO + body + visualization, target **≥ 30–35 GiB free**; either:
  1. execute a reviewed subset of Plan C (legacy conda/.local, after proving current env independence), or
  2. run HERO arm-by-arm, keep only compact depth/metrics, and delete temporary XYZ/Mesh after each group acceptance.
- Preserve a **15–20 GiB safety margin**; root is already at 98%, so working at <10 GiB free risks failed writes and corrupted caches.

## Cache sharing rule

Cache key must include target/support frame IDs, RGB/mask hashes, intrinsics, relative poses, model hash and preprocessing version. Only byte-identical input tuples may share HERO output. Never reuse an old depth map after a camera/BA change.
