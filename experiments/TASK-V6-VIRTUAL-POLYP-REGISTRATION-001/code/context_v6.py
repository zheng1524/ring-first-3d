import shutil
import numpy as np
from common import *
def span(C):
 d=C[:,:3,2];dist=np.linalg.norm(C[:,:3,3],axis=1)
 return dict(frames=len(C),axis_pair_max_deg=float(np.rad2deg(np.arccos(np.clip((d@d.T).min(),-1,1)))),center_to_ring_min_mm=float(dist.min()),center_to_ring_max_mm=float(dist.max()))
base=Path('/home/liu/ring_first_3d_workspace/runs/v6_raw_to_hero_001/HIST');src=read(T/'inputs/VIEW_SOURCES.json');out=[]
for v in ['004','005']:
 folder=T/'inputs'/('V6_HIST_'+v);original=base/(CFG['case']+'_'+v)/'metrics/GATES.json';shutil.copyfile(original,folder/'GATES.json');g=read(original);C=np.load(folder/'local005_camera_0.npz')['c2w'];sim=np.array([r['Camera_to_Ring']for r in src['selected']if r['video']==v]);vals=[r['metrics']['held_reprojection']['MAE'] for r in g];ring=[r['metrics']['ring_held_self_contour_px']['MAE']for r in g];out.append(dict(video=v,source=str(original),source_sha256=sha(original),V6=span(C),simulation_FIT=span(sim),Q0=sum(r['old_pass']for r in g),Q1=sum(r['new_pass']for r in g),held_RGB_per_frame_MAE_median_px=float(np.median(vals)),held_RGB_per_frame_MAE_max_px=float(max(vals)),ring_per_frame_MAE_median_px=float(np.median(ring)),reference_only=True,real_V6_predictions_are_not_GT=True))
save(T/'evidence/V6_REFERENCE_CONTEXT.json',out)
