"""Ring cross-sections, source labels only; no P/Q or morphology-specific branch."""
from common import *
from dxy_cross_section_helpers import smooth_normal,beyond

def sample(labels):
    rm=labels==2; pol=labels==1;h,w=rm.shape
    cs,_=cv2.findContours(rm.astype(np.uint8),cv2.RETR_CCOMP,cv2.CHAIN_APPROX_NONE)
    ys,xs=np.where(rm); rr=max(np.ptp(xs),np.ptp(ys))/2 if len(xs) else 1.
    rows=[]
    for ci,c in enumerate(cs):
        c=c[:,0].astype(float)
        for i in range(0,len(c),4):
            p=c[i];n=smooth_normal(c,i)if len(c)>=19 else None
            row=dict(sample_id=len(rows),contour=ci,index=i,point=p.tolist(),class_raw='D',class_final='D',reason='normal_unreliable')
            if n is None:rows.append(row);continue
            exits=[beyond(rm,p,sgn*n,max(4,int(np.ceil(.75*rr))))for sgn in [1,-1]]
            if any(x is None for x in exits):row['reason']='exit_missing';rows.append(row);continue
            width=float(np.linalg.norm(exits[0]-exits[1]));width=max(1.,width)
            row.update(normal=n.tolist(),exits=[e.tolist()for e in exits],width_px=width,midpoint=np.mean(exits,axis=0).tolist())
            fracs=[];sites=[]
            for j,sgn in enumerate([1,-1]):
                counts=np.zeros(2);side_sites=[]
                for offset in [.25,.5]:
                    q=exits[j]+sgn*n*max(1.,offset*width);side_sites.append(q.tolist());radius=max(1.,.15*width)
                    x0=max(0,int(np.floor(q[0]-radius)));x1=min(w,int(np.ceil(q[0]+radius))+1);y0=max(0,int(np.floor(q[1]-radius)));y1=min(h,int(np.ceil(q[1]+radius))+1)
                    yy,xx=np.mgrid[y0:y1,x0:x1];valid=((xx-q[0])**2+(yy-q[1])**2<=radius**2)&(~rm[y0:y1,x0:x1])
                    if len(xx) and valid.any():
                        vals=labels[y0:y1,x0:x1][valid];counts += [(vals==1).sum(),(vals==0).sum()]
                fracs.append((counts/max(1.,sum(counts))).tolist() if sum(counts) else [0.,0.]);sites.append(side_sites)
            row.update(fractions=fracs,sites=sites,reason='sampled')
            rows.append(row)
    valid=[r for r in rows if 'fractions'in r]
    if valid:
        mids=np.array([r['midpoint']for r in valid]);tree=cKDTree(mids)
        for r in valid:
            # Pool nearby sections without requiring every noisy sample to agree.
            inds=tree.query_ball_point(r['midpoint'],max(1.,.5*r['width_px']))
            f=np.array(r['fractions'])
            neigh=[]
            for j in inds:
                q=valid[j]
                if abs(np.dot(q['normal'],r['normal']))<.8:continue
                g=np.array(q['fractions']);g=g if np.dot(q['normal'],r['normal'])>=0 else g[::-1];neigh.append(g)
            if neigh:f=.5*f+.5*np.mean(neigh,axis=0)
            def lab(a):return 'P'if a[0]>=.35 else'B'if a[1]>=.6 else'U'
            sides=[lab(a)for a in f];raw=[lab(a)for a in r['fractions']]
            def classify(x):return 'D'if'U'in x else'A'if x==['P','P']else'C'if x==['B','B']else'B'
            r.update(side_labels=sides,pooled_fractions=f.tolist(),class_raw=classify(raw),class_final=classify(sides),neighbor_N=len(neigh))
    # Assign to actual Ring pixels plus a width-scaled neighborhood only.
    classmap=np.zeros(labels.shape,np.uint8);band=np.zeros_like(rm)
    if rows:
        coords=np.array([r.get('midpoint',r['point'])for r in rows]);tree=cKDTree(coords)
        yy,xx=np.mgrid[:h,:w];_,idx=tree.query(np.c_[xx.ravel(),yy.ravel()]);idx=idx.reshape(h,w)
        widths=np.array([r.get('width_px',1.)for r in rows]);codes=np.array(['ABCD'.index(r['class_final'])+1 for r in rows],np.uint8)
        dist=cv2.distanceTransform((~rm).astype(np.uint8),cv2.DIST_L2,cv2.DIST_MASK_PRECISE)
        band=rm|(dist<=.5*widths[idx]);classmap[band]=codes[idx[band]]
    return rows,classmap,band

def main():
    counts=[]
    for name in ['virtual','real']:
        for v in getcase(name)['views']:
            a=np.load(R/'inputs'/name/(v['id']+'.npz'));rows,cm,band=sample(a['labels'])
            np.savez_compressed(R/'inputs'/name/(v['id']+'_SIDES.npz'),classes=cm,band=band)
            save('metrics/sides/'+v['id']+'.json',rows)
            table('metrics/sides/'+v['id']+'.csv',rows)
            counts.append(dict(case=name,view=v['id'],**{c:sum(r['class_final']==c for r in rows)for c in 'ABCD'},band_N=int(band.sum()),Polyp_N=int((a['labels']==1).sum())))
    table('metrics/RING_SIDES_COUNTS.csv',counts);print(counts,flush=True)

if __name__=='__main__':main()
