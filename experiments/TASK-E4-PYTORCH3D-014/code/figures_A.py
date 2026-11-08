from visual_base import *
def main():
 vv=load(R/'config/ALL_VIEWS.json');cases=load(R/'config/CASE_LOCK.json');fig=plt.figure(figsize=(20,17));fig2=plt.figure(figsize=(20,17));colors=['#2879a6','#e87a34']
 for j,c in enumerate(cases):
  n=c['name'];vs=[v for v in vv if v['case']==n];ax=fig.add_subplot(3,4,j+1,projection='3d');bx=fig2.add_subplot(3,4,j+1,projection='3d')
  r=np.load(R/'inputs'/n/'RING.npz');ax.add_collection3d(Poly3DCollection(r['V'][r['F']],facecolor='black',edgecolor='none'))
  for k,sid in enumerate(sorted({v['sid']for v in vs})):
   data=[v for v in vs if v['sid']==sid];P=np.array([np.asarray(v['T'])[:3,3]for v in data]);D=np.array([v['direction']for v in data]);ax.scatter(*P.T,s=8,c=colors[k%2],label=sid);bx.scatter(*D.T,s=10,c=colors[k%2],label=sid);H=[v for v in data if v['HERO_sources']]
   if H:pp=np.array([np.asarray(v['T'])[:3,3]for v in H]);dd=np.array([v['direction']for v in H]);ax.scatter(*pp.T,s=45,c=colors[k%2],marker='*',edgecolors='black',linewidths=.3);bx.scatter(*dd.T,s=45,c=colors[k%2],marker='*',edgecolors='black',linewidths=.3)
  ax.set_title(n+f' | {len(vs)} posed candidates',fontsize=9);ax.set_xlabel('world X (mm)',fontsize=6);ax.set_ylabel('Y (mm)',fontsize=6);ax.set_zlabel('Z (mm)',fontsize=6);ax.tick_params(labelsize=6);ax.legend(fontsize=5);bx.set_title(n+' direction coverage',fontsize=9);bx.set(xlim=(-1,1),ylim=(-1,1),zlim=(-1,1));bx.tick_params(labelsize=6);bx.set_xlabel('unit X',fontsize=6);bx.set_ylabel('unit Y',fontsize=6);bx.set_zlabel('unit Z',fontsize=6)
 fig.suptitle('014 | Actual candidate camera centers, separate metric world per specimen\nBlue/orange videos; stars original HERO; black fixed CAD. Conditional poses, not pose GT.');fig2.suptitle('Actual unit observation directions | no common world across physical specimens\nMore frames need not provide new angles; unposed photos/frames remain in inventory.');finish(fig,'Fig1_All_Groups_Camera_Partitions.png');finish(fig2,'details/Unit_Direction_Coverage.png')
 fig,axs=plt.subplots(11,4,figsize=(16,27))
 for i,c in enumerate(cases):
  vs=[v for v in vv if v['case']==c['name']];ids=np.linspace(0,len(vs)-1,4).astype(int)
  for ax,k in zip(axs[i],ids):
   v=vs[k];a=np.load(R/'inputs'/c['name']/(v['id']+'.npz'));ax.imshow(a['RGB']);edge(ax,a['labels']==1,'lime');edge(ax,a['labels']==2,'cyan');ax.set_title(v['id']+' '+v['role'],fontsize=6);ax.axis('off')
 fig.suptitle('Fixed order representative real RGB / native Mask atlas | no result-based view choice');finish(fig,'details/Candidate_RGB_Mask_Atlas.png')
if __name__=='__main__':main()
