import os,sys,runpy
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
import cv2
cv2.setNumThreads(1)
import open3d as o3d
original=o3d.t.geometry.RaycastingScene
class SingleThreadScene(original):
 def __init__(self,*a,**kw):kw['nthreads']=1;super().__init__(*a,**kw)
 def cast_rays(self,*a,**kw):kw['nthreads']=1;return super().cast_rays(*a,**kw)
 def compute_distance(self,*a,**kw):kw['nthreads']=1;return super().compute_distance(*a,**kw)
o3d.t.geometry.RaycastingScene=SingleThreadScene
script=sys.argv.pop(1);sys.argv[0]=script;runpy.run_path(script,run_name='__main__')
