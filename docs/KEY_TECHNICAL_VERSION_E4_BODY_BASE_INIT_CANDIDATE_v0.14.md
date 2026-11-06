# E4 关键技术版本候选 v0.14：九例主体/基底初始化

状态：CANDIDATE / AWAITING_HUMAN_REVIEW，未替代正式主线。继承v0.13的修复PyTorch3D/Ring-Aware和原生深度语义，新增统一低维主体拟合与独立背景平面/接触代理。相机、HERO、Mask、CAD、DXY冻结；历史Gate不作为本任务入组否决条件。

任务：[TASK-E4-BODY-BASE-INIT-009技术报告](../experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/runs/BODY_BASE_INIT_009/TECHNICAL_REPORT.md)。预注册e1daf3e。Ip G01/G02/G03，Is G07/G04/G05，IIa G06/G08/G09；G08=IIa22，G09=新IIa4.5。新病例按授权复用原选帧/SIFT/Ring-First/HERO流程；排除一份误重复G08的临时计算，保留失败记录。

统一9参数椭球，固定三初值，数据残差触发有界星凸；真实背景平面稳定且接触广泛才尝试6→7→9参数保留冠面。无类型专用优化分支、无自由顶点或新训练。推断基底闭合面不进入图像/深度监督。

九例均输出；B留出IoU提高7/9、固定深度代价降低8/9；五例截断，存在轮廓/覆盖退化。B/C各5/9无CAD相交，G03/G05/G06/G07仍有微米级相交，未PASS。不能凭地下结构移除宣布解剖基底正确，真实3D准确度NOT_EVALUABLE。所有候选、失败及完整本地图保留，未经人工审核不接入自由Mesh更新。
