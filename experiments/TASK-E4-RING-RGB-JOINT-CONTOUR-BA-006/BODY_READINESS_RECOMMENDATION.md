# BODY_READINESS_RECOMMENDATION

`BODY_NOT_USED_FOR_CAMERA_OPTIMIZATION`

## 结论

**本轮不改变 004 的准入结论，也不建议在相机未做 A0/A1/A2 对照前进入 Body 初始化。**

| 实例 | 004 结论 | 本轮追加证据 | 建议 |
|---|---|---|---|
| G06/005 | READY_WITH_CAUTION（5 CORE, held 2.47） | Ring 轮廓质量最好（DXY 残差低） | **可进入受控 Body 初始化** |
| G05/005 | READY_WITH_CAUTION | RAW-V2 N=16 held 2.07 | 可谨慎进入 |
| G03/005 | READY_WITH_CAUTION（2 CORE） | N=32 时 VALIDATED=6, held 2.47 | 可谨慎进入 |
| G01/004, G01/005, G05/004, G06/004 | READY_WITH_CAUTION | — | 可谨慎进入 |
| G02/004, G02/005 | CAMERA_REPAIR_REQUIRED | 密度可改善（N=22 held 6.61） | 先修相机 |
| G03/004 | CAMERA_REPAIR_REQUIRED | 所有密度均 75–127 px | 先修相机 |

## 前提

本建议基于 004 的相机（冻结 8/16 视角 DXY 之外的原始边界方案）。
本轮 A1/A2 **未运行**，因此**没有证据**表明 DXY 柔性轮廓能改善相机；在得到该证据之前，不应把新方法写入准入判据。
