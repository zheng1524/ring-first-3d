"""All18 actual RGB-named tracks, without pose/body/HERO evaluation or identity pruning."""
from common import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def main():
 tr=load(R/'observations/CROSS_COMMON_TRACKS.json');audit={a['track']:a for a in load(R/'metrics/CROSS_TRACK_INITIALIZATION_AUDIT.json')};fig,axs=plt.subplots(6,3,figsize=(19,21))
 for ax,t in zip(axs.ravel(),tr):
  strips=[];names=[]
  for side in [0,1]:
   o=next(o for o in t['observations']if o['side']==side);im=np.array(Image.open(o['RGB_source']).convert('RGB'));u,v=np.rint(o['uv']).astype(int);x0=max(0,u-40);y0=max(0,v-40);crop=im[y0:min(im.shape[0],v+41),x0:min(im.shape[1],u+41)];cw,ch=crop.shape[1],crop.shape[0];img=cv2.resize(crop,(200,200));pos=(int((o['uv'][0]-x0+.5)*200/cw-.5),int((o['uv'][1]-y0+.5)*200/ch-.5));cv2.drawMarker(img,pos,(255,40,40),cv2.MARKER_CROSS,12,1);strips.append(img);names.append(o['view']+' #'+str(o['feature_id']))
  a=audit[t['track']];ax.imshow(np.concatenate(strips,axis=1));ax.axis('off');ax.set_title('Track %d | %d real observations | %d RGB links\n%s\n%s\nindependent X separation %.2f mm; not identity-rejection threshold'%(t['track'],len(t['observations']),len(t['cross_RGB_evidence']),*names,a['independent_3D_difference_at_RoMa_mm']),fontsize=7)
 fig.suptitle('All18 real named SIFT tracks: 004 left /005 right, red cross = actual feature UV\nNative RGB crops resized for display only. Descriptors / original IDs / all FIT observations retained; all background texture.\nMultiframe RGB-RANSAC supports identity; repetitive texture, static-material assumptions and camera errors remain uncertain. No 3D-nearest identity or GT.');fig.tight_layout(rect=[0,0,1,.95]);fig.savefig(R/'figures/All18_Actual_RGB_Track_Identity_Audit.png',dpi=120);plt.close(fig);save('provenance/ALL18_RGB_CONTACT_SHEET.json',dict(figure=asset(R/'figures/All18_Actual_RGB_Track_Identity_Audit.png'),tracks=18,all_preserved=True,not_physical_GT=True));print('ALL18_RGB_SHEET_COMPLETE',flush=True)
if __name__=='__main__':main()
