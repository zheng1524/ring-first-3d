import json,csv,os,collections,gzip
from pathlib import Path
T=Path(__file__).resolve().parent.parent;W=Path('/home/liu/ring_first_3d_workspace')
def read(p):return json.loads(Path(p).read_text())
def csvout(p,rows):
 with Path(p).open('w',newline='')as f:
  w=csv.DictWriter(f,list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
plan=read(T/'evidence/CLEANUP_PLAN.json');done=read(T/'evidence/CLEANUP_EXECUTED.json');dedup=read(T/'evidence/OPEN3D_DEDUP_RECEIPT.json');kept=read(T/'evidence/RETAINED_PATHS.json');roots=read(T/'evidence/RETIRED_ROOTS.json');arc=read(T/'evidence/ARCHIVE_RECEIPT.json');start=read(T/'evidence/SPACE_START.json');fs=os.statvfs(W);final=fs.f_bavail*fs.f_frsize
per=[]
for root,route in roots.items():
 dd=[x for x in done['deleted']if x['root']==root];rr=[x for x in kept if x['root']==root];real=[x for x in rr if Path(x['path']).is_file()and Path(x['path']).resolve()==Path(x['path'])];aliases=[x for x in rr if Path(x['path']).resolve()!=Path(x['path'])];seen=set();alloc=0
 for x in real:
  st=Path(x['path']).stat();key=(st.st_dev,st.st_ino)
  if key not in seen:alloc+=st.st_blocks*512;seen.add(key)
 per.append(dict(route=route,root=root,deleted_paths=len(dd),deleted_last_link_bytes=sum(x['blocks']for x in dd if x['last_inode_link_removed']),remaining_direct_files=len(real),remaining_unique_inode_bytes_within_root=alloc,alias_rows_not_additional_storage=len(aliases),remaining_consumers='; '.join(sorted(set(x['reason']for x in rr))),archive=arc['full_archive']))
csvout(T/'evidence/RETIRED_ROOT_DISPOSITION.csv',per)
summary=[]
for route in sorted(set(roots.values())):
 rr=[x for x in per if x['route']==route];summary.append(dict(route=route,roots=len(rr),deleted_paths=sum(x['deleted_paths']for x in rr),last_link_bytes=sum(x['deleted_last_link_bytes']for x in rr),remaining_root_bytes=sum(x['remaining_unique_inode_bytes_within_root']for x in rr)))
# No duplicate runtime/Git/RAW count is added to release; df is authoritative.
space=dict(start_available=start['available'],before_deletion=done['before_available_bytes'],after_deletion=done['after_available_bytes'],deletion_net=done['net_df_release_bytes'],runtime_dedup_net=dedup['net_df_release_bytes'],full_archive_bytes=arc['full_bytes'],source_archive_bytes=arc['source_bytes'],final_available=final,whole_phase_net_after_archive_and_evidence=final-start['available'],df_scope='same mount /, st_dev='+str(os.stat(W).st_dev));(T/'evidence/CLEANUP_SPACE_FINAL.json').write_text(json.dumps(space,indent=2))
text='''# M2F13 退役路线最终清理

本轮授权覆盖旧P和相关废弃3D工作区；不再沿用旧P只读跳过规则。按上轮审计路径刷新141个退役根，保存源码/配置/输入身份/正负结论与代表结果，逐成员核验归档后清理。没有删除Git历史、RAW照片/视频/ZIP、GT/CAD、公共模型或现用Graph/ARAP/Sweep。

## 逐技术闭环

| 技术 | 已处理根 | 删除路径数 | 实际末链接分配字节 | 剩余根库存字节* |
|---|---:|---:|---:|---:|
'''
for r in summary:text+=f"| {r['route']} | {r['roots']} | {r['deleted_paths']} | {r['last_link_bytes']} | {r['remaining_root_bytes']} |\n"
text+='''
*剩余根库存是逐根去重inode后的目录库存，跨根仍可能共享inode，不相加当物理总量；符号链接别名不重复计体积。精确根路径/删除数量/剩余体积/保留理由见[RETIRED_ROOT_DISPOSITION.csv](evidence/RETIRED_ROOT_DISPOSITION.csv)，逐文件清单在压缩JSON中。未把旧模型已offload的历史空间算成本轮收益。

- TSDF/NeuralFusion：处理旧P及e4_e1e2、pose_depth、e4_a1等废弃树的Mesh/预览/逐轮产物；保留源码、配置、完整失败指标和真实代表。共享硬链接逐路径删除，仅最后链接计块释放。
- MonoSDF/E0/E2与MapAnything：处理已在本地的退役派生输出；所有`FINAL_LAST_SAFE_step000`、`STOP_UNSAFE_step001`、初态检查点保留，因为文件SHA并不等同。保留未完成/停在不安全更新的真实状态，不声称训练充分。MapAnything checkpoint在前次审计已缺失，本轮删除权重0字节；其源码/依赖revision和负结果归档，无专属活动环境可卸载。
- PMGR谱/FFD：清理重复派生显示/产物；主要剩余是小型完整metrics和源码。Graph/ARAP核心独立保留，未按名称误删。
- Hull H1/H2：删参数子集与叠层展示冗余；明确保留两视频完整`H2_nALL.ply`、faces unknown/ROI分类、nALL voxel、Fig2完整视图及Fig9失败见证，不以CONTROL小图替代正式结果。
- 旧补片/GICP/固定主面融合：清理surface_fusion_v1/v2/v3、independent_confidence_fusion及旧phase任务的专属输出。现用导入只需要V2 `inputs/real_camera_0.npz`和replay的`inputs/R10_ring.obj`等明确闭包，未因旧`pack/mesh_for`函数定义而保护全部旧预测。
- 旧Body-E/自由顶点结构更新/失败soft-zbuf：退出SU003训练缓存921个NPZ；保留六个FINAL、INITIAL/GRAPH/GT与源码/失败日志。精确保留SU004三个`{G01,G03,G05}/DEFORM_GROW/FINAL.npz`供SB002历史对照。当前主体核心在独立STRUCTURED-BODY-UPDATE-002的INITIAL、STEP_024 GRAPH/BODY/UPDATES，Sweep在mainline/results，不依赖SU003全缓存。
- UNIFIED-002及M2E/M2F1/2/3/5/8/9：删除剩余冗余派生数据/图集，归档包装代码和身份；保留输入祖先、真正被V6消费的准备代码与R5/R10 CAD。M2F10/11/12全部结果与M2F6保持。

## 唯一共享依赖与例外

`surface_fusion_v1/weights/mvsanywhere_hero_full.ckpt`约2.3GiB是当前官方HERO模型，`ring-first-hero-core/site_config.local.json`明确消费；不是退出TSDF后可删权重。V3 vendor Open3D被本次渲染、M2F12评价和公共入口使用。23个完整SHA相同的Open3D文件已与`.venv/lib/python3.12/site-packages/open3d`权威文件共享inode，原路径不改、无需算法迁移；原本共享的CUDA pybind没有再次计收益。共享Python环境不卸载。

原始输入/真实照片、GT/CAD、旧相机/地标祖先，以及其他runtime/权重的具体剩余路径和理由均列在RETAINED_PATHS；无法确认独占性的少量类型单列`individual unknown file kind`，没有因此阻断整条技术清理。废弃工作区根中残留的Git对象保留；不把几乎空的工作区根声称为整树删除。

## 空间实测

'''
for k,v in space.items():text+=f'- {k}: `{v}`\n'
text+=f'''\n清理unlink的df净增加 **{space['deletion_net']/2**30:.4f} GiB**，公共运行库去重另增加 **{space['runtime_dedup_net']/2**30:.4f} GiB**；含归档、清单及同期写入后的整个阶段净增加 **{space['whole_phase_net_after_archive_and_evidence']/2**30:.4f} GiB**。最终普通用户可用 **{final/2**30:.4f} GiB**。同盘移动不计释放。

完整精简证据归档位于`{arc['full_archive']}`，{arc['full_bytes']} B、{arc['full_verified_members']}成员，SHA `{arc['full_sha256']}`；本地保留，不上传整套旧运行。上传源码/报告子包`archive/RETIRED_SOURCE_AND_REPORTS.tar.gz`，{arc['source_bytes']} B，SHA `{arc['source_sha256']}`。归档成员、源路径与SHA随压缩清单上传。

## 保留入口与内容验证

6项清理边界测试通过。清理后30,975个既有工作文件内容SHA、176个科学源码和M2F12冻结2991文件全部一致；7仓库原有修改binary patch已存。Open3D0.19真实射线测试得到t_hit≈1；R5/R10 CAD、V2旧相机与Ring标定均校验。旧递归资产目录清单不再代表现用消费闭包，SU003退出项在RETIRED_CLOSURE_EXCEPTIONS逐文件说明，历史清单不回写。未以轻量检查冒称重跑科研主线。

HERO后续只新增69组合的候选预算，按旧单次输出最大体积和顺序执行预留2GiB输出/图表余量；原V6/H004大Mesh直接引用，不整套复制。实际预算须由完整输入身份冻结后生效。
'''
(T/'CLEANUP_FINAL.md').write_text(text)
# Keep large audit lists compressed in Git; local original JSONs remain executable/reviewable.
large=[p for p in (T/'evidence').iterdir()if p.is_file()and p.stat().st_size>2**20 and p.suffix in ['.json','.jsonl']]
for p in large:
 with p.open('rb')as src,gzip.open(str(p)+'.gz','wb')as dst:
  for block in iter(lambda:src.read(1024*1024),b''):dst.write(block)
(T/'.gitignore').write_text('code/__pycache__/\n'+''.join('evidence/'+p.name+'\n'for p in large))
(T/'evidence/README.md').write_text('Large audit JSON/JSONL lists are gzip-compressed in Git. Exact uncompressed originals remain at the same local paths. For a fresh checkout, decompress the needed file with `gzip -dk evidence/FILE.json.gz` before replaying inspection tools. They are historical execution receipts, not a command to repeat deletion.\n')
print(space)
