"""Display/source consistency checks only; no reconstruction accuracy metrics."""
import ast,subprocess
import scene004 as s
np=s.np;R=s.R;checks=[]
def check(name,value,**detail):
    assert bool(value),name;checks.append(dict(check=name,passed=True,**detail))
def main():
    c=s.load(R/'provenance/SELECTED004.json');m=s.load(R/'metrics/SCENE004.json');cfg=s.load(R/'config.json');out=R/'local_scenes/G01_004_same_camera_ref03';layers=dict(np.load(out/'Point_layers_and_source_ids.npz'));bg=dict(np.load(out/'Background_FULL_DISPLAY_ONLY.npz'));p=dict(np.load(c['pack']));source=dict(np.load(c['source_points']));uv=source['uv'];small=np.asarray(s.Image.open(c['RGB']).convert('RGB'));h,w=small.shape[:2]
    check('only_G01_video004_selected',m['actual_video']=='004'and c['id']=='G01_004_ref03'and not cfg['other_videos_enabled'])
    files=s.load(R/'provenance/INPUT004.json')['files'];check('all_used_frozen_input_hashes_unchanged',all(s.sha(x['path'])==x['sha256']for x in files),files=len(files))
    check('full_frozen_c2w_including_roll_unchanged',np.array_equal(np.asarray(m['c2w']),p['pose'])and np.array_equal(p['pose'],np.load(c['camera_file'])['c2w'][c['reference_index']]))
    check('source_intrinsics_unchanged',np.array_equal(m['source_K'],p['K']))
    K=s.base.scaled_intrinsics(p['K'],(w,h),m['native_image_size']);check('native_intrinsics_only_pixel_center_resize',np.array_equal(K,m['native_K'])and np.array_equal(K,layers['K_native']))
    check('no_independent_rotation_or_P0_crop',cfg['observation_rotation']is None and cfg['polyp_crop']is None and m['P0_points_cropped']==0)
    check('all_24343_original_P0_coordinates_preserved_exactly',np.array_equal(source['points_mm'],layers['P0_XYZ_mm'])and len(layers['P0_XYZ_mm'])==24343 and np.array_equal(layers['P0_source_u'],uv[:,0])and np.array_equal(layers['P0_source_v'],uv[:,1]))
    projected,_=s.base.project_camera(source['points_mm'],p['K'],p['pose']);check('source_pixel_identity_projection_interface',np.max(abs(projected-uv))<1e-8,meaning='numerical input/projection identity, not geometry accuracy')
    a=bg['display_mask'];u=bg['source_u'][a];v=bg['source_v'][a];B=bg['XYZ_mm'][a]
    check('background_only_original_background_Mask_pixels',np.all(p['labels'][v,u]==0)and len(B)==30336)
    check('background_has_no_Polyp_source_pixel_overlap',not np.intersect1d(uv[:,1]*w+uv[:,0],v*w+u).size)
    check('background_is_frozen_depth_3D_backprojection',np.allclose(B,s.unproject(np.c_[u,v],p['depth_mm'][v,u],p['K'],p['pose']),rtol=0,atol=1e-8)and np.array_equal(B,layers['background_display_XYZ_mm']))
    check('background_RGB_exact_from_same_frame',np.array_equal(bg['rgb'][a],small[v,u]/255.))
    check('background_no_world_crop_or_fake_depth',cfg['background_world_z_clip']is None and cfg['background_world_radial_clip']is None and not m['background_approximation_used'])
    ring_path=s.Path('/home/liu/polyp_research/ring_anchor_3d/experiments/surface_fusion_v2/inputs/R10_ring.obj');ring=s.trimesh.load(ring_path,process=False);scene=s.SameCameraScene(ring,K,p['pose'],m['native_image_size'],cfg['open3d_vendor'])
    plt=s.base.configure();fig,ax=plt.subplots();image,drawn,info=scene.draw(ax,source['points_mm'],small[uv[:,1],uv[:,0]]/255.,B,bg['rgb'][a],point_size=.8)
    check('Polyp_and_Background_share_one_scatter_artist',len(ax.collections)==1)
    artist=ax.collections[0];check('same_original_point_style_size_opacity_edges',np.array_equal(artist.get_sizes(),[.8])and artist.get_alpha()is None and np.all(artist.get_linewidths()==0)and artist.get_rasterized())
    allP=np.r_[source['points_mm'],B];allRGB=np.r_[small[uv[:,1],uv[:,0]]/255.,bg['rgb'][a]];alluv,z=s.base.project_camera(allP,K,p['pose']);order=np.argsort(-z[drawn]);check('shared_artist_uses_projected_points_and_true_RGB',np.allclose(artist.get_offsets(),alluv[drawn][order],atol=1e-10)and np.array_equal(artist.get_facecolors()[:,:3],allRGB[drawn][order]))
    check('perspective_CAD_and_points_use_identical_camera',np.array_equal(scene.K,K)and np.array_equal(scene.c2w,p['pose']))
    check('CAD_original_mesh_and_thickness_unchanged',np.array_equal(scene.mesh.vertices,ring.vertices)and len(ring.faces)==32768 and abs(np.ptp(ring.vertices[:,2])-1.2)<1e-5)
    check('CAD_opaque_black_actual_mesh_first_hits',np.array_equal(np.unique(image[:,:,3]),[0.,1.])and image[:,:,:3].max()<.1 and (image[:,:,3]==1).sum()>1000)
    center_uv,_=s.base.project_camera(ring.centroid[None],K,p['pose']);x,y=np.rint(center_uv[0]).astype(int);check('CAD_has_projected_open_center_not_filled_bar',image[y,x,3]==0)
    check('visible_background_present_after_CAD',info['Background_drawn']==29853 and info['Background_drawn']>1000)
    plt.close(fig)
    native=np.asarray(s.Image.open(out/'Selected_Real_Frame.png').convert('RGB'));scene_image=np.asarray(s.Image.open(out/'Local_3D_Scene.png').convert('RGB'));pair=np.asarray(s.Image.open(out/'Real_vs_3D.png').convert('RGB'));H,W=native.shape[:2]
    check('real_and_scene_same_native_resolution',native.shape==scene_image.shape==(720,1280,3))
    check('comparison_pastes_both_views_without_zoom_or_crop',np.array_equal(pair[78:78+H,:W],native)and np.array_equal(pair[78:78+H,W+16:W+16+W],scene_image))
    replay=s.load(R/'metrics/REPLAY_CHECK.json');check('four_images_independent_replay_byte_identical',replay['status']=='PASS'and len(replay['files'])==4 and all(x['independent_replay_byte_identical']for x in replay['files']))
    figure_names=['Selected_Real_Frame.png','Local_3D_Scene.png','Real_vs_3D.png','Projection_Overlay.png'];figures=[]
    for name in figure_names:
        q=R/'figures/G01_004_same_camera'/name;im=s.Image.open(q);im.verify();check(name+'_matches_local_source',s.sha(q)==s.sha(out/name));figures.append(dict(path=str(q.relative_to(R)),sha256=s.sha(q),bytes=q.stat().st_size))
    for root,snap in s.load(R/'provenance/protected_worktrees.json').items():
        def git(*a):return subprocess.check_output(['git','-C',root,*a])
        idx=s.Path(git('rev-parse','--git-path','index').decode().strip());idx=idx if idx.is_absolute()else s.Path(root)/idx
        check(root+'_HEAD_index_status_and_existing_user_changes_preserved',git('rev-parse','HEAD').decode().strip()==snap['HEAD']and s.hashlib.sha256(git('status','--porcelain=v1','-uall','-z')).hexdigest()==snap['status_sha256']and s.sha(idx)==snap['index_sha256']and all(s.sha(s.Path(root)/q)==h for q,h in snap['modified_sha256'].items()))
    original=s.load(s.REPO/'visualization/real_p0_renderer_provenance.json');text=s.Path(original['original_script']).read_text();oldnodes=[ast.dump(n,include_attributes=False)for n in ast.parse(text).body if isinstance(n,ast.FunctionDef)and n.name in ['basis','view','limits']];bundle=[ast.dump(n,include_attributes=False)for n in ast.parse((s.REPO/'visualization/_phasec_c0_view_frozen.py').read_text()).body if isinstance(n,ast.FunctionDef)];check('original_legacy_drawing_functions_still_unchanged',oldnodes==bundle)
    s.save(R/'metrics/VALIDATION004.json',dict(status='PASS',total_checks=len(checks),checks=checks,GT_used=False,geometry_accuracy_evaluated=False,other_videos_run_after_correction=0))
    s.save(R/'provenance/FIGURE004_MANIFEST.json',dict(images=figures,only_selected_video='004',only_current_sample_published=True))
    source_files=[s.REPO/'visualization/real_p0_renderer.py',s.REPO/'visualization/same_camera_scene.py',R/'code/scene004.py',R/'code/validate004.py',R/'config.json',R/'PROTOCOL.md'];s.save(R/'provenance/EXECUTION004_SOURCES.json',dict(files=[dict(path=str(q),sha256=s.sha(q))for q in source_files],mainline_base_commit='02dee8092dce9f89d050bccca35aa51768988645',camera_extension_in_experiment_branch_only=True))
    print('VALIDATION004_PASS',len(checks),'source/render checks; no accuracy evaluation',flush=True)
if __name__=='__main__':main()
