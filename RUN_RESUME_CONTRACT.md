# M2F7 Long-Run Evidence Contract

## Run identity

Every new run must have one immutable `run_id` of the form:

```text
{METHOD}-{GROUP}-{VIDEO}-{UTC_TIMESTAMP}-{SHORT_RANDOM}
```

The run directory is `runs/<task>/<run_id>/`; it must never reuse another run's directory. Existing `HIST-V6-G01-005-RAW-001` and `M2F6-UNIFIED-OBSERVATION-001` are preserved as executed; this contract is for subsequent runs.

## `RUN_STATE.json`

Required fields:

```json
{
  "run_id": "HIST-V6-...",
  "route_id": "rf-m2f7-hist-v6@1",
  "code_commit": "full git SHA",
  "config_sha256": "...",
  "parent_run_id": null,
  "stages": [
    {"stage": "input", "status": "completed",
     "input_sha256": "...", "output_sha256": "...",
     "command": "...", "started_utc": "...", "finished_utc": "..."}
  ]
}
```

## Resume rule

A run may resume only when all of the following are true:

1. `run_state.run_id` equals the requested run_id;
2. `code_commit` and `config_sha256` match the current checkout/config;
3. every completed stage's output path exists and matches `output_sha256`;
4. the next stage's input SHA equals the preceding stage's output SHA;
5. no historical V6/V5 intermediate appears in the input lineage.

Otherwise create a new run_id and re-execute from the affected upstream stage. Never backfill, overwrite, or reconstruct an existing `RUN_TRACE`; the current `RUN_TRACE/` remains the raw execution record.

Validation command:

```bash
python tools/m2f7_run_guard.py --state runs/<task>/<run_id>/RUN_STATE.json --root runs/<task>/<run_id>
```
