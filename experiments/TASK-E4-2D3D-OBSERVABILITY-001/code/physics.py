from model import *
sys.path.insert(0,'/home/liu/ring_first_3d_e4_pmgr_r1/experiments/TASK-E4-PMGR-R1/runtime/packages')
import fcl
def obj(V,F):
    m=fcl.BVHModel();m.beginModel(len(V),len(F));m.addSubModel(np.asarray(V,float),np.asarray(F,np.int32));m.endModel();return fcl.CollisionObject(m)
def physical(V,F):
    c=np.load(R/'inputs/RING_CAD.npz');a=obj(V,F);b=obj(c['V'],c['F']);n=fcl.collide(a,b,fcl.CollisionRequest(),fcl.CollisionResult());gap=fcl.distance(a,b,fcl.DistanceRequest(),fcl.DistanceResult())if not n else-1
    return dict(collision=bool(n),triangle_gap_mm=float(gap),quality=normals_quality(V,F),self_intersection='NOT_CERTIFIED_by_FCL_Ring_query')
