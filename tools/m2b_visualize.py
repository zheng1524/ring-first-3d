#!/usr/bin/env python3
"""M2B visual audit: all cameras, complete Ring boundary, 3D trajectories, G03 A0/A1/A2."""
import json,html
from pathlib import Path
import numpy as np,pandas as pd,cv2
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import sys
WS=Path('/home/liu/ring_first_3d_workspace'); OUT=WS/'runs/m2b_ring_global_branch'; VIS=OUT/'visualization'; M1=WS/'runs/m1_final_39'
sys.path[:0]=[str(WS/'src'),str(WS/'camera_mainline/code')]
from ring_first_3d.mainline.native.camera import observe,torus_contours
from ring_first_3d.mainline.native.geometry import project
DF=pd.read_csv(OUT/'W0_79_VIDEO_RESULTS.csv'); DF['video_id']=DF.video_id.astype(int)
COL={'ACCEPT':(60,180,60),'QUARANTINE':(0,140,255),'INSUFFICIENT_EVIDENCE':(255,120,40),'REJECT':(30,30,220)}

def prep_of(g,v):
    r=DF[(DF.group_id==g)&(DF.video_id==int(v))].iloc[0]
    p=Path(r.output_path)
    cand=p/'PREPARED.json'
    if cand.exists(): return r,json.loads(cand.read_text())
    m=r.recovery_method
    if m=='R1': roots=[M1/'prepared']
    elif m=='C3': roots=[OUT/'prepared_c3']
    elif m=='C3B': roots=[OUT/'prepared_c3b']
    else: roots=[OUT/'prepared_c3b',WS/'runs/m2a_w0_recovery/prepared_c2b',WS/'runs/m2a_w0_recovery/prepared_c2',WS/'runs/m2a_w0_recovery/prepared_b1r',WS/'runs/m2a_w0_recovery/prepared_c3']
    for root in roots:
        q=root/f'{g}_{v}'/'PREPARED.json'
        if q.exists(): return r,json.loads(q.read_text())
    raise FileNotFoundError((g,v,m))


def load_packet(r):
    p=Path(r.output_path); w=np.load(p/'W0.npz'); cr=np.load(p/'camera_result.npz'); adm=pd.read_csv(p/'admission.csv')
    return w,cr,adm

def draw_view(r,meta,view_id,c2w,adm,size=(320,180)):
    q=next(x for x in meta['views'] if x['view']==view_id); a=np.load(q['cache']); rgb=a['RGB'].copy(); labels=a['labels']; K=np.asarray(a['K'],float)
    ob=observe(labels,'all'); R=float(meta.get('ring_mm',10.0))/2; wire=.6
    ov=np.zeros_like(rgb); ov[labels==2]=(150,150,150); rgb=cv2.addWeighted(rgb,.72,ov,.28,0)
    for pts,color in [(ob['q_train'],(0,230,80)),(ob['ring_boundary_contact_polyp'],(230,0,220))]:
        for x,y in np.rint(pts).astype(int): cv2.circle(rgb,(int(x),int(y)),1,color,-1)
    try:
        cs=torus_contours(c2w,K,R,wire)
        # identify by area, never assume order
        cs=sorted([np.asarray(c,float) for c in cs],key=lambda c:abs(cv2.contourArea(c.astype(np.float32))))
        for idx,c in enumerate(cs):
            col=(255,210,0) if idx==0 else (0,150,255)  # smaller cyan-like BGR, larger orange
            cv2.polylines(rgb,[np.rint(c).astype(np.int32)],True,col,2)
        th=np.linspace(0,2*np.pi,360); P=np.c_[R*np.cos(th),R*np.sin(th),np.zeros(360)]; uv,z=project(P,c2w,K); ok=z>0
        if ok.sum()>1: cv2.polylines(rgb,[np.rint(uv[ok]).astype(np.int32)],False,(0,220,255),1)
    except Exception as e:
        cv2.putText(rgb,'CAD_INVALID',(8,40),cv2.FONT_HERSHEY_SIMPLEX,.5,(0,0,255),1)
    ar=adm[adm.view.astype(str)==str(view_id)]
    st=ar.admission_status.iloc[0] if len(ar) else 'NO_ADMISSION'; reason=ar.admission_reasons.iloc[0] if len(ar) and pd.notna(ar.admission_reasons.iloc[0]) else ''
    rmae=ar.ring_raw_mae.iloc[0] if len(ar) else np.nan; hm=ar.held_median.iloc[0] if len(ar) else np.nan; hp=ar.held_p95.iloc[0] if len(ar) else np.nan
    return cv2.resize(rgb,size),st,reason,rmae,hm,hp

def contact_sheet(r):
    g=str(r.group_id); v=f'{int(r.video_id):03d}'; w,cr,adm=load_packet(r); meta=json.loads((Path(r.output_path)/'PREPARED.json').read_text()) if (Path(r.output_path)/'PREPARED.json').exists() else prep_of(g,v)[1]
    ids=[str(x) for x in cr['ids']]; cams=np.asarray(cr['c2w'],float)
    thumbs=[]
    for i,view in enumerate(ids):
        th,st,reason,rmae,hm,hp=draw_view(r,meta,view,cams[i],adm)
        band=np.full((52,320,3),245,np.uint8); cv2.putText(band,f'{view.split("-")[-1]} {st[:18]}',(4,15),cv2.FONT_HERSHEY_SIMPLEX,.38,(20,20,20),1)
        cv2.putText(band,f'R {rmae:.2f} H {hm:.1f}/{hp:.1f}' if np.isfinite(hm) else f'R {rmae:.2f} H NA',(4,31),cv2.FONT_HERSHEY_SIMPLEX,.34,(40,40,40),1)
        cv2.putText(band,reason[:42],(4,46),cv2.FONT_HERSHEY_SIMPLEX,.3,(60,60,60),1)
        thumbs.append(np.vstack([th,band]))
    cols=2; rows=(len(thumbs)+1)//2; sheet=np.full((70+rows*232,640,3),255,np.uint8)
    cv2.putText(sheet,f'{g}/{v} {r.ring_type} {r.recovery_method} W0={r.new_w0_poses} ACC={r.new_accept}',(6,22),cv2.FONT_HERSHEY_SIMPLEX,.42,(0,0,0),1)
    cv2.putText(sheet,'green=q_train complete boundary; magenta=Ring-Polyp contact; cyan/orange=CAD inner/outer; yellow=centerline',(6,44),cv2.FONT_HERSHEY_SIMPLEX,.3,(40,40,40),1)
    for i,t in enumerate(thumbs):
        y=64+(i//2)*232; x=(i%2)*320; sheet[y:y+232,x:x+320]=t
    d=VIS/'C_nonaccept_w0'/'per_video_contact_sheets'; d.mkdir(parents=True,exist_ok=True); p=d/f'{g}_{v}.png'; cv2.imwrite(str(p),sheet); return p

def torus(R=5.6,r=.6):
    u=np.linspace(0,2*np.pi,70); vv=np.linspace(0,2*np.pi,32); U,V=np.meshgrid(u,vv)
    return (R+r*np.cos(V))*np.cos(U),(R+r*np.cos(V))*np.sin(U),r*np.sin(V)

def camera3d(r,path=None):
    w,cr,adm=load_packet(r); C=np.asarray(cr['c2w'],float); ids=[str(x) for x in cr['ids']]; ad=dict(zip(adm.view.astype(str),adm.admission_status.astype(str)))
    _,meta=prep_of(str(r.group_id),f'{int(r.video_id):03d}'); X,Y,Z=torus(float(meta.get('ring_mm',10.0))/2,.6); lim=max(12,float(np.abs(C[:,:3,3]).max())*1.15)
    fig,axes=plt.subplots(2,2,figsize=(8,7),subplot_kw={'projection':'3d'})
    for ax,(e,a,nm) in zip(axes.ravel(),[(22,-62,'Perspective'),(90,-90,'Top'),(0,-90,'Side'),(0,0,'Front')]):
        ax.plot_surface(X,Y,Z,color='#9e9e9e',alpha=.33,linewidth=0)
        for i,T in enumerate(C):
            col=np.array(COL.get(ad.get(ids[i],''),'#777'))[::-1]/255.; c=T[:3,3]; ax.scatter(*c,c=[col],s=22,depthshade=False); ax.quiver(*c,*(T[:3,2]*2.5),color=col,arrow_length_ratio=.3,lw=.8)
        ax.plot(C[:,0,3],C[:,1,3],C[:,2,3],c='#333',lw=.8,alpha=.7)
        for i in range(len(C)-1):
            dR=np.degrees(np.arccos(np.clip((np.trace(C[i,:3,:3].T@C[i+1,:3,:3])-1)/2,-1,1))); dt=np.linalg.norm(C[i+1,:3,3]-C[i,:3,3])
            if dR>10 or dt>5: ax.plot(C[i:i+2,0,3],C[i:i+2,1,3],C[i:i+2,2,3],c='red',lw=2)
        ax.set_xlim(-lim,lim); ax.set_ylim(-lim,lim); ax.set_zlim(-lim,lim); ax.set_box_aspect((1,1,1)); ax.view_init(e,a); ax.set_title(nm,fontsize=7); ax.tick_params(labelsize=5)
    fig.suptitle(f'{r.group_id}/{int(r.video_id):03d} {r.ring_type} {r.recovery_method} W0={r.new_w0_poses} ACC={r.new_accept} maxRot={r.max_adjacent_rotation_deg:.1f}',fontsize=7)
    if path is None:
        d=VIS/'D_camera_ring_3d'/'per_video'; d.mkdir(parents=True,exist_ok=True); path=d/f'{r.group_id}_{int(r.video_id):03d}.png'
    fig.tight_layout(); fig.savefig(path,dpi=90); plt.close(fig); return path

def g03_compare():
    g='GP_Ip_20.0mm_closed_R10_single_refY'; paths=[]
    for v in ['004','005']:
        fig,axes=plt.subplots(1,3,figsize=(13,4.6),subplot_kw={'projection':'3d'})
        for ax,(method,root) in zip(axes,[('A0 M2A',None),('A1 Ring',OUT/'g03_A1'/g/v),('A2 Global',OUT/'g03_A2'/g/v)]):
            if root is None:
                r=DF[(DF.group_id=='GP_Ip_20.0mm_closed_R10_single_refY')&(DF.video_id==int(v))].iloc[0]
                # A0 source M2A path
                p=WS/'runs/m2a_w0_recovery'/('recovery/C1' if v=='005' else 'recovery/C3')/g/v
                if not (p/'camera_result.npz').exists(): p=WS/'runs/m1_final_39'/g/v
            else: p=root
            cr=np.load(p/'camera_result.npz'); C=np.asarray(cr['c2w'],float); X,Y,Z=torus(5.6,.6); lim=max(12,float(np.abs(C[:,:3,3]).max())*1.15)
            ax.plot_surface(X,Y,Z,color='#9e9e9e',alpha=.3,linewidth=0); ax.plot(C[:,0,3],C[:,1,3],C[:,2,3],c='#333',lw=1)
            for i,T in enumerate(C): ax.scatter(*T[:3,3],s=16,c='#1f77b4'); ax.quiver(*T[:3,3],*(T[:3,2]*2.5),arrow_length_ratio=.25,lw=.7,color='#1f77b4')
            ax.set_xlim(-lim,lim); ax.set_ylim(-lim,lim); ax.set_zlim(-lim,lim); ax.set_box_aspect((1,1,1)); ax.view_init(22,-62); ax.set_title(method,fontsize=7); ax.tick_params(labelsize=5)
        d=VIS/'B_global_branch'/'G03_detailed'; d.mkdir(parents=True,exist_ok=True); p=d/f'G03_{v}_A0_A1_A2.png'; fig.tight_layout(); fig.savefig(p,dpi=120); plt.close(fig); paths.append(p)
    return paths

def ring_compare():
    rows=[]
    for g,v in [('GP_IIa_14.0mm_closed_R5_single_refY','005'),('GP_IIa_22.0mm_closed_R5_single_refY','004'),('GP_IIa_22.0mm_closed_R5_single_refY','005'),('GP_Is_18.0mm_closed_R5_single_refY','005')]:
        meta=json.loads((M1/'prepared'/f'{g}_{v}'/'PREPARED.json').read_text()); q=meta['views'][0]; a=np.load(q['cache']); rgb=a['RGB']; labels=a['labels']; o0=observe(labels,'legacy'); o1=observe(labels,'all')
        imgs=[]
        for ob,txt in [(o0,'R0 legacy: q_train=%d'%len(o0['q_train'])),(o1,'R1 complete: q_train=%d'%len(o1['q_train']))]:
            im=rgb.copy(); ov=np.zeros_like(im); ov[labels==2]=(150,150,150); im=cv2.addWeighted(im,.7,ov,.3,0)
            for x,y in np.rint(ob['q_train']).astype(int): cv2.circle(im,(int(x),int(y)),1,(0,230,80),-1)
            for x,y in np.rint(ob['ring_boundary_contact_polyp']).astype(int): cv2.circle(im,(int(x),int(y)),1,(230,0,220),-1)
            cv2.putText(im,txt,(8,20),cv2.FONT_HERSHEY_SIMPLEX,.45,(0,0,0),1); imgs.append(im)
        sheet=np.hstack([cv2.resize(x,(480,270)) for x in imgs]); d=VIS/'A_ring_observation'/'complete_boundary_before_after'; d.mkdir(parents=True,exist_ok=True); p=d/f'{g}_{v}.png'; cv2.imwrite(str(p),sheet); rows.append(p)
    return rows

def main():
    for d in ['A_ring_observation/complete_boundary_before_after','A_ring_observation/ring_polyp_contact_examples','B_global_branch/G03_detailed','B_global_branch/trajectory_before_after','C_nonaccept_w0/per_video_contact_sheets','C_nonaccept_w0/quarantine','C_nonaccept_w0/insufficient','D_camera_ring_3d/per_video','D_camera_ring_3d/branch_risk','E_summary']:
        (VIS/d).mkdir(parents=True,exist_ok=True)
    ring_compare()
    sheets=[]; cams=[]
    for _,r in DF.iterrows():
        p=contact_sheet(r); sheets.append((r,p)); cams.append(camera3d(r))
        if (r.max_adjacent_rotation_deg or 0)>30 or (r.trajectory_jump_count or 0)>=5:
            import shutil; shutil.copyfile(p,VIS/'C_nonaccept_w0'/'quarantine'/p.name); shutil.copyfile(cams[-1],VIS/'D_camera_ring_3d'/'branch_risk'/cams[-1].name)
    # HTML index
    rows=[]
    for idx,(r,p) in enumerate(sheets):
        rows.append(f'<tr><td>{html.escape(str(r.group_id))}</td><td>{int(r.video_id):03d}</td><td>{r.recovery_method}</td><td>{int(r.new_w0_poses)}</td><td>{int(r.new_accept or 0)}</td><td><a href="C_nonaccept_w0/per_video_contact_sheets/{p.name}">2D all cameras</a></td><td><a href="D_camera_ring_3d/per_video/{cams[idx].name}">3D</a></td></tr>')
    htmltxt='<html><head><meta charset="utf-8"><title>M2B non-ACCEPT W0 index</title></head><body><h2>M2B all W0 cameras — 2D + 3D visual index</h2><p>Every camera is shown; non-ACCEPT is not hidden. Status colors: green ACCEPT, orange QUARANTINE, blue INSUFFICIENT, red REJECT.</p><table border=1 cellpadding=3><tr><th>group</th><th>video</th><th>method</th><th>W0</th><th>ACCEPT</th><th>2D</th><th>3D</th></tr>'+''.join(rows)+'</table></body></html>'
    (VIS/'NONACCEPT_INDEX.html').write_text(htmltxt)
    g03_compare()
    print('sheets',len(sheets),'cameras',len(cams),'index',VIS/'NONACCEPT_INDEX.html')

if __name__=='__main__': main()
