# 失败与未决记录

| ID | 状态/机制 | 证据与处置 |
| --- | --- | --- |
| ENV01 | RESOLVED：四PM文件起初缺失 | 研究者下载补齐后才正式预登记；没有编造规则；docs/保留原字节 |
| ENV02 | RESOLVED：EasyDict1.9 PyPI TLS失败 | pip/curl均未改主环境；取官方1.9标签精确模块置runtime/python，blob/SHA已记录 |
| IMPL01 | CORRECTED：阴性测试u/v赋值颠倒导致IndexError | config/VALIDATION_INITIAL_EXECUTION_ISSUE.json；修正测试索引，仅重跑中断验证，阈值不变 |
| IMPL02 | CORRECTED：派生重核AST namespace遗漏make_domain | config/DERIVED_RECHECK_EXECUTION_ISSUE.json；复用原helper，保留已完成crop，只续算metric |
| GEO01 | FAIL：r14裁后一个medial-ridge宽度代理2px<3px | Fig4、REVIEW02；原生无对应细柄代理。可能是Mask边缘锯齿，不认证细柄丢失；不改ROI/门槛 |
| GEO02 | OBSERVED：nearest重采样身份损失/极端量化 | ref03/r04/r00原ID保留69.48%/77.29%/70.94%；r00原始最大49.77mm，派生仍19.56mm；全部分母和失配身份留存 |
| VIS01 | OBSERVED：离散采样改变CAD前后次序 | 解析变化0，实际采样6源64/45/86/47/107/51（派生）；不把采样资格变化隐藏成解析PASS |
| ROI01 | ORIGINAL_STOP_RETAINED：全包域61.837mm过粗 | 128³voxel0.4831mm，诊断小域55点出界；按任务停域选择并给人工判图 |
| CLN01 | USER_AUTHORIZED：一轮派生清理46点 | 仅55已判读候选，固定跨视角规则/逐点依据；原数据不变，其他原点不清理。条件性相机、RGB相关和背景遮挡未独立标定 |
| CLN02 | UNRESOLVED：9点未获得大轮廓反证 | P47–P55落入其他Polyp Mask/存在深度层和CAD遮挡；保留，未扩大参数搜索或追加一轮 |
| ROI02 | CANDIDATE_PENDING_PM：清理后全包域29.641mm | 容纳全部保留点，0.23157mm/voxel；诊断小域仍9点出界，不使用小域硬裁；正式域未冻结 |
| MOD01 | NOT_TESTED：真正NeuralFusion前向/Unknown译码/GPU | strict CPU加载成功只证明结构/权重；没有F0–F5、Translator前向、任何Mesh、训练或新TSDF |

原始42PASS/2FAIL并未被覆盖。新增清理前后均保留106,144原始点分母；派生输入有效106,098另列，46点动作不冒充重建误差改善。

人工判读仅提供可信性意见，不构成物理GT或相机认证。当前整体GATE_A_FAIL_GEOMETRY；不建议绕过r14门槛直接开Gate B。
