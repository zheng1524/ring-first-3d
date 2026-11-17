from safe_geometry import *
def main():
 ring=np.load(R/'inputs/G01/RING.npz');rv,rf=ring['V'],ring['F'];rs=scene(rv,rf)
 V=np.array([[0,0,0],[20,2,0],[20,-2,0]],float);F=np.array([[0,1,2]]);e=np.array([[0,1],[1,2],[0,2]]);sparse=rs.compute_signed_distance(o3d.core.Tensor(points(V,F,e).astype(np.float32))).numpy();dense=dense_face_distance(rs,V,F,rv,32);cm=trimesh.collision.CollisionManager();cm.add_object('Ring',trimesh.Trimesh(rv,rf,process=False));fcl=cm.in_collision_single(trimesh.Trimesh(V,F,process=False));assert sparse.min()>0 and dense.min()<-.1 and fcl
 rows=[dict(test='triangle-interior material penetration missed by old vertices/midpoints/centroid',old_min_mm=float(sparse.min()),new_dense_min_mm=float(dense.min()),FCL=fcl,PASS=True)]
 V2=np.r_[np.array([[0,0,0],[2,0,0],[0,2,0]]),np.array([[.5,.5,-1],[.5,.5,1],[1,.5,0]])];F2=np.array([[0,1,2],[3,4,5]]);si=self_intersections(V2,F2);assert si['intersections']==1;rows.append(dict(test='nonadjacent crossing triangles',Open3D_intersections=si['intersections'],PASS=True))
 V2[3:]+=10;si=self_intersections(V2,F2);assert si['intersections']==0;rows.append(dict(test='separated triangles',PASS=True))
 table('metrics/GEOMETRY_PREFLIGHT.csv',rows);save('provenance/GEOMETRY_PREFLIGHT.json',dict(epoch=time.time(),code=asset(Path(__file__)),guard=asset(R/'code/safe_geometry.py'),checks=rows,mesh_writes_to_history=0));print(rows)
if __name__=='__main__':main()
