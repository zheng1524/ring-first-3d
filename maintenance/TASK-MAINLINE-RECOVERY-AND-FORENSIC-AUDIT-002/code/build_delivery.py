"""Build audit-only reports from measured artifacts, without scientific recomputation."""
import os,csv,gzip,json,sqlite3,hashlib,collections,html,shutil
from pathlib import Path
O=Path(__file__).resolve().parents[1];R=O.parents[1];REVIEW=O/'INDEPENDENT_REVIEW_PACKAGE'
C=sqlite3.connect('file:'+str(O/'ASSET_INVENTORY.sqlite')+'?mode=ro',uri=True)
def read(n):return json.loads((O/n).read_text())
def dump(n,d):(O/n).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb')as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()
S=read('ASSET_SCAN_SUMMARY.json');D=read('DUPLICATE_ASSET_REPORT.json');L=read('REPORT_LINK_SUMMARY.json');G=read('INDEPENDENT_REVIEW_PACKAGE/GIT_OBJECT_AUDIT.json');Z=read('SMART_ENDOSCOPE_ARCHIVE_AUDIT.json');env=read('RUNTIME_ENVIRONMENTS.json')
task_id='TASK-MAINLINE-RECOVERY-AND-FORENSIC-AUDIT-002'
source=Path('/home/liu/.codex/attachments/6ccde946-0b7d-4429-84b8-125fd30afe9f/Pasted text.txt')
if not (O/'TASK.md').exists():shutil.copyfile(source,O/'TASK.md')
(O/'TASK.yaml').write_text('''task_id: TASK-MAINLINE-RECOVERY-AND-FORENSIC-AUDIT-002
kind: READ_ONLY_FORENSIC_AUDIT_AND_EVIDENCE_INDEX_REPAIR
baseline_commit: 73568493d127d0aead361314afcb32e11fe886f0
branch: maintenance/TASK-MAINLINE-RECOVERY-AND-FORENSIC-AUDIT-002
source_algorithm_changes: forbidden
historical_result_changes: forbidden
deletion_migration_training: forbidden
allowed_writes: [new_audit_worktree, new_branch_and_commit_metadata]
protected_read_only: [/home/liu/polyp_research, /home/liu/new-polyp-dxy, all_previous_worktrees]
phases: [evidence_recovery, git_forensics, asset_inventory, runtime_audit, metric_audit, convergence_plan, independent_review]
acceptance: [source_status_unchanged, original_report_hashes_preserved, full_inventory_consistent, independent_findings_retained]
scientific_acceptance: NOT_APPLICABLE_NO_NEW_PREDICTION
stop: after_delivery_and_incremental_push
attachment_note: supplied text truncates at section_11_opening; preceding scope and prohibitions complete
''')
# Join full asset accounting into every independently discovered worktree/root record.
with (REVIEW/'CLONE_WORKTREE_MATRIX.csv').open()as f:matrix=list(csv.DictReader(f))
unique_hashes={x[0]for x in C.execute("SELECT sha256 FROM assets WHERE kind='file' GROUP BY sha256,size HAVING count(*)=1")}
assets=collections.defaultdict(lambda:dict(files=0,logical_bytes=0,unique_content_paths=0,unique_content_logical_bytes=0,unknown=0))
owners=sorted({r['repository_root']for r in matrix if r.get('repository_root')},key=len,reverse=True)
with gzip.open(O/'ASSET_OWNERSHIP.csv.gz','wt',newline='')as ownership:
 ow=csv.writer(ownership);ow.writerow(['path','scan_root','worktree_or_repository','task','sha256','hash_status','ownership_method'])
 for path,root,task,h,size,value,kind in C.execute('SELECT path,root,task,sha256,size,value,kind FROM assets'):
  owner=next((x for x in owners if path.startswith(x+'/')),root)
  ow.writerow([path,root,owner,task,h,'HASH_INHERITED','Longest actual git-root prefix; scan root fallback; nested vendor roots in external Git audit'])
  if kind!='file':continue
  a=assets[owner];a['files']+=1;a['logical_bytes']+=size;a['unknown']+=value=='UNKNOWN'
  if h in unique_hashes:a['unique_content_paths']+=1;a['unique_content_logical_bytes']+=size
plans=[]
for i,row in enumerate(matrix,1):
 p=row['path'];a=assets.get(p,{})
 role='KEEP_ACTIVE_MAINLINE' if p=='/home/liu/ring_first_3d_mainline' else 'KEEP_CURRENT_AUDIT' if p==str(R) else 'KEEP_EXTERNAL_INDEPENDENT_PROJECT' if p in ['/home/liu/polyp_research','/home/liu/polyp_research/ring_anchor_3d','/home/liu/ring-first-hero-core'] else 'KEEP_OBJECT_OWNER_OR_DEPENDENCY' if p in ['/home/liu/ring_first_3d','/home/liu/ring_first_3d_harness','/home/liu/polyp_research/ring-first-3d'] else 'COLD_ARCHIVE_PROPOSAL_ONLY'
 candidate=p=='/home/liu/ring_first_3d_harness_main_ready'
 if row.get('dirty')=='True':role='KEEP_UNCOMMITTED_RESEARCH'
 if p=='/home/liu/ring_first_3d_e4_sdf_localization':role='KEEP_UNCOMMITTED_RESEARCH_AND_IGNORED_RESULTS'
 if candidate:role='RETIREMENT_CANDIDATE_NEEDS_CLOSURE'
 plans.append(dict(worktree_id=f'WT{i:03}',path=p,clone_owner=row.get('clone_owner'),branch=row.get('branch'),HEAD=row.get('HEAD'),tracked_changes=row.get('tracked_changes'),untracked=row.get('untracked'),ignored=row.get('ignored'),asset_files=a.get('files','NOT_SCANNED_SEPARATELY'),unique_content_paths=a.get('unique_content_paths','UNKNOWN'),unique_content_logical_bytes=a.get('unique_content_logical_bytes','UNKNOWN'),proposal=role,independent_decision='NEEDS_MORE_EVIDENCE' if candidate or role=='COLD_ARCHIVE_PROPOSAL_ONLY' else 'REJECT_RETIREMENT',reason='Clean Git is not asset closure. All unique/untracked/ignored/UNKNOWN assets retained; absolute-path/static and runtime dependencies unresolved.' if candidate or role=='COLD_ARCHIVE_PROPOSAL_ONLY' else 'Active use, shared object/alternate dependency, independent research or dirty source must be protected',recovery='Keep current path. Before future authorized retirement: preserve refs/reflogs/all object bytes including dangling; snapshot dirty/untracked/ignored unique scientific files with SHA; preserve runtime and raw-data bindings; validate cold restore and dependent replay in isolated new path. No retirement executed.'))
with (O/'WORKTREE_RETIREMENT_PLAN.csv').open('w',newline='')as f:
 w=csv.DictWriter(f,list(plans[0]));w.writeheader();w.writerows(plans)
with (O/'WORKTREE_ASSET_SUMMARY.csv').open('w',newline='')as f:
 w=csv.DictWriter(f,['root','files','logical_bytes','unique_content_paths','unique_content_logical_bytes','unknown']);w.writeheader();w.writerows(dict(root=k,**v)for k,v in assets.items())

# Metric provenance uses historical files/code verbatim; no distances or predictions recomputed.
line=Path('/home/liu/ring_first_3d_mainline/src/ring_first_3d/mainline/lineage/experiments')
gr='TASK-E4-G01-G03-GROWTH-RECOVERY-001';sb='TASK-E4-STRUCTURED-BODY-UPDATE-002';oldgr=Path('/home/liu/ring_first_3d_growth_recovery/experiments')/gr
defs=[
 ('G01_best_SE3_Chamfer','shape only; separate best scale-fixed SE3 per prediction','12000 prediction +12000 GT; area samples, seeds20261117/20261118; concatenated distances','mm; unsquared point→actual triangle; pooled MAE/median/P95/max','GT read after ALL prediction freezes; independent align per arm',line/gr/'code/evaluate.py',oldgr/'metrics/BODY_METRICS.csv','0.334905749 →0.303622948; Fscore and coverage worsen; no world-location conclusion'),
 ('G01_fixed_INITIAL_GT_Chamfer','same saved INITIAL→GT matrix for every candidate','same N/seeds; same fixed GT target; new topology does not share material identity','mm; same shape() statistic','GT evaluation only; no new rigid alignment for each arm',line/gr/'code/evaluate.py',oldgr/'metrics/BODY_METRICS.csv','0.335971902 →0.356987893; worsening, cannot pool with best-SE3 metric'),
 ('FIT_HOLDOUT_Mask_IoU','original frozen metric cameras, no GT alignment','known pixels only; excludes 3-dilated Ring band; CAD depth occlusion .05mm; per-view arithmetic means in final report','dimensionless intersection/union; empty union denominator max1','real Polyp/Ring masks; HOLDOUT not in optimization',line/sb/'code/projection_gate.py',oldgr/'metrics/PER_VIEW_METRICS.csv','Training weights balanced per-video/partition but report final averages may differ; retain per-view/video denominators'),
 ('Boundary_Fscore_MAE','same fixed source camera and native pixel grid','boundary sample cap100000; both directions concatenated; known pixels; empty boundary fallback max(image dimensions)','px MAE; precision/recall threshold2px; harmonic F-score','target real mask, no GT Body',line/sb/'code/projection_gate.py',oldgr/'metrics/PER_VIEW_METRICS.csv','Not identical to IoU or full-image contour mean; target boundary generation is part of protocol'),
 ('Fscore_GT_coverage','same chosen explicitly tagged GT alignment frame','12000 each; precision=prediction→GT<=.5mm; recall=GT→prediction<=.5mm','F-score harmonic mean; GT coverage=recall','GT independent after prediction freeze',line/gr/'code/evaluate.py',oldgr/'metrics/BODY_METRICS.csv','G01 Fscore .906155→.887552; GT coverage .865833→.854083'),
 ('Chamfer_vs_Hausdorff','must carry own alignment tag','finite area samples versus full continuous surfaces','historical Chamfer is non-squared pooled distance; sampled max is not exact continuous Hausdorff','GT independent after freeze',line/gr/'code/evaluate.py',oldgr/'metrics/BODY_METRICS.csv','Do not rename sampled maximum Hausdorff or average two directional p95 values'),
 ('Ring_nonworsening','fixed mm Ring CAD; no alignment','fixed CAD samples and Body probes; topology-changing union uses per-CAD local max provenance','penetration max mm, area mm², area-weighted p² energy mm⁴','No GT; hard gate with no Ring repulsion gradient',line/gr/'code/ring_gate.py',oldgr/'metrics/RING_COLLISION_METRICS.csv','Structured compares current and INITIAL; Recovery current-only. Repeat-query/float32 epsilon calibration; different protocols must stay tagged'),
 ('Stalk_exposed_length','original frozen Body signed-distance scene','1025 centerline samples bracket unique exit; brentq; speed quadrature','mm arc length; total=embedded+exposed','No GT in predictor; controls frozen before evaluation',line/gr/'code/lengths.py',oldgr/'metrics/GROWTH_METRICS.csv','Only accepted G01 formal 1.726844mm; failed G03 5.428867 diagnostic only, formal NaN'),
 ('Root_section_exposure','original Body; fixed root station','actual root ellipse station vs original signed geometry; centerline inside does not imply full section inside','mm maximum exposed root cross-section; surface/root checks distinct','No GT correction',oldgr/'review_code/publish.py',oldgr/'metrics/ROOT_GEOMETRY_AUDIT.csv','G01 .047185mm / G03 1.450052mm root defects retained; publish.py writes evidence/POST_RUN_GEOMETRY_AUDIT.json, review_code/verify_delivery.py exports CSV; no scripts executed by this audit'),
 ('HERO_depth','native axial z and frozen camera/source pixel identities','fixed depth tape support+misses; original per-case weights; never mix T28 old depth with T30 native HERO','mm proxy depth difference / weighted optimizer loss are different','HERO is prediction, not independent real GT',R/'src/ring_first_3d/inita/train.py',Path('/home/liu/ring_first_3d_mainline/maintenance/TASK-MAINLINE-ASSET-CONSOLIDATION-001/REPRODUCIBILITY_TESTS/DEPTH_SUPERVISED_PYTORCH.json'),'No real absolute 3D-accuracy claim; old replay records arithmetic equality, not new scientific accuracy'),
 ('Multivideo_HERO_consistency','original metric world cameras; NEVER GT-aligned evaluation copies','fixed source-mask support and per-view/video counts; nearest-surface overlap not certified material matching','mm nearest-surface MAE/P95 and HOLDOUT IoU','Real HERO lacks complete independent GT',line/'TASK-E4-MULTIVIEW-STRUCTURAL-UPDATE-001/code/hero_relocation.py',Path('/home/liu/ring_first_3d_structural_update/experiments/TASK-E4-MULTIVIEW-STRUCTURAL-UPDATE-001/REAL_HERO_METRICS.csv'),'More concentrated can be less correct; Body adherence alone is not spatial accuracy'),
 ('Strict_3D_IoU','prediction frozen then scale-fixed SE3 evaluation copy','fixed volume bounds/grid and valid solid assumptions; nonwatertight/invalid solids unscorable','strict occupied intersection/union; conditional occupancy separately named','GT only independent shape evaluation',R/'src/ring_first_3d/inita/evaluate.py',line/'TASK-E4-MULTIVIDEO-INIT-A-HERO-ALIGN-001/TECHNICAL_REPORT.md','IoU NOT_EVALUABLE when strict solid validity fails; conditional occupancy never substitutes strict IoU'),
]
mr=[]
for name,frame,denom,units,gt,code,evidence,note in defs:
 mr.append(dict(metric_id=name,alignment_frame=frame,denominator_sampling=denom,definition_units=units,GT_role=gt,code_path=str(code),code_sha256=sha(code)if code.is_file()else'SOURCE_UNRESOLVED',evidence_path=str(evidence),evidence_sha256=sha(evidence)if evidence.is_file()else'PATH_UNRESOLVED',limitations=note))
with (O/'METRIC_DEFINITION_MATRIX.csv').open('w',newline='')as f:
 w=csv.DictWriter(f,list(mr[0]));w.writeheader();w.writerows(mr)
metricdoc='''# Metric definition audit — definitions, not historical recalculation

G01 has two legitimate but different recorded questions. Independently realigning each prediction to GT measures shape after placement freedom: **0.334906→0.303623 mm**. Keeping the same INITIAL→GT transform measures geometry in a fixed evaluation frame: **0.335972→0.356988 mm**. We do not select one as universally correct or pool them. Both were read from historical CSV and the corresponding evaluator, never recalculated here.

The independently aligned mean improves while F-score@0.5mm **0.906155→0.887552** and GT coverage **0.865833→0.854083** decline. Therefore neither all-metric improvement nor improved metric-world localization follows. G03 remains a rejected diagnostic, formal prediction/length NaN.

The evaluator uses unsquared Euclidean distances from 12,000 area samples on each surface to actual opposite triangles, seeds20261117/20261118; concatenates24,000 distances for mean/median/P95/max. Reusing counts and seeds does not establish shared material identities across changed topology. Sampling maxima are not exact continuous Hausdorff. Per-arm SE3 matrices and INITIAL→GT matrices must be separate artifacts and never return to training/cameras/HERO.

Projection metrics exclude the actual three-pixel Ring unknown band and require predicted Body axial depth in front of CAD by0.05mm. Boundary empty-set fallback and sampling cap are part of the definition. Training balanced weights and simple reported per-view means are different aggregations. The full per-view table is required; pooled means must not hide G03's two failing005 views.

Structured Ring gates enforce current and INITIAL non-worsening; Growth Recovery's explicitly revised gate compares current only. These protocols cannot silently share one metric label. Penetration energy has units mm⁴; area mm². Recovery area-tolerance formula multiplies total area by a depth epsilon: its dimensional interpretation is an unresolved engineering convention and requires an explicit future tolerance specification, not a retrospective metric rewrite. Root-centerline embedding is distinct from full proximal-section containment; both defects remain.

HERO native axial-depth loss is a proxy supervision term with its own fixed support, weights, misses and version. It is not independent GT error. T28 and T30 remain distinct. Real multi-surface consistency does not prove absolute spatial accuracy, and unaligned original-world outputs are the only legal HERO anchors. Strict solid IoU and conditional occupancy IoU retain separate validity states.

Future **proposed, not retrospectively applied** Metric Protocol: each record must bind task/run, frozen prediction SHA, input/camera/Ring/split SHA, units, source IDs, validity, alignment label (`WORLD_METRIC`, `FIXED_INITIAL_GT`, `PER_PREDICTION_SE3_SHAPE`), transform hash, sampled Mesh/F or material IDs, counts/seeds, visibility/unknown masks, aggregation weights and failure treatment. Freeze predictions before GT first access. Publish both directional surface summaries plus pooled MAE/median/P95/max, GT recall/coverage and F-score at a frozen threshold; report strict IoU only with solid-validity evidence. Use fixed full target denominators, NaN for invalid formal outcomes, paired common-success comparisons alongside all-target coverage. No GT-based method/checkpoint selection, no unrecorded best-alignment, no dropping difficult views.

See [definition matrix](METRIC_DEFINITION_MATRIX.csv) for exact code/evidence paths and SHA256. Missing historical evidence is explicitly PATH_UNRESOLVED, not fabricated.
'''
(O/'METRIC_DEFINITION_AUDIT.md').write_text(metricdoc)

convergence='''# Proposed convergence — no retirement authorized or executed

1. Canonical repository identity: **C, currently owned by `/home/liu/ring_first_3d_harness/.git`**. Canonical active scientific worktree: **`/home/liu/ring_first_3d_mainline`**. It currently is a worktree, not an independent clone. This is the operating recommendation, not a claim that object closure/portability already exists. Keep this audit branch separately for review.
2. C borrows B (`/home/liu/polyp_research/ring-first-3d/.git/objects`) through alternates. Keep B at its existing path. Future separately authorized consolidation must first preserve complete C+B object closure, refs/reflogs and unreachable objects, compare all commits against A and preserve A's unique refs/objects, then validate a self-contained recovery copy with alternates disabled. Only then consider making the final mainline directory a standalone canonical clone. No fetch/materialization/repack/history rewrite is performed now.
3. A's primary worktree hosts39 worktrees; C hosts15 including this audit and mainline. None can be inferred redundant from equal remotes. Four roots contain19 tracked local modifications; untracked/ignored results and unknown assets remain protected. Keep dirty worktrees until owner-approved evidence snapshots are recoverable.
4. `harness_main_ready` is the only clean/empty-metadata candidate noted by the independent reviewer; its global dependency and restore closure are still unproven. All other inactive worktrees are merely **cold-archive proposals**. Per-object proposals and recovery requirements are in WORKTREE_RETIREMENT_PLAN.csv. No object is approved for immediate retirement.
5. LOCAL_ONLY: original videos/RGB/Mask/depth/GT/CAD, native HERO assets, unique meshes/failed attempts, complete run trees, official weights, compiled runtime, complete inventory database and full Git stores. Keep current paths until explicit bindings and restore tests pass. Prefer external bulk storage for the4GB ZIP, videos/weights, immutable full-run archives and complete Git backups if later authorized; preserve content hashes and source roles. Do not treat the ZIP as disposable: not all member bytes exist standalone.
6. Preserve historical branches/commits and original report SHA; canonical reports are navigation sidecars. Registry entries separate source snapshot, actual execution identity and publication commit. Unknown execution commit stays SOURCE_COMMIT_UNVERIFIED, with per-stage hashes and resumed-stage identity instead of fabricated HEAD substitution.
7. Codex task lifecycle proposal: create independent task/run directory and short TASK.yaml referencing registered modules, data roles/frozen inputs/FIT-HOLDOUT/authorized stages/budgets/stop criteria; validate Research Policy, explicit input identities and source contracts before execution. Checkpoint atomically with immutable attempt IDs. Freeze predictions before GT access. Close by exporting EVIDENCE.json, metrics/failure ledger/visualization, live link/hash check, independent review and explicit versioned publication. This audit does not alter the scientific Runner.
8. Scientific functions remain only in `src/ring_first_3d`; experiments contain configs, handlers and evidence, importing module APIs. Retain version-isolated lineage references for historical reproduction; do not create another complete source copy per experiment. Package runtime/data manifests explicitly and avoid hidden fallbacks to old worktree source paths. Directory target layout is a plan, not an instruction to migrate current evidence.
9. Recovery per proposed retirement requires a manifest of all tracked+dirty+untracked+ignored unique assets, complete dependency closure including fixed paths/ABI/model weights, hash verification, isolated cold restore, retained failure reports and owner/independent review. No absence-of-reference inference, deletion quota, or automatic UNKNOWN promotion.
'''
(O/'PROJECT_CONVERGENCE_PLAN.md').write_text(convergence)

gitrows=['| Object owner | Worktrees | Git allocated bytes | Physical objects | Borrowed objects | Physically unique objects | Ref-reachable unique commits |','|---|---:|---:|---:|---:|---:|---:|']
for g in G['clones']:
 gitrows.append(f"| {g['owner']} | {len(g['worktrees'])} | {g['git_storage']['allocated_unique_inode']} | {g['physically_stored_object_count']} | {g['accessible_but_not_physically_stored_here_count']} | {g['physical_unique_object_count']} | {g['unique_ref_reachable_commit_count']} |")
M=json.loads((R/'docs/registry/MODULE_REGISTRY.json').read_text());symlink_count=C.execute("SELECT count(*) FROM assets WHERE kind='symlink'").fetchone()[0]
report=f'''# {task_id}

工程审计与证据恢复已交付；**不宣布科研主线通过，不批准删除或退役**。本轮没有算法修改、历史结果重算、训练、资产迁移、环境清理或Git对象整理。独立智能体已直接核验Git/资产/指标并保留挑战；最终复核意见见审查包。

最重要的发现：Harness/mainline的Git对象域C通过alternates借用旧科研仓库B的**15,536个对象**。三套主项目Clone不能视为三套完整独立对象库。B必须保留原路径。旧母仓库另有大对象库与未提交研究修改，不能当普通旧目录清理。

## 范围与方法

用户附件在第十一节“在独”处截断，前十节审计范围与禁止项完整；原始附件及哈希保留。本轮从73568493d127d0aead361314afcb32e11fe886f0新建独立维护分支/worktree。所有旧源目录只读；唯一预期Git元数据增量为本轮分支/worktree/提交及正常增量push。无fetch/gc/prune/repack/删除/历史重写。`polyp_research`和DXY未写入。

56个资产扫描根，含所有旧`ring_first_3d*`、未被通配符覆盖的原目录、整个polyp_research、独立HERO core和只读DXY。自引用的本轮输出工作树排除，Git元数据独立统计，目录符号链接不递归跟随；具体外部引用另审计，动态/模板路径不冒充已解析依赖。版本、归档及共享环境大小不混为可节省空间。

## 科研证据恢复

核查5个指定任务并修复实验索引；实际代码/报告/失败记录及来源分支有文件证据。原执行SHA无法充分核验时标记SOURCE_COMMIT_UNVERIFIED；发布提交或当前HEAD不充当原执行提交。Structured执行cadde3e9、Structural执行6415993f（C0为原d78cacd8恢复）、Fusion执行16489355经报告及源码字节核对。Growth是分阶段恢复，执行身份用原freeze/source hash，发布bac3fc89不冒充单一执行SHA。维护001发布73568493也不是完整重放执行SHA。

模块表**69→{len(M['modules'])}**：恢复既有SU01–06、SB01–11、GR01–13 Runner合同ID，没有为凑数新拆算法。IA01明确EXACT013身份；每项记录功能/入口/输入输出/依赖/任务/源码SHA/来源提交/实际运行证据/工程与科研状态/主线身份。E1/E2没有替换EXACT013。Smooth ARAP是Graph限制的自动微分版本，不宣称论文原始无约束求解器；原Sweep未接受、G03保护失败、根部外露等科学事实保留。

18个lineage任务加维护001建立19份EVIDENCE；39份复制的报告/结果卡原始字节全部保留。共{L['total']}条Markdown/图片/HTML/JSON/代码引用分类：{json.dumps(L['counts'],ensure_ascii=False)}。MOVED_TARGET共{L['counts'].get('MOVED_TARGET',0)}条通过原始复制来源上下文定位，导航可直接访问实际文件及SHA。未恢复的链接仍逐项BROKEN/MISSING/UNRESOLVED；同名候选只列候选，未凭名字冒充同一历史图。各任务CANONICAL_REPORT及REPORT_LINK_AUDIT.csv是新增映射，未改历史报告以掩盖断链。这里包含JSON运行目录相对上下文缺失等问题，不能将全部BROKEN数量解读为独有资产真实丢失。

## Git法证结果

主项目55个工作树：A39/B1/C15（含新增审计工作树）；另母仓库与HERO core独立Git根。ring_anchor目录本身继承母仓库，不是另一个clone。vendor嵌套Git与DXY独立登记为外部依赖。工作树/refs/live remotes/alternates/pack/object/reflog/dangling/LFS/submodule见独立原始JSON和关系图。

{chr(10).join(gitrows)}

对象唯一性按实际本地pack索引及loose枚举，与可访问的alternate对象明确区分。唯一对象的压缩表示字节不等于可释放pack字节；未发现同SHA重复pack不能推出所有Git对象无重复。五个主扫描对象域只读fsck均exit0；仅reflog可达和无refs/reflog对象均逐库列出，未删除。副项目/vendor对象独立统计不并入主项目55工作树。

4个旧根共19项tracked未提交修改：polyp母14、e3_sdf_full3、e3_sdf_multi1、structural_update1。还有大量untracked和ignored科研源码/结果，e4_sdf_localization6257项untracked/94941项ignored。母仓库远端实查失败128，同步状态UNKNOWN，不以本地tracking refs代替实时证据。其他远端可读；完整未推送/独有commit列表保持在Git审计原件。56个非审计Git工作目录两次状态完全相同。

## 文件与存储

登记**{S['files']:,}**项，逻辑字节**{S['logical_bytes']:,}**；全局唯一inode分配**{S['unique_inode_allocated_bytes']:,}**字节（约{S['unique_inode_allocated_bytes']/2**30:.2f}GiB），不包含独立统计的.git和外部conda目录。常规文件唯一inode{S['unique_regular_file_inodes']:,}；符号链接{symlink_count:,}。扫描错误0。422150次HASH_RECOMPUTED包括368887个文件inode与53263个链接文本，24451条HASH_INHERITED仅从本次稳定同inode继承，均指明来源；不把旧审计哈希当新重算。symlink哈希是链接文本，不是目标内容。

严格同字节A/B重复{D['strict_AB_groups']:,}组；逻辑重复{D['logical_repeated_bytes']:,}字节，其中跨不同inode相同内容逻辑量{D['different_inode_identical_content_logical_bytes']:,}字节。**这些都不是批准可释放量**。{D['version_or_run_groups']}组不同版本/运行关系保留；不能将近似Mesh、重压缩图像或不同运行当严格重复。单路径内容{D['single_path_hash_assets']:,}项不意味着全部是独有科研真值。资产价值标签是保护性扩展名/路径启发式，UNIQUE_RAW_DATA/UNIQUE_MODEL_WEIGHT不构成来源或全局唯一性认证；UNKNOWN一律保留。

完整CSV.gz可流式读取，SQLite是本地便捷查询副本、不要求上传；CSV内容/数量与数据库对照验证。原始观察、模型、失败Mesh、训练轨迹和所有环境保留。本轮删除数0，迁移数0，释放空间声明0。基线001的节省数字没有被本轮重新加算。

## ZIP与运行环境

smart_endoscope归档{Z['size']:,}字节，SHA256 `{Z['sha256']}`。实际中央目录15571成员，6388个.jpg、4619种JPG内容哈希；3985成员有本地独立字节匹配，2403没有。此前2865不是当前完整中央目录计数，原计数范围不明，按子目录清单保留差异，不伪造调和。逐成员流式哈希/CRC验证，无磁盘解压，归档保留；统计只覆盖已审计根，不声称整个/home存在性穷尽。

发现4个pyvenv配置，实际依赖3个共享conda base环境（polypseg、vpo、息肉检测），不能把两个使用vpo的入口算成两份完整环境。尺寸、Python/torch/CUDA/ABI/引用者见矩阵及SHARED_BASE_ENVIRONMENTS。主线按原bash launcher实测：Python3.12.13、torch2.7.1+cu128、CUDA12.8、PyTorch3D0.7.9、Open3D0.19.0、FCL0.7.0.11；nvdiffrast在此环境不可导入，未安装。Blender及驱动命令原始输出保留。共享base环境全payload未重算哈希，明确仅尺寸/ABI审计；项目根文件/关键已引用依赖另有完整哈希。

官方HERO/DINO/权重依赖继承并核对本地主线manifest，唯一权重不覆盖。主线仍依赖旧polyp下Open3D vendor、共享base Python、原始数据/权重与Blender绝对路径。所有资产内Python/shell静态sys.path/PYTHONPATH/importlib/exec/路径/权重/数据引用均有行号与源码SHA。动态表达式未运行，不声称依赖闭包完成。现有shell入口0644需用bash调用；首次直接exec失败及纠正记录保留。跨机器复现仍NOT_CERTIFIED。

## 指标口径与科研结论

G01独立SE3形状MAE改善但固定INITIAL→GT框架变差，且F-score/覆盖下降；全部并列，不判定哪一个历史指标“唯一正确”。固定分母/采样/单位/GT访问/对齐副本与HERO世界坐标边界见METRIC_DEFINITION_AUDIT及12项矩阵。未重算历史距离。G01仍带根部外露，G03仍PER_VIEW_PROTECTION拒绝、正式柄长NaN；本轮不改变科研结论。未来协议仅为建议，不追溯套用。

## 收敛与独立审查

建议C作为规范Git身份、mainline作为唯一活动科研工作树，先解决B alternates依赖与A/C独有对象保全，随后另行授权收敛。当前无可立即执行的退役；harness_main_ready仅候选，其他历史工作树仅冷归档提案，每项均列理由/阻断/恢复步骤。LOCAL_ONLY/外部存储/实验开结项协议见PROJECT_CONVERGENCE_PLAN和逐工作树计划。不会为目录整洁调整历史结构。

独立审查包包含实测命令、关系图、pack/object身份、dirty/untracked/ignored清单、抽查与争议。16对硬链接、32项资产独立哈希抽查匹配；审查发现SYMLINKS导出SQL错误后已修复53263条，首版空导出及IR-009仍保留。ARAP/成长科研有效性不由本轮重新认证；不存在自动将NEEDS_MORE_EVIDENCE改为ACCEPT。

## 固定审计表

|审计项目|必须汇报|
|---|---|
|目标组数|工程：56资产根、55主项目WT、5指定任务、8项原核心模块证据；无新增测量目标|
|本算法独立成功|N/A，本轮无新预测；审计范围与文件数见原始表|
|本算法失败|N/A；保留历史G03正式NaN及未解决断链/来源身份/同步状态|
|历史测量值回退|0；历史数字仅审计对照，不生成预测|
|失败组及具体原因|Growth G03保护拒绝、G01根部缺陷；本轮工程导出/入口调用错误与修复均保留|
|最终统计样本|全量审计分母，不只报告成功/重复项；真实测量误差统计N/A|
|是否使用GT选择算法|否；没有训练、参数选择或历史科研重算，仅核对冻结后评价代码/文件|

## 审计局限与未解决问题

未认证跨机重建；未获得母仓库实时远端状态；旧来源执行commit部分不明确；动态路径/部分报告相对上下文未解析；归档独有成员和全部UNKNOWN需保留；科学局限及Ring面积容差量纲解释待审；没有执行任何收敛迁移。输出的新维护分支SHA在Git提交后另行记录，不在自身文件内伪造自引用SHA。
'''
(O/'TECHNICAL_REPORT.md').write_text(report)
(O/'RESULT_CARD.md').write_text(f'''# Audit result card

审计与证据恢复交付，**无删除/迁移/训练/科学算法修改**。

- Git：55主项目工作树、3对象域；C借用B15536对象。另2独立科研对象域与vendor/DXY依赖。
- 文件：446601项，唯一inode分配49.88GiB；严格重复48341组不是可删除量。
- 注册：5任务索引核验，模块69→{len(M['modules'])}；19份EVIDENCE；历史报告原字节保留。
- ZIP：6388 JPG成员，2403未找到独立字节匹配，KEEP。
- 保护：19项tracked修改及所有untracked/ignored/UNKNOWN保留。
- 科研：G01两种对齐指标结论不同，F-score/coverage下降；G03正式失败NaN不变。
- 独立复核及未解决事项见INDEPENDENT_REVIEW_PACKAGE。没有批准退役，跨机复现未认证。

[技术报告](TECHNICAL_REPORT.md) · [收敛提案](PROJECT_CONVERGENCE_PLAN.md) · [指标口径](METRIC_DEFINITION_AUDIT.md) · [审计导航](visualization/index.html)
''')

reviewtask='''# Independent review task

Do not accept the primary agent's reports as facts. Read the full attached task, prohibition list and actual source roots. Write only new review files in INDEPENDENT_REVIEW_PACKAGE. No deletion, migration, fetch, gc, prune, repack, reset, force push, environment modification, scientific recomputation or training.

Independently verify Git marker/common-dir/objects/alternates, all worktree HEAD/dirty/untracked/ignored and branch publication. Physical object enumerations must exclude alternates when measuring storage. Check unique commits including only-reflog/dangling, LFS and submodules; remote failures remain UNKNOWN.

Challenge SHA and inode accounting using original files, not copied summaries. Examine the full inventory and unique/duplicate lists; strict duplicates require full SHA+size, not basename/geometric proximity. Challenge every retirement row with ACCEPT/REJECT/NEEDS_MORE_EVIDENCE and recovery prerequisites. No proposal is execution permission.

Verify the5 task records, existing SU/SB/GR module IDs against real freeze contracts, source/execution/publication distinction, original report SHA preservation, MOVED versus missing/template links and absence of silent repairs. Recheck corrected symlink export against SQLite and CSV; original export error must remain documented. Check extension-based value labels are only protective heuristics.

Read metric CSV and calculation code independently: best per-prediction SE3 versus fixed INITIAL→GT, fixed sampling, Fscore/coverage, world HERO restrictions, failed G03 NaN. Do not choose/merge a metric frame or re-evaluate history.

Audit runtime base environments, layered vendors/ABI/absolute paths and archive central directory/member hash comparison without extracting. Explicitly preserve scope gaps and disagreements. Output final findings and per-retirement classifications; primary agent cannot self-certify audit acceptance.
'''
(O/'INDEPENDENT_REVIEW_TASK.md').write_text(reviewtask)
dump('INDEPENDENT_REVIEW_PACKAGE/REVIEW_PACKAGE_INDEX.json',dict(scope='Independent filesystem/Git challenge; pointers require local source access',task=str(O/'TASK.md'),method=str(O/'TECHNICAL_REPORT.md'),clone_worktree=str(REVIEW/'CLONE_WORKTREE_MATRIX.csv'),git_objects=str(REVIEW/'GIT_OBJECT_AUDIT.json'),duplicates=str(O/'DUPLICATE_ASSET_REPORT.json'),unique_assets=str(O/'UNIQUE_ASSETS.csv.gz'),index_issues=str(O/'EXPERIMENT_INDEX_REPAIR.json'),module_issues=str(O/'MODULE_REGISTRY_REPAIR.json'),report_links=str(O/'REPORT_LINK_AUDIT.csv'),metric_conflicts=str(O/'METRIC_DEFINITION_AUDIT.md'),runtime=str(O/'RUNTIME_ENVIRONMENT_MATRIX.csv'),retirement=str(O/'WORKTREE_RETIREMENT_PLAN.csv'),unresolved=str(O/'TECHNICAL_REPORT.md')+'#审计局限与未解决问题',primary_does_not_self_approve=True))
vis=O/'visualization';vis.mkdir(exist_ok=True)
items=['TECHNICAL_REPORT.md','RESULT_CARD.md','PROJECT_CONVERGENCE_PLAN.md','WORKTREE_RETIREMENT_PLAN.csv','METRIC_DEFINITION_AUDIT.md','METRIC_DEFINITION_MATRIX.csv','EXPERIMENT_INDEX_REPAIR.json','MODULE_REGISTRY_REPAIR.json','REPORT_LINK_AUDIT.csv','ASSET_SCAN_SUMMARY.json','DUPLICATE_ASSET_REPORT.json','SMART_ENDOSCOPE_ARCHIVE_AUDIT.json','RUNTIME_ENVIRONMENT_MATRIX.csv','INDEPENDENT_REVIEW_PACKAGE/INDEPENDENT_FINDINGS.md','INDEPENDENT_REVIEW_TASK.md']
links=''.join('<li><a href="../'+html.escape(x,quote=True)+'">'+html.escape(x)+'</a></li>'for x in items)
evidence=list((O/'evidence').glob('*/EVIDENCE.json'))
evlinks=''.join('<li>'+html.escape(p.parent.name)+': <a href="../'+str(p.relative_to(O))+'">EVIDENCE</a>'+(' · <a href="../'+str((p.parent/'CANONICAL_REPORT.md').relative_to(O))+'">原报告与证据导航</a>'if(p.parent/'CANONICAL_REPORT.md').exists()else'')+'</li>'for p in evidence)
(vis/'index.html').write_text('<!doctype html><html lang="zh"><meta charset="utf-8"><title>主线恢复与法证审计002</title><style>body{font:16px system-ui;max-width:1100px;margin:40px auto;line-height:1.6}a{color:#146}li{margin:7px 0}.warning{background:#fff1d4;padding:18px}</style><h1>主线恢复与法证审计002</h1><p class="warning">本轮不执行删除或退役，不重新认证科研成功。Harness/mainline依赖旧B对象库，不能直接移走旧仓库。所有原报告和失败保留。</p><p>446601文件/链接 · 55主项目工作树 · 69→'+str(len(M['modules']))+'模块 · 19份EVIDENCE。指标口径与独立争议均可直接检查。</p><h2>审计文件</h2><ul>'+links+'</ul><h2>各实验原始证据与恢复映射</h2><ul>'+evlinks+'</ul><p>这是审计导航，不生成新的科学图像。相对链接在本地可用；历史大资产继续留在原来源路径。</p></html>')
dump('FAILURE_REGISTRY.json',dict(records=[dict(id='FA002-SYMLINK-EXPORT',type='ENGINEERING_ERROR',cause='SQLite identifier/literal ambiguity',evidence='AUDIT_REVISIONS.json',fix='Bound parameter export, original error preserved',regression='audit_validation.py:symlink row equivalence',permanent_rule=False),dict(id='FA002-RUNTIME-EXEC',type='ENGINEERING_INVOCATION_ERROR',cause='Historical launcher0644',fix='bash unchanged launcher',evidence='LAYERED_RUNTIME_PROBE.json',permanent_rule=False),dict(id='FA002-ALTERNATE',type='RETIREMENT_BLOCKER',cause='C object store borrows B',fix='No retirement; future separately authorized object closure validation',evidence='INDEPENDENT_REVIEW_PACKAGE/GIT_OBJECT_AUDIT.json',permanent_rule=False),dict(id='FA002-G01-METRICS',type='SCIENTIFIC_NEGATIVE_RETAINED',cause='Different alignment frames and mixed metric changes',evidence='METRIC_DEFINITION_AUDIT.md',fix='Keep separate definitions, no recomputation',permanent_rule=False),dict(id='FA002-TRUNCATED-INPUT',type='TASK_ATTACHMENT_TRUNCATED',cause='File ends at section11 opening',evidence='TASK.md',fix='Execute complete preceding scope and preserve missing tail disclosure',permanent_rule=False)]))
# Current task EVIDENCE, with an explicit non-self-referential source identity.
dump('EVIDENCE.json',dict(task_id=task_id,source_commit='73568493d127d0aead361314afcb32e11fe886f0',execution_commit='UNCOMMITTED_AUDIT_SOURCE_FREEZE_SEE_DELIVERY_MANIFEST',source_files=[dict(path=str(p),sha256=sha(p),hash_status='HASH_RECOMPUTED')for p in sorted((O/'code').glob('*.py'))],input_assets=[dict(path=str(source),sha256=sha(source),hash_status='HASH_RECOMPUTED')],output_assets=[dict(path=str(O/n),sha256=sha(O/n),hash_status='HASH_RECOMPUTED')for n in ['TECHNICAL_REPORT.md','RESULT_CARD.md','REPORT_LINK_AUDIT.csv']],metrics=[dict(path=str(O/'ASSET_SCAN_SUMMARY.json'),sha256=sha(O/'ASSET_SCAN_SUMMARY.json'))],visualizations=[dict(path=str(vis/'index.html'),sha256=sha(vis/'index.html'))],failure_evidence=[dict(path=str(O/'FAILURE_REGISTRY.json'),sha256=sha(O/'FAILURE_REGISTRY.json'))],dependencies=[dict(path=str(O/'RUNTIME_ENVIRONMENT_MATRIX.csv'),sha256=sha(O/'RUNTIME_ENVIRONMENT_MATRIX.csv'))],scientific_status='NOT_APPLICABLE_NO_NEW_SCIENCE',engineering_status='AUDIT_DELIVERY_PENDING_FINAL_INDEPENDENT_REVIEW'))
print('DELIVERY_BUILT',len(M['modules']),len(evidence),flush=True)
