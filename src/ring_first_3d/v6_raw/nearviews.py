"""Supplementary fixed physical close views with explicit projected crop counts."""
from .visualize import *

def projected_out(V,bounds,cad,elev,azim):
 allv=np.r_[bounds,cad['V']];center=(allv.min(0)+allv.max(0))/2;rad=np.linalg.norm(allv-center,axis=1).max();e,a=np.radians([elev,azim]);pos=center+rad*3.4*np.array([np.cos(e)*np.cos(a),np.cos(e)*np.sin(a),np.sin(e)])
 forward=(center-pos)/np.linalg.norm(center-pos);right=np.cross(forward,[0.,0.,1.]);right/=np.linalg.norm(right);down=np.cross(forward,right);pc=(V-pos)@np.array([right,down,forward]).T;uv=pc[:,:2]/np.maximum(pc[:,2:3],1e-12)*490+199.5
 return(pc[:,2]<=0)|(uv[:,0]<0)|(uv[:,0]>=400)|(uv[:,1]<0)|(uv[:,1]>=400)

def make(O,kinds=('近景RGB','近景逐源'),full_range_link=True):
 s=read(O/'SUMMARY.json');rows=[r for r in read(O/'RESULTS.json')if r['status']=='RENDERABLE']
 assert len(rows)==s['renderable']
 if not rows:return None
 data=geometry(rows);case=s['case'];variant=s['variant'];inner=5 if'_R5_'in case else 10;half=inner/2+5;bounds=np.array([[x,y,z]for x in [-half,half]for y in [-half,half]for z in [-half,half]])
 cad=dict(np.load(W/'runs/m2f5_unified/cad'/('R5.npz'if inner==5 else'R10.npz')));V=[];F0=[];RGB=[];SRC=[];n=0;palette=plt.get_cmap('turbo')
 for i,r in enumerate(sorted(rows,key=lambda r:r['raw_target'])):
  v,f,c=data[r['tag']];V.append(v);F0.append(f+n);n+=len(v);RGB.append(c[f].mean(1));SRC.append(np.tile(palette(i/max(1,len(rows)-1))[:3],(len(f),1)))
 V=np.concatenate(V);F0=np.concatenate(F0);records=[]
 for name,col in [(name,col) for name,col in [('近景RGB',np.concatenate(RGB)),('近景逐源',np.concatenate(SRC))] if name in kinds]:
  fig,axs=plt.subplots(2,3,figsize=(12,9))
  for ax,(label,e,a)in zip(axs.flat,ANGLES):
   draw(ax,V,F0,col,cad,bounds,e,a);out=projected_out(V,bounds,cad,e,a);count=int(out.sum());faces=int(out[F0].any(1).sum());ax.set_title(f'{label}：出画顶点 {count}/{len(V)}\n含出画顶点三角形 {faces}/{len(F0)}',fontsize=8)
   if name==kinds[0]:records.append(dict(view=label,outside_vertices=count,total_vertices=len(V),triangles_with_outside_vertex=faces,total_triangles=len(F0)))
  fig.suptitle(short(case)+' / '+LABEL[variant]+f'：补充近景，{len(rows)}个面源仍全部送入原renderer\n观察框按Ring内径固定为±{half:g}毫米；实际投影出画数量逐视角标注'+('；完整范围见总览' if full_range_link else '；仅显示近景，原Mesh全量保留')+'\n'+('颜色按真实Target帧先后（蓝→红），不表示质量或准入；黑色为CAD'if name=='近景逐源'else'原始RGB；没有裁掉或重建Mesh文件'),fontsize=10)
  fig.tight_layout(rect=(0,.09,1,.92),h_pad=3.8,w_pad=1.2)
  if name=='近景逐源':
   from matplotlib.colors import Normalize
   cb=fig.colorbar(plt.cm.ScalarMappable(norm=Normalize(0,max(1,len(rows)-1)),cmap=palette),cax=fig.add_axes([.13,.045,.74,.015]),orientation='horizontal',ticks=range(len(rows)))
   cb.ax.set_xticklabels([str(r['raw_target'])for r in sorted(rows,key=lambda r:r['raw_target'])],fontsize=6);cb.set_label('真实RAW Target帧（时序颜色，不表示质量）',fontsize=8)
  fig.savefig(T/'figures'/(variant+'__'+case+'__'+name+'.png'),dpi=105);plt.close(fig)
 return dict(case=case,variant=variant,viewer_bound_half_mm=half,views=records,ordered_raw_targets=sorted(r['raw_target']for r in rows))

if __name__=='__main__':
 save(T/'evidence/NEARVIEW_CROP_COUNTS.json',[r for r in[make(p.parent)for p in sorted((B/'evaluation').glob('*/*/COMPLETE.json'))]if r])
