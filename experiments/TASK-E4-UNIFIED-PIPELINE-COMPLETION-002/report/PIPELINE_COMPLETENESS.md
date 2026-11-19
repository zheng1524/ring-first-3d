# 十段视频标准流程验收

| Group | Video | RGB_reference_bank | Ring_First | yaw | Ring_projection | HERO | PyTorch3D | B1 | B2 | GT_evaluation | HOLDOUT_evaluation |
|---|---|---|---|---|---|---|---|---|---|---|---|
| G01 | 004 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| G01 | 005 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| G02 | 004 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| G02 | 005 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| G03 | 004 | PASS | PARTIAL | PASS | PARTIAL | PASS | PASS | PASS | PASS | PASS | PARTIAL |
| G03 | 005 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| G05 | 004 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| G05 | 005 | PASS | PARTIAL | PARTIAL | PARTIAL | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN |
| G06 | 004 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| G06 | 005 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |

Ring-First PASS 要求全部冻结 FIT/HOLDOUT；FIT 完整但 HOLDOUT 失败记 PARTIAL。HERO PASS 仅覆盖冻结的 8 个 FIT 目标；HOLDOUT 不参与训练。原有参考未重训。每项 PASS 的实际路径、源码、日志见 PIPELINE_STAGE_RECORDS.csv。
