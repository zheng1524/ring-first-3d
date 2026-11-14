"""Data-only, landmark-marginalized information. Diagnostics, never an optimizer."""
from joint_ba import *
from scipy.sparse import csr_matrix

def main(g):
 checkfreeze('provenance/'+g+'_MAIN_POSES_FROZEN.json');r=load(N/'results'/g/'B3/FINAL.json');o=Joint(g,'B3',initial=r);p=o.build();camids=[v['id']for v in o.fit if v['id']!=o.anchors[v['video']]and o.nobs[v['id']]>=6];params=[o.local[k]for k in camids];spans=[(p0,[0,1,2,3,4])for p0 in params];hd=[]
 if g=='G01':params.append(o.H['005']);spans.append((o.H['005'],list(range(6))));hd=['005']
 pointids=[k for k,x in o.X.items()if p.has_parameter_block(x)];params += [o.X[k]for k in pointids];spans += [(o.X[k],list(range(3)))for k in pointids];opts=ce.EvaluateOptions();opts.apply_loss_function=False;opts.set_parameter_blocks(params);J0=p.evaluate_jacobian(opts);JJ=csr_matrix((J0.values,J0.cols,J0.rows),shape=(J0.num_rows,J0.num_cols));nc=5*len(camids)+6*len(hd);npnt=3*len(pointids);expected=nc+npnt
 assert JJ.shape[1]==expected,(JJ.shape,expected)
 # first allRing blocks, then allRGB blocks, before priors
 nr=sum(c.num_residuals()for c in o.keep[:len(o.fit)+len(o.obs)]);A=JJ[:nr,:nc];B=JJ[:nr,nc:];schur=(A.T@A).toarray();Hbx=(B.T@A).toarray();Hbb=B.T@B
 for j,k in enumerate(pointids):
  h=Hbb[j*3:j*3+3,j*3:j*3+3].toarray();cross=Hbx[j*3:j*3+3];schur-=cross.T@np.linalg.pinv(h,rcond=1e-10)@cross
 schur=(schur+schur.T)/2;ev,U=np.linalg.eigh(schur);largest=max(float(ev[-1]),1e-30);rank=int((ev>largest*1e-12).sum());pos=ev[ev>largest*1e-12];cond=float(np.sqrt(largest/pos.min()))if len(pos)else None
 # Complete joint residual finite differences: one fixed random direction over
 # actual active tangent components. Same frozen correspondence and samepriors.
 rng=np.random.default_rng(20261115);d=rng.normal(size=expected);d/=np.linalg.norm(d);old=[a.copy()for a in params];fdrows=[];ad=JJ@d
 for h in [1e-4,1e-5,1e-6]:
  rr=[]
  for sign in [1,-1]:
   off=0
   for (a,idx),v in zip(spans,old):a[:]=v;a[idx]+=sign*h*d[off:off+len(idx)];off+=len(idx)
   rr.append(np.array(p.evaluate_residuals(opts)))
  for a,v in zip(params,old):a[:]=v
  fd=(rr[0]-rr[1])/(2*h);ab=float(np.max(abs(fd-ad)));rel=float(np.linalg.norm(fd-ad)/max(np.linalg.norm(fd),1e-15));fdrows.append(dict(step=h,absolute=ab,relative=rel,PASS=ab<1e-5 or rel<1e-4))
 graph={v['id']:set()for v in o.fit}
 for t in o.tracks:
  ids=[z['view']for z in t['observations']if z['view']in graph]
  for a in ids:graph[a].update(b for b in ids if b!=a)
 seen=set();components=[]
 for k in graph:
  if k in seen:continue
  queue=[k];comp=[]
  while queue:
   a=queue.pop()
   if a in seen:continue
   seen.add(a);comp.append(a);queue.extend(graph[a]-seen)
  components.append(comp)
 result=dict(group=g,joint_parameter_dimension=expected,active_camera_chart_dimension=nc,active_XYZ_dimension=npnt,actual_variable_camera_N=len(camids),fixed_anchors=o.anchors,shared_H_variables=hd,data_residual_dimension=nr,all_residual_dimension=JJ.shape[0],marginal_camera_information_rank=rank,marginal_camera_information_dimension=nc,condition_J_proxy=cond,eigenvalues=ev,weak_eigenvectors=U[:,:min(6,nc)].T,priors_excluded=True,landmarks_eliminated=True,method='explicit diagnostic 3x3pointblock elimination via SciPy pinv; not replacement for actualCeresSchur',Ceres_raw_jacobian_unrobust=True,complete_joint_FD=fdrows,graph_components=components,actual_graph_degrees={k:len(v)for k,v in graph.items()},physical=o.physical(),no_GT_HERO=True)
 save('metrics/'+g+'_JOINT_INFORMATION.json',result);print('JOINT_INFO',g,JJ.shape,'camrank',rank,'/',nc,'FD',fdrows,flush=True)
if __name__=='__main__':main(sys.argv[1])
