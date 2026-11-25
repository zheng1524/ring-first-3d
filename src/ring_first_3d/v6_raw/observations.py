"""Show real RGB/labels and the observation/CAD boundary, including zero-HERO videos."""
from .visualize import *
from .route import legacy,sha

def make(variant,case):
 R=B/variant/case;L=read(R/'inputs/ledger005.json');gates=read(R/'metrics/GATES.json');primary=read(R/'predictions/local005_primary.json')['primary_version'];C=np.load(R/f'predictions/local005_camera_{primary}.npz')['c2w'];mods=legacy().source_modules(3.1 if '_R5_'in case else 5.6)
 inds=sorted(set([0,len(L)//2,len(L)-1]));fig,axs=plt.subplots(len(inds),4,figsize=(15,8.7),squeeze=False)
 for row,i in enumerate(inds):
  a=L[i];im=cv2.cvtColor(cv2.imread(a['RGB_path']),cv2.COLOR_BGR2RGB);lab=cv2.imread(a['Mask_path'],0);ob=np.load(R/'observations'/(a['id']+'_ring.npz'));ax=axs[row]
  ax[0].imshow(im);ax[0].set_title(f"RAW {a['raw_frame']} 原RGB\n时间戳 {a['time_sec']:.4f}秒"if'time_sec'in a else f"RAW {a['raw_frame']} 原RGB")
  ax[1].imshow(lab,vmin=0,vmax=2,cmap='viridis');ax[1].set_title('原标签：背景0 / 息肉1 / Ring2\nSIFT/HERO使用此标签，不换成拟合椭圆')
  ax[2].imshow(im)
  for key,color,label in [('q_train','cyan','轮廓训练'),('q_held','red','轮廓留出'),('ambiguous_boundary','yellow','邻息肉边界，不强迫作轮廓')]:
   q=ob[key];ax[2].scatter(q[:,0],q[:,1],s=2,color=color,label=label)
  ax[2].legend(fontsize=5,loc='upper right');ax[2].set_title('实际Ring边界观测；非椭圆补点')
  ax[3].imshow(im)
  try:
   curves=mods['g5'].contour_project(C[i])
   for c in curves:ax[3].plot(c[:,0],c[:,1],color='red',lw=1)
  except Exception as ex:ax[3].text(10,30,'CAD投影不可计算：'+str(ex)[:35],fontsize=7)
  ax[3].set(xlim=(0,640),ylim=(360,0));g=gates[i];ax[3].set_title(f"相机条件下真实CAD投影\n旧/新门控：{g['old_pass']} / {g['new_pass']}")
  for q in ax:q.axis('off')
 fig.suptitle(short(case)+' / '+LABEL[variant]+'：按时间取首/中/末三帧的观测链\n图像均为实际本轮RAW处理；Ring内径'+('5'if'_R5_'in case else'10')+'毫米；像素坐标；相机未由GT标定',fontsize=11)
 name=variant+'__'+case+'__观测链.jpg';finish(fig,F/name);return dict(case=case,variant=variant,image=name,raw_frames=[L[i]['raw_frame']for i in inds],code_sha256=sha(__file__))

if __name__=='__main__':
 records=[]
 for variant in ['HIST','GRAPH']:
  for R in sorted((B/variant).glob('GP_*')):
   if(R/'HERO_COMPLETE.json').exists():records.append(make(variant,R.name))
 save(T/'evidence/OBSERVATIONS_INDEX.json',records)
 (T/'OBSERVATIONS_INDEX.html').write_text('<!doctype html><meta charset="utf-8"><title>V6实际观测链</title><style>body{max-width:1500px;margin:auto;font-family:system-ui}img{width:100%}</style><h1>实际RAW、Mask、Ring观测与CAD投影</h1><p><a href="VISUALIZATION_INDEX.html">返回完整HERO图集</a></p>'+''.join(f'<h2>{short(r["case"])} / {LABEL[r["variant"]]}</h2><img loading="lazy" src="figures/{r["image"]}">'for r in records))
