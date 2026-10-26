# Phase-C默认真实P0可视化

后续Phase-C使用`real_p0_renderer.py`。它优先包装C0/M0原脚本的`basis/view/limits`；历史脚本不可用时使用同目录逐字提取的三函数副本。脚本存在但哈希不同则拒绝渲染，不静默切换版本。原脚本、SHA与配置见`real_p0_renderer_provenance.json`。

默认观察角(-65°,22°)、点大小0.8、CAD Ring原顶点每7个取1个仅作环显示、Ring点大小0.4、暗色#26343d、固定等比例毫米轴、网格0.15及原比例尺。005原认可局部视角(0°,0°)仍可通过`angle`显式调用。点云使用全部源点及源RGB，不改几何，不填孔，不插值，不平滑。该方式是原有真实三维点投影与深度排序的scatter绘制，不是新建光照Mesh渲染器。

比较时先用Raw计算共同`limits()`，三个状态共享范围、angle、size、DPI。不能按Cleaned重新缩小窗口。保留完整异常范围，局部放大另标窗口与比例尺。

API：`limits([P1,P2], ring, angle)`，`view(ax, P, rgb, ring, bounds, angle, title)`。独立命令运行`python visualization/real_p0_renderer.py --help`。本任务复现示例见实验目录`TECHNICAL_REPORT.md`。
