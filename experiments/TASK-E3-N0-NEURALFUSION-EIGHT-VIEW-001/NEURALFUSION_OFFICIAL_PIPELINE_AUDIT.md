# Official pipeline audit — 源码与上轮证据预检

本轮八视角执行状态：`NOT_RUN_PENDING_REQUIRED_VERSION_DOCUMENT`。以下是可核验的既有执行链，不冒充本轮新实验结果。

上一轮40ed60a的code/infer.py及NN_V6_F0_RUN.json表明：真实depth/Mask/K/c2w → 官方GPU unproject → FusionExtractor → FusionNet → FusionIntegrator写回latent → 官方get_translation调用Translator → SDF → skimage Marching Cubes level0 → 浮点坐标转毫米 → 完整原Mesh保存。严格加载1,403,920参数，前后逐值一致。它确实经过Translator，不是占据立方块或点云堆叠替代。

官方128³的get_translation分支只查询非零latent索引；容器其他位置保留未查询标志。官方导出在未知域使用+0.04哨兵，可能形成闭合边界面。必须把原Translator输出、known/queried mask和导出哨兵分开保存，不能把未查询0当零水平集，也不能将邻接Unknown自动判错并删面。本轮用户允许形状先验推断，推断支持/未知/真实深度支持应只影响评价与展示。

本轮待执行时需记录实际调用数、latent/count统计、译码点数和TSDF范围，核对MC浮点插值、坐标逆映射、拓扑/法线及几何身份；平面与平滑法线着色必须共用相同顶点和三角面，不做几何平滑/缩面/补洞。旧F0粗糙图像不能单独替代完整八视角正逆序结果。正式八视角中不再用几何质量阈值提前终止。
