import sys,json,pathlib,cv2,numpy as np
from PIL import Image
WS=pathlib.Path('/home/liu/ring_first_3d_workspace');sys.path.insert(0,str(WS/'src'))
from ring_first_3d.mainline.native.geometry import unproject,project,resize_index_intrinsics,native_rgb_labels
O=WS/'runs/m2d_mvs_reproduction'; V=O/'pixel_roundtrip';V.mkdir(parents=True,exist_ok=True)
R=WS/'experiments/TASK-E4-UNIFIED-RING-FIRST-HERO-DEPTH-001/runs/RF_ONLY_V1'; ids=['G01_004_ref03','G03_key00_raw00100','G05_key00_raw00097','G06_004_ref04']; rows=[]
for hid in ids:
 g=hid.split('_')[0]; src=json.loads((R/g/'004'/'hero'/hid/'SOURCE.json').read_text()); z=dict(np.load(src['input_caches'][0]['path'])); rgb=np.asarray(z['RGB']); labels=np.asarray(z['labels']); K=np.asarray(z['K'],float)
 out=O/'historical_reproduction'/'R1'/hid; d=dict(np.load(out/'HERO_native.npz')); dep=np.asarray(d['depth_mm']); Kn=np.asarray(d['K_index_native'],float); T=np.asarray(d['reference_pose_mm'],float)
 yy,xx=np.nonzero(np.isfinite(dep)&(dep>0)); uv=np.c_[xx,yy].astype(float); X=unproject(dep[yy,xx],T,uv,Kn); uv2,zz=project(X,T,Kn); err=np.linalg.norm(uv2-uv,axis=1)
 nrgba,nlab,_=native_rgb_labels(rgb,labels,K); eq=float((nlab[yy,xx]==labels[yy,xx]).mean())
 # map native pixel to work pixel via native_rgb_labels's inverse-ish nearest: use projection through K_native/K
 # recover source pixel from native pixel using the index-centred mapping relation
 Kwork=K; # work K is 360x640; native K is resized; source-to-native mapping computed by native_rgb_labels floor
 yy2,xx2=np.mgrid[:352,:640]; p=np.c_[xx2.ravel(),yy2.ravel(),np.ones(xx2.size)]@np.linalg.inv(Kn).T@Kwork.T; p=(p[:,:2]/p[:,2:]).astype(int); p[:,0]=np.clip(p[:,0],0,639); p[:,1]=np.clip(p[:,1],0,359); lab_work=labels[p[:,1],p[:,0]].reshape(352,640); eq2=float((nlab==lab_work).mean())
 rows.append(dict(historical_id=hid,group=g,native_valid_pixels=int(len(uv)),native_pixel_median_error_px=float(np.median(err)),native_pixel_p95_error_px=float(np.percentile(err,95)),native_pixel_max_error_px=float(err.max()),work_label_agreement=eq2,native_label_agreement_source_pixel=eq,K_work_sha=hashlib.sha256(K.tobytes()).hexdigest()[:16] if False else ''))
 # figure
 import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
 fig,ax=plt.subplots(1,3,figsize=(12,3));ax[0].imshow(rgb);ax[0].set_title('A work RGB');ax[0].axis('off');ax[1].imshow(nlab,cmap='gray');ax[1].set_title('native labels 352x640');ax[1].axis('off');ax[2].imshow(dep,cmap='turbo');ax[2].set_title('native depth mm');ax[2].axis('off');fig.tight_layout();fig.savefig(V/f'{hid}_A_to_A.png',dpi=100);plt.close(fig)
import pandas as pd
pd.DataFrame(rows).to_csv(O/'PIXEL_ROUNDTRIP_VALIDATION.csv',index=False);print(pd.DataFrame(rows).to_string(index=False))
