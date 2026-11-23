# EXECUTION_DEFECT_REGISTER（028-CORRECTIVE）

| # | 问题 | 证据 | 修复 |
|---|---|---|---|
| D1 | 历史 `ring020_026` 的模块级 `R`/`VIEWS` 在多视频写入时被覆盖 | KeyError `'G03_key02_raw00327'` | 全部视角一次写入 VIEWS.json；每组单 renderer |
| D2 | ring 证据写入 `runs/<G>/ring`，而历史模块从 `R/ring` 读取 | FileNotFoundError | `rep/ring -> runs/<G>/ring` symlink |
| D3 | `cams` 含未载入 RingRenderer 的视角 | KeyError `'G03_v005_raw00085'` | 选择后把 `cams` 限制到选中视角 |
| D4 | BA geometry 用 `role[ref]=='005'` 判断取相机 | KeyError | 改为按视图所属视频取 |
| D5 | `fixed_track_tri` 在 sys.path 设置前导入 | ModuleNotFoundError | 移到 `sys.path` 之后 |
| **D7** | `epipolar_score(fit_ids)` 与 `r.ref_index` 空间不一致 | `H_CANDIDATES.csv` 的 `epi` 全空、score=1e6+ring | **未修** |
| **D8** | W0 自动补算未做删除缓存演练 | 无 `w0/w0_*.log` 复算记录 | **未验证** |
| D9 | G03/G06 进程被会话预算终止 | 无 SUMMARY / BA npz | 未完成 |
