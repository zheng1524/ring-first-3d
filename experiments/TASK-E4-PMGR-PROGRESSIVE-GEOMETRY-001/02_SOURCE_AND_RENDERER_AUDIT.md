# 来源与渲染器核验

父分支实际本地和远端均4a09aedc669092d264f070ccac4fd12851097dd1，无用户脏修改。新工作树独立，未改旧CPU保护。inputs.py只AST提取纯IO/数学函数，逐文件SHA及函数名见metrics/PURE_SOURCE_EXTRACTION.json；没有导入A1 common.py。DXY仅使用父任务已输出的E1九参数结果。

官方nvdiffrast commit253ac4fcea7de5f396371124af597e6cc957bfae，源码文档明确OpenGL clip-space、bottom-up存储及antialias梯度。任务专用runtime安装ninja1.13.2和nvdiffrast0.4.0，未改历史环境。PyTorch2.7.1+cu128，CUDA12.8，RTX3060 Laptop6GiB。实际CV+Z→clip后翻回顶行，对26相机/初值通过P0_RENDERER_GATE；原生352×640/归档360×640映射保持pixel-center。

可微Mask为GPU实际三角面和黑色CAD联合zbuffer；精确原生深度选实际三角面首次命中，再求相机轴向Z的分段可微交点，没有把欧氏射线长度当Z。Native深度导数已与真实像素有限差分核验。历史A→B render函数采用Open3D相同射线/face/bary约定；此处的CPU对照是该渲染内核的受控重用，不运行历史GT评价程序。

每源路径/SHA和清理版本见assets_index/LOCAL_DATA_SOURCES.json，原始输入只读。G07缺当前合格清理，Raw压力状态未升级；G04/G05资格不足。背景G06旧ref04与当前A不同且Gate不足，所有Base关闭。B仅用于冻结评价，不反传。
