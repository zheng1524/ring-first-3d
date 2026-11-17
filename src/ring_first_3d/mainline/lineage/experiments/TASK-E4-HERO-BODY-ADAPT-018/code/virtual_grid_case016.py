"""Virtual-only direct Blender renderer-grid target, preserving native Mask/cameras."""
from p3d import *
class RenderGridCase(Case):
 def __init__(self,name):
  super().__init__(name)
  assert name=='virtual_Ip','This is a declared virtual sensor-grid adapter, never real data'
  for cid,d in self.views.items():
   a=np.load(R/'inputs'/name/(cid+'_RENDER_TARGET.npz'));assert a['target'].shape==self.size;d['target']=tensor(a['target'])
