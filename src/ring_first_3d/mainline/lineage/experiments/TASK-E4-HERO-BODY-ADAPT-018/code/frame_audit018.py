from common import *
def main():
 plan=load(R/'config/VIEW_PLAN.json');rows=[]
 for g in ['G06','G05','G01','G03']:
  rr=[r for r in plan if r['group']==g];video=next(r['meta']['source_video']for r in rr if r['meta'].get('source_video'));targets={r['view_id']:hashlib.sha256(np.asarray(Image.open(r['meta']['RGB_source']).convert('RGB')).tobytes()).hexdigest()for r in rr};reverse={}
  for cid,h in targets.items():reverse.setdefault(h,[]).append(cid)
  found={cid:[]for cid in targets};cap=cv2.VideoCapture(video);i=0
  while True:
   ok,im=cap.read()
   if not ok:break
   for name,inter in [('AREA',cv2.INTER_AREA),('LINEAR',cv2.INTER_LINEAR)]:
    rgb=cv2.cvtColor(cv2.resize(im,(640,360),interpolation=inter),cv2.COLOR_BGR2RGB);h=hashlib.sha256(rgb.tobytes()).hexdigest()
    for cid in reverse.get(h,[]):found[cid].append(dict(raw_index_zero_based=i,resize=name))
   i+=1
  cap.release()
  for r in rr:rows.append(dict(group=g,video='004',view_id=r['view_id'],role=r['role'],video_path=video,video_SHA256=sha(video),declared_raw_frame=r['meta'].get('raw_frame'),exact_content_matches=found[r['view_id']],status='EXACT_VIDEO_PIXEL_CONTENT_SET'if found[r['view_id']]else'ARCHIVED_CAMERA_RGB_BINDING_ONLY_RAW_SEQUENCE_NOT_RECOVERED',camera_source=r['meta'].get('pose_source'),RGB_SHA256=r['RGB_SHA256'],no_pose_modification=True))
  save('metrics/FRAME_BINDING_AUDIT.json',rows);table('metrics/FRAME_BINDING_AUDIT.csv',rows);print('FRAME_AUDIT',g,sum(bool(found[c])for c in found),'/',len(rr),flush=True)
if __name__=='__main__':main()
