"""Record old geometry before any separately authorized release; never modify it."""
from pathlib import Path
import csv,gzip,json,hashlib,time
import numpy as np,trimesh
WT=Path(__file__).resolve().parents[1];T=WT/'experiments/TASK-V6-R1-STORAGE-REAUDIT-001'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(2**20),b''):h.update(b)
 return h.hexdigest()

def join_inventory(metrics):
 bypath={x['path']:x['status'] for x in metrics}
 for name in ['FILE_AUDIT.csv.gz','PROPOSED_FILES.csv.gz']:
  path=T/name
  with gzip.open(path,'rt',encoding='utf-8') as f:
   reader=csv.DictReader(f);fields=reader.fieldnames;records=list(reader)
  for x in records:
   if x['path'] in bypath:x['metric_status']=bypath[x['path']]
  tmp=path.with_name(path.name+'.tmp')
  with gzip.open(tmp,'wt',encoding='utf-8',newline='') as f:
   writer=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');writer.writeheader();writer.writerows(records)
  tmp.replace(path)

def main():
 with gzip.open(T/'PROPOSED_FILES.csv.gz','rt') as f:files=[x for x in csv.DictReader(f) if Path(x['path']).suffix.lower() in {'.ply','.obj','.stl','.off','.glb','.gltf'}]
 byhash={};rows=[]
 for i,x in enumerate(files):
  p=Path(x['path']);h=x['sha256'];assert sha(p)==h,('GEOMETRY_CHANGED',str(p))
  if h not in byhash:
   out=dict(status='RECORDED',vertices=0,faces=0,finite_vertices=0,bounds='NOT_EVALUABLE',surface_area='NOT_EVALUABLE',units='native_units_not_independently_certified',metric_meaning='geometry inventory, not reconstruction accuracy or GT error')
   try:
    a=trimesh.load(p,process=False)
    if isinstance(a,trimesh.Scene):
     # Do not silently flatten scene transforms into a claimed original V/F.
     out.update(status='SCENE_ARCHIVE_REQUIRED',vertices=sum(len(g.vertices) for g in a.geometry.values()),faces=sum(len(g.faces) for g in a.geometry.values() if hasattr(g,'faces')),metric_meaning='scene object counts only; transforms/material references require archive before release')
    else:
     V=np.asarray(a.vertices);F=np.asarray(a.faces) if hasattr(a,'faces') else np.empty((0,3),int);finite=np.isfinite(V).all(1)
     out.update(vertices=len(V),faces=len(F),finite_vertices=int(finite.sum()))
     if len(V) and finite.all():out['bounds']=json.dumps([V.min(0).tolist(),V.max(0).tolist()])
     if len(F) and finite.all():
      area=float(trimesh.triangles.area(V[F]).sum());out['surface_area']=area if np.isfinite(area) else 'NOT_EVALUABLE'
     if not finite.all():out['status']='NONFINITE_RECORDED'
     if not len(V):out['status']='EMPTY_RECORDED'
   except Exception as e:out.update(status='NOT_EVALUABLE',metric_meaning=repr(e))
   byhash[h]=out
  rows.append(dict(path=str(p),sha256=h,size_bytes=int(x['size_bytes']),**byhash[h]))
  if (i+1)%250==0:print('MESH_RECORDED',i+1,'unique',len(byhash),flush=True)
 with gzip.open(T/'MESH_METRICS.csv.gz','wt',encoding='utf-8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
 join_inventory(rows)
 summary=dict(files=len(rows),unique_content=len(byhash),status_counts={k:sum(x['status']==k for x in rows) for k in sorted({x['status'] for x in rows})},no_geometry_modified=True,no_GT_accuracy_claim=True,epoch=time.time())
 (T/'evidence/MESH_METRICS_SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n');print(summary,flush=True)
if __name__=='__main__':main()
