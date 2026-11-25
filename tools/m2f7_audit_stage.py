#!/usr/bin/env python3
"""Read-only stage audit for HIST-V6. Never changes solver, thresholds or data."""
import sys,json,argparse,hashlib
from pathlib import Path
import numpy as np
V6=Path('/home/liu/polyp_research/ring_anchor_3d/experiments/ring_first_v6_local_reconstruction')
WS=Path('/home/liu/ring_first_3d_workspace');RUN=WS/'runs/m2f7_hist_g01/hist_v6'
V5=Path('/home/liu/polyp_research/ring_anchor_3d/experiments/ring_first_v5_geometry_crossvideo')
DXY=Path('/home/liu/new-polyp-dxy')

def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def arr_equal(a,b):
 a=np.asarray(a);b=np.asarray(b)
 if a.shape!=b.shape:return dict(equal=False,reason='SHAPE',a_shape=a.shape,b_shape=b.shape)
 finite=np.isfinite(a)&np.isfinite(b);nan=False
 if np.issubdtype(a.dtype,np.number):
  nan=bool(np.any(np.isfinite(a)!=np.isfinite(b)))
  if finite.any():md=float(np.max(np.abs(a[finite].astype(float)-b[finite].astype(float))))
  else:md=0.0
  return dict(equal=bool(np.array_equal(a,b,equal_nan=True)),maxdiff=md,nan_pattern_diff=nan,n=int(a.size))
 return dict(equal=bool(np.array_equal(a,b)))

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',required=True);ap.add_argument('--out',required=True);a=ap.parse_args();root=Path(a.root).resolve();out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
 sys.path[:0]=[str(V6/'scripts'),str(V5/'scripts'),str(DXY/'src')]
 import v6_common
 v6_common.R=root;v6_common.V5=root/'v5raw';v6_common.E=root.parent;v6_common.REPO=Path('/home/liu/polyp_research')
 import local_ring_sfm
 local_ring_sfm.R=root;local_ring_sfm.V5=root/'v5raw';local_ring_sfm.REPO=Path('/home/liu/polyp_research')
 # ensure ledger/obs/initial/tracks are root-local
 tr=np.load(root/'observations/tracks005.npz');pk=np.load(root/'observations/pairs005.npz')
 cam={v:np.load(root/f'predictions/local005_initial_{v}.npz') for v in [0,1]}
 res={}
 for v in [0,1]:
  poses=cam[v]['c2w'];X,tids,support=local_ring_sfm.triangulate_training(poses,dict(tr))
  np.savez_compressed(out/f'tri_v{v}.npz',X=X,tids=tids,support=np.array([np.asarray(s) for s in support],dtype=object),allow_pickle=True)
  # capture the exact first residual call made by the unmodified BA
  import scipy.optimize as so
  orig=local_ring_sfm.least_squares; captured={}
  def wrapper(fun,x0,*args,**kwargs):
   r=np.asarray(fun(x0));captured['initial']=dict(norm=float(np.linalg.norm(r)),mae=float(np.mean(abs(r))),p95=float(np.quantile(abs(r),.95)),n=int(r.size))
   return orig(fun,x0,*args,**kwargs)
  local_ring_sfm.least_squares=wrapper
  try:
   cur,P,ba=local_ring_sfm.BA(poses,X,tids,support,dict(tr),10)
  finally:local_ring_sfm.least_squares=orig
  np.savez_compressed(out/f'ba_{v}.npz',c2w=cur,points=P)
  res[v]=dict(initial_captured=captured.get('initial'),ba=ba)
 with open(out/'solver_receipt.json','w') as f:json.dump(res,f,default=str,indent=1)
 print('AUDIT',root,'saved',out,flush=True)
if __name__=='__main__':main()
