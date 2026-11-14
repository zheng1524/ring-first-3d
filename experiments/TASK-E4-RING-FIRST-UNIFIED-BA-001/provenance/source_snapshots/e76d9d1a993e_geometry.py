"""Prediction-side geometry: this module never loads ground truth."""
import numpy as np, cv2
from scipy.spatial.transform import Rotation
from scipy.spatial import cKDTree
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def boundary(mask,n=None):
    contours,_=cv2.findContours(mask.astype(np.uint8),cv2.RETR_LIST,cv2.CHAIN_APPROX_NONE)
    q=np.concatenate([c[:,0,:] for c in contours]).astype(float)+.5
    if n is not None:q=q[np.linspace(0,len(q)-1,min(n,len(q)),dtype=int)]
    return q

def torus_contours(C,rot,K,R=5.6,r=.6,n=256):
    """Exact perspective apparent contours n(X) dot (C-X)=0.
    Valid in the top-view, open-hole, non-self-occluded regime checked by gate.
    theta is a curve parameter, never a claimed physical correspondence.
    rot maps camera coordinates to ring coordinates.
    """
    th=np.arange(n)*2*np.pi/n; a=C[0]*np.cos(th)+C[1]*np.sin(th)-R
    b=C[2]; length=np.sqrt(a*a+b*b)
    if np.any(length<=r):raise ValueError('invalid torus apparent-contour regime')
    phi=np.arctan2(b,a)[None,:]+np.array([-1,1])[:,None]*np.arccos(r/length)[None,:]
    X=np.stack([(R+r*np.cos(phi))*np.cos(th),(R+r*np.cos(phi))*np.sin(th),r*np.sin(phi)],-1)
    cam=(X-C) @ rot; uv=cam @ K.T
    return uv[...,:2]/uv[...,2:]

def contour_mask(C,rot,K,shape):
    curves=torus_contours(C,rot,K,n=512)
    areas=[abs(cv2.contourArea(q.astype(np.float32))) for q in curves]
    outer=np.argmax(areas); result=np.zeros(shape,np.uint8)
    # OpenCV integer pixel x represents the physical center x+.5.
    cv2.fillPoly(result,[np.round(curves[outer]-.5).astype(np.int32)],1)
    cv2.fillPoly(result,[np.round(curves[1-outer]-.5).astype(np.int32)],0)
    return result

def masks(name):
    result=[]
    directory=ROOT/'synthetic'/name
    for p in sorted((directory/'segmentation').glob('*.png')):
        img=cv2.imread(str(p)); ring=(img[:,:,1]>128)&(img[:,:,1]>img[:,:,0])&(img[:,:,1]>img[:,:,2])
        polyp=(img[:,:,2]>128)&(img[:,:,2]>img[:,:,0])&(img[:,:,2]>img[:,:,1])
        for folder,m in [('ring_mask',ring),('polyp_mask',polyp)]:
            (directory/folder).mkdir(exist_ok=True); cv2.imwrite(str(directory/folder/p.name),m.astype(np.uint8)*255)
        result.append(ring)
    return np.array(result)

def project(X,C,rot,K):
    cam=(X-C) @ rot; q=cam @ K.T
    return q[...,:2]/q[...,2:],cam[...,2]

def unproject(depth,K,c2w,uv):
    xy=np.floor(uv).astype(int); z=depth[xy[:,1],xy[:,0]]
    rays=np.c_[uv,np.ones(len(uv))] @ np.linalg.inv(K).T
    return (rays*z[:,None]) @ c2w[:3,:3].T+c2w[:3,3]

def overlay(rgb,observed,predicted):
    out=rgb.copy(); b=boundary(observed).astype(int); p=boundary(predicted).astype(int)
    out[b[:,1],b[:,0]]=[0,255,0]; out[p[:,1],p[:,0]]=[255,0,255]
    return out

def stats(x):
    x=np.asarray(x); x=x[np.isfinite(x)]
    if not len(x):return dict(n=0,median=None,mae=None,p95=None,max=None)
    return dict(n=len(x),median=float(np.median(x)),mae=float(np.mean(x)),p95=float(np.percentile(x,95)),max=float(np.max(x)))
