"""Source identity, exact XYZ layers and actual diagnostic-artist checks."""
import subprocess
import audit as a
np=a.np;R=a.R;checks=[]
def check(name,value,**extra):
    assert bool(value),name;checks.append(dict(check=name,passed=True,**extra))
def main():
    a.verify();cc=a.scenes();check('five_scenes_four_independent_groups',len(cc)==5 and len(set(c['group']for c in cc))==4 and sum(c['points']for c in cc)==76885)
    cfg=a.config();check('no_fixed_world_Z_or_point_subsampling',cfg['world_Z_cutoff']is None and not cfg['point_subsampling']and not cfg['point_coordinates_changed'])
    images=[];assets=[]
    for c in cc:
        cid=c['scene_id'];folder=R/'local_layers'/cid;layers=dict(np.load(folder/'Layers_L1-L4_XYZ_RGB.npz'));bg=dict(np.load(folder/'Raw_Background_FULL.npz'));P,uv,p,rgb=a.raw(c);meta=a.load(R/f'metrics/{cid}_audit.json');B=layers['background_XYZ_mm'];sel=bg['selection_'+str(cfg['background_selected_scale'])]
        check(cid+'_P0_XYZ_and_source_pixels_exact',np.array_equal(layers['P0_XYZ_mm'],P)and np.array_equal(layers['P0_source_u'],uv[:,0])and np.array_equal(layers['P0_source_v'],uv[:,1]))
        check(cid+'_P0_RGB_exact',np.array_equal(layers['P0_RGB'],rgb[uv[:,1],uv[:,0]]/255.))
        check(cid+'_background_exact_subset_no_point_moves',np.array_equal(B,bg['XYZ_mm'][sel])and np.array_equal(layers['background_source_u'],bg['source_u'][sel])and np.array_equal(layers['background_source_v'],bg['source_v'][sel]))
        u,v=bg['source_u'][sel],bg['source_v'][sel];check(cid+'_background_only_Mask0_and_true_RGB',np.all(p['labels'][v,u]==0)and np.array_equal(layers['background_RGB'],rgb[v,u]/255.))
        check(cid+'_background_frozen_depth_coordinate_binding',np.allclose(B,a.unproject(np.c_[u,v],p['depth_mm'][v,u],p['K'],p['pose']),atol=1e-8,rtol=0))
        check(cid+'_all_contact_witnesses_preserved',not np.any(bg['witness']&~sel))
        check(cid+'_three_nested_background_regions',not np.any(bg['selection_1.5']&~bg['selection_2.0'])and not np.any(bg['selection_2.0']&~bg['selection_2.5']))
        check(cid+'_source_camera_unchanged',np.array_equal(layers['source_c2w'],p['pose'])and np.array_equal(meta['source_c2w'],p['pose']))
        for name,delta in [('left',-1),('right',1)]:
            d=layers['diagnostic_'+name+'_c2w'];check(cid+'_'+name+'_actual_translation_not_rotation_only',np.array_equal(d[:3,:3],p['pose'][:3,:3])and np.allclose(d[:3,3]-p['pose'][:3,3],delta*p['pose'][:3,0],atol=1e-12))
        n=len(P)+len(B);st=meta['stages'];check(cid+'_L1_L2_L3_L4_count_contract',[x['total_points']for x in st[:4]]==[len(P),len(B),n,n])
        check(cid+'_all_five_stages_have_source_coordinate_and_style',len(st)==5 and all(s['source_XYZ']and s['coordinate_system']=='unchanged Ring local XYZ / millimeters / independent per video'and s['source_RGB']==c['RGB']and s['point_renderer']=='visualization.real_p0_renderer.draw_rgb_points'and s['point_size']==(.8 if s['stage']=='L5'else .08)for s in st))
        check(cid+'_diagnostic_all_points_no_CAD_culling_or_dense_glyphs',len(meta['panels'])==20 and all(x['input_points']==x['positive_depth_drawn']and not x['point_subsampling']and not x['background_image_used']and not x['CAD_hides_points']and x['glyph_size']==.08 and x['antialias']==False for x in meta['panels']))
        check(cid+'_XYZ_equal_mm_ranges',all(np.isclose(b[0][1]-b[0][0],b[1][1]-b[1][0])for b in meta['XYZ_mm_bounds'])and len(set(round(b[0][1]-b[0][0],8)for b in meta['XYZ_mm_bounds']))==1)
        frame=a.load(R/f'metrics/{cid}_frame_identity.json');check(cid+'_sequential_native_frame_bound',frame['decoder'].startswith('SEQUENTIAL_ZERO_BASED')and frame['raw_frame']==c['raw_frame']and frame['resize_storage_MAD']<1)
        for name in ['Layers_L1-L5.png','Camera_3Views.png','XYZ_3Views.png','Real_vs_3D.png']:
            path=R/'figures'/cid/name;im=a.Image.open(path);im.verify();im=a.Image.open(path);check(cid+'_'+name+'_valid_png',im.width>=2000 and im.height>=720);images.append(dict(scene_id=cid,path=str(path.relative_to(R)),sha256=a.sha(path),bytes=path.stat().st_size,width=im.width,height=im.height))
        for path in folder.iterdir():
            if path.is_file():assets.append(dict(path=str(path.relative_to(R)),sha256=a.sha(path),bytes=path.stat().st_size,public=False))
    # Inspect a live diagnostic canvas: no source image for L3, only CAD image for L4.
    c=cc[0];data=dict(np.load(R/'local_layers'/c['scene_id']/'Layers_L1-L4_XYZ_RGB.npz'));P=np.r_[data['P0_XYZ_mm'],data['background_XYZ_mm']];RGB=np.r_[data['P0_RGB'],data['background_RGB']];mesh=a.trimesh.load(a.ring_path(c),process=False);basis=a.base.basis(cfg['layer_oblique_angle_degrees']);bounds=a.diag.square_bounds([P,mesh.vertices],[basis])[0];scene=a.SameCameraScene(mesh,data['source_K'],data['source_c2w'],tuple(data['source_image_size']),cfg['open3d_vendor']);plt=a.base.configure();fig,ax=plt.subplots(1,2)
    for i in [0,1]:a.diag.points(ax[i],P,RGB,bounds,'check',point_size=.08,alpha=1.,basis=basis,ring_scene=scene if i else None)
    check('L3_has_no_image_artist_L4_only_CAD',len(ax[0].images)==0 and len(ax[1].images)==1 and len(ax[0].collections)==1 and len(ax[1].collections)==1)
    artist=ax[0].collections[0];q=np.c_[P@basis[1],P@basis[2]];order=np.argsort(P@basis[0]);check('actual_artist_is_original_XYZ_point_projection_and_RGB',np.array_equal(artist.get_offsets(),q[order])and np.array_equal(artist.get_facecolors()[:,:3],RGB[order]))
    check('actual_diagnostic_point_style_preserves_visible_glyphs',np.array_equal(artist.get_sizes(),[.08])and artist.get_alpha()==1 and np.all(artist.get_linewidths()==0)and not np.any(artist.get_antialiased()));plt.close(fig)
    for root,snap in a.load(R/'provenance/protected_worktrees.json').items():
        def git(*args):return subprocess.check_output(['git','-C',root,*args])
        idx=a.Path(git('rev-parse','--git-path','index').decode().strip());idx=idx if idx.is_absolute()else a.Path(root)/idx
        check(root+'_existing_work_preserved',git('rev-parse','HEAD').decode().strip()==snap['HEAD']and a.hashlib.sha256(git('status','--porcelain=v1','-uall','-z')).hexdigest()==snap['status_sha256']and a.sha(idx)==snap['index_sha256']and all(a.sha(a.Path(root)/p)==h for p,h in snap['modified_sha256'].items()))
    check('all_twenty_core_images_present',len(images)==20)
    replay=a.load(R/'metrics/XYZ_ONLY_REPLAY.json');check('all_five_scenes_independently_replayed_with_source_images_blocked',replay['tested_scenes']==5 and len(replay['comparisons'])==10 and all(x['byte_identical']and x['complete_entry_SHA256']==x['XYZ_only_SHA256']==a.sha(R/'figures'/x['scene']/x['file'])for x in replay['comparisons']));a.verify()
    a.save('metrics/VALIDATION.json',dict(status='PASS',total_checks=len(checks),checks=checks,original_P0_points=76885,GT_used=False,accuracy_evaluated=False))
    a.save('provenance/FIGURE_MANIFEST.json',dict(images=images,diagnostic_figures=15,L5_only_figures=5))
    a.save('provenance/LOCAL_LAYER_ASSETS.json',dict(files=assets,full_XYZ_data_local_only=True))
    sources=[R/'code/audit.py',R/'code/replay_layers.py',R/'code/validate.py',a.REPO/'visualization/pointcloud_audit_renderer.py',R/'config.json',R/'PROTOCOL.md'];a.save('provenance/EXECUTION_SOURCES.json',dict(files=[dict(path=str(p),sha256=a.sha(p))for p in sources],research_camera_unchanged=True))
    print('VALIDATED',len(checks),'checks;',len(images),'core PNG; original data and prior L5 retained',flush=True)
if __name__=='__main__':main()
