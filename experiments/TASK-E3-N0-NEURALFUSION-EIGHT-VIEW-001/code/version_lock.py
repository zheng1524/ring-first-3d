"""Create the initial technical version from actual scripts, before experiments."""
from pathlib import Path
import json,hashlib,datetime
R=Path(__file__).resolve().parents[1];REPO=R.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    roots={
      'Camera Gate':REPO/'experiments/TASK-CAMERA-GATE-G01-004-PILOT-001',
      'Gate A':REPO/'experiments/TASK-E3-N0-GATE-A-COMPAT-CROP-METRIC-001',
      'A2':REPO/'experiments/TASK-E3-N0-GATE-A2-PROJECTIVE-CLEANUP-001',
      'A3/V4':REPO/'experiments/TASK-E3-N0-GATE-A3-MASK-BOUNDARY-CLEANUP-001',
      'V5/V6 local':Path('/home/liu/ring_first_3d_e3n0_a3/experiments/TASK-E3-N0-GATE-A3-MASK-BOUNDARY-CLEANUP-001'),
      'Prior official F0':REPO/'experiments/TASK-E3-N0-GATE-B-NEURALFUSION-F0-F2-001'}
    records=[]
    for module,root in roots.items():
        for p in sorted((root/'code').glob('*.py')):
            records.append(dict(module=module,path=str(p),sha256=sha(p),bytes=p.stat().st_size))
    (R/'provenance/SCRIPT_VERSION_AUDIT.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
    doc=REPO/'docs/KEY_TECHNICAL_VERSION_v1.0.md';doc.parent.mkdir(exist_ok=True)
    doc.write_text('''# 关键技术版本 v1.0 — G01_004 当前工程主线及本轮一致性接口

创建依据：研究者2026-11-03明确说明无既存总版本文档，授权根据当前G01_004工作调研建立首版。此文件是首次汇总，不声称存在更早总版本，也不将候选技术升级为正式科学基线。

适用任务：TASK-E3-N0-NEURALFUSION-EIGHT-VIEW-001。历史结论与文件均只读。最新执行细节由该任务config及BEFORE_*冻结记录绑定；任何新工程修正写入该任务TECHNICAL_CHANGELOG.md。

## 真实版本链

E3-A 8f5f7ea（身份/DAG/冻结K和c2w）→E3-B a7c6233（原生HERO/B0/B1）→E3-C e8feece（可见性证据）→E3-D0 d69ade1（原生深度到公制适配）。Camera Gate为6423b27的v0.1候选规范；并非所有相机已通过，原pilot五个均为INSUFFICIENT_EVIDENCE。A2为75ba883；A3/V4为b114ee0；V5/V6为A3本地脚本与原生ID记录，V6证据在40ed60a归档。实际每个脚本的完整路径、字节数、SHA见本轮provenance/SCRIPT_VERSION_AUDIT.json。

## 来源、坐标和相机

以E1 INPUT_ELIGIBILITY.json及E3-A来源DAG绑定原生HERO、原始RGB、Polyp/Ring Mask、归档pack、相机索引和实际CAD。原生深度是相机轴向Z（mm），c2w旋转将相机坐标映射到Ring世界坐标，平移为mm。原生K采用半像素中心一致的尺寸变换；不得混用640×352与640×360。引用缓存rXX不等于解码视频帧号，未知原始帧号保留UNKNOWN。

本轮G01和G06–G08使用同一Camera Gate v0.1数值规则：真实CAD双向轮廓，遮挡/边界剔除，真实RGB独立F与固定空间留出，冻结位姿Sampson误差，视差/正深度/退化与无先验Jacobian可观测性。优先历史真实RGB匹配，缺少时仅CPU SIFT；不下载模型，不用HERO认证位姿，不重新优化相机。完整阈值照录config/CAMERA_GATE_RULES.json。分区使用View Partition原有冻结相机及block，不跨视频混合。

资格与入组分开：CONDITIONAL_USABLE仍不是GT；INSUFFICIENT_EVIDENCE保留原身份。按研究者本轮条件性制度，在身份/坐标合格、Ring没有明确矛盾、没有充分RGB几何反证时，可作为CONDITIONAL_RESEARCH_INPUT入组，明确所有关系/可观测性缺口。UNQUALIFIED_GEOMETRY不入组。负向清理票不得来自Ring不通过或存在明确矛盾的相机；正向支持/未知遮挡仍保留。不会为了八个输入伪造严格资格。

## 清理、Mask及裁剪

原始深度/XYZ/Mask/相机/CAD从不覆盖。已人工认可的G01六来源V6保持其删除ID；其中V3全B、V4 Raw代理、V5及V6定向区域属于显式历史探索，不冒称物理真值。V6的Z<−10.5且X>−3mm是G01人工判读，不能外推其他组。新来源及第二组统一执行A2固定候选规则和同一投影证据：每源最多512候选，合法四邻深度跳变≥1mm、包围带0.25mm、轴极值、Raw距离>1mm且Mask边缘≤2px；未审查保留。实际相机射线、原Mask、CAD首次遮挡，0.25mm支持，8归档px轮廓距离；两个不同分区反证且无支持/层竞争才屏蔽。未知/遮挡不作为负票，CORE内部保护。B竞争点按最新已批准V3原则屏蔽（Polyp内部及非Polyp非Ring原始Mask别名），Ring身份歧义保留。此操作的范围仅固定A2候选，不扩大搜索。新组不凭Raw代理或G01定向XYZ规则额外删除。

每视角独立原生Polyp+Ring bbox，加max(16px,20%最大边长)余量，最小4:3虚拟矩形，等比例至320×240。完全复用Gate A make_crop，A的偏移a*(0.5-x0)-0.5，K_crop=A K_native。最近邻原生ID采样，invalid深度为0，不补洞。旧3px细柄门槛已废止。主体/头部/细柄/连通/新孔洞仅报告真实变化。

## 公制域与官方推理

各组选定清理输入所有保留XYZ加实际CAD顶点，margin=max(2mm,10%最大跨度)，立方边长向上取0.001mm，N=128；O=(lo+hi)/2−L/2，X_model=(X_mm−O)/L，深度Z/L，相机平移(C−O)/L，旋转不变。真实CAD尺寸由顶点检查，不从R10等文件名推断。域在输出前冻结，不根据网络外观重选，不裁掉未解决合法点。

官方NeuralFusion commit 4f0c14f67ad9d2368b68cbeb78c237a6328971e5，ShapeNet noise005匹配config，best.ckpt SHA256=3ac6dc9f219449e8aa5a26dec0a77691714e55d4e29da688c79630bf46068bff。严格加载全部参数；eval/inference_mode，无optimizer、无反传、无训练。实际extractor→FusionNet→integrator写latent→Translator输出SDF与occupancy→官方unknown正哨兵仅供MC→iso0浮点MC→mm。Translator按官方全known查询，不能擅自分块改变count归一。unknown原预测、known及MC哨兵分别保存；边界封闭仅标记不删面。每前缀保留完整latent/count、TSDF、Mesh。平面/插值顶点法线显示使用相同顶点和面，禁止几何平滑。

## 本轮冻结与评价

基于当前资格/分区/姿态多样性选择G01八源；不以网络结果挑选。第二组选G06–G08中当前输入质量好且可用数量足够者，有几源如实报告。每序列空latent/count，正序全前缀及严格逆序全前缀均完整执行；低质量指标不是停止理由，只有工程无效可暂停修复。20–30视角仅规划不推理。

固定分母为所选来源原生合法Polyp观测，删除/未命中都保留计数，CAD遮挡单列，原始面与面积保留率独立。0.25mm一致性仅几何代理，不等于物理GT。分开报告光滑/完整/真实；新增面按输入邻近及真实射线深度近似标记支持/推断/未知，不删面。历史Open3D只作评价且标明输入/分辨率差异。GT/Oracle/Dxy不读取；无直径准确度结论。
''')
    p=R/'TECHNICAL_VERSION_LOCK.md'
    p.write_text('''# Technical version lock — v1.0

当前关键技术文档：../../docs/KEY_TECHNICAL_VERSION_v1.0.md（首次建立，研究者2026-11-03授权）。具体脚本SHA为provenance/SCRIPT_VERSION_AUDIT.json；历史报告阅读记录为provenance/READING_AND_VERSION_RECEIPTS.json。

版本文档SHA256：'''+sha(doc)+'''。

当前状态：技术接口已冻结；输入名单/资格、清理派生文件和各组物理域在正式推理前依次写入config，BEFORE_GPU冻结全部SHA。Camera Gate v0.1仍为候选规范，逐源资格与条件性入组区分。旧F0质量停机规则不适用本轮，不回写历史结果。

官方代码4f0c14f；checkpoint 3ac6dc9f…；无训练。既有六源V6保留历史删除ID，新来源和新组一致复用A2投影及最新B类Mask语义；不外推G01人工XYZ删除。每组各自全保留XYZ+CAD域，Gate A原裁剪函数不变。
''')
    (R/'TECHNICAL_CHANGELOG.md').write_text('''# Technical change record

## v1.0 — 2026-11-03，正式新实验前

- 研究者确认无现成总技术MD，首次根据实际G01_004脚本创建docs/KEY_TECHNICAL_VERSION_v1.0.md。
- 新薄适配将Camera Gate相同规则扩至本轮候选，保留INSUFFICIENT_EVIDENCE并独立记录条件性入组。未修改冻结相机。
- 从旧F0适配层移除仅属于旧任务的几何质量提前停机；本轮完整正序与严格逆序。
- 按研究者新任务对每组独立冻结物理域；不复用旧固定27.959mm。
- 旧规范3px细柄硬门槛已撤销；不作为本轮门禁。
- 不修改历史代码/报告/输入。后续工程差异将在此追加。
''')
    status=json.loads((R/'TASK_STATUS.json').read_text());status['status']='TECHNICAL_V1_CREATED_INPUT_PREPARATION';status['canonical_version_document']=str(doc);status['canonical_version_SHA256']=sha(doc)
    (R/'TASK_STATUS.json').write_text(json.dumps(status,ensure_ascii=False,indent=2)+'\n')
    print('TECHNICAL_V1_CREATED',doc,sha(doc),'scripts',len(records))
if __name__=='__main__':main()
