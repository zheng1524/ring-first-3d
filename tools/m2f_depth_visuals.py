import sys,json,pathlib
import numpy as np,pandas as pd,open3d as o3d,matplotlib
matplotlib.use('Agg');import matplotlib.pyplot as plt
from PIL import Image
WS=pathlib.Path('/home/liu/ring_first_3d_workspace');O=WS/'runs/m2f_metric_depth_diagnosis';V=O/'visualization'/'depth_diagnosis';V.mkdir(parents=True,exist_ok=True)
G=['GP_Ip_12.0mm_closed_R10_single_refY','GP_Is_9.79mm_closed_R10_single_refY','GP_Is_14.0mm_closed_R10_single_refY'];e=pd.read_csv(O/'hero/HERO_EXECUTION_RESULTS.csv');cad=np.load(O/'cad/R10.npz')
for g in G:
 r=e[e.group_id==g].iloc[0];out=pathlib.Path(r.output_dir);z=np.load(out/'HERO_native.npz');H=z['depth_mm'];Kn=z['K_index_native'];C=z['reference_pose_mm'];lab=np.load(out/'NATIVE_RGB_LABELS.npz')['labels'];sc=o3d.t.geometry.RaycastingScene(nthreads=2);sc.add_triangles(o3d.core.Tensor(cad['V'].astype(np.float32)),o3d.core.Tensor(cad['F'].astype(np.uint32)));yy,xx=np.mgrid[:352,:640];uv=np.c_[xx.ravel(),yy.ravel(),np.ones(xx.size)];dirs=(uv@np.linalg.inv(Kn).T)@C[:3,:3].T;rays=np.c_[np.broadcast_to(C[:3,3],dirs.shape),dirs];cd=sc.cast_rays(o3d.core.Tensor(rays.astype(np.float32)))['t_hit'].numpy().reshape(352,640);valid=np.isfinite(cd)&(cd>0)&(lab==2)&(H>0);diff=np.full_like(H,np.nan);diff[valid]=H[valid]-cd[valid]
 fig,ax=plt.subplots(1,5,figsize=(20,4));ax[0].imshow(np.load(out/'NATIVE_RGB_LABELS.npz')['RGB']);ax[0].set_title('RGB');ax[1].imshow(lab);ax[1].set_title('labels (2=Ring)');im=ax[2].imshow(cd,cmap='turbo');ax[2].set_title('CAD Ring depth mm');ax[3].imshow(H,cmap='turbo');ax[3].set_title('HERO depth mm');im2=ax[4].imshow(diff,cmap='coolwarm',vmin=-20,vmax=20);ax[4].set_title('HERO-CAD mm (Ring pixels)');[a.axis('off') for a in ax];fig.colorbar(im2,ax=ax[4],fraction=.046);fig.suptitle(f'{g} | {r.target_id} | valid Ring px={valid.sum()}');fig.tight_layout();fig.savefig(V/f'{g}.png',dpi=110);plt.close(fig)
print('depth visuals',len(list(V.glob('*.png'))))
