"""Downstream reader: GROUP.json is the sole source index; no M4/M5 guesses."""
from pathlib import Path
import json,hashlib
import numpy as np
def apply_source(V,F,selection,T,coordinate_frame):
 if coordinate_frame!='LOCAL':raise ValueError('Raw vertices must be LOCAL; refuse a second transform')
 T=np.asarray(T);return V@T[:3,:3].T+T[:3,3],F[np.asarray(selection,int)]
def load_source(group_file,source_id):
 import trimesh
 group=json.loads(Path(group_file).read_text());source=next(s for s in group['sources']if s['source_id']==source_id)
 if not source['connected'] or source['clean_status']!='COMPLETE':raise ValueError('Source is not ready in the common frame')
 def verified(p,h):
  p=Path(p);assert hashlib.sha256(p.read_bytes()).hexdigest()==h;return p
 m=trimesh.load(verified(source['raw_mesh'],source['raw_mesh_sha256']),process=False);state=np.load(verified(source['selection'],source['selection_sha256']));V,F=apply_source(np.asarray(m.vertices),np.asarray(m.faces),state['trusted_original_face_id'],source['T_local_to_common'],source['raw_coordinate_frame'])
 camera=next(v for v in group['videos']if v['case']==source['case']);cams=np.load(verified(camera['common_cameras'],camera['common_cameras_sha256']))
 assert camera['camera_coordinate_frame']=='COMMON'
 return dict(V=V,F=F,original_face_id=state['trusted_original_face_id'],c2w=cams['c2w'],K=cams['K'],reference=source['reference'],units='mm')
