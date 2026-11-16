"""Actual frozen geometry/correspondence figures, shared mm axes and color scales."""
import csv
import json
from pathlib import Path
import numpy as np
from .io import fetch,stage_record,save_json,outputs
from .correspondence import METHODS
from ..contracts.coordinates import unproject


def render(task,attempt):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import Normalize
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    root=attempt.parents[1];sc=task["science"];figdir=attempt/"figures";figdir.mkdir()
    body=np.load(fetch(root,"G0_prepare","public/initial_body.npz"));truth=np.load(fetch(root,"G0_prepare","private/g01_mesh.npz"));ring=np.load(fetch(root,"G0_prepare","public/ring.npz"))
    V,F=truth["V"],truth["F"];cameras=json.loads(fetch(root,"G0_prepare","private/cameras.json").read_text())
    records=[];titles={};allrows=[];table=[]
    def save(fig,name,title):
        fig.suptitle(title,fontsize=10);fig.savefig(figdir/name,dpi=120,bbox_inches="tight");plt.close(fig);titles[name]=title
    def mesh(ax,wide=False):
        ax.add_collection3d(Poly3DCollection(V[F],facecolors="#8b9eaa",edgecolors="none",alpha=.3))
        ax.add_collection3d(Poly3DCollection(ring["V"][ring["F"][::16]],facecolors="#15191f",edgecolors="none",alpha=.6))
        lim=45 if wide else 12
        ax.set(xlim=(-lim,lim),ylim=(-lim,lim),zlim=(-lim,lim),xlabel="World X [mm]",ylabel="World Y [mm]",zlabel="World Z [mm]")
        ax.view_init(25,-60);ax.set_box_aspect((1,1,1))
    fig=plt.figure(figsize=(12,5));ax=fig.add_subplot(121,projection="3d");mesh(ax,True)
    for cam in cameras:
        T=np.array(cam["T"]);K=np.array(cam["K"]);C=T[:3,3]
        color="#d75145"if cam["role"]=="FIT"else"#e49825"
        ax.scatter(*C,color=color,s=25);ax.text(*C,cam["id"].replace("G01_004_",""),fontsize=6)
        corners=unproject(np.array([[0,0],[319,0],[319,179],[0,179]]),np.full(4,12.),K,T)
        for p in corners:ax.plot(*np.stack([C,p]).T,color=color,lw=.6)
        ax.plot(*np.vstack([corners,corners[0]]).T,color=color,lw=.6)
    ax.set_title("Genuine GT + R10 CAD + frozen FIT/HOLDOUT cameras")
    ax=fig.add_subplot(122,projection="3d");mesh(ax);ax.scatter(*body["V"][::10].T,s=2,color="#387fca",label="Controlled initial Body = same real GT mesh")
    ax.legend(fontsize=7);ax.set_title("Synthetic author-world placement; no deployed-pose claim")
    save(fig,"01_scene.png","G01 spec_01p-12- | Blender METRIC x1000 -> mm | GT 1857 vertices / Ring R10 | no fitted alignment")
    fig=plt.figure(figsize=(12,5))
    for ci,zoom in enumerate([False,True]):
        ax=fig.add_subplot(1,2,ci+1,projection="3d")
        if not zoom:mesh(ax,True)
        for camera in cameras[:1]:
            T=np.array(camera["T"]);pr=np.load(fetch(root,"C3_predict","predictions/"+camera["id"]+".npz"));pert=pr["T_estimated"]
            for pose,color,label in [(T,"#2168af","True camera"),(pert,"#d34893","C3 estimated camera")]:
                C=pose[:3,3];ax.scatter(*C,color=color,s=30,label=label)
                for k in range(3):ax.quiver(*C,*(pose[:3,k]*5),length=1,normalize=False,color=color,linewidth=1)
            delta=pert[:3,3]-T[:3,3];ax.quiver(*T[:3,3],*delta,length=1,normalize=False,color="black",linewidth=2)
            if zoom:
                C=T[:3,3];ax.set(xlim=(C[0]-2,C[0]+6),ylim=(C[1]-2,C[1]+6),zlim=(C[2]-2,C[2]+6),xlabel="World X [mm]",ylabel="World Y [mm]",zlabel="World Z [mm]")
                ax.view_init(25,-60);ax.set_box_aspect((1,1,1))
        ax.legend(fontsize=7);ax.set_title("C3 actual right-local pose before/after"if not zoom else"Same fixed 3D view; 5 mm frame axes")
    save(fig,"07_camera_pose_injection.png",f"{cameras[0]['id']} | C3 local Ry=2 deg, tx=0.5 mm | black origin displacement at scale x1; Body/Ring fixed")
    fig=plt.figure(figsize=(15,10))
    for ri,condition in enumerate(sc["condition_order"]):
        cid=cameras[0]["id"];obs=np.load(fetch(root,"G0_prepare","public/C0/"+cid+".npz"));ev=np.load(fetch(root,condition+"_evaluate","evaluation/"+cid+".npz"));pr=np.load(fetch(root,condition+"_predict","predictions/"+cid+".npz"))
        Ptrue=ev["P_true"];Pobs=pr["P_obs"];ix=np.linspace(0,len(Ptrue)-1,min(90,len(Ptrue))).astype(int)
        ax=fig.add_subplot(3,3,ri*3+1,projection="3d");mesh(ax)
        ax.scatter(*Ptrue[ix].T,s=4,color="#287b9e");ax.scatter(*Pobs[ix].T,s=4,color="#e26943")
        d=Pobs[ix]-Ptrue[ix];ax.quiver(*Ptrue[ix].T,*d.T,length=1,normalize=False,color="#d73d43",linewidth=.6)
        cfg=sc["conditions"][condition];ax.set_title(f"{condition}: z+{cfg['depth_bias_mm']}mm; Ry {cfg['rotation_y_deg']}deg; tx {cfg['translation_x_mm']}mm",fontsize=8)
        for col,values,title in [(2,np.linalg.norm(Pobs-Ptrue,axis=1),"Injected world displacement [mm]"),(3,ev["pixel_face_error_mm"],"Pixel-Face material error [mm]")]:
            ax=fig.add_subplot(3,3,ri*3+col);image=np.full((180,320),np.nan);x,y=obs["uv"].astype(int).T;image[y,x]=values
            h=ax.imshow(image,vmin=0,vmax=2,cmap="inferno");ax.set_title(title,fontsize=8);ax.set(xlabel="Working x [px]",ylabel="Working y [px]");fig.colorbar(h,ax=ax,shrink=.7,extend="max")
    save(fig,"02_injected_layers.png",f"{cameras[0]['id']} | C0/C1/C3 same 3D view, arrows at physical scale x1 | all error colorbars 0–2+ mm")
    methods=[*METHODS,"oracle_true_camera"]
    for condition in sc["condition_order"]:
        _,metrics=stage_record(root,condition+"_evaluate");rows=metrics["rows"];allrows+=rows
        fig,axes=plt.subplots(len(cameras),4,figsize=(15,11),layout="constrained")
        for ri,cam in enumerate(cameras):
            cid=cam["id"];obs=np.load(fetch(root,"G0_prepare","public/C0/"+cid+".npz"));ev=np.load(fetch(root,condition+"_evaluate","evaluation/"+cid+".npz"));private=np.load(fetch(root,"G0_prepare","private/"+cid+".npz"));x,y=obs["uv"].astype(int).T
            for ci,method in enumerate(methods):
                ax=axes[ri,ci];err=ev[method+"_error_mm"];valid=ev[method+"_valid"]
                rgba=np.zeros((180,320,4));rgba[...,3]=1;rgba[private["ring_hidden"]]=[.2,.2,.2,1]
                rgba[y[valid],x[valid]]=plt.cm.inferno(np.clip(err[valid]/2,0,1));rgba[y[~valid],x[~valid]]=[1.,0.,1.,1.]
                ax.imshow(rgba);r=next(r for r in rows if r["view_id"]==cid and r["method"]==method)
                ax.set_title(f"{method}\n{r['independent_numeric_N']}/{r['target_N']} MAE {r['MAE_mm']:.4f} p95 {r['p95_mm']:.4f} mm",fontsize=7)
                ax.set(xlabel="Working x [px]",ylabel=cid+"\n"+cam["role"])
        fig.colorbar(plt.cm.ScalarMappable(norm=Normalize(0,2),cmap="inferno"),ax=axes,shrink=.75,label="3D material correspondence error [mm], shared 0–2+",extend="max")
        save(fig,f"03_errors_{condition}.png",f"G01 {condition} {sc['conditions'][condition]} | magenta=unmatched observed target; gray=Ring-hidden GT, excluded from observed denominator | no hidden failures")
    # Pixel -> face/barycentric -> actual world point audit, same anchor pixels.
    cid=cameras[0]["id"];obs=np.load(fetch(root,"G0_prepare","public/C0/"+cid+".npz"));selected=np.linspace(0,len(obs["uv"])-1,12).astype(int)
    fig,axes=plt.subplots(2,3,figsize=(14,7),layout="constrained")
    for ri,condition in enumerate(["C1","C3"]):
        pr=np.load(fetch(root,condition+"_predict","predictions/"+cid+".npz"));ev=np.load(fetch(root,condition+"_evaluate","evaluation/"+cid+".npz"));x,y=obs["uv"].astype(int).T
        images=[]
        valid=pr["pixel_face_valid"]
        image=np.full((180,320),np.nan);image[y[valid],x[valid]]=pr["pixel_face_face"][valid];images.append((image,"Body Face ID (fixed topology)","turbo",0,len(F)))
        baryimage=np.zeros((180,320,3));baryimage[y[valid],x[valid]]=np.clip(pr["pixel_face_bary"][valid],0,1);baryimage[y[~valid],x[~valid]]=[1,0,1]
        for col in [0,1]:
            ax=axes[ri,col]
            if col==0:
                h=ax.imshow(image,vmin=0,vmax=len(F),cmap="turbo");fig.colorbar(h,ax=ax,shrink=.65,label="Face ID")
                ax.scatter(x[~valid],y[~valid],s=.3,c="magenta")
            else:ax.imshow(baryimage)
            ax.set_title(condition+(" Face ID"if col==0 else" barycentric RGB = (b0,b1,b2)"));ax.set(xlabel="Working x [px]",ylabel="Working y [px]")
            for k,ix in enumerate(selected):ax.text(*obs["uv"][ix],str(k),fontsize=6,color="white",bbox=dict(facecolor="black",alpha=.6,pad=.2))
        axes[ri,2].axis("off")
        lines=[]
        for k,ix in enumerate(selected):
            uv=obs["uv"][ix];Q=pr["pixel_face_points"][ix];bary=pr["pixel_face_bary"][ix];face=int(pr["pixel_face_face"][ix])
            lines.append(f"{k:02d} uv {uv} f{face} b{np.round(bary,2)}\n   XYZmm {np.round(Q,3)} err {ev['pixel_face_error_mm'][ix]:.3f}")
            for method in METHODS:
                q=pr[method+"_points"][ix];b=pr[method+"_bary"][ix]
                table.append(dict(condition=condition,source_id=cid,pixel_index=int(ix),working_u=int(uv[0]),working_v=int(uv[1]),native_u=float((uv[0]+.5)*2-.5),native_v=float((uv[1]+.5)*2-.5),method=method,valid=bool(pr[method+"_valid"][ix]),face=int(pr[method+"_face"][ix]),b0=float(b[0]),b1=float(b[1]),b2=float(b[2]),X_mm=float(q[0]),Y_mm=float(q[1]),Z_mm=float(q[2]),material_error_mm=float(ev[method+"_error_mm"][ix])))
        axes[ri,2].text(0,1,"\n".join(lines),va="top",fontfamily="monospace",fontsize=6)
    save(fig,"04_pixel_face_barycentric.png",f"{cid} | C1 vs C3 pixel/Face ID/barycentric/XYZ; magenta=unmatched | working 320x180; native u=(u+.5)*2-.5")
    # 3D correspondence vectors for all practical methods, identical sample IDs/views.
    fig=plt.figure(figsize=(15,9))
    for ri,condition in enumerate(["C1","C3"]):
        pr=np.load(fetch(root,condition+"_predict","predictions/"+cid+".npz"));ev=np.load(fetch(root,condition+"_evaluate","evaluation/"+cid+".npz"))
        for ci,method in enumerate(METHODS):
            ax=fig.add_subplot(2,3,ri*3+ci+1,projection="3d");mesh(ax)
            valid=pr[method+"_valid"][selected];ix=selected[valid];P=pr["P_obs"][ix];Q=pr[method+"_points"][ix]
            ax.scatter(*ev["P_true"][selected].T,color="green",s=8,label="True latent point (evaluation)")
            ax.scatter(*P.T,color="#e06f43",s=7,label="Biased observation")
            ax.scatter(*Q.T,color="#2774c9",s=8,label="Predicted correspondence")
            for p,q in zip(P,Q):ax.plot(*np.stack([p,q]).T,color="#2774c9",lw=.8)
            ax.set_title(f"{condition} {method}: {len(ix)}/{len(selected)} selected rays",fontsize=8)
            if ri==0 and ci==0:ax.legend(fontsize=6)
    save(fig,"05_correspondence_vectors.png",f"{cid} | Actual correspondence segments, green independent targets | identical 3D view and mm axes | Body never updated")
    fig,axes=plt.subplots(1,2,figsize=(12,4),layout="constrained")
    for ci,condition in enumerate(sc["condition_order"]):
        for mi,method in enumerate(methods):
            rs=[r for r in allrows if r["condition"]==condition and r["method"]==method];N=sum(r["target_N"]for r in rs);n=sum(r["independent_numeric_N"]for r in rs)
            axes[0].bar(ci*5+mi,100*n/N,color=plt.cm.tab10(mi),label=method if ci==0 else None)
            axes[1].scatter(ci*5+mi,sum(r["MAE_mm"]*r["independent_numeric_N"]for r in rs)/n,color=plt.cm.tab10(mi))
    for ax in axes:ax.set_xticks([1.5,6.5,11.5],sc["condition_order"]);ax.grid(axis="y",alpha=.2)
    axes[0].set(ylabel="Numeric matches / all observed targets [%]",ylim=(0,105));axes[0].legend(fontsize=6);axes[1].set(ylabel="Conditional mean material error [mm]")
    save(fig,"06_coverage_and_error.png","G01 all four frozen cameras | coverage denominator retained | Oracle diagnostic excluded from practical method claims")
    with (attempt/"PIXEL_FACE_AUDIT.csv").open("w",newline="")as f:
        writer=csv.DictWriter(f,list(table[0]),lineterminator="\n");writer.writeheader();writer.writerows(table)
    save_json(attempt/"FIGURE_INDEX.json",dict(figures=titles,source_id="G01:spec_01p-12-",units="mm",heatmap_limits_mm=[0,2],fixed_3D_view=[25,-60],display_CAD_triangle_stride=16,raw_CAD_unchanged=True,rows=allrows))
    return outputs(attempt,dict(status="PASS",role="evaluator",figures=titles,rows=allrows,body_updates=0))
