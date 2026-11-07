from common import *

def main():
 for c in load(R/'config/CASE_LOCK.json'):
  n=c['name'];out=R/'review_models'/n;out.mkdir(parents=True,exist_ok=True);rr=np.load(R/'inputs'/n/'RING.npz');ring=trimesh.Trimesh(rr['V'],rr['F'],process=False);ring.visual.face_colors=np.tile([5,5,5,255],(len(rr['F']),1));ring.export(out/'RING_CAD_mm.ply');entries=[]
  for tag,path,color in [('C011',R/'inputs'/n/'C_011.npz',[45,155,205,255]),('FINAL011',R/'inputs'/n/'INITIAL.npz',[222,169,55,255]),('FINAL012',R/'local_results'/n/'FINAL.npz',[179,90,165,255])]:
   z=np.load(path);m=trimesh.Trimesh(z['V'],z['F_solid'],process=False);col=np.tile(color,(len(z['F_solid']),1));col[z['inferred_base_faces']]=[155,155,155,255];m.visual.face_colors=col;m.export(out/(tag+'_mm.ply'));entries.append(dict(label=tag,source=asset(path),inferred_base_face_IDs=np.flatnonzero(z['inferred_base_faces']),observation_eligible_face_N=len(z['F']),V_N=len(z['V']),F_solid_N=len(z['F_solid']),PLY_units='mm',PLY_export_float_precision='review copy; exact original NPZ remains indexed'))
   if tag=='FINAL012':
    body=m.copy();body.vertices=np.array(body.vertices)*.001;rm=ring.copy();rm.vertices=np.array(rm.vertices)*.001;sc=trimesh.Scene();sc.add_geometry(body,node_name='Polyp_FINAL012',geom_name='Polyp_FINAL012');sc.add_geometry(rm,node_name='Ring_CAD',geom_name='Ring_CAD');sc.export(out/'FINAL012_with_Ring_m.glb');loaded=trimesh.load(out/'FINAL012_with_Ring_m.glb',force='scene');expected=np.array([np.r_[z['V'],rr['V']].min(0),np.r_[z['V'],rr['V']].max(0)])*.001;assert np.allclose(loaded.bounds,expected,rtol=1e-5,atol=1e-8)
  save('review_models/'+n+'/MODEL_SEMANTICS.json',dict(case=n,stage_models=entries,Ring_frozen=True,GLB_units='metres, exact display-format conversion mm*0.001 only; no additional scientific scale recovery',GLB_bounds_verified=True,GLB_role='interactive review only; possible face-color vertex duplication is not used for topology or metrics',gray_faces='inferred basal closure, not an observed Polyp surface',predictions_changed=False))
 (R/'review_models/README.md').write_text('''# 审阅模型

九例各自目录包含011 C、011 FINAL、012 FINAL与独立黑色Ring CAD的PLY，坐标单位为毫米。灰色面是推断底盖，面ID与精确NPZ来源见MODEL_SEMANTICS.json，不是可见息肉GT。

FINAL012_with_Ring_m.glb用于交互旋转审阅。glTF标准单位是米，因此仅做mm×0.001的格式转换，Ring内径10mm对应0.010m；不是重新估计尺度。GLB可能为面颜色拆分顶点，拓扑、几何指标与测量使用本地原始NPZ，不以平滑外观冒充改进。所有GLB已重新载入核验几何包围范围。

这些都是冻结结果的轻量副本，没有删面、补洞、平滑、非刚性配准或GT形状回填。精确NPZ、PT恢复状态和全部中间Mesh路径/SHA见LOCAL_RESULTS_INDEX。
''')
 with(R/'review_models/README.md').open('a')as f:
  f.write('\n|病例|011 C|011 FINAL|012 FINAL|012带Ring交互模型|面身份|\n|---|---|---|---|---|---|\n')
  for n in load(R/'config/PROTOCOL.json')['cases']:f.write(f'|{n}|[PLY]({n}/C011_mm.ply)|[PLY]({n}/FINAL011_mm.ply)|[PLY]({n}/FINAL012_mm.ply)|[GLB]({n}/FINAL012_with_Ring_m.glb)|[语义]({n}/MODEL_SEMANTICS.json)|\n')
 print('NINE_REVIEW_MODEL_PACKAGES_EXPORTED')

if __name__=='__main__':main()
