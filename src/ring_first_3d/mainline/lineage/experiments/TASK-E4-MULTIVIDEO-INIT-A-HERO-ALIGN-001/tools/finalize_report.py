"""Summarize frozen evidence; no optimization, GT refit or parameter changes."""
from pathlib import Path
import json,csv,hashlib,subprocess
import numpy as np
root=Path.cwd();td=root/'experiments/TASK-E4-MULTIVIDEO-INIT-A-HERO-ALIGN-001';vis=td/'visualization';s=json.loads((td/'SCIENTIFIC_RESULT.json').read_text());pairs=json.loads((vis/'FINAL_PAIRED_ANSWERS.json').read_text());body=json.loads((vis/'BODY_SHAPE_METRICS.json').read_text())['rows'];diag=json.loads((vis/'OPTIMIZATION_DIAGNOSTICS.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();source=json.loads((td/'inputs/SOURCES.json').read_text());lock=json.loads((td/'inputs/CODE_LOCK.json').read_text());versions=[]
for r in lock['files']:versions.append(dict(role='015 exact historical source',commit=r['commit'],path=r['git_path'],local_path=r['path'],sha256=r['sha256']))
for r in source['cases']:
 for label,key in [('013 actual initial Mesh','resolved013_initial'),('A0 immutable015 FINAL','A0')]:versions.append(dict(role=label,commit='905e2a9b3615a5f429553837a05e5d53826cef03 manifest verified',path=r[key]['path'],local_path=r[key]['path'],sha256=r[key]['sha256'],case=r['case']))
for file in ['src/ring_first_3d/stress/real.py','src/ring_first_3d/multisurface/registration.py','src/ring_first_3d/sim/mapping.py']:
 raw=subprocess.check_output(['git','show','b1f8fb433f37677b93ac52ac5719afd902c1fa11:'+file]);assert hashlib.sha256(raw).hexdigest()==sha(root/file);versions.append(dict(role='Inherited HERO adapter/optimizer/mapping API',commit='b1f8fb433f37677b93ac52ac5719afd902c1fa11',path=file,local_path=str(root/file),sha256=sha(root/file)))
for file in (root/'src/ring_first_3d/inita').glob('*.py'):versions.append(dict(role='New minimal task/mesh/data adapter',commit=s['implementation_commit'],path=str(file.relative_to(root)),local_path=str(file),sha256=sha(file)))
fields=list(dict.fromkeys(k for row in versions for k in row))
with(td/'VERSION_SOURCES.csv').open('w',newline='')as f:w=csv.DictWriter(f,fields,lineterminator='\n');w.writeheader();w.writerows(versions)
(td/'VERSION_SOURCES.json').write_text(json.dumps(versions,indent=2)+'\n')
strict=[r for r in pairs if r['strict_IoU_both_valid']];mean=lambda key,rows:float(np.mean([r[key]for r in rows]));summary=f'''**最终回答：004+005在合法实体IoU可评价的3组（G01/G10/G11）上更好，但没有证据证明全11组普遍更好；这种形状收益没有进一步带来稳定的真实HERO统一定位收益。**

- 严格IoU共同有效3/11组：均值 **{mean('conditional_occupancy_IoU_A1',strict):.6f}→{mean('conditional_occupancy_IoU_A2',strict):.6f}**，3/3提高。不能将其余无效实体的条件占据值冒充严格IoU。
- A1/A2共同数值10/11组：条件占据IoU仅5/10提高；曲面Chamfer仅6/10下降，均值 **{mean('Chamfer_A1_mm',pairs):.6f}→{mean('Chamfer_A2_mm',pairs):.6f}mm**。G08缺004，两条新臂均为NaN，不用005冒充。
- 真实HERO：4/11组有来源绑定完整多曲面（其中3组含004+005，G06仅004）；其余组保留旧深度库存但本轮未接入可核验的完整多曲面接口，列为迁移未完成/NOT_EVALUABLE，不能当成算法失败或成功。
- 3个双视频组中，A2相对A1的跨视频最近表面一致性仅G05略好 **0.275479→0.275344mm**；G01 **0.480163→0.480198mm**、G03 **1.930246→1.953501mm**均未改善。G05收益极小；真实数据没有独立三维GT，不能解释为绝对位置精度。

G02确认的半椭球起点没有被本轮成功纠正：条件IoU **0.537035→0.524640**，曲面MAE **0.339934→0.364178mm**；实际GT刚体对齐图仍显示错误半体形态。G03仍没有长柄。所有负结果与六个独立A2S控制保留，不用GT事后改选S臂。

'''
p=td/'TECHNICAL_REPORT.md';text=p.read_text();end=text.find('\n\n',text.find('!['));text=text[:end+2]+summary+text[end+2:];text+='''
## 失败Ip的可动自由度、实际支持与优化瓶颈

G02 A1/A2的名义线性几何自由度均1683；FIT支持顶点由358增至573，但实际最大位移仅0.482/0.570mm，形状并未可靠恢复。G03均1926自由度，支持顶点由292增至369；A1/A2分别只接受22/25步，最大位移0.471/0.439mm。A2候选原因统计：Ring穿透恶化1675、反向包含恶化1712、完整FIT目标469以下的其他拒绝另见完整日志；拒绝原因可同时出现，不能当作独立候选数相加。

这直接支持“新视角增加了支持，但现有几何约束下优化停滞”，不是顶点没有自由度。当前固定预算/约束的对照不足以唯一分离分辨率、初始形状、可见性、先验与优化器的因果贡献，不能据此断言必须换主体架构。G03共享005版本也在23接受后停滞，没有形态专项补丁。

初始与最终均以同一密集64三角面/Ring查询及自交API独立复核。训练原有密集32/FCL/反向包含检查未删；本轮未发现超过原1e-5mm容差的新增穿透恶化，已有微小穿入仍保留。完整前后有符号距离、自交、面积比、步长上限与位移见OPTIMIZATION_DIAGNOSTICS。原损失ramp随attempt变化，跨attempt总目标不能当作固定权重单调曲线；接受比较仍是同次权重。

## 来源版本与留出范围

[完整版本来源表](VERSION_SOURCES.csv)逐文件列出52个015源码、全部11个013初值/A0、继承HERO API及新接口SHA。[历史提交数据核验](evidence/HISTORICAL_905_DATA_VERIFICATION.json)确认初始和A0与905e2a9提交内清单一致。精确双精度世界模型和GT评价副本在review_meshes，包含观测F、F_solid、推断基底及T；不是仅供显示的采样点。

新增005是否提供互补方向见每例VIEW_COMPLEMENTARITY_AND_ISOLATION；角度来自既有相机/初始主体中心，不是独立世界部署认证。HERO留出图与本轮Body FIT无RGB内容哈希重合；留出是本轮更新的留出，不声称整个历史相机/初始化链从未见过。历史Init-A已有弱HERO深度项按用户要求保留；第二部分不再据HERO更新主体，所有HERO对照均使用原公制世界模型，不读取GT对齐坐标。

[精确模型目录](review_meshes/)按病例提供WORLD/ALIGNED NPZ；全部完整HERO原几何/拓扑、优化器/RNG检查点、候选拒绝与对齐PLY在本地原始runs中保留。Git只提交精选几何和离线审阅资产，不上传原视频、HERO权重或完整训练缓存。

## 实测验收

130项回归、13阶段执行/产物门禁通过；15个实际Mesh离线页面逐一通过Chrome渲染（11个真正GT对齐页面、4个完整HERO页面），JavaScript异常0，逐视频/曲面开关有效。严格IoU有效性、科学失败、执行完成分开。最初INIT_A_001门禁失败和修复经过见ENGINEERING_FIXES，未启动那次科学训练。最终整理时仅回收本会话已关闭浏览器的临时缓存，实验文件和历史证据没有清理。
'''
text=text.replace('完整FIT目标469以下的其他拒绝另见完整日志','完整FIT目标拒绝107次');p.write_text(text)
card=td/'RESULT_CARD.md';card.write_text('# '+s['task_id']+'\n\n'+summary+'\n[报告](TECHNICAL_REPORT.md) · [主体全11组](visualization/BODY_SHAPE_METRICS.csv) · [真实HERO全11组含无效](visualization/HERO_ALL11_METRICS.csv) · [版本表](VERSION_SOURCES.csv) · [失败台账](visualization/FAILURE_LEDGER.json) · [实际GT对齐矩阵](visualization/GT_RIGID_TRANSFORMS.json)\n\n实现SHA：`'+s['implementation_commit']+'`。130测试、13门禁、15个离线页面通过；37个实际评价模型，2个缺004主臂NaN。\n')
# Extend the failure evidence with the actual verified morphology outcome.
ledger=json.loads((vis/'FAILURE_LEDGER.json').read_text());ledger['verified_Ip_morphology_negatives']=[dict(case='G02',reason='Actual013 half-ellipsoid source persists afterA2; aligned conditional occupancy and surface MAE worsen',evidence='figures/Fig3_Verified_Ip_Failures.png'),dict(case='G03',reason='No recovered long stalk; A1/A2/A2S fixed-stall with Ring/containment rejections',evidence='OPTIMIZATION_DIAGNOSTICS.json')];(vis/'FAILURE_LEDGER.json').write_text(json.dumps(ledger,indent=2)+'\n')
p=td/'FAILURE_REGISTRY.json';r=json.loads(p.read_text());fp=vis/'figures/Fig3_Verified_Ip_Failures.png';r['failures'].append(dict(id='FM-INIT-A-IP-MORPHOLOGY-001',category='scientific_negative',modules=['IA01','IA03','IA04'],symptom='Verified G02 wrong half-body persists; G03 no long stalk after multivideo',cause='Observed constrained optimization stall and source-shape bias; unique causal allocation not established',cause_status='observed_only',repair='Retain full actual original/aligned Mesh, all arms and geometry rejection logs; no case-specific patch or GT checkpoint selection',regression=['130 tests: exact013 lineage, original optimizer budget, per-video permissions and evaluator-copy isolation'],evidence=[dict(path=str(fp.relative_to(root)),sha256=sha(fp)),dict(path=str((vis/'OPTIMIZATION_DIAGNOSTICS.json').relative_to(root)),sha256=sha(vis/'OPTIMIZATION_DIAGNOSTICS.json'))],rule_status='candidate',review=dict(status='unreviewed',reviewer=None,evidence=None)));p.write_text(json.dumps(r,indent=2)+'\n')
p=vis/'index.html';text=p.read_text().replace('<p>首图使用真实尺度1刚体对齐后的Mesh副本；所有公制世界预测、相机和HERO保持冻结。</p>','<p><b>结果：严格IoU有效3组均改善，但全组不稳定；真实HERO统一定位无稳定收益。G02错误半体和G03缺柄保留。</b> 首图使用真正尺度1 GT对齐副本，原公制预测与HERO不变。</p>');text=text.replace('</html>','<p><a href="../VERSION_SOURCES.csv">完整版本来源SHA</a> · <a href="../evidence/OFFLINE_BROWSER_VERIFICATION.json">15页面浏览器实测</a></p></html>');p.write_text(text)
(td/'README.md').write_text('''# Init-A多视频审阅

打开visualization/index.html。Figure1为实际GT刚体对齐后的形状，Figure2为原公制世界Mask解释，Figure3为经原Mesh/RGB核验的G02/G03失败，Figure4为完整HERO真实三角面切面，且没有融合表面遮挡。每病例GT页面可切换A0/A1/A2/A2S；HERO页面可切换M0/历史Body/重跑A1/A2/ICP及逐曲面显示。

所有精确WORLD/ALIGNED小型NPZ在review_meshes；GT变换只在ALIGNED副本，原世界模型供HERO使用。源、代码、数据版本见VERSION_SOURCES与TASK_FREEZE。130回归、13执行门禁通过；科学负结果单列。最初门禁失败与独立修复记录保留。

```bash
bash tools/research/run.sh tools/research/policy.py status --task experiments/TASK-E4-MULTIVIDEO-INIT-A-HERO-ALIGN-001/TASK.yaml --run-dir experiments/TASK-E4-MULTIVIDEO-INIT-A-HERO-ALIGN-001/runs/INIT_A_002
```

check校验固定来源/科学源码；run --stage按原冻结顺序恢复；accept只验收执行产物。init_multivideo_init_a.py为首次审计草案生成器；已完成的TASK采用记录在案的评价元数据隔离修订，不重新生成或覆盖。原完整优化器、原Mesh、PLY、原RGB/Mask/深度和所有拒绝保留在本地runs，Git保存精选几何和离线审阅资产。
''')
(td/'WORK_STATUS.md').write_text('''# Completed

INIT_A_002 completed all13 stages and Runner acceptance. 130 regression tests passed. No more scientific runs or parameter/model selection is authorized by this task. Original failed pre-science INIT_A_001 retained. All15 offline Mesh pages passed Chrome. Remaining delivery steps: final manifest verification, explicit curated commit/push and remote SHA check. Never alter src/tools-research/tests or frozen predictions to change outcomes.
''')
print('Final report and version table complete:',len(versions),'source records')
