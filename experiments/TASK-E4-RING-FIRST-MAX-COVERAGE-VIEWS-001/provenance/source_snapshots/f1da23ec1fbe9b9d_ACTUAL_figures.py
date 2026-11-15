"""Eight real-data scientific figures. Same per-group world/bounds, no geometry repair."""
from plot_common import *
from evaluate_geometry import new_sources
from coverage import direction_stats

def fig1():
 fig=plt.figure(figsize=(14,11))
 for k,g in enumerate(GROUPS):
  ax=fig.add_subplot(2,2,k+1,projection='3d');vv=load(camera_file(g));u=np.linspace(0,2*np.pi,32);v=np.linspace(0,np.pi,16);ax.plot_wireframe(np.outer(np.cos(u),np.sin(v)),np.outer(np.sin(u),np.sin(v)),np.outer(np.ones(len(u)),np.cos(v)),color='lightgray',alpha=.15,lw=.3)
  for s,col in COLS.items():
   for kind,mark in [('formal','o'),('weak','^'),('hold','x')]:
    rr=[q for q in vv if q['video']==s and q.get('C')is not None and(q['formal']if kind=='formal'else q['role']=='HOLDOUT'if kind=='hold'else not q['formal']and q['role']!='HOLDOUT'and q.get('RGB_inliers_N',0)>=6)]
    if rr:d=np.array([unit(np.array(x['C'])[:3,3])for x in rr]);ax.scatter(*d.T,c=col,s=18 if kind=='formal'else 35,marker=mark,alpha=.65,label=s+' '+kind+' N='+str(len(rr)))
  unresolved=sum(q.get('RGB_inliers_N',0)<6 and q['role']!='HOLDOUT'for q in vv);ax.set_title(g+' | yaw-unresolved not located: '+str(unresolved));ax.set_xlabel('Ring-world X direction');ax.set_ylabel('Y direction');ax.set_zlabel('Z direction');ax.set_box_aspect((1,1,1));ax.legend(fontsize=6,loc='upper left')
 fig.suptitle('Fig1 | All recovered candidate directions, not area coverage\nCircle: conditional validation; triangle: RGB numeric weak; cross: protected HOLDOUT; Ring-only yaw is NOT placed in common world');fig.tight_layout(rect=[0,0,1,.94]);finish(fig,'Fig1_All_Candidate_Directions.png')

def fig2():
 vv=load(camera_file('G03'));canon=[v for v in vv if v.get('initial_canonical_id')];chosen=list(canon);base=unit(np.array(next(v['C']for v in canon if v['role']=='FIT'))[:3,3]);new=[v for v in vv if not v.get('initial_canonical_id')and v['video']=='005'and v['formal']];new=sorted(new,key=lambda v:angle(np.array(v['C'])[:3,3],base),reverse=True)
 for v in new:
  if all(q['video']!='005'or angle(np.array(v['C'])[:3,3],np.array(q['C'])[:3,3])>4 for q in chosen):chosen.append(v)
  if len(chosen)>=16:break
 chosen +=[v for v in vv if v['video']=='PHOTO'];chosen=sorted(chosen,key=lambda v:angle(np.array(v['C'])[:3,3],base)if v.get('C')is not None and (v.get('RGB_inliers_N',0)>=6 or v['role']=='HOLDOUT') else 999);fig,axs=plt.subplots(int(np.ceil(len(chosen)/4)),4,figsize=(16,3.1*np.ceil(len(chosen)/4)));axs=np.ravel(axs)
 for ax,v in zip(axs,chosen):
  d=np.load(v['cache']);ax.imshow(d['RGB']);edges(ax,d['labels']==1,'lime');edges(ax,d['labels']==2,'cyan');a=angle(np.array(v['C'])[:3,3],base)if v.get('C')is not None and (v.get('RGB_inliers_N',0)>=6 or v['role']=='HOLDOUT') else None;ax.set_title(v['id']+'\n'+(f'{a:.1f} deg'if a is not None else'UNLOCATED / yaw not resolved')+' | '+('HOLDOUT'if v['role']=='HOLDOUT'else'conditional'if v['formal']else'weak')+'\nRing IoU '+(str(round(v['Ring']['Ring_IoU'],3))if v.get('Ring',{}).get('Ring_IoU')is not None else 'NOT_FIT_SCORED'),fontsize=8);ax.axis('off')
 for ax in axs[len(chosen):]:ax.axis('off')
 fig.suptitle('Fig2 | G03 actual RGB ordered by recovered direction; includes all6 original FIT+3 HOLDOUT and3 photos\nDifferent frame count is not independent directional support. Photo003 cannot be located.');fig.tight_layout(rect=[0,0,1,.95]);finish(fig,'Fig2_G03_Real_RGB_Directions.png')

def fig3():
 actual=load(N/'metrics/HERO_COUNT_ACTUAL_COVERAGE.json');fig,axs=plt.subplots(2,4,figsize=(17,8))
 for k,g in enumerate(GROUPS):
  a=load(selpath(g,'_COUNT_ABLATION.json'));base=a[0];rr=[r for r in a if r['requested'].isdigit()];by={r['actual_N']:r for r in rr};xx=sorted(by);axs[0,k].plot(xx,[by[n]['HERO_proxy_visible_mm2']for n in xx],'o-',label='Frozen FIT HERO visible proxy');axs[0,k].scatter([base['actual_N']],[base['HERO_proxy_visible_mm2']],marker='*',s=100,label='unchanged historical baseline');axs[0,k].plot(xx,[by[n]['direction2_mm2']for n in xx],'s--',label='>=2 independent directions');axs[0,k].set_title(g);axs[0,k].set_xlabel('actual nonredundant targets');axs[0,k].set_ylabel('area proxy mm²');axs[0,k].set_xlim(0,38);axs[0,k].grid(alpha=.2);axs[0,k].legend(fontsize=6)
  rows=[r for r in actual if r['group']==g];by={r['actual_target_N']:r for r in rows};xx=sorted(by);ax=axs[1,k];ax.plot(xx,[by[n]['dedup_new_bin_area_proxy_mm2']for n in xx],'o-',c='darkorange',label='new bins (unverified)');ax.set_xlabel('actual new HERO targets');ax.set_ylabel('new area-bin proxy mm²');ax.set_xlim(0,38);ax.grid(alpha=.2);ax2=ax.twinx();ax2.plot(xx,[by[n]['HERO_unique_support_N']/max(1,by[n]['HERO_unique_source_fixed_N'])for n in xx],'s-',c='green');ax2.set_ylim(0,1);ax2.set_ylabel('old-FIT same-layer union / fixed pixels');ax.legend(fontsize=6)
 fig.suptitle('Fig3 | Target-count saturation vs actual new HERO evidence\nBudgets12/20/28/36 not filled by duplicates. New area bins are NOT proved new anatomical surface.');fig.tight_layout(rect=[0,0,1,.93]);finish(fig,'Fig3_Counts_Coverage_And_Actual_HERO.png')

def fig4():
 fig,axs=plt.subplots(4,6,figsize=(20,13));labels=['old6–8','new8','new12','new20','new28','new36']
 for i,g in enumerate(GROUPS):
  conf,old=frozen_sources(g);new=[s for s in new_sources(g)if s['variant']=='GEOMETRIC3'];ring=np.load(conf['ring']['path']);bounds=bound_parts(old+new,ring)
  for j,n in enumerate([0,8,12,20,28,36]):
   use=old if n==0 else[s for s in new if s['rank']<=n];maxn=len(new)
   if n>maxn and j>0 and [0,8,12,20,28,36][j-1]>=maxn:axs[i,j].text(.5,.5,g+'\nS'+str(n)+' unavailable\nactual max '+str(maxn),ha='center',va='center');axs[i,j].axis('off');continue
   title=g+' | '+labels[j]+' | actual '+str(len(use))
   if n>maxn:title+=' (budget not filled)'
   panel(axs[i,j],parts(use),ring,bounds,title)
 fig.suptitle('Fig4 | Actual native TRUSTED subsets, source colors, fixed per-group world/bounds\nBlack CAD Ring; unchanged triangles; internal017 labels do not certify cross-source consistency; no fusion / ICP / hole filling.');fig.tight_layout(rect=[0,0,1,.94]);finish(fig,'Fig4_Actual_HERO_Surface_Sets.png')

def fig5():
 fig,axs=plt.subplots(4,2,figsize=(11,17));palette=np.array([[.6,.6,.6],[.9,.7,.18],[.2,.65,.8],[.15,.65,.3]])
 for i,g in enumerate(GROUPS):
  conf,ss=frozen_sources(g);ring=np.load(conf['ring']['path']);bounds=bound_parts(ss,ring);pr=np.load(selpath(g,'_PROXY.npz'));vv=np.load(selpath(g,'_VISIBILITY.npz'));sel=load(selpath(g,'_SELECTION.json'));ids=vv['candidate_ids'].tolist();ii=[ids.index(c)for c in sel['independent_direction_ids']];cnt=vv['visible'][ii].sum(0)if ii else np.zeros(len(pr['X']),int);lookup={tuple(k):min(int(v),3)for k,v in zip(pr['key'],cnt)};pp=[]
  for s in ss:
   tr=s['V'][s['F']];nn=np.cross(tr[:,1]-tr[:,0],tr[:,2]-tr[:,0]);nn/=np.maximum(np.linalg.norm(nn,axis=1)[:,None],1e-15);nn*=np.sign(nn[np.arange(len(nn)),np.argmax(abs(nn),axis=1)])[:,None];key=np.c_[np.floor(tr.mean(1)/.2).astype(int),np.rint(nn/.5).astype(int)];c=np.array([lookup.get(tuple(k),0)for k in key]);pp.append((s['V'],s['F'],palette[c]))
  panel(axs[i,0],pp,ring,bounds,g+' | frozen FIT HERO evidence surface');bm=np.load(conf['bodies']['B0']['path']);bc=vv['body_visible'][ii].sum(0)if ii else np.zeros(len(bm['F']),int);panel(axs[i,1],[(bm['V'],bm['F'],palette[np.minimum(bc,3)])],ring,bounds,g+' | coarse Body INFERRED proxy')
 fig.suptitle('Fig5 | Selected independent directions >=5°: gray0 / yellow1 / cyan2 / green3+\nGray Body is unobserved inference, not absence of anatomy. Proxy areas are kept separate.');fig.tight_layout(rect=[0,0,1,.95]);finish(fig,'Fig5_Independent_Direction_Surface_Heatmaps.png')

def evidence_parts(s,g):
 path=N/'evaluation'/g/(s['id']+'_EVIDENCE.npz');e=np.load(path);state=np.full(len(s['F']),4,int);mapping={int(f):i for i,f in enumerate(s['mesh']['original_face_id'])}
 for f,c in zip(e['original_face_id'],e['class_id']):
  if int(f)in mapping:state[mapping[int(f)]]=int(c)
 cols=np.array([[.18,.7,.3],[.9,.2,.15],[.95,.65,.15],[.2,.4,.9],[.6,.6,.6],[.65,.2,.8]]);return(s['V'],s['F'],cols[state])

def fig6():
 g='G03';conf,old=frozen_sources(g);new=[s for s in new_sources(g)if s['variant']=='GEOMETRIC3'];ring=np.load(conf['ring']['path']);bounds=bound_parts(old+new,ring);fig,axs=plt.subplots(2,3,figsize=(15,10))
 for j,ang in enumerate([(25,-65),(5,20),(0,110)]):
  panel(axs[0,j],parts(old),ring,bounds,'G03 original native FIT HERO | '+str(ang),ang);panel(axs[1,j],[evidence_parts(s,g)for s in new],ring,bounds,'new12 | actual evidence vs frozen old',ang)
 fig.suptitle('Fig6 | G03 real surfaces: long-stalk/head/base anatomy remains UNANNOTATED / UNKNOWN\nGreen same-layer; red front-disagreement proxy; orange deeper/possible occlusion; blue CAD hidden; gray unknown; purple mixed. No anatomy guessed from Body.');fig.tight_layout(rect=[0,0,1,.92]);finish(fig,'Fig6_G03_Actual_Added_Surface_And_Conflicts.png')
 # Dedicated close views preserve original triangles and fixed global millimeters.
 fig,axs=plt.subplots(1,3,figsize=(15,5));near=bounds[np.linalg.norm(bounds,axis=1)<16];bnear=near if len(near)else bounds
 for j,(title,ss)in enumerate([('old raw native TRUSTED',old),('new raw native TRUSTED',new),('old + new (not fused)',old+new)]):panel(axs[j],parts(ss),ring,bnear,title,angle=(0,20))
 fig.suptitle('G03 Ring-near detail | zoom only, full scene retained in Fig6 and GLB; same camera and mm scale');fig.tight_layout(rect=[0,0,1,.9]);finish(fig,'G03_Ring_Near_Local_Detail.png')

def fig7():
 fig=plt.figure(figsize=(15,17))
 for i,g in enumerate(GROUPS):
  conf,old=frozen_sources(g);new=[s for s in new_sources(g)if s['variant']=='GEOMETRIC3'];ring=np.load(conf['ring']['path']);bounds=bound_parts(old+new,ring);ax=fig.add_subplot(4,2,2*i+1);panel(ax,parts(old+new),ring,bounds,g+' | unchanged old + actually inferred new HERO')
  ax=fig.add_subplot(4,2,2*i+2,projection='3d');vs=load(camera_file(g));countunknown=0
  for s,col in COLS.items():
   vv=[v for v in vs if v['video']==s and v.get('C')is not None and v.get('RGB_inliers_N',0)>=6];Pp=np.array([np.array(v['C'])[:3,3]for v in vv]);
   if len(Pp):ax.scatter(*Pp.T,c=col,s=[22 if v['formal']else 8 for v in vv],marker='^'if s=='PHOTO'else'o',label=s+' cameras')
   if s!='PHOTO'and len(Pp):ax.plot(*Pp.T,c=col,lw=.35,alpha=.5)
   countunknown+=sum(v['video']==s and v.get('RGB_inliers_N',0)<6 for v in vs)
  reg=load(N/'registration'/g/('JOINT_FULL6_NATIVE005_FINAL.json'if g=='G01'else'JOINT_FULL6_FINAL.json'));X=np.array(list(reg['X'].values()));
  if len(X):ax.scatter(*X.T,s=4,c='gray',alpha=.4,label='real RGB XYZ')
  ax.scatter(*ring['V'][::80].T,s=2,c='black',label='CAD reference');ax.set_xlabel('X mm');ax.set_ylabel('Y mm');ax.set_zlabel('Z mm');ax.set_title(g+' | actual world cameras / RGB landmarks\nyaw-unlocated '+str(countunknown)+' NOT merged');ax.legend(fontsize=6)
 fig.suptitle('Fig7 | Multi-source common metric world; conditional registration, no similarity scale / ICP\nIndependent source Meshes remain separate. G03/G05/G06 005 initialized by004RGB PnP, not independent005SLAM.');fig.tight_layout(rect=[0,0,1,.95]);finish(fig,'Fig7_Cross_Source_Metric_Worlds.png')

def fig8():
 fig,axs=plt.subplots(2,4,figsize=(17,8));actual=load(N/'metrics/HERO_SOURCE_ACTUAL_CONTRIBUTIONS.json')
 for i,g in enumerate(GROUPS):
  a=load(selpath(g,'_SOURCE_CONTRIBUTIONS.json'));x=np.arange(3);base=a[0]['coverage_mm2'];gain=[r['coverage_mm2']-base for r in a];axs[0,i].bar(x,gain,color=['#3978b8','#e59c30','#ab42a2']);axs[0,i].set_xticks(x,['004','+005','+photos']);axs[0,i].set_ylabel('additional existing-FIT visible proxy mm²');axs[0,i].set_title(g+' | conditional camera-pool E5');
  for j,r in enumerate(a):axs[0,i].text(j,gain[j],str(r['actual_N'])+' targets',ha='center',fontsize=7)
  b=[r for r in actual if r['group']==g];axs[1,i].bar(x,[r['new_area_bins_proxy_mm2']for r in b],color=['#3978b8','#e59c30','#ab42a2']);axs[1,i].set_xticks(x,['004','+005','+photos']);axs[1,i].set_ylabel('actual new HERO bins mm² (UNVERIFIED)');axs[1,i].set_title('same frozen selected pool, source-filtered')
 fig.suptitle('Fig8 | Source marginal contributions: new direction / new bins do NOT imply accurate geometry\nPhoto candidates are excluded from formal inference unless independently supported. No pose tuning on these scores.');fig.tight_layout(rect=[0,0,1,.93]);finish(fig,'Fig8_Source_Marginal_Contributions.png')

def sixview():
 for g in GROUPS:
  conf,old=frozen_sources(g);new=[s for s in new_sources(g)if s['variant']=='GEOMETRIC3'];ring=np.load(conf['ring']['path']);bounds=bound_parts(old+new,ring);fig,axs=plt.subplots(2,3,figsize=(14,9));angles=[(25,-65),(25,20),(85,-65),(0,20),(0,200),(-65,20)]
  for ax,ang in zip(axs.ravel(),angles):panel(ax,parts(old+new),ring,bounds,g+' | elevation/azimuth '+str(ang),ang)
  fig.suptitle(g+' full six-view raw native surface atlas | fixed mm bounds | no fusion / no smoothing');fig.tight_layout(rect=[0,0,1,.95]);finish(fig,g+'_Six_View_Atlas.png')

def main():
 for f in [fig1,fig2,fig3,fig4,fig5,fig6,fig7,fig8,sixview]:f();print('FIGURE_DONE',f.__name__,flush=True)
if __name__=='__main__':main()
