from common import *
def main():
 rows=load(R/'metrics/FRAME_BINDING_AUDIT.json');p=Path('/home/liu/polyp_research/ring_anchor_3d/experiments/surface_fusion_v1/inputs/real_frames_manifest.json');fm=load(p);plan={r['view_id']:r for r in load(R/'config/VIEW_PLAN.json')};evidence=[]
 for row in rows:
  if row['exact_content_matches']:continue
  target=np.asarray(Image.open(plan[row['view_id']]['meta']['RGB_source']).convert('RGB'));matches=[]
  for src in fm:
   image=cv2.imread(src['image_path']);small=cv2.cvtColor(cv2.resize(image,(640,360),interpolation=cv2.INTER_AREA),cv2.COLOR_BGR2RGB)
   if not np.array_equal(small,target):continue
   assert sha(src['image_path'])==src['image_sha256'];cap=cv2.VideoCapture(row['video_path']);cap.set(cv2.CAP_PROP_POS_FRAMES,int(src['frame_index']));ok,bgr=cap.read();cap.release();assert ok
   ok,data=cv2.imencode('.jpg',bgr,[cv2.IMWRITE_JPEG_QUALITY,95]);assert ok;h=hashlib.sha256(data.tobytes()).hexdigest();matches.append(dict(raw_index_zero_based=src['frame_index'],JPEG_quality=95,JPEG_SHA256=src['image_sha256'],raw_decode_reencoded_SHA256=h,raw_decode_exact_JPEG_match=h==src['image_sha256'],parent=asset(src['image_path']),manifest=asset(p),cache_resize_exact=True))
  row['JPEG_chain_matches']=matches
  if matches and all(x['raw_decode_exact_JPEG_match']for x in matches):row['status']='EXACT_RAW_JPEG95_AREA_CACHE_CHAIN'
  evidence.append(dict(view=row['view_id'],matches=matches))
 save('metrics/FRAME_BINDING_JPEG_RECOVERY.json',evidence);save('metrics/FRAME_BINDING_AUDIT.json',rows);table('metrics/FRAME_BINDING_AUDIT.csv',rows);print('FRAME_BINDINGS_PROVEN',sum(r['status'].startswith('EXACT_')for r in rows),'/',len(rows),flush=True)
if __name__=='__main__':main()
