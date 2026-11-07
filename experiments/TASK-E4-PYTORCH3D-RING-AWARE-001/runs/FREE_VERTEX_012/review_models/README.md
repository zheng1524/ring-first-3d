# 审阅模型

九例各自目录包含011 C、011 FINAL、012 FINAL与独立黑色Ring CAD的PLY，坐标单位为毫米。灰色面是推断底盖，面ID与精确NPZ来源见MODEL_SEMANTICS.json，不是可见息肉GT。

FINAL012_with_Ring_m.glb用于交互旋转审阅。glTF标准单位是米，因此仅做mm×0.001的格式转换，Ring内径10mm对应0.010m；不是重新估计尺度。GLB可能为面颜色拆分顶点，拓扑、几何指标与测量使用本地原始NPZ，不以平滑外观冒充改进。所有GLB已重新载入核验几何包围范围。

这些都是冻结结果的轻量副本，没有删面、补洞、平滑、非刚性配准或GT形状回填。精确NPZ、PT恢复状态和全部中间Mesh路径/SHA见LOCAL_RESULTS_INDEX。

|病例|011 C|011 FINAL|012 FINAL|012带Ring交互模型|面身份|
|---|---|---|---|---|---|
|G01|[PLY](G01/C011_mm.ply)|[PLY](G01/FINAL011_mm.ply)|[PLY](G01/FINAL012_mm.ply)|[GLB](G01/FINAL012_with_Ring_m.glb)|[语义](G01/MODEL_SEMANTICS.json)|
|G02|[PLY](G02/C011_mm.ply)|[PLY](G02/FINAL011_mm.ply)|[PLY](G02/FINAL012_mm.ply)|[GLB](G02/FINAL012_with_Ring_m.glb)|[语义](G02/MODEL_SEMANTICS.json)|
|G03|[PLY](G03/C011_mm.ply)|[PLY](G03/FINAL011_mm.ply)|[PLY](G03/FINAL012_mm.ply)|[GLB](G03/FINAL012_with_Ring_m.glb)|[语义](G03/MODEL_SEMANTICS.json)|
|G07|[PLY](G07/C011_mm.ply)|[PLY](G07/FINAL011_mm.ply)|[PLY](G07/FINAL012_mm.ply)|[GLB](G07/FINAL012_with_Ring_m.glb)|[语义](G07/MODEL_SEMANTICS.json)|
|G04|[PLY](G04/C011_mm.ply)|[PLY](G04/FINAL011_mm.ply)|[PLY](G04/FINAL012_mm.ply)|[GLB](G04/FINAL012_with_Ring_m.glb)|[语义](G04/MODEL_SEMANTICS.json)|
|G05|[PLY](G05/C011_mm.ply)|[PLY](G05/FINAL011_mm.ply)|[PLY](G05/FINAL012_mm.ply)|[GLB](G05/FINAL012_with_Ring_m.glb)|[语义](G05/MODEL_SEMANTICS.json)|
|G06|[PLY](G06/C011_mm.ply)|[PLY](G06/FINAL011_mm.ply)|[PLY](G06/FINAL012_mm.ply)|[GLB](G06/FINAL012_with_Ring_m.glb)|[语义](G06/MODEL_SEMANTICS.json)|
|G08|[PLY](G08/C011_mm.ply)|[PLY](G08/FINAL011_mm.ply)|[PLY](G08/FINAL012_mm.ply)|[GLB](G08/FINAL012_with_Ring_m.glb)|[语义](G08/MODEL_SEMANTICS.json)|
|G09|[PLY](G09/C011_mm.ply)|[PLY](G09/FINAL011_mm.ply)|[PLY](G09/FINAL012_mm.ply)|[GLB](G09/FINAL012_with_Ring_m.glb)|[语义](G09/MODEL_SEMANTICS.json)|
