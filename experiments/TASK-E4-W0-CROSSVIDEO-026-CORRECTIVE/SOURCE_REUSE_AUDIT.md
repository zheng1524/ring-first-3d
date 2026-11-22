# SOURCE_REUSE_AUDIT

| 历史模块 | 提交 | 本轮用途 | 是否修改 |
|---|---|---|---|
| `020/ring020.py` | `5636aae` | `RingRenderer`/`CADCurves` | 复制为 `replay/ring020_026.py`，**仅 2 行**路径 → 环境变量 |
| `019/features019.py` | `5636aae` | 三角化敏感性（复用 026 已生成的基线/扰动地标） | **未改** |
| `019/ring019.py` | `5636aae` | 通过其调用的 `dxy_mid._engine.ring_component.recover` 生成真实 centerline | 代码**未改**；以相同调用方式重跑 |
| `020/features020.py` | `5636aae` | 本轮未用（身份沿用 025） | — |

依赖：`scikit-image`（DXY `_engine` 需要）本轮安装到项目 venv；`pytorch3d`/`open3d` 沿用。
未修改 W0、DXY、HERO、Body、Ring CAD；未覆盖 026 原始文件。
