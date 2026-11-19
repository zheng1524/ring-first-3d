"""SHA-checked selective AST reuse of T05-T09; no historical IO/main imports."""
import ast,json,hashlib,subprocess,time,types
from functools import lru_cache
from pathlib import Path
import numpy as np,cv2
from scipy.spatial.transform import Rotation
from scipy.ndimage import map_coordinates
from scipy.special import expit
from scipy.optimize import least_squares
from ..policy.contracts import ROOT,require
from .geometry import camera_rays,cast,contour


def namespace(task):
    lock=json.loads(Path(task['sim']['assets']['reuse_lock']['path']).read_text());receipts=[]
    ns=dict(np=np,cv2=cv2,Rotation=Rotation,map_coordinates=map_coordinates,expit=expit,least_squares=least_squares,
      time=time,lru_cache=lru_cache,vis=types.SimpleNamespace(camera_rays=camera_rays),contour=contour,
      cast=lambda s,uv,K,T:(cast(s,uv,K,T)[0],None))
    def compile_named(key,names,cls=None):
        rec=lock['sources'][key]
        # Ordinary local workspace: exact source bytes are retained independently
        # of Git. The original scientific SHA check remains mandatory.
        raw=(ROOT/'src/ring_first_3d/mainline/frozen_registry'/rec['path']).read_bytes()
        require(hashlib.sha256(raw).hexdigest()==rec['sha256'],'SOURCE_SHA',key)
        tree=ast.parse(raw);nodes=tree.body if cls is None else next(n for n in tree.body if isinstance(n,ast.ClassDef)and n.name==cls).body
        nodes=[n for n in nodes if isinstance(n,ast.FunctionDef)and n.name in names]
        require({n.name for n in nodes}==set(names),'SOURCE_CONTRACT',key)
        exec(compile(ast.Module(body=nodes,type_ignores=[]),rec['path'],'exec'),ns)
        for n in nodes:receipts.append(dict(source=rec,name=(cls+'.'if cls else'')+n.name,AST_sha256=hashlib.sha256(ast.dump(n,include_attributes=False).encode()).hexdigest(),mathematics_modified=False))
    compile_named('models',['decode','sphere_mesh'])
    compile_named('common',['mesh','ray_components','first_depth'])
    compile_named('losses',['robust','ellipse_projection','signed_distance','field_sample','distance_field_sample','target_data','cad_visibility','two_d_parts'])
    compile_named('solver',['solve'],cls='Problem')
    ns['reuse_receipts']=receipts;return ns
