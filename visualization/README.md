# Phase-C默认真实P0可视化

正式主线版本：1.0.0。本次仅纳入Raw P0绘图及必要依赖；没有导入任何点云清理算法、清理参数或C/M/A阈值。函数来源/版本见`VERSION.json`。视频场景的实体Ring/背景扩展在独立任务分支审查。

当前实验分支另提供1.1.0-camera-preview：`project_camera/camera_rays/view_camera_rgb`使用完整冻结K/c2w，`draw_rgb_points`沿用原scatter尺寸、RGB、深度排序及无边线样式。息肉和背景须合并通过同一接口、同一artist绘制。`same_camera_scene.py`仅增加同一相机下的实际黑色CAD三角网格。真实帧对照不能使用旧的独立`--angle`正交入口；请使用本任务`code/scene004.py`。该扩展尚未进入main，也未修改科研相机或任何清理算法。

后续Phase-C使用`real_p0_renderer.py`。它优先包装C0/M0原脚本的`basis/view/limits`；历史脚本不可用时使用同目录逐字提取的三函数副本。脚本存在但哈希不同则拒绝渲染，不静默切换版本。原脚本、SHA与配置见`real_p0_renderer_provenance.json`。

默认观察角(-65°,22°)、点大小0.8、CAD Ring原顶点每7个取1个仅作环显示、Ring点大小0.4、暗色#26343d、固定等比例毫米轴、网格0.15及原比例尺。005原认可局部视角(0°,0°)仍可通过`angle`显式调用。点云使用全部源点及源RGB，不改几何，不填孔，不插值，不平滑。该方式是原有真实三维点投影与深度排序的scatter绘制，不是新建光照Mesh渲染器。

比较时先用Raw计算共同`limits()`，三个状态共享范围、angle、size、DPI。不能按Cleaned重新缩小窗口。保留完整异常范围，局部放大另标窗口与比例尺。

API：`limits([P1,P2], ring, angle)`，`view(ax, P, rgb, ring, bounds, angle, title)`。独立命令运行`python visualization/real_p0_renderer.py --help`。依赖见`requirements.txt`，原P0/RGB/CAD资产由调用方提供，不随模块上传。
