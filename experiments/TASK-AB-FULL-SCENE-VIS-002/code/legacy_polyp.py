"""Exact AST reuse of prior polyp-only metric kernel; never changes old outputs."""
from common import *
import ast
from functools import lru_cache
sys.path.insert(0,str(VENDOR));import open3d as o3d
_path=AUDIT/'code/reprojection.py'
_nodes=[n for n in ast.parse(_path.read_text()).body if isinstance(n,ast.FunctionDef)and n.name in ['cad_scene','render','evaluate']]
assert len(_nodes)==3
exec(compile(ast.Module(body=_nodes,type_ignores=[]),str(_path),'exec'),globals())
