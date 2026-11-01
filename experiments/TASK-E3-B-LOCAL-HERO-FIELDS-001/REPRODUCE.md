# E3-B REPRODUCE

仅依赖白名单原始资产和已核验的历史几何函数；大NPZ/PLY/视频/权重不复制。Python：`/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python`；CPU Open3D为原surface_fusion_v3/vendor，CUDA_VISIBLE_DEVICES为空。缺文件/哈希不符必须停止，禁止以旧融合结果、照片、其他预测补齐。

初次执行顺序（必须是父提交8f5f7ea的新隔离分支，不能覆盖本次冻结）：

```bash
E3B_ROOT=/home/liu/ring_first_3d_e3b/experiments/TASK-E3-B-LOCAL-HERO-FIELDS-001
E3B_PYTHON=/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python
export PYTHONDONTWRITEBYTECODE=1
"$E3B_PYTHON" "$E3B_ROOT/code/hero_native_adapter.py"
"$E3B_PYTHON" "$E3B_ROOT/code/validate_local_fields.py"
"$E3B_PYTHON" "$E3B_ROOT/code/visualize.py"
"$E3B_PYTHON" "$E3B_ROOT/code/delivery.py"
```

本次实际运行003完成主检查，随后以`validate_local_fields.py --supplement-only`补充独有Raw面和原始法向/Ring控制；无参数变化。Fig3单独修正同阶段重叠显示。执行索引与代码冻结保存初始和最终状态。初始化器检查父SHA，已提交交付只运行`delivery.py`复核；完整重放应另建隔离目录，不删除父SHA或历史快照检查。

可直接使用场（原始资产存在时，无需本地缓存）：

```python
from projective_local_field import ProjectiveLocalField
from mesh_local_field import MeshLocalField
# source_id来自HERO_NATIVE_INPUT_MANIFEST，不允许任意融合路径
a = ProjectiveLocalField("G01_005_raw00745")
b = MeshLocalField("G01_005_raw00745")
qa, qb = a.query([[0., 0., 1.]]), b.query([[0., 0., 1.]])
# 按valid_surface/free、cad_occluded、unknown及field_kind解释；Unknown值NaN
```

坐标是该视频Ring局部毫米，t_hit为轴向Z；原生K通过现有半像素函数换算，无新相机模型。活动value与raw_udf_mm/raw_projective_delta_mm诊断分开。主域标签0 Surface /1条件Free /2 CAD /3 Unknown /4 Ambiguous；reason_codes为位掩码，字典见provenance/QUERY_REASON_CODES.json。竞争只检查32个最近原面重心候选，有向符号条件性，不能作全局物体内外。

LOCAL_FIELD_MANIFEST保存可重建对象的工厂、输入SHA、冻结ROI/协议，而非训练权重。local_results仅存本机查询证据缓存，不是融合Mesh或神经预测；缺缓存仍可从原资产查询。68基础控制+51符号/Ring控制、34资格表、34域表、17来源增量全保留。全部原面/UDF、独有区域保护与来源祖先必须同时复核，不能用B0数值零值代替Raw Mesh等价。
