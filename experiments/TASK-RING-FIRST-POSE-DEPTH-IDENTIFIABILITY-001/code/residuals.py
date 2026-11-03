"""Fixed correspondences, full residual vectors, metric axial-depth and right SE3."""
from common import *

class ResidualModel:
    def __init__(self,ids):
        self.ids=ids;self.n=len(ids);self.p=6*(self.n-1)+self.n
        self.scales=np.r_[np.tile(np.r_[np.full(3,.1),np.full(3,np.deg2rad(.1))],self.n-1),np.full(self.n,.1)]
        self.names=[f'{cid}:{s}'for cid in ids[1:]for s in ['tx_mm','ty_mm','tz_mm','rx_rad','ry_rad','rz_rad']]+[cid+':bias_mm'for cid in ids]
        self.s=[source(c)for c in ids];self.data=[cleaned(c)for c in ids];self.records=[];self.inventory=[];self.ring=[]
        self.scene=CC[ids[0]]['scene_id'];self.sdf=[signed_distance(s['labels']==1)for s in self.s]
        for i,a in enumerate(ids):
            self.prepare_ring(i)
            for j,b in enumerate(ids):
                if i!=j:self.prepare_relation(i,j)
        self.zero=self.parts(np.zeros(self.p))

    def state(self,y):
        x=y*self.scales;T=[self.s[0]['T']]+[perturb(self.s[i]['T'],x[6*(i-1):6*i])for i in range(1,self.n)]
        return T,x[6*(self.n-1):]

    def project(self,X,j,T):return vis.project_camera(X,self.s[j]['K'],T[j])

    def points(self,i,ray,z,T,b):
        return (ray*(z+b[i])[:,None])@T[i][:3,:3].T+T[i][:3,3]

    def raypoints(self,i,uv):
        n=self.data[i];uvn=(uv+.5)*np.array(n['depth'].shape[::-1])/np.array([640,360])-.5;xy=pix(uvn,n['depth'].shape)
        return np.c_[xy,np.ones(len(xy))]@np.linalg.inv(n['Kn']).T,n['depth'][xy[:,1],xy[:,0]].astype(float),n['valid'][xy[:,1],xy[:,0]],xy[:,1]*n['depth'].shape[1]+xy[:,0]

    def qualified_visible(self,i,j,X,uv,z):
        s=self.s[j];n=self.data[j];xy=pix(uv);v=inside(uv)&(z>0)&(at(s['labels'],uv)==1)&(at(s['RGB'],uv).min(1)<245)
        v&=at(cv2.distanceTransform((s['labels']==1).astype(np.uint8),cv2.DIST_L2,cv2.DIST_MASK_PRECISE),uv)>2
        r,_,ok,ids=self.raypoints(j,uv);zz=n['depth'].ravel()[ids].astype(float)
        cad,_=cast(ringscene(self.scene),uv,s['K'],s['T']);v&=ok&(z<=cad+.05)&(z<=zz+.25)
        return v,zz,ids

    def prepare_relation(self,i,j):
        a,b=self.ids[i],self.ids[j];si,sj=self.s[i],self.s[j];T=[s['T']for s in self.s];bi=np.zeros(self.n)
        d=matching(a,b);p,q=d['p'],d['q'];m=d['independent_good']
        # Independent RGB-only epipolar correspondences, no RF error filtering.
        ep=select(np.flatnonzero(m),64)
        ray,z,ok,nid=self.raypoints(i,p);X=self.points(i,ray,z,T,bi);uv,dz=self.project(X,j,T)
        # Correspondence's measured target pixel must be Polyp and known; depth/cad guards use actual projected ray.
        valid,_,_=self.qualified_visible(i,j,X,uv,dz)
        rp=select(np.flatnonzero(m&ok&valid&(at(si['labels'],p)==1)&(at(sj['labels'],q)==1)),64)
        self.records.append(dict(kind='epipolar',i=i,j=j,p=p[ep],q=q[ep],original_match_indices=ep))
        self.records.append(dict(kind='reprojection',i=i,j=j,ray=ray[rp],z=z[rp],q=q[rp],native_id=nid[rp],original_match_indices=rp))
        # Deterministic surface subset before target qualification; all baseline rejection causes counted.
        nn=self.data[i];ii=select(np.arange(len(nn['native_uv'])),1024);xy=nn['native_uv'][ii];ray=np.c_[xy,np.ones(len(xy))]@np.linalg.inv(nn['Kn']).T;z=nn['depth'][xy[:,1],xy[:,0]].astype(float)
        X=self.points(i,ray,z,T,bi);uv,dz=self.project(X,j,T);valid,target_z,target_ids=self.qualified_visible(i,j,X,uv,dz);sel=select(np.flatnonzero(valid),128)
        self.records.append(dict(kind='depth',i=i,j=j,ray=ray[sel],z=z[sel],target_z=target_z[sel],q=uv[sel],native_id=nn['native_id'][ii[sel]],target_native_id=target_ids[sel]))
        # Source anatomical Mask boundary, never newly cleaned hole boundary.
        pb=boundary(si['labels']==1);free=cv2.distanceTransform((si['labels']!=2).astype(np.uint8),cv2.DIST_L2,cv2.DIST_MASK_PRECISE)
        r,zs,ok,ni=self.raypoints(i,pb);X=self.points(i,r,zs,T,bi);pu,pz=self.project(X,j,T);cad,_=cast(ringscene(self.scene),pu,sj['K'],sj['T'])
        good=ok&inside(pu)&(pz>0)&(pz<=cad+.05)&(at(free,pb)>2)&(abs(sample(self.sdf[j],pu))<=8)&(at(sj['labels'],pu)!=2)
        ss=select(np.flatnonzero(good),32)
        self.records.append(dict(kind='silhouette',i=i,j=j,ray=r[ss],z=zs[ss],native_id=ni[ss],q=pu[ss]))
        self.inventory.append(dict(A=a,B=b,raw_RGB_matches=len(p),independent_RGB_matches=int(m.sum()),epipolar_scalar_N=len(ep),reprojection_points=len(rp),depth_candidates=len(ii),depth_valid_before_cap=int(valid.sum()),depth_fixed_points=len(sel),silhouette_fixed_points=len(ss),qualified_match_status='ENOUGH'if len(rp)>=12 else'INSUFFICIENT_EVIDENCE',joint_source_RGB_correlation='HERO upstream DAG not independent trials; no statistical probability claim'))

    def prepare_ring(self,i):
        s=self.s[i];p=boundary(s['labels']==2);clear=cv2.distanceTransform((s['labels']!=1).astype(np.uint8),cv2.DIST_L2,cv2.DIST_MASK_PRECISE)
        p=p[(at(clear,p)>2)&(p[:,0]>=2)&(p[:,0]<638)&(p[:,1]>=2)&(p[:,1]<358)];p=p[select(np.arange(len(p)),128)]
        curves=ring_curves(self.ids[i],s['T']);flat=curves.reshape(-1,2);idx=cKDTree(flat).query(p)[1];C=curves.shape[1];tangent=(np.roll(curves,-1,axis=1)-np.roll(curves,1,axis=1)).reshape(-1,2)[idx]
        normal=np.c_[-tangent[:,1],tangent[:,0]];normal/=np.maximum(1e-12,np.linalg.norm(normal,axis=1))[:,None]
        self.ring.append(dict(i=i,p=p,idx=idx,normal=normal))

    def parts(self,y):
        T,b=self.state(y);pieces={k:[]for k in ['epipolar','reprojection','silhouette','depth','ring']}
        for r in self.records:
            i,j,k=r['i'],r['j'],r['kind']
            if k=='epipolar':v=sampson(fundamental(self.s[i]['K'],T[i],self.s[j]['K'],T[j]),r['p'],r['q'],signed=True)/2
            else:
                X=self.points(i,r['ray'],r['z'],T,b);uv,z=self.project(X,j,T)
                if k=='reprojection':v=(uv-r['q']).ravel()/2
                elif k=='depth':v=(z-r['target_z']-b[j])/.25
                else:v=sample(self.sdf[j],uv)/3
            pieces[k].append(v)
        for r in self.ring:
            i=r['i'];curves=ring_curves(self.ids[i],T[i]).reshape(-1,2);pieces['ring'].append(((curves[r['idx']]-r['p'])*r['normal']).sum(1)/3)
        return {k:np.concatenate(v)if v else np.empty(0)for k,v in pieces.items()}

    def vector(self,y,constraint='C3',balanced=True):
        p=self.parts(y);ks=protocol()['B'][constraint]
        return np.concatenate([p[k]/np.sqrt(max(1,len(p[k])))if balanced else p[k]for k in ks])

    def dynamic(self,y):
        """Separate visibility switching diagnostic, never changes Jacobian row identities."""
        T,b=self.state(y);zdelta=[];rgberr=[];outline=[];valid_count=total=switched=0
        for r in self.records:
            if r['kind']!='depth':continue
            i,j=r['i'],r['j'];X=self.points(i,r['ray'],r['z'],T,b);uv,z=self.project(X,j,T);n=self.data[j];xy=pix((uv+.5)*np.array(n['depth'].shape[::-1])/np.array([640,360])-.5,n['depth'].shape)
            target=n['depth'][xy[:,1],xy[:,0]].astype(float)+b[j];cad,_=cast(ringscene(self.scene),uv,self.s[j]['K'],T[j]);v=inside(uv)&(z>0)&(at(self.s[j]['labels'],uv)==1)&n['valid'][xy[:,1],xy[:,0]]&(z<=cad+.05)&(z<=target+.25)
            total+=len(v);valid_count+=int(v.sum());switched+=int((~v).sum());zdelta.extend(z[v]-target[v]);outline.extend(sample(self.sdf[j],uv[v]))
            # Source original RGB only; target is evaluation here, not prediction coloring.
            sn=self.data[i];native_id=r['native_id'];su=np.c_[native_id%sn['depth'].shape[1],native_id//sn['depth'].shape[1]];archive=(su+.5)*[640/sn['depth'].shape[1],360/sn['depth'].shape[0]]-.5
            rgb1=at(self.s[i]['RGB'],archive);rgb2=at(self.s[j]['RGB'],uv);rgberr.extend(abs(rgb1[v].astype(float)-rgb2[v]).mean(1))
        return dict(fixed_baseline_depth_count=total,dynamic_visible_count=valid_count,dynamic_visible_fraction=valid_count/max(1,total),visibility_changes=switched,depth_mm=stats(zdelta),RGB_MAE_255=stats(rgberr),silhouette_px=stats(outline))

    def save_observations(self,path):
        arr={};metadata=[]
        for k,r in enumerate(self.records+self.ring):
            meta={}
            for name,v in r.items():
                if isinstance(v,np.ndarray):arr[f'record{k}_{name}']=v
                else:meta[name]=v
            metadata.append(meta)
        arr['metadata_json']=np.array(json.dumps(metadata));np.savez_compressed(path,**arr)
