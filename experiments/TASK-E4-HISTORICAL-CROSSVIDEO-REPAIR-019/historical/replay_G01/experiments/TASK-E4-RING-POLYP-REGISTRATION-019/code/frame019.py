from common import *
def main():
 vv=[v for v in load(R/'config/VIEWS.json')if v['video']=='005'];src=next(a['source']for a in load(REPO/'experiments/TASK-E4-PYTORCH3D-014/config/RAW_ASSETS.json')if a['case']=='G01'and a.get('video')=='005');lookup={};matches={v['id']:[]for v in vv}
 for v in vv:lookup.setdefault(hashlib.sha256(np.ascontiguousarray(np.array(Image.open(v['RGB_source']).convert('RGB'))).tobytes()).hexdigest(),[]).append(v['id'])
 cap=cv2.VideoCapture(src);idx=0
 while True:
  ok,bgr=cap.read()
  if not ok:break
  for mode in [cv2.INTER_AREA,cv2.INTER_LINEAR]:
   im=cv2.resize(bgr,(640,360),interpolation=mode)[:,:,::-1];h=hashlib.sha256(np.ascontiguousarray(im).tobytes()).hexdigest()
   for cid in lookup.get(h,[]):matches[cid].append(dict(raw_index=idx,resize='AREA'if mode==cv2.INTER_AREA else'LINEAR'))
  idx+=1
 cap.release();rows=[]
 for v in vv:rows.append(dict(view=v['id'],role=v['role'],declared=v.get('raw_frame'),exact_raw_matches=matches[v['id']],status='EXACT_RAW_PIXEL_CONTENT'if matches[v['id']]else'ARCHIVE_RGB_CAMERA_EXACT_UNRESOLVED_RAW_INDEX',RGB_SHA256=v['RGB_SHA256'],original_pose_not_modified=True))
 save('metrics/VIDEO005_FRAME_BINDING.json',dict(source_video=asset(src),decoded_frame_count=idx,rows=rows));table('metrics/VIDEO005_FRAME_BINDING.csv',rows);print('VIDEO005_EXACT_FRAMES',sum(bool(x['exact_raw_matches'])for x in rows),'/',len(rows),flush=True)
if __name__=='__main__':main()
