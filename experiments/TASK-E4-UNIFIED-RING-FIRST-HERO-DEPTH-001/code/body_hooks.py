"""Only the accepted collision interface and frozen 018 depth IO are adapted."""
import ast
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import torch
from pytorch3d.structures import Meshes
from pytorch3d.utils import cameras_from_opencv_projection
from pytorch3d.renderer import MeshRasterizer,RasterizationSettings
from pytorch3d.ops import interpolate_face_attributes
from ring_first_3d.mainline.paths import LINEAGE
from ring_first_3d.mainline.native.io import save_json

REC=LINEAGE/'experiments/TASK-E4-G01-G03-GROWTH-RECOVERY-001/code/ring_gate.py'
s=importlib.util.spec_from_file_location('accepted_current_ring_gate',REC);g=importlib.util.module_from_spec(s);s.loader.exec_module(g)
class RingGateAdapter(g.CurrentRingGate):
    def check(self,body,current,sweep=None):return super().check(body,current)

def historical_depth(case,chart,io_root,out):
    source=LINEAGE/'experiments/TASK-E4-HERO-BODY-ADAPT-018/code/hero_objective018.py'
    def tensor(x,dtype=torch.float32):return torch.as_tensor(x,dtype=dtype,device='cuda:0')
    ns=dict(np=np,torch=torch,ROOT=Path(io_root),Path=Path,tensor=tensor,MeshRasterizer=MeshRasterizer,RasterizationSettings=RasterizationSettings,cameras_from_opencv_projection=cameras_from_opencv_projection,interpolate_face_attributes=interpolate_face_attributes,load=lambda p:__import__('json').loads(Path(p).read_text()),sha=__import__('ring_first_3d.mainline.native.io',fromlist=['sha256']).sha256,save=lambda p,x:save_json(Path(out)/Path(p).name,x))
    nodes=[n for n in ast.parse(source.read_text()).body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in ['huber018','HeroDepth018']]
    assert len(nodes)==2
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(source),'exec'),ns)
    return ns['HeroDepth018'](case,SimpleNamespace(D=chart['D_mm']),'TRUSTED')

def mesh(V,F,case):
    return Meshes(verts=[((V-torch.as_tensor(case.center,device=V.device,dtype=V.dtype))/case.scale).float()],faces=[torch.as_tensor(F,dtype=torch.int64,device=V.device)])
