"""One low-priority CPU process; never alter upstream processes or runtime state."""
import os,sys,runpy
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
import cv2
cv2.setNumThreads(1)
from threadpoolctl import threadpool_limits
threadpool_limits(1)
# The reused ray helpers request two threads; intercept only the runtime query
# boundary to enforce the user's one-thread budget without changing geometry.
import open3d as o3d
Original=o3d.t.geometry.RaycastingScene
class OneThreadScene:
 def __init__(self,*a,**k):k['nthreads']=1;self.inner=Original(*a,**k)
 def __getattr__(self,name):
  value=getattr(self.inner,name)
  if name in ['cast_rays','compute_closest_points','compute_distance','compute_signed_distance','count_intersections','test_occlusions']:
   def call(*a,**k):k['nthreads']=1;return value(*a,**k)
   return call
  return value
o3d.t.geometry.RaycastingScene=OneThreadScene
args=sys.argv[1:]
if args[0]=='-':sys.argv=['-']+args[1:];exec(compile(sys.stdin.read(),'<stdin>','exec'),{'__name__':'__main__'})
elif args[0]=='-m':sys.argv=args[1:];runpy.run_module(args[1],run_name='__main__',alter_sys=True)
else:sys.argv=args;runpy.run_path(args[0],run_name='__main__')
