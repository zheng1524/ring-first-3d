"""Unify all raw assets and unposed candidates in the delivery inventory.
Original projectable-only preregistration CSV is archived byte-for-byte; no change
to camera/Mask/selection/training inputs.
"""
from common import *
import shutil
def main():
 p=R/'VIEW_INVENTORY.csv';archive=R/'metrics/PROJECTABLE_VIEW_INVENTORY_FROZEN.csv'
 if not archive.exists():shutil.copyfile(p,archive)
 rows=list(csv.DictReader(archive.open()))
 for r in rows:r.update(record_kind='PROJECTABLE_VIEW',available_camera=True)
 for v in load(R/'metrics/UNPOSED_RAW_CANDIDATES.json'):
  rows.append(dict(case=v['case'],id=v['id'],sid=v['sid'],video=v['video'],record_kind='UNPOSED_RAW_CANDIDATE',role=v['role'],RGB_source=v['RGB_source'],Mask_source=v['Mask_source'],RGB_sha=v['RGB_SHA256'],Mask_sha=v['Mask_SHA256'],raw_frame=v['raw_frame'],time_sec=v['time_sec'],frame_binding=v['frame_binding'],available_camera=False,qualification='NO_METRIC_BG_PNP_SOLUTION; retain UNKNOWN',source_video_SHA256=v['source_video_SHA256']))
 for a in load(R/'config/RAW_ASSETS.json'):
  row=dict(case=a['case'],id=a['id'],video=a.get('video'),record_kind='RAW_VIDEO_ASSET'if a['type']=='video'else'INDEPENDENT_PHOTO',RGB_source=a['source'],RGB_sha=a['sha256'],available_camera=False,qualification='ASSET_INDEX_ONLY'if a['type']=='video'else'NO_VERIFIED_PHOTO_K_OR_METRIC_POSE',frame_count=a.get('frame_count'),physical_specimen=a['physical_specimen'])
  if a['type']=='photo':
   try:
    with Image.open(a['source'])as im:row.update(width=im.width,height=im.height,readable=True)
   except Exception as e:row.update(readable=False,decode_error=str(e))
  else:row['raw_frame_timeline']=str(R/'new_views'/a['sid']/'inputs/RAW_FRAME_TIMELINE.csv')
  rows.append(row)
 table('VIEW_INVENTORY.csv',rows);save('provenance/INVENTORY_DELIVERY_COMPLETION.json',dict(epoch=time.time(),projectable_original=asset(archive),complete_inventory=asset(p),row_N=len(rows),projectable_N=sum(r['record_kind']=='PROJECTABLE_VIEW'for r in rows),source_camera_Mask_and_selection_changed=False,reason='merge previously separate raw/photo/unposed ledgers without dropping unknowns'))
if __name__=='__main__':main()
