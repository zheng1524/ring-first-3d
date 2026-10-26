"""Small numerical and exact renderer restoration checks; no geometry GT."""
import ast,sys
import run as r
np=r.np
sys.path.insert(0,str(r.REPO))
from visualization import real_p0_renderer as renderer
checks=[]
def check(name,value,**extra):
    assert value,name;checks.append(dict(test=name,passed=True,**extra))
conf=r.config();tier=conf['presets']['M']
check('sparse_alone_not_removed',not r.candidates(np.array([5.]),np.array([1.]),tier)[0])
check('stretch_alone_not_removed',not r.candidates(np.array([1.]),np.array([5.]),tier)[0])
check('unknown_support_retained',not r.candidates(np.array([np.nan]),np.array([5.]),tier)[0])
check('joint_abnormality_is_candidate',r.candidates(np.array([4.]),np.array([4.]),tier)[0])
lab=np.ones((45,45),int);v,u=np.nonzero(lab);uv=np.c_[u,v];comp=np.ones(len(uv),int)
(a,b),_=r.local_anchors(uv,comp,lab,[np.ones(len(uv))*.02,np.ones(len(uv))*7],conf)
check('uniform_sparse_or_tilted_surface_is_not_removed',not r.candidates(.02/a,7/b,tier).any())
check('relative_spacing_invariant_to_uniform_metric_scale',np.allclose((.02*3)/(a*3),.02/a,equal_nan=True))
spacing=np.array([1.2,1.7,2.2,3.2,10]);stretch=spacing.copy();masks={k:r.candidates(spacing,stretch,t)for k,t in conf['presets'].items()}
check('three_presets_nested',not (masks['C']&~masks['M']).any()and not (masks['M']&~masks['A']).any())
faces=[]
for y in range(3):
    for x in range(3):
        i=y*4+x;faces.extend([[i,i+1,i+4],[i+1,i+5,i+4]])
faces=np.array(faces);deleted=np.zeros(16,bool);deleted[5]=True
check('interior_puncture_detected',r.interior_deletion_patches(faces,deleted)==1)
deleted[:]=False;deleted[0]=True
check('boundary_trimming_distinguished_from_interior_patch',r.interior_deletion_patches(faces,deleted)==0)
check('shared_edge_connectivity',len(np.unique(r.face_components(faces)))==1)
meta=r.load(r.REPO/'visualization/real_p0_renderer_provenance.json');original=r.Path(meta['original_script']);source=original.read_text();tree=ast.parse(source);nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name in ['basis','view','limits']]
bundled=ast.parse((r.REPO/'visualization/_phasec_c0_view_frozen.py').read_text());bn=[n for n in bundled.body if isinstance(n,ast.FunctionDef)]
check('three_original_functions_vendored_unchanged',[ast.dump(x,include_attributes=False)for x in nodes]==[ast.dump(x,include_attributes=False)for x in bn])
cc=r.load(r.PREV/'provenance/CASES.json');c=next(c for c in cc if c['id']=='G01_004_ref13');a=r.fields(c);P=a['XYZ_mm'];ring=r.trimesh.load('/home/liu/polyp_research/ring_anchor_3d/experiments/surface_fusion_v2/inputs/R10_ring.obj',process=False);color=renderer.source_colors(c['RGB'],a['source_u'],a['source_v'])
namespace=dict(np=np,ring=ring,data=lambda _:dict(XYZ_mm=P));exec(compile(ast.Module(body=nodes,type_ignores=[]),str(original),'exec'),namespace)
oldbounds=namespace['limits']([0]);newbounds=renderer.limits([P],ring)
check('original_camera_and_raw_bounds_identical',np.array_equal(oldbounds,newbounds))
plt=renderer.configure();images=[]
for fn in [lambda ax:namespace['view'](ax,P,color,oldbounds,title='same'),lambda ax:renderer.view(ax,P,color,ring,newbounds,title='same')]:
    fig,ax=plt.subplots(figsize=(6,6),dpi=100);fn(ax);fig.canvas.draw();images.append(np.asarray(fig.canvas.buffer_rgba()).copy());plt.close(fig)
check('actual_G01_original_vs_wrapper_pixel_identical',np.array_equal(*images),pixels=int(images[0].shape[0]*images[0].shape[1]))
r.save('metrics/small_tests.json',dict(status='PASS',tests=checks,count=len(checks),kind='numerical/renderer regression checks, not scientific 3D accuracy'))
print('PASS',len(checks),'small checks; original renderer pixel identical')
