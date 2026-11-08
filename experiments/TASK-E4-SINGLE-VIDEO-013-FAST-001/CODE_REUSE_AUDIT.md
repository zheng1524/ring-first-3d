# 直接复用与最小适配

直接复制013最终renderer、Ring-Aware、相机变换、FreeVertices、A3轮廓/深度/相对先验、O3N方向、原稀疏GeometryGuard、原训练循环与最佳SE3评价。来源及SHA见provenance/CODE_REUSE.json。

仅适配train_normalized中的逐视角反向传播、输入按病例核验、增量日志与完整checkpoint恢复，以及全体预测冻结后的禁止更新保护；统一diff见TRAINER_ADAPTATION.json。source调度/IO变化不改变Adam候选、回缩、接受条件、停止或预算。源FrozenPrior支持掩码从013原样复制，不因更多视角改变。

014只复用同视频RGB/Mask/K/c2w/SIDES缓存与方向选择接口；全部主视频Delta为Identity。绝不读取005到004的修正。密集Ring检查独立模块dense_audit014.py只被最终评价导入；不用其更严格拒绝规则改变本轮013优化。

原九例初值为013的原INITIAL（精确011 FINAL）；G10/G11仍明确为013已冻结配方等效初始化。S0结果复用经过验证的同方法缓存，S8/S16/S32失败绝不回退。没有HERO新推理、Mask重算、相机新估计或DXY写入。
