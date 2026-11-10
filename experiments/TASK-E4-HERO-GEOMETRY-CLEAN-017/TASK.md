# TASK-E4-HERO-GEOMETRY-CLEAN-017

用户授权：G01/G03/G05/G06，原生HERO几何可靠性与保守清理。复用Phase-C Type-2/Phase-D/E/E3-B代码，识别边缘拉伸、局部采样/深度/法向问题及Ring粘连。TRUSTED/UNCERTAIN/REJECTED，未知保留，不以近Ring、长边、曲率或低密度独立删除。保留全部来源和原Face/Pixel ID，保留顶点不移动。只交付原面子集和可靠性证据，不做重建、插值、补全、主体配准或融合。真实GT不参与清理；016/DXY/Ring-First/HERO/Mask/CAD冻结。四组处理后报告并停止，等待人工。

输入范围决议：本轮继承当前video004世界坐标，不引入G01_005或新跨视频资产。全部既有catalog原生深度纳入，G01=11、G03=1、G05=1、G06=5；共享上游RGB不是独立统计票。

原始Mesh子集为正式清理输出。未过滤原生深度格仅诊断，新增索引面不作为重建或适配输入。
