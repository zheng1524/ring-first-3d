"""Bounded sparse/stretch diagnostics and derived cleanup. No upstream inference."""
import os,sys,json,csv,hashlib,datetime
from pathlib import Path
R=Path(__file__).resolve().parents[1]; REPO=R.parents[1]
PREV=REPO/'experiments/TASK-PHASEC-DENSITY-MULTIGROUP-001'
os.environ.setdefault('MPLCONFIGDIR',str(R/'runtime/matplotlib'))
import numpy as np
import cv2,trimesh
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

def firewall():
    def audit(event,args):
        if event!='open' or not isinstance(args[0],(str,bytes)):return
        p=Path(os.fsdecode(args[0])).resolve();s=str(p);name=p.name.lower()
        if '/gt_mapping/'in s or '/private_gt/'in s or '/evaluation_exports/'in s or name.endswith('.blend')or name.startswith('gt_')or 'oracle'in name:raise PermissionError('GT prohibited '+s)
        flags=args[2]if len(args)>2 and isinstance(args[2],int)else 0;mode=args[1]if len(args)>1 and isinstance(args[1],str)else''
        if s.startswith(('/home/liu/polyp_research/','/home/liu/new-polyp-dxy/'))and(any(c in mode for c in 'wax+')or flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC)):raise PermissionError('Historical assets read only '+s)
    sys.addaudithook(audit)
firewall()
def load(p):return json.loads(Path(p).read_text())
def clean(x):
    if isinstance(x,dict):return {str(k):clean(v)for k,v in x.items()}
    if isinstance(x,(list,tuple)):return [clean(v)for v in x]
    if isinstance(x,np.ndarray):return clean(x.tolist())
    if isinstance(x,(np.integer,np.bool_)):return x.item()
    if isinstance(x,(float,np.floating)):return float(x)if np.isfinite(x)else None
    return x
def save(p,x):
    p=R/p;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(clean(x),ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def csvsave(p,rows):
    with (R/p).open('w',newline='')as f:
        w=csv.DictWriter(f,list(dict.fromkeys(k for r in rows for k in r)),lineterminator='\n');w.writeheader()
        for row in rows:w.writerow({k:json.dumps(clean(v),ensure_ascii=False)if isinstance(v,(dict,list,tuple,np.ndarray))else clean(v)for k,v in row.items()})
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb')as f:
        for b in iter(lambda:f.read(2**20),b''):h.update(b)
    return h.hexdigest()
def config():return load(R/'parameters.json')
def cases():return load(R/'provenance/CASES.json')
def fields(c):return dict(np.load(PREV/f'local_fields/{c["id"]}_fields.npz'))
def stats(v):
    v=np.asarray(v,float);v=v[np.isfinite(v)]
    return dict(n=len(v),median=np.median(v)if len(v)else None,p95=np.percentile(v,95)if len(v)else None,max=v.max()if len(v)else None)
def source_components(pack,uv):
    n,lab,st,_=cv2.connectedComponentsWithStats((pack['labels']==1).astype(np.uint8));largest=1+np.argmax(st[1:,cv2.CC_STAT_AREA])
    return lab,lab[uv[:,1],uv[:,0]],largest

def local_anchors(uv,component,lab,values,conf):
    """Fixed square source neighborhood, lower-quartile reference, no kNN search."""
    half=conf['source_window_pixels']//2;offset=np.arange(-half,half+1);dx,dy=np.meshgrid(offset,offset);dx=dx.ravel();dy=dy.ravel();h,w=lab.shape
    images=[]
    for v in values:
        a=np.full((h,w),np.nan);a[uv[:,1],uv[:,0]]=v;images.append(a)
    anchors=[np.full(len(uv),np.nan)for _ in values];support=[np.zeros(len(uv),int)for _ in values]
    for start in range(0,len(uv),conf['chunk_points']):
        stop=min(start+conf['chunk_points'],len(uv));x=uv[start:stop,0,None]+dx;y=uv[start:stop,1,None]+dy;inside=(x>=0)&(x<w)&(y>=0)&(y<h);xx=np.clip(x,0,w-1);yy=np.clip(y,0,h-1);same=inside&(lab[yy,xx]==component[start:stop,None])
        for index,image in enumerate(images):
            patch=np.where(same,image[yy,xx],np.nan);n=np.isfinite(patch).sum(1);support[index][start:stop]=n;ok=n>=conf['minimum_local_valid_points']
            if ok.any():anchors[index][start:stop][ok]=np.nanpercentile(patch[ok],conf['local_reference_percentile'],axis=1)
    return anchors,support

def candidates(spacing_ratio,stretch_ratio,tier):
    return np.isfinite(spacing_ratio)&np.isfinite(stretch_ratio)&(spacing_ratio>=tier['spacing_ratio'])&(stretch_ratio>=tier['stretch_ratio'])

def face_components(faces):
    if not len(faces):return np.empty(0,int)
    edges=np.sort(faces[:,[[0,1],[1,2],[2,0]]].reshape(-1,2),axis=1);ids=np.repeat(np.arange(len(faces)),3);order=np.lexsort((edges[:,1],edges[:,0]));e=edges[order];f=ids[order];same=np.all(e[1:]==e[:-1],axis=1);a,b=f[:-1][same],f[1:][same]
    graph=coo_matrix((np.ones(2*len(a)),(np.r_[a,b],np.r_[b,a])),shape=(len(faces),len(faces))).tocsr()
    return connected_components(graph,directed=False)[1]
def edge_counts(faces):
    e=np.sort(faces[:,[[0,1],[1,2],[2,0]]].reshape(-1,2),axis=1)
    return np.unique(e,axis=0,return_counts=True)
def interior_deletion_patches(faces,deleted):
    e,count=edge_counts(faces);boundary=np.unique(e[count==1]);referenced=np.unique(faces);ii=np.flatnonzero(deleted);mapping=np.full(len(deleted),-1,int);mapping[ii]=np.arange(len(ii));pairs=e[np.all(deleted[e],axis=1)]
    if not len(ii):return 0
    a,b=mapping[pairs].T if len(pairs)else(np.array([],int),np.array([],int));graph=coo_matrix((np.ones(2*len(a)),(np.r_[a,b],np.r_[b,a])),shape=(len(ii),len(ii))).tocsr();n,labels=connected_components(graph,directed=False)
    touched=np.zeros(n,bool);touched[labels[np.isin(ii,boundary)]]=True;surface=np.zeros(n,bool);surface[labels[np.isin(ii,referenced)]]=True
    return int((~touched&surface).sum())

def prepare():
    prior=load(PREV/'provenance/INPUT_FREEZE.json');frozen=load(PREV/'provenance/DIAGNOSTIC_OUTPUTS_FROZEN.json')
    for x in prior['files']:assert sha(x['path'])==x['sha256'],x['path']
    for p,h in frozen['fields'].items():assert sha(p)==h,p
    cc=load(PREV/'provenance/CASES.json');save('provenance/CASES.json',cc);csvsave('metrics/input_identity.csv',cc)
    paths={Path(x['path'])for x in prior['files']}|{Path(p)for p in frozen['fields']}|set((R/'code').glob('*.py'))|{R/'parameters.json',R/'PROTOCOL.md',R/'provenance/CASES.json'}
    paths|=set((REPO/'visualization').glob('*.py'))|set((REPO/'visualization').glob('*.json'))|{REPO/'experiments/TASK-PHASEC-C0-M0-E0-001/code/visualize.py'}
    for n in ['Fig1_004_raw_and_C0.png','Fig3_005_Ring_below_layers.png']:paths.add(REPO/'experiments/TASK-PHASEC-C0-M0-E0-001/figures'/n)
    save('provenance/INPUT_MANIFEST.json',dict(UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),files=[dict(path=str(p),sha256=sha(p),bytes=p.stat().st_size)for p in sorted(paths)],GT_used=False,prior_fields_exact=True))
    print('PREPARED',len(paths),'frozen inputs/source files',flush=True)
def verify():
    for p in load(R/'provenance/INPUT_MANIFEST.json')['files']:assert sha(p['path'])==p['sha256'],p['path']

def run():
    verify();conf=config();rows=[];risk=[]
    for c in cases():
        a=fields(c);P=a['XYZ_mm'];uv=np.c_[a['source_u'],a['source_v']];pack=dict(np.load(c['pack']));m=trimesh.load(c['mesh'],process=False);assert len(P)==c['points']and np.allclose(P,m.vertices,rtol=0,atol=1e-5)
        z=pack['depth_mm'][uv[:,1],uv[:,0]];sampling=a['knn_k_distance_mm']/z;stretch=a['adjacency_perspective_stretch_max'];lab,comp,largest=source_components(pack,uv)
        (anchor_k,anchor_s),support=local_anchors(uv,comp,lab,[sampling,stretch],conf)
        with np.errstate(invalid='ignore',divide='ignore'):
            ratio_k=sampling/anchor_k;ratio_s=stretch/anchor_s
        valid=np.isfinite(ratio_k)&np.isfinite(ratio_s)&(anchor_k>0)&(anchor_s>0);ratio_k[~valid]=np.nan;ratio_s[~valid]=np.nan
        masks={t:candidates(ratio_k,ratio_s,v)for t,v in conf['presets'].items()}
        assert not np.any(masks['C']&~masks['M'])and not np.any(masks['M']&~masks['A'])
        rgb=cv2.imread(c['RGB'])[:,:,::-1][uv[:,1],uv[:,0]];base=R/'local_results'/c['id'];base.mkdir(exist_ok=True)
        trimesh.points.PointCloud(P,colors=rgb).export(base/'Raw.ply')
        payload=dict(XYZ_mm=P,source_u=uv[:,0],source_v=uv[:,1],group=c['group'],actual_video=c['video'],reference_frame=c['reference'],original_faces=m.faces,spacing_depth_normalized=sampling,local_spacing_anchor=anchor_k,local_stretch_anchor=anchor_s,spacing_ratio=ratio_k,stretch_ratio=ratio_s,valid_support=valid,local_spacing_count=support[0],local_stretch_count=support[1],original_D0=a['D0'],original_D1=a['D1'])
        rawcl=face_components(m.faces);areas=m.area_faces;rawca=np.bincount(rawcl,weights=areas);main=int(rawca.argmax());rawmain=rawcl==main;rawarea=float(rawca[main]);rawedges,rawcounts=edge_counts(m.faces);rawborder=set(map(tuple,rawedges[rawcounts==1]));minor=comp!=largest;cut=np.quantile(uv[minor,1],.8)if minor.any()else np.inf
        cohorts={'possible_stalk_proxy':minor&(uv[:,1]>=cut),'Ring_near':a['Ring_near'],'Mask_boundary':a['boundary'],'compact_sampling_control':sampling<=np.median(sampling),'raw_sparse_stretched_proxy':(sampling>=np.quantile(sampling,.75))&(stretch>=4),'main_source_component':comp==largest}
        if c['group']=='G01':
            below=P[:,2]<-.6
            if below.any():
                cut2=np.quantile(P[below,1],[1/3,2/3]);cohorts['Ring_below_relative_right_third']=below&(P[:,1]>cut2[1]);cohorts['Ring_below_relative_left_third']=below&(P[:,1]<=cut2[0])
        for tier,deleted in masks.items():
            keep=~deleted;ids=np.flatnonzero(keep);mapback=np.full(len(P),-1,int);mapback[ids]=np.arange(len(ids));facekeep=~deleted[m.faces].any(1);faces=m.faces[facekeep];cl=face_components(faces);ca=np.bincount(cl,weights=areas[facekeep])if len(cl)else np.array([]);mainremaining=rawmain[facekeep];pieceareas=np.bincount(cl[mainremaining],weights=areas[facekeep][mainremaining])if mainremaining.any()else np.array([])
            edge,count=edge_counts(faces);boundary=set(map(tuple,edge[count==1]));marked=rgb.copy();marked[deleted]=[220,25,25]
            trimesh.points.PointCloud(P,colors=marked).export(base/f'Candidate_Marked_{tier}.ply');trimesh.points.PointCloud(P[keep],colors=rgb[keep]).export(base/f'Cleaned_{tier}.ply')
            trimesh.Trimesh(vertices=m.vertices[keep],faces=mapback[faces],process=False).export(base/f'Cleaned_{tier}_original_faces.ply')
            payload['candidate_'+tier]=deleted;payload['cleaned_'+tier+'_original_point_indices']=ids;payload['cleaned_'+tier+'_original_face_indices']=np.flatnonzero(facekeep)
            row=dict(id=c['id'],group=c['group'],video=c['video'],morphology=c['morphology'],ring=c['ring'],condition=c['condition'],tier=tier,status='DERIVED_EXPERIMENTAL_NOT_GT_CERTIFIED',original_points=len(P),deleted_points=int(deleted.sum()),deleted_fraction=float(deleted.mean()),kept_points=int(keep.sum()),unknown_kept=int((~valid).sum()),original_faces=len(m.faces),removed_faces=int((~facekeep).sum()),kept_faces=int(facekeep.sum()),original_area_mm2=float(areas.sum()),removed_area_mm2=float(areas[~facekeep].sum()),raw_main_component_area_mm2=rawarea,raw_main_area_retained_fraction=float(areas[facekeep&rawmain].sum()/rawarea),largest_piece_of_raw_main_fraction=float(pieceareas.max()/rawarea)if len(pieceareas)else 0,raw_face_components=len(rawca),cleaned_face_components=len(ca),raw_main_remaining_pieces=int(np.count_nonzero(pieceareas)),raw_boundary_edges=len(rawborder),cleaned_boundary_edges=len(boundary),new_boundary_edges=len(boundary-rawborder),interior_deletion_patches=interior_deletion_patches(m.faces,deleted),spacing_ratio=stats(ratio_k),stretch_ratio=stats(ratio_s),GT_accuracy=None)
            for name,sel in cohorts.items():
                frac=float(deleted[sel].mean())if sel.any()else None;row[name+'_N']=int(sel.sum());row[name+'_deleted']=int((deleted&sel).sum());row[name+'_deleted_fraction']=frac
                risk.append(dict(id=c['id'],group=c['group'],condition=c['condition'],tier=tier,cohort=name,original_support=int(sel.sum()),deleted=int((deleted&sel).sum()),kept=int((keep&sel).sum()),meaning='frozen observation proxy, not true anatomical/error labels'))
            g=conf['review_guards'];checks={'main_area':row['raw_main_area_retained_fraction']>=g['raw_main_component_area_retained_minimum'],'main_continuity':row['largest_piece_of_raw_main_fraction']>=g['largest_remaining_piece_of_raw_main_minimum'],'stalk_proxy':row['possible_stalk_proxy_deleted_fraction']is None or row['possible_stalk_proxy_deleted_fraction']<=g['possible_stalk_proxy_removal_maximum'],'Ring_near':row['Ring_near_deleted_fraction']is None or row['Ring_near_deleted_fraction']<=g['Ring_near_removal_maximum'],'compact':row['compact_sampling_control_deleted_fraction']<=g['compact_sampling_control_removal_maximum'],'interior_patches':row['interior_deletion_patches']<=g['interior_deletion_patch_maximum']};row['engineering_guards']=checks;row['engineering_guard_pass']=all(checks.values());rows.append(row)
            print(c['id'],tier,'delete',int(deleted.sum()),'main retention',round(row['raw_main_area_retained_fraction'],5),'interior',row['interior_deletion_patches'],'guard',row['engineering_guard_pass'],flush=True)
        np.savez_compressed(base/'Raw_Marked_Cleaned_identities.npz',**payload)
    save('metrics/reference_results.json',rows);csvsave('metrics/reference_results.csv',rows);save('metrics/region_risks.json',risk);csvsave('metrics/region_risks.csv',risk)
    records=[dict(path=str(p.relative_to(R)),sha256=sha(p),bytes=p.stat().st_size)for p in sorted((R/'local_results').rglob('*'))if p.is_file()]
    save('provenance/OUTPUTS_FROZEN.json',dict(UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),files=records,presets_evaluated=['C','M','A'],new_upstream_predictions=0,GT_used=False,original_assets_changed=False))
    verify();print('COMPLETE',len(rows),'reference/tier rows;',len(records),'local derived artifacts',flush=True)

if __name__=='__main__':
    if sys.argv[1]=='prepare':prepare()
    elif sys.argv[1]=='run':run()
