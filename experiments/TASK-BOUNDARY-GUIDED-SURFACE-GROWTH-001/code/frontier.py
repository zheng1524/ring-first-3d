"""Actual original-triangle frontier and source-index scene representation."""
from assets import *
def block_P(block):return transform(source(block['reference'])['P'],np.array(block['H']))
def block_N(block):return normal(block['reference'])[0]@np.array(block['H'])[:3,:3].T
def initial_scene(sid):
    cid=load(R/'provenance/MAIN_SURFACES_SELECTED.json')['selections'][sid];blocks=[]
    parts=face_partitions(cid);parts.sort(key=lambda f:-source(cid)['areas'][f].sum())
    for i,ids in enumerate(parts):blocks.append(dict(id='main_'+str(i),reference=cid,face_ids=ids,H=np.eye(4),generation=0,face_generations=np.zeros(len(ids),int),role='PRIMARY'if i==0 else'PRIMARY_AUXILIARY_PRESERVED',stiffness=cfg()['growth_primary_stiffness'],original_component=int(face_components(source(cid)['F'])[ids[0]])))
    if sid[:3]in ['G06','G07','G08']:
        c=next(c for c in cases()if sceneid(c)==sid and c.get('new_reference'));z=old_F2(c['id']);ids=np.flatnonzero(z['accepted'][source(c['id'])['F']].all(1))
        for i,f in enumerate(face_partitions(c['id'],ids)):
            blocks.append(dict(id='seed_'+str(i),reference=c['id'],face_ids=f,H=np.eye(4),generation=0,face_generations=np.zeros(len(f),int),role='ENGINEERING_ACCEPTED_SEED',stiffness=cfg()['growth_existing_patch_stiffness'],original_component=int(face_components(source(c['id'])['F'])[f[0]])))
    return blocks
def mesh_arrays(blocks):
    P=[];F=[];N=[];bid=[];fid=[];offset=0
    for i,b in enumerate(blocks):
        s=source(b['reference']);p=block_P(b);fs=s['F'][b['face_ids']];P.append(p);F.append(fs+offset);n=block_N(b);q=n[fs].mean(1);q/=np.maximum(np.linalg.norm(q,axis=1)[:,None],1e-12);N.append(q);bid.append(np.full(len(fs),i,int));fid.append(np.array(b['face_ids']));offset+=len(p)
    return dict(P=np.concatenate(P),F=np.concatenate(F),face_normals=np.concatenate(N),face_blocks=np.concatenate(bid),original_face_ids=np.concatenate(fid))
def display_arrays(blocks):
    P=[];C=[];ref=[];ids=[];generation=[]
    for i,b in enumerate(blocks):
        s=source(b['reference']);ix=np.unique(s['F'][b['face_ids']]);P.append(block_P(b)[ix]);C.append(s['C'][ix]);ref.extend([b['reference']]*len(ix));ids.append(ix);g=np.zeros(len(s['P']),int)
        for j in range(3):np.maximum.at(g,s['F'][b['face_ids'],j],b['face_generations'])
        generation.append(g[ix])
    return dict(P=np.concatenate(P),C=np.concatenate(C),references=np.array(ref),original_ids=np.concatenate(ids),generation=np.concatenate(generation))
def edge_data(F):
    e=np.sort(np.r_[F[:,[0,1]],F[:,[1,2]],F[:,[2,0]]],1);face=np.tile(np.arange(len(F)),3);order=np.lexsort((e[:,1],e[:,0]));e=e[order];face=face[order];unique,start,count=np.unique(e,axis=0,return_index=True,return_counts=True)
    return unique,start,count,face,e
@lru_cache(None)
def source_edge_maps(cid):
    s=source(cid);E,_,C,_,_=edge_data(s['F']);rawmap={tuple(e):int(c)for e,c in zip(E,C)};E,_,C,_,_=edge_data(s['F'][clean_faces(cid)]);return rawmap,{tuple(e):int(c)for e,c in zip(E,C)}
def frontier(blocks,save_tag=None):
    mids=[];lengths=[];normals=[];eligible=[];which=[];rows=[];all_edges=[];details=[]
    for j,b in enumerate(blocks):
        s=source(b['reference']);fids=np.asarray(b['face_ids']);F=s['F'][fids];E,start,count,face,expanded=edge_data(F);ix=np.flatnonzero(count==1);E=E[ix];neighbor=fids[face[start[ix]]];p=block_P(b);m=p[E].mean(1);uv=s['uv'][E].mean(1);uv=np.floor(uv+.5).astype(int);labels=s['p']['labels'];ring=cv2.distanceTransform((labels!=2).astype(np.uint8),cv2.DIST_L2,5)[uv[:,1],uv[:,0]];mask=cv2.distanceTransform((labels==1).astype(np.uint8),cv2.DIST_L2,5)[uv[:,1],uv[:,0]]
        rawmap,cleanmap=source_edge_maps(b['reference']);kind=[]
        for k,e in enumerate(E):
            key=tuple(e)
            if ring[k]<=cfg()['growth_frontier_Ring_pixels']:label='RING_OCCLUSION'
            elif cleanmap.get(key,0)==1 and rawmap.get(key,0)>1:label='CLEANING_INTERNAL_HOLE'
            elif rawmap.get(key,0)==1 and mask[k]<=cfg()['growth_boundary_Mask_pixels']:label='OBSERVATION_TERMINATION'
            elif rawmap.get(key,0)==1:label='DEPTH_DISCONTINUITY_OR_RAW_HOLE'
            elif cleanmap.get(key,0)>1:label='GROWTH_SELECTION_FRONTIER'if b['role']!='PRIMARY_AUXILIARY_PRESERVED'else'UNKNOWN_AUXILIARY'
            else:label='UNKNOWN'
            kind.append(label)
        kind=np.array(kind);ok=np.isin(kind,['OBSERVATION_TERMINATION','GROWTH_SELECTION_FRONTIER','RING_OCCLUSION']);ok&=b['role']!='PRIMARY_AUXILIARY_PRESERVED';n=block_N(b)[E].mean(1);n/=np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-12);length=np.linalg.norm(p[E[:,0]]-p[E[:,1]],axis=1)
        for label in sorted(set(kind)):rows.append(dict(block=b['id'],reference=b['reference'],category=label,edges=int((kind==label).sum()),length_mm=float(length[kind==label].sum()),eligible_for_conditional_growth=label in ['OBSERVATION_TERMINATION','GROWTH_SELECTION_FRONTIER','RING_OCCLUSION'],Ring_requires_independent_disocclusion=label=='RING_OCCLUSION'))
        detail=dict(reference=b['reference'],block=b['id'],original_vertex_edges=E,XYZ_endpoints=p[E],source_uv_endpoints=s['uv'][E],normals=n,kind=kind,eligible=ok,adjacent_original_face=neighbor,source_camera_view_direction=s['p']['pose'][:3,3]-m,H_source_to_scene=b['H'],boundary_reliability=np.where(kind=='OBSERVATION_TERMINATION',.8,np.where(kind=='GROWTH_SELECTION_FRONTIER',.7,np.where(kind=='RING_OCCLUSION',.4,0.))))
        if save_tag:
            path=R/'local_results/frontiers'/save_tag/(str(j)+'.npz');path.parent.mkdir(parents=True,exist_ok=True);np.savez_compressed(path,**detail)
        mids.append(m);lengths.append(length);normals.append(n);eligible.append(ok);which.append(np.full(len(E),j,int));all_edges.append(p[E]);details.append(detail)
    out=dict(midpoints=np.concatenate(mids),lengths=np.concatenate(lengths),normals=np.concatenate(normals),eligible=np.concatenate(eligible),blocks=np.concatenate(which),XYZ_edges=np.concatenate(all_edges),categories=np.concatenate([d['kind']for d in details]),rows=rows,total_length_mm=float(sum(x.sum()for x in lengths)),eligible_length_mm=float(sum(x[y].sum()for x,y in zip(lengths,eligible))))
    if save_tag:save('metrics/frontier_'+save_tag+'.json',rows)
    return out
def snapshot(sid,step,blocks,record):
    tag=sid+'_S'+str(step).zfill(3);path=R/'local_results/scenes'/(tag+'.json');path.parent.mkdir(exist_ok=True);save(str(path.relative_to(R)),dict(scene=sid,step=step,blocks=blocks,record=record,GT_used=False));f=frontier(blocks,tag);return tag,f
def load_scene(sid,step='final'):
    if step=='final':return load(R/f'local_results/scenes/{sid}_Final.json')['blocks']
    return load(R/f'local_results/scenes/{sid}_S{int(step):03d}.json')['blocks']
if __name__=='__main__':
    rows=[]
    for sid in load(R/'provenance/MAIN_SURFACES_SELECTED.json')['selections']:
        b=initial_scene(sid);tag,f=snapshot(sid,0,b,dict(kind='initial_selected_main_plus_prior_engineering_seed_controls',adjustable_derived_versions=True));rows.append(dict(scene=sid,stage='S0',blocks=len(b),original_complete_face_area_mm2=sum(source(x['reference'])['areas'][x['face_ids']].sum()for x in b),frontier_length_mm=f['total_length_mm'],eligible_frontier_length_mm=f['eligible_length_mm']))
    both('initial_frontier_summary',rows);print('Initial actual frontiers saved',flush=True)
