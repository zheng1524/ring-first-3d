import numpy as np
from scipy.spatial.transform import Rotation as Rot

def make_obs(n=360):
    t = np.linspace(0, 2*np.pi, n, endpoint=False)
    inner = np.c_[60*np.cos(t), 45*np.sin(t)]
    outer = np.c_[75*np.cos(t), 58*np.sin(t)]
    return dict(inner=inner, outer=outer, inner_vis=np.ones(n,bool), outer_vis=np.ones(n,bool))
