# 失败台账

失败保留，不以删除来源/GT选模/原生结果回填制造PASS。数值候选不是认证位姿。

| group | Body | accepted | total | reasons |
|---|---|---|---|---|
| G03 | Body-E | 0 | 18 | {'BODY_REGION_GEOMETRY_UNEXPLAINED': 18, 'BACKGROUND_HOLDOUT_CONFLICT': 3, 'RING_RASTER_WORSENING': 2, 'NEW_OR_WORSENED_HERO_RING_PENETRATION': 1} |
| G03 | Body-U | 0 | 18 | {'BODY_REGION_GEOMETRY_UNEXPLAINED': 17, 'NEW_OR_WORSENED_HERO_RING_PENETRATION': 7, 'RING_RASTER_WORSENING': 2, 'BACKGROUND_HOLDOUT_CONFLICT': 5} |
| G05 | Body-E | 0 | 16 | {'BODY_REGION_GEOMETRY_UNEXPLAINED': 16, 'BACKGROUND_HOLDOUT_CONFLICT': 4, 'NEW_OR_WORSENED_HERO_RING_PENETRATION': 2, 'RING_RASTER_WORSENING': 2} |
| G05 | Body-U | 7 | 16 | {'BODY_REGION_GEOMETRY_UNEXPLAINED': 2, 'BACKGROUND_HOLDOUT_CONFLICT': 5, 'RING_RASTER_WORSENING': 2, 'NEW_OR_WORSENED_HERO_RING_PENETRATION': 6} |
| G01 | Body-E | 10 | 26 | {'BODY_REGION_GEOMETRY_UNEXPLAINED': 8, 'NEW_OR_WORSENED_HERO_RING_PENETRATION': 4, 'BACKGROUND_HOLDOUT_CONFLICT': 9, 'INSUFFICIENT_INDEPENDENT_INFORMATION': 2, 'INSUFFICIENT_BACKGROUND_HOLDOUT': 1} |
| G01 | Body-U | 0 | 26 | {'BODY_REGION_GEOMETRY_UNEXPLAINED': 20, 'NEW_OR_WORSENED_HERO_RING_PENETRATION': 8, 'BACKGROUND_HOLDOUT_CONFLICT': 9, 'INSUFFICIENT_INDEPENDENT_INFORMATION': 2, 'RING_RASTER_WORSENING': 1, 'INSUFFICIENT_BACKGROUND_HOLDOUT': 1} |
| G06 | Body-E | 11 | 15 | {'BACKGROUND_HOLDOUT_CONFLICT': 4, 'RING_RASTER_WORSENING': 1, 'NEW_OR_WORSENED_HERO_RING_PENETRATION': 2} |
| G06 | Body-U | 6 | 15 | {'BACKGROUND_HOLDOUT_CONFLICT': 6, 'NEW_OR_WORSENED_HERO_RING_PENETRATION': 6, 'RING_RASTER_WORSENING': 2} |

## 控制与工程失败

- C1：刚体不能消除原射线加性深度造成的形态扭曲；未静默改为非刚性算法。
- C0 Body-U：0.156mm漂移，未通过预登记0.1mm；条件背景/Ring通过不等于正确。
- Body-E：G03半轴达到约20mm边界，G01/G05出现扁平解；保留有限预算结果，无HERO初始化补救。
- 首轮控制CAD轮廓子采样漏管截面、鲁棒化先后导致离群放大，已修复后全控制重跑；旧源码/结果在runtime/CONTROL_RING_AND_ROBUST_CONTRACT_FIX，不选旧版更好结果。
- 早期Body-E遗漏bounds调用、控制导入/拆分身份等实现错误均归档；真实定位开始前修复冻结。
- 图片SIFT几何有退化RANSAC异常时记录0匹配，不制造背景对应。
- 来源级派生相机允许原视频相对关系变化，不能等同正式轨迹恢复；真实绝对位姿、测量精度NaN/NOT_EVALUABLE。
- 真实相机/深度/Body/区域误配因果尚未完全可辨识；未获资格提案accepted_H=NaN，A0只独立对照。

## 逐来源失败

- 29份旧Mesh无逐顶点原生PixelID，保留归档UV/K、原顶点序号及原面ID；原生ID缺失=-1/UNKNOWN，未伪造映射。所有区域锚的OBS原生PixelID仍完整。
- MAX__G03_v004_raw00014 / Body-E: BODY_REGION_GEOMETRY_UNEXPLAINED；[候选/原生ID](local_results/G03/Body-E/MAX__G03_v004_raw00014/CANDIDATES_FROZEN.json)；[可视化证据](figures/G03_Three_Fixed_Directions.png)。
- MAX__G03_v004_raw00014 / Body-U: BODY_REGION_GEOMETRY_UNEXPLAINED；[候选/原生ID](local_results/G03/Body-U/MAX__G03_v004_raw00014/CANDIDATES_FROZEN.json)；[可视化证据](figures/G03_Three_Fixed_Directions.png)。
- MAX__G03_v004_raw00116 / Body-E: BODY_REGION_GEOMETRY_UNEXPLAINED；[候选/原生ID](local_results/G03/Body-E/MAX__G03_v004_raw00116/CANDIDATES_FROZEN.json)；[可视化证据](figures/G03_Three_Fixed_Directions.png)。
- MAX__G03_v004_raw00116 / Body-U: BODY_REGION_GEOMETRY_UNEXPLAINED, NEW_OR_WORSENED_HERO_RING_PENETRATION；[候选/原生ID](local_results/G03/Body-U/MAX__G03_v004_raw00116/CANDIDATES_FROZEN.json)；[可视化证据](figures/G03_Three_Fixed_Directions.png)。
- MAX__G03_v004_raw00220 / Body-E: BODY_REGION_GEOMETRY_UNEXPLAINED；[候选/原生ID](local_results/G03/Body-E/MAX__G03_v004_raw00220/CANDIDATES_FROZEN.json)；[可视化证据](figures/G03_Three_Fixed_Directions.png)。
- MAX__G03_v004_raw00220 / Body-U: NEW_OR_WORSENED_HERO_RING_PENETRATION；[候选/原生ID](local_results/G03/Body-U/MAX__G03_v004_raw00220/CANDIDATES_FROZEN.json)；[可视化证据](figures/G03_Three_Fixed_Directions.png)。
- MAX__G03_v004_raw00408 / Body-E: BODY_REGION_GEOMETRY_UNEXPLAINED；[候选/原生ID](local_results/G03/Body-E/MAX__G03_v004_raw00408/CANDIDATES_FROZEN.json)；[可视化证据](figures/G03_Three_Fixed_Directions.png)。
- MAX__G03_v004_raw00408 / Body-U: BODY_REGION_GEOMETRY_UNEXPLAINED, NEW_OR_WORSENED_HERO_RING_PENETRATION；[候选/原生ID](local_results/G03/Body-U/MAX__G03_v004_raw00408/CANDIDATES_FROZEN.json)；[可视化证据](figures/G03_Three_Fixed_Directions.png)。
- MAX__G03_v004_raw00552 / Body-E: BODY_REGION_GEOMETRY_UNEXPLAINED；[候选/原生ID](local_results/G03/Body-E/MAX__G03_v004_raw00552/CANDIDATES_FROZEN.json)；[可视化证据](figures/G03_Three_Fixed_Directions.png)。
- MAX__G03_v004_raw00552 / Body-U: RING_RASTER_WORSENING, BODY_REGION_GEOMETRY_UNEXPLAINED；[候选/原生ID](local_results/G03/Body-U/MAX__G03_v004_raw00552/CANDIDATES_FROZEN.json)；[可视化证据](figures/G03_Three_Fixed_Directions.png)。
- MAX__G03_v004_raw00642 / Body-E: BODY_REGION_GEOMETRY_UNEXPLAINED；[候选/原生ID](local_results/G03/Body-E/MAX__G03_v004_raw00642/CANDIDATES_FROZEN.json)；[可视化证据](figures/G03_Three_Fixed_Directions.png)。
- MAX__G03_v004_raw00642 / Body-U: BODY_REGION_GEOMETRY_UNEXPLAINED；[候选/原生ID](local_results/G03/Body-U/MAX__G03_v004_raw00642/CANDIDATES_FROZEN.json)；[可视化证据](figures/G03_Three_Fixed_Directions.png)。
- MAX__G03_v005_raw00029 / Body-E: BACKGROUND_HOLDOUT_CONFLICT, BODY_REGION_GEOMETRY_UNEXPLAINED；[候选/原生ID](local_results/G03/Body-E/MAX__G03_v005_raw00029/CANDIDATES_FROZEN.json)；[可视化证据](figures/G03_Three_Fixed_Directions.png)。
- MAX__G03_v005_raw00029 / Body-U: BACKGROUND_HOLDOUT_CONFLICT, BODY_REGION_GEOMETRY_UNEXPLAINED；[候选/原生ID](local_results/G03/Body-U/MAX__G03_v005_raw00029/CANDIDATES_FROZEN.json)；[可视化证据](figures/G03_Three_Fixed_Directions.png)。
- MAX__G03_v005_raw00131 / Body-E: BACKGROUND_HOLDOUT_CONFLICT, BODY_REGION_GEOMETRY_UNEXPLAINED；[候选/原生ID](local_results/G03/Body-E/MAX__G03_v005_raw00131/CANDIDATES_FROZEN.json)；[可视化证据](figures/G03_Three_Fixed_Directions.png)。
- MAX__G03_v005_raw00131 / Body-U: BACKGROUND_HOLDOUT_CONFLICT, BODY_REGION_GEOMETRY_UNEXPLAINED；[候选/原生ID](local_results/G03/Body-U/MAX__G03_v005_raw00131/CANDIDATES_FROZEN.json)；[可视化证据](figures/G03_Three_Fixed_Directions.png)。
- MAX__G03_v005_raw00171 / Body-E: BODY_REGION_GEOMETRY_UNEXPLAINED；[候选/原生ID](local_results/G03/Body-E/MAX__G03_v005_raw00171/CANDIDATES_FROZEN.json)；[可视化证据](figures/G03_Three_Fixed_Directions.png)。
- MAX__G03_v005_raw00171 / Body-U: BODY_REGION_GEOMETRY_UNEXPLAINED；[候选/原生ID](local_results/G03/Body-U/MAX__G03_v005_raw00171/CANDIDATES_FROZEN.json)；[可视化证据](figures/G03_Three_Fixed_Directions.png)。
- MAX__G03_v005_raw00445 / Body-E: RING_RASTER_WORSENING, BODY_REGION_GEOMETRY_UNEXPLAINED；[候选/原生ID](local_results/G03/Body-E/MAX__G03_v005_raw00445/CANDIDATES_FROZEN.json)；[可视化证据](figures/G03_Three_Fixed_Directions.png)。
- MAX__G03_v005_raw00445 / Body-U: BODY_REGION_GEOMETRY_UNEXPLAINED；[候选/原生ID](local_results/G03/Body-U/MAX__G03_v005_raw00445/CANDIDATES_FROZEN.json)；[可视化证据](figures/G03_Three_Fixed_Directions.png)。
- MAX__G03_v005_raw00589 / Body-E: BACKGROUND_HOLDOUT_CONFLICT, RING_RASTER_WORSENING, BODY_REGION_GEOMETRY_UNEXPLAINED；[候选/原生ID](local_results/G03/Body-E/MAX__G03_v005_raw00589/CANDIDATES_FROZEN.json)；[可视化证据](figures/G03_Three_Fixed_Directions.png)。
- MAX__G03_v005_raw00589 / Body-U: BACKGROUND_HOLDOUT_CONFLICT, RING_RASTER_WORSENING, BODY_REGION_GEOMETRY_UNEXPLAINED；[候选/原生ID](local_results/G03/Body-U/MAX__G03_v005_raw00589/CANDIDATES_FROZEN.json)；[可视化证据](figures/G03_Three_Fixed_Directions.png)。
- MAX__G03_v005_raw00633 / Body-E: BODY_REGION_GEOMETRY_UNEXPLAINED, NEW_OR_WORSENED_HERO_RING_PENETRATION；[候选/原生ID](local_results/G03/Body-E/MAX__G03_v005_raw00633/CANDIDATES_FROZEN.json)；[可视化证据](figures/G03_Three_Fixed_Directions.png)。
- MAX__G03_v005_raw00633 / Body-U: BODY_REGION_GEOMETRY_UNEXPLAINED, NEW_OR_WORSENED_HERO_RING_PENETRATION；[候选/原生ID](local_results/G03/Body-U/MAX__G03_v005_raw00633/CANDIDATES_FROZEN.json)；[可视化证据](figures/G03_Three_Fixed_Directions.png)。
- OLD018__G03_key00_raw00100 / Body-E: BODY_REGION_GEOMETRY_UNEXPLAINED；[候选/原生ID](local_results/G03/Body-E/OLD018__G03_key00_raw00100/CANDIDATES_FROZEN.json)；[可视化证据](figures/G03_Three_Fixed_Directions.png)。
- OLD018__G03_key00_raw00100 / Body-U: BODY_REGION_GEOMETRY_UNEXPLAINED；[候选/原生ID](local_results/G03/Body-U/OLD018__G03_key00_raw00100/CANDIDATES_FROZEN.json)；[可视化证据](figures/G03_Three_Fixed_Directions.png)。
- OLD018__G03_key04_raw00554 / Body-E: BODY_REGION_GEOMETRY_UNEXPLAINED；[候选/原生ID](local_results/G03/Body-E/OLD018__G03_key04_raw00554/CANDIDATES_FROZEN.json)；[可视化证据](figures/G03_Three_Fixed_Directions.png)。
- OLD018__G03_key04_raw00554 / Body-U: BODY_REGION_GEOMETRY_UNEXPLAINED, NEW_OR_WORSENED_HERO_RING_PENETRATION；[候选/原生ID](local_results/G03/Body-U/OLD018__G03_key04_raw00554/CANDIDATES_FROZEN.json)；[可视化证据](figures/G03_Three_Fixed_Directions.png)。
- OLD018__G03_v004_raw00161 / Body-E: BODY_REGION_GEOMETRY_UNEXPLAINED；[候选/原生ID](local_results/G03/Body-E/OLD018__G03_v004_raw00161/CANDIDATES_FROZEN.json)；[可视化证据](figures/G03_Three_Fixed_Directions.png)。
- OLD018__G03_v004_raw00161 / Body-U: BODY_REGION_GEOMETRY_UNEXPLAINED；[候选/原生ID](local_results/G03/Body-U/OLD018__G03_v004_raw00161/CANDIDATES_FROZEN.json)；[可视化证据](figures/G03_Three_Fixed_Directions.png)。
- OLD018__G03_v004_raw00406 / Body-E: BODY_REGION_GEOMETRY_UNEXPLAINED；[候选/原生ID](local_results/G03/Body-E/OLD018__G03_v004_raw00406/CANDIDATES_FROZEN.json)；[可视化证据](figures/G03_Three_Fixed_Directions.png)。
- OLD018__G03_v004_raw00406 / Body-U: BODY_REGION_GEOMETRY_UNEXPLAINED；[候选/原生ID](local_results/G03/Body-U/OLD018__G03_v004_raw00406/CANDIDATES_FROZEN.json)；[可视化证据](figures/G03_Three_Fixed_Directions.png)。
- OLD018__G03_v004_raw00651 / Body-E: BODY_REGION_GEOMETRY_UNEXPLAINED；[候选/原生ID](local_results/G03/Body-E/OLD018__G03_v004_raw00651/CANDIDATES_FROZEN.json)；[可视化证据](figures/G03_Three_Fixed_Directions.png)。
- OLD018__G03_v004_raw00651 / Body-U: BACKGROUND_HOLDOUT_CONFLICT, BODY_REGION_GEOMETRY_UNEXPLAINED, NEW_OR_WORSENED_HERO_RING_PENETRATION；[候选/原生ID](local_results/G03/Body-U/OLD018__G03_v004_raw00651/CANDIDATES_FROZEN.json)；[可视化证据](figures/G03_Three_Fixed_Directions.png)。
- OLD018__G03_v004_raw00834 / Body-E: BODY_REGION_GEOMETRY_UNEXPLAINED；[候选/原生ID](local_results/G03/Body-E/OLD018__G03_v004_raw00834/CANDIDATES_FROZEN.json)；[可视化证据](figures/G03_Three_Fixed_Directions.png)。
- OLD018__G03_v004_raw00834 / Body-U: BACKGROUND_HOLDOUT_CONFLICT, BODY_REGION_GEOMETRY_UNEXPLAINED, NEW_OR_WORSENED_HERO_RING_PENETRATION；[候选/原生ID](local_results/G03/Body-U/OLD018__G03_v004_raw00834/CANDIDATES_FROZEN.json)；[可视化证据](figures/G03_Three_Fixed_Directions.png)。
- MAX__G05_photo002 / Body-E: BODY_REGION_GEOMETRY_UNEXPLAINED；[候选/原生ID](local_results/G05/Body-E/MAX__G05_photo002/CANDIDATES_FROZEN.json)；[可视化证据](figures/G05_Three_Fixed_Directions.png)。
- MAX__G05_photo002 / Body-U: BODY_REGION_GEOMETRY_UNEXPLAINED；[候选/原生ID](local_results/G05/Body-U/MAX__G05_photo002/CANDIDATES_FROZEN.json)；[可视化证据](figures/G05_Three_Fixed_Directions.png)。
- MAX__G05_v004_raw00189 / Body-E: BACKGROUND_HOLDOUT_CONFLICT, BODY_REGION_GEOMETRY_UNEXPLAINED；[候选/原生ID](local_results/G05/Body-E/MAX__G05_v004_raw00189/CANDIDATES_FROZEN.json)；[可视化证据](figures/G05_Three_Fixed_Directions.png)。
- MAX__G05_v004_raw00189 / Body-U: BACKGROUND_HOLDOUT_CONFLICT；[候选/原生ID](local_results/G05/Body-U/MAX__G05_v004_raw00189/CANDIDATES_FROZEN.json)；[可视化证据](figures/G05_Three_Fixed_Directions.png)。
- MAX__G05_v004_raw00248 / Body-E: BODY_REGION_GEOMETRY_UNEXPLAINED；[候选/原生ID](local_results/G05/Body-E/MAX__G05_v004_raw00248/CANDIDATES_FROZEN.json)；[可视化证据](figures/G05_Three_Fixed_Directions.png)。
- MAX__G05_v004_raw00248 / Body-U: BACKGROUND_HOLDOUT_CONFLICT, RING_RASTER_WORSENING, NEW_OR_WORSENED_HERO_RING_PENETRATION；[候选/原生ID](local_results/G05/Body-U/MAX__G05_v004_raw00248/CANDIDATES_FROZEN.json)；[可视化证据](figures/G05_Three_Fixed_Directions.png)。
- MAX__G05_v004_raw00395 / Body-E: BACKGROUND_HOLDOUT_CONFLICT, BODY_REGION_GEOMETRY_UNEXPLAINED；[候选/原生ID](local_results/G05/Body-E/MAX__G05_v004_raw00395/CANDIDATES_FROZEN.json)；[可视化证据](figures/G05_Three_Fixed_Directions.png)。
- MAX__G05_v004_raw00395 / Body-U: BACKGROUND_HOLDOUT_CONFLICT；[候选/原生ID](local_results/G05/Body-U/MAX__G05_v004_raw00395/CANDIDATES_FROZEN.json)；[可视化证据](figures/G05_Three_Fixed_Directions.png)。
- MAX__G05_v004_raw00526 / Body-E: BODY_REGION_GEOMETRY_UNEXPLAINED；[候选/原生ID](local_results/G05/Body-E/MAX__G05_v004_raw00526/CANDIDATES_FROZEN.json)；[可视化证据](figures/G05_Three_Fixed_Directions.png)。
- MAX__G05_v004_raw00616 / Body-E: BODY_REGION_GEOMETRY_UNEXPLAINED, NEW_OR_WORSENED_HERO_RING_PENETRATION；[候选/原生ID](local_results/G05/Body-E/MAX__G05_v004_raw00616/CANDIDATES_FROZEN.json)；[可视化证据](figures/G05_Three_Fixed_Directions.png)。
- MAX__G05_v004_raw00616 / Body-U: NEW_OR_WORSENED_HERO_RING_PENETRATION；[候选/原生ID](local_results/G05/Body-U/MAX__G05_v004_raw00616/CANDIDATES_FROZEN.json)；[可视化证据](figures/G05_Three_Fixed_Directions.png)。
- MAX__G05_v004_raw00899 / Body-E: BODY_REGION_GEOMETRY_UNEXPLAINED；[候选/原生ID](local_results/G05/Body-E/MAX__G05_v004_raw00899/CANDIDATES_FROZEN.json)；[可视化证据](figures/G05_Three_Fixed_Directions.png)。
- MAX__G05_v005_raw00219 / Body-E: BACKGROUND_HOLDOUT_CONFLICT, RING_RASTER_WORSENING, BODY_REGION_GEOMETRY_UNEXPLAINED；[候选/原生ID](local_results/G05/Body-E/MAX__G05_v005_raw00219/CANDIDATES_FROZEN.json)；[可视化证据](figures/G05_Three_Fixed_Directions.png)。
- OLD018__G05_key04_raw00542 / Body-E: BODY_REGION_GEOMETRY_UNEXPLAINED；[候选/原生ID](local_results/G05/Body-E/OLD018__G05_key04_raw00542/CANDIDATES_FROZEN.json)；[可视化证据](figures/G05_Three_Fixed_Directions.png)。
- OLD018__G05_v004_raw00117 / Body-E: BACKGROUND_HOLDOUT_CONFLICT, RING_RASTER_WORSENING, BODY_REGION_GEOMETRY_UNEXPLAINED, NEW_OR_WORSENED_HERO_RING_PENETRATION；[候选/原生ID](local_results/G05/Body-E/OLD018__G05_v004_raw00117/CANDIDATES_FROZEN.json)；[可视化证据](figures/G05_Three_Fixed_Directions.png)。
- OLD018__G05_v004_raw00117 / Body-U: BACKGROUND_HOLDOUT_CONFLICT, RING_RASTER_WORSENING, BODY_REGION_GEOMETRY_UNEXPLAINED, NEW_OR_WORSENED_HERO_RING_PENETRATION；[候选/原生ID](local_results/G05/Body-U/OLD018__G05_v004_raw00117/CANDIDATES_FROZEN.json)；[可视化证据](figures/G05_Three_Fixed_Directions.png)。
- OLD018__G05_v004_raw00217 / Body-E: BODY_REGION_GEOMETRY_UNEXPLAINED；[候选/原生ID](local_results/G05/Body-E/OLD018__G05_v004_raw00217/CANDIDATES_FROZEN.json)；[可视化证据](figures/G05_Three_Fixed_Directions.png)。
- OLD018__G05_v004_raw00217 / Body-U: NEW_OR_WORSENED_HERO_RING_PENETRATION；[候选/原生ID](local_results/G05/Body-U/OLD018__G05_v004_raw00217/CANDIDATES_FROZEN.json)；[可视化证据](figures/G05_Three_Fixed_Directions.png)。
- OLD018__G05_v004_raw00337 / Body-E: BODY_REGION_GEOMETRY_UNEXPLAINED；[候选/原生ID](local_results/G05/Body-E/OLD018__G05_v004_raw00337/CANDIDATES_FROZEN.json)；[可视化证据](figures/G05_Three_Fixed_Directions.png)。
- OLD018__G05_v004_raw00377 / Body-E: BODY_REGION_GEOMETRY_UNEXPLAINED；[候选/原生ID](local_results/G05/Body-E/OLD018__G05_v004_raw00377/CANDIDATES_FROZEN.json)；[可视化证据](figures/G05_Three_Fixed_Directions.png)。
- OLD018__G05_v004_raw00377 / Body-U: BACKGROUND_HOLDOUT_CONFLICT, NEW_OR_WORSENED_HERO_RING_PENETRATION；[候选/原生ID](local_results/G05/Body-U/OLD018__G05_v004_raw00377/CANDIDATES_FROZEN.json)；[可视化证据](figures/G05_Three_Fixed_Directions.png)。
- OLD018__G05_v004_raw00457 / Body-E: BODY_REGION_GEOMETRY_UNEXPLAINED；[候选/原生ID](local_results/G05/Body-E/OLD018__G05_v004_raw00457/CANDIDATES_FROZEN.json)；[可视化证据](figures/G05_Three_Fixed_Directions.png)。
- OLD018__G05_v004_raw00636 / Body-E: BODY_REGION_GEOMETRY_UNEXPLAINED；[候选/原生ID](local_results/G05/Body-E/OLD018__G05_v004_raw00636/CANDIDATES_FROZEN.json)；[可视化证据](figures/G05_Three_Fixed_Directions.png)。
- OLD018__G05_v004_raw00796 / Body-E: BODY_REGION_GEOMETRY_UNEXPLAINED；[候选/原生ID](local_results/G05/Body-E/OLD018__G05_v004_raw00796/CANDIDATES_FROZEN.json)；[可视化证据](figures/G05_Three_Fixed_Directions.png)。
- OLD018__G05_v004_raw00796 / Body-U: NEW_OR_WORSENED_HERO_RING_PENETRATION；[候选/原生ID](local_results/G05/Body-U/OLD018__G05_v004_raw00796/CANDIDATES_FROZEN.json)；[可视化证据](figures/G05_Three_Fixed_Directions.png)。
- MAX__G01_photo001 / Body-E: BODY_REGION_GEOMETRY_UNEXPLAINED；[候选/原生ID](local_results/G01/Body-E/MAX__G01_photo001/CANDIDATES_FROZEN.json)；[可视化证据](figures/G01_Three_Fixed_Directions.png)。
- MAX__G01_photo001 / Body-U: BODY_REGION_GEOMETRY_UNEXPLAINED, NEW_OR_WORSENED_HERO_RING_PENETRATION；[候选/原生ID](local_results/G01/Body-U/MAX__G01_photo001/CANDIDATES_FROZEN.json)；[可视化证据](figures/G01_Three_Fixed_Directions.png)。
- MAX__G01_v004_raw00049 / Body-U: BODY_REGION_GEOMETRY_UNEXPLAINED；[候选/原生ID](local_results/G01/Body-U/MAX__G01_v004_raw00049/CANDIDATES_FROZEN.json)；[可视化证据](figures/G01_Three_Fixed_Directions.png)。
- MAX__G01_v004_raw00158 / Body-E: BODY_REGION_GEOMETRY_UNEXPLAINED, NEW_OR_WORSENED_HERO_RING_PENETRATION；[候选/原生ID](local_results/G01/Body-E/MAX__G01_v004_raw00158/CANDIDATES_FROZEN.json)；[可视化证据](figures/G01_Three_Fixed_Directions.png)。
- MAX__G01_v004_raw00158 / Body-U: BODY_REGION_GEOMETRY_UNEXPLAINED, NEW_OR_WORSENED_HERO_RING_PENETRATION；[候选/原生ID](local_results/G01/Body-U/MAX__G01_v004_raw00158/CANDIDATES_FROZEN.json)；[可视化证据](figures/G01_Three_Fixed_Directions.png)。
- MAX__G01_v004_raw00282 / Body-U: BODY_REGION_GEOMETRY_UNEXPLAINED；[候选/原生ID](local_results/G01/Body-U/MAX__G01_v004_raw00282/CANDIDATES_FROZEN.json)；[可视化证据](figures/G01_Three_Fixed_Directions.png)。
- MAX__G01_v004_raw00341 / Body-E: BACKGROUND_HOLDOUT_CONFLICT；[候选/原生ID](local_results/G01/Body-E/MAX__G01_v004_raw00341/CANDIDATES_FROZEN.json)；[可视化证据](figures/G01_Three_Fixed_Directions.png)。
- MAX__G01_v004_raw00341 / Body-U: BACKGROUND_HOLDOUT_CONFLICT, BODY_REGION_GEOMETRY_UNEXPLAINED；[候选/原生ID](local_results/G01/Body-U/MAX__G01_v004_raw00341/CANDIDATES_FROZEN.json)；[可视化证据](figures/G01_Three_Fixed_Directions.png)。
- MAX__G01_v004_raw00499 / Body-U: BODY_REGION_GEOMETRY_UNEXPLAINED；[候选/原生ID](local_results/G01/Body-U/MAX__G01_v004_raw00499/CANDIDATES_FROZEN.json)；[可视化证据](figures/G01_Three_Fixed_Directions.png)。
- MAX__G01_v004_raw00657 / Body-U: BODY_REGION_GEOMETRY_UNEXPLAINED；[候选/原生ID](local_results/G01/Body-U/MAX__G01_v004_raw00657/CANDIDATES_FROZEN.json)；[可视化证据](figures/G01_Three_Fixed_Directions.png)。
- MAX__G01_v004_raw00813 / Body-E: BODY_REGION_GEOMETRY_UNEXPLAINED, NEW_OR_WORSENED_HERO_RING_PENETRATION；[候选/原生ID](local_results/G01/Body-E/MAX__G01_v004_raw00813/CANDIDATES_FROZEN.json)；[可视化证据](figures/G01_Three_Fixed_Directions.png)。
- MAX__G01_v004_raw00813 / Body-U: BODY_REGION_GEOMETRY_UNEXPLAINED；[候选/原生ID](local_results/G01/Body-U/MAX__G01_v004_raw00813/CANDIDATES_FROZEN.json)；[可视化证据](figures/G01_Three_Fixed_Directions.png)。
- MAX__G01_v004_raw01093 / Body-E: BODY_REGION_GEOMETRY_UNEXPLAINED；[候选/原生ID](local_results/G01/Body-E/MAX__G01_v004_raw01093/CANDIDATES_FROZEN.json)；[可视化证据](figures/G01_Three_Fixed_Directions.png)。
- MAX__G01_v004_raw01093 / Body-U: BODY_REGION_GEOMETRY_UNEXPLAINED；[候选/原生ID](local_results/G01/Body-U/MAX__G01_v004_raw01093/CANDIDATES_FROZEN.json)；[可视化证据](figures/G01_Three_Fixed_Directions.png)。
- MAX__G01_v004_raw01264 / Body-U: BODY_REGION_GEOMETRY_UNEXPLAINED；[候选/原生ID](local_results/G01/Body-U/MAX__G01_v004_raw01264/CANDIDATES_FROZEN.json)；[可视化证据](figures/G01_Three_Fixed_Directions.png)。
- MAX__G01_v005_raw00104 / Body-E: INSUFFICIENT_INDEPENDENT_INFORMATION, BACKGROUND_HOLDOUT_CONFLICT；[候选/原生ID](local_results/G01/Body-E/MAX__G01_v005_raw00104/CANDIDATES_FROZEN.json)；[可视化证据](figures/G01_Three_Fixed_Directions.png)。
- MAX__G01_v005_raw00104 / Body-U: INSUFFICIENT_INDEPENDENT_INFORMATION, BACKGROUND_HOLDOUT_CONFLICT, NEW_OR_WORSENED_HERO_RING_PENETRATION；[候选/原生ID](local_results/G01/Body-U/MAX__G01_v005_raw00104/CANDIDATES_FROZEN.json)；[可视化证据](figures/G01_Three_Fixed_Directions.png)。
- MAX__G01_v005_raw00185 / Body-E: INSUFFICIENT_INDEPENDENT_INFORMATION, BACKGROUND_HOLDOUT_CONFLICT；[候选/原生ID](local_results/G01/Body-E/MAX__G01_v005_raw00185/CANDIDATES_FROZEN.json)；[可视化证据](figures/G01_Three_Fixed_Directions.png)。
- MAX__G01_v005_raw00185 / Body-U: INSUFFICIENT_INDEPENDENT_INFORMATION, BACKGROUND_HOLDOUT_CONFLICT；[候选/原生ID](local_results/G01/Body-U/MAX__G01_v005_raw00185/CANDIDATES_FROZEN.json)；[可视化证据](figures/G01_Three_Fixed_Directions.png)。
- MAX__G01_v005_raw00439 / Body-E: BACKGROUND_HOLDOUT_CONFLICT；[候选/原生ID](local_results/G01/Body-E/MAX__G01_v005_raw00439/CANDIDATES_FROZEN.json)；[可视化证据](figures/G01_Three_Fixed_Directions.png)。
- MAX__G01_v005_raw00439 / Body-U: BACKGROUND_HOLDOUT_CONFLICT；[候选/原生ID](local_results/G01/Body-U/MAX__G01_v005_raw00439/CANDIDATES_FROZEN.json)；[可视化证据](figures/G01_Three_Fixed_Directions.png)。
- MAX__G01_v005_raw00562 / Body-E: BACKGROUND_HOLDOUT_CONFLICT, BODY_REGION_GEOMETRY_UNEXPLAINED；[候选/原生ID](local_results/G01/Body-E/MAX__G01_v005_raw00562/CANDIDATES_FROZEN.json)；[可视化证据](figures/G01_Three_Fixed_Directions.png)。
- MAX__G01_v005_raw00562 / Body-U: BACKGROUND_HOLDOUT_CONFLICT, RING_RASTER_WORSENING；[候选/原生ID](local_results/G01/Body-U/MAX__G01_v005_raw00562/CANDIDATES_FROZEN.json)；[可视化证据](figures/G01_Three_Fixed_Directions.png)。
- MAX__G01_v005_raw00694 / Body-E: BACKGROUND_HOLDOUT_CONFLICT；[候选/原生ID](local_results/G01/Body-E/MAX__G01_v005_raw00694/CANDIDATES_FROZEN.json)；[可视化证据](figures/G01_Three_Fixed_Directions.png)。
- MAX__G01_v005_raw00694 / Body-U: BACKGROUND_HOLDOUT_CONFLICT, NEW_OR_WORSENED_HERO_RING_PENETRATION；[候选/原生ID](local_results/G01/Body-U/MAX__G01_v005_raw00694/CANDIDATES_FROZEN.json)；[可视化证据](figures/G01_Three_Fixed_Directions.png)。
- MAX__G01_video005_v005_00000 / Body-E: INSUFFICIENT_BACKGROUND_HOLDOUT；[候选/原生ID](local_results/G01/Body-E/MAX__G01_video005_v005_00000/CANDIDATES_FROZEN.json)；[可视化证据](figures/G01_Three_Fixed_Directions.png)。
- MAX__G01_video005_v005_00000 / Body-U: INSUFFICIENT_BACKGROUND_HOLDOUT, BODY_REGION_GEOMETRY_UNEXPLAINED, NEW_OR_WORSENED_HERO_RING_PENETRATION；[候选/原生ID](local_results/G01/Body-U/MAX__G01_video005_v005_00000/CANDIDATES_FROZEN.json)；[可视化证据](figures/G01_Three_Fixed_Directions.png)。
- MAX__G01_video005_v005_00326 / Body-E: BACKGROUND_HOLDOUT_CONFLICT, BODY_REGION_GEOMETRY_UNEXPLAINED；[候选/原生ID](local_results/G01/Body-E/MAX__G01_video005_v005_00326/CANDIDATES_FROZEN.json)；[可视化证据](figures/G01_Three_Fixed_Directions.png)。
- MAX__G01_video005_v005_00326 / Body-U: BACKGROUND_HOLDOUT_CONFLICT, BODY_REGION_GEOMETRY_UNEXPLAINED；[候选/原生ID](local_results/G01/Body-U/MAX__G01_video005_v005_00326/CANDIDATES_FROZEN.json)；[可视化证据](figures/G01_Three_Fixed_Directions.png)。
- MAX__G01_video005_v005_00860 / Body-E: BACKGROUND_HOLDOUT_CONFLICT；[候选/原生ID](local_results/G01/Body-E/MAX__G01_video005_v005_00860/CANDIDATES_FROZEN.json)；[可视化证据](figures/G01_Three_Fixed_Directions.png)。
- MAX__G01_video005_v005_00860 / Body-U: BACKGROUND_HOLDOUT_CONFLICT；[候选/原生ID](local_results/G01/Body-U/MAX__G01_video005_v005_00860/CANDIDATES_FROZEN.json)；[可视化证据](figures/G01_Three_Fixed_Directions.png)。
- OLD018__G01_004_new_r00 / Body-E: BACKGROUND_HOLDOUT_CONFLICT, BODY_REGION_GEOMETRY_UNEXPLAINED, NEW_OR_WORSENED_HERO_RING_PENETRATION；[候选/原生ID](local_results/G01/Body-E/OLD018__G01_004_new_r00/CANDIDATES_FROZEN.json)；[可视化证据](figures/G01_Three_Fixed_Directions.png)。
- OLD018__G01_004_new_r00 / Body-U: BACKGROUND_HOLDOUT_CONFLICT, BODY_REGION_GEOMETRY_UNEXPLAINED, NEW_OR_WORSENED_HERO_RING_PENETRATION；[候选/原生ID](local_results/G01/Body-U/OLD018__G01_004_new_r00/CANDIDATES_FROZEN.json)；[可视化证据](figures/G01_Three_Fixed_Directions.png)。
- OLD018__G01_004_ref03 / Body-U: BODY_REGION_GEOMETRY_UNEXPLAINED, NEW_OR_WORSENED_HERO_RING_PENETRATION；[候选/原生ID](local_results/G01/Body-U/OLD018__G01_004_ref03/CANDIDATES_FROZEN.json)；[可视化证据](figures/G01_Three_Fixed_Directions.png)。
- OLD018__G01_004_ref08 / Body-U: BODY_REGION_GEOMETRY_UNEXPLAINED；[候选/原生ID](local_results/G01/Body-U/OLD018__G01_004_ref08/CANDIDATES_FROZEN.json)；[可视化证据](figures/G01_Three_Fixed_Directions.png)。
- OLD018__G01_004_ref13 / Body-U: BODY_REGION_GEOMETRY_UNEXPLAINED；[候选/原生ID](local_results/G01/Body-U/OLD018__G01_004_ref13/CANDIDATES_FROZEN.json)；[可视化证据](figures/G01_Three_Fixed_Directions.png)。
- OLD018__G01_v004_raw00152 / Body-U: BODY_REGION_GEOMETRY_UNEXPLAINED；[候选/原生ID](local_results/G01/Body-U/OLD018__G01_v004_raw00152/CANDIDATES_FROZEN.json)；[可视化证据](figures/G01_Three_Fixed_Directions.png)。
- OLD018__G01_v004_raw00412 / Body-E: NEW_OR_WORSENED_HERO_RING_PENETRATION；[候选/原生ID](local_results/G01/Body-E/OLD018__G01_v004_raw00412/CANDIDATES_FROZEN.json)；[可视化证据](figures/G01_Three_Fixed_Directions.png)。
- OLD018__G01_v004_raw00412 / Body-U: BODY_REGION_GEOMETRY_UNEXPLAINED, NEW_OR_WORSENED_HERO_RING_PENETRATION；[候选/原生ID](local_results/G01/Body-U/OLD018__G01_v004_raw00412/CANDIDATES_FROZEN.json)；[可视化证据](figures/G01_Three_Fixed_Directions.png)。
- OLD018__G01_v004_raw00852 / Body-U: BODY_REGION_GEOMETRY_UNEXPLAINED；[候选/原生ID](local_results/G01/Body-U/OLD018__G01_v004_raw00852/CANDIDATES_FROZEN.json)；[可视化证据](figures/G01_Three_Fixed_Directions.png)。
- OLD018__G01_video004_004_15 / Body-E: BODY_REGION_GEOMETRY_UNEXPLAINED；[候选/原生ID](local_results/G01/Body-E/OLD018__G01_video004_004_15/CANDIDATES_FROZEN.json)；[可视化证据](figures/G01_Three_Fixed_Directions.png)。
- OLD018__G01_video004_004_15 / Body-U: BODY_REGION_GEOMETRY_UNEXPLAINED；[候选/原生ID](local_results/G01/Body-U/OLD018__G01_video004_004_15/CANDIDATES_FROZEN.json)；[可视化证据](figures/G01_Three_Fixed_Directions.png)。
- MAX__G06_v004_raw00046 / Body-E: BACKGROUND_HOLDOUT_CONFLICT；[候选/原生ID](local_results/G06/Body-E/MAX__G06_v004_raw00046/CANDIDATES_FROZEN.json)；[可视化证据](figures/G06_Three_Fixed_Directions.png)。
- MAX__G06_v004_raw00046 / Body-U: BACKGROUND_HOLDOUT_CONFLICT, NEW_OR_WORSENED_HERO_RING_PENETRATION；[候选/原生ID](local_results/G06/Body-U/MAX__G06_v004_raw00046/CANDIDATES_FROZEN.json)；[可视化证据](figures/G06_Three_Fixed_Directions.png)。
- MAX__G06_v004_raw00606 / Body-U: BACKGROUND_HOLDOUT_CONFLICT, RING_RASTER_WORSENING, NEW_OR_WORSENED_HERO_RING_PENETRATION；[候选/原生ID](local_results/G06/Body-U/MAX__G06_v004_raw00606/CANDIDATES_FROZEN.json)；[可视化证据](figures/G06_Three_Fixed_Directions.png)。
- MAX__G06_v004_raw00744 / Body-U: BACKGROUND_HOLDOUT_CONFLICT, RING_RASTER_WORSENING；[候选/原生ID](local_results/G06/Body-U/MAX__G06_v004_raw00744/CANDIDATES_FROZEN.json)；[可视化证据](figures/G06_Three_Fixed_Directions.png)。
- MAX__G06_v004_raw00944 / Body-U: NEW_OR_WORSENED_HERO_RING_PENETRATION；[候选/原生ID](local_results/G06/Body-U/MAX__G06_v004_raw00944/CANDIDATES_FROZEN.json)；[可视化证据](figures/G06_Three_Fixed_Directions.png)。
- MAX__G06_v004_raw01037 / Body-U: NEW_OR_WORSENED_HERO_RING_PENETRATION；[候选/原生ID](local_results/G06/Body-U/MAX__G06_v004_raw01037/CANDIDATES_FROZEN.json)；[可视化证据](figures/G06_Three_Fixed_Directions.png)。
- OLD018__G06_004_ref04 / Body-E: BACKGROUND_HOLDOUT_CONFLICT, RING_RASTER_WORSENING, NEW_OR_WORSENED_HERO_RING_PENETRATION；[候选/原生ID](local_results/G06/Body-E/OLD018__G06_004_ref04/CANDIDATES_FROZEN.json)；[可视化证据](figures/G06_Three_Fixed_Directions.png)。
- OLD018__G06_004_ref04 / Body-U: BACKGROUND_HOLDOUT_CONFLICT；[候选/原生ID](local_results/G06/Body-U/OLD018__G06_004_ref04/CANDIDATES_FROZEN.json)；[可视化证据](figures/G06_Three_Fixed_Directions.png)。
- OLD018__G06_v004_raw00348 / Body-E: BACKGROUND_HOLDOUT_CONFLICT；[候选/原生ID](local_results/G06/Body-E/OLD018__G06_v004_raw00348/CANDIDATES_FROZEN.json)；[可视化证据](figures/G06_Three_Fixed_Directions.png)。
- OLD018__G06_v004_raw00348 / Body-U: BACKGROUND_HOLDOUT_CONFLICT；[候选/原生ID](local_results/G06/Body-U/OLD018__G06_v004_raw00348/CANDIDATES_FROZEN.json)；[可视化证据](figures/G06_Three_Fixed_Directions.png)。
- OLD018__G06_v004_raw00721 / Body-U: NEW_OR_WORSENED_HERO_RING_PENETRATION；[候选/原生ID](local_results/G06/Body-U/OLD018__G06_v004_raw00721/CANDIDATES_FROZEN.json)；[可视化证据](figures/G06_Three_Fixed_Directions.png)。
- OLD018__G06_v004_raw00940 / Body-E: BACKGROUND_HOLDOUT_CONFLICT, NEW_OR_WORSENED_HERO_RING_PENETRATION；[候选/原生ID](local_results/G06/Body-E/OLD018__G06_v004_raw00940/CANDIDATES_FROZEN.json)；[可视化证据](figures/G06_Three_Fixed_Directions.png)。
- OLD018__G06_v004_raw00940 / Body-U: BACKGROUND_HOLDOUT_CONFLICT, NEW_OR_WORSENED_HERO_RING_PENETRATION；[候选/原生ID](local_results/G06/Body-U/OLD018__G06_v004_raw00940/CANDIDATES_FROZEN.json)；[可视化证据](figures/G06_Three_Fixed_Directions.png)。
