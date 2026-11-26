from audit import *
import ast

expected='99c00fe52effa2589c21ad93c2f06a3b1c4d9c86c4c0c37b9bf5a2db33495b56'
cleanwt=CT.parents[1]
docs={n:dict(path=str(CT/n),sha256=sha(CT/n)) for n in ['METHOD.md','TECHNICAL_REPORT.md','config/SOURCES_FROZEN.json','evidence/VERIFICATION.json','evidence/RENDER_RECEIPT.json']}
for n in ['METHOD.md','TECHNICAL_REPORT.md']:(CT/n).read_text()
frozen=read(CT/'config/SOURCES_FROZEN.json');verification=read(CT/'evidence/VERIFICATION.json');render=read(CT/'evidence/RENDER_RECEIPT.json');results=read(CT/'evidence/RESULTS.json')
assert verification['result']=='PASS' and read(B/'SNAPSHOT.json')['execution_commit']=='da92d8ddfaf9a3fc266b518e56e2d3a6c2ed056a'
modules={}
for name in ['v6_raw/trusted_restore.py','v6_raw/surface_clean.py','mainline/native/cleaning.py','mainline/native/_clean_kernels.py','mainline/native/cleaning_protocol.json']:
 p=cleanwt/'src/ring_first_3d'/name;modules[name]=dict(path=str(p),delivery_sha256=sha(p))
 raw=subprocess.check_output(['git','show','e30ac479e6b555cbe906bd516d09c4849e4b8cbd:src/ring_first_3d/'+name],cwd=cleanwt)
 modules[name]['classification_execution_sha256']=hashlib.sha256(raw).hexdigest()
assert modules['mainline/native/cleaning_protocol.json']['delivery_sha256']==expected==frozen['protocol_sha256']
x=dict(task=T.name,status='人工认可、当前固定、等待全量确认',checked_beijing=now(),V6_execution_commit='da92d8ddfaf9a3fc266b518e56e2d3a6c2ed056a',V6_snapshot=read(B/'SNAPSHOT.json'),clean_delivery_commit='2d34cc866cd175d4d770a3e09d07b31a5c3662d7',classification_execution_commit='e30ac479e6b555cbe906bd516d09c4849e4b8cbd',historical_rule_commit='62c286fcbf39cbba9ec5adb148bd50ba9dc94093',protocol_sha256=expected,modules=modules,documents=docs,pipeline=['current V6 Raw + actual pixel/camera mapping','017 four-state classification','frozen gap supplement','018 F[state==0] subset preserving original V and Face/Vertex IDs'],states={'0':'TRUSTED','1':'UNCERTAIN','2':'REJECTED','3':'UNKNOWN'},excluded_states=[1,2,3],four_examples_not_full_runner=True,four_source_classification_code_sha256=sorted(set(r['source_code_sha256'] for r in results)),input_adapter_sha256=sorted(set(r['input_adapter_sha256'] for r in results)),display_source_sha256=render['source_sha256'],display_note=render['change'],full_clean_executed=False,algorithm_or_parameters_changed=False,limitations=['可信孤片仍可能残留','开放边界可能收缩','UNKNOWN是证据不足，不是错误真值','无GT，删面比例不是精度或误删率'],excluded_work=['C1','MAE gates','Body','smoothing','hole filling','full clean'],confirmation_scope='全量完成后统一检查固定分母的覆盖、残留和边界损失；本轮只固定方法，不开展优化或额外推理')
save(T/'METHOD_FREEZE.json',x)
(T/'METHOD_FREEZE.md').write_text('''# 当前方法冻结

状态：**人工认可、当前固定、等待全量确认**。本次仅记录，不修改运行代码、阈值、队列或输入输出。

| 层次 | 固定身份 |
|---|---|
| V6 HIST全量科学执行 | da92d8ddfaf9a3fc266b518e56e2d3a6c2ed056a，现场命令/配置见BACKGROUND_HEALTH |
| TRUSTED-only实际分类执行 | e30ac479e6b555cbe906bd516d09c4849e4b8cbd |
| clean图文交付 | 2d34cc866cd175d4d770a3e09d07b31a5c3662d7；箭头重绘不等于分类重跑 |
| 历史017分类＋gap＋018可信子集 | 62c286fcbf39cbba9ec5adb148bd50ba9dc94093 |
| 协议SHA256 | 99c00fe52effa2589c21ad93c2f06a3b1c4d9c86c4c0c37b9bf5a2db33495b56 |

入口由当前V6 Raw及真实像素/相机映射进入mapped_input_for_source，调用classify_native及原017核函数和冻结gap，最终导出完整原Raw的F[state==0]。保留原V、原面身份、坐标、Face/Vertex ID；1=UNCERTAIN、2=REJECTED、3=UNKNOWN都进入排除集。方法、参数、适配和展示各自的文件SHA见METHOD_FREEZE.json。

trusted_restore.py目前是四例执行/展示入口，不是已经完成的全量clean运行器；只固定算法及参数，不把四例名单作为全量适用范围。全量完成后再确认适用性。本轮没有全量clean、C1、MAE门控、Body、平滑或补洞。

四例仍有可信孤片残留和开放边界收缩；没有GT，未知不等于错误，删面比例不是正确率。这些限制随方法一并保留。
''')
print('METHOD_FROZEN',expected)
