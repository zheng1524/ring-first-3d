# 002 最终独立审阅

审阅基于提交033271c9a及随后交付核验修复。范围：DXY候选身份修复/迁移、消费者、全量核验器、报告和归档器。没有修改科学模块或启动大计算；本记录不替代待完成的最终图表/归档验证。

## 已关闭 Important

- 此前消费者输入子文件未递归核验、001科学依赖漏出缓存键：前次已验证修复，现仍保持严格校验。
- 本次发现最终核验器未校验VISIBILITY/FIGURES是否属于当前RESULT/BODY，只检查存在及PNG SHA。现加入实际生成键比对及VISIBILITY.npz SHA；report入口要求当前科学键/配置的FINAL_VERIFICATION。还核验freeze中的DXY全帧清单和身份迁移回执。实际刷新前执行新核验器已产生STALE_VISIBILITY拒绝日志，证明不会将旧派生物冒充新结果。

## DXY身份与执行来源

旧包装器近似allclose误指邻近候选，是证据身份错误；此前抽查确认了候选ID唯一与未使用profile，但未充分检查选中参数的精确一致，故未捕获此问题。本轮修复未隐藏该不足。

新执行通过真实to_candidate返回对象和原records对象身份定位，no-Q通过真实baseline对象身份定位；相同数值重复候选必须有对象身份，不任意取第一个。旧完整缓存迁移采用同body/shape/origin且绝对误差≤1e-10的唯一记录；有歧义必须真实重跑。3个身份回归测试再次实测通过，包括旧错误重现与重复参数拒绝。

迁移记录完整覆盖1700帧，修正363个ID，记录0次数值重执行；原选中center/basis/weight、CURVES和官方导出字节不变。原执行包装器及原回执另存并有源码证据包；当前FRAME分别标明旧数值执行SHA与新元数据校验SHA，不把迁移说成重新计算DXY。两条单帧对象捕获诊断单独标记，不冒充全量重跑。

最终二维核验记录为1627 OFFICIAL、66 PIXEL_ONLY、7 NO_CURVE；原32个缺曲线帧恢复29个。758个原可用帧的中心/basis差为0；未将7个不可解帧去掉分母。数据状态、可靠性、正式Ring毫米测量分别记录。

## 主体、科学声明与保护

消费者仍拒绝旧001路径、过期科学键、未授权联合，递归校验相机、CAD、RGB/Mask、二维过程和来源几何。局部单视频与合格子集路由未被身份修复改变。报告区分受控偏置结果、真实残差、不可评价GT；当前拒绝候选不监督，官方恢复候选保留历史拒绝身份；无将收敛/完整网格等同形状验证的声明。

只读核验93个按新科学键实际复算的比较回执：九参数最大差0、偏置最大差0。报告因此可以说明此次ID修复未改变数值主体结果；不能据此宣称真实形状准确。

归档器保护紧凑初体/采样/配准评价及三个完整二维例子，并另保留全量DXY本地过程包；原RGB/视频/权重不复制。旧身份元数据备份另列于DXY_PRESERVE_DEPENDENCIES，原包装器与回执有独立小证据包。全图集本地保留、精选PNG上传，范围在报告中明确。

结论：截至本次审阅，无未关闭Critical/Important。最终交付仍需完成正在执行的全部派生图表刷新、FINAL_VERIFICATION、归档逐成员SHA、提交/远端核验；本审阅不预先声明这些后续动作完成。

## 审阅时文件SHA

- code/dxy_full.py: `093ee813444a4977b542921433fe487156e95dd1b715cda4d338bd761c8eea0f`
- code/repair_dxy_selection_ids.py: `1cd6e645551a78cc0aaca69c3b6843186abe9c18cdfbf6ef0981deb7cd41b709`
- code/verify_revision.py: `9daae7f333fa15a21233abf0fcae0e0d31abb3e23c156e9ede75fa29ac49ceaf`
- code/consume_revision.py: `c73656432c0132d93f141f8e3180f515a7cd116ae25aa1384202875c93c6abfc`
- code/report_revision.py: `8a3d5c17164a3e2682fefab83abfd53118a287bed70592742942f0b846471fbc`
- code/package_revision.py: `8f6f1203db627ea954cb6c00d9fdf288d7ffacc7628ea635760caf7a3086be33`
- evidence/SELECTION_ID_REPAIR_FIT_COMPARISON.json: `a31fc5a31b8c5d332ed86426325492a259fa8a40a6a44513d70bb6acb0831571`
- evidence/stale_derivative_rejection.log: `82d56a1b39cb72aefcff5db93045bb3566709c81b785d3606f7e7824d263b397`
