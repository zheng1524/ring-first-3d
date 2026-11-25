"""Lossless RAW decoder identity. JPEG hashes alone can alias distinct frames."""
import hashlib
import numpy as np,cv2
def digest(image):return hashlib.sha256(image.tobytes()).hexdigest()
def bind_frames(video,requested,jpeg_sha256):
 cap=cv2.VideoCapture(str(video));targets={};seek_hash=[];seek_pts=[]
 for i,index in enumerate(requested):
  cap.set(cv2.CAP_PROP_POS_FRAMES,int(index));ok,image=cap.read()
  if not ok:raise ValueError('SEEK_DECODE_FAILED:'+str(index))
  assert digest(cv2.imencode('.jpg',image,[cv2.IMWRITE_JPEG_QUALITY,95])[1])==jpeg_sha256[i],'JPEG changed from original preparation'
  h=digest(image);pts=round(cap.get(cv2.CAP_PROP_POS_MSEC),6);seek_hash.append(h);seek_pts.append(pts);targets.setdefault((h,pts),[]).append(i)
 cap.release();cap=cv2.VideoCapture(str(video));actual={};frame=0;equivalent={h:[]for h in seek_hash}
 while True:
  ok,image=cap.read()
  if not ok:break
  h=digest(image);pts=round(cap.get(cv2.CAP_PROP_POS_MSEC),6)
  if h in equivalent:equivalent[h].append(frame)
  for i in targets.get((h,pts),[]):actual.setdefault(i,[]).append(frame)
  frame+=1
 cap.release()
 if len(actual)!=len(requested)or any(len(x)!=1 for x in actual.values()):raise ValueError('LOSSLESS_RAW_AND_PTS_IDENTITY_NOT_UNIQUE:'+str(actual))
 return [dict(frame_index=actual[i][0],raw_BGR_sha256=seek_hash[i],decoder_timestamp_ms=seek_pts[i],identical_raw_pixel_frames=equivalent[seek_hash[i]],JPEG95_sha256=jpeg_sha256[i],requested_seek_frame=int(requested[i]),identity='EXACT_SEQUENTIAL_RAW_BGR_SHA256_AND_DECODER_PTS_AND_JPEG95')for i in range(len(requested))]
