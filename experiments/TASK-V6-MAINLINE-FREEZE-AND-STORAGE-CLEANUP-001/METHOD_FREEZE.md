# 当前方法冻结

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
