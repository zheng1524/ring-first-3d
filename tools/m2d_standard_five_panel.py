import sys,json,pathlib
import numpy as np,cv2
from PIL import Image
WS=pathlib.Path('/home/liu/ring_first_3d_workspace');sys.path.insert(0,str(WS/'src'));sys.path.insert(0,str(WS/'src/ring_first_3d/mainline/frozen_registry'));sys.path.insert(0,str(WS/'src/ring_first_3d/mainline/lineage/experiments/TASK-VIEW-OBSERVABILITY-GT-EVAL-001/code'))
import reprojection as r
sample=json.loads((WS/'mainline/configs/A_TO_B_SAMPLE.json').read_text());row=sample['pair'];c=sample['source'];t=row['B_target']
P=np.asarray(np.load(c['source_points'])['points_mm']);uv=np.asarray(np.load(c['source_points'])['uv']);m=np.load(c['camera_file']);pose=np.asarray(m['c2w'],float)
if pose.ndim==3: pose=pose[int(c['reference_index'])]
if pose.shape==(3,4): pose=np.vstack([pose,[0,0,0,1]])
p=dict(K=np.asarray(m['K'],float),pose=pose);rgb=np.asarray(Image.open(c['RGB']).convert('RGB'));C=rgb[uv[:,1],uv[:,0]]/255.
pred=dict(np.load(WS/'runs/m2d_mvs_reproduction/standard_a_to_b/PREDICTION.npz'));B=np.asarray(Image.open(t['RGB']).convert('RGB'));labels=cv2.imread(t['Mask'],0)
metrics,mae,common=r.evaluate(pred,B,labels);metrics.update(pair_id=row['pair_id'],conditional_optical_angle_deg=0.0,conditional_baseline_mm=0.0)
rm=r.ring(c); r.ring=lambda x:rm
out=WS/'runs/m2d_mvs_reproduction/standard_a_to_b'; r.R=out
print(r.make_figure(row,pred,metrics,mae,common,P,C,p,c,B))
