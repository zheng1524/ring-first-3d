"""Photo preparation under the researcher-confirmed shared acquisition settings."""
from pathlib import Path
import hashlib
import cv2
import numpy as np
from PIL import Image

def prepare_group(r,group,coordinate_system):
 cfg=r.FULL_CONFIG['frontend'];assert cfg['photo_intrinsics_basis']=='USER_CONFIRMED_SAME_OPTICS_ZOOM_CROP_DISTORTION_AS_VIDEO'
 manifest=r.read(r.FULL_CONFIG['manifest']);entries=[p for p in manifest['static_photos'] if Path(p['path']).stem.rsplit('_',1)[0]==group]
 dest=Path(cfg['photo_cache']);dest.mkdir(parents=True,exist_ok=True);rows=[];model=None
 for p in entries:
  path=Path(p['path']);assert r.sha(path)==p['sha256'];pid=path.stem.rsplit('_',1)[1];out=dest/path.stem;out.mkdir(exist_ok=True);receipt=out/'PREPARED.json'
  if receipt.exists():
   row=r.read(receipt);assert row['source_sha256']==p['sha256'] and row['protocol_signature']==r.protocol_signature('prepare')
   assert r.sha(row['RGB_path'])==row['RGB_SHA256'] and r.sha(row['Mask_path'])==row['Mask_SHA256']
  else:
   with Image.open(path) as im:orientation=im.getexif().get(274,1)
   if orientation!=1:raise ValueError('PHOTO_ORIENTATION_REQUIRES_EXPLICIT_GEOMETRY')
   native=cv2.imread(str(path));h,w=native.shape[:2]
   if abs(w/h-640/360)>1e-8:raise ValueError('PHOTO_FOV_ASPECT_NOT_VIDEO_CONTRACT')
   work=cv2.resize(native,(640,360),interpolation=cv2.INTER_AREA);rgb=out/'RGB.png';mask=out/'Mask.png';assert cv2.imwrite(str(rgb),work)
   if model is None:
    from dxy_mid.segmentation import INITSegmentation
    model=INITSegmentation(str(r.INIT_PATH),'cuda')
   labels=model.predict(str(rgb));assert labels.shape==(360,640) and np.isin(labels,[0,1,2]).all();assert cv2.imwrite(str(mask),labels)
   A=np.array([[640/w,0,(640/w-1)/2],[0,360/h,(360/h-1)/2],[0,0,1.]])
   row=dict(id='photo_'+pid,view_id=group+':photo:'+pid,photo_id=pid,media_type='photo',raw_frame=None,video_raw_frame=None,time_sec=None,source_id=pid,source=path.name,source_path=str(path),source_sha256=p['sha256'],native_BGR_sha256=hashlib.sha256(native.tobytes()).hexdigest(),physical_view_id=hashlib.sha256(work.tobytes()).hexdigest(),RGB_path=str(rgb),Mask_path=str(mask),RGB_SHA256=r.sha(rgb),Mask_SHA256=r.sha(mask),K=r.K.tolist(),native_shape=[h,w],working_shape=[360,640],orientation=orientation,original_to_work=A.tolist(),native_K_under_shared_assumption=(np.linalg.inv(A)@r.K).tolist(),intrinsics_basis=cfg['photo_intrinsics_basis'],independent_calibration_available=False,valid_pixel_domain='full image; same crop confirmed; resize only',protocol_signature=r.protocol_signature('prepare'),original16=False)
   r.save(receipt,row)
  rows.append(dict(row,coordinate_system=coordinate_system,video_id=None))
 return rows
