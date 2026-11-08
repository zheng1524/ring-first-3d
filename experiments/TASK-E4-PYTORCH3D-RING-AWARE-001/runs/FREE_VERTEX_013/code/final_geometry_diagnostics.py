from common import *
def main():
 rows=[];base={}
 for c in load(R/'config/CASE_LOCK.json'):
  n=c['name'];z=np.load(R/'inputs'/n/'INITIAL.npz');m=trimesh.Trimesh(z['V'],z['F'],process=False);base[n]=(z['V'],z['F'],m.edges_unique)
  for stage,p in [('013',R/'local_results'/n/'FINAL.npz'),('012',R/'local_results/metric'/n/'FINAL012.npz')]:
   a=np.load(p);V0,F,edges=base[n];V=a['V'];l0=np.linalg.norm(V0[edges[:,0]]-V0[edges[:,1]],axis=1);l=np.linalg.norm(V[edges[:,0]]-V[edges[:,1]],axis=1);disp=np.linalg.norm(V-V0,axis=1);ratio=l/np.maximum(l0,1e-12);face_disp=disp[F].max(1);rows.append(dict(case=n,stage=stage,vertex_N=len(V),observed_face_N=len(F),moved_vertex_over0p1mm_N=int((disp>.1).sum()),moved_vertex_over1mm_N=int((disp>1).sum()),moved_faces_over1mm_N=int((face_disp>1).sum()),edge_stretch=stats(ratio),max_edge_stretch=float(ratio.max()),min_edge_stretch=float(ratio.min()),edges_over2x_N=int((ratio>2).sum()),edges_over5x_N=int((ratio>5).sum()),topology_faces_unchanged=bool(np.array_equal(a['F'],F)),no_resolution_or_topology_control_run=True))
 save('metrics/EDGE_STRETCH_AND_RESOLUTION.json',rows);table('metrics/EDGE_STRETCH_AND_RESOLUTION.csv',rows)
 # Preserve all rejected-loss replays, separate from optimizer input.
 replays=[]
 for p in (R/'arms').glob('*/metrics/G03_REJECTED_LOSS_BREAKDOWN.json'):replays+=load(p)
 save('metrics/G03_REJECTED_LOSS_BREAKDOWN.json',replays);table('metrics/G03_REJECTED_LOSS_BREAKDOWN.csv',replays)
 receipt=[asset(p)for p in sorted((R/'local_results').rglob('*'))if p.is_file()and p.suffix in ['.pt','.npz','.ply']];save('assets_index/LOCAL_RESULT_INDEX.json',dict(files=receipt,large_files_local=True))
if __name__=='__main__':main()
