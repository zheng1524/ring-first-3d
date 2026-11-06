"""Plane sign equivalence and common-anchor stability, without P0 or type inputs."""
import numpy as np

def normalize(p):
 p=np.asarray(p,float).copy();q=np.linalg.norm(p[:3]);assert np.isfinite(p).all()and q>1e-12;return p/q

def align(p,reference):
 p=normalize(p);q=normalize(reference);return -p if p[:3]@q[:3]<0 else p

def compare(p,reference,anchor):
 q=normalize(reference);p=align(p,q);angle=float(np.degrees(np.arctan2(np.linalg.norm(np.cross(p[:3],q[:3])),np.clip(p[:3]@q[:3],-1,1))));offset=float(abs((p[:3]-q[:3])@np.asarray(anchor)+p[3]-q[3]));return p,angle,offset

def orient_retained(p,internal):
 p=normalize(p);v=np.asarray(internal)@p[:3]+p[3]
 if len(v)and np.median(v)<0:p=-p;v=-v
 return p,dict(internal_N=len(v),fraction_positive=float(np.mean(v>=0))if len(v)else None,median_signed_height_mm=float(np.median(v))if len(v)else None,rule='median of reliable original Polyp interior; never B or type')
