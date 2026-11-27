# R1 storage audit cleanup implementation plan

> **For agentic workers:** Execute this plan inline. The user explicitly authorized the audit cleanup and removal of the blanket `polyp_research` protection.

**Goal:** Reclaim space from exact files in `TASK-V6-R1-STORAGE-REAUDIT-001/PROPOSED_FILES.csv.gz` while preserving active R1 dependencies and producing restartable receipts.

**Architecture:** Use the shared maintenance lock for manifest publication and deletion. Replace the blanket `polyp_research` guard with the audit's explicit active dependency guards. Release small exact-file batches; compare current file identity and hash before unlink, record each result atomically, and measure actual free space.

**Tech Stack:** Python 3 standard library, `flock`, `sha256sum`, `statvfs`, `df`, audit CSV/JSON.

---

### Task 1: Freeze input and protection

**Files:** Audit `PROPOSED_FILES.csv.gz`, `evidence/ACTIVE_DEPENDENCIES.json`; shared `PROTECTED_ASSETS.json`.

- [ ] Verify audit SHA `41cb5d2aedb0a8c71a44fed2d46ed13fe59253230f0824ae786fc8b39172ec69` with `sha256sum`.
- [ ] Under `maintenance.lock`, remove only the blanket `/home/liu/polyp_research` entry and add the audit's active protected directories and files. Record old and new manifest SHA.
- [ ] Verify current HERO/INIT checkpoint paths and protected anchors remain readable.

### Task 2: Execute old method weight batch

**Files:** Exact 12 audit rows with `PROPOSE_RETIRE_OLD_METHOD_WEIGHTS` or `PROPOSE_RETIRE_DOWNLOAD_FRAGMENTS`; shared release, receipt, and report.

- [ ] Publish a READY release containing the 12 absolute paths, realpaths, sizes, SHA256, reasons, audit reference, and current protected manifest SHA.
- [ ] Before unlink, check each regular file's path, size, SHA256, active protection, and open file state; write RUNNING receipt atomically.
- [ ] Unlink only verified files, update each result atomically, then record protected checks and `df` before/after in COMPLETE receipt.

### Task 3: Continue eligible audit categories

**Files:** Same audit CSV; new releases and receipts.

- [ ] Select only files whose category conditions are evidenced and whose current identity matches the audit. Keep raw media, GT, active inputs, unclassified rows, and migration gated rows.
- [ ] For duplicates, recheck retained copy hash and Git blob; for geometry, require complete metric and retired consumer evidence.
- [ ] Execute additional exact-file batches with the same lock and receipt rules. Record every skip.

### Task 4: Report and verify

**Files:** `runs/v6_r1_split_handoff_001/CLEANUP_REPORT.md`; `experiments/TASK-V6-R1-STORAGE-CLEANUP-A-001/TECHNICAL_REPORT.md`.

- [ ] Report logical bytes, attributable allocated block recovery, `df` delta, current free bytes, and concurrent-write caveat separately.
- [ ] Recheck active protected anchors, release and receipt SHA linkage, and remaining pending batches.
- [ ] Commit only small plan, scripts, and reports on an isolated cleanup branch; do not stage unrelated dirty files or large assets.
