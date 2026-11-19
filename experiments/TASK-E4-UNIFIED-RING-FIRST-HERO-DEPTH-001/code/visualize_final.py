"""Static figures from actual admitted camera/depth/body/evaluation artifacts."""
from pathlib import Path
import csv,json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from scipy.spatial import cKDTree
import pipeline as p
from ring_first_3d.mainline.native.camera import torus_contours,observe
T=p.TASK;OUT=T/'runs/RF_ONLY_V1';VIS=T/'visualization';VIS.mkdir(exist_ok=True)
plt.rcParams.update({'font.size':8,'savefig.dpi':125})

def full_mesh(ax,V,F,color,alpha=.8,values=None):
    coll=Poly3DCollection(V[F],edgecolor='none',alpha=alpha,rasterized=True)
    if values is None:coll.set_facecolor(color)
    else:coll.set_array(np.asarray(values)[F].mean(1));coll.set_cmap('viridis');coll.set_clim(0,1)
    ax.add_collection3d(coll);return coll

def axes3(ax,limits):
    for a,lim in zip('xyz',limits):getattr(ax,'set_'+a+'lim')(lim);getattr(ax,'set_'+a+'label')(a+' [mm]')
    ax.view_init(15,-65);ax.set_box_aspect([b-a for a,b in limits])

def limits(V):
    mid=(V.min(0)+V.max(0))/2;rad=np.ptp(V,axis=0).max()*.6
    return [(x-rad,x+rad) for x in mid]

def main():
    assert p.read(OUT/'GT_EVALUATION_COMPLETE.json')['status']=='PASS'
    views=p.read(T/'audit/SELECTED_VIEWS.json');metrics=list(csv.DictReader(open(T/'metrics/PER_VIEW_METRICS.csv')));index=[]
    for c in p.cases():
        group=c['case'];folder=VIS/group;folder.mkdir(exist_ok=True);ss=[v for v in views if v['meta']['case']==group];evaluation=OUT/group/'004/evaluation';initial=dict(np.load(c['initial']['path']));ring=dict(np.load(c['static']['RING.npz']['path']));bodies={'B0':initial}
        for arm in ['B1','B2']:
            z=OUT/group/'004/body'/arm/'FINAL.npz'
            if z.exists():bodies[arm]=dict(np.load(z))
        # Per-view Ring evidence includes rejected cameras, never hides a gap.
        for v in ss:
            m=v['meta'];a=p.check_input(v);cam=OUT/group/m['video']/'camera'/m['id'];ad=p.read(cam/'ADMISSION.json');fig,axes=plt.subplots(1,3,figsize=(14,4))
            axes[0].imshow(a['RGB']);axes[0].contour(a['labels']==2,levels=[.5],colors='cyan',linewidths=.8);axes[0].set_title('Actual RGB + observed Ring Mask')
            axes[1].imshow(a['RGB'],alpha=.6);axes[2].imshow(a['RGB'],alpha=.3)
            result=p.read(cam/'CAMERA_RESULT.json') if (cam/'CAMERA_RESULT.json').exists() else None
            if result:
                curves=torus_contours(np.array(result['c2w_mm']),a['K'])
                for curve in curves:axes[1].plot(*curve.T,color='yellow',linewidth=.8)
                ob=observe(a['labels']);q=ob['q_train'];d=cKDTree(curves.reshape(-1,2)).query(q)[0];im=axes[2].scatter(*q.T,c=d,vmin=0,vmax=6,cmap='magma',s=8);fig.colorbar(im,ax=axes[2],label='Observed Ring -> CAD [px]')
                axes[1].set_title('Unchanged RF5DoF + RGB yaw candidate\n'+ad['status']);axes[2].set_title(f'MAE {d.mean():.3f}px; P95 {np.percentile(d,95):.3f}px')
            else:
                axes[1].text(.5,.5,'NO RESOLVED RF CAMERA',ha='center',transform=axes[1].transAxes,color='red');axes[2].text(.5,.5,'Yaw unresolved; no PnP replacement',ha='center',transform=axes[2].transAxes)
            for ax in axes:ax.set_xlim(0,640);ax.set_ylim(360,0);ax.set_xlabel('u [px]');ax.set_ylabel('v [px]')
            fig.suptitle(f"{m['id']} | {m['role']} | RF_ONLY_V1 | {ad['status']} | input {v['cache']['sha256'][:12]}")
            sub=folder/m['video'];sub.mkdir(exist_ok=True);fig.tight_layout();fig.savefig(sub/(m['id']+'_RingFirst.png'));plt.close(fig)
        # Each video has its own displayed Ring frame, never a shared-world claim.
        fig=plt.figure(figsize=(12,5))
        for j,video in enumerate(['004','005']):
            ax=fig.add_subplot(1,2,j+1,projection='3d');full_mesh(ax,ring['V'],ring['F'],'black',.6);points=[];passed=0
            for v in [q for q in ss if q['meta']['video']==video]:
                d=OUT/group/video/'camera'/v['meta']['id'];ad=p.read(d/'ADMISSION.json')
                if not (d/'CAMERA_RESULT.json').exists():continue
                C=np.array(p.read(d/'CAMERA_RESULT.json')['c2w_mm']);points.append(C[:3,3]);passed+=ad['status']=='PASS';ax.scatter(*C[:3,3],c='green' if ad['status']=='PASS' else 'orange',s=16)
            if points:axes3(ax,limits(np.r_[ring['V'],points]))
            else:axes3(ax,[(-10,10),(-10,10),(-10,10)])
            ax.set_title(f'{group}/{video}: own Ring coordinate frame\n{passed} admitted; orange = diagnostic only')
        fig.suptitle('Separate video frames — no certified cross-video transform assumed');fig.tight_layout();fig.savefig(folder/'Figure1_CameraPoses.png');plt.close(fig)
        # Deterministic representative frame, not selected by result quality.
        rep=[v for v in ss if v['meta']['video']=='004' and v['meta']['role']=='FIT'][4];cid=rep['meta']['id'];a=p.check_input(rep);hero=OUT/group/'004/hero'/cid
        __import__('shutil').copy2(folder/'004'/(cid+'_RingFirst.png'),folder/'Figure1_RingFirst.png')
        if (hero/'ADMISSION.json').exists() and p.read(hero/'ADMISSION.json')['status']=='PASS':
            depth=np.load(hero/'HERO_native.npz')['depth_mm'];native=dict(np.load(hero/'RAW_NATIVE_MESH.npz'));valid=np.load(hero/'DEPTH_VALIDITY.npz')['valid'];fig=plt.figure(figsize=(16,4))
            ax=fig.add_subplot(141);ax.imshow(a['RGB']);ax.set_title('Actual target RGB')
            ax=fig.add_subplot(142);im=ax.imshow(depth,vmin=0,vmax=100,cmap='turbo');fig.colorbar(im,ax=ax,label='Axial Z [mm]');ax.set_title('Fresh official HERO raw depth\nScale 0–100mm; out-of-scale pixels '+str(int((depth>100).sum())))
            ax=fig.add_subplot(143);ax.imshow(valid,cmap='gray',vmin=0,vmax=1);ax.set_title('Finite positive raw validity\nNot a statement of depth accuracy')
            ax=fig.add_subplot(144,projection='3d');full_mesh(ax,native['V'],native['F'],'#e67e22');axes3(ax,limits(native['V']));ax.set_title(f"Full raw open Mesh\n{len(native['V'])} V / {len(native['F'])} F")
            fig.suptitle(f'{group}/004 target {cid}; supports fixed offsets 2,4,6; no historical depth');fig.tight_layout();fig.savefig(folder/'Figure2_HERO.png');plt.close(fig)
        else:
            fig,ax=plt.subplots(figsize=(10,3));ax.axis('off');ax.text(.5,.6,group+' HERO NOT_RUN',ha='center',fontsize=18);ax.text(.5,.3,'No admitted same-video Ring-First input; no depth substitute',ha='center');fig.savefig(folder/'Figure2_HERO_NOT_RUN.png');plt.close(fig)
        lim=limits(np.concatenate([b['V'] for b in bodies.values()]));fig=plt.figure(figsize=(15,5))
        for j,arm in enumerate(['B0','B1','B2']):
            if arm in bodies:
                ax=fig.add_subplot(1,3,j+1,projection='3d');b=bodies[arm];full_mesh(ax,b['V'],b['F_solid'],'#8855aa');full_mesh(ax,ring['V'],ring['F'],'black',.5);axes3(ax,lim);ax.set_title(arm+' actual world Mesh\nFixed Ring / no GT alignment')
            else:
                ax=fig.add_subplot(1,3,j+1);ax.axis('off');ax.text(.5,.5,arm+' NOT_RUN',ha='center',fontsize=18)
        fig.suptitle(group+': common view and mm bounds; original world predictions');fig.tight_layout();fig.savefig(folder/'Figure3_Body.png');plt.close(fig)
        # All frozen 004 view projections, including failed HOLDOUT cameras.
        for v in [v for v in ss if v['meta']['video']=='004']:
            m=v['meta'];a=p.check_input(v);fig,axes=plt.subplots(1,3,figsize=(14,4))
            for ax,arm in zip(axes,['B0','B1','B2']):
                ax.imshow(a['RGB']);ax.contour(a['labels']==1,levels=[.5],colors=['lime'],linewidths=.7);pr=evaluation/'projections'/arm/(m['id']+'.npz')
                if pr.exists():
                    rr=dict(np.load(pr));ax.contour(rr['predicted'],levels=[.5],colors=['magenta'],linewidths=.8)
                    item=next(r for r in metrics if r['group']==group and r['arm']==arm and r['id']==m['id']);ax.set_title(arm+' IoU '+str(round(float(item['IoU']),4)))
                else:ax.set_title(arm+' NOT_EVALUABLE — camera or prediction missing',color='red')
                ax.set_xlim(0,640);ax.set_ylim(360,0);ax.axis('off')
            fig.suptitle(m['id']+' '+m['role']+' | green: observed Polyp; magenta: actual Body projection\nRing-contact unknown band excluded identically; no image deformation');fig.tight_layout();fig.savefig(folder/'004'/(m['id']+'_BodyProjection.png'));plt.close(fig)
        # Actual rigid-aligned evaluation copies, same GT and mm view for all arms.
        gt=dict(np.load(c['GT']['path']));aligned={}
        for arm in bodies:
            q=evaluation/(arm+'_GT_ALIGNED.npz')
            if q.exists():aligned[arm]=dict(np.load(q))
        lim=limits(np.concatenate([gt['V']]+[b['V'] for b in aligned.values()]));fig=plt.figure(figsize=(15,5))
        for j,arm in enumerate(['B0','B1','B2']):
            ax=fig.add_subplot(1,3,j+1,projection='3d');full_mesh(ax,gt['V'],gt['F'],'gray',.22)
            if arm in aligned:full_mesh(ax,aligned[arm]['V'],aligned[arm]['F_solid'],'#8844bb',.75)
            axes3(ax,lim);ax.set_title(arm+' + independent GT\n'+('Scale-fixed genuine SE(3)' if arm in aligned else 'NOT_RUN'))
        fig.suptitle(group+': independent shape evaluation copies; transformations never enter training/HERO');fig.tight_layout();fig.savefig(folder/'Figure5_GT_Aligned.png');plt.close(fig)
        if all(a in bodies for a in ['B1','B2']):
            fig=plt.figure(figsize=(12,5))
            for j,arm in enumerate(['B1','B2']):
                b=bodies[arm];values=np.linalg.norm(b['V']-initial['V'],axis=1);ax=fig.add_subplot(1,2,j+1,projection='3d');im=full_mesh(ax,b['V'],b['F_solid'],None,values=values);axes3(ax,limits(initial['V']));ax.set_title(f'{arm} vertex displacement\nMAE {values.mean():.5f} mm / P95 {np.percentile(values,95):.5f} mm');fig.colorbar(im,ax=ax,label='Actual displacement [mm]',shrink=.6)
            fig.suptitle(group+': shared displacement colour scale 0–1mm; no camera update');fig.tight_layout();fig.savefig(folder/'Figure6_Displacement.png');plt.close(fig)
            fig,axes=plt.subplots(1,3,figsize=(15,4))
            for arm,col in [('B1','royalblue'),('B2','firebrick')]:
                updates=p.read(OUT/group/'004/body'/arm/'UPDATES.json');rr=updates['iterations'];axes[0].plot([r['iteration'] for r in rr],[sum(v['IoU'] for v in r['views'])/8 for r in rr],color=col,label=arm);axes[1].plot([r['iteration'] for r in rr],[r['energies']['contour'] for r in rr],color=col,label=arm);axes[2].plot([r['iteration'] for r in rr],[r['HERO_depth'] for r in rr],color=col,label=arm)
            for ax,title in zip(axes,['FIT IoU (8 fixed views)','Actual contour objective','Weighted HERO depth term']):ax.set_title(title);ax.set_xlabel('Fixed outer iteration');ax.legend();ax.grid(alpha=.2)
            fig.suptitle(group+': all 36 accepted/rejected iteration records retained; no checkpoint selection');fig.tight_layout();fig.savefig(folder/'Figure6_Training.png');plt.close(fig)
        index.append(f"- {group}: [Ring-First 每帧](./{group}/004/)、[HERO](./{group}/{'Figure2_HERO.png' if hero.exists() else 'Figure2_HERO_NOT_RUN.png'})、[主体](./{group}/Figure3_Body.png)、[独立 GT 对齐](./{group}/Figure5_GT_Aligned.png)。")
    (VIS/'README.md').write_text('# 静态科学图\n\n全部使用实际输入或冻结 Mesh；未执行项明确标记，无 HTML。每帧 ID、角色、状态在 PNG 标题中。\n\n'+'\n'.join(index)+'\n\n绿色为真实 Polyp 轮廓，紫色为实际 Mesh 投影；GT 仅用于独立评价副本。\n')
    print('STATIC_FINAL_FIGURES',len(list(VIS.rglob('*.png'))),flush=True)

if __name__=='__main__':main()
