"""Root zooms from real triangles, with explicitly labelled display-only crops."""
import sys
from pathlib import Path
import numpy as np
import trimesh
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
TD=Path(__file__).resolve().parents[1];sys.path.insert(0,str(TD/'code'))
from io_utils import read,body,source_folder
from lengths import spline
from ring_collision_gate import signed
from ring_first_3d.multisurface.geometry import scene

def clipped(V,F,lo,hi):
    V,F=V.copy(),F.copy()
    for k in range(3):
        n=np.eye(3)[k];p=np.zeros(3);p[k]=lo[k];V,F,_=trimesh.intersections.slice_faces_plane(V,F,n,p)
        p=p.copy();p[k]=hi[k];V,F,_=trimesh.intersections.slice_faces_plane(V,F,-n,p)
    return V[F]

for case in ['G01','G03']:
    d=TD/'review_assets'/case;r=read(d/'PREDICTIONS_FROZEN.json')['records'][0];g=read(d/'CHOSEN_GATES.json');sw=body(d/'FINAL_SWEEP_PARAMETERS.npz')
    before=body(source_folder(case)/'STEP_024/BODY.npz');final=body(d/('FINAL.npz'if r['status']=='NUMERIC'else'FAILED_ATTEMPT.npz'))
    config=read(d/'LOCAL_CONFIGURATION.json')['embedding'];curve=spline(sw['control']);u=np.linspace(0,1,1025);C=curve(u);exit_u=g['length']['exit_parameter'];exitpoint=curve(exit_u)
    span=config['root_radius_mm']*1.35;lo=C.min(0)-span;hi=C.max(0)+span
    original=clipped(before['V'],before['F_solid'],lo,hi)
    exposed=clipped(final['V'],final['F_solid'][final['solid_face_operand']==1],lo,hi)
    phi=signed(scene(before['V'],before['F_solid']),sw['V']);internal=(phi[sw['F']]<0).all(1)
    embedded=clipped(sw['V'],sw['F'][internal],lo,hi)
    fig=plt.figure(figsize=(14,5))
    for j,(elev,azim)in enumerate([(20,-65),(10,25),(75,-90)]):
        ax=fig.add_subplot(1,3,j+1,projection='3d')
        for tri,color,alpha,label in [(original,'gray',.18,'frozen Body reference'),(exposed,'purple',.6,'actual external new surface'),(embedded,'orange',.35,'internal construction (removed by union)')]:
            if len(tri):ax.add_collection3d(Poly3DCollection(tri,facecolor=color,alpha=alpha,edgecolor='none',label=label))
        ax.plot(*C[u<=exit_u].T,c='orange',lw=3,label='embedded arc (excluded)');ax.plot(*C[u>=exit_u].T,c='cyan',lw=3,label='exposed arc')
        ax.scatter(*exitpoint,c='red',s=30,label='first exit / length starts')
        ax.set(xlim=(lo[0],hi[0]),ylim=(lo[1],hi[1]),zlim=(lo[2],hi[2]),xlabel='x mm',ylabel='y mm',zlabel='z mm');ax.set_box_aspect(hi-lo);ax.view_init(elev,azim);ax.tick_params(labelsize=6)
        if j==0:ax.legend(fontsize=6,loc='upper left')
    fig.suptitle(f'{case}: '+('automatic gate PASS; proximal-section exposure remains'if r['status']=='NUMERIC'else'FAILED ATTEMPT / formal length NaN')+'\nReal-triangle zoom; display crop without caps; full source Mesh unchanged',fontsize=10)
    fig.subplots_adjust(left=.01,right=.98,bottom=.08,top=.87,wspace=.1);fig.savefig(TD/'visualization/figures'/(case+'_ROOT.png'),dpi=125);plt.close(fig)
print('Re-rendered display-only root crops; no prediction geometry changed.')
