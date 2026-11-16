# 失败台账

所有失败保留；数值主解与科研验收分别列报。

| pool | arm | start | reason | nfev | evidence |
| --- | --- | --- | --- | --- | --- |
| G03_005 | E2 | 0 | ["OPTIMIZER_NOT_CONVERGED"] | 60 | local_results/G03_005/E2/START_0.json |
| G05_004 | E2 | 1 | ["OPTIMIZER_NOT_CONVERGED"] | 60 | local_results/G05_004/E2/START_1.json |

## G01_004 / E1

原因：HELDOUT_PROJECTION_INCONSISTENT。

[主解与全部初值](local_results/G01_004/E1/SELECTION.json)；[全来源投影](figures/G01_004_ALL_VIEW_OVERLAYS.png)；[六方向主体与Ring](figures/G01_004_SIX_DIRECTION_BODIES.png)。

- `MAX__G01_v004_raw00049`：role=FIT, IoU=0.8011291779584463, FN=4343, FP=60；[逐帧本地图](figures/overlays/MAX__G01_v004_raw00049.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `MAX__G01_v004_raw00158`：role=HOLDOUT, IoU=0.8008096850792168, FN=4576, FP=541；[逐帧本地图](figures/overlays/MAX__G01_v004_raw00158.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `MAX__G01_v004_raw00282`：role=HOLDOUT, IoU=0.7896185764443026, FN=5008, FP=265；[逐帧本地图](figures/overlays/MAX__G01_v004_raw00282.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `MAX__G01_v004_raw00341`：role=HOLDOUT, IoU=0.8075700292146417, FN=4468, FP=11；[逐帧本地图](figures/overlays/MAX__G01_v004_raw00341.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `MAX__G01_v004_raw00499`：role=FIT, IoU=0.8420615621849238, FN=2536, FP=127；[逐帧本地图](figures/overlays/MAX__G01_v004_raw00499.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `MAX__G01_v004_raw00657`：role=HOLDOUT, IoU=0.8599576735021528, FN=1859, FP=60；[逐帧本地图](figures/overlays/MAX__G01_v004_raw00657.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `MAX__G01_v004_raw00813`：role=FIT, IoU=0.8608742362183576, FN=1972, FP=100；[逐帧本地图](figures/overlays/MAX__G01_v004_raw00813.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `MAX__G01_v004_raw01093`：role=FIT, IoU=0.8908661417322835, FN=1273, FP=113；[逐帧本地图](figures/overlays/MAX__G01_v004_raw01093.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `MAX__G01_v004_raw01264`：role=FIT, IoU=0.9034203803576497, FN=1190, FP=171；[逐帧本地图](figures/overlays/MAX__G01_v004_raw01264.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `OLD018__G01_004_new_r00`：role=HOLDOUT, IoU=0.8134620290841058, FN=4257, FP=130；[逐帧本地图](figures/overlays/OLD018__G01_004_new_r00.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `OLD018__G01_004_ref03`：role=HOLDOUT, IoU=0.8225603059024529, FN=4122, FP=240；[逐帧本地图](figures/overlays/OLD018__G01_004_ref03.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `OLD018__G01_004_ref08`：role=HOLDOUT, IoU=0.8588385812779871, FN=1946, FP=40；[逐帧本地图](figures/overlays/OLD018__G01_004_ref08.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `OLD018__G01_004_ref13`：role=FIT, IoU=0.8853425181783391, FN=1443, FP=55；[逐帧本地图](figures/overlays/OLD018__G01_004_ref13.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `OLD018__G01_v004_raw00152`：role=HOLDOUT, IoU=0.8042307392084928, FN=4439, FP=577；[逐帧本地图](figures/overlays/OLD018__G01_v004_raw00152.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `OLD018__G01_v004_raw00412`：role=HOLDOUT, IoU=0.8328911232137038, FN=3235, FP=355；[逐帧本地图](figures/overlays/OLD018__G01_v004_raw00412.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `OLD018__G01_v004_raw00852`：role=FIT, IoU=0.8614072494669509, FN=2034, FP=46；[逐帧本地图](figures/overlays/OLD018__G01_v004_raw00852.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `OLD018__G01_video004_004_15`：role=FIT, IoU=0.9011450381679389, FN=1161, FP=134；[逐帧本地图](figures/overlays/OLD018__G01_video004_004_15.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。

## G01_004 / E2

原因：MULTISTART_UNSTABLE; RING_BODY_SURFACE_PENETRATION。

[主解与全部初值](local_results/G01_004/E2/SELECTION.json)；[全来源投影](figures/G01_004_ALL_VIEW_OVERLAYS.png)；[六方向主体与Ring](figures/G01_004_SIX_DIRECTION_BODIES.png)。

- `MAX__G01_v004_raw00049`：role=FIT, IoU=0.8449747508602583, FN=3172, FP=297；[逐帧本地图](figures/overlays/MAX__G01_v004_raw00049.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `MAX__G01_v004_raw00158`：role=HOLDOUT, IoU=0.8321817140675701, FN=3349, FP=1047；[逐帧本地图](figures/overlays/MAX__G01_v004_raw00158.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `MAX__G01_v004_raw00282`：role=HOLDOUT, IoU=0.8353192668540438, FN=3698, FP=462；[逐帧本地图](figures/overlays/MAX__G01_v004_raw00282.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `MAX__G01_v004_raw00341`：role=HOLDOUT, IoU=0.8564341615703717, FN=3239, FP=118；[逐帧本地图](figures/overlays/MAX__G01_v004_raw00341.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `MAX__G01_v004_raw00499`：role=FIT, IoU=0.8675151017535628, FN=1942, FP=317；[逐帧本地图](figures/overlays/MAX__G01_v004_raw00499.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `MAX__G01_v004_raw00657`：role=HOLDOUT, IoU=0.875377969762419, FN=1484, FP=247；[逐帧本地图](figures/overlays/MAX__G01_v004_raw00657.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `MAX__G01_v004_raw00813`：role=FIT, IoU=0.8766341495786051, FN=1583, FP=276；[逐帧本地图](figures/overlays/MAX__G01_v004_raw00813.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `MAX__G01_v004_raw01093`：role=FIT, IoU=0.8949622362376392, FN=1093, FP=256；[逐帧本地图](figures/overlays/MAX__G01_v004_raw01093.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `MAX__G01_v004_raw01264`：role=FIT, IoU=0.8975907845754021, FN=1142, FP=316；[逐帧本地图](figures/overlays/MAX__G01_v004_raw01264.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `OLD018__G01_004_new_r00`：role=HOLDOUT, IoU=0.8540513336688476, FN=3024, FP=456；[逐帧本地图](figures/overlays/OLD018__G01_004_new_r00.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `OLD018__G01_004_ref03`：role=HOLDOUT, IoU=0.8567352515672721, FN=3024, FP=541；[逐帧本地图](figures/overlays/OLD018__G01_004_ref03.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `OLD018__G01_004_ref08`：role=HOLDOUT, IoU=0.8762814211487151, FN=1549, FP=213；[逐帧本地图](figures/overlays/OLD018__G01_004_ref08.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `OLD018__G01_004_ref13`：role=FIT, IoU=0.8978168587022438, FN=1166, FP=182；[逐帧本地图](figures/overlays/OLD018__G01_004_ref13.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `OLD018__G01_v004_raw00152`：role=HOLDOUT, IoU=0.8329069456642102, FN=3232, FP=1144；[逐帧本地图](figures/overlays/OLD018__G01_v004_raw00152.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `OLD018__G01_v004_raw00412`：role=HOLDOUT, IoU=0.8538129760484537, FN=2520, FP=666；[逐帧本地图](figures/overlays/OLD018__G01_v004_raw00412.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `OLD018__G01_v004_raw00852`：role=FIT, IoU=0.8769261161596207, FN=1645, FP=224；[逐帧本地图](figures/overlays/OLD018__G01_v004_raw00852.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `OLD018__G01_video004_004_15`：role=FIT, IoU=0.8990714878840492, FN=1056, FP=281；[逐帧本地图](figures/overlays/OLD018__G01_video004_004_15.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。

## G01_005 / E1

原因：RING_BODY_SURFACE_PENETRATION。

[主解与全部初值](local_results/G01_005/E1/SELECTION.json)；[全来源投影](figures/G01_005_ALL_VIEW_OVERLAYS.png)；[六方向主体与Ring](figures/G01_005_SIX_DIRECTION_BODIES.png)。

- `MAX__G01_v005_raw00104`：role=FIT, IoU=0.9065555377464337, FN=1242, FP=507；[逐帧本地图](figures/overlays/MAX__G01_v005_raw00104.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `MAX__G01_v005_raw00185`：role=HOLDOUT, IoU=0.9282570687888105, FN=626, FP=564；[逐帧本地图](figures/overlays/MAX__G01_v005_raw00185.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `MAX__G01_v005_raw00439`：role=HOLDOUT, IoU=0.9344375963020031, FN=521, FP=330；[逐帧本地图](figures/overlays/MAX__G01_v005_raw00439.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `MAX__G01_v005_raw00562`：role=FIT, IoU=0.935794289320082, FN=531, FP=283；[逐帧本地图](figures/overlays/MAX__G01_v005_raw00562.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `MAX__G01_v005_raw00694`：role=FIT, IoU=0.9286086164258753, FN=641, FP=456；[逐帧本地图](figures/overlays/MAX__G01_v005_raw00694.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `MAX__G01_video005_v005_00000`：role=FIT, IoU=0.8794838145231846, FN=2105, FP=650；[逐帧本地图](figures/overlays/MAX__G01_video005_v005_00000.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `MAX__G01_video005_v005_00326`：role=FIT, IoU=0.9274670610379134, FN=638, FP=441；[逐帧本地图](figures/overlays/MAX__G01_video005_v005_00326.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `MAX__G01_video005_v005_00860`：role=FIT, IoU=0.957530734336993, FN=528, FP=118；[逐帧本地图](figures/overlays/MAX__G01_video005_v005_00860.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。

## G01_005 / E2

原因：MULTISTART_UNSTABLE; RING_BODY_SURFACE_PENETRATION。

[主解与全部初值](local_results/G01_005/E2/SELECTION.json)；[全来源投影](figures/G01_005_ALL_VIEW_OVERLAYS.png)；[六方向主体与Ring](figures/G01_005_SIX_DIRECTION_BODIES.png)。

- `MAX__G01_v005_raw00104`：role=FIT, IoU=0.8895610278372591, FN=1593, FP=470；[逐帧本地图](figures/overlays/MAX__G01_v005_raw00104.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `MAX__G01_v005_raw00185`：role=HOLDOUT, IoU=0.903736237290175, FN=1002, FP=598；[逐帧本地图](figures/overlays/MAX__G01_v005_raw00185.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `MAX__G01_v005_raw00439`：role=HOLDOUT, IoU=0.9245764678579717, FN=698, FP=277；[逐帧本地图](figures/overlays/MAX__G01_v005_raw00439.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `MAX__G01_v005_raw00562`：role=FIT, IoU=0.9320913939972932, FN=687, FP=166；[逐帧本地图](figures/overlays/MAX__G01_v005_raw00562.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `MAX__G01_v005_raw00694`：role=FIT, IoU=0.9357081374561346, FN=778, FP=193；[逐帧本地图](figures/overlays/MAX__G01_v005_raw00694.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `MAX__G01_video005_v005_00000`：role=FIT, IoU=0.8826367264593659, FN=2085, FP=591；[逐帧本地图](figures/overlays/MAX__G01_video005_v005_00000.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `MAX__G01_video005_v005_00326`：role=FIT, IoU=0.9159612649827318, FN=909, FP=332；[逐帧本地图](figures/overlays/MAX__G01_video005_v005_00326.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `MAX__G01_video005_v005_00860`：role=FIT, IoU=0.9624218492925304, FN=469, FP=102；[逐帧本地图](figures/overlays/MAX__G01_video005_v005_00860.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。

## G01_PHOTO / E1

原因：NOT_EVALUABLE_INSUFFICIENT_MULTIVIEW。

[不足多视角状态](local_results/G01_PHOTO/E1/SELECTION.json)；[原始图像证据](figures/G01_PHOTO_ALL_VIEW_OVERLAYS.png)。

- `MAX__G01_photo001`：role=NOT_EVALUABLE, IoU=None, FN=None, FP=None；[逐帧本地图](figures/overlays/MAX__G01_photo001.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。

## G01_PHOTO / E2

原因：NOT_EVALUABLE_INSUFFICIENT_MULTIVIEW。

[不足多视角状态](local_results/G01_PHOTO/E2/SELECTION.json)；[原始图像证据](figures/G01_PHOTO_ALL_VIEW_OVERLAYS.png)。

- `MAX__G01_photo001`：role=NOT_EVALUABLE, IoU=None, FN=None, FP=None；[逐帧本地图](figures/overlays/MAX__G01_photo001.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。

## G03_004 / E1

原因：HELDOUT_PROJECTION_INCONSISTENT。

[主解与全部初值](local_results/G03_004/E1/SELECTION.json)；[全来源投影](figures/G03_004_ALL_VIEW_OVERLAYS.png)；[六方向主体与Ring](figures/G03_004_SIX_DIRECTION_BODIES.png)。

- `MAX__G03_v004_raw00014`：role=FIT, IoU=0.8266830523445601, FN=3506, FP=1007；[逐帧本地图](figures/overlays/MAX__G03_v004_raw00014.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `MAX__G03_v004_raw00116`：role=FIT, IoU=0.8404914646080244, FN=3202, FP=1199；[逐帧本地图](figures/overlays/MAX__G03_v004_raw00116.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `MAX__G03_v004_raw00220`：role=HOLDOUT, IoU=0.8434954228605023, FN=2793, FP=934；[逐帧本地图](figures/overlays/MAX__G03_v004_raw00220.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `MAX__G03_v004_raw00408`：role=FIT, IoU=0.8394312255541069, FN=3051, FP=890；[逐帧本地图](figures/overlays/MAX__G03_v004_raw00408.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `MAX__G03_v004_raw00552`：role=FIT, IoU=0.82146023190667, FN=3798, FP=1237；[逐帧本地图](figures/overlays/MAX__G03_v004_raw00552.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `MAX__G03_v004_raw00642`：role=FIT, IoU=0.830680838839414, FN=4152, FP=1742；[逐帧本地图](figures/overlays/MAX__G03_v004_raw00642.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `OLD018__G03_key00_raw00100`：role=FIT, IoU=0.8341291781854737, FN=3460, FP=1160；[逐帧本地图](figures/overlays/OLD018__G03_key00_raw00100.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `OLD018__G03_key04_raw00554`：role=FIT, IoU=0.8197082105711547, FN=3874, FP=1205；[逐帧本地图](figures/overlays/OLD018__G03_key04_raw00554.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `OLD018__G03_v004_raw00161`：role=HOLDOUT, IoU=0.8225869941741458, FN=3080, FP=1427；[逐帧本地图](figures/overlays/OLD018__G03_v004_raw00161.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `OLD018__G03_v004_raw00406`：role=FIT, IoU=0.8424464831804281, FN=2985, FP=879；[逐帧本地图](figures/overlays/OLD018__G03_v004_raw00406.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `OLD018__G03_v004_raw00651`：role=HOLDOUT, IoU=0.8366617496879609, FN=4145, FP=1613；[逐帧本地图](figures/overlays/OLD018__G03_v004_raw00651.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `OLD018__G03_v004_raw00834`：role=HOLDOUT, IoU=0.8619922917284316, FN=3386, FP=1269；[逐帧本地图](figures/overlays/OLD018__G03_v004_raw00834.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。

## G03_004 / E2

原因：MULTISTART_UNSTABLE; HELDOUT_PROJECTION_INCONSISTENT; RING_BODY_SURFACE_PENETRATION。

[主解与全部初值](local_results/G03_004/E2/SELECTION.json)；[全来源投影](figures/G03_004_ALL_VIEW_OVERLAYS.png)；[六方向主体与Ring](figures/G03_004_SIX_DIRECTION_BODIES.png)。

- `MAX__G03_v004_raw00014`：role=FIT, IoU=0.8486927717969952, FN=3510, FP=327；[逐帧本地图](figures/overlays/MAX__G03_v004_raw00014.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `MAX__G03_v004_raw00116`：role=FIT, IoU=0.860345598093252, FN=3290, FP=460；[逐帧本地图](figures/overlays/MAX__G03_v004_raw00116.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `MAX__G03_v004_raw00220`：role=HOLDOUT, IoU=0.857339410095451, FN=2940, FP=378；[逐帧本地图](figures/overlays/MAX__G03_v004_raw00220.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `MAX__G03_v004_raw00408`：role=FIT, IoU=0.860827332105175, FN=3094, FP=230；[逐帧本地图](figures/overlays/MAX__G03_v004_raw00408.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `MAX__G03_v004_raw00552`：role=FIT, IoU=0.848615317254716, FN=3706, FP=443；[逐帧本地图](figures/overlays/MAX__G03_v004_raw00552.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `MAX__G03_v004_raw00642`：role=FIT, IoU=0.854637257507308, FN=4124, FP=799；[逐帧本地图](figures/overlays/MAX__G03_v004_raw00642.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `OLD018__G03_key00_raw00100`：role=FIT, IoU=0.8603123038871867, FN=3388, FP=396；[逐帧本地图](figures/overlays/OLD018__G03_key00_raw00100.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `OLD018__G03_key04_raw00554`：role=FIT, IoU=0.8467744879705013, FN=3772, FP=425；[逐帧本地图](figures/overlays/OLD018__G03_key04_raw00554.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `OLD018__G03_v004_raw00161`：role=HOLDOUT, IoU=0.8525229544161859, FN=2993, FP=637；[逐帧本地图](figures/overlays/OLD018__G03_v004_raw00161.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `OLD018__G03_v004_raw00406`：role=FIT, IoU=0.8618393500293157, FN=3067, FP=232；[逐帧本地图](figures/overlays/OLD018__G03_v004_raw00406.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `OLD018__G03_v004_raw00651`：role=HOLDOUT, IoU=0.8607355169600186, FN=4102, FP=677；[逐帧本地图](figures/overlays/OLD018__G03_v004_raw00651.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `OLD018__G03_v004_raw00834`：role=HOLDOUT, IoU=0.871242682519943, FN=3737, FP=508；[逐帧本地图](figures/overlays/OLD018__G03_v004_raw00834.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。

## G03_005 / E1

原因：MULTISTART_UNSTABLE。

[主解与全部初值](local_results/G03_005/E1/SELECTION.json)；[全来源投影](figures/G03_005_ALL_VIEW_OVERLAYS.png)；[六方向主体与Ring](figures/G03_005_SIX_DIRECTION_BODIES.png)。

- `MAX__G03_v005_raw00029`：role=FIT, IoU=0.8806060799795417, FN=2945, FP=790；[逐帧本地图](figures/overlays/MAX__G03_v005_raw00029.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `MAX__G03_v005_raw00131`：role=FIT, IoU=0.8184555744003322, FN=4017, FP=1228；[逐帧本地图](figures/overlays/MAX__G03_v005_raw00131.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `MAX__G03_v005_raw00171`：role=HOLDOUT, IoU=0.8343068668070366, FN=4343, FP=536；[逐帧本地图](figures/overlays/MAX__G03_v005_raw00171.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `MAX__G03_v005_raw00445`：role=HOLDOUT, IoU=0.8994229183841714, FN=2292, FP=1246；[逐帧本地图](figures/overlays/MAX__G03_v005_raw00445.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `MAX__G03_v005_raw00589`：role=FIT, IoU=0.8775295268186264, FN=3256, FP=0；[逐帧本地图](figures/overlays/MAX__G03_v005_raw00589.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `MAX__G03_v005_raw00633`：role=FIT, IoU=0.9401433133421606, FN=1399, FP=138；[逐帧本地图](figures/overlays/MAX__G03_v005_raw00633.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。

## G03_005 / E2

原因：NOT_ALL_THREE_STARTS_ELIGIBLE; MULTISTART_UNSTABLE; RING_BODY_SURFACE_PENETRATION。

[主解与全部初值](local_results/G03_005/E2/SELECTION.json)；[全来源投影](figures/G03_005_ALL_VIEW_OVERLAYS.png)；[六方向主体与Ring](figures/G03_005_SIX_DIRECTION_BODIES.png)。

- `MAX__G03_v005_raw00029`：role=FIT, IoU=0.8962505598566767, FN=2478, FP=765；[逐帧本地图](figures/overlays/MAX__G03_v005_raw00029.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `MAX__G03_v005_raw00131`：role=FIT, IoU=0.845165843330981, FN=3711, FP=677；[逐帧本地图](figures/overlays/MAX__G03_v005_raw00131.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `MAX__G03_v005_raw00171`：role=HOLDOUT, IoU=0.8486399781577421, FN=4044, FP=391；[逐帧本地图](figures/overlays/MAX__G03_v005_raw00171.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `MAX__G03_v005_raw00445`：role=HOLDOUT, IoU=0.93701370878103, FN=1054, FP=1156；[逐帧本地图](figures/overlays/MAX__G03_v005_raw00445.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `MAX__G03_v005_raw00589`：role=FIT, IoU=0.8926297655606321, FN=2751, FP=116；[逐帧本地图](figures/overlays/MAX__G03_v005_raw00589.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `MAX__G03_v005_raw00633`：role=FIT, IoU=0.9466445797056784, FN=967, FP=418；[逐帧本地图](figures/overlays/MAX__G03_v005_raw00633.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。

## G05_004 / E1

原因：MULTISTART_UNSTABLE; RING_BODY_SURFACE_PENETRATION。

[主解与全部初值](local_results/G05_004/E1/SELECTION.json)；[全来源投影](figures/G05_004_ALL_VIEW_OVERLAYS.png)；[六方向主体与Ring](figures/G05_004_SIX_DIRECTION_BODIES.png)。

- `MAX__G05_v004_raw00189`：role=FIT, IoU=0.8842486024334101, FN=1683, FP=1485；[逐帧本地图](figures/overlays/MAX__G05_v004_raw00189.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `MAX__G05_v004_raw00248`：role=FIT, IoU=0.8727279095016286, FN=1896, FP=1738；[逐帧本地图](figures/overlays/MAX__G05_v004_raw00248.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `MAX__G05_v004_raw00395`：role=FIT, IoU=0.8975590628369767, FN=2077, FP=1058；[逐帧本地图](figures/overlays/MAX__G05_v004_raw00395.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `MAX__G05_v004_raw00526`：role=HOLDOUT, IoU=0.8998333641918164, FN=2243, FP=1003；[逐帧本地图](figures/overlays/MAX__G05_v004_raw00526.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `MAX__G05_v004_raw00616`：role=FIT, IoU=0.9076322149159782, FN=3136, FP=151；[逐帧本地图](figures/overlays/MAX__G05_v004_raw00616.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `MAX__G05_v004_raw00899`：role=HOLDOUT, IoU=0.8948580641446421, FN=2340, FP=1312；[逐帧本地图](figures/overlays/MAX__G05_v004_raw00899.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `OLD018__G05_key04_raw00542`：role=HOLDOUT, IoU=0.8995196279411315, FN=2201, FP=1083；[逐帧本地图](figures/overlays/OLD018__G05_key04_raw00542.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `OLD018__G05_v004_raw00117`：role=EXCLUDED_DIAGNOSTIC, IoU=0.877271915729334, FN=1769, FP=1668；[逐帧本地图](figures/overlays/OLD018__G05_v004_raw00117.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `OLD018__G05_v004_raw00217`：role=FIT, IoU=0.8861958439874671, FN=1713, FP=1447；[逐帧本地图](figures/overlays/OLD018__G05_v004_raw00217.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `OLD018__G05_v004_raw00337`：role=FIT, IoU=0.8949915966386555, FN=1962, FP=1162；[逐帧本地图](figures/overlays/OLD018__G05_v004_raw00337.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `OLD018__G05_v004_raw00377`：role=HOLDOUT, IoU=0.8937194858680129, FN=1935, FP=1265；[逐帧本地图](figures/overlays/OLD018__G05_v004_raw00377.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `OLD018__G05_v004_raw00457`：role=FIT, IoU=0.8958379843725084, FN=2100, FP=1166；[逐帧本地图](figures/overlays/OLD018__G05_v004_raw00457.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `OLD018__G05_v004_raw00636`：role=HOLDOUT, IoU=0.9155121260785541, FN=2869, FP=235；[逐帧本地图](figures/overlays/OLD018__G05_v004_raw00636.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `OLD018__G05_v004_raw00796`：role=FIT, IoU=0.909437958034943, FN=2583, FP=667；[逐帧本地图](figures/overlays/OLD018__G05_v004_raw00796.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。

## G05_004 / E2

原因：NOT_ALL_THREE_STARTS_ELIGIBLE; MULTISTART_UNSTABLE; RING_BODY_SURFACE_PENETRATION。

[主解与全部初值](local_results/G05_004/E2/SELECTION.json)；[全来源投影](figures/G05_004_ALL_VIEW_OVERLAYS.png)；[六方向主体与Ring](figures/G05_004_SIX_DIRECTION_BODIES.png)。

- `MAX__G05_v004_raw00189`：role=FIT, IoU=0.8771265163382026, FN=1806, FP=1567；[逐帧本地图](figures/overlays/MAX__G05_v004_raw00189.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `MAX__G05_v004_raw00248`：role=FIT, IoU=0.8584629332589442, FN=2196, FP=1863；[逐帧本地图](figures/overlays/MAX__G05_v004_raw00248.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `MAX__G05_v004_raw00395`：role=FIT, IoU=0.8881300813008131, FN=2235, FP=1205；[逐帧本地图](figures/overlays/MAX__G05_v004_raw00395.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `MAX__G05_v004_raw00526`：role=HOLDOUT, IoU=0.8902195608782435, FN=2413, FP=1162；[逐帧本地图](figures/overlays/MAX__G05_v004_raw00526.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `MAX__G05_v004_raw00616`：role=FIT, IoU=0.9057743077009492, FN=3184, FP=171；[逐帧本地图](figures/overlays/MAX__G05_v004_raw00616.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `MAX__G05_v004_raw00899`：role=HOLDOUT, IoU=0.8799302618040471, FN=2635, FP=1566；[逐帧本地图](figures/overlays/MAX__G05_v004_raw00899.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `OLD018__G05_key04_raw00542`：role=HOLDOUT, IoU=0.8908642576638558, FN=2336, FP=1249；[逐帧本地图](figures/overlays/OLD018__G05_key04_raw00542.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `OLD018__G05_v004_raw00117`：role=EXCLUDED_DIAGNOSTIC, IoU=0.8692971200456231, FN=1948, FP=1719；[逐帧本地图](figures/overlays/OLD018__G05_v004_raw00117.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `OLD018__G05_v004_raw00217`：role=FIT, IoU=0.877257224914737, FN=1884, FP=1535；[逐帧本地图](figures/overlays/OLD018__G05_v004_raw00217.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `OLD018__G05_v004_raw00337`：role=FIT, IoU=0.8881409290331224, FN=2069, FP=1271；[逐帧本地图](figures/overlays/OLD018__G05_v004_raw00337.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `OLD018__G05_v004_raw00377`：role=HOLDOUT, IoU=0.8848556977090152, FN=2078, FP=1405；[逐帧本地图](figures/overlays/OLD018__G05_v004_raw00377.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `OLD018__G05_v004_raw00457`：role=FIT, IoU=0.8871705303270879, FN=2252, FP=1301；[逐帧本地图](figures/overlays/OLD018__G05_v004_raw00457.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `OLD018__G05_v004_raw00636`：role=HOLDOUT, IoU=0.9055923193751356, FN=3113, FP=368；[逐帧本地图](figures/overlays/OLD018__G05_v004_raw00636.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `OLD018__G05_v004_raw00796`：role=FIT, IoU=0.8966969629793837, FN=2860, FP=868；[逐帧本地图](figures/overlays/OLD018__G05_v004_raw00796.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。

## G05_005 / E1

原因：NOT_EVALUABLE_INSUFFICIENT_MULTIVIEW。

[不足多视角状态](local_results/G05_005/E1/SELECTION.json)；[原始图像证据](figures/G05_005_ALL_VIEW_OVERLAYS.png)。

- `MAX__G05_v005_raw00219`：role=NOT_EVALUABLE, IoU=None, FN=None, FP=None；[逐帧本地图](figures/overlays/MAX__G05_v005_raw00219.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。

## G05_005 / E2

原因：NOT_EVALUABLE_INSUFFICIENT_MULTIVIEW。

[不足多视角状态](local_results/G05_005/E2/SELECTION.json)；[原始图像证据](figures/G05_005_ALL_VIEW_OVERLAYS.png)。

- `MAX__G05_v005_raw00219`：role=NOT_EVALUABLE, IoU=None, FN=None, FP=None；[逐帧本地图](figures/overlays/MAX__G05_v005_raw00219.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。

## G05_PHOTO / E1

原因：NOT_EVALUABLE_INSUFFICIENT_MULTIVIEW。

[不足多视角状态](local_results/G05_PHOTO/E1/SELECTION.json)；[原始图像证据](figures/G05_PHOTO_ALL_VIEW_OVERLAYS.png)。

- `MAX__G05_photo002`：role=NOT_EVALUABLE, IoU=None, FN=None, FP=None；[逐帧本地图](figures/overlays/MAX__G05_photo002.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。

## G05_PHOTO / E2

原因：NOT_EVALUABLE_INSUFFICIENT_MULTIVIEW。

[不足多视角状态](local_results/G05_PHOTO/E2/SELECTION.json)；[原始图像证据](figures/G05_PHOTO_ALL_VIEW_OVERLAYS.png)。

- `MAX__G05_photo002`：role=NOT_EVALUABLE, IoU=None, FN=None, FP=None；[逐帧本地图](figures/overlays/MAX__G05_photo002.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。

## G06_004 / E1

原因：PARAMETER_BOUND_OR_AXIS_RATIO_RISK; MULTISTART_UNSTABLE; RING_BODY_SURFACE_PENETRATION。

[主解与全部初值](local_results/G06_004/E1/SELECTION.json)；[全来源投影](figures/G06_004_ALL_VIEW_OVERLAYS.png)；[六方向主体与Ring](figures/G06_004_SIX_DIRECTION_BODIES.png)。

- `MAX__G06_004_growth_r01`：role=HOLDOUT, IoU=0.9388175985334556, FN=377, FP=157；[逐帧本地图](figures/overlays/MAX__G06_004_growth_r01.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `MAX__G06_v004_raw00046`：role=FIT, IoU=0.9288232989421444, FN=462, FP=83；[逐帧本地图](figures/overlays/MAX__G06_v004_raw00046.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `MAX__G06_v004_raw00109`：role=FIT, IoU=0.9469150174621653, FN=381, FP=75；[逐帧本地图](figures/overlays/MAX__G06_v004_raw00109.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `MAX__G06_v004_raw00458`：role=HOLDOUT, IoU=0.9338971733808146, FN=435, FP=159；[逐帧本地图](figures/overlays/MAX__G06_v004_raw00458.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `MAX__G06_v004_raw00606`：role=FIT, IoU=0.9480174338258743, FN=284, FP=205；[逐帧本地图](figures/overlays/MAX__G06_v004_raw00606.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `MAX__G06_v004_raw00744`：role=FIT, IoU=0.9309780830879948, FN=708, FP=136；[逐帧本地图](figures/overlays/MAX__G06_v004_raw00744.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `MAX__G06_v004_raw00944`：role=HOLDOUT, IoU=0.9240242516104585, FN=861, FP=342；[逐帧本地图](figures/overlays/MAX__G06_v004_raw00944.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `MAX__G06_v004_raw01037`：role=HOLDOUT, IoU=0.9226532711977243, FN=818, FP=460；[逐帧本地图](figures/overlays/MAX__G06_v004_raw01037.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `OLD018__G06_004_growth_r01`：role=EXCLUDED_DIAGNOSTIC, IoU=0.9391095341650452, FN=366, FP=166；[逐帧本地图](figures/overlays/OLD018__G06_004_growth_r01.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `OLD018__G06_004_growth_r03`：role=EXCLUDED_DIAGNOSTIC, IoU=0.9414535666218035, FN=246, FP=276；[逐帧本地图](figures/overlays/OLD018__G06_004_growth_r03.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `OLD018__G06_004_new_r00`：role=FIT, IoU=0.940223862824482, FN=406, FP=96；[逐帧本地图](figures/overlays/OLD018__G06_004_new_r00.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `OLD018__G06_004_ref04`：role=FIT, IoU=0.9469045343527662, FN=365, FP=135；[逐帧本地图](figures/overlays/OLD018__G06_004_ref04.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `OLD018__G06_v004_raw00348`：role=FIT, IoU=0.9451065366558324, FN=269, FP=187；[逐帧本地图](figures/overlays/OLD018__G06_v004_raw00348.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `OLD018__G06_v004_raw00721`：role=HOLDOUT, IoU=0.9288957423113167, FN=672, FP=158；[逐帧本地图](figures/overlays/OLD018__G06_v004_raw00721.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `OLD018__G06_v004_raw00940`：role=FIT, IoU=0.9307584804980308, FN=788, FP=302；[逐帧本地图](figures/overlays/OLD018__G06_v004_raw00940.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。

## G06_004 / E2

原因：MULTISTART_UNSTABLE; HELDOUT_PROJECTION_INCONSISTENT; RING_BODY_SURFACE_PENETRATION。

[主解与全部初值](local_results/G06_004/E2/SELECTION.json)；[全来源投影](figures/G06_004_ALL_VIEW_OVERLAYS.png)；[六方向主体与Ring](figures/G06_004_SIX_DIRECTION_BODIES.png)。

- `MAX__G06_004_growth_r01`：role=HOLDOUT, IoU=0.7864786993208479, FN=928, FP=1147；[逐帧本地图](figures/overlays/MAX__G06_004_growth_r01.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `MAX__G06_v004_raw00046`：role=FIT, IoU=0.752058448335846, FN=1089, FP=1049；[逐帧本地图](figures/overlays/MAX__G06_v004_raw00046.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `MAX__G06_v004_raw00109`：role=FIT, IoU=0.7806796727501574, FN=1072, FP=1019；[逐帧本地图](figures/overlays/MAX__G06_v004_raw00109.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `MAX__G06_v004_raw00458`：role=HOLDOUT, IoU=0.7695716395864106, FN=1012, FP=1328；[逐帧本地图](figures/overlays/MAX__G06_v004_raw00458.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `MAX__G06_v004_raw00606`：role=FIT, IoU=0.8228756884343037, FN=835, FP=966；[逐帧本地图](figures/overlays/MAX__G06_v004_raw00606.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `MAX__G06_v004_raw00744`：role=FIT, IoU=0.8600096711798839, FN=1421, FP=316；[逐帧本地图](figures/overlays/MAX__G06_v004_raw00744.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `MAX__G06_v004_raw00944`：role=HOLDOUT, IoU=0.8767149758454106, FN=1881, FP=33；[逐帧本地图](figures/overlays/MAX__G06_v004_raw00944.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `MAX__G06_v004_raw01037`：role=HOLDOUT, IoU=0.8789789232956301, FN=1842, FP=116；[逐帧本地图](figures/overlays/MAX__G06_v004_raw01037.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `OLD018__G06_004_growth_r01`：role=EXCLUDED_DIAGNOSTIC, IoU=0.785523613963039, FN=920, FP=1169；[逐帧本地图](figures/overlays/OLD018__G06_004_growth_r01.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `OLD018__G06_004_growth_r03`：role=EXCLUDED_DIAGNOSTIC, IoU=0.7922143579373104, FN=805, FP=1250；[逐帧本地图](figures/overlays/OLD018__G06_004_growth_r03.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `OLD018__G06_004_new_r00`：role=FIT, IoU=0.7749651399764025, FN=1077, FP=1021；[逐帧本地图](figures/overlays/OLD018__G06_004_new_r00.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `OLD018__G06_004_ref04`：role=FIT, IoU=0.8191667487442136, FN=965, FP=871；[逐帧本地图](figures/overlays/OLD018__G06_004_ref04.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `OLD018__G06_v004_raw00348`：role=FIT, IoU=0.7907127429805616, FN=798, FP=1140；[逐帧本地图](figures/overlays/OLD018__G06_v004_raw00348.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `OLD018__G06_v004_raw00721`：role=HOLDOUT, IoU=0.8588452500839208, FN=1281, FP=401；[逐帧本地图](figures/overlays/OLD018__G06_v004_raw00721.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。
- `OLD018__G06_v004_raw00940`：role=FIT, IoU=0.8792245557350565, FN=1834, FP=35；[逐帧本地图](figures/overlays/OLD018__G06_v004_raw00940.png)，Git交付图集使用上方链接；详细轮廓误差见metrics/ALL_VIEW_EVALUATION.csv。

## 上游资格及重复身份

- OLD018__G05_v004_raw00117：UPSTREAM_CAMERA_EXPLORATORY_NOT_FIT；保留诊断，不作为独立FIT/HOLDOUT。
- OLD018__G06_004_growth_r01：DUPLICATE_RGB_NOT_INDEPENDENT；保留诊断，不作为独立FIT/HOLDOUT。
- OLD018__G06_004_growth_r03：UPSTREAM_CAMERA_EXPLORATORY_NOT_FIT；保留诊断，不作为独立FIT/HOLDOUT。

## 固定审计表

| 审计项目 | 必须汇报 |
| --- | --- |
| 目标组数 | 4独立物理组；75来源（74唯一RGB）；主分析每方案4组，附加005有2池 |
| 本算法独立成功 | E1=4/4、E2=4/4主组独立数值输出；附加各2/2池；完整科研验收0/4组每方案，不能当作测量正确 |
| 本算法失败 | 主组无数值输出失败；完整验收8/8主组方案失败；3单视角池×2方案为null/NaN；36初值有2个未收敛且排除主解 |
| 历史测量值回退 | 0；Body-U和旧DT+AMS只在预测冻结后作对照 |
| 失败组及具体原因 | [逐组失败台账](FAILURE_LEDGER.md)，关联候选、逐帧投影和图集 |
| 最终统计样本 | 仅独立成功主分析4组每方案；23张相同HOLDOUT（各池9/4/5/5）；全部75来源始终登记；不把来源数当独立组数 |
| 是否使用 GT 选择算法 | 否；GT未读，协议→DXY→视角/源码冻结→全部预测冻结→独立评价的SHA回执见provenance |
