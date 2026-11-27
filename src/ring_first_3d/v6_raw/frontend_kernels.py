"""Checked in-memory adapters of the actual external V5/V6 kernels.

Never writes external sources. Original functions remain the stage implementations.
"""
import ast, hashlib, inspect, json
from pathlib import Path
import numpy as np
from .frontend_policy import finite_le,region_scale,view_tag,match_partners

RECEIPTS={}
def corrected_observation(labels, original):
 from ..mainline.native.camera import observe,sample
 native=observe(labels,ring_mode='all');points=sample(native['ring_boundary_all'],320)
 held=np.arange(len(points))%5==0;out=dict(original)
 out.update(ring_train=points[~held],ring_heldout=points[held],ring_boundary_contact_polyp=native['ring_boundary_contact_polyp'])
 d=dict(old_contour_count=len(original['ring_train'])+len(original['ring_heldout']),new_contour_count=len(points),raw_boundary_count=len(native['ring_boundary_all']),contact_polyp_count=native['ring_boundary_contact_polyp_count'],excluded_for_polyp_adjacency=0,image_border_ring_pixels=int((labels[0]==2).sum()+(labels[-1]==2).sum()+(labels[:,0]==2).sum()+(labels[:,-1]==2).sum()),boundary_source='real label transitions inside image; no virtual image-border closure; no filled/CAD ellipse samples',independent_occlusion_exclusions=0,independent_occlusion_evidence='none supplied; adjacency alone is not exclusion')
 return out,d

class Tags(ast.NodeTransformer):
 def visit_Call(self,node):
  self.generic_visit(node)
  if isinstance(node.func,ast.Name) and node.func.id=='next' and len(node.args)==1 and isinstance(node.args[0],ast.GeneratorExp):
   names={x.id for x in ast.walk(node.args[0]) if isinstance(x,ast.Name)}
   for key in ['_M2F9_REFERENCE_INDEX','_M2F9_HELDOUT_INDEX']:
    if key in names:return ast.copy_location(ast.Name(id=key,ctx=ast.Load()),node)
  return node
 def visit_FormattedValue(self,node):
  self.generic_visit(node)
  v=node.value
  if isinstance(v,ast.Subscript) and isinstance(v.slice,ast.Constant) and v.slice.value=='raw_frame':
   node.value=ast.Call(func=ast.Name(id='_FRONTEND_VIEW_TAG',ctx=ast.Load()),args=[v.value],keywords=[]);node.format_spec=None
  return node

class SafeValidation(Tags):
 def visit_Compare(self,node):
  self.generic_visit(node)
  if len(node.ops)==1 and isinstance(node.ops[0],ast.LtE):
   return ast.Call(func=ast.Name(id='_FRONTEND_FINITE_LE',ctx=ast.Load()),args=[node.left,node.comparators[0]],keywords=[])
  return node
 def visit_FunctionDef(self,node):
  self.generic_visit(node)
  if node.name!='main':return node
  for loop in node.body:
   if isinstance(loop,ast.For) and ast.unparse(loop.target)=='(v, pk)':
    insert=ast.parse("point_categories=tr['category'][pk['point_track_ids']]; Pp=pk['points'][point_categories==1]; P=np.median(Pp,0) if len(Pp)>=5 else np.zeros(3)").body
    loop.body=insert+loop.body
  # Original preview selector must use the primary candidate's own coverage center.
  for i,n in enumerate(node.body):
   if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='directions' for t in n.targets):
    node.body[i:i]=ast.parse("P=np.asarray(next(x['P_estimate_mm'] for x in span if x['version']==primary))").body;break
  return node

def patch_function(module,name,transform):
 path=Path(module.__file__);tree=ast.parse(path.read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
 tree=ast.Module(body=[fn],type_ignores=[]);tree=transform(tree);ast.fix_missing_locations(tree)
 compiled=ast.unparse(tree);exec(compile(tree,str(path),'exec'),module.__dict__)
 RECEIPTS[f'{module.__name__}.{name}']=dict(module_file=str(path),function_source_location=f'{path}:{fn.lineno}',disk_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),adapted_ast_sha256=hashlib.sha256(ast.dump(tree).encode()).hexdigest(),adapted_source=compiled)

def residual_transform(tree):
 class Weight(ast.NodeTransformer):
  def visit_Call(self,node):
   self.generic_visit(node)
   if ast.unparse(node.func)=='np.sqrt' and isinstance(node.args[0],ast.BinOp) and ast.unparse(node.args[0].left)=='len(q)':
    denominator=node.args[0].right
    return ast.Call(func=ast.Name(id='_FRONTEND_REGION_SCALE',ctx=ast.Load()),args=[ast.parse('len(q)',mode='eval').body,denominator],keywords=[])
   return node
 return Weight().visit(tree)

def solver_transform(tree):
 class Solver(ast.NodeTransformer):
  def visit_Call(self,node):
   self.generic_visit(node)
   if ast.unparse(node)=='np.diff(full)':return ast.parse('_FRONTEND_TIME_DIFF(full)',mode='eval').body
   return node
  def visit_BinOp(self,node):
   self.generic_visit(node)
   if ast.unparse(node)=='6 * (n - 1)':return ast.parse('6 * len(_FRONTEND_TEMPORAL)',mode='eval').body
   return node
  def visit_For(self,node):
   self.generic_visit(node)
   if ast.unparse(node.iter)=='range(n - 1)' and ast.unparse(node.target)=='i':
    node.iter=ast.Name(id='_FRONTEND_TEMPORAL',ctx=ast.Load());node.target=ast.Tuple(elts=[ast.Name(id='i',ctx=ast.Store()),ast.Name(id='_temporal_j',ctx=ast.Store())],ctx=ast.Store())
    class Index(ast.NodeTransformer):
     def visit_BinOp(self,x):
      if ast.unparse(x)=='i + 1':return ast.Name(id='_temporal_j',ctx=ast.Load())
      return self.generic_visit(x)
    node.body=[Index().visit(x) for x in node.body]
   return node
  def visit_FunctionDef(self,node):
   self.generic_visit(node)
   if node.name=='triangulate_training':
    for loop in node.body:
     if isinstance(loop,ast.For) and ast.unparse(loop.target)=='t':
      for k,n in enumerate(loop.body):
       if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='frames' for t in n.targets):
        loop.body[k+1:k+1]=ast.parse('if len(frames)<2: continue').body;break
   return node
 return Solver().visit(tree)

def track_transform(tree):
 class Track(ast.NodeTransformer):
  def visit_For(self,node):
   self.generic_visit(node)
   if ast.unparse(node.target)=='skip' and ast.unparse(node.iter)=="cfg()['pair_offsets']":
    assert ast.unparse(node.body[0])=='j = i + skip'
    node.target=ast.Name(id='j',ctx=ast.Store());node.iter=ast.parse("_FRONTEND_MATCH_PARTNERS(i,L,cfg()['pair_offsets'])",mode='eval').body;node.body=node.body[1:]
   return node
  def visit_keyword(self,node):
   self.generic_visit(node)
   if node.arg=='frame_raw':node.value=ast.parse("[a['raw_frame'] if a['raw_frame'] is not None else -1 for a in L]",mode='eval').body
   return node
 return Track().visit(tree)

def package_transform(tree):
 class Package(ast.NodeTransformer):
  def visit_Assign(self,node):
   self.generic_visit(node)
   if any(isinstance(t,ast.Name) and t.id=='ts' for t in node.targets):
    node.value=ast.IfExp(test=ast.parse('held>=0',mode='eval').body,body=node.value,orelse=ast.parse('np.array([],dtype=int)',mode='eval').body)
   return node
  def visit_keyword(self,node):
   self.generic_visit(node)
   if node.arg=='heldout_frame' and isinstance(node.value,ast.Subscript):
    node.value=ast.IfExp(test=ast.parse('held>=0',mode='eval').body,body=node.value,orelse=ast.Constant(value=None))
   return node
  def visit_Call(self,node):
   self.generic_visit(node)
   if isinstance(node.func,ast.Name) and node.func.id=='dict' and any(k.arg=='heldout_feature_count' for k in node.keywords):
    node.keywords.append(ast.keyword(arg='heldout_evaluation_status',value=ast.parse("'CONDITIONAL_DIAGNOSTIC' if held>=0 else 'NOT_EVALUABLE_ORIGINAL_B_OUTSIDE_COMPONENT'",mode='eval').body))
   return node
 return Package().visit(tree)

def install(adapter):
 original_modules=adapter.source_modules
 def modules(radius):
  mods=original_modules(radius);g5=mods['g5'];lba=mods['lba'];track=mods['track'];v6=mods['v6']
  g5._FRONTEND_REGION_SCALE=region_scale;patch_function(g5,'torus_residual',residual_transform)
  v6.ring_residual=g5.torus_residual;lba.ring_residual=g5.torus_residual
  for name in ['initialize','triangulate_training','BA']:patch_function(lba,name,solver_transform)
  lba._FRONTEND_TEMPORAL=[]
  lba._FRONTEND_TIME_DIFF=lambda x:np.asarray([x[j]-x[i] for i,j in lba._FRONTEND_TEMPORAL])
  track._FRONTEND_MATCH_PARTNERS=match_partners;patch_function(track,'main',track_transform)
  import ring_observations
  if not hasattr(ring_observations,'_frontend_original'):ring_observations._frontend_original=ring_observations.ns['adapt']
  def adapt(image,labels,source):
   ob,status=ring_observations._frontend_original(image,labels,source);ob,receipt=corrected_observation(labels,ob)
   status.update(frontend_correction=receipt,background_facing_contour_candidates=receipt['new_contour_count'],occlusion_policy='real all Ring mask boundaries; adjacency diagnostic only')
   return ob,status
  ring_observations.ns['adapt']=adapt
  RECEIPTS['ring_observations.adapt']=dict(module_file=ring_observations.__file__,original_adapter_function_file=inspect.getsourcefile(ring_observations._frontend_original),adapter_file=__file__,adapter_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
  return mods
 adapter.source_modules=modules
 original_lookups=adapter.adapt_reference_lookups
 def lookups(source,*args,**kwargs):
  tree,receipt=original_lookups(source,*args,**kwargs)
  if Path(source).name=='validate_select.py':tree=SafeValidation().visit(tree)
  else:tree=Tags().visit(tree)
  ast.fix_missing_locations(tree);receipt['frontend_ast_sha256']=hashlib.sha256(ast.dump(tree).encode()).hexdigest()
  RECEIPTS[str(source)]=dict(module_file=str(source),disk_sha256=hashlib.sha256(Path(source).read_bytes()).hexdigest(),adapted_ast_sha256=receipt['frontend_ast_sha256'])
  return tree,receipt
 adapter.adapt_reference_lookups=lookups
 original_invoke=adapter.invoke_adapted_v6
 def invoke(module,*args,**kwargs):
  module._FRONTEND_FINITE_LE=finite_le;module._FRONTEND_VIEW_TAG=view_tag
  return original_invoke(module,*args,**kwargs)
 adapter.invoke_adapted_v6=invoke
 original_package=adapter.adapt_independent_package
 def package(source):
  tree,receipt=original_package(source);tree=package_transform(tree);ast.fix_missing_locations(tree)
  receipt.update(missing_original_diagnostic_never_substituted=True,frontend_ast_sha256=hashlib.sha256(ast.dump(tree).encode()).hexdigest())
  return tree,receipt
 adapter.adapt_independent_package=package
 return adapter
