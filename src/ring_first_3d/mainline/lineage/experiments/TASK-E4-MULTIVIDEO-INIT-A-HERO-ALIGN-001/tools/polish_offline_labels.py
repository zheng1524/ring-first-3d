"""Clarify offline figure labels; immutable prediction and Runner snapshots untouched."""
from pathlib import Path
import re
vis=Path.cwd()/'experiments/TASK-E4-MULTIVIDEO-INIT-A-HERO-ALIGN-001/visualization'
for folder in vis.iterdir():
 p=folder/'multisurface_3d.html'
 if not p.is_file():continue
 s=p.read_text()
 if folder.name.endswith('_HERO'):
  s=s.replace('<option value="fusion">整体融合</option>','').replace('<option value="evaluation">GT评价</option>','').replace('<option>0</option>','').replace('<option>1</option>','')
  s=s.replace('紫融合、灰Body、黑GT','灰色冻结Body；本页没有GT或融合层').replace('no independent GT; no fused surface. ','no independent GT; no fused surface. ').replace('Camera files frozen; only surface rigid corrections applied. Mesh ownership conflicts and missing sections are retained.','Cameras and actual Init-A Body frozen; only full-source rigid surface corrections. No fused surface is drawn.')
 else:
  s=re.sub(r'(<h1>.*?</h1>)<p>.*?</p>',r'\1<p>紫色为实际预测Mesh，灰色半透明为独立Blender GT。每个预测都使用已保存的真正尺度1 SE(3)评价副本；原公制世界模型不变。这里没有HERO、融合层或部署定位精度声明。</p>',s,count=1)
  s=s.replace('>Body灰色','>预测主体紫色').replace('>GT黑色网格线','>GT灰色半透明').replace("'\\nComplete independent surfaces shown: '+shown+'/16\\n'", "'\\nActual stored rigid-aligned prediction and independent GT\\n'")
  for cid in ['condition','method','tol','stage']:
   s=re.sub(r'<label>([^<]*)<select id="'+cid+'"',r'<label style="display:none">\1<select id="'+cid+'"',s)
 # Keep dormant inputs for the inherited viewer's draw callbacks, but don't offer irrelevant actions.
 s=s.replace('<label><input id="showfused"','<label style="display:none"><input id="showfused"')
 p.write_text(s)
print('Updated only offline display labels; all scientific Mesh data unchanged')
