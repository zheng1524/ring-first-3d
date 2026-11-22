#!/usr/bin/env python3
"""Read-only, evidence-preserving inspection of G03 021-CORRECTIVE SIFT/Sampson residuals.

This is a forensic visualization, NOT a replacement for the official objective.
Source of the OFFICIAL Sampson number: pinned 021/core/shared_se3.py::sampson_px.
The script independently derives F to draw epipolar lines, and cross-checks scores.

Outputs: point/pair CSVs, per-frame stats, residual heatmap, distribution, annotated
matched-image panels, and example point-to-epiline overlays using ACTUAL images.

No thresholds/labels/admission/camera/optimizer/measurement pipeline are modified.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys
from typing import Optional
import cv2
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

PROJECT = 'experiments/TASK-E4-W0-CROSSVIDEO-021-CORRECTIVE'
PREP = 'experiments/TASK-E4-UNIFIED-RING-CONTOUR-REFINEMENT-005/runs/prepared'
ERROR_BINS = [(0,3,'<3 px','#21966e'),(3,10,'3–10 px','#c2a039'),(10,50,'10–50 px','#e47732'),(50,float('inf'),'>50 px','#cd3a40')]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1<<20),b''):h.update(block)
    return h.hexdigest()


def write_csv(path:Path, rows:list[dict], fields:list[str]) -> None:
    with path.open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)


def get_cam(root: Path, group: str, video: str):
    p=root/'camera_mainline'/group/('video'+video)/'camera_result.npz'
    if not p.exists():raise FileNotFoundError(f'W0 source unavailable: {p}')
    with np.load(p,allow_pickle=False) as v:
        cams={str(i):np.asarray(v['c2w'][j],dtype=float) for j,i in enumerate(v['ids'])}
        K=np.asarray(v['K'],dtype=float)
    if K.shape !=(3,3):raise ValueError(f'unexpected W0 K shape {K.shape} at {p}')
    return cams,K,p


def load_views(root:Path,group:str,video:str):
    p=root/PREP/(group+'_'+video)/'PREPARED.json'
    if not p.exists():raise FileNotFoundError(f'PREPARED not found: {p}')
    data=json.loads(p.read_text(encoding='utf-8'))
    return {x['view']:x for x in data['views']},p


def load_rgb(root:Path,v:dict)->np.ndarray:
    q=Path(v['cache'])
    if not q.is_absolute():q=root/q
    if not q.exists():raise FileNotFoundError(f'RGB cache unavailable: {q}')
    with np.load(q,allow_pickle=False) as f:
        arr=np.asarray(f['RGB'])
    if arr.ndim==2: return np.repeat(arr[:,:,None],3,axis=2)
    if arr.shape[2]==4: arr=arr[:,:,:3]
    if arr.shape[2]!=3:raise ValueError(f'RGB shape unexpected: {arr.shape}')
    if np.issubdtype(arr.dtype,np.floating) and arr.max(initial=0)<=1.1:arr=(arr*255).clip(0,255)
    return np.asarray(arr,dtype=np.uint8)


def skew(t):
    return np.array([[0,-t[2],t[1]],[t[2],0,-t[0]],[-t[1],t[0],0]],dtype=float)


def build_F(H:np.ndarray,C4:np.ndarray,C5:np.ndarray,K4:np.ndarray,K5:np.ndarray):
    T=np.linalg.inv(C5)@(H@C4)
    R,t=T[:3,:3],T[:3,3]
    # pixel coordinates x5^T F x4=0; K4/K5 may differ
    F=np.linalg.inv(K5).T@skew(t)@R@np.linalg.inv(K4)
    n=np.linalg.norm(F)
    if n<1e-15: return None,float(np.linalg.norm(t))
    return F/n,float(np.linalg.norm(t))


def sampson(F:np.ndarray,a:np.ndarray,b:np.ndarray):
    x=np.column_stack([a,np.ones(len(a))]);y=np.column_stack([b,np.ones(len(b))])
    Fx=(F@x.T).T;Fty=(F.T@y.T).T
    n=np.abs(np.sum(y*Fx,axis=1));d=np.sqrt(np.sum(Fx[:,:2]**2,axis=1)+np.sum(Fty[:,:2]**2,axis=1))+1e-12
    return n/d


def line_distance(l:np.ndarray,xy:np.ndarray):
    d=math.hypot(float(l[0]),float(l[1]))
    return abs(float(l[0]*xy[0]+l[1]*xy[1]+l[2]))/d if d>1e-12 else float('nan')


def clipped_line(l:np.ndarray,w:int,h:int):
    a,b,c=map(float,l);cand=[]
    if abs(b)>1e-12:
        for x in (0,w-1):
            y=-(a*x+c)/b
            if 0<=y<h:cand.append((x,y))
    if abs(a)>1e-12:
        for y in (0,h-1):
            x=-(b*y+c)/a
            if 0<=x<w:cand.append((x,y))
    if len(cand)<2:return None
    best=None;dist=-1
    for i in range(len(cand)):
        for j in range(i+1,len(cand)):
            d=(cand[i][0]-cand[j][0])**2+(cand[i][1]-cand[j][1])**2
            if d>dist:dist=d;best=(cand[i],cand[j])
    return best


def foot_on_line(l:np.ndarray,p:np.ndarray):
    a,b,c=map(float,l);d=a*a+b*b
    if d<1e-15:return np.array([np.nan,np.nan])
    s=(a*p[0]+b*p[1]+c)/d
    return np.array([p[0]-s*a,p[1]-s*b])


def err_bin(v:float):
    for lo,hi,label,color in ERROR_BINS:
        if lo<=v<hi:return label,color
    return '>50 px',ERROR_BINS[-1][3]


def robust_f_test(u:np.ndarray,v:np.ndarray):
    """Diagnostic only; inlier evidence is *not* fed back to optimizer or official metrics."""
    if len(u)<8:return dict(rgb_ransac_status='INSUFFICIENT_MATCHES',rgb_inlier_ratio=float('nan'),rgb_inlier_n=0)
    flag=getattr(cv2,'USAC_MAGSAC',cv2.FM_RANSAC)
    try:
        F,m=cv2.findFundamentalMat(np.asarray(u,np.float32),np.asarray(v,np.float32),flag,1.5,0.999,10000)
        if F is None or m is None: return dict(rgb_ransac_status='NO_CONSENSUS',rgb_inlier_ratio=float('nan'),rgb_inlier_n=0)
        mask=np.asarray(m).ravel()>0
        return dict(rgb_ransac_status='ESTIMATED',rgb_inlier_ratio=float(mask.mean()),rgb_inlier_n=int(mask.sum()))
    except (cv2.error,ValueError):
        return dict(rgb_ransac_status='ERROR',rgb_inlier_ratio=float('nan'),rgb_inlier_n=0)


def plot_heatmap(rows, out):
    A=sorted({r['v004'] for r in rows});B=sorted({r['v005'] for r in rows});idx4={x:i for i,x in enumerate(A)};idx5={x:j for j,x in enumerate(B)}
    # Each unit is an IMAGE PAIR, not a single SIFT point.
    fig,axes=plt.subplots(1,2,figsize=(16,6),constrained_layout=True)
    for ax,key,title,vmax in [(axes[0],'median_px','Median Sampson error (px)',30),(axes[1],'frac_gt50','Fraction of matches >50 px',1)]:
        a=np.full((len(A),len(B)),np.nan)
        for r in rows:a[idx4[r['v004']],idx5[r['v005']]]=r[key]
        im=ax.imshow(a,interpolation='nearest',aspect='auto',cmap='inferno',vmin=0,vmax=vmax)
        ax.set_xticks(range(len(B)),[s.split('raw')[-1] for s in B],rotation=80,fontsize=8)
        ax.set_yticks(range(len(A)),[s.split('raw')[-1] for s in A],fontsize=9)
        ax.set_xlabel('005 raw frame');ax.set_ylabel('004 raw frame');ax.set_title(title)
        for i in range(len(A)):
            for j in range(len(B)):
                if np.isfinite(a[i,j]):
                    label=f'{a[i,j]:.0f}' if key=='median_px' else f'{a[i,j]:.0%}'
                    ax.text(j,i,label,ha='center',va='center',fontsize=5.6,color='white' if a[i,j]>vmax*.4 else 'black')
        fig.colorbar(im,ax=ax,shrink=.8)
    fig.suptitle('021-CORRECTIVE G03: actual W0 poses, SIFT matches, final H\nNot an algorithm acceptance plot',fontsize=12)
    fig.savefig(out/'01_pair_error_heatmap.png',dpi=170);plt.close(fig)


def plot_hist(allerr,out):
    e=np.array(allerr,dtype=float);e=e[np.isfinite(e)]
    edges=[0,1,3,5,10,20,50,100,200,400,max(500,math.ceil(float(e.max(initial=0))/100)*100+100)]
    edges=np.unique(edges)
    fig,ax=plt.subplots(figsize=(10,5),constrained_layout=True)
    n,b,patches=ax.hist(e,bins=edges,edgecolor='white')
    for patch,left in zip(patches,b[:-1]):
        patch.set_facecolor(err_bin(left)[1])
    ax.set_xticks(edges);ax.tick_params(axis='x',labelrotation=45)
    ax.set_xlabel('Sampson residual (px; 021 official definition)');ax.set_ylabel('Matched points')
    ax.set_title(f'G03, N={len(e)}  | median={np.median(e):.2f} px, p95={np.percentile(e,95):.1f} px, >50px={(e>50).mean():.1%}')
    ax.grid(axis='y',alpha=.2)
    fig.savefig(out/'02_residual_distribution.png',dpi=180);plt.close(fig)


def plot_sample_pairs(pair_data:dict, out:Path, v4:dict, v5:dict, root:Path):
    ranked=sorted(pair_data.values(),key=lambda p:(-p['frac_gt50'],-p['p95_px']))
    # Show both systematic and more typical examples, not just the rare worst matches.
    candidates=ranked[:4]+sorted(pair_data.values(),key=lambda p:p['median_px'])[:2]
    used=set()
    for d in candidates:
        key=d['key']
        if key in used:continue
        used.add(key)
        try:
            im4=load_rgb(root,v4[d['v004']]);im5=load_rgb(root,v5[d['v005']])
        except (OSError,KeyError,ValueError) as ex:
            (out/'MISSING_IMAGE_WARNING.txt').open('a',encoding='utf8').write(key+': '+str(ex)+'\n')
            continue
        a,b,e=d['pa'],d['pb'],d['err'];w4=im4.shape[1];h4=im4.shape[0];w5=im5.shape[1]
        fig,ax=plt.subplots(figsize=(14,5.5),constrained_layout=True)
        canvas=np.zeros((max(h4,im5.shape[0]),w4+w5,3),dtype=np.uint8)
        canvas[:h4,:w4]=im4;canvas[:im5.shape[0],w4:w4+w5]=im5
        ax.imshow(canvas);ax.axis('off')
        indices=np.arange(len(e)) if len(e)<=100 else np.unique(np.linspace(0,len(e)-1,100).astype(int))
        for j in indices:
            _,color=err_bin(float(e[j]));p1=a[j];p2=b[j]
            ax.plot([p1[0],w4+p2[0]],[p1[1],p2[1]],color=color,alpha=.46,lw=.8)
            ax.plot([p1[0],w4+p2[0]],[p1[1],p2[1]],'.',color=color,markersize=3)
        ax.set_title(f'004 {d["v004"]}  ↔  005 {d["v005"]}  | N={len(e)}, median={np.median(e):.1f}px, >50px={(e>50).mean():.0%}\n'
                     'Colored links show matching ID, NOT pixel displacement error',fontsize=10)
        f=(out/'pair_montages'/f'{d["v004"]}__{d["v005"]}.png')
        fig.savefig(f,dpi=150);plt.close(fig)


def plot_epi_cases(point_rows,pair_data,out,v4,v5,root):
    # Pick one real correspondence from each residual bin. Prefer examples spanning
    # different frame pairs to reduce a single anomalous pair dominating story.
    used=set();cases=[]
    allr=sorted(point_rows,key=lambda r:r['err_px'])
    target=[1.5,6.,20.,120.]
    for lo,hi,_,_ in ERROR_BINS:
        cand=[r for r in allr if lo<=r['err_px']<hi]
        if not cand:continue
        want=target[len(cases)] if len(cases)<len(target) else 100
        cand.sort(key=lambda r:(abs(r['err_px']-want),r['pair_key'] in used))
        chosen=next((r for r in cand if r['pair_key'] not in used),cand[0]);used.add(chosen['pair_key']);cases.append(chosen)
    if not cases:return
    fig,axs=plt.subplots(len(cases),2,figsize=(14,max(5,len(cases)*3.15)),squeeze=False,constrained_layout=True)
    for row,ex in enumerate(cases):
        pair=pair_data[ex['pair_key']];i=int(ex['match_index_in_pair']);F=pair['F']
        a=np.r_[pair['pa'][i],1.];b=np.r_[pair['pb'][i],1.]
        try:
            imgs=[load_rgb(root,v4[pair['v004']]),load_rgb(root,v5[pair['v005']])]
        except (OSError,KeyError,ValueError) as exc:
            for ax in axs[row]:ax.text(.1,.5,'Image unavailable: '+str(exc)[:80]);ax.axis('off')
            continue
        lines=[F.T@b,F@a];pts=[a[:2],b[:2]]
        _,c=err_bin(ex['err_px'])
        for k in range(2):
            ax=axs[row,k];im=imgs[k];h,w=im.shape[:2]
            ax.imshow(im);ax.set_xlim(0,w);ax.set_ylim(h,0);ax.axis('off')
            line=clipped_line(lines[k],w,h)
            if line:ax.plot([line[0][0],line[1][0]],[line[0][1],line[1][1]],c='#00d8ff',lw=1.7,label='Predicted epipolar line')
            p=pts[k];foot=foot_on_line(lines[k],p)
            if np.isfinite(foot).all():ax.plot([p[0],foot[0]],[p[1],foot[1]],linestyle='--',c='#ff4f68',lw=1.4)
            ax.scatter([p[0]],[p[1]],s=48,c=[c],marker='o',edgecolor='white',linewidths=1)
            ax.set_title(f'{"004" if k==0 else "005"} raw{ex["v004" if k==0 else "v005"].split("raw")[-1]} | point-to-line {line_distance(lines[k],p):.2f}px',fontsize=10)
        axs[row,0].set_ylabel(f'Case {row+1}\nSampson {ex["err_px"]:.2f} px',fontsize=11,labelpad=10)
    fig.suptitle('REAL image points (colored dots) vs predicted epipolar lines (cyan)\nRed dashed segment = one-sided point-to-line distance; different from Sampson',fontsize=12)
    fig.savefig(out/'03_epipolar_examples.png',dpi=175,bbox_inches='tight');plt.close(fig)



def plot_spatial_frames(frame_rows, point_rows, out, views5, root):
    # Aggregate point residuals from all 004 views onto each 005 REAL frame.
    # The points have different 004 sources; they must be labelled accordingly.
    v5=[r for r in frame_rows if r['video']=='005']
    high=sorted(v5,key=lambda r:(-r['frac_gt50'],-r['p95_px']))[:4]
    low=sorted(v5,key=lambda r:(r['frac_gt50'],r['p95_px']))[:2]
    selected=[]
    for r in high+low:
        if r['view'] not in selected:selected.append(r['view'])
    if not selected:return
    fig,axs=plt.subplots(math.ceil(len(selected)/2),2,figsize=(14,4.4*math.ceil(len(selected)/2)),squeeze=False,constrained_layout=True)
    for ax in axs.flat:ax.axis('off')
    for ax,frame in zip(axs.flat,selected):
        try:rgb=load_rgb(root,views5[frame])
        except (OSError,KeyError,ValueError) as e:
            ax.text(.1,.5,f'Unable to load {frame}: {e}');continue
        ax.imshow(rgb);ax.axis('off')
        rows=[r for r in point_rows if r['v005']==frame]
        for lo,hi,label,color in ERROR_BINS:
            sub=[r for r in rows if lo<=r['err_px']<hi]
            if sub:ax.scatter([r['u005_x'] for r in sub],[r['u005_y'] for r in sub],s=17,alpha=.6,c=color,label=f'{label}: {len(sub)}',edgecolors='none')
        ax.set_title(f'005 raw{frame.split("raw")[-1]} | N={len(rows)}, >50px={sum(r["err_px"]>50 for r in rows)/max(len(rows),1):.1%}',fontsize=11)
        ax.legend(loc='lower right',fontsize=8,facecolor='white',framealpha=.8)
    fig.suptitle('Spatial distribution of G03 errors on REAL 005 frames\nEach dot is a match from one of six 004 views; this tests spatial clustering, not causation',fontsize=12)
    fig.savefig(out/'04_error_spatial_overlay_005.png',dpi=160);plt.close(fig)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--root',required=True,help='Path to ring_first_3d_workspace with 021 and W0/Prepared inputs')
    ap.add_argument('--group',default='G03')
    ap.add_argument('--out',required=True)
    a=ap.parse_args();root=Path(a.root).expanduser().resolve();out=Path(a.out).expanduser().resolve();out.mkdir(parents=True,exist_ok=True)
    (out/'pair_montages').mkdir(exist_ok=True)
    current=root/PROJECT;run=current/'runs'/a.group
    mp=run/'MATCHES.npz';res=run/'RESULTS.json';sp=run/'SPLIT.json'
    for p in (mp,res,sp):
        if not p.exists():raise FileNotFoundError(f'Missing required input {p}; do not fabricate it')
    with np.load(mp,allow_pickle=False) as M:
        av=list(map(str,M['a']));bv=list(map(str,M['b']));off=np.asarray(M['off'],dtype=int)
        pa=np.asarray(M['pa'],dtype=float);pb=np.asarray(M['pb'],dtype=float)
    if len(av)!=len(bv) or len(off)!=len(av)+1 or off[0]!=0 or off[-1]!=len(pa) or len(pa)!=len(pb):
        raise ValueError('MATCHES.npz shape/integrity mismatch')
    r=json.loads(res.read_text());split=json.loads(sp.read_text());fit=set(split['fit'])
    H=np.asarray(r['H'],float);ca,K4,p4=get_cam(root,a.group,'004');cb,K5,p5=get_cam(root,a.group,'005')
    v4,prep4=load_views(root,a.group,'004');v5,prep5=load_views(root,a.group,'005')
    # For parity with the official 021 score, ONLY K4 is used in pinned 021.
    # G03's 004/005 K happen to agree, but script refuses silently mixing unequal K.
    if not np.allclose(K4,K5,atol=1e-9):
        raise ValueError('021 official uses a shared hardcoded K. Here 004/005 K differ; halt, do not silently compare unlike definitions.')
    if not np.allclose(K4,np.array([[490,0,319.5],[0,490,179.5],[0,0,1.]]),atol=1e-9):
        raise ValueError('Official 021 uses K=[490,490,319.5,179.5]; current W0 K differs. Need explicitly compare metrics before plotting.')
    sys.path.insert(0,str(current/'core'))
    try:
        from shared_se3 import sampson_px as official_sampson
    except ImportError as ex:raise RuntimeError('Cannot load the pinned 021/shared_se3.py official metric') from ex
    point_rows=[];pair_rows=[];pair_data={};allerrs=[]
    for k,(u,v) in enumerate(zip(av,bv)):
        if u not in ca or v not in cb:raise KeyError(f'W0 camera not found for pair {u} / {v}')
        lo,hi=off[k:k+2];xy4=pa[lo:hi];xy5=pb[lo:hi]
        F,baseline=build_F(H,ca[u],cb[v],K4,K5)
        if F is None:raise RuntimeError(f'Degenerate 0 baseline camera pair {u}/{v}; requires separate diagnosis')
        e=sampson(F,xy4,xy5)
        off_e=official_sampson(xy4,xy5,H,ca[u],cb[v],K4)
        max_delta=float(np.max(np.abs(e-off_e),initial=0.))
        if max_delta>1e-5:raise RuntimeError(f'Independent epiline metric differs from OFFICIAL 021 by {max_delta:.5g} for {u} {v}')
        key=f'{u}__{v}';fitlabel='FIT' if v in fit else 'HOLDOUT'
        epi4=np.column_stack([xy5,np.ones(len(e))])@F
        epi5=np.column_stack([xy4,np.ones(len(e))])@F.T
        ransac=robust_f_test(xy4,xy5)
        p_row=dict(pair_key=key,v004=u,v005=v,split=fitlabel,n=len(e),median_px=float(np.median(e)),
                   p90_px=float(np.percentile(e,90)),p95_px=float(np.percentile(e,95)),
                   max_px=float(e.max()),frac_gt50=float(np.mean(e>50)),frac_lt3=float(np.mean(e<3)),
                   baseline_mm=baseline,**ransac)
        pair_rows.append(p_row);pair_data[key]={**p_row,'key':key,'pa':xy4,'pb':xy5,'err':e,'F':F}
        allerrs.extend(e.tolist())
        for j,x in enumerate(e):
            point_rows.append(dict(pair_key=key,v004=u,v005=v,split=fitlabel,match_index_in_pair=j,
                   u004_x=float(xy4[j,0]),u004_y=float(xy4[j,1]),u005_x=float(xy5[j,0]),u005_y=float(xy5[j,1]),
                   err_px=float(x),line004_px=line_distance(epi4[j],xy4[j]),line005_px=line_distance(epi5[j],xy5[j]),
                   category=err_bin(float(x))[0]))
    write_csv(out/'point_residuals.csv',point_rows,list(point_rows[0]))
    write_csv(out/'pair_residuals.csv',pair_rows,list(pair_rows[0]))
    frame_rows=[]
    for side,col in [('004','v004'),('005','v005')]:
        for frame in sorted(set(r[col] for r in point_rows)):
            ff=np.array([rr['err_px'] for rr in point_rows if rr[col]==frame]);frame_rows.append(dict(video=side,view=frame,n=len(ff),
                    median_px=float(np.median(ff)),p95_px=float(np.percentile(ff,95)),frac_gt50=float(np.mean(ff>50))))
    write_csv(out/'frame_residuals.csv',frame_rows,list(frame_rows[0]))
    plot_heatmap(pair_rows,out);plot_hist(allerrs,out);plot_sample_pairs(pair_data,out,v4,v5,root)
    plot_epi_cases(point_rows,pair_data,out,v4,v5,root);plot_spatial_frames(frame_rows,point_rows,out,v5,root)
    # The `top5` in 022 is POINT-level, not pair median; avoid misleading pair-level inference.
    metrics=dict(group=a.group,matched_pairs=len(pair_rows),matched_points=len(point_rows),
                 official_sampson_median=float(np.median(allerrs)),official_sampson_p95=float(np.percentile(allerrs,95)),
                 frac_gt50=float(np.mean(np.asarray(allerrs)>50)),focus_note='Top-5 extreme rows are individual SIFT matches, not image-pair metrics.',
                 test_commit='021 bfd9c622bb2660b4a2e4c2ffdbadbb72b19971fd',
                 sha256_inputs={str(p):sha256(p) for p in [mp,res,sp,p4,p5,prep4,prep5]},
                 warnings=['RGB-MAGSAC consistency is diagnostic only; not independent of SIFT matching.',
                           'F_img may be degenerate under planar scene or small baseline.',
                           'Sampson is not Euclidean match displacement across the two images.',
                           'Sampson only tests epipolar consistency, not true 3D point identity or depth.'])
    (out/'SUMMARY.json').write_text(json.dumps(metrics,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps(metrics,indent=2,ensure_ascii=False))
    print(f'Images and CSV diagnostics saved to {out}')

if __name__=='__main__':main()
