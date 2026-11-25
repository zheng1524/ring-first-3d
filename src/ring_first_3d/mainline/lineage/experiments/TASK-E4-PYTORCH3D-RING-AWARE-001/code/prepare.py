from common import *
import shutil, subprocess, ast

def main():
    manifest=[]
    def copy(src,dst):
        dst=R/dst;dst.parent.mkdir(parents=True,exist_ok=True)
        assert not dst.exists(),dst
        shutil.copyfile(src,dst);manifest.append(dict(source=asset(src),copy=asset(dst)));return dst
    protect=[]
    for base in [OLD,REPO/'experiments/TASK-E4-PROGRESSIVE-DOF-001']:
        for p in sorted(base.rglob('*')):
            if p.is_file() and not any(k in p.parts for k in ['runtime','.git','__pycache__']):protect.append(asset(p))
    save('assets_index/HISTORY_PROTECTION.json',protect)
    up=R/'runtime/pytorch3d'
    for name in ['docs/tutorials/fit_textured_mesh.ipynb','pytorch3d/utils/camera_conversions.py','pytorch3d/renderer/mesh/shader.py','LICENSE']:
        copy(up/name,'upstream/'+Path(name).name)
    dxy=Path('/home/liu/new-polyp-dxy')
    paths=[dxy/'src/dxy_mid/_engine'/s for s in ['v83_boundary_slice.py','raw_g3_helpers.py','v83_boundary.py','cross_ring_boundary.py']]
    save('assets_index/DXY_READONLY_REFERENCE.json',dict(commit=subprocess.check_output(['git','-C',str(dxy),'rev-parse','HEAD'],text=True).strip(),files=[asset(p)for p in paths],used='AST-extracted smooth_normal/beyond only; no imports, P/Q classification or body algorithm'))
    # Copy exactly the small pure helpers, not the DXY execution closure.
    ns=[]
    for p,names in [(paths[0],['smooth_normal']),(paths[1],['beyond'])]:
        src=p.read_text();tree=ast.parse(src)
        ns.extend(ast.get_source_segment(src,n)for n in tree.body if isinstance(n,ast.FunctionDef)and n.name in names)
    (R/'code/dxy_cross_section_helpers.py').write_text('# Read-only AST extraction; provenance in DXY_READONLY_REFERENCE.json\nimport numpy as np\nRULE83={"normal_offsets":[3,5,9],"normal_cos_min":.8}\n\n'+'\n\n'.join(ns)+'\n')
    copy(OLD/'inputs/BASE_SOURCE_MESH.npz','inputs/virtual/INITIAL.npz')
    copy(OLD/'inputs/RING_CAD.npz','inputs/virtual/RING.npz')
    views=load(OLD/'inputs/CAMERAS.json');vcase=[]
    for c in views:
        p=copy(OLD/'inputs'/('TARGET__'+c['id']+'.png'),'inputs/virtual/'+c['id']+'_LABEL_RGB.png')
        rgb=np.asarray(Image.open(p).convert('RGB'));label=np.zeros(rgb.shape[:2],np.uint8);label[(rgb[:,:,0]>128)&(rgb[:,:,0]>rgb[:,:,1])]=1;label[rgb[:,:,1]>128]=2
        np.savez_compressed(R/'inputs/virtual'/(c['id']+'.npz'),labels=label,RGB=rgb,K=np.array(c['K_pixel_center']),T=np.array(c['c2w_mm']))
        vcase.append(dict(id=c['id'],role=c['role'],qualification='KNOWN_BLENDER_CAMERA',width=640,height=360))
    save('inputs/virtual/CASE.json',dict(name='virtual',identity='IIa6.5_R10 native static Blender',views=vcase,initialization='Gate A independent Ring-only P0; exact source mesh',GT='posterior only',unit='mm'))
    copy(R1/'local_results/G01_004/P0.npz','inputs/real/INITIAL.npz')
    copy(R1/'inputs/G01_004_CAD.npz','inputs/real/RING.npz')
    sources=load(Path('/home/liu/ring_first_3d_neural_e1/experiments/TASK-NEURAL-E1-PIPELINE-RECOVERY-001/provenance/INPUT_ELIGIBILITY.json'))['references']
    core=['G01_004_ref08','G01_004_ref13','G01_004_ref03'];hold=['G01_004_growth_r04','G01_004_growth_r06','G01_004_growth_r10']
    gate=load(Path('/home/liu/ring_first_3d_e3n0_eight/experiments/TASK-E3-N0-NEURALFUSION-EIGHT-VIEW-001/config/CAMERA_GATE_RESULTS.json'))
    real=[]
    for cid in core+hold:
        c=next(c for c in sources if c['id']==cid)
        rgb=np.asarray(Image.open(c['RGB']).convert('RGB'));lab=np.asarray(Image.open(c['Mask']));p=np.load(c['pack'])
        assert np.array_equal(lab,p['labels']) and np.allclose(p['pose'],c['c2w_mm'],atol=1e-10)
        assert np.allclose(np.load(c['camera_file'])['c2w'][c['reference_index']],p['pose'],atol=1e-10)
        np.savez_compressed(R/'inputs/real'/(cid+'.npz'),labels=lab,RGB=rgb,K=p['K'],T=p['pose'])
        for k in ['RGB','Mask','pack','camera_file']:manifest.append(dict(source=asset(c[k]),role=k,view=cid))
        g=next(g for g in gate['sources']if g['source']==cid)
        real.append(dict(id=cid,role='FIT'if cid in core else'UPDATE_HOLDOUT',qualification=g['qualification'],width=640,height=360,source_RGB=c['RGB'],source_Mask=c['Mask']))
    save('inputs/real/CASE.json',dict(name='real',identity='GP_Ip_12.0mm_closed_R10_single_refY/video004',views=real,unit='mm',initialization='R1 conservative P0; used all seven views, HOLDOUT is update-stage only',GT='NOT_EVALUABLE'))
    save('assets_index/INPUT_MANIFEST.json',manifest)
    cfg=dict(task=R.name,seed=20261106,official_commit=subprocess.check_output(['git','-C',str(up),'rev-parse','HEAD'],text=True).strip(),official_steps=2000,project_steps=300,project_image_size=[180,320],sigma=1e-4,faces_per_pixel=50,optimizer=dict(name='SGD',lr=1.,momentum=.9),weights=dict(silhouette=1.,edge=1.,normal=.01,laplacian=1.),tau_depth_mm=.05,project_checkpoints=[0,100,200,300],cases=['virtual','real'],GT_access='postfreeze except independent projection gate',hyperparameter_search=False)
    save('config/FROZEN.json',cfg)
    save('assets_index/UPSTREAM.json',dict(official_commit=cfg['official_commit'],tutorial=asset(up/'docs/tutorials/fit_textured_mesh.ipynb'),cow=asset(R/'runtime/cow.obj'),dxy='sampling mechanism only'))
    print('Prepared exact source inputs; no target regeneration',flush=True)

if __name__=='__main__':main()
