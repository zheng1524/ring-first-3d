from pathlib import Path
import json,hashlib,shutil
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from ring_first_3d.synthetic.io import fetch
from ring_first_3d.sim.legacy import namespace
from ring_first_3d.sim.geometry import contour
from ring_first_3d.synthetic.raster import ray_map
from ring_first_3d.policy.contracts import load_task
root=Path.cwd();td=root/'experiments/TASK-E4-G01-DUALVIDEO-BODY-ANCHORED-REGISTRATION-001-SIM-PROTOCOL-REV1';run=td/'runs/SIM_REV1_001';task=load_task(td/'TASK.yaml');ns=namespace(task)
frames=json.loads(fetch(run,'G0_simulate','public/frame_index.json').read_text());fits=json.loads(fetch(run,'G1_initialize','IMAGE_FITS.json').read_text());body=dict(np.load(fetch(run,'G1_initialize','FROZEN_BODY.npz')));ring=dict(np.load(fetch(run,'G0_simulate','public/canonical_ring.npz')));g0=json.loads(fetch(run,'G0_simulate','G0_SCENE_AUDIT.json').read_text());quality={r['source_id']:r for r in g0['realism_quality']};reps=[next(r for r in frames if r['video']==v and r['role']==role)for v in ['004','005']for role in ['FIT','HOLDOUT']]
fig1,axes1=plt.subplots(2,2,figsize=(13,9),layout='constrained');fig2,axes2=plt.subplots(2,2,figsize=(13,9),layout='constrained')
for row,ax,bx in zip(reps,axes1.ravel(),axes2.ravel()):
 cid=row['id'];obs=np.load(fetch(run,'G0_simulate','public/initialization/'+cid+'.npz'));fit=next(r for r in fits if r['id']==cid and r['domain']=='real_source');maps=np.load(fetch(run,'G2_mapping','maps/real_source__'+cid+'__MEDIATED.npz'))
 projection=ray_map(ring['V'],ring['F'],obs['K'],obs['C'],(360,640))['valid'];q=quality[row['source_id']]
 ax.imshow(obs['real_RGB']);ax.contour(obs['real_labels']==2,levels=[.5],colors=['lime'],linewidths=.8);ax.contour(projection,levels=[.5],colors=['magenta'],linewidths=.8);ax.plot([],[],c='lime',label='Real observed Ring');ax.plot([],[],c='magenta',label='Full R10 native-pose projection');ax.legend(fontsize=7)
 ax.set_title(f'{row["source_id"]} | {row["role"]}\nSupport@2px {q["support_within2px"]:.4f}; boundary p95 {q["observed_to_CAD_boundary_p95_px"]:.3f}px',fontsize=9)
 bx.imshow(obs['real_RGB']);uv=contour(obs['real_labels']==1);bx.plot(uv[:,0],uv[:,1],'.',c='lime',ms=.4,label='Real source contour')
 theta=np.linspace(0,2*np.pi,256);ellipse=np.c_[np.cos(theta),np.sin(theta)]@np.asarray(fit['basis_px']).T+fit['center_px'];bx.plot(ellipse[:,0],ellipse[:,1],c='magenta',lw=1,label=fit['mapping_fit']);curve=maps['body_curve'];bx.plot(curve[:,0],curve[:,1],c='gray',lw=1,label='Frozen virtual Body projection')
 good=maps['valid'];mapped=maps['mapped_uv'];bx.scatter(mapped[good,0],mapped[good,1],c=maps['confidence'][good],vmin=0,vmax=1,cmap='viridis',s=6);bx.scatter(mapped[~good,0],mapped[~good,1],c='magenta',marker='x',s=10,label='No Body face');bx.legend(fontsize=6)
 bx.set_title(f'{row["source_id"]} / {row["role"]}\nPose {row["pose_sha256"][:12]}; no injected error; virtual-ray diagnostic only',fontsize=9)
 for a in [ax,bx]:a.set(xlim=(0,639),ylim=(359,0),xlabel='native x [px]',ylabel='native y [px]')
fig1.suptitle('True source Camera-to-Ring / R10 audit | Realism quality only; no re-fit or deployment certification',fontsize=11);fig1.savefig(td/'visualization/figures/REAL_CAMERA_RING_AUDIT.png',dpi=110);plt.close(fig1)
fig2.suptitle('Real source contour -> frozen API ellipse -> shared virtual Body candidate region | G01-like, not physical GT',fontsize=11);fig2.savefig(td/'visualization/figures/REAL_CONTOUR_ELLIPSE_BODY.png',dpi=110);plt.close(fig2)
fig,ax=plt.subplots(figsize=(8,1.6),layout='constrained');fig.colorbar(plt.cm.ScalarMappable(norm=Normalize(0,1),cmap='turbo'),cax=ax,orientation='horizontal',label='Independent GT surface distance [mm], fixed 004 gauge; values >=1mm saturate; uncapped numeric maxima retained');fig.savefig(td/'visualization/figures/GT_ERROR_COLORBAR.png',dpi=120);plt.close(fig)
# Only visualization, based entirely on already frozen public camera matrices and meshes.
fig=plt.figure(figsize=(13,6),layout='constrained');ax=fig.add_subplot(121,projection='3d');bx=fig.add_subplot(122,projection='3d')
for a in [ax,bx]:
 a.add_collection3d(Poly3DCollection(body['V'][body['F']],facecolors='#999999',alpha=.16,linewidths=0));a.add_collection3d(Poly3DCollection(ring['V'][ring['F']],facecolors='#111111',alpha=.9,linewidths=0));a.set(xlabel='X [mm]',ylabel='Y [mm]',zlabel='Z [mm]');a.view_init(24,-70)
for v,col in [('004','#cc263c'),('005','#2377c9')]:
 cameras=[]
 for row in frames:
  if row['video']!=v:continue
  obs=np.load(fetch(run,'G0_simulate','public/initialization/'+row['id']+'.npz'));C=obs['C'];cameras.append(C[:3,3]);p=C[:3,3];tip=p+C[:3,2]*4
  ax.plot(*np.array([p,tip]).T,c=col,lw=.7)
 cameras=np.array(cameras);ax.plot(*cameras.T,'o',ms=2,color=col,label=v+' original native cameras')
 clean=np.load(fetch(run,'G0_simulate','private/'+v+'_clean.npz'));bx.add_collection3d(Poly3DCollection(clean['V'][clean['F']],facecolors=col,alpha=.75,linewidths=0))
ax.set(xlim=(-40,40),ylim=(-40,40),zlim=(-16,45));ax.set_box_aspect([80,80,61]);ax.legend(fontsize=8);ax.set_title('Original distinct 004/005 camera sources; unified virtual Ring')
bx.set(xlim=(-10,10),ylim=(-10,10),zlim=(-16,9));bx.set_box_aspect([20,20,25]);bx.set_title('Actual full local meshes around frozen coarse Body / R10')
fig.suptitle('G01_LIKE_SIMULATION | shared static GT placement [0,0,-4]mm; original geometry size unchanged; not certified real deployment',fontsize=10);fig.savefig(td/'visualization/figures/VIRTUAL_CAMERA_RING_FULL_MESH.png',dpi=110);plt.close(fig)
add=[('REAL_CAMERA_RING_AUDIT.png','真实原图Ring与原生相机CAD投影差异'),('REAL_CONTOUR_ELLIPSE_BODY.png','真实轮廓、已冻结API椭圆及虚拟Body候选区域'),('VIRTUAL_CAMERA_RING_FULL_MESH.png','真实双轨迹来源在声明的共同虚拟坐标系和完整局部曲面'),('GT_ERROR_COLORBAR.png','所有GT表面误差图共享Turbo色标0–1+mm')]
p=td/'visualization/index.html';s=p.read_text();extra=''.join(f'<h2>{caption}</h2><img loading="lazy" src="figures/{name}" alt="{caption}">'for name,caption in add);s=s.replace('</html>',extra+'</html>');p.write_text(s)
p=td/'TECHNICAL_REPORT.md';s=p.read_text();s+='\n## 冻结后只读审阅补充\n\n下列图仅导出已冻结的源图、二维候选、相机、Body和完整Mesh；没有新增DXY评估、拟合、优化或GT选参。完整Runner快照保留。\n\n';s+='\n'.join(f'- [{caption}](visualization/figures/{name})'for name,caption in add)+'\n';p.write_text(s)
p=td/'PRESENTATION_RECEIPT.json';x=json.loads(p.read_text());x['extra_figures']='Read-only plots of already frozen original RGB/Ring projection, existing ellipse/body candidates, camera sources and shared numerical colorbar; no new DXY or optimization';p.write_text(json.dumps(x,indent=2)+'\n')
print('Additional read-only evidence plots',len(add))
