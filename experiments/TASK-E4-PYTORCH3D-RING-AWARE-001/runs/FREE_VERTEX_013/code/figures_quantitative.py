from visual013 import *

def main():
 rows=load(R/'metrics/BLENDER_GEOMETRIC_METRICS.json');cases=[c['name']for c in load(R/'config/CASE_LOCK.json')];fig,axs=plt.subplots(2,3,figsize=(19,11));tags=['FINAL011','FINAL012','FINAL013'];colors=['#c39742','#5086bc','#a652af'];x=np.arange(len(cases));keys=['Chamfer_MAE_mm','Dxy_AE_mm','surface_Fscore_0.5mm'];titles=['Full bidirectional Chamfer MAE (mm)','Dxy absolute error (mm)','Two-direction surface F-score at 0.5mm']
 for ax,key,title in zip(axs[0],keys,titles):
  for j,(tag,col)in enumerate(zip(tags,colors)):
   y=[next((r.get(key)for r in rows if r['case']==c and r['label']==tag),None)for c in cases];y=[np.nan if v is None else v for v in y];ax.bar(x+(j-1)*.25,y,width=.24,label=tag,color=col)
  ax.set_xticks(x,cases,rotation=45);ax.set_title(title);ax.legend(fontsize=7);ax.grid(alpha=.2,axis='y')
 for ax,n in zip(axs[1,:2],['G03','G09']):
  zz=[r for r in rows if r['case']==n];gt=next((r for r in zz if r.get('height_max_GT_mm')is not None),None)
  if gt is None:ax.text(.5,.5,n+' author-base NOT_EVALUABLE',transform=ax.transAxes);continue
  vals=[]
  for j,(tag,col)in enumerate(zip(tags,colors)):
   z=next(r for r in zz if r['label']==tag);lo=z.get('lowest_point_vs_author_base_mm');hi=z.get('height_max_pred_mm')
   if lo is not None and hi is not None:ax.plot([j,j],[lo,hi],lw=10,c=col);ax.scatter([j],[z['H95_pred_mm']],c='black',s=20,zorder=5);ax.text(j,hi+.02*max(1,hi),'span %.2f'%z['prediction_top_to_bottom_span_mm'],ha='center',fontsize=7)
  gmax=gt['height_max_GT_mm'];gmin=gmax-gt['GT_top_to_bottom_span_mm'];ax.axhline(gmax,c='gray',ls='--',label='GT max');ax.axhline(gmin,c='gray',ls=':',label='GT min');ax.axhline(gt['H95_GT_mm'],c='black',ls='--',label='GT area H95');ax.set_xticks(range(3),tags,rotation=20);ax.set_ylabel('Signed distance to author base (mm)');ax.set_title(n+' complete height interval, not Hmax alone');ax.legend(fontsize=6);ax.grid(alpha=.2)
 ax=axs[1,2];ax.axis('off');ax.text(0,1,'After Ring-based Metric Recovery\nand Best 6-DoF Rigid Alignment\n\nOne transform per mesh for ALL metrics.\nScale fixed by CAD, not ICP/GT.\n\nGT/author base may be conditional.\nOpen/self-intersecting solids: strict IoU NaN.\nF-score is a surface tolerance proxy,\nnever a replacement named as solid IoU.\n\nSmall Dxy/Hmax errors do not prove\nstalk completeness; inspect full height\nspan, minimum point and GT-to-prediction.',va='top',fontsize=10)
 fig.suptitle('All eleven groups; same evaluator for011/012/013, no successful-case filtering\nError distributions and individual directions are available in the full CSV/JSON. Black dots: area-sampled H95.');finish(fig,'full/Quantitative_All_Cases.png')
if __name__=='__main__':main()
