# M2F8 Shared RAW Diagnostic Manifest — PLANNED

**Status: NOT EXECUTED. This is a pre-registration, not a result manifest.**

## Planned common input (G01-005)

- Raw video: `GP_Ip_12.0mm_closed_R10_single_refY_005.mp4`
- Raw SHA-256: `1d56e7890cf46364d0138007e559d5d77bb2919510b73a5b62e68ce964a9c86d`
- Frames: one pre-frozen set from the current M2F6 2D candidates, not historical V6 22-frame identities.
- Each frame must have fresh RGB/Mask/K and hashes; no historical PNG/camera/Ring/hero/mesh.
- Target and three Support identities must be frozen before any HERO result is read.

## Planned controls

| Experiment | Camera source | Support source |
|---|---|---|
| A | V6-GENERALIZED | V6 selection |
| B | CURRENT-M2F6 | V6 selection |
| C | V6-GENERALIZED | T13 selection |
| D | CURRENT-M2F6 | T13 selection |

A/B and C/D must use exactly the same Target and four RGB/Mask/K arrays. No camera can be borrowed from another route. If one tuple is not legal, write `NOT_COMPARABLE` and do not substitute.

## Blockers

- R5 V6 Ring adapter GAP (for Is14/Ip8.8).
- No common input frozen yet.
- HERO adapter equivalence not tested.
- No B/C/D execution authorized in this phase.
