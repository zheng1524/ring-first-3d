"""Recheck cached Ring projections and frame identities, without any filter/fit."""
from common import *
import open3d as o3d
OLD14=REPO/'experiments/TASK-E4-PYTORCH3D-014'
def main():
 rows=[];refs=load(R/'config/REFERENCE_VIDEOS.json');sel=load(R/'config/VIEW_SELECTION.json')
 for case in load(R/'config/CASE_LOCK.json'):
  n=case['name'];rr=np.load(R/'inputs'/n/'RING.npz');oldrg=np.load(OLD14/'inputs'/n/'RING.npz');assert np.array_equal(rr['V'],oldrg['V'])and np.array_equal(rr['F'],oldrg['F']);rs=None
  for v in getcase(n)['views']:
   cid=v['id'];a=np.load(R/'inputs'/n/(cid+'.npz'));b=np.load(OLD14/'inputs'/n/(cid+'.npz'));assert all(np.array_equal(a[k],b[k])for k in ['RGB','labels','K','T']);assert v['video']==refs[n]['reference_video'];p=OLD14/'runtime/cad_depth'/(cid+'.npz')
   if p.exists():z=np.load(p)['z'];origin='014 exact same CAD/K/T independent projection cache'
   else:
    rs=rs or scene(rr['V'],rr['F']);z=cast(rs,a['K'],a['T'],360,640);origin='read-only frozen CAD raycast, no geometry inference'
   lab=a['labels'];rm=lab==2;cad=np.isfinite(z)&(lab!=1);cp=contour(cad);ct=contour(rm);bd=stats(cKDTree(cp).query(ct)[0])if len(cp)and len(ct)else stats([]);rows.append(dict(case=n,view=cid,video=v['video'],role=v['role'],original_S0=cid in sel[n]['S0'],selected_S8=cid in sel[n]['S8'],selected_S16=cid in sel[n]['S16'],selected_S32=cid in sel[n]['S32'],raw_frame=v.get('raw_frame'),frame_binding=v.get('frame_binding'),archived_camera_image_identity_exact=True,raw_frame_identity_status='KEEP_ORIGINAL_BINDING_QUALIFICATION',Ring_CAD_mask_IoU=float((rm&cad).sum()/max(1,(rm|cad).sum())),CAD_pixel_N=int(np.isfinite(z).sum()),observed_Ring_boundary_to_CAD_px=bd,projection_source=origin,no_filter_or_camera_change=True))
 save('metrics/INPUT_RING_AND_FRAME_AUDIT.json',rows);table('INPUT_RING_AND_FRAME_AUDIT.csv',rows)
 print('INPUT_AUDIT_COMPLETE',len(rows),'no new pose/mask/HERO and no exclusions',flush=True)
if __name__=='__main__':main()
