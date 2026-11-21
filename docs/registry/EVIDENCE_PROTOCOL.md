# Evidence protocol proposal from forensic audit002

This is a versioned infrastructure proposal. It does not silently promote any Failure Registry entry into a permanent scientific rule or alter the Research Policy Runner.

Each new important task should have immutable EVIDENCE.json with task_id; per-file source snapshot commit/path/SHA; actual execution commit or SOURCE_COMMIT_UNVERIFIED; separate publication commit; fixed input identities and data roles; prediction freeze and independent evaluator first-GT-access; output paths/SHA; metric definitions/denominators/alignment frame; visualizations; failures including invalid/NaN outcomes; dependencies/ABI; engineering and scientific statuses. A resumed stage retains its original code/input/run identity. A current HEAD or later report commit never proves original execution.

Legacy reports retain original bytes and SHA. Sidecars and canonical navigation can repair links with provenance-backed original document/repository context; missing assets and unresolved templates remain explicit. Basename-only or geometric/visual resemblance never proves identity. Link statuses are VALID, BROKEN_TARGET, MISSING_ASSET, MOVED_TARGET, EXTERNAL_DEPENDENCY, UNRESOLVED.

Full forensic CSV.gzip is the portable metadata export; SQLite is an optional LOCAL_ONLY index. For multiline duplicate-path groups, use csv.field_size_limit with a sufficient limit before streaming. HASH_INHERITED binds the exact provenance of an existing computed hash; current audit uses only stable same-scan inode inheritance. A symlink hash covers the link text, never implied target payload. Root scan scope, actual Git ownership and external runtime dependencies are distinct. Classification UNIQUE_* labels are protective hypotheses until origin/role review, not deletion authority.

Future retirement requires separate user authorization, independent per-object review, dirty/untracked/ignored/unique asset preservation, Git refs/reflogs/unreachable-object preservation, explicit runtime/data rebinding and successful isolated cold restore. Clean status or pushed commits alone never establish data recoverability. This audit executes no retirement.
