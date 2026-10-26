"""Unchanged original C0 drawing functions. Globals injected by wrapper."""

def basis(angle):
    az,el=np.deg2rad(angle);eye=np.array([np.cos(el)*np.cos(az),np.cos(el)*np.sin(az),np.sin(el)])
    dire=-eye;right=np.cross(dire,[0,0,1]);right/=np.linalg.norm(right);up=np.cross(right,dire);return eye,right,up

def view(ax,P,color,limits,angle=(-65,22),title='',size=.8,highlight=None):
    eye,right,up=basis(angle);q=np.c_[P@right,P@up];order=np.argsort(P@eye)
    if len(P):ax.scatter(q[order,0],q[order,1],s=size,c=np.broadcast_to(color,(len(P),3))[order],linewidths=0,rasterized=True)
    rv=ring.vertices[::7];ax.scatter(rv@right,rv@up,s=.4,c='#26343d',linewidths=0,rasterized=True)
    if highlight is not None and len(highlight):
        h=np.c_[highlight@right,highlight@up];ax.scatter(h[:,0],h[:,1],s=10,facecolors='none',edgecolors='blue',linewidths=.5)
    ax.set(xlim=limits[0],ylim=limits[1],xlabel='Ring视平面横向 / mm',ylabel='Ring视平面纵向 / mm',title=title)
    ax.set_aspect('equal');ax.grid(alpha=.15)
    x0=limits[0][0]+.06*np.ptp(limits[0]);y0=limits[1][0]+.06*np.ptp(limits[1]);length=5. if np.ptp(limits[0])>=20 else 2.5 if np.ptp(limits[0])>=10 else 1.
    ax.plot([x0,x0+length],[y0,y0],c='black',lw=2);ax.text(x0,y0+.025*np.ptp(limits[1]),f'{length:g} mm',fontsize=8)

def limits(cases,angle=(-65,22)):
    _e,right,up=basis(angle);P=np.concatenate([data(c)['XYZ_mm'] for c in cases]+[ring.vertices]);q=np.c_[P@right,P@up]
    lo=q.min(0);hi=q.max(0);center=(lo+hi)/2;rad=max(hi-lo)*.56;return [(center[i]-rad,center[i]+rad)for i in range(2)]
