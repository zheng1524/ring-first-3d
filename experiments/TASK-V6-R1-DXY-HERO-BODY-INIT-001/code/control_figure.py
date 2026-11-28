from visualize import *
def main():
 a=read(T/'evidence/CONTROL_RESULT.json');root=T/'runs/control';truth=np.load(a['GT_shape']['path']);parent=np.load(root/'PARENT.npz');fig,axes=plt.subplots(2,3,figsize=(12,8));center=np.array([0.,0.,-4.]);n=np.array([0.,1.,0.]);B=np.array([[1,0],[0,0],[0,1]])
 for j,cond in enumerate(a['conditions']):
  ax=axes[0,j];seg=section(truth['V'],truth['F'],n,center);ax.add_collection(LineCollection((seg-center)@B,colors='#333333',linewidths=1.4,label='原虚拟 G01 真值'))
  seg=section(parent['V'],parent['F'],n,center);ax.add_collection(LineCollection((seg-center)@B,colors=COL['parent'],linewidths=1,label='完整粗母体'))
  path=root/(cond['name']+'.npz')
  if path.exists():
   m=np.load(path)
   for F,color in [(m['F'],COL['body']),(m['F_solid'][m['inferred_base_faces']],COL['cap'])]:ax.add_collection(LineCollection((section(m['V'],F,n,center)-center)@B,colors=color,linewidths=1.7))
  pl=np.array(cond['plane']);ax.axhline(-pl[3]/pl[2]-center[2],ls='--',color='#bb3333');ax.set(xlim=(-8,8),ylim=(-11,8),xlabel='X / mm',ylabel='Z-参考点 / mm',title=cond['name']);ax.set_aspect('equal');ax.grid(alpha=.2)
  below=axes[1,j];rows=cond['metrics']['depth'];N=sum(r['fixed_N']for r in rows);hit=sum(r['valid_N']for r in rows);cap=sum(r['cap_only_N']for r in rows);below.bar(['有效主体','仅底盖','无有效主体'],[hit,cap,N-hit-cap],color=[COL['body'],COL['cap'],COL['missing']]);below.set_ylim(0,N);below.set_ylabel('固定观测数');below.set_title(f"切侧观测 {cond['original_trusted_cut_side_N']}/{N}\n{cond['clip_error']or'真实三角裁切完成'}",fontsize=9)
 fig.suptitle('既有虚拟 G01 控制实验：真实三角面剖面与错误基底\n黑 原虚拟形状 / 蓝 完整粗母体 / 绿 裁切主体 / 紫 推断底盖；无 GT 拟合或参数选优',fontsize=12);fig.tight_layout(rect=(0,0,1,.92));out=T/'figures';out.mkdir(exist_ok=True);fig.savefig(out/'CONTROL_BASE_FAILURE.png',dpi=130);plt.close(fig)
if __name__=='__main__':main()
