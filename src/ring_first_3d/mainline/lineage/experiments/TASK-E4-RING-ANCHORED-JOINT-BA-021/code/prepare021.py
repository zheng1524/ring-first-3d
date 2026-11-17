"""Freeze inputs, common landmark identities and four-group quantitative protocol."""
from common import *
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
from scipy.sparse import lil_matrix
import collections
P20=REPO/'experiments/TASK-E4-RING-SIFT-SYMMETRIC-REGISTRATION-020'
P18=REPO/'experiments/TASK-E4-HERO-BODY-ADAPT-018'

def project(X,C,K):
 p=(X-C[:3,3])@C[:3,:3];z=p@K.T;return z[...,:2]/z[...,2:]

def initialize(scope,H):
 vv={v['id']:v for v in load(R/'config/VIEWS.json')};cross=scope=='CROSS';names=['CROSS_004','INDEPENDENT_005']if cross else['NEGATIVE_004','NEGATIVE_LATE_004'];AB=[load(R/'landmarks'/(n+'_OBSERVATIONS.json'))for n in names];lm=[np.load(R/'landmarks'/(n+'.npz'))['X']for n in names];pairs=load(R/'features'/(scope+'_NAMED_3D_TRACK_PAIRS.json'))['matches'];tracks=[];allobs=[];audit=[];features={};assets={}
 for k,pair in enumerate(pairs):
  obs=[];descriptors=[];material=[]
  for side,idx in [(0,pair['landmark004']),(1,pair['landmark005'])]:
   for o in AB[side][idx]['observations']:
    v=vv[o['view']];assert v['role']=='FIT';features.setdefault(o['view'],dict(np.load(R/'features'/(o['view']+'.npz'))));f=features[o['view']];i=o['feature_id'];assert np.allclose(f['xy'][i],o['uv'],atol=1e-6);C=np.asarray(v['T']);C=H@C if side else C;K=np.asarray(v['K']);block=v['direction_block019'];q=o|dict(side=side,track=k,K=K,C=C,native_C=v['T'],role=v['role'],RGB_source=v['RGB_source'],RGB_SHA=v['RGB_sha'],direction_block=block,region=int(f['region'][i]));obs.append(q);descriptors.append(f['des'][i]);material.append(int(f['region'][i]));assets[v['RGB_source']]=dict(path=v['RGB_source'],sha256=v['RGB_sha']);assets[str(R/'features'/(o['view']+'.npz'))]=asset(R/'features'/(o['view']+'.npz'))
  # Equal mass per video, then direction block, then observation within block.
  for side in [0,1]:
   sub=[o for o in obs if o['side']==side];counts=collections.Counter(o['direction_block']for o in sub)
   for o in sub:o['weight']=.5/len(counts)/counts[o['direction_block']]
  # Linear triangulation from every actual normalized pixel/camera. No frozen independent X.
  A=[]
  for o in obs:
   W=np.linalg.inv(o['C']);u=np.r_[o['uv'],1]@np.linalg.inv(o['K']).T;A.extend([u[0]*W[2]-W[0],u[1]*W[2]-W[1]])
  _,sv,Vh=np.linalg.svd(A);X=Vh[-1,:3]/Vh[-1,3]
  fun=lambda x:np.concatenate([(project(x,o['C'],o['K'])-o['uv'])*np.sqrt(o['weight']) for o in obs])
  fit=least_squares(fun,X,loss='huber',f_scale=3,max_nfev=100);X=fit.x
  J=fit.jac;G=J.T@J;e,Q=np.linalg.eigh(G);cov=Q@np.diag(1/np.maximum(e,1e-12))@Q.T;ce,CQ=np.linalg.eigh(cov);regcov=CQ@np.diag(np.clip(ce,.05**2,3**2))@CQ.T;W=CQ@np.diag(1/np.sqrt(np.clip(ce,.05**2,3**2)))@CQ.T
  dirs=np.array([(X-o['C'][:3,3])/np.linalg.norm(X-o['C'][:3,3])for o in obs]);angle=np.degrees(np.arccos(np.clip(dirs@dirs.T,-1,1))).max();pos=[float(((X-o['C'][:3,3])@o['C'][:3,:3])[2])for o in obs];err=[float(np.linalg.norm(project(X,o['C'],o['K'])-o['uv']))for o in obs];status='INITIALIZED'if np.isfinite(X).all()and min(pos)>0 else'INITIALIZATION_FAILURE_RETAINED';assert status=='INITIALIZED', (scope,k,status)
  for o in obs:allobs.append(o)
  cat='all_background'if all(x==0 for x in material)else'all_polyp'if all(x==1 for x in material)else'mixed'
  tracks.append(dict(track=k,source_landmark004=pair['landmark004'],source_landmark005=pair['landmark005'],X0=X,covariance_unit_pixel_proxy=cov,regularized_covariance_mm2=regcov,whitener=W,category=cat,observations=obs,cross_RGB_evidence=pair['evidence'],X004_independent=lm[0][pair['landmark004']],X005_independent=lm[1][pair['landmark005']],status=status))
  audit.append(dict(scope=scope,track=k,identity='MULTIVIEW_RGB_SIFT_RANSAC_SUPPORTED_NOT_PHYSICAL_GT',status=status,observations=len(obs),video004_N=sum(o['side']==0 for o in obs),video005_N=sum(o['side']==1 for o in obs),actual_cross_links=len(pair['evidence']),category=cat,source_parallax004_deg=AB[0][pair['landmark004']]['parallax_deg'],source_parallax005_deg=AB[1][pair['landmark005']]['parallax_deg'],joint_parallax_deg=float(angle),minimum_depth_mm=min(pos),joint_reprojection_px=stats(err),JtJ_eigenvalues=e,point_condition_number=float(e[-1]/max(e[0],1e-20)),std_principal_mm=np.sqrt(np.linalg.eigvalsh(cov)),independent_3D_difference_at_RoMa_mm=float(np.linalg.norm(lm[0][pair['landmark004']]-(H[:3,:3]@lm[1][pair['landmark005']]+H[:3,3]))),material_static='plausible static phantom texture; not independently proven',highlight_repetitive='020 intensity/descriptor mutual-ratio/RGB-RANSAC/multiframe filters retained; residual identity uncertainty'))
 np.savez_compressed(R/'observations'/(scope+'_DESCRIPTORS.npz'),descriptors=np.array(descriptors)if len(tracks)==1 else np.concatenate([np.array([features[o['view']]['des'][o['feature_id']]for o in t['observations']])for t in tracks]))
 save('observations/'+scope+'_COMMON_TRACKS.json',tracks);save('metrics/'+scope+'_TRACK_INITIALIZATION_AUDIT.json',audit);table('metrics/'+scope+'_TRACK_INITIALIZATION_AUDIT.csv',audit);save('provenance/'+scope+'_RGB_FEATURE_ASSETS.json',list(assets.values()));return tracks

def main():
 assert not(R/'provenance/BEFORE_OPTIMIZATION_FREEZE.json').exists(),'Do not reinitialize frozen experiment'
 hist=load(R/'config/HISTORICAL_CANDIDATES.json');H=np.asarray(next(x['T']for x in hist if x['tag']=='HISTORICAL_FULL_RoMa'))
 tr=initialize('CROSS',H);nt=initialize('NEGATIVE',np.eye(4));counts=collections.Counter(t['category']for t in tr)
 for scope,tracks in [('CROSS',tr),('NEGATIVE',nt)]:
  ct=collections.Counter(t['category']for t in tracks)
  for t in tracks:t['track_weight']=1/len(ct)/ct[t['category']]
  save('observations/'+scope+'_COMMON_TRACKS.json',tracks)
 # Tolerance from FIT segmentation/preprocessing uncertainty ONLY, not pose residual or HOLDOUT.
 dist={k:[]for k in ['inner','outer']}
 for v in load(R/'config/VIEWS.json'):
  if v['role']!='FIT':continue
  a=np.load(R/'ring_evidence_v2'/(v['id']+'.npz'))
  for k in dist:dist[k].extend(a[k+'_original_mask_nearest_distance_px'])
 eps={k:float(max(1.,np.quantile(dist[k],.95)+.5))for k in dist}
 save('config/RING_TOLERANCE_FIT_ONLY.json',dict(formula='max(1 px, FIT q95(original-DXY-point to original Mask boundary distance)+0.5 pixel quantization allowance)',epsilon_px=eps,observations={k:stats(x)for k,x in dist.items()},HOLDOUT=False,RoMa_residual_not_used=True))
 proto=dict(task='TASK-E4-RING-ANCHORED-JOINT-BA-021',seed=20261111,GT=False,pose_direction='X004=T004_from005 @ X005, OpenCV c2w, mm, left perturbation',pose_scale=[.6]*3+[np.deg2rad(5)]*3,lambda_reprojection=.2,lambda_Ring=1.,lambda_curve=.05,lambda_pose_prior=.01,lambda_point_prior=.001,pixel_sigma=3.,epsilon_px=eps,iterations=100,adam_pose_lr=.01,adam_point_lr_mm=.02,backtracks=8,acceptance_tolerance=1e-6,translation_bound_mm=1.2,rotation_bound_deg=10.,point_whitened_bound=6.,point_displacement_bound_mm=3.,observations='all18 named RGB tracks, no 3D consistency rejection; equal video/direction/track/category mass; no EPI loss',geometry_rule='fixed signed-CAD sample threshold -0.02mm, 11-ray parity; independent audit, not BA loss',hero_support_mm=.5,hero_ring_margin_mm=.05,coverage_proxy_voxel_mm=.25,physical_accuracy='NOT_EVALUABLE',main_routes=['B1','B2','B3'],sensitivity_routes=['SENS_B2_LightGlue','SENS_B2_020R2'],negative_routes=['NEG_B1','NEG_B2','NEG_B3'],no_body_no_HERO=True,independent_track_evaluation='020 source landmark IDs excluding all18 BA IDs, in each direction; actual endpoint IDs excluded when available; separate protected-view and unused-track rows',original_020=[asset(P20/'results'/(n+'.json'))for n in ['R0','R2','R3','R3_MASK_ONLY']])
 save('config/PROTOCOL.json',proto)
 plan=load(P18/'config/VIEW_PLAN.json');groups=[];inputs=[]
 for g in ['G01','G03','G05','G06']:
  src=[]
  for v in plan:
   if v['group']!=g:continue
   base=P18/('hero_fit'if v['role']=='FIT'else'holdout/hero')/v['view_id'];d=dict(id=v['view_id'],group=g,video=v['video'],role=v['role'],cache=v['cache'],meta=v['meta'],origin='018_CORE',mesh=asset(base/'TRUSTED_HERO.npz'),observation=asset(base/'OBS_TRUSTED.npz'),face_evidence=asset(base/'FACE_EVIDENCE.npz'),source=asset(base/'SOURCE.json'),original_native=asset(base/'HERO_native.npz'));src.append(d)
  if g=='G01':
   for v in load(R/'config/HERO_EVALUATION_SOURCES.json'):
    if v['video']=='005':src.append(v|dict(group=g,origin='020_NATIVE005_SUPPLEMENT'))
  bodies=dict(B0=asset(P18/'inputs'/g/'INITIAL.npz'),B2=asset(P18/'arms/B2_TRUSTED_COH16/local_results'/g/'FINAL.npz'))
  groups.append(dict(group=g,sources=src,bodies=bodies,ring=asset(P18/'inputs'/g/'RING.npz'),views=[v for v in plan if v['group']==g],only_G01_crossvideo=True))
  inputs.extend(list(bodies.values())+[asset(P18/'inputs'/g/'RING.npz')])
  for s in src:
   inputs.extend([s['mesh'],s['observation']]);inputs.append(asset(s['cache']))if'cache'in s else None
 save('config/FOUR_GROUP_INPUTS.json',groups)
 files=[p for p in(P20/'code').glob('*.py')]+[P20/n for n in ['TECHNICAL_REPORT_SUMMARY.md','METHOD_AND_INPUT_AUDIT.md','FAILURE_LEDGER.md']]+[P18/'config/VIEW_PLAN.json']
 for n in ['TASK-E4-RING-POLYP-REGISTRATION-019','TASK-E4-HERO-BODY-ADAPT-018','TASK-E4-HERO-GEOMETRY-CLEAN-017','TASK-E4-UPDATE-CAUSALITY-016']:
  files.extend(p for p in [REPO/'experiments'/n/x for x in ['TECHNICAL_REPORT_SUMMARY.md','METHOD_AND_INPUT_AUDIT.md']]if p.exists())
 files.extend(Path('/home/liu/new-polyp-dxy/src/dxy_mid/_engine')/n for n in ['ring_component.py','polypseg_ring_fitting.py','ring_holes.py'])
 save('provenance/UPSTREAM_READONLY.json',dict(files=[asset(p)for p in files]+inputs,source_commit_020='d225ca0e6eeacbe20bad3a4cdb2fa6cd6b41d8d8',no_upstream_writes=True))
 (R/'01_PROTOCOL.md').write_text('''# 021 预登记
G01 004/005；004 8 FIT+5 HOLDOUT、005 52 FIT+3 HOLDOUT完全继承020，不根据已知留出结果调参。全部18条真实同名轨迹进入BA，不以独立三维距离删点；非BA轨迹与保护视角用于冻结后评价。共同X由全部合法FIT二维观测线性三角化+固定鲁棒点优化初始化，非单侧X或ICP。
B1/B2/B3同RoMa种子、观测、100次候选和回溯；B1 X固定，B2开放共同X；B3仅增加I/O容差。L=.2 reproj+RingMask+.01 posePrior+.001 whitenedPointPrior；B3加.05*(Ieps+Oeps)。各轨迹两视频等权、视频内方向分区等权、类别与轨迹归一。重投影向量Huber sigma=3px；曲线epsilon由FIT源边界稳定性q95+.5px且至少1px，见配置；Mid只诊断。点先验为初值的单位像素协方差代理，不是GT；标准差裁剪.05..3mm。点移动上限3mm及白化6、共享SE3范围1.2mm/10°，均固定，不静默放宽。优化使用官方PyTorch3D Ring渲染与PyTorch Adam；投影Jacobian的点局部块稀疏，冻结后显式Schur消元审计；未声称使用专用Schur BA求解器。
主结果先冻结，再只增加两个固定历史种子敏感性实验；三条同视频负对照种子I。所有候选完成后才读取HOLDOUT/body/HERO作评价。无主体或HERO训练损失、无逐帧BA、无尺度/GT/融合。
四组全部018 43原生来源，G01另登记8个020原生005来源。四组同指标定义；实际Ring/同像素原生轴向深度、.5mm支持代理、.05mm CAD可见性容差；独立.25mm占据格仅为表面覆盖代理，累计面积不称解剖面积。B0/B2共同/新增/丢失射线全记录。全部原Face/坐标保留，底盖仅推断身份。无GT绝对精度NOT_EVALUABLE，可算的代理不得省略。
六视角、A/B/C图层、来源独立GLB、八张核心图和四份独立量化报告全部交付，不以BA是否变好为前提。完成后停止。
''',encoding='utf8')
 save('provenance/INPUTS_AND_PROTOCOL_FROZEN.json',dict(epoch=time.time(),protocol=asset(R/'config/PROTOCOL.json'),groups=asset(R/'config/FOUR_GROUP_INPUTS.json'),tracks=[asset(R/'observations'/(s+'_COMMON_TRACKS.json'))for s in ['CROSS','NEGATIVE']],no_GT=True,no_HOLDOUT=True))
 print('021_PREPARED',len(tr),len(nt),'Ring_eps',eps,'groups',[(g['group'],len(g['sources']))for g in groups],flush=True)
if __name__=='__main__':main()
