"""Verify actual removals and produce the final protected-cleanup receipt."""
from audit import *
from protected_delete import verify_static
import gzip

run=read(O/'EXECUTION.json');before=read(O/'HEALTH_BEFORE.json');after=read(O/'HEALTH_AFTER.json');plan=read(O/'DELETE_PLAN.json');inv=read(O/'INVENTORY_BEFORE.json');kept=read(O/'RETAINED_LEAVES.json')
assert sha(O/'DELETE_PLAN.json')==run['plan_sha256']=='1102e51c2612c9b873d64b5606dba760cb5a8b09365234120df688ab6a18772c'
assert len(run['deleted'])==len(plan['files'])==4942 and not run['exceptions']
assert not any(Path(r['path']).exists() or Path(r['path']).is_symlink() for r in run['deleted'])
assert sha(T/'code/protected_delete.py')==run['execution_source_sha256']
checked=verify_static();assert checked==36430
assert len(after['raw_future_readability'])==79 and all(r['readable'] for r in after['raw_future_readability'])
identities=[]
for pid in [185164,212960]:
 a=next(p for p in before['processes'] if p['pid']==pid);b=next((p for p in after['processes'] if p['pid']==pid),None)
 assert b is not None and all(a[k]==b[k] for k in ['start_ticks','command','cwd','exe'])
 identities.append(dict(pid=pid,started_beijing=a['started_beijing'],start_ticks=a['start_ticks'],command=a['command'],cwd=a['cwd'],unchanged=True))
assert after['full']['runner_log']['size']>before['full']['runner_log']['size']
assert after['full']['sources']>before['full']['sources']
save(T/'BACKGROUND_HEALTH.json',dict(before_beijing=before['checked_beijing'],after_beijing=after['checked_beijing'],process_identities=identities,static_file_checks=checked,raw_videos_readable=79,full_before={k:v for k,v in before['full'].items() if k not in ['queue','snapshot','latest_log_tail']},full_after={k:v for k,v in after['full'].items() if k not in ['queue','snapshot','latest_log_tail']},ring_sift_status=after['ring_sift_queue']['status'],ring_sift_updated_epoch=after['ring_sift_queue']['updated_epoch'],full_source_count_delta=after['full']['sources']-before['full']['sources'],protocol_atomic_rewrites='Only 4 same-content receipts; SHA checked, no relaxation for code/input/config',deleted_paths_absent=True,representatives_and_static_inputs_intact=True,source_configuration_changed=False))

fail=[]
states=list(csv.DictReader((T/'evidence/VIDEOS_AFTER.csv').open()))
for state in states:
 if 'FAILED' not in state['status']:continue
 p=Path(state['run_path']);j=p/'metrics/local005_solver.json';log=B/'logs'/(state['case']+'__camera.log');versions=read(j) if j.exists() else []
 lines=log.read_text().splitlines();error=lines[-1] if lines else 'NO_LOG';when=float(state['updated_epoch']);fail.append(dict(case=state['case'],stage='camera',status=state['status'],failure_beijing=datetime.datetime.fromtimestamp(when,datetime.timezone(datetime.timedelta(hours=8))).isoformat(),last_error=error,log=str(log),log_tail=lines[-12:],solver_versions=[dict(version=v['version'],success=v['success'],failure=v.get('failure','').splitlines()[-1:] or None) for v in versions],before_actual_deletion=datetime.datetime.fromisoformat(run['start_beijing']).timestamp()>when))
save(T/'evidence/CAMERA_FAILURES_AFTER.json',fail)
actual=[dict(r,status='DELETED',dependency_result='REVIEWED_NO_CURRENT_OR_FUTURE_CONSUMER') for r in run['deleted']];table(T/'CLEANUP_MANIFEST.csv',actual)
summaries=[];children=[]
for route in sorted({r['route'] for r in inv}):
 root=Path(next(r['root'] for r in inv if r['route']==route));remaining=[identity(p) for p in files(root)];prior=[r for r in inv if r['route']==route];deleted=[r for r in actual if r['route']==route]
 unique=lambda rs:sum(r['blocks'] for r in {(r['device'],r['inode']):r for r in rs}.values())
 reasons=collections.Counter(r['reason'] for r in kept if r['route']==route)
 summaries.append(dict(route=route,path=str(root),before_unique_allocated_bytes=unique(prior),deleted_files=len(deleted),deleted_last_link_allocated_bytes=sum(r['reclaimed_allocated_bytes'] for r in deleted),remaining_files=len(remaining),remaining_unique_allocated_bytes=unique(remaining),retention_reasons=json.dumps(reasons,ensure_ascii=False),source_and_conclusion='METHOD_FREEZE + existing M2F13 evidence archive + retained original run metadata; retired variants not adopted'))
 for child in sorted({Path(r['path']).relative_to(root).parts[0] for r in prior}):
  prefix=root/child;old=[r for r in prior if under(Path(r['path']),prefix)];rr=[r for r in remaining if under(Path(r['path']),prefix)];dd=[r for r in deleted if under(Path(r['path']),prefix)]
  if unique(old)<1024**2:continue
  consumers=sorted(set(r['consumer'] for r in read(T/'PROTECTED_PATHS.json')['paths'] if r['path']==str(prefix)))
  children.append(dict(path=str(prefix),before_bytes=unique(old),deleted_files=len(dd),reclaimed_allocated_bytes=sum(r['reclaimed_allocated_bytes'] for r in dd),remaining_bytes=unique(rr),consumer='; '.join(consumers) or 'retained source/config/input identities/metrics plus representative evidence; see PROTECTED_PATHS and RETAINED_LEAVES'))
table(T/'ROOT_DISPOSITION.csv',summaries);table(T/'CHILD_DISPOSITION.csv',children)
table(T/'RETAINED_LEAVES.csv',kept)
for source,target in [(T/'CLEANUP_MANIFEST.csv',T/'CLEANUP_MANIFEST.csv.gz'),(T/'RETAINED_LEAVES.csv',T/'RETAINED_LEAVES.csv.gz'),(O/'HEALTH_AFTER.json',T/'evidence/HEALTH_AFTER.json.gz'),(O/'EXECUTION.json',T/'evidence/EXECUTION.json.gz')]:
 raw=source.read_bytes();target.write_bytes(gzip.compress(raw,mtime=0));assert gzip.decompress(target.read_bytes())==raw
space_now=space();task_alloc=int(subprocess.check_output(['du','-s','-B1',str(T)],text=True).split()[0]);local_alloc=int(subprocess.check_output(['du','-s','-B1',str(O)],text=True).split()[0])
numbers=dict(checked_beijing=now(),device=run['before']['device'],audit_start_available_bytes=before['space']['available_bytes'],before_deletion_available_bytes=run['before']['available_bytes'],after_deletion_available_bytes=run['after']['available_bytes'],current_available_bytes=space_now['available_bytes'],last_link_allocated_reclaimed_bytes=run['reclaimed_allocated_bytes'],deletion_interval_df_net_bytes=run['net_df_bytes'],concurrent_unattributed_delta_bytes=run['net_df_bytes']-run['reclaimed_allocated_bytes'],whole_audit_net_available_bytes=space_now['available_bytes']-before['space']['available_bytes'],task_evidence_allocated_bytes=task_alloc,local_receipts_allocated_bytes=local_alloc,old_archive_bytes=read(T/'evidence/EXISTING_ARCHIVE_CHECK.json')['bytes'],new_full_archive_bytes=0,existing_historical_release_counted=False,same_mount_move_counted=False)
save(T/'evidence/SPACE_FINAL.json',numbers)
gib=lambda n:f'{n/2**30:.4f}'
f=after['full'];phase='阶段' if f['queue']['status'] not in ['COMPLETE','COMPLETE_WITH_FAILURES'] else '最终'
summary_table='| 退役运行 | 删除叶数 | 回收分配MiB | 剩余库存MiB |\n|---|---:|---:|---:|\n'+'\n'.join(f"| {r['route']} | {r['deleted_files']} | {r['deleted_last_link_allocated_bytes']/2**20:.2f} | {r['remaining_unique_allocated_bytes']/2**20:.2f} |" for r in summaries)
space_table='| 时点/量 | 字节 | GiB |\n|---|---:|---:|\n'+'\n'.join(f'| {label} | {numbers[key]} | {gib(numbers[key])} |' for label,key in [('审计开始可用','audit_start_available_bytes'),('实际删除前可用','before_deletion_available_bytes'),('实际删除后可用','after_deletion_available_bytes'),('末链接分配空间回收','last_link_allocated_reclaimed_bytes'),('删除时段df净增加','deletion_interval_df_net_bytes'),('交付检查时可用','current_available_bytes'),('审计开始至交付净变化','whole_audit_net_available_bytes')])
status=f"{after['checked_beijing']}（北京时间），固定 **39组79视频**。{phase}状态：正常结束且有输出 **{f['normal_with_output']}**，正常结束无输出 **{f['normal_without_output']}**，失败 **{sum(v for k,v in f['counts'].items() if 'FAILED' in k)}**，运行 **{sum(v for k,v in f['counts'].items() if 'RUNNING' in k or k=='RENDERING')}**，待运行 **{f['counts'].get('PENDING',0)}**。已有 **{f['videos_with_output']}/79视频（{f['video_coverage']:.2%}）、{f['groups_with_output']}/39组（{f['group_coverage']:.2%}）、{f['sources']}个非空HERO面源**。这些是输出覆盖，不是几何正确率。"
report=f'''# 受保护的V6方法冻结与清理报告

完成方法身份记录，并按新冻结清单实际删除 **4942个普通叶文件，回收 {gib(run['reclaimed_allocated_bytes'])} GiB 分配空间**。13条退役运行均已处置；没有运行算法优化或全量clean。独立执行提交 `1d3fe256`，逐文件身份、理由、状态见 [CLEANUP_MANIFEST.csv.gz](CLEANUP_MANIFEST.csv.gz)，本地另有同名未压缩CSV。

## 当前采用的方法

人工认可、当前固定、等待全量确认：V6 HIST `da92d8ddfaf9a3fc266b518e56e2d3a6c2ed056a`；clean分类执行 `e30ac479e6b555cbe906bd516d09c4849e4b8cbd`、交付 `2d34cc866cd175d4d770a3e09d07b31a5c3662d7`、历史规则 `62c286fcbf39cbba9ec5adb148bd50ba9dc94093`。方法为原V6 Raw及真实映射→017四态→冻结gap→018 `F[state==0]`；原坐标和Face/Vertex ID不变。协议、适配和展示SHA分别见 [METHOD_FREEZE](METHOD_FREEZE.json)。四例名单不是全量入口，四例脚本不是已完成的全量clean运行器。可信孤片残留、开放边界收缩及无GT限制保留。

## 实际清理及保留

{summary_table}

库存按各根唯一inode统计，跨根可能共享，不能把库存简单相加当物理总量。删除回收仅以每次unlink前的末链接分配块计算；本轮最终4942个候选均为独立inode，无硬链接重复计量。没有递归删除父目录，空目录可保留。

- M2F10：清理未采用SMOKE、旧FORMAL-01及诊断重复深度／Mesh／抽帧和图集；FORMAL-02约0.915GiB是当前基线协议及正式面源池，完整保护。M2F11的9个部分运行/审计子目录独立保护，没有按M2F10父目录整树清理。
- H004：删除M2F13扩展曲面和旧重复评价转换；M2F12只删明确无消费者的派生项，保留004相机／地标、完整小指标和代表输入闭包。旧H004方法及本轮未采纳结论仍可追溯；不重新推理或重新选相机。
- M2F7/8/9：清理退役参考帧／相机策略专属缓存、重复抽帧、分割、SIFT／BA派生数组和HERO输出；保留真实失败记录、原配置、输入身份和按原路径顺序选定的少量原生深度／同源Mesh代表。
- M2E、M2F1/2/3/5及深度诊断：只处理现存遗漏派生文件。R5/R10共享CAD完整保留；源码、配置、CSV/JSON指标、日志、patch和原先精简归档没有再次清理。

逐子目录字节与消费者见 [CHILD_DISPOSITION.csv](CHILD_DISPOSITION.csv)，逐根见 [ROOT_DISPOSITION.csv](ROOT_DISPOSITION.csv)。逐保留叶原因见 [RETAINED_LEAVES.csv.gz](RETAINED_LEAVES.csv.gz)；`IMAGE_ORIGIN_NOT_CONFIRMED`、`EXTERNAL_OR_PROTECTED_HARDLINK_ALIAS`及非普通文件单项留存，不阻断其他清理。

源码与版本保留在所有原工作树/Git历史、原RUN_STATE/配置/输入身份文件及M2F13现有归档。现有 `RETIRED_FINAL_EVIDENCE.tar.gz` **94,516,429 B**，完整SHA重新核验等于 `97c894d00be9e93ba9cfdc3471c4a90eb4183a47996039a7527aee68b5fa26c0`，位置未变；没有再复制或压缩整套大目录，也未重复计算M2F13历史释放量。

## 后台与保留资产验证

[PROTECTED_PATHS](PROTECTED_PATHS.json)按消费者及真实目标列保护范围；[代表闭包](evidence/REPRESENTATIVE_CLOSURE.json)追踪链接和manifest依赖。复核在删除前发现并保护9个代表依赖，随后568条保护链接、完整代表JSON与候选0冲突。删除器9项边界检查通过，逐路线批前检查全部静态文件，批内每64叶刷新fd/mmap。没有移动、改名、换链接或更改活动权限，没有暂停/重启后台，没有git clean、历史清洗、环境卸载或系统缓存清扫。

**36,430项静态保留文件检查通过，79段原始视频可读。** 原始视频/大模型只核既有身份与stat，没有重新全盘哈希。所有现用科学源码、协议、参数、CAD、clean输入与实际输出内容核验；仅4个全量协议回执允许运行器同内容原子重写，SHA必须相同。旧HIST池完整静态保全，最新四源clean的Raw/分类/排除集/映射/图与完整回执保留。虚拟配准RUN_001的748文件及RETAIN_DEPENDENCIES祖先均保全，g01_multisurface/g01_sim_rev1实体根和全部assets不动。官方HERO权重、分割权重、P共享环境、V3 Open3D、DXY不在删除允许根内。

前后 **V6 PID185164、Ring+SIFT PID212960的启动ticks、命令、cwd、exe一致**。全量面源从 {before['full']['sources']} 增至 {f['sources']}，runner.log继续推进；SIFT保持 `{after['ring_sift_queue']['status']}`，更新时间随原30秒轮询推进，未抢GPU。完整进程/子进程/fd/maps在压缩前后回执；摘要见 [BACKGROUND_HEALTH.json](BACKGROUND_HEALTH.json)。

{status}

当前阶段见BACKGROUND_HEALTH的active；最近日志 `{f['latest_log']}`，mtime_ns `{f['latest_log_mtime_ns']}`。失败仍在79分母。7例失败中6例为Ring pose graph disconnected；Is18/R5/005的两候选BA完成后，旧validate_select因None与整数比较抛TypeError。记录的7例均发生在实际删除前，没有文件缺失报错；本轮没有修改失败状态或旧验证算法，见 [失败回执](evidence/CAMERA_FAILURES_AFTER.json)。

## 同挂载点空间

全部位于 `/dev/nvme0n1p3`、挂载 `/`、st_dev=66307；普通用户可用空间如下。

{space_table}

删除时段：{run['start_beijing']} → {run['end_beijing']}。df净变化比末链接块数多 {numbers['concurrent_unattributed_delta_bytes']/2**20:.2f} MiB，这是同期其他磁盘活动/元数据统计净差，未归因且不计本轮删除收益。审计期间全量持续写入，新清单、日志及工作树也占空间，因此整个审计时段净变化与删除量不同；以字节回执为准。当前任务证据 {task_alloc/2**20:.2f} MiB，本地审计/删除回执 {local_alloc/2**20:.2f} MiB；新完整资产归档0字节。工作树初次checkout再稀疏的临时释放、同盘移动均不计收益。

本地审计及删除回执：`{O}`；原大资产留在原位，Git只交方法、工程守卫、清单和报告。当前图集继续使用 http://127.0.0.1:8957/index.html ，四源clean展示仍为 http://127.0.0.1:8959/index.html 。本轮到此停止，不自动全量clean或改变科学主线。
'''
(T/'CLEANUP_REPORT.md').write_text(report)
(T/'TECHNICAL_REPORT.md').write_text('# TASK-V6-MAINLINE-FREEZE-AND-STORAGE-CLEANUP-001\n\n本任务完整技术报告见 [CLEANUP_REPORT.md](CLEANUP_REPORT.md)。\n\n方法冻结：[METHOD_FREEZE.md](METHOD_FREEZE.md)。保护、实际删除和后台健康均在该报告链接的机器可读回执中。\n')
(T/'BACKGROUND_HEALTH.md').write_text('# 后台健康\n\n'+status+'\n\nV6与SIFT进程启动身份、命令、cwd一致；全量产物与日志推进，SIFT按原计划等待。36,430静态文件与79视频读取检查通过；虚拟配准与全部祖先保全。源码/配置未改变。相机失败未重试或覆盖，详细原因见CLEANUP_REPORT与CAMERA_FAILURES_AFTER.json。\n')
save(T/'evidence/FINAL_VERIFICATION.json',dict(checked_beijing=now(),result='PASS',deleted_count=4942,deleted_paths_absent=True,protected_static_files=checked,all_79_raw_readable=True,process_identity_unchanged=identities,execution_source_sha256=run['execution_source_sha256'],plan_sha256=run['plan_sha256'],reclaimed_allocated_bytes=run['reclaimed_allocated_bytes'],failure_records_unchanged=True,recorded_failures_before_deletion=all(x['before_actual_deletion'] for x in fail),current_available_bytes=space_now['available_bytes']))
print('FINAL_PASS',len(actual),'deleted,',checked,'static files;',space_now['available_bytes'],'available bytes')
