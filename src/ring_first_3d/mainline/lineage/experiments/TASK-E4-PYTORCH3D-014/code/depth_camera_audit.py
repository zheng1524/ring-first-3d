"""Native HERO pixels and RGB pixels use different K, but must be identical rays."""
from common import *

def main():
 rows=[]
 for case in load(R/'config/CASE_LOCK.json'):
  n=case['name']
  for v in load(R/'inputs'/n/'CASE.json')['views']:
   cid=v['id'];p=R/'depth_observations'/(cid+'.npz')
   if not p.exists():continue
   a=np.load(p);b=np.load(R/'inputs'/n/(cid+'.npz'));uv=a['uv'];rgbuv=a['RGB_uv'];native=np.c_[uv,np.ones(len(uv))]@np.linalg.inv(a['K']).T;rgb=np.c_[rgbuv,np.ones(len(rgbuv))]@np.linalg.inv(b['K']).T
   projected=native@b['K'].T;projected=projected[:,:2]/projected[:,2:]
   row=dict(case=n,view=cid,video=v['video'],native_depth_shape=a['native_shape'].tolist(),RGB_shape=list(b['labels'].shape),T_max_abs_error=float(abs(a['T']-b['T']).max()),raw_K_matrix_difference=float(abs(a['K']-b['K']).max()),mapped_ray_max_abs_error=float(abs(native-rgb).max()),RGB_uv_mapping_error_px=float(abs(projected-rgbuv).max()))
   row['coordinate_contract_pass']=row['T_max_abs_error']<1e-10 and row['mapped_ray_max_abs_error']<1e-10 and row['RGB_uv_mapping_error_px']<1e-8;rows.append(row)
 assert rows and all(r['coordinate_contract_pass']for r in rows)
 save('provenance/DEPTH_RENDER_CAMERA_CONSISTENCY.json',dict(epoch=time.time(),rows=rows,all_coordinate_contracts_pass=True,interpretation='Native HERO 640x352 and RGB 640x360 have different fy/cy by pixel mapping. Compare rays after the frozen RGB_uv mapping, not raw K entries. Depth and RGB c2w coincide; no extra correction or scale applied.',GT_used=False))
 print('NATIVE_DEPTH_RGB_RAY_CONTRACT_PASS',len(rows))
if __name__=='__main__':main()
