# Engineering gate evidence

INIT_A_001 stopped at inita_regression, before any scientific prediction. All 130 tests ran; test_source_sha_cannot_drift was rejected with GT_LEAK instead of SOURCE_SHA because YAML key sorting caused the valid evaluator-only metadata asset to be hashed before the intentionally corrupted sources binding. External regression passed without the trusted worker I/O guard, so this ordering issue was only exposed by the actual Runner.

Fix: verify sources/code-lock SHA before parsing or checking later evaluator-only assets. No scientific setting, optimizer, test assertion or permission was weakened. The complete failed attempt and FREEZE remain in INIT_A_001; a new INIT_A_002 reruns all prerequisite gates under the corrected source fingerprint.
