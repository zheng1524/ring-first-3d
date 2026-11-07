# 012失败与限制记录

九例均有独立末状态；以下限制不通过删面、换病例、选最好checkpoint或修改评价标准隐藏。

- **G01**：NO_ACCEPTANCE_FOR_80_ATTEMPTS，接受127/214；最大实际位移2.307654mm，主要候选拒绝[('FULL_FIT_OBJECTIVE', 1884)]。留出IoU变化+0.08530，原始分母深度覆盖变化+0.08464；CAD三角形相交对0→0，自交检出0。[原图/三阶段Mesh](figures/full/G01_Three_Stage_Detail.png)。
- **G02**：NO_ACCEPTANCE_FOR_80_ATTEMPTS，接受65/146；最大实际位移0.656493mm，主要候选拒绝[('AREA_DEGENERACY', 1511), ('FACE_ORIENTATION', 142), ('FULL_FIT_OBJECTIVE', 3)]。留出IoU变化+0.11909，原始分母深度覆盖变化+0.00000；CAD三角形相交对0→0，自交检出0。[原图/三阶段Mesh](figures/full/G02_Three_Stage_Detail.png)。
- **G03**：NO_ACCEPTANCE_FOR_80_ATTEMPTS，接受13/100；最大实际位移0.000341mm，主要候选拒绝[('FULL_FIT_OBJECTIVE', 1231), ('RING_WORSENING', 293)]。留出IoU变化+0.00000，原始分母深度覆盖变化+0.00000；CAD三角形相交对20→22，自交检出0。[原图/三阶段Mesh](figures/full/G03_Three_Stage_Detail.png)。
- **G07**：ACCEPTED_TARGET_REACHED，接受300/300；最大实际位移0.018565mm，主要候选拒绝[('RING_WORSENING', 2381)]。留出IoU变化+0.00172，原始分母深度覆盖变化+0.00000；CAD三角形相交对34→38，自交检出0。[原图/三阶段Mesh](figures/full/G07_Three_Stage_Detail.png)。
- **G04**：NO_ACCEPTANCE_FOR_80_ATTEMPTS，接受22/102；最大实际位移0.261384mm，主要候选拒绝[('AREA_DEGENERACY', 1354), ('FACE_ORIENTATION', 58)]。留出IoU变化+0.06219，原始分母深度覆盖变化+0.01172；CAD三角形相交对0→0，自交检出0。[原图/三阶段Mesh](figures/full/G04_Three_Stage_Detail.png)。
- **G05**：ACCEPTED_TARGET_REACHED，接受300/300；最大实际位移0.004716mm，主要候选拒绝[('RING_WORSENING', 2400)]。留出IoU变化+0.00028，原始分母深度覆盖变化+0.00000；CAD三角形相交对34→34，自交检出0。[原图/三阶段Mesh](figures/full/G05_Three_Stage_Detail.png)。
- **G06**：NO_ACCEPTANCE_FOR_80_ATTEMPTS，接受29/117；最大实际位移0.000192mm，主要候选拒绝[('FULL_FIT_OBJECTIVE', 1251), ('RING_WORSENING', 418)]。留出IoU变化+0.00000，原始分母深度覆盖变化+0.00000；CAD三角形相交对34→34，自交检出0。[原图/三阶段Mesh](figures/full/G06_Three_Stage_Detail.png)。
- **G08**：ACCEPTED_TARGET_REACHED，接受300/300；最大实际位移0.068040mm，主要候选拒绝[('NEW_CAD_COLLISION', 2374), ('RING_WORSENING', 595), ('RING_CONTAINMENT_WORSENING', 298)]。留出IoU变化+0.00646，原始分母深度覆盖变化+0.00195；CAD三角形相交对0→0，自交检出0。[原图/三阶段Mesh](figures/full/G08_Three_Stage_Detail.png)。
- **G09**：NO_ACCEPTANCE_FOR_80_ATTEMPTS，接受28/108；最大实际位移0.192037mm，主要候选拒绝[('AREA_DEGENERACY', 1374), ('FACE_ORIENTATION', 94), ('BASE_HALFSPACE_OR_BOUNDARY', 21)]。留出IoU变化-0.00468，原始分母深度覆盖变化+0.00000；CAD三角形相交对0→0，自交检出0。[原图/三阶段Mesh](figures/full/G09_Three_Stage_Detail.png)。

GT实体限制：['G02', 'G03', 'G07', 'G05']原始来源存在自交或非闭合，保留原始几何而非修复后制造IoU。严格IoU仅1/9，另外4例仅占据代理。

G01头部粗糙度p95约6.10→21.37度，并有一个>120度邻面角；未检出自交不等于形态合理。G03几乎无更新且缺柄；G09条件高度和整体占据明显不足。G03/G07 CAD相交对数量小幅增加，不能把离散穿入代理受控称为严格连续非穿透证明。

011已知严格轮廓重放问题继承为限制，没有改容差称PASS。Git早期HTTP2/分块推送失败后改用HTTP1.1与固定postBuffer传输，远端结果以最终ref实测核验；该问题没有改变任何科学输入或预测。

所有接受里程碑与停止原因均原样保留；没有因达到300数值接受就声称形成有效细柄。
