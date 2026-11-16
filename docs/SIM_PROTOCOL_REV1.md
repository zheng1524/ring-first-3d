# G01-like 受控仿真：人工批准的独立修订

用户于本轮明确批准将上一轮真实部署认证门槛修订为仿真质量指标。原schema 1/2/3、历史TASK、失败证据和回归测试均保留。独立schema 4的任务是`TASK-E4-G01-DUALVIDEO-BODY-ANCHORED-REGISTRATION-001-SIM-PROTOCOL-REV1`，不会恢复或修改历史G0失败运行。

仿真保留原004/005相机来源及各自Camera-to-Ring，将两者放入共同虚拟R10坐标系。一个真实Blender息肉仅使用共享刚体平移摆放，不缩放、不按视频独立移动。摆放由冻结候选和FIT原轮廓选择，属于generator的仿真生成；不能把其参数交给Body预测器。原图投影差异与缺少真实部署认证仍记录。单位、SHA、相机坐标、轴向深度、完整网格和角色边界失败继续阻断。

阶段：Preflight→Contracts→82项回归→G0生成→G1独立初始化/评价→G2中介对应/评价→S0/S1预测Smoke及独立评价→G3完整矩阵→G4独立评价/可视化→Artifacts→accept。原Runner的前置依赖、预算、独立attempt、原子快照、源码及环境冻结机制直接复用，没有force或skip。

角色由注册代码决定：G0 generator可读原GT；G1/G2/G3 predictor不得读GT或评价目录；G3还禁止读取G0干净相机目录及G2干净坐标锚点，必须以受扰相机重新计算中介。evaluator仅在相关预测冻结后读GT。Body选择遵循固定E1/E2/显式代理顺序与FIT目标，无GT选参。正式DXY的candidate、strict-stability和代理状态分别记录；非收敛但有限的诊断模型保留标签，不能称合格重建。

主条件按004/005：S0=I/I、S1=I/A、S2=I/B、S3=A/B、S4=A/A。A=+Y2°和+X0.5mm，B=+Y3°和+X0.3mm，旋转中心为Ring原点，世界左乘；相机、Ring和完整局部Mesh同步变换。L1单独为005相机局部A，CAD Ring固定。种子20261116。

每视频只估计一个共享SE(3)，Body冻结。M0、Open3D Robust ICP、二维中介联合优化、Ring-only、直接Pixel对照和Ring辅助联合优化均独立产生结果。优化约束可抽样，最终输出应用于完整原局部Mesh全部顶点；边长和Face拓扑断言排除Body替换与形变。Ring-only采用无标记CAD的中心/法向最小扭转规范，本轮Y倾斜可以被它直接解释，不能将此恢复归功于二维主体。S4用相对SE(3)与共同规范评价，不能错误统计共有世界误差。

运行方式：

```bash
bash tools/research/run.sh tools/research/policy.py check --task experiments/TASK-E4-G01-DUALVIDEO-BODY-ANCHORED-REGISTRATION-001-SIM-PROTOCOL-REV1/TASK.yaml
bash tools/research/run.sh tools/research/policy.py run --task experiments/TASK-E4-G01-DUALVIDEO-BODY-ANCHORED-REGISTRATION-001-SIM-PROTOCOL-REV1/TASK.yaml --run-dir /absolute/project/experiments/TASK-E4-G01-DUALVIDEO-BODY-ANCHORED-REGISTRATION-001-SIM-PROTOCOL-REV1/runs/new-run --stage all
bash tools/research/run.sh tools/research/policy.py accept --task experiments/TASK-E4-G01-DUALVIDEO-BODY-ANCHORED-REGISTRATION-001-SIM-PROTOCOL-REV1/TASK.yaml --run-dir /absolute/project/experiments/TASK-E4-G01-DUALVIDEO-BODY-ANCHORED-REGISTRATION-001-SIM-PROTOCOL-REV1/runs/new-run
```

某个方法不收敛或不准确为科研负结果，不会切换到另一方法的预测或停止其他合法对照。数据损坏、内部坐标/几何/权限错误或必要计算不可执行才阻断。所有新失败规则均为候选，未经审查不晋升永久规则。accept只验收执行与产物完整性，科学结论始终等待人工审阅。
