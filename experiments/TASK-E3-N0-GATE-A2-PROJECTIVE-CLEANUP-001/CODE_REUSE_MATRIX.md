# Executed code reuse

| 历史资产/函数 | 真实路径（相对新repo或绝对只读路径） | 本轮复用 | 未执行/保护 |
| --- | --- | --- | --- |
| Gate A common / guard / native | /home/liu/ring_first_3d_e3n0/experiments/TASK-E3-N0-GATE-A-COMPAT-CROP-METRIC-001/code/common.py | 精确AST绑定新R/REPO；只给该历史GT审计Markdown只读例外 | 不执行旧main；不写旧R；无神经import |
| Gate A baseline及清理证据 | 同上ROOT的DERIVED_INPUT_LINEAGE、PROJECTIVE_CLEANUP_EVIDENCE/DECISIONS、config/PROJECTIVE_CLEANUP_PREREGISTERED、POST_REVIEW_DOMAIN_SELECTION | SHA继承106098基线和46历史排除，保留9点身份 | 不重复删除46点 |
| make_crop / ridge_proxy | 同上code/crop.py | 精确函数、不改20%/16px ROI、nearest、K'=AK | 无双线性或新Mask |
| make_domain / wire_box | 同上code/metric_domain.py、human_review_figures.py | 精确域规则及线框可视化 | 不以25.735mm设目标 |
| source / mesh_scene / cast / ringscene / ringmesh | experiments/TASK-E3-D0-OPEN3D-TSDF-BASELINE-001/code/common.py | 通过Gate A精确AST复用；冻结CAD首交/相机 | 不调用TSDF integrate/体积接口 |
| HEROToTSDFAdapter | D0/code/hero_tsdf_adapter.py | 原生合法深度身份和公制转换检查 | 无新TSDF |
| unproject | /home/liu/polyp_research/ring_anchor_3d/experiments/ring_first_v1/scripts/common.py | 原K/c2w的精确历史反投影 | 不改相机 |
| scaled_intrinsics / project_camera / camera_rays / configure | visualization/real_p0_renderer.py | 直接导入、实际调用；含native/archive半像素关系 | 只读CPU |
| SameCameraScene | visualization/same_camera_scene.py | 原黑色CAD实体raycast/ring_image | 无合成纹理或补面 |
| View Partition、来源DAG、E3-A/B身份 | D0/HERO_TSDF_INPUT_MANIFEST.json、VIEW_COVERAGE_SELECTION.csv；E1/provenance/INPUT_ELIGIBILITY.json | 直接继承已审六源、上游RGB SHA与block，不重审全17源 | ref08/r04共享B3；Raw面只作原身份/距离候选 |
| Camera Gate资格 | experiments/TASK-CAMERA-GATE-G01-004-PILOT-001/CAMERA_QUALIFICATION.csv | 五pilot历史INSUFFICIENT_EVIDENCE原样输出 | r14不可否定他源；不优化位姿 |
| E3-C可见性设计 | /home/liu/ring_first_3d_e3c/experiments/TASK-E3-C-VISIBILITY-CONSENSUS-001/code/visibility.py | 沿用CAD/层竞争/Unknown不作否定的既有语义；实际cast由同源D0路径执行 | 不导入其17源main/资格，不消费FREE_SPACE_CONFLICT删除标签 |

所有实际抽取函数的源码SHA、AST SHA和行号见config/VALIDATION_REUSE.json。新增仅为候选枚举、保守证据归约、派生副本、诊断及组合图，不重新发明投影/反投影/射线。
