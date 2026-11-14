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

