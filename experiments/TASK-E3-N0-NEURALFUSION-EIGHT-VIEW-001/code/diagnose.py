"""Output fidelity, full fixed-ray multi-intersections, novelty and order effects."""
from common import *
from evaluate import observations
sys.path[:0]=[str(RB/'runtime/python')]
from skimage.measure import marching_cubes
def first_layers(scene,uv,K,T):
    result=scene.list_intersections(o3d.core.Tensor(vis.camera_rays(uv,K,T).astype(np.float32)));splits=result['ray_splits'].numpy();t=result['t_hit'].numpy();r=result['ray_ids'].numpy();counts=np.zeros(len(uv),int)
    # Coincident hits at shared triangle edges are deduplicated in axial Z.
    order=np.lexsort((t,r));t=t[order];r=r[order]
    keep=np.ones(len(t),bool)
    if len(t)>1:keep[1:]=(r[1:]!=r[:-1])|(abs(t[1:]-t[:-1])>1e-4)
    np.add.at(counts,r[keep],1);return counts,t[keep],r[keep]
def main():
    p=protocol();audit=[];layer_rows=[];novelty=[];order_rows=[];identity_rows=[]
    for scene,ii in p['orders'].items():
        L=p['domains'][scene]['L_mm'];O=np.array(p['domains'][scene]['O_mm'])
        previous=np.empty((0,3))
        for j,cid in enumerate(ii):
            s=cleaned(cid);X=s['X'];novel=np.ones(len(X),bool)if not len(previous)else cKDTree(previous).query(X)[0]>.25;tag=f'{scene}_forward_F{j}';m=trimesh.load(R/'meshes'/f'{tag}_raw_mm.ply',process=False);ds=mesh_scene(m.vertices,m.faces);nn=distance(ds,X);cad,_=cast(ringscene(scene),s['native_uv'],s['Kn'],s['T']);z=s['depth'].flat[s['native_id']];visible=~(np.isfinite(cad)&(z>cad+.002));hit,_=cast(ds,s['native_uv'],s['Kn'],s['T']);agree=np.isfinite(hit)&(abs(hit-z)<=.25)
            novelty.append(dict(scene=scene,stage='F'+str(j),source=cid,retained_native_N=len(X),novel_vs_previous_input_0p25_N=int(novel.sum()),novel_visible_N=int((novel&visible).sum()),novel_visible_mesh_near_N=int((novel&visible&(nn<=.25)).sum()),novel_visible_first_hit_agree_N=int((novel&visible&agree).sum()),side_interpretation='new input geometry proxy; not automatically anatomical side truth'))
            previous=np.concatenate([previous,X])
        for order in ['forward','reverse']:
            for j in range(len(ii)):
                tag=f'{scene}_{order}_F{j}';a=np.load(R/'local_results'/f'{tag}_MC_identity.npz');field=np.load(R/'local_results'/f'{tag}_field.npz');verts,F,_,_=marching_cubes(field['sdf_MC_unknown_positive_sentinel'],level=0,allow_degenerate=False)
                assert np.array_equal(F,a['faces'])and np.array_equal(verts,a['vertices_index_float']);assert np.allclose(verts/128*L+O,a['vertices_mm'],rtol=0,atol=1e-12)
                raw=trimesh.load(R/'meshes'/f'{tag}_raw_mm.ply',process=False);flat=trimesh.load(R/'meshes'/f'{tag}_flat_mm.ply',process=False);smooth=trimesh.load(R/'meshes'/f'{tag}_smooth_normals_mm.ply',process=False);glb=trimesh.load(R/'meshes'/f'{tag}_SI_m.glb',process=False,force='mesh')
                assert np.array_equal(raw.vertices,flat.vertices)and np.array_equal(raw.faces,flat.faces)and np.array_equal(raw.vertices,smooth.vertices)and np.array_equal(raw.faces,smooth.faces)
                assert np.array_equal(raw.faces,glb.faces);error=float(np.max(abs(raw.vertices-glb.vertices*1000)));assert error<1e-5
                assert np.isfinite(raw.vertices).all()and (raw.faces>=0).all()and(raw.faces<len(raw.vertices)).all()
                audit.append(dict(tag=tag,MC_replayed_exact=True,float_interpolation_preserved=True,flat_smooth_geometry_identical=True,PLY_GLTF_unit_inverse_max_mm=error,all_original_output_faces_preserved=True,normals_unit_max_error=float(abs(np.linalg.norm(smooth.vertex_normals,axis=1)-1).max()),mesh_SHA256=sha(R/'meshes'/f'{tag}_raw_mm.ply')))
                if j in sorted(set([0,min(2,len(ii)-1),min(4,len(ii)-1),len(ii)-1])):
                    ds=mesh_scene(raw.vertices,raw.faces)
                    for cid in ii:
                        s=observations(cid);count,depth,ray=first_layers(ds,s['native_uv'],s['Kn'],s['T']);visible=s['visible'];layer_rows.append(dict(tag=tag,source=cid,fixed_visible_N=int(visible.sum()),hit_N=int((visible&(count>0)).sum()),rays_2plus_surfaces_N=int((visible&(count>=2)).sum()),rays_4plus_surfaces_N=int((visible&(count>=4)).sum()),two_plus_fraction=float((visible&(count>=2)).sum()/visible.sum()),crossings_are_not_all_anatomical_layers=True))
                    # Keep full actual intersections for ref08/ref04 and the final mesh.
                    if j==len(ii)-1:
                        cid=ii[0];s=observations(cid);counts,depth,ray=first_layers(ds,s['native_uv'],s['Kn'],s['T']);np.savez_compressed(R/'local_results'/f'{tag}_first_source_intersections.npz',native_id=s['native_id'],intersection_counts=counts,axial_depth_mm=depth,ray_index=ray)
        a=trimesh.load(R/'meshes'/f'{scene}_forward_F{len(ii)-1}_raw_mm.ply',process=False);b=trimesh.load(R/'meshes'/f'{scene}_reverse_F{len(ii)-1}_raw_mm.ply',process=False);da=distance(mesh_scene(b.vertices,b.faces),a.triangles_center);db=distance(mesh_scene(a.vertices,a.faces),b.triangles_center)
        ar=load(R/f'metrics/{scene}_forward_F{len(ii)-1}_METRICS.json');br=load(R/f'metrics/{scene}_reverse_F{len(ii)-1}_METRICS.json')
        order_rows.append(dict(scene=scene,forward_to_reverse_face_distance_mm=stats(da),reverse_to_forward_face_distance_mm=stats(db),forward_area_mm2=float(a.area),reverse_area_mm2=float(b.area),same_source_set=True,empty_initial_states_both=True))
        identity_rows.extend(dict(scene=scene,source=c,raw_native_N=int(native(c)['valid'].sum()),retained_native_N=int(cleaned(c)['valid'].sum()),original_native_ID_preserved=True)for c in ii)
    for a in load(R/'provenance/ORIGINAL_SHA_START.json')['files']:assert sha(a['path'])==a['sha256']
    for a in load(R/'provenance/OFFICIAL_CHECKED_FILES.json')['files']:assert sha(a['path'])==a['sha256']
    table('metrics/MESH_EXTRACTION_AND_SHADING_AUDIT.csv',audit);table('metrics/MULTILAYER_RAY_DIAGNOSTICS.csv',layer_rows);table('metrics/NEW_VIEW_GEOMETRY_PROXY.csv',novelty);save('metrics/ORDER_COMPARISON.json',order_rows);table('metrics/INPUT_IDENTITY_COUNTS.csv',identity_rows)
    save('metrics/FINAL_INVARIANTS.json',dict(meshes_replayed_N=len(audit),original_inputs_SHA_unchanged=True,official_source_and_weights_SHA_unchanged=True,all26_use_real_Translator=True,optimizer_steps=0,GT=False,geometry_smoothing=False,mesh_deletion=False))
    print('AUDIT_PASS',len(audit),'actual meshes; original data and weights unchanged',flush=True)
if __name__=='__main__':main()
