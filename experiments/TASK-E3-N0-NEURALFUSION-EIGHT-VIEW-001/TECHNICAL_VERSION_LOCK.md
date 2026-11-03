# Technical version lock — v1.0

当前关键技术文档：../../docs/KEY_TECHNICAL_VERSION_v1.0.md（首次建立，研究者2026-11-03授权）。具体脚本SHA为provenance/SCRIPT_VERSION_AUDIT.json；历史报告阅读记录为provenance/READING_AND_VERSION_RECEIPTS.json。

版本文档SHA256：dad083594292801582c7cdd242b16fdce684079fb02bc26468e435e77d352118。

当前状态：技术接口已冻结；输入名单/资格、清理派生文件和各组物理域在正式推理前依次写入config，BEFORE_GPU冻结全部SHA。Camera Gate v0.1仍为候选规范，逐源资格与条件性入组区分。旧F0质量停机规则不适用本轮，不回写历史结果。

官方代码4f0c14f；checkpoint 3ac6dc9f…；无训练。既有六源V6保留历史删除ID，新来源和新组一致复用A2投影及最新B类Mask语义；不外推G01人工XYZ删除。每组各自全保留XYZ+CAD域，Gate A原裁剪函数不变。
