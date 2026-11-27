"""Read-only mask replay and compact evidence using retained native observers/renderers."""
from pathlib import Path
import argparse,json,sys
import cv2,numpy as np
from ring_first_3d.v6_raw.full_run import read,atomic_json,table,hash_file
W=Path('/home/liu/ring_first_3d_workspace');WT=Path(__file__).resolve().parents[1];TASK='TASK-V6-FRONTEND-RECOVERY-AND-PHOTO-PILOT-001';T=WT/'experiments'/TASK;O=W/'runs/v6_frontend_photo_pilot_001';B=W/'runs/v6_full_run_001'
def replay():
 from ring_first_3d.v6_raw.frontend_kernels import corrected_observation
 from ring_first_3d.mainline.native.camera import observe
 from ring_first_3d.v6_raw.visualize import plt
 (T/'figures').mkdir(exist_ok=True);rows=[];chosen=None
 for video in read(T/'evidence/ALL79_120_MANIFEST.json')['videos']:
  case=video['case'];s=read(B/'states'/(case+'.json'));R=Path(s['run_path']);L=read(R/'inputs/INPUT_IDENTITY.json')['frames']
  for a in L:
   assert hash_file(a['Mask_path'])==a['Mask_SHA256'];label=cv2.imread(a['Mask_path'],0);old=dict(np.load(R/'v5raw/observations'/(a['id']+'.npz')));new,d=corrected_observation(label,old);native=observe(label,ring_mode='all')
   q=np.r_[new['ring_train'],new['ring_heldout']];q=q[np.lexsort((q[:,0],q[:,1]))];q=q[np.linspace(0,len(q)-1,min(len(q),256),dtype=int)] if len(q) else q;held=np.arange(len(q))%5==0;new.update(q_train=q[~held],q_held=q[held])
   rows.append(dict(case=case,view=a['id'],raw_frame=a['raw_frame'],mask_sha256=hash_file(a['Mask_path']),old_q_train=len(old['q_train']),old_q_held=len(old['q_held']),new_q_train=len(new['q_train']),new_q_held=len(new['q_held']),actual_q_changed=not(np.array_equal(old['q_train'],new['q_train']) and np.array_equal(old['q_held'],new['q_held'])),region_train_points=len(old['p_train']),region_held_points=len(old['p_held']),background_train_points=len(old['b_train']),**d))
   if case=='GP_Is_18.0mm_closed_R5_single_refY_005' and chosen is None:chosen=(a,label,old,new,native,rows[-1])
 table(T/'evidence/ALL79_MASK_REPLAY.csv',rows)
 summary=dict(videos=len({r['case'] for r in rows}),views=len(rows),actual_q_changed_views=sum(r['actual_q_changed'] for r in rows),count_changed_views=sum(r['old_q_train']!=r['new_q_train'] or r['old_q_held']!=r['new_q_held'] for r in rows),old_empty=sum(r['old_q_train']==0 for r in rows),new_empty=sum(r['new_q_train']==0 for r in rows),replay_only_no_camera_or_HERO=True)
 atomic_json(T/'evidence/MASK_REPLAY_SUMMARY.json',summary)
 a,lab,old,new,native,d=chosen;rgb=cv2.cvtColor(cv2.imread(a['RGB_path']),cv2.COLOR_BGR2RGB);fig,axs=plt.subplots(2,2,figsize=(13,8))
 axs[0,0].imshow(rgb);axs[0,0].set_title('真实RGB / RAW '+str(a['raw_frame']))
 axs[0,1].imshow(lab,vmin=0,vmax=2,cmap='viridis');axs[0,1].set_title('实际INIT Mask：背景0 / 息肉1 / Ring2')
 for ax,ob,title in [(axs[1,0],old,'旧规则：邻息肉关系剔除了真实Ring边界'),(axs[1,1],new,'新规则：真实Ring边界保留，邻接仅作诊断')]:
  ax.imshow(rgb)
  for key,color,name in [('q_train','cyan','实际训练q'),('q_held','red','实际留出q')]:
   q=ob[key];ax.scatter(q[:,0],q[:,1],s=6,c=color,label=f'{name}={len(q)}')
  q=native['ring_boundary_contact_polyp'];ax.scatter(q[:,0],q[:,1],s=1,c='yellow',alpha=.3,label='邻息肉真实边界')
  ax.set_title(title);ax.legend(fontsize=8)
 for ax in axs.flat:ax.axis('off')
 fig.suptitle('Is18 / R5 / 005：观测语义修正（尚不代表相机或HERO恢复）\n独立遮挡证据未提供；邻接排除0；不填绘图像边缘、不以CAD点替代观测。Ring像素边界数='+str(d['raw_boundary_count'])+f"；区域p训练/留出={d['region_train_points']}/{d['region_held_points']}；背景b训练={d['background_train_points']}",fontsize=10)
 fig.tight_layout(rect=(0,0,1,.91));fig.savefig(T/'figures/RING_BEFORE_AFTER.png',dpi=115);plt.close(fig);print(summary,flush=True)
if __name__=='__main__':replay()
