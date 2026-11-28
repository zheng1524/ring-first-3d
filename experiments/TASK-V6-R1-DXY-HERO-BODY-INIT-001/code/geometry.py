"""Reuse historical ellipsoid and clipping kernels; new bounded-bias ray interface."""
from core import *
from scipy.spatial.transform import Rotation
import trimesh
A1='4a09aedc669092d264f070ccac4fd12851097dd1'
CP='experiments/TASK-E4-A1-ELLIPSE-VS-FULLMASK-001/code/'
E10='534b9597ee0670badfb1435b3af6f821b5c8aed1'
BP='experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/runs/BODY_BASE_PYTORCH3D_010/code/'
definitions(A1,CP+'common.py',['decode','ray_components','first_depth'],globals())
definitions(A1,CP+'losses.py',['robust','ellipse_projection','signed_distance'],globals())
definitions(E10,BP+'planes.py',['normalize','align','compare'],globals())
definitions(E10,BP+'clip_mesh.py',['basis','ear_clip','clip'],globals())
SPHERE=trimesh.creation.icosphere(subdivisions=3)
def body_mesh(p):
 c,Q,a=decode(p,np.eye(3));return (np.asarray(SPHERE.vertices)*a)@Q.T+c,np.asarray(SPHERE.faces)
def rays(uv,K,C):
 d=np.c_[uv,np.ones(len(uv))]@np.linalg.inv(K).T@C[:3,:3].T
 return np.c_[np.tile(C[:3,3],(len(uv),1)),d]
def project(X,K,C):
 q=(X-C[:3,3])@C[:3,:3];v=q@K.T;return v[:,:2]/v[:,2,None],q[:,2]
def ellipsoid_depth(p,r):return first_depth(p,np.eye(3),r)
def corrected_points(r,D,b):return r[:,:3]+r[:,3:]*(D-b)[:,None]
def clipped_depth(p,r,plane=None):
 A,B,C,disc=ray_components(p,np.eye(3),r);s=np.sqrt(np.maximum(disc,0));lo=(-B-s)/A;hi=(-B+s)/A
 front=np.where(lo>0,lo,hi);valid=(disc>=0)&(front>0);cap=np.zeros(len(r),bool)
 if plane is not None:
  plane=normalize(plane);h=r[:,:3]@plane[:3]+plane[3];v=r[:,3:]@plane[:3]
  cross=-h/np.where(abs(v)>1e-14,v,1e-14)
  start=np.maximum(lo,np.where(v>1e-14,cross,-np.inf));end=np.minimum(hi,np.where(v< -1e-14,cross,np.inf))
  front=np.where(start>0,start,end);valid&=(end>=np.maximum(start,0))&~((abs(v)<=1e-14)&(h<0))
  cap=valid&(abs(front-cross)<1e-7)&(abs(v)>1e-14)
 hit=valid&~cap;return np.where(valid,front,np.inf),hit,cap
