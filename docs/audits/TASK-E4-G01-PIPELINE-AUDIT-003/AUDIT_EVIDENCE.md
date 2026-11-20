# AUDIT_EVIDENCE

本文件记录审计中**两个关键复算**的完整方法与可复现命令。所有复算**只读**，在内存中完成，不写回任何冻结产物。

环境：`/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python`（工作区既有解释器，未新建环境）。

---

## E1. G03/005 的 Body 投影在 v0 / v1 两套相机下的对比

**目的：** 证明"Ring 通过但 Body 不投影"是**相机版本选择**造成，而不是 Body 形态问题。

**输入（均为已冻结文件，未修改）：**
- Body：`runs/RF_ONLY_V1/G03/005/body/B1/FINAL.npz`（`V`,`F`）
- 相机：`runs/RF_ONLY_V1/G03/005/reference_build/REV1/predictions/NATIVE_CALIBRATION_{0,1}.npz`
- 视角与掩膜：`audit/SELECTED_VIEWS.json` 的 `cache` 路径（360×640，`labels`,`K`）

**方法：** 按 `native/geometry.project` 的约定 `q=(V−t)@R`、`uv=(q@K.T)[:2]/z`，对每个三角面做 `cv2.fillPoly` 得到剪影，与 `labels==1` 求 IoU。**这是粗略光栅化**（不做遮挡与深度测试），故数值略高于流水线自报值（0.238），但两版本之间的差距是结论所在。

**实测结果：**

| 视角 | IoU@v0 | IoU@v1 |
|---|---:|---:|
| G03_v005_raw00070 | 0.1313 | 0.8335 |
| G03_v005_raw00589 | 0.1633 | 0.8493 |
| G03_v005_raw00402 | 0.7864 | 0.8361 |
| G03_v005_raw00373 | 0.7675 | 0.8269 |
| G03_v005_raw00561 | 0.1646 | 0.8493 |
| G03_v005_raw00474 | 0.1507 | 0.8499 |
| G03_v005_raw00099 | 0.1337 | 0.8267 |
| G03_v005_raw00546 | 0.1641 | 0.8440 |
| **均值** | **0.3077** | **0.8395** |

**可复现命令：**

```bash
cd /home/liu/ring_first_3d_workspace/experiments/TASK-E4-UNIFIED-PIPELINE-COMPLETION-002
/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python - <<'PY'
import numpy as np, json, cv2
views={v['meta']['id']:v for v in json.load(open('audit/SELECTED_VIEWS.json'))}
def sil_iou(C,K,V,F,labels):
    q=(V-C[:3,3])@C[:3,:3]
    z=q[:,2]; uv=(q@K.T)[:,:2]/np.where(abs(z)>1e-9,z,1)[:,None]
    m=np.zeros(labels.shape,np.uint8)
    for f in F:
        if not np.all(z[f]>1e-6): continue
        cv2.fillPoly(m,[np.rint(uv[f]).astype(np.int32)],1)
    gt=(labels==1).astype(np.uint8)
    return int((m&gt).sum())/max(int(((m>0)|(gt>0)).sum()),1)
run='runs/RF_ONLY_V1/G03/005'
body=np.load(f'{run}/body/B1/FINAL.npz'); V,F=body['V'],body['F']
cams={v:dict(np.load(f'{run}/reference_build/REV1/predictions/NATIVE_CALIBRATION_{v}.npz'))['c2w'] for v in [0,1]}
ids=list(dict(np.load(f'{run}/reference_build/REV1/predictions/NATIVE_CALIBRATION_0.npz'))['ids'])
for v,x in views.items():
    if x['meta']['case']!='G03' or x['meta']['video']!='005' or x['meta']['role']!='FIT': continue
    c=np.load(x['cache']['path']); i=ids.index(v)
    print(v, round(sil_iou(cams[0][i],c['K'],V,F,c['labels']),4),
             round(sil_iou(cams[1][i],c['K'],V,F,c['labels']),4))
PY
```

**补充证据（不依赖渲染）：**
- 两版本相机相对旋转：174.10°–179.42°（逐视角）。
- `CALIBRATION_RING_DIAGNOSTIC.json`：`center_spread_mm` = 64.73 / 60.28 mm（仅 raw00373 / raw00402），其余 1.27–2.26 mm。
- `LOCAL_CALIBRATION_RUNS.json`：v0 `local_BA.success=False`，`nfev=60`；v1 `success=True`，`nfev=46`。
- `bootstrap_references.py:85`：`primary=min(poses)` → 选 v0。

---

## E2. HERO 深度与相机距离的尺度一致性扫描

**目的：** 量化"HERO 深度是否与 Ring-First 相机给出的公制尺度自洽"。

**指标：** `median(depth_mm where >0) / ||c2w[:3,3]||`。场景尺度约 40 mm，正常应为 ~1。

**实测（40 个已求解视角，全量）：**

| 视角 | HERO 深度中位 (mm) | 相机 \|t\| (mm) | 比值 |
|---|---:|---:|---:|
| G03_v005_raw00373 | 1060.8 | 41.7 | **25.41** |
| G03_v005_raw00402 | 246.6 | 40.3 | **6.11** |
| G03_v005_raw00070 | 83.1 | 43.6 | 1.91 |
| …（其余 37 个） | — | — | 中位 1.03，p90 1.61 |

**对照（版本 v1 下的目标-支持相机间距）：**
- `raw00373`：v0 为 61.0/60.1/60.2 mm；v1 为 6.7/13.4/13.5 mm。
- `raw00402`：v0 为 57.9/4.0/58.9 mm；v1 为 12.4/2.8/4.8 mm。

**可复现命令：**

```bash
cd /home/liu/ring_first_3d_workspace/experiments/TASK-E4-UNIFIED-PIPELINE-COMPLETION-002/runs/RF_ONLY_V1
/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python - <<'PY'
import numpy as np, json, glob, os
for hp in sorted(glob.glob('*/*/hero/*/SOURCE.json')):
    v=os.path.dirname(hp); group,video=hp.split('/')[0],hp.split('/')[1]
    vid=os.path.basename(v)
    cam=f'{group}/{video}/camera/{vid}/CAMERA_RESULT.json'
    if not os.path.exists(cam): continue
    d=np.load(f'{v}/HERO_native.npz')['depth_mm']; med=float(np.nanmedian(d[d>0]))
    dist=float(np.linalg.norm(np.array(json.load(open(cam))['c2w_mm'])[:3,3]))
    print(f'{group}/{video}/{vid:28s} depth={med:8.1f} cam={dist:6.1f} ratio={med/dist:6.2f}')
PY
```

**结论边界：** 数据只能证明"深度与相机尺度不一致且未被门禁拦截"，**不能证明**成因是相机还是模型——后者需重跑官方推理，属下一任务。

---

## E3. 参考库来源分布

按 `runs/RF_ONLY_V1/*/*/bank/ADMISSION.json` 的 `execution` 字段统计：

| execution | 实例 | 地标数 |
|---|---|---:|
| `FROZEN_REFERENCE` | G01/004, G03/004, G05/004, G06/004 | 8 / 6 / 8 / 7 |
| `NEW_BUILD_OR_RECOVERY` | G01/005, G02/004 | 980 / 125 |
| `MATURE_G01_NATIVE_REFERENCE_BUILD_REV1` | G02/005, G03/005, G05/005, G06/005 | 230 / 145 / 107 / 52 |

---

## E4. Body 更新有效性

`runs/RF_ONLY_V1/<G>/<v>/body/<arm>/{INITIAL,FINAL}.npz` 的顶点欧氏距离：

| 实例 | B1 max (mm) | B2 max (mm) | 已接受步数(B1) |
|---|---:|---:|---:|
| G01/005 | 0.633112 | 0.565624 | 20/36 |
| G02/004 | 0.092045 | 0.143587 | 13/36 |
| G02/005 | **0.000016** | **0.000018** | 9/36 |
| G03/005 | 0.462125 | 0.087598 | 11/36 |
| G06/005 | **0.000026** | **0.000027** | 9/36 |

---

## E5. V6 跨视频对齐（不是本轮计算，是读取历史冻结产物）

`/home/liu/polyp_research/ring_anchor_3d/experiments/ring_first_v6_local_reconstruction/metrics/alignment005_to004_disjoint.json`：

```
accepted = false
status   = MODEL_PREDICTED_ALIGNMENT_ONLY
method   = whole-scene Ring-axis rotation plus normal-sign branch, no ICP or scale correction
alpha_deg = -88.8988
held_005_to004 = {n:188, median:8.832, MAE:9.165, p95:14.495}
held_004_to005 = {n:5, median:5.102, MAE:41.912, p95:110.917}
```

---

## E6. 源码同源性比对

`native/_kernels.py` 的 `decode` / `image_seeds` / `solve` 与
`polyp_research/ring_anchor_3d/experiments/ring_pose_contact_v1/scripts/recover.py` 同名函数：

```
decode          IDENTICAL
image_seeds     IDENTICAL
solve           IDENTICAL
```

比对方式：`ast.get_source_segment` 抽取函数源码后 `strip()` 字符串比较。

**已知差异：** 调用方配置不同——V6 `prepare_ring.py` 用 `seed_retain=4, max_nfev=100`；`native/camera.py:16` 的 `RF_CONFIG` 用 `seed_retain=2, max_nfev=35`。
