"""Read-only Blender generator: exact historical evaluated-world mesh extraction."""
import bpy
import sys,json,hashlib,ast
from pathlib import Path
import numpy as np

request=json.loads(Path(sys.argv[sys.argv.index('--')+1]).read_text())
assets=request['assets'];source=Path(assets['blend']['path'])
assert hashlib.sha256(source.read_bytes()).hexdigest()==assets['blend']['sha256']
bpy.ops.wm.open_mainfile(filepath=str(source))
assert bpy.context.scene.unit_settings.system=='METRIC' and bpy.context.scene.unit_settings.scale_length==1.
deps=bpy.context.evaluated_depsgraph_get();verts=[];faces=[];offset=0;records=[]
# Original export_blender_gt.py mathematical statements, hash-verified AST;
# only original I/O/main enumeration is excluded.
raw=Path(assets['export_source']['path']).read_bytes()
assert hashlib.sha256(raw).hexdigest()==assets['export_source']['sha256']
tree=ast.parse(raw)
loop=next(n for n in ast.walk(tree)if isinstance(n,ast.For)and ast.unparse(n.target)=='name')
c=dict(body_objects=request['body_objects'],unit_to_mm=request['unit_to_mm'])
exec(compile(ast.Module(body=[loop],type_ignores=[]),'historical_g01_export_AST','exec'))
out=Path(request['output']);np.savez_compressed(out/'g01_mesh.npz',V=np.concatenate(verts),F=np.concatenate(faces))
(out/'extraction.json').write_text(json.dumps(dict(Blender=bpy.app.version_string,unit_to_mm=request['unit_to_mm'],records=records,geometry_modified=False),ensure_ascii=False,indent=2))
