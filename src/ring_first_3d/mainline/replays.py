"""Fixed-input engineering replays. No optimization, training, or GT selection."""
import ast,json,sys,hashlib
from pathlib import Path
from types import SimpleNamespace
import numpy as np
from .paths import ROOT,LINEAGE,activate

def read(p):return json.loads(Path(p).read_text())
def save(p,x):
    from ring_first_3d.evaluation.validation import clean
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(clean(x),indent=2,allow_nan=False)+'\n')
def arrays(p):return dict(np.load(p))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def cfg():return read(ROOT/'mainline/configs/SITE.local.json')
def tol():return read(ROOT/'mainline/configs/REPLAY_TOLERANCES.json')
def definitions(path,names,ns):
    nodes=[n for n in ast.parse(Path(path).read_text()).body if isinstance(n,(ast.ClassDef,ast.FunctionDef))and n.name in names]
    assert {n.name for n in nodes}==set(names)
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),ns);return ns

def ring_first(out):
    from .native.cli import main
    main(['camera_demo','--data',cfg()['controlled_example'],'--out',str(out/'camera')])
    d=read(out/'camera/HISTORICAL_CAMERA_COMPARISON.json')
    return dict(status='PASS'if d['c2w_max_abs']<=tol()['camera_max_abs']and d['candidate_source_equal']else'MISMATCH',**d,algorithm='original RF5DoF + actual SIFT/PnP yaw, no Body or GT',camera=read(out/'camera/CAMERA_RESULT.json'))

def hero(out):
    from .native.cli import main
    main(['hero_demo','--data',cfg()['controlled_example'],'--out',str(out/'hero'),'--runtime-config',str(ROOT/'mainline/configs/SITE.local.json'),'--compare-history'])
    d=read(out/'hero/HISTORICAL_COMPARISON.json')
    good=d['depth_bitwise_equal']and d['raw_faces_equal']and d['raw_pixel_ids_equal']and d['raw_vertex_max_mm']==0
    return dict(status='PASS'if good else'MISMATCH',inference=read(out/'hero/INFERENCE.json'),comparison=d,model_receipt=read(out/'hero/MODEL_RECEIPT.json'))

def body_initialization(out):
    activate('TASK-E4-G01-G03-GROWTH-RECOVERY-001')
    from io_utils import load_inputs,source_folder
    from common import INITIALIZE
    rows=[]
    for case in ['G01','G03']:
        initial,views,ring,_,_,row=load_inputs(case,'FIT');canonical=ROOT/'mainline/configs/body_initialization/assets'/case/'EXACT013_INPUT.npz'
        assert sha(canonical)==row['resolved013_initial']['sha256'], 'CANONICAL_INITIAL_IDENTITY'
        a=INITIALIZE(canonical,ring,ring)
        equal={k:bool(np.array_equal(a[k],initial[k]))for k in a};np.savez_compressed(out/(case+'_INITIAL.npz'),**a)
        rows.append(dict(case=case,bitwise_equal=equal,input=row['resolved013_initial'],implementation='same exact013 initializer; no E1/E2 substitution'))
    return dict(status='PASS'if all(all(r['bitwise_equal'].values())for r in rows)else'MISMATCH',cases=rows)

def body_update(out):
    import torch
    activate('TASK-E4-G01-G03-GROWTH-RECOVERY-001')
    from io_utils import load_inputs,source_folder
    from deformation_graph import DeformationGraph
    from smooth_arap import SmoothARAP
    rows=[]
    for case in ['G01','G03']:
        initial,views,ring,_,_,_=load_inputs(case,'FIT');folder=source_folder(case);state=arrays(folder/'STEP_024/GRAPH.npz');expected=arrays(folder/'STEP_024/BODY.npz')
        graph=DeformationGraph(initial['V'],initial['F_solid']);w=torch.tensor(state['rotation'],dtype=torch.float64);t=torch.tensor(state['translation'],dtype=torch.float64)
        actual=graph.mesh(w,t).detach().numpy();error=float(np.linalg.norm(actual-expected['V'],axis=1).max())
        arap=SmoothARAP(initial['V'],initial['F_solid']);v=torch.tensor(actual,dtype=torch.float64);rot=arap.rotations(v);a,b,e=arap.energies(v,rot)
        np.savez_compressed(out/(case+'_STEP024_REPLAY.npz'),V=actual,F=initial['F'],F_solid=initial['F_solid'])
        rows.append(dict(case=case,max_vertex_error_mm=error,graph_nodes_equal=bool(np.array_equal(graph.g.numpy(),state['nodes'])),graph_edges_equal=bool(np.array_equal(graph.edges_np,state['edges'])),ARAP=float(a),Smooth=float(b),SARAP=float(e),lambda_smooth=.7,optimizer_steps=0,meaning='Replay the actual saved node rotations/translations through the original graph function'))
    return dict(status='PASS'if all(r['max_vertex_error_mm']<=tol()['mesh_vertices_max_mm']and r['graph_edges_equal']for r in rows)else'MISMATCH',cases=rows)

def growth(out,case):
    import torch
    activate('TASK-E4-G01-G03-GROWTH-RECOVERY-001')
    from io_utils import load_inputs,source_folder
    from embedded_sweep import EmbeddedSweep
    from bspline_sweep import basis
    from union_mesh import union
    from lengths import measure
    from projection import RecoveryProjection
    from geometry_gate import namespace,check
    from ring_gate import CurrentRingGate
    from common import legacy
    original=arrays(source_folder(case)/'STEP_024/BODY.npz');d=ROOT/'mainline/results'/case;sw=arrays(d/'FINAL_SWEEP_PARAMETERS.npz');local=read(d/'LOCAL_CONFIGURATION.json');conf=local['embedding'];sweep=EmbeddedSweep(conf)
    B,_=basis();radii=np.linalg.lstsq(B,np.log(np.expm1(sw['axes'])),rcond=None)[0]
    with torch.no_grad():sweep.control_tail.copy_(torch.tensor(sw['control'][1:]));sweep.radii.copy_(torch.tensor(radii))
    v,info=sweep.generate();tube=v.detach().numpy();actual=union(original,tube,sweep.F,out/'boolean');np.savez_compressed(out/'REPLAY_UNION.npz',**actual)
    reference=arrays(d/('FINAL.npz'if case=='G01'else'FAILED_ATTEMPT.npz'));sameVshape=actual['V'].shape==reference['V'].shape
    error=float(np.linalg.norm(actual['V']-reference['V'],axis=1).max())if sameVshape else None;face_equal=bool(np.array_equal(actual['F_solid'],reference['F_solid']));tube_error=float(np.linalg.norm(tube-sw['V'],axis=1).max())
    initial,views,ring,base,chart,_=load_inputs(case,'FIT');pg=RecoveryProjection(views,ring,legacy.balanced_weights(views),local['optimizer']['projection'])
    old=read(source_folder(case)/'UPDATES.json');support=next(g for g in old['growth']if g['iteration']==24)['candidates'][0]['support_views'];pg.setup(original,initial,conf,support)
    fresh=pg.rebuild(actual);why,projected=pg.assess(actual,fresh);record=read(d/'CHOSEN_GATES.json');expected={x['id']:x for x in record['projection']['views']}
    max_iou=max(abs(x['IoU_delta']-expected[x['id']]['IoU_delta'])for x in projected['views']);max_boundary=max(abs(x['Boundary_MAE_delta_px']-expected[x['id']]['Boundary_MAE_delta_px'])for x in projected['views'])
    geomwhy,geometry=check(actual,tube,sweep.F,original,initial,conf,base,chart,namespace());rg=CurrentRingGate(original,ring);ring_ok,ringmetrics,_=rg.check(actual);length=measure(sw['control'],original)
    save(out/'PROJECTION.json',projected);save(out/'GEOMETRY.json',geometry);save(out/'LENGTH.json',length)
    equivalent=error is not None and error<=tol()['mesh_vertices_max_mm']and face_equal and max_iou<=tol()['projection_IoU_abs']and max_boundary<=tol()['boundary_MAE_abs_px']
    expected_outcome=(not why and not geomwhy and ring_ok)if case=='G01'else'PER_VIEW_PROTECTION'in why
    return dict(status='PASS'if equivalent and expected_outcome else'MISMATCH',case=case,mesh_vertex_max_mm=error,faces_identical=face_equal,recovered_sweep_vertex_max_mm=tube_error,IoU_delta_max_error=max_iou,Boundary_delta_max_error_px=max_boundary,projection_reasons=why,geometry_reasons=geomwhy,geometry=geometry,Ring_ok=ring_ok,Ring_delta=ringmetrics['delta'],length=length,formal_stalk_length_mm=length['exposed_stalk_length_mm']if case=='G01'else None,scientific_state='ACTIVE_RESEARCH_MAINLINE; proximal-section exposure and fixed-frame GT worsening remain',optimizer_steps=0)

def a_to_b(out):
    import open3d as o3d,trimesh
    from PIL import Image
    from ring_first_3d.sim.geometry import camera_rays
    sample=read(ROOT/'mainline/configs/A_TO_B_SAMPLE.json');a=sample['source'];pair=sample['pair'];z=arrays(a['source_points']);pack=arrays(a['pack']);P=z.get('XYZ_mm',z.get('points_mm'));uv=z.get('pixel_uv',z.get('source_uv',z.get('uv')));rgb=np.asarray(Image.open(a['RGB']).convert('RGB'));colors=rgb[uv[:,1],uv[:,0]]/255.;m=trimesh.load(a['mesh'],process=False)
    assert len(P)==len(m.vertices)and np.allclose(P,m.vertices,atol=1e-5,rtol=0)
    ringpath='/home/liu/polyp_research/ring_anchor_3d/experiments/surface_fusion_v2/inputs/R10_ring.obj'if a['ring']=='R10'else'/home/liu/polyp_research/ring_anchor_3d/assets/ring_R5.obj'
    ring=trimesh.load(ringpath,process=False);rs=o3d.t.geometry.RaycastingScene(nthreads=2);rs.add_triangles(o3d.core.Tensor(np.asarray(ring.vertices,np.float32)),o3d.core.Tensor(np.asarray(ring.faces,np.uint32)))
    source=LINEAGE/'experiments/TASK-VIEW-OBSERVABILITY-GT-EVAL-001/code/reprojection.py';ns=dict(np=np,o3d=o3d,vis=SimpleNamespace(camera_rays=camera_rays),cad_scene=lambda kind:rs)
    definitions(source,['render','evaluate','neutral'],ns);target=pair['B_target'];pred=ns['render'](P,m.faces,colors,np.array(target['K']),np.array(target['c2w']),np.array(pair['H_A_to_B_world']),a['ring']);np.savez_compressed(out/'PREDICTION.npz',**pred)
    ref=arrays(sample['historical_output']);same={k:bool(np.array_equal(pred[k],ref[k],equal_nan=True))for k in pred}
    B=np.asarray(Image.open(target['RGB']).convert('RGB'));labels=np.asarray(Image.open(target['Mask']));metrics,mae,common=ns['evaluate'](pred,B,labels)
    import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,4,figsize=(15,4));axes[0].imshow(rgb);axes[0].set_title('A actual source RGB');axes[1].imshow(B);axes[1].set_title('B independent target RGB');axes[2].imshow(ns['neutral'](pred['RGBA']));axes[2].set_title('A triangles / A RGB projected to B');heat=np.where(common,mae,np.nan);axes[3].imshow(heat,cmap='magma',vmin=0,vmax=80);axes[3].set_title('RGB residual; unmatched retained')
    for ax in axes:ax.axis('off')
    fig.suptitle(pair['pair_id']+' | fixed historical conditional cameras | no target RGB/depth in prediction');fig.tight_layout();fig.savefig(out/'A_TO_B.png',dpi=120);plt.close(fig)
    return dict(status='PASS'if all(same.values())else'MISMATCH',pair_id=pair['pair_id'],bitwise_equal=same,valid_pixels=int(pred['valid'].sum()),metrics=metrics,pose_status=pair['pose_status'],independent_geometry_GT=False)

def depth_supervised(out):
    import torch,open3d as o3d
    from pytorch3d.ops import interpolate_face_attributes
    from pytorch3d.renderer import MeshRasterizer,RasterizationSettings
    from ring_first_3d.rendering.pytorch3d_renderer import MetricRenderer
    data=read(ROOT/'mainline/configs/DEPTH_SAMPLE.json');old=Path(data['history_arm_root']);(out/'inputs').mkdir();(out/'inputs/G01').symlink_to(old/'inputs/G01');(out/'config').mkdir();(out/'config/PROTOCOL.json').symlink_to(old/'config/PROTOCOL.json')
    renderer=MetricRenderer(out,'G01');c=renderer.case;ns=dict(renderer.namespace,R=out,save=lambda p,v:save(out/p,v),sha=sha,interpolate_face_attributes=interpolate_face_attributes,MeshRasterizer=MeshRasterizer,RasterizationSettings=RasterizationSettings)
    root=LINEAGE/'experiments/TASK-E4-HERO-BODY-ADAPT-018/code';definitions(root/'free_model.py',['FreeVertices'],ns);ch=ns['FreeVertices'](c)
    ns['ROOT']=Path(data['root_hero_fit']);definitions(root/'hero_objective018.py',['huber018','HeroDepth018'],ns);native=ns['HeroDepth018'](c,ch,'TRUSTED',data['HERO_views']);q=torch.zeros((ch.N,3),device=ns['device'],dtype=torch.float64,requires_grad=True);cid=data['view'];loss,info,_=native.term(ch.mesh(q),cid);weighted=.01*native.w[cid]*loss;grad=torch.autograd.grad(weighted,q)[0]
    history=arrays(data['history_gradients'])['hero_'+cid];actual=grad.detach().cpu().numpy();den=max(1e-30,np.linalg.norm(history));relative=float(np.linalg.norm(actual-history)/den);delta=abs(float(weighted.detach())-data['history_scalar']['weighted_loss'])
    np.savez_compressed(out/'NATIVE_DEPTH_GRADIENT.npz',gradient=actual,history_gradient=history)
    return dict(status='PASS'if delta<=tol()['loss_abs']and relative<=tol()['gradient_relative_norm']and bool(torch.isfinite(grad).all())else'MISMATCH',case='G01',view=cid,observation_model='T30 actual native HERO first-hit barycentric block; T28 separately retained',weighted_loss=float(weighted.detach()),historical_weighted_loss=data['history_scalar']['weighted_loss'],loss_abs_error=delta,gradient_norm=float(grad.norm()),historical_gradient_norm=float(np.linalg.norm(history)),gradient_relative_error=relative,finite_gradient=bool(torch.isfinite(grad).all()),details=info,optimizer_steps=0,GT_read=False)

FUNCTIONS={'ring-first':ring_first,'hero':hero,'body-initialization':body_initialization,'body-update':body_update,'stalk-growth-g01':lambda o:growth(o,'G01'),'stalk-growth-g03':lambda o:growth(o,'G03'),'a-to-b':a_to_b,'depth-supervised-pytorch':depth_supervised}
