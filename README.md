# Ring-First 3D · Human-in-the-loop research collaboration

Status: **PHASE_D_RESEARCH_AUTHORIZED** · Collaboration standard: **v1.3** · No certified 3D algorithm baseline has been imported.

Researcher authorization: [TASK-PHASED-MAIN-SURFACE-CROSSVIDEO-001](experiments/TASK-PHASED-MAIN-SURFACE-CROSSVIDEO-001/TASK.md). This task may use frozen legacy assets/source read-only, wrap them, and make necessary bounded copies. Full migration and a baseline tag are not prerequisites. Frozen upstream models, cameras, P0, Dxy and GT restrictions remain in force.

This repository is for incremental Codex-produced reproducible source, configurations, diagnostics, curated visuals and one technical report per task. RA and PM collaborate through human-relayed prompts and reports; they are not required to write GitHub.

Canonical technical path: Ring-First camera pose → MVSAnywhere HERO depth → open metric Polyp/Ring/local tissue scene → 3D-derived metrics.

Read `COLLAB_STANDARD_v1.3.md` and `AGENTS.md`. Old sources and large raw assets remain LOCAL_ONLY pending reviewed selective baseline import. Do not infer current code state from legacy `polyp-resarch` Git HEAD.

Approved visualization utility: [fixed real P0 renderer](visualization/README.md), with its own dependencies and provenance. This selective mainline import contains raw point visualization only; experimental point cleanup and scientific algorithm baselines are not imported.

Current Phase-D task: **REPORTED — NOT FUSED; awaiting human acceptance**. [Technical report](experiments/TASK-PHASED-MAIN-SURFACE-CROSSVIDEO-001/TECHNICAL_REPORT.md) · [four real figures and local GLB index](experiments/TASK-PHASED-MAIN-SURFACE-CROSSVIDEO-001/RESULT_INDEX.md) · [reproduction](experiments/TASK-PHASED-MAIN-SURFACE-CROSSVIDEO-001/REPRODUCE.md). Both single-video scenes preserve source layers; the cross-video transform is a diagnostic candidate. No scientific baseline acceptance or mainline algorithm merge is implied.

Current incremental task: **REPORTED — EXPERIMENTAL / ASSET LIMITED; awaiting human acceptance**. [Technical report](experiments/TASK-PHASED-INCREMENTAL-FUSION-MULTIGROUP-001/TECHNICAL_REPORT.md) · [four-group review figures and local gallery/model index](experiments/TASK-PHASED-INCREMENTAL-FUSION-MULTIGROUP-001/RESULT_INDEX.md) · [reproduction](experiments/TASK-PHASED-INCREMENTAL-FUSION-MULTIGROUP-001/REPRODUCE.md). Four physical groups were processed; only G01 has multiple references. Cleaning candidates were not adopted, height support is conditional, and projected diameter remains NOT_EVALUABLE. Formal Dxy and frozen upstream assets remain protected.

Current observability/GT audit: **REPORTED — SHAPE SCALARS CONDITIONAL; awaiting human acceptance**. [Technical report](experiments/TASK-VIEW-OBSERVABILITY-GT-EVAL-001/TECHNICAL_REPORT.md) · [four core figures and full local HTML index](experiments/TASK-VIEW-OBSERVABILITY-GT-EVAL-001/RESULT_INDEX.md) · [research handoff](experiments/TASK-VIEW-OBSERVABILITY-GT-EVAL-001/research/TOP_LEVEL_RESEARCH_HANDOFF.md). Four original Blender shapes were verified, 27 frozen height and 81 diameter conditions retained, and 22 source-only cross-view projections audited. No new reconstruction or fusion was performed. Cross-video/photo poses remain candidates, and formal 3D projected diameter remains NOT_EVALUABLE.
