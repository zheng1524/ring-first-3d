# W0 blocker root cause

- Prior M2F1 pipeline did not call A2 candidate recovery/BA; W0_BRANCH_REPAIR was false.
- Track audit: Is9.79/004 max_id=161 vs track_count=126; Is10.5 R5/005 mismatch.
- Recompute Is9.79 W0 stopped at RING_POSE_GRAPH_DISCONNECTED.
- No truncation/modulo or historical camera substitution was used; Is9.79 remains conditional.
- No valid A2 candidate+BA call exists in the current implementation; this remains NOT_EXECUTED, not scientific failure.
