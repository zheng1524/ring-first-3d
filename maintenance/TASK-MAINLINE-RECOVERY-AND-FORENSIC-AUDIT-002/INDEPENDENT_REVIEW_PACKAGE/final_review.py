import pathlib,csv,json,collections,datetime,hashlib,gzip
O=pathlib.Path(__file__).resolve().parent;P=O.parent
rows=list(csv.DictReader(open(P/'WORKTREE_RETIREMENT_PLAN.csv')));dec=[]
for r in rows:
 p=r['path'];proposal=r['proposal'];nonwt=(p=='/home/liu/polyp_research/ring_anchor_3d')
 if proposal.startswith('KEEP_'):
  decision='ACCEPT';why='Accept retaining current path and evidence. This accepts the KEEP recommendation, not retirement.'
 else:
  decision='NEEDS_MORE_EVIDENCE';why='Unique scientific assets, ignored/untracked outputs, fixed-path and runtime dependencies, Git object closure and cold restore have not all been discharged. Keep current path.'
 if nonwt:why+=' This is a nested directory inherited from mother repository, not an independent worktree.'
 if p.endswith('/ring-first-3d'):why+=' Harness object store borrows this object directory through alternates; do not relocate.'
 if p.endswith('e4_sdf_localization'):why+=' Independent status captured6257 untracked items including actual source and94941 ignored items; preserve all.'
 if p.endswith('harness_main_ready'):why+=' Tracked clean/untracked0/ignored0 is confirmed, but two globally single-path contents and dependency closure remain; no deletion is approved.'
 if p.endswith('forensic_audit_002'):why+=' Audit outputs are intentionally mutable until publication; exclude from source-status invariance checks.'
 dec.append(dict(worktree_id=r['worktree_id'],path=p,object_type='NESTED_DIRECTORY_NOT_AN_INDEPENDENT_WORKTREE'if nonwt else'GIT_ROOT_OR_REGISTERED_WORKTREE',parent_proposal=proposal,independent_decision_on_proposal=decision,immediate_retirement='REJECT',reason=why,evidence='CLONE_WORKTREE_MATRIX.csv; GIT_OBJECT_AUDIT.json; WORKTREE_FILES_*.json.gz; SOURCE_STATUS_RECHECK.json; parent inventory is sample-challenged, not assumed perfect',restore_requirement=r['recovery']))
with open(O/'FINAL_RETIREMENT_DECISIONS.csv','w')as f:w=csv.DictWriter(f,fieldnames=list(dec[0]));w.writeheader();w.writerows(dec)
checks=json.load(open(O/'FINAL_PACKAGE_CHECKS.json'));links=list(csv.DictReader(open(P/'REPORT_LINK_AUDIT.csv')));fusion=json.load(open(P/'evidence/TASK-E4-G01-MULTISURFACE-BODY-FUSION-001/EVIDENCE.json'));matrix=list(csv.DictReader(open(P/'METRIC_DEFINITION_MATRIX.csv')));root=next(r for r in matrix if r['metric_id']=='Root_section_exposure')
example=next((r for r in links if r['source'].endswith('TASK-E4-2D-CONTOUR-GUIDED-INIT-A-HERO-001/FAILURE_REGISTRY.json') and r['reference']=='experiments/TASK-E4-2D-CONTOUR-GUIDED-INIT-A-HERO-001/visualization/FAILURE_LEDGER.json'),{})
resolved={
 'IR-009':dict(initial='Rejected empty symlink export (SQLite quoted identifier collision).',current='Corrected export independently counted53263 rows. Initial finding and empty export retained.',status='CORRECTED_VERIFIED'),
 'IR-010':dict(initial='Extension-based labels do not prove raw-origin/global uniqueness.',current='Technical report explicitly limits labels to conservative protection heuristic; provenance certification remains unproven.',status='REMAINS_A_DOCUMENTED_LIMITATION'),
 'IR-011':dict(initial='Root metric evidence path ROOT_EMBEDDING_AUDIT.json nonexistent; geometry_gate.py is not the posterior root-section metric producer.',current=f"Now evidence={root['evidence_path']}; code={root['code_path']}. Independently inspected original review_code/publish.py and verify_delivery.py producer chain without executing.",status='CORRECTED_VERIFIED'if pathlib.Path(root['evidence_path']).is_file()and root['code_path'].endswith('/review_code/publish.py')else'UNRESOLVED'),
 'IR-012':dict(initial='Repo-root-relative JSON evidence path was incorrectly resolved against report directory and marked BROKEN_TARGET.',current=example,status='CORRECTED_VERIFIED'if example.get('status')in ['MOVED_TARGET','VALID','EXTERNAL_DEPENDENCY']and pathlib.Path(example.get('resolved_path','/nonexistent')).is_file()else'UNRESOLVED'),
 'IR-013':dict(initial='Fusion EVIDENCE had metrics=[] despite existing original JSON/CSV metrics.',current={'metric_records':len(fusion['metrics']),'paths':[r['path']for r in fusion['metrics']]},status='CORRECTED_VERIFIED'if fusion['metrics']else'UNRESOLVED'),
 'IR-014':dict(initial='e4_sdf_localization cold archive proposal described tracked-clean state despite untracked scientific source.',current=next(r['proposal']for r in rows if r['path'].endswith('e4_sdf_localization')),status='CORRECTED_VERIFIED'if next(r['proposal']for r in rows if r['path'].endswith('e4_sdf_localization')).startswith('KEEP_UNCOMMITTED')else'REMAINS_CONDITIONAL')}
result=dict(review_time_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),independence='Second agent directly reads original Git/files/source rather than assuming first agent claims. No source alterations, deletion, migration or scientific recomputation.',decisions=collections.Counter(r['independent_decision_on_proposal']for r in dec),immediate_retirement_approved=0,rows=len(dec),corrections=resolved,remaining=['Mother polyp live remote unavailable','Unverified per-stage execution commit where evidence insufficient','Thousands of broken/unresolved report references remain; not all indicate lost assets','Runtime portability and dynamic dependency closure not certified','Heuristic value labels do not certify raw origin or uniqueness','No unique-asset absence or cold-restore certification for retirement','Scientific G01 root defect/fixed-frame worsening and G03 rejection remain'],status='INDEPENDENT_CHALLENGE_COMPLETE_WITH_LIMITS; NO_GENERAL_AUDIT_PASS_OR_RETIREMENT_AUTHORIZATION')
json.dump(result,open(O/'FINAL_REVIEW_RESULT.json','w'),ensure_ascii=False,indent=2)
text='''# Final independent review — TASK-MAINLINE-RECOVERY-AND-FORENSIC-AUDIT-002

本文件由第二智能体独立形成。没有把主审计结论当作原始事实；Git元数据、源代码、存量指标、文件哈希和ZIP中央目录均直接检查。**不宣布项目全面审计通过，不批准任何删除、移动或工作树退役。**

## 实测范围

独立确认三套主项目对象库A/B/C和55个工作树，另母科研仓库与HERO core对象域。C通过alternates借用B的15,536个对象。直接枚举本地pack/loose并区分可访问对象，完整只读fsck、live ls-remote、refs及工作树状态已记录。56个非本轮审计Git工作目录两次状态完全一致。19项已跟踪修改及未跟踪/忽略科研文件保持保护。母仓库远端访问失败仍为UNKNOWN。

16对硬链接独立SHA一致；另32项全量库存记录（16本次inode继承/16重算）独立SHA和stat抽查一致。对本轮补登记的SU/SB/GR共30模块逐项核验实际代码SHA、原代码SHA、历史Git快照字节和执行证据路径，全部匹配；这不将发布SHA自动提升为执行SHA。Growth/维护001执行身份仍保留SOURCE_COMMIT_UNVERIFIED及阶段性身份限制。39份历史报告/结果卡原副本SHA逐项匹配；36条VALID/MOVED/EXTERNAL链接样本实际SHA匹配。指标矩阵12项代码/证据路径和SHA逐项核验。详情见FINAL_PACKAGE_CHECKS.json。

ZIP完整文件独立流式重算SHA匹配，中央目录15,571成员、6,388 JPG与本轮主审计一致；12个跨目录JPG成员在内存流式读取，SHA/size/CRC均匹配成员清单。没有磁盘解压，没有改写归档。此前2,865范围仍不明，不能假定与现计数等价。独立样本不证明所有独有成员已在其他位置保存，必须继续保留归档。

## 纠正过程与保留异议

'''
for key,v in resolved.items():text+=f"- **{key} — {v['status']}**：首版问题：{v['initial']} 当前证据：{v['current']}\n\n"
text+='''上述首版错误仍作为审计发现保留，后续修正不会抹去原记录。版本化修订是纠错，不是对原始科研结果的修改。

## 指标判断

独立源代码核验确认：G01独立最佳尺度固定SE3对齐MAE改善，固定INITIAL→GT框架MAE恶化，F-score/覆盖率也下降。它们的对齐规范和科学含义不同，报告现在并列展示，接受这种区分；不选择其中一个替代其他指标。当前Root_section指标明确追溯后验review_code/publish.py→POST_RUN_GEOMETRY_AUDIT→verify_delivery.py→CSV链。没有执行评价代码或重算历史科研距离。

## 逐对象退役意见

全部58条计划行均在FINAL_RETIREMENT_DECISIONS.csv给出独立意见。ACCEPT仅接受KEEP建议；所有冷归档及候选退役均NEEDS_MORE_EVIDENCE，**立即退役一律REJECT**。ring_anchor一行是嵌套目录，不是额外worktree。harness_main_ready虽然tracked clean、untracked0、ignored0，仍有路径唯一内容与依赖待闭合，不能立即删。e4_sdf_localization因真实未跟踪源码/大量忽略结果，保留建议是合理纠正。

原则上接受“C为未来规范Git身份、mainline为活动科研工作树”的条件性组织建议；它不代表C已成为独立完整clone。必须先解决B对象借用、A/C独有对象保全、LOCAL_ONLY与ABI绑定和可恢复性，再另行审查实施。当前任务不得实际收敛迁移。

## 未解决事项

母仓库实时同步状态、部分执行commit身份、动态绝对路径闭包、剩余断链的历史相对上下文、全部UNKNOWN资产语义及跨机环境恢复仍需后续证据。原始来源目录、权重、深度和科研失败保持不变。G01根部局部外露、固定框架恶化、G03正式NaN不因工程审计而获得科研认证。

本轮第二智能体已完成独立挑战并核验所列修正；这不等于对全量科研资产无遗漏的保证，也不授权任何退休操作。保留NEEDS_MORE_EVIDENCE与主审计的所有未决事项，不自动转为ACCEPT。
'''
(O/'FINAL_INDEPENDENT_REVIEW.md').write_text(text)
print('rows',len(dec),'decisions',dict(result['decisions']),'corrections',{k:v['status']for k,v in resolved.items()})
