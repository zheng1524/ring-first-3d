"""Frozen real-SIFT reference-map matching and PnP, without old IO modules."""
import cv2
import numpy as np

def features(rgb, labels):
    sift=cv2.SIFT_create(nfeatures=6000,contrastThreshold=.01)
    keys,des=sift.detectAndCompute(cv2.cvtColor(rgb,cv2.COLOR_RGB2GRAY),None)
    xy=np.array([k.pt for k in keys],float).reshape(-1,2)
    des=np.empty((0,128),np.float32) if des is None else des
    pix=np.clip(np.rint(xy).astype(int),[0,0],[639,359])
    return dict(xy=xy,des=des,region=labels[pix[:,1],pix[:,0]])

def mutual(a,b):
    if len(a)<2 or len(b)<2:return []
    matcher=cv2.BFMatcher(cv2.NORM_L2)
    ab={m.queryIdx:m for m,n in matcher.knnMatch(np.asarray(a,np.float32),np.asarray(b,np.float32),k=2) if m.distance<.72*n.distance}
    ba={m.queryIdx:m.trainIdx for m,n in matcher.knnMatch(np.asarray(b,np.float32),np.asarray(a,np.float32),k=2) if m.distance<.72*n.distance}
    return [(i,m.trainIdx,float(m.distance)) for i,m in ab.items() if ba.get(m.trainIdx)==i]

def pnp(rgb, labels, K, rgb_map):
    f=features(rgb,labels);pairs=mutual(rgb_map['des'],f['des'])
    rows=[dict(landmark=k,feature=j,distance=d,X=rgb_map['X'][k],uv=f['xy'][j],region=int(f['region'][j]),role='FEATURE_HELD' if k%5==0 else 'FIT')for k,j,d in pairs]
    fit=[r for r in rows if r['role']=='FIT'];C=None;inrows=[]
    if len(fit)>=6:
        X=np.array([r['X'] for r in fit]);uv=np.array([r['uv'] for r in fit])
        cv2.setRNGSeed(20261115)
        ok,r,t,ids=cv2.solvePnPRansac(X,uv,np.array(K),None,iterationsCount=1000,reprojectionError=3.,confidence=.999,flags=cv2.SOLVEPNP_EPNP)
        if ok and ids is not None and len(ids)>=6:
            ii=ids.ravel();r,t=cv2.solvePnPRefineLM(X[ii],uv[ii],np.array(K),None,r,t)
            W=np.eye(4);W[:3,:3]=cv2.Rodrigues(r)[0];W[:3,3]=t.ravel();C=np.linalg.inv(W);inrows=[fit[j] for j in ii]
    return dict(matches=rows,fit_pnp_inliers=inrows,C=C,features_N=len(f['xy']),
                map_ancestry='Frozen real reference-video SIFT triangulation; conditional, not pose GT')
