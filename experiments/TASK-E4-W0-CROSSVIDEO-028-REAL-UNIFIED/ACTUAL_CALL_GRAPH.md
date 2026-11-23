# ACTUAL_CALL_GRAPH

```
core/u028.py --group G
 ├─ videos_of()          prepared/{G}_*
 ├─ discover()           camera_mainline/G/video* 或 runs/G/video*/camera_result.npz
 ├─ ring_evidence()      dxy_mid._engine.ring_component.recover  (历史)
 ├─ build_renderer()     ring020_026.RingRenderer  (历史, R 指向本组)
 ├─ ring_scores()        M/I/C/O per view
 ├─ features019.features/landmarks   (历史)
 └─ features019.match_desc           (历史)  -> IDENTITIES.csv / SPLIT.json
tests/test_u028_contracts.py          3/3（无组分支、无冻结准入、H 一次）
```
