# 020 预注册

主实验仅共享SE(3)：完整RoMa左乘扰动，Ring四通道+双向SIFT+2D-only极线+弱先验，无主体/HERO。

{
  "seed": 20261111,
  "views": "exact019 0048FIT+5HOLDOUT,00552FIT+3HOLDOUT",
  "initial": "historical full RoMa004_from005; no yaw projection",
  "pose_scale": [
    0.6,
    0.6,
    0.6,
    0.08726646259971647,
    0.08726646259971647,
    0.08726646259971647
  ],
  "ring_weights": {
    "M": 0.25,
    "I": 0.35,
    "C": 0.05,
    "O": 0.35
  },
  "sigma_curve_px": 3.0,
  "feature_sigma_px": 3.0,
  "lambda_feature": 0.2,
  "lambda_epi": 0.02,
  "lambda_prior": 0.01,
  "lambda_body_R4": 1.0,
  "iterations": 80,
  "Adam_lr": 0.01,
  "backtracks": 8,
  "accept_tolerance": 1e-06,
  "translation_bound_mm": 1.2,
  "rotation_bound_deg": 10.0,
  "normalization": "all Ring channels independently normalized, native direction-sector-balanced target frames; SIFT mean per landmark track then equal directions; EPI mean per pair then target",
  "mid": "720 DXY fitted samples, 72 bins; both-side1, one-side.25, unknown0, global channel .05; correlated auxiliary not independent truth",
  "occlusion": "Only DXY semantic visible samples, snapped <=2.5px to ORIGINAL Ring-Mask boundary (not preprocessed invented points); no fitted hidden I/O arcs. Polyp on nonmaterial side alone is NOT occlusion proof. Actual CAD selfvisibility. Mid unknown bins zero.",
  "CADcurve": "actual CAD occluding edges from face sign transitions; selfvisibility via O3D; classify against hard-rendered inner/outer; projected segment distances remain autograd differentiable; not r+/-wire planar circles",
  "surface": "fixed original Ring; body/HERO forbidden in R0-R3 and data selection",
  "arms": [
    "R0",
    "R1",
    "R2",
    "R3",
    "R3_MASK_ONLY",
    "R3_INNER_OUTER",
    "R4",
    "NEGATIVE_R3"
  ],
  "arm_order": "R1,R2,R3,ablations,negative -> freeze no-body predictions -> R4 -> freeze all -> evaluate HOLDOUT/body/HERO",
  "candidate": "RoMa primary; optional named3D robust rigid candidate if >=8 pairs, >=50% within.75mm, Ringcenter<=1.2mm and tilt<=10deg; evaluated same R3 objective, never body/HOLDOUT",
  "GT": false
}

冻结019全部FIT/HOLDOUT。R4只增加冻结004主体轮廓，不能反向选择R3。任何独立匹配/梯度/数值失败保留，不改参数搜索。预测冻结后才读取留出特征、主体评价和HERO。
