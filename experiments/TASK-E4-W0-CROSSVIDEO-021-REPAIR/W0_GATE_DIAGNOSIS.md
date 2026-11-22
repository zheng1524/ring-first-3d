# W0_GATE_DIAGNOSIS

## G03：唯一具备 ACCEPT 的组

004 6 ACCEPT / 10 QUARANTINE（held p95 > 8 px），005 16 ACCEPT。

## G01：POSE_UNCERTAIN

004：14 QUARANTINE（held p95 超标）+ 2 RING_ERROR（ring_raw > 2 px）；005：15 QUARANTINE + 1 EVAL。
held 中位 6.02 / 2.63 px，p95 33.8 / 18.6 px —— 不是"观测不足"，是**残差尾部太大**。

## G05：OBSERVATION_INSUFFICIENT

004：13 INSUFFICIENT_EVIDENCE（有效轨迹 <20）+ 3 QUARANTINE；005：16 INSUFFICIENT_EVIDENCE。
**这一类不能读成"相机错误"**，只能读成"证据不足以判断"。005 的 held 中位 27.15 px 提示其单视频几何本身也很差，
但门控给出的判定是证据不足。

## 未修改门限

三个组使用同一份 `CAMERA_ADMISSION_POLICY.yaml`，没有为任何组调整阈值。
