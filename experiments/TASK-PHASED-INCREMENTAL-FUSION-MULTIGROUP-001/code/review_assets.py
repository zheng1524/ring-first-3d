"""Source-aware local scene exports and declared-view model consistency metrics."""
from pipeline import *
from triangle_projection import triangle_predict
def topology(m):
    lab=face_components(m.faces);ar=m.area_faces;pieces=np.bincount(lab,weights=ar);_,count=edge_counts(m.faces);return dict(faces=len(m.faces),components=len(pieces),largest_component_area_fraction=float(pieces.max()/pieces.sum()),nonmanifold_edges=int((count>2).sum()),boundary_edges=int((count==1).sum()),model_area_mm2=float(ar.sum()))
def ring_geometry(c):
    m=ring(c).copy();m.vertices=np.asarray(m.vertices)/1000;m.visual=trimesh.visual.TextureVisuals(material=trimesh.visual.material.PBRMaterial(baseColorFactor=[0,0,0,255],metallicFactor=0.,roughnessFactor=.8,doubleSided=True));m.metadata.update(identity='KNOWN_CAD',source_path=str(ring_path(c)),centerline_radius_mm=c['R_mm']);return m
def export(sc,mode):
    scene=trimesh.Scene();c=source(sc['main_reference'])['c'];scene.add_geometry(ring_geometry(c),node_name='Ring_KNOWN_CAD');contents=[]
    for rank,cid in enumerate(sc['reference_order']):
        a=dict(np.load(R/f'local_results/scenes/{sc["id"]}/{cid}_faces_exact.npz'));st=a['face_status']
        for k in [0,1,2,3,5]:
            take=st==k
            if mode=='primary_priority'and rank>0:take&=st==5
            if not take.any():continue
            fid=np.flatnonzero(take);F=a['faces'][fid];ids=np.unique(F);back=np.full(len(a['XYZ_mm']),-1,int);back[ids]=np.arange(len(ids));g=trimesh.Trimesh(a['XYZ_mm'][ids]/1000,back[F],vertex_colors=np.rint(a['RGB'][ids]*255).astype(np.uint8),process=False);g.metadata.update(reference=cid,group=sc['group'],actual_video=sc['video'],source_class=sc['class_legend'][str(k)],source_mesh_vertex_indices=ids.tolist(),original_vertex_N=int(a['original_vertex_N']),source_edge_original_ids=a['source_edge_original_ids'][ids].tolist(),parent_original_face_id=a['parent_original_face_id'][fid].tolist(),child_code=a['child_code'][fid].tolist(),parent_barycentric=a['parent_barycentric'][fid].tolist(),source_exact_file=str(R/f'local_results/scenes/{sc["id"]}/{cid}_faces_exact.npz'));scene.add_geometry(g,node_name=cid+'_'+sc['class_legend'][str(k)]);contents.append(dict(reference=cid,class_id=k,faces=len(fid)))
        if rank==0:
            used=np.unique(a['faces']);unused=applied(cid)['kept_original_indices'];unused=unused[~np.isin(unused,used)]
            if len(unused):g=trimesh.points.PointCloud(source(cid)['P'][unused]/1000,colors=np.rint(source(cid)['rgb'][unused]*255).astype(np.uint8));g.metadata.update(reference=cid,kind='ORIGINAL_P0_POINTS_WITHOUT_FACES',original_ids=unused.tolist());scene.add_geometry(g,node_name=cid+'_original_unreferenced_points')
        b=background(cid);sel=b['display'];g=trimesh.points.PointCloud(b['P'][sel]/1000,colors=np.rint(b['rgb'][sel]*255).astype(np.uint8));g.metadata.update(reference=cid,kind='ACTUAL_BACKGROUND_FROZEN_DEPTH',source_original_indices=np.flatnonzero(sel).tolist(),source_uv=b['uv'][sel].tolist());scene.add_geometry(g,node_name=cid+'_Background_RGB_XYZ')
    scene.metadata.update(task=R.name,scene=sc['id'],mode=mode,status=sc['status'],coordinate='independent local Ring frame, serialized meters, original millimeters',GT_used=False,source_contents=contents,primary_original_geometry_fixed=True,subdivision_is_original_triangle_only=True,unknown_conflict_not_certified=True)
    def extras(tree):
        for m in tree['meshes']:m.setdefault('extras',{}).update(clean(scene.geometry[m['name']].metadata))
    folder=R/'local_results/GLB';folder.mkdir(parents=True,exist_ok=True);p=folder/(sc['id']+'_'+mode+'.glb');scene.export(p,tree_postprocessor=extras);return dict(scene=sc['id'],group=sc['group'],mode=mode,path=str(p),bytes=p.stat().st_size,sha256=sha(p),geometries=len(scene.geometry),public_uploaded=False,status=sc['status'])
def main():
    outputs=[];rows=[];targets=[]
    for sc in load(R/'metrics/B_scenes.json'):
        t=target(sc['id']);targets.append(dict(scene=sc['id'],target=t,role='SELECTION_VIEW_USED_FOR_FUSION_NOT_INDEPENDENT'))
        if sc['group']=='G01':
            for tt in load(PHASE/'provenance/TARGETS_FROZEN.json'):
                if tt['video']==sc['video']and tt['role']=='holdout':targets.append(dict(scene=sc['id'],target=dict(tt,ring_case=sc['main_reference']),role='PREVIOUS_FROZEN_HOLDOUT_NOT_NEW_BLIND_TEST'))
    save('provenance/REVIEW_TARGETS_FROZEN.json',targets);save('provenance/REVIEW_EVALUATION_SOURCE.json',stamp([Path(__file__),R/'code/triangle_projection.py',R/'provenance/REVIEW_TARGETS_FROZEN.json']))
    for sc in load(R/'metrics/B_scenes.json'):
        for mode in ['primary_priority','evidence_preserved']:outputs.append(export(sc,mode))
        modes=['primary','second','core','evidence']+(['B','C']if sc['group']=='G01'else[])
        for mode in modes:
            if mode in ['B','C']:
                m=trimesh.load(ICF/('meshes/'+sc['video']+'_Polyp_'+('B_raw_multiref.ply'if mode=='B'else'C_confidence_fused.ply')),process=False);P=np.array(m.vertices);rgb=m.visual.vertex_colors[:,:3]/255.
            else:m=scene_mesh(sc,mode);P,rgb,_rr,_ii=scene_points(sc,mode)
            top=topology(m)
            for spec in [x for x in targets if x['scene']==sc['id']]:
                t=spec['target'];pred=point_projection(P,rgb,t);tri=triangle_predict(m,t);B=np.asarray(Image.open(t['RGB']).convert('RGB'));mask=cv2.imread(t['Mask'],0)==1;valid=(tri['kind']==1)&mask;pp=(pred['kind']==1)&mask;row=dict(scene=sc['id'],group=sc['group'],method=mode,target=t['id'],view_role=spec['role'],target_mask_N=int(mask.sum()),point_coverage_N=int(pp.sum()),point_coverage=float(pp.sum()/mask.sum()),triangle_coverage_N=int(valid.sum()),triangle_coverage=float(valid.sum()/mask.sum()),point_RGB=errors(pred,B,pp),triangle_RGB=errors(tri,B,valid),outside_target_mask_triangle_pixels=int(((tri['kind']==1)&~mask).sum()),topology=top,not_absolute_accuracy=True);rows.append(row);dest=R/f'local_results/coverage/{sc["id"]}/{mode}/{t["id"]}';dest.mkdir(parents=True,exist_ok=True);np.savez_compressed(dest/'source_RGB_prediction.npz',point_RGBA=pred['RGBA'],triangle_RGBA=tri['RGBA'],point_original_id=pred['source_original_id'],triangle_source_face_id=tri['face_id'],source_barycentric=tri['source_barycentric']);Image.fromarray(tri['RGBA']).save(dest/'Source_RGB_prediction.png')
        print('REVIEW_EXPORT',sc['id'],flush=True)
    save('metrics/GLB_INDEX.json',outputs);csvsave('metrics/GLB_INDEX.csv',outputs);save('metrics/E_visible_coverage.json',rows);csvsave('metrics/E_visible_coverage.csv',rows)
if __name__=='__main__':main()
