"""Arc length and first inside-to-outside exit of the frozen original Body."""
import numpy as np
from scipy.interpolate import BSpline
from scipy.integrate import quad
from scipy.optimize import brentq
from ring_first_3d.multisurface.geometry import scene
from ring_collision_gate import signed

def spline(control):
    return BSpline(np.r_[np.zeros(4),.5,np.ones(4)],np.asarray(control),3)

def measure(control,original,samples=1025):
    curve=spline(control);derivative=curve.derivative();u=np.linspace(0,1,samples)
    engine=scene(original['V'],original['F_solid']);phi=signed(engine,curve(u))
    exits=np.flatnonzero((phi[:-1]<0)&(phi[1:]>=0))
    entries=np.flatnonzero((phi[:-1]>=0)&(phi[1:]<0))
    if phi[0]>=0 or len(exits)!=1 or len(entries):
        raise ValueError('NON_UNIQUE_EXIT_OR_REENTRY:'+str(dict(start=float(phi[0]),exits=len(exits),entries=len(entries))))
    i=int(exits[0]);exit_u=brentq(lambda x:float(signed(engine,curve(x)[None])[0]),u[i],u[i+1],xtol=1e-10)
    speed=lambda x:float(np.linalg.norm(derivative(x)))
    total=quad(speed,0,1,epsabs=1e-8)[0];inside=quad(speed,0,exit_u,epsabs=1e-8)[0]
    return dict(total_centerline_length_mm=total,embedded_length_mm=inside,exposed_stalk_length_mm=total-inside,
        embedding_depth_SDF_mm=-float(phi[0]),exit_parameter=exit_u,exit_point=curve(exit_u).tolist(),
        unique_exit=True,reentries=0,centerline_endpoint=curve(1).tolist())

