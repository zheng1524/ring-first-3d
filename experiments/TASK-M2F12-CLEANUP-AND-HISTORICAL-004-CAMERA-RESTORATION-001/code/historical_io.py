"""M2F12 input isolation and source loading; no scientific stage reimplementation."""
import ast,hashlib,types,sys,json,os
from pathlib import Path
E=Path('/home/liu/polyp_research/ring_anchor_3d/experiments')
H=Path('/home/liu/polyp_research/ring-first-3d/experiments')
W=Path('/home/liu/ring_first_3d_workspace')
SOURCES={
 'common':E/'ring_first_v5_real_validation/scripts/common.py',
 'adapter':E/'ring_first_v4_synthetic_audit/scripts/adapter.py',
 'track_scene':E/'ring_first_v3_static_ba/scripts/track_scene.py',
 'visual_initialize':E/'ring_first_v5_real_validation/scripts/visual_initialize.py',
 'geometry_safe':E/'ring_first_v5_real_validation/scripts/geometry_safe.py',
 'ring_candidates':E/'ring_first_v5_real_validation/scripts/ring_candidates.py',
 'ba_safe':E/'ring_first_v5_real_validation/scripts/ba_safe.py',
 'run_real':E/'ring_first_v5_real_validation/scripts/run_real.py',
 'evaluate_real':E/'ring_first_v5_real_validation/scripts/evaluate_real.py',
 'features019':H/'TASK-E4-RING-POLYP-REGISTRATION-019/code/features019.py',
 'common019':H/'TASK-E4-RING-POLYP-REGISTRATION-019/code/common.py',
}

def sha(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()

def permitted(path,run,files,library_roots):
 p=Path(path).resolve();r=Path(run).resolve()
 if p==r or r in p.parents or str(p) in files:return True
 if any(p==Path(x) or Path(x) in p.parents for x in library_roots):return True
 return False

def adapt_constants(tree,major):
 if major==5.6:return tree
 class Physical(ast.NodeTransformer):
  def visit_Constant(self,n):
   if type(n.value)==float and n.value in (5.6,6.2):
    return ast.copy_location(ast.Constant(major if n.value==5.6 else major+.6),n)
   return n
 return ast.fix_missing_locations(Physical().visit(tree))

def load(name,run,major=5.6,alias=None):
 p=SOURCES[name];key=alias or name;m=types.ModuleType(key);m.__file__=str(p);sys.modules[key]=m
 tree=ast.parse(p.read_text())
 if name in ['geometry_safe','ring_candidates','ba_safe']:tree=adapt_constants(tree,major)
 if name=='adapter' and major!=5.6:
  # Only the physical inner diameter passed to the existing DXY FrameInput.
  for n in ast.walk(tree):
   if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='FrameInput':n.args[2]=ast.Constant(2*(major-.6))
 exec(compile(ast.fix_missing_locations(tree),str(p),'exec'),m.__dict__)
 m.R=Path(run);return m

def common(run):
 m=load('common',run);m.PROJECT=Path('/home/liu/polyp_research');m.DXY=Path('/home/liu/new-polyp-dxy')
 return m

def firewall(run,files,extra_roots=()):
 run=Path(run).resolve();events={}
 libs=['/usr','/lib','/lib64','/proc','/sys','/dev',str(Path(sys.prefix)),
 '/home/liu/miniconda3',str(E/'surface_fusion_v3/vendor'),str(E/'ring_depth_v3/vendor'),*extra_roots]
 allowed=set(map(str,files))
 def audit(event,args):
  if event!='open' or not isinstance(args[0],(str,bytes)):return
  p=Path(os.fsdecode(args[0])).resolve();mode=args[1]if isinstance(args[1],str)else'';flags=args[2]if isinstance(args[2],int)else 0
  writing=any(c in mode for c in 'wax+') or flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC)
  if writing:
   if str(p).startswith('/home/liu/') and not permitted(p,run,[],[]):raise PermissionError('WRITE_OUTSIDE_RUN:'+str(p))
   return
  # Source imports are allowed; scientific assets are exact allowlisted.
  if str(p).startswith('/home/liu/') and p.suffix not in ['.py','.pyc','.so','.pyd','.pth'] and not permitted(p,run,allowed,libs):
   events[str(p)]='DENIED';raise PermissionError('OLD_OR_UNREGISTERED_INPUT:'+str(p))
  if str(p).startswith('/home/liu/') and p.suffix in ['.npz','.json','.png','.jpg','.mp4','.ckpt','.safetensors']:events[str(p)]='READ'
 sys.addaudithook(audit);return events
