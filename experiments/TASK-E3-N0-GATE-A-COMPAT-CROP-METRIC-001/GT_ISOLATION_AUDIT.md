# GT隔离与数据保护

执行入口只读D0六份原始HERO白名单、冻结RGB/Mask/K/c2w/Ring和源码/PM文档。以源码审计方式阅读官方training/database.py及training/pipeline.py，没有导入或调用其Database、setup、训练/评估逻辑；官方test.py未执行。没有GT/Oracle/Blender/Dxy/历史测量值访问。

原模块构造使用官方FusionPipeline置入普通torch.nn.Module的_pipeline命名空间，严格加载完整state_dict；避免Lightning与graphics的GT数据库初始化。checkpoint仅用weights_only=True及审读过的EasyDict1.9类。所有参数放CPU。profile守卫禁止官方/torch.nn forward入口；运行模型前向计数0，CUDA initialized=False，training/graphics/Lightning模块导入列表为空。见config/MODEL_LOAD_GUARD_RESULTS.json。

common.py运行审计hook拒绝：任务外写入、GT/Oracle/Dxy路径、非白名单几何/权重、training/graphics/Lightning导入、执行期网络。负测试的GT_READ、TRAINING_IMPORT、HISTORY_WRITE在文件访问/创建前触发PermissionError；并未创建假GT文件。无效0/NaN/Ring/BG进入有效深度数量0。外部文件读清单与预期拒绝见config/GEOMETRY_RUNTIME_ACCESS.json。

只有用户在看到两张真实判读图后明确新增授权的一轮派生清理写入了新的depth/valid副本；原始Mask、native深度、Raw三角面、相机、Ring CAD和DAG完全保留。清理范围固定55个原native像素，46排除、9保留，其他点逐位不变。没有将派生数组覆盖回源文件。

六来源及其必要资产SHA、所有历史工作树HEAD/已修改文件SHA在最终交付前复核；结果见config/FINAL_PROTECTION_CHECK.json。新实验只在独立分支和任务目录写入，没有git clean/reset/force push。主Python环境未pip升级；权重与隔离依赖仅在task runtime下，不上传。

所有图均为真实RGB/Mask、真实HERO坐标或候选体素边界；无神经输出、纹理平面、GT对齐或补面。结构精度/测量误差/真实相机位姿GT均NOT_EVALUABLE，直径NaN，历史回退0。
