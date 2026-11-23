> **M1 consolidation note (2026-11-23):** the authoritative route inventory is
> `docs/registry/routes.yaml`. `registry/routes.yaml` is legacy and read-only;
> `tools/registry_check.py` still reads it until the Round 2 validator migration.
> There must not be two independently maintained route registries.

# Registry (auto-generated view)

**本文件为 registry 的 legacy 快照。** M1 后的权威 Route Registry 是 `docs/registry/routes.yaml`；`registry/components.yaml` 与 `registry/routes.yaml` 保留为历史只读输入，等待 Round 2 validator 迁移。

| route_id | component | version | status | manifest | reproduction |
|---|---|---|---|---|---|
| ring-cad-inner-outer | dxy_ring_observation | 1 | candidate | runs/ring-cad-inner-outer-v1/manifest.yaml | PENDING_INDEPENDENT_REPRODUCTION |
| cam-ring-rgb-joint | camera_ring_rgb | 1 | exploring | — | not_started |

状态机：`exploring → candidate → confirmed → frozen`（另有 `rejected / deprecated`）。
只有独立接收组在干净环境复现后才能升 `confirmed`；`frozen` 需人工批准。
