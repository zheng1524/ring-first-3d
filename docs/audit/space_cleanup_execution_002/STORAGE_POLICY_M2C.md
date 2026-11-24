# STORAGE_POLICY_M2C

1. Cache key = input RGB/mask hashes + frame IDs + K + relative poses + model/source version. Identical keys share one result.
2. Never save duplicate XYZ if it can be losslessly regenerated from retained depth + camera + K.
3. Keep group-level temporary outputs; publish only final/compact results.
4. Retain: formal W0/camera results, frozen configs/manifests, independent holdout, failure evidence, representative visualizations.
5. Stop launching new compute batches when free space is below the agreed threshold (target 20 GiB; full 3-arm HERO target 30–35 GiB).
6. Do not auto-delete research assets after a failed run. Mark failed outputs and require human approval.
7. HERO reuse is allowed only for byte-identical input tuples; a camera/BA change invalidates old depth.
8. Keep at least one protected original copy of raw data/weights outside any cleanup candidate.
