# Ring-First 3D · Human-in-the-loop research collaboration

Status: **PHASE_D_RESEARCH_AUTHORIZED** · Collaboration standard: **v1.3** · No certified 3D algorithm baseline has been imported.

Researcher authorization: [TASK-PHASED-MAIN-SURFACE-CROSSVIDEO-001](experiments/TASK-PHASED-MAIN-SURFACE-CROSSVIDEO-001/TASK.md). This task may use frozen legacy assets/source read-only, wrap them, and make necessary bounded copies. Full migration and a baseline tag are not prerequisites. Frozen upstream models, cameras, P0, Dxy and GT restrictions remain in force.

This repository is for incremental Codex-produced reproducible source, configurations, diagnostics, curated visuals and one technical report per task. RA and PM collaborate through human-relayed prompts and reports; they are not required to write GitHub.

Canonical technical path: Ring-First camera pose → MVSAnywhere HERO depth → open metric Polyp/Ring/local tissue scene → 3D-derived metrics.

Read `COLLAB_STANDARD_v1.3.md` and `AGENTS.md`. Old sources and large raw assets remain LOCAL_ONLY pending reviewed selective baseline import. Do not infer current code state from legacy `polyp-resarch` Git HEAD.

Approved visualization utility: [fixed real P0 renderer](visualization/README.md), with its own dependencies and provenance. This selective mainline import contains raw point visualization only; experimental point cleanup and scientific algorithm baselines are not imported.

Current Phase-D task: **REPORTED — NOT FUSED; awaiting human acceptance**. [Technical report](experiments/TASK-PHASED-MAIN-SURFACE-CROSSVIDEO-001/TECHNICAL_REPORT.md) · [four real figures and local GLB index](experiments/TASK-PHASED-MAIN-SURFACE-CROSSVIDEO-001/RESULT_INDEX.md) · [reproduction](experiments/TASK-PHASED-MAIN-SURFACE-CROSSVIDEO-001/REPRODUCE.md). Both single-video scenes preserve source layers; the cross-video transform is a diagnostic candidate. No scientific baseline acceptance or mainline algorithm merge is implied.

Current incremental task: `TASK-PHASED-INCREMENTAL-FUSION-MULTIGROUP-001` — RUNNING under the researcher's explicit new task. Four-group diagnostics, frozen cleaning reuse and source-traceable local fusion only; formal Dxy and upstream assets remain protected.
