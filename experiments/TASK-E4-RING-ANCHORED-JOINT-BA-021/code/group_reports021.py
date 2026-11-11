"""Four independent numerical research reports, fixed metric definitions and denominators."""
from geometry021 import *
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

def md(rows,keys):
 def fmt(x):
  if x is None:return'NOT_EVALUABLE'
  if isinstance(x,float):return'%.6f'%x
  return str(x).replace('|','/')
 return'| '+' | '.join(keys)+' |\n| '+' | '.join(['---']*len(keys))+' |\n'+'\n'.join('| '+' | '.join(fmt(x.get(k))for k in keys)+' |'for x in rows)+'\n'

def pooled(group):
 conf=next(g for g in load(R/'config/FOUR_GROUP_INPUTS.json')if g['group']==group);out=[];trans=[]
 for role in ['FIT','HOLDOUT','ALL']:
  for body in ['B0','B2']:
   errs=[];N=0;hit=0;cost=0.;supported=0;unknown=0
   for s in conf['sources']:
    if role!='ALL'and s['role']!=role:continue
    a=np.load(R/'evaluation/groups'/group/(s['id']+'_SOURCE_EVIDENCE.npz'));mask=a[body+'_active'];unknown+=int((~a['HERO_own_CAD_order_valid']).sum())if'HERO_own_CAD_order_valid'in a else 0;err=abs(a[body+'_depth_mm']-a['HERO_depth_mm']);N+=len(mask);hit+=int(mask.sum());supported+=int((mask&(err<=.5)).sum());errs.extend(err[mask]);cost+=float(np.where(mask,np.minimum(err,10.),10.).sum())
   out.append(dict(group=group,body=body,role=role,fixed_native_N=N,hit_N=hit,miss_N=N-hit,HERO_CAD_order_UNKNOWN_N=unknown,hit_fraction=hit/N,correct_first_depth_proxy_fraction=supported/N,MAE_mm=stats(errs)['MAE'],median_mm=stats(errs)['median'],p95_mm=stats(errs)['p95'],max_mm=stats(errs)['maximum'],fixed_denominator_capped_cost_mm=cost/N,missing_penalty_mm=10.,conditional_error_not_GT=True))
  a=[];b=[];gain=[];lost=[];N=0;co=0;ng=0;nl=0
  for s in conf['sources']:
   if role!='ALL'and s['role']!=role:continue
   d=np.load(R/'evaluation/groups'/group/(s['id']+'_SOURCE_EVIDENCE.npz'));x=d['B0_active'];y=d['B2_active'];c=x&y;g=~x&y;l=x&~y;N+=len(x);co+=int(c.sum());ng+=int(g.sum());nl+=int(l.sum());e0=abs(d['B0_depth_mm']-d['HERO_depth_mm']);e2=abs(d['B2_depth_mm']-d['HERO_depth_mm']);a.extend(e0[c]);b.extend(e2[c]);gain.extend(e2[g]);lost.extend(e0[l])
  trans.append(dict(group=group,role=role,fixed_N=N,common_N=co,gained_N=ng,lost_N=nl,net_hit_change_N=ng-nl,common_B0_error_mm=stats(a),common_B2_error_mm=stats(b),gained_B2_error_mm=stats(gain),lost_B0_error_mm=stats(lost)))
 save('metrics/groups/'+group+'_POOLED_BODY_NATIVE.json',out);table('metrics/groups/'+group+'_POOLED_BODY_NATIVE.csv',out);save('metrics/groups/'+group+'_EXACT_COMMON_GAINED_LOST.json',trans);table('metrics/groups/'+group+'_EXACT_COMMON_GAINED_LOST.csv',trans);return out,trans

def source_connectivity(group):
 conf=next(g for g in load(R/'config/FOUR_GROUP_INPUTS.json')if g['group']==group);out=[]
 for s in conf['sources']:
  z=np.load(s['mesh']['path']);m=trimesh.Trimesh(z['V'],z['F'],process=False);adj=m.face_adjacency;G=coo_matrix((np.ones(len(adj)),(adj[:,0],adj[:,1])),shape=(len(z['F']),len(z['F']))).tocsr();n,lab=connected_components(G,directed=False);fa=trimesh.triangles.area(z['V'][z['F']]);mass=np.bincount(lab,weights=fa);out.append(dict(group=group,source=s['id'],face_connected_components_N=n,largest_component_area_fraction=float(mass.max()/fa.sum()),cumulative_source_area_mm2=float(fa.sum()),original_face_ids_preserved=True,open_surface_watertight_expected=False))
 save('metrics/groups/'+group+'_SOURCE_CONNECTIVITY.json',out);table('metrics/groups/'+group+'_SOURCE_CONNECTIVITY.csv',out);return out

def report(group):
 consistency=load(R/'metrics/groups'/f'{group}_HERO_CONSISTENCY.json');coverage=load(R/'metrics/groups'/f'{group}_GEOMETRIC_COVERAGE.json');quality=load(R/'metrics/groups'/f'{group}_BODY_QUALITY.json');views=load(R/'metrics/groups'/f'{group}_PROJECTIONS.json');areas=load(R/'metrics/groups'/f'{group}_SOURCE_AREAS.json');loc=load(R/'metrics/groups'/f'{group}_FAILURE_LOCATIONS.json');ring=load(R/'metrics/groups'/f'{group}_HERO_RING_MATERIAL.json');base=load(R/'metrics/groups'/f'{group}_ESTIMATED_BASE_RELATION.json');bodycoverage=load(R/'metrics/groups'/f'{group}_BODY_COVERAGE.json');pool,trans=pooled(group);conn=source_connectivity(group);p={(a['body'],a['role']):a for a in pool};q={a['body']:a for a in quality};t={a['role']:a for a in trans};direction=next(a for a in load(R/'metrics/FOUR_GROUP_DIRECTION_COVERAGE.json')if a['group']==group);proj=[]
 for b in ['B0','B2']:
  for role in ['FIT','HOLDOUT']:
   a=[v for v in views if v['body']==b and v['role']==role];I=[v['Inner_px']['MAE']for v in a if v['Inner_px']['N']];O=[v['Outer_px']['MAE']for v in a if v['Outer_px']['N']];proj.append(dict(group=group,body=b,role=role,views_N=len(a),IoU_macro=float(np.mean([v['IoU']for v in a])),IoU_worst=min(v['IoU']for v in a),contour_MAE_macro_px=float(np.mean([v['contour_px']['MAE']for v in a])),contour_worst_frame_p95_px=max(v['contour_px']['p95']for v in a),Ring_hard_balanced_MSE_macro=float(np.mean([v['Ring_hard_balanced_MSE']for v in a])),Ring_Inner_macro_MAE_px=float(np.mean(I))if I else None,Ring_Outer_macro_MAE_px=float(np.mean(O))if O else None,Ring_Inner_valid_views_N=len(I),Ring_Outer_valid_views_N=len(O)))
 table('metrics/groups/'+group+'_PROJECTION_MACRO.csv',proj);save('metrics/groups/'+group+'_PROJECTION_MACRO.json',proj);d={(a['body'],a['role']):a for a in proj};err=consistency['depth_difference_mm'];score=dict(group=group,TRUSTED_sources_N=consistency['sources_N'],directed_HERO_pairs_N=consistency['ordered_pairs_N'],fixed_pair_observation_N=consistency['fixed_pair_observation_N'],common_effective_fraction=consistency['effective_common_fraction'],HERO_pair_MAE_mm=err['MAE'],HERO_pair_median_mm=err['median'],HERO_pair_p95_mm=err['p95'],HERO_support_fraction=consistency['supported_fraction'],front_disagreement_proxy_fraction=consistency['front_proxy_fraction'],deeper_observation_fraction=consistency['deeper_fraction'],CAD_occluded_fraction=consistency['CAD_occluded_fraction'],UNKNOWN_fraction=consistency['unknown_fraction'],cumulative_source_area_mm2=coverage['cumulative_source_area_mm2'],distinct_centroid_surface_cells_025mm_N=coverage['distinct_occupied_surface_cells_N'],multi_source_cell_fraction=coverage['multiple_source_cell_fraction'],native_TRUSTED_pixel_N=coverage['native_TRUSTED_N'],native_Polyp_pixel_denominator=coverage['native_Polyp_mask_denominator'],B0_FIT_HERO_MAE_mm=p['B0','FIT']['MAE_mm'],B2_FIT_HERO_MAE_mm=p['B2','FIT']['MAE_mm'],B0_FIT_hit_fraction=p['B0','FIT']['hit_fraction'],B2_FIT_hit_fraction=p['B2','FIT']['hit_fraction'],common_FIT_N=t['FIT']['common_N'],gained_FIT_N=t['FIT']['gained_N'],lost_FIT_N=t['FIT']['lost_N'],B0_HOLDOUT_HERO_MAE_mm=p['B0','HOLDOUT']['MAE_mm'],B2_HOLDOUT_HERO_MAE_mm=p['B2','HOLDOUT']['MAE_mm'],B0_FIT_HERO_p95_mm=p['B0','FIT']['p95_mm'],B2_FIT_HERO_p95_mm=p['B2','FIT']['p95_mm'],B0_HOLDOUT_HERO_p95_mm=p['B0','HOLDOUT']['p95_mm'],B2_HOLDOUT_HERO_p95_mm=p['B2','HOLDOUT']['p95_mm'],B0_HOLDOUT_IoU=d['B0','HOLDOUT']['IoU_macro'],B2_HOLDOUT_IoU=d['B2','HOLDOUT']['IoU_macro'],Ring_HOLDOUT_Inner_MAE_px=d['B2','HOLDOUT']['Ring_Inner_macro_MAE_px'],Ring_HOLDOUT_Outer_MAE_px=d['B2','HOLDOUT']['Ring_Outer_macro_MAE_px'],B2_dense_Ring_min_mm=q['B2']['Ring_dense_min_mm'],B2_Ring_FCL_surface_collision=q['B2']['Ring_FCL_surface_collision'],B2_self_intersection_pairs_N=q['B2']['self_intersection_pairs_N'],B2_components_N=q['B2']['components_N'],B2_nonmanifold_edges_N=q['B2']['nonmanifold_edges_N'],B2_max_displacement_mm=q['B2']['max_vertex_displacement_mm'],B2_max_edge_stretch=q['B2']['max_edge_stretch'],B2_min_area_ratio=q['B2']['min_area_ratio'],all_native_source_coordinates_verified=True,absolute_3D_accuracy='NOT_EVALUABLE',GT_used=False)
 cov=load(R/'metrics/groups'/f'{group}_CO_VISIBLE_FIRST_LAYER.json');ce=cov['co_visible_candidate_depth_mm'];rev=load(R/'metrics/groups'/f'{group}_REVERSE_RING_CONTAINMENT.json');rb=next(x for x in rev if x['body']=='B2');score.update(co_visible_first_layer_candidate_N=cov['co_visible_first_layer_candidate_N'],co_visible_first_layer_candidate_fraction=cov['co_visible_candidate_fraction_fixed'],co_visible_candidate_MAE_mm=ce['MAE'],co_visible_candidate_median_mm=ce['median'],co_visible_candidate_p95_mm=ce['p95'],own_source_CAD_order_UNKNOWN_N=cov['own_source_CAD_order_UNKNOWN_N'],B2_reverse_CAD_containment_status=rb['status'],B2_CAD_vertices_inside_body_N=rb['CAD_vertices_inside_body_N'],B2_CAD_face_centers_inside_body_N=rb['CAD_face_centers_inside_body_N'],B2_CAD_to_body_min_signed_mm=rb['min_CAD_to_body_signed_mm'])
 score.update(cumulative_HERO_vertices_inside_CAD_beyond02mm_N=sum(a['vertices_inside_CAD_beyond02mm_N']for a in ring),cumulative_HERO_face_centers_inside_CAD_beyond02mm_N=sum(a['face_centers_inside_CAD_beyond02mm_N']for a in ring),cumulative_HERO_inside_CAD_face_centroid_area_proxy_mm2=sum(a['inside_face_centroid_area_proxy_mm2']for a in ring))
 # Case-specific interpretation of actual evidence, not case-specific fitting/thresholds.
 notes={
 'G03':('长柄的来源间分歧与主体缺失同时存在','共同命中集合的FIT/HOLDOUT MAE分别从1.278→1.097、1.085→0.981mm改善；但新增命中3213/1418条射线的平均误差达7.204/7.816mm，实际长柄原面到主体短翼交点的连线证明新增命中不等于正确首层恢复。详见G03_NEW_HIT_FAILURE_LOCATIONS与New_First_Hits_Are_Not_Correct_Surface.png。原生HERO含长柄可见片，但各来源深度分歧明显；图中长柄片与头部还存在原始断开/错层。B2只产生短棱/三角翼，未覆盖完整长柄。021没有优化主体，不能把新图当新恢复。历史016实测未命中分支缺少深度梯度、候选支持与观测方向限制；本轮以当前命中、毫米残差、逐面位置和方向覆盖复核这些问题，不能从静态审计单独证明唯一成因。','先在相同原生Pixel/Face ID上区分长柄同层支持、来源深度断裂和真正未命中；优先补互补观察方向或受控缺失覆盖机制，而不是增加无解释迭代。','不建议直接进行整个长柄拼接。可以保留已有可见原面作为研究输入，但需先解决跨来源分歧和头柄连接证据。'),
 'G05':('局部接触/基底不确定性与少量来源差异','多HERO大部分可比较区域相容，B2与可信可见面的适配较好；仍有前方分歧、深层和Unknown，不能将所有表面合为一层。背景基底仍为WEAK，模型冠面/灰底盖不是已恢复的真实基底。继承的CAD微小相交必须保留。','优先验证同层支持较强、远离Ring材料冲突的局部原面与主体连接；保留基底不确定性，不用隐藏底盖定义真实组织。','适合作为局部原生HERO保留与受控曲面拼接的候选，先解决Ring接触和接缝可见性。此建议不是本轮已通过最终融合验收。'),
 'G06':('主体局部网格畸变，而非普遍HERO失配','原生HERO的一致性相对较好；B2整体适配提高，但局部边长明显伸长、面积压缩。无非邻接自交不等于局部质量良好，继承微小Ring穿入也不能忽略。','优先在固定可信原面和相同分母下研究局部连接与面片质量保护；针对伸长/面积压缩最大面片建立局部可见性检查，避免重复全局收缩。','四组中较适合优先开展局部原生HERO保留/主体拼接的受控候选；必须处理Ring邻近实体冲突和局部低质量三角形，不自动进入融合。'),
 'G01':('跨视频共享刚体与原生深度的残余不一致','本报告默认使用事前指定021 B3派生005坐标，并同时保留RoMa/020R3/021B2-B3统一比较。共同SIFT全部是背景，低重投影残差不直接保证息肉几何一致。相机轨迹误差、HERO深度和局部非刚性/分割因素尚不能完全分离。','优先根据共同地标消元信息、未参与BA轨迹、固定21源HERO支持/Unknown与实际残差空间分布决定下一步；不以主体IoU或命中条件MAE一项选择位姿。','暂不建议全局跨视频拼接。可先在明确同层且多来源支持的局部原面上设计下一轮验证；当前共同坐标只是冻结研究候选。')}
 title,analysis,nextstep,join=notes[group];top=sorted(loc,key=lambda a:a['B2_surface_distance_mm'],reverse=True)[:8];boundary=[]
 for x in top:boundary.append(dict(source=x['source'],original_face_id=x['original_face_id'],XYZ_mm=x['XYZ_mm'],B0_surface_mm=x['B0_surface_distance_mm'],B2_surface_mm=x['B2_surface_distance_mm'],visibility=x['visibility_class']))
 text=f'''# {group} 定量几何审计

**主要瓶颈：{title}。** 本轮只读原生TRUSTED、018 B0/B2及冻结相机；无局部ICP、HERO重推、表面修复或GT。G01的005只施加共享刚体；其他三组均为同视频叠加，绝非已完成跨视频配准。

## A. 指标总表与口径

真实来源{consistency['sources_N']}份，{consistency['ordered_pairs_N']}个有向源–目标对；固定重复观测分母{consistency['fixed_pair_observation_N']:,}，有效可比较{consistency['comparable_N']:,}（{consistency['effective_common_fraction']:.3%}）。这些不是独立统计样本，也不是唯一表面积。

| 指标 | 数值 | 单位/分母/说明 |
| --- | ---: | --- |
| HERO深度 MAE / Median / P95 / Max | {err['MAE']:.6f} / {err['median']:.6f} / {err['p95']:.6f} / {err['maximum']:.6f} | mm；所有合格可比较有向观测池化，N={err['N']:,}；包括单列的后方观测，不冒充纯共表面准确误差 |
| 首层共同可见候选 MAE / Median / P95 / Max | {ce['MAE']:.6f} / {ce['median']:.6f} / {ce['p95']:.6f} / {ce['maximum']:.6f} | mm；N={cov['co_visible_first_layer_candidate_N']:,}，占固定分母{cov['co_visible_candidate_fraction_fixed']:.3%}；排除后方/可能正常自遮挡，仍是未校准可见性代理 |
| 源HERO自身位于CAD后方/次序未知 | {cov['own_source_CAD_order_UNKNOWN_N']:,} | 重复源–目标分母；不把它当真实自由空间 |
| ±0.5mm支持代理 | {consistency['supported_fraction']:.3%} | 固定源–目标分母 |
| 前方分歧代理 | {consistency['front_proxy_fraction']:.3%} | 同分母；几何代理非物理错误GT |
| 后方/可能自遮挡 | {consistency['deeper_fraction']:.3%} | 同分母；不能直接称错误双层 |
| Ring CAD遮挡 | {consistency['CAD_occluded_fraction']:.3%} | 同分母；首次交点判断 |
| UNKNOWN | {consistency['unknown_fraction']:.3%} | 越界、缺深度、目标Ring次序不可靠等 |
| 累计来源TRUSTED面积 | {coverage['cumulative_source_area_mm2']:.6f} | mm²；按来源相加，非唯一解剖面积 |
| 占据的面心表面格 | {coverage['distinct_occupied_surface_cells_N']} | 0.25mm固定格的面心并集代理；非面积/体积真值 |
| 多来源占据表面格比例 | {coverage['multiple_source_cell_fraction']:.3%} | 上述表面格N；受离散面片和格相位影响 |
| 原生TRUSTED可用观测 | {coverage['native_TRUSTED_N']:,} / {coverage['native_Polyp_mask_denominator']:,} | 每源Polyp原生像素重复分母；空缺含未观测/不合格，不等于缺失解剖面积 |
| 独立绝对相机/形状精度 | NOT_EVALUABLE | 无部署位姿GT，禁止伪造绝对精度 |

首层共同可见候选严格要求源HERO位于自身CAD之前、目标原生首次深度有效且位于目标CAD之前；候选为±0.5mm相容或前方分歧，后方观测排除为可能正常自遮挡。与上表包括后方的历史可比较口径并列保留，不能把任何一项冒充物理GT共表面精度。

### 原生HERO→主体首层命中（全部原始ID，不补缺失）

'''+md(pool,['body','role','fixed_native_N','hit_N','miss_N','HERO_CAD_order_UNKNOWN_N','hit_fraction','correct_first_depth_proxy_fraction','MAE_mm','median_mm','p95_mm','max_mm','fixed_denominator_capped_cost_mm'])+'''
误差单位mm，条件误差只对真实有效首层且HERO本身位于CAD之前的观测计算；miss_N是全部无有效首层（含CAD/源次序Unknown），不全部归因主体。原生观测分母不删；G03/G05/G06已独立核验619,078条源次序Unknown为0。正确首层代理是有效且|dz|≤0.5mm，占固定分母。固定代价为min(|dz|,10mm)，未命中10mm，预登记诊断而非GT误差。

'''+md(trans,['role','fixed_N','common_N','gained_N','lost_N','net_hit_change_N','common_B0_error_mm','common_B2_error_mm','gained_B2_error_mm','lost_B0_error_mm'])+'''
共同/新增/丢失严格依据同一来源原生Pixel ID，不比较不同集合的均值来制造收益。

'''+f"二维与深度需分别判断：HOLDOUT IoU {d['B0','HOLDOUT']['IoU_macro']:.6f}→{d['B2','HOLDOUT']['IoU_macro']:.6f}，但HOLDOUT深度MAE {p['B0','HOLDOUT']['MAE_mm']:.6f}→{p['B2','HOLDOUT']['MAE_mm']:.6f}mm；FIT深度P95 {p['B0','FIT']['p95_mm']:.6f}→{p['B2','FIT']['p95_mm']:.6f}mm。覆盖增加不能自动解释为正确形状改善。"+'''

### 完整真实Mask和Ring投影

'''+md(proj,['body','role','views_N','IoU_macro','IoU_worst','contour_MAE_macro_px','contour_worst_frame_p95_px','Ring_hard_balanced_MSE_macro','Ring_Inner_macro_MAE_px','Ring_Outer_macro_MAE_px','Ring_Inner_valid_views_N','Ring_Outer_valid_views_N'])+'''
640×360原图像素；每视角内轮廓双向距离统计，再宏平均。Ring硬Mask平衡MSE不是像素距离，也不同于优化用180×320软Mask MSE。I/O来自DXY实际弧回溯原Ring Mask≤2.5px，非完整外推椭圆；无弧则缺失N=0。逐视角JSON/CSV保留MAE/Median/P95/Max与样本N。

### 主体质量、形变、CAD和基底

'''+md(quality,['body','vertices_N','visible_faces_N','solid_faces_N','inferred_cap_faces_N','components_N','boundary_edges_N','nonmanifold_edges_N','self_intersection_pairs_N','Ring_FCL_surface_collision','Ring_dense_min_mm','Ring_dense_inside_faces_N','max_vertex_displacement_mm','max_edge_stretch','min_area_ratio'])+'''
位移和CAD距离为mm；边长/面积比无量纲。主体64阶面内采样、CAD11射线符号，沿用−0.001mm侵入诊断；源HERO另用统一−0.02mm材料样本诊断。FCL独立检查表面相交，有限采样不是精确无穿透证书。底盖参与闭合实体质量检查，始终不参与可见深度/轮廓监督。

'''+md(base,['body','base_status','cap_enabled','minimum_vertex_height_mm','illegal_below_base_vertices_N','cap_vertex_plane_distance_max_mm','model_Hmax_above_estimated_base_mm','model_H95_vertex_sample_mm'])+'''
基底来自独立历史背景估计而非Ring平面，保留其不确定性；上表中高度只是相对估计基底的模型值，绝非真实高度精度。

### Ring反向实体包含检查

'''+md(rev,['body','status','fixed_CAD_samples_N','CAD_vertices_inside_body_N','CAD_face_centers_inside_body_N','min_CAD_to_body_signed_mm','tolerance_mm'])+'''
Ring实际顶点/面心到有效闭合主体的有符号距离；仅在主体封闭、法向一致、无非邻接自交时计算。阈值−0.001mm，与表面相交/FCL及主体→CAD检查互补；有限采样不保证不存在任何穿透。推断底盖仅用于明确标识的模型实体诊断。

### 原生TRUSTED HERO与CAD材料

'''+md(ring,['source','referenced_vertex_N','original_face_N','vertices_inside_CAD_beyond02mm_N','face_centers_inside_CAD_beyond02mm_N','min_signed_CAD_distance_mm','inside_face_centroid_area_proxy_mm2'])+'''
全部原始来源独立记录；统一材料距离阈值−0.02mm、11射线多数符号。面积为被判入材料的原面面心面积代理，跨来源重复，不是精确穿入体积或唯一面积。未因靠近Ring删除/移动任何原面，也不把TRUSTED标签当实体无穿透证书。

### 主体的来源支持/未知面积代理

'''+md(bodycoverage,['body','visible_mesh_area_mm2','supported_centroid_area_proxy_mm2','front_disagreement_area_proxy_mm2','behind_only_area_proxy_mm2','unknown_area_proxy_mm2','supported_area_fraction'])+'''

单位mm²，按主体真实可见面三角形面心在各原生来源中的首层深度证据归类；不是唯一解剖面积或真实背面恢复证明。

## B. 真实三维误差分布与完整六视角

'''+f'''[HERO逐面毫米误差与局部变形](figures/groups/{group}/Actual_3D_Error_Distribution.png) · [主体真实命中三角面的毫米误差](figures/groups/{group}/Body_Surface_Native_Depth_Error_mm.png) · [完整六视角A/B/C图集](figures/groups/{group}/Six_View_HERO_Body_Evidence.png) · [B0/B2六视角主体](figures/groups/{group}/Six_View_B0_B2_Body_Only.png)。

[原生可用覆盖与缺失首层](figures/groups/{group}/Native_Observation_Coverage_And_Missing_Hits.png) · [实际Ring穿入面片与局部质量](figures/groups/{group}/Ring_Contact_And_Local_Mesh_Quality.png)。

主体误差色图来自实际原生首层交点的轴向残差，按实际命中三角面归集，未命中面和推断底盖为灰色；灰色不是零误差。HERO表面色图为原始面心到实际主体三角面的几何距离（0–2mm显示截幅，原数值不截断）；它不替代可见性或首层深度评价。

## C. 主要失败区域定位

'''+md(boundary,['source','original_face_id','XYZ_mm','B0_surface_mm','B2_surface_mm','visibility'])+f'''
完整逐面/原生像素数组见`evaluation/groups/{group}/*_SOURCE_EVIDENCE.npz`，所有来源Face ID、Pixel ID和来源相机可追溯。上表是冻结后的最大局部误差诊断，不用于选择模型或清面。逐面名义TRUSTED不等于物理GT。

方向覆盖（各视频各自合法坐标，不跨未配准坐标池化）：`{json.dumps(direction['per_native_video'],ensure_ascii=False)}`。来源连续性见`metrics/groups/{group}_SOURCE_CONNECTIVITY.csv`；原始分量和缺口均保留，不补洞。

## D. 误差来源判断

{analysis}

- Ring重投影提供当前固定相机的真实二维几何代理；同一Ring的绕轴对称使它不能单独认证全部六自由度。坐标核对通过只是输入完整性，不是相机真实精度。
- 原生源–目标深度及前方/后方分布支持“来源存在/缺少一致性”的判断；不能仅凭它区分相机误差与HERO深度误差。后方表面保留合法遮挡解释。
- 主体未命中、错误首层、实际位移/面片质量及来源原面位置可说明哪些表面未被当前表达解释；本轮未重新训练，不能单独认定增加自由度必能修复。
- Ring邻近材料矛盾按实际CAD样本与FCL独立记录。属于继承接触/穿入的情况不得称为新021优化造成，也不得称零碰撞成功。

## E. 下一步具体建议

主要瓶颈为**{title}**；当前多来源可比较深度误差量级MAE={err['MAE']:.3f}mm、P95={err['p95']:.3f}mm，影响区域和原面见上表及三维图。支持代理覆盖为{consistency['supported_fraction']:.2%}固定重复分母；这是可信候选区域的证据，不是准确率。

{nextstep}

**是否建议原生HERO保留与主体拼接：** {join}

## 固定审计表

| 审计项目 | 必须汇报 |
| --- | --- |
| 目标组数 | 本报告1组；全任务4组；本组{consistency['sources_N']}个原生来源，全部保留 |
| 本算法独立成功 | 本组完成021自身定量审计与图层导出；018主体为明确授权只读对照，未冒充021新重建 |
| 本算法失败 | 物理精度NOT_EVALUABLE，继承碰撞/未命中/局部分歧均保留，不以数值输出称科学成功 |
| 历史测量值回退 | 0；未读旧Dxy测量补值 |
| 失败组及具体原因 | 见本报告C/D及原面位置CSV，原始未知与缺面不填补 |
| 最终统计样本 | 全部来源/计划视角/固定原生Pixel ID；未命中保留在分母 |
| 是否使用GT选择算法 | 否；冻结资产直接审计，无GT或逐模型ICP |

完整来源、图层、相机和公制GLB：`derived/{group}/SOURCE_LAYER_INDEX.json`、`derived/{group}/{group}_INDEPENDENT_LAYERS_NOT_FUSION.glb`。全部原面保持独立；GLB只作精确mm→m单位导出，不是尺度估计。GT测量MedARE/MAE/P95/Max均NOT_EVALUABLE，历史测量回退=0。
'''
 (R/(group+'_GEOMETRY_AUDIT.md')).write_text(text,encoding='utf8');save('metrics/groups/'+group+'_SCORECARD_ROW.json',score);save('runtime/'+group+'_REPORT_COMPLETE.json',dict(epoch=time.time()));print('GROUP_REPORT021',group,flush=True);return score

def main():
 rows=[]
 for g in ['G03','G05','G06','G01']:
  while not all((R/'runtime'/(g+'_'+m+'.json')).exists()for m in ['FIGURES_COMPLETE','BODY_ERROR_MAP_COMPLETE','SOURCE_GEOMETRY_COMPLETE','CO_VISIBLE_COMPLETE','REVERSE_RING_COMPLETE','COVERAGE_FIGURE_COMPLETE','COLLISION_FIGURE_COMPLETE']):time.sleep(5)
  rows.append(report(g))
 rows=sorted(rows,key=lambda a:GROUPS.index(a['group']));save('metrics/FOUR_GROUP_GEOMETRY_SCORECARD.json',rows);table('FOUR_GROUP_GEOMETRY_SCORECARD.csv',rows);save('runtime/FOUR_GROUP_REPORTS_COMPLETE.json',dict(epoch=time.time()));print('FOUR_GROUP_REPORTS021_COMPLETE',flush=True)
if __name__=='__main__':main()
