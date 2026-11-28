"""Frozen controlled G01 bias evidence; one column, no fitting or parameter edits."""
from common import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
FONT='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
font_manager.fontManager.addfont(FONT)
plt.rcParams.update({'font.family':'Noto Sans CJK JP','axes.unicode_minus':False})

def main():
    data_path=T/'evidence/CONTROL_REVISION.json';data=read(data_path)
    generator_path=T/'runs/control/GENERATOR.json';generator=read(generator_path)
    conditions={r['condition']:r for r in data['conditions']}
    files=[asset(data_path),asset(generator_path)]
    for r in conditions.values():
        freeze=r['prediction_freeze'];asset(freeze['path'],freeze['sha256']);files.append(freeze)
        m=T/'runs/control'/(r['condition']+'_BODY.npz');mesh=np.load(m)
        np.testing.assert_array_equal(mesh['b'],r['fitted_b_mm']);files.append(asset(m))
        diagnostic=T/'runs/control'/(r['condition']+'_FIXED_GT_DIAGNOSTIC.json')
        np.testing.assert_array_equal(read(diagnostic)['b'],r['fixed_true_geometry_fitted_b_mm']);files.append(asset(diagnostic))
    zero=conditions['ZERO'];injected=conditions['OPPOSITE_025'];x=np.arange(4)
    labels=['004 / new_r00','004 / raw00282','005 / raw00104','005 / raw00694']
    fig,axes=plt.subplots(3,1,figsize=(9,12.2),sharex=True,sharey=True)
    for ax in axes:
        ax.axhline(0,color='#a0a0a0',lw=.8);ax.grid(axis='y',alpha=.25);ax.set_ylim(-.32,.32);ax.set_yticks(np.arange(-.3,.31,.1));ax.set_ylabel('来源轴向偏置 b / mm');ax.set_xlim(-.45,3.45)
    for ax,r,title in zip(axes[:2],[zero,injected],['零注入：实际九参数主体与来源偏置联合求解','±0.25 mm 注入：实际九参数主体与来源偏置联合求解']):
        truth=np.array(r['injected_b_mm']);fitted=np.array(r['fitted_b_mm'])
        ax.plot(x,truth,'D',color='#414141',ms=5,label='注入值（冻结后评价）')
        ax.plot(x,fitted,'o',color='#2875b9',ms=7,label='实际 theta/b 优化')
        for i,(a,b) in enumerate(zip(truth,fitted)):
            ax.plot([i,i],[a,b],color='#2875b9',lw=1.3)
            ax.annotate(f'{b:+.4f}',(i,b),xytext=(0,13 if b>=0 else -18),textcoords='offset points',ha='center',fontsize=10,color='#15548c')
        ax.set_title(title+'\n平均绝对偏差 '+f"{np.mean(abs(fitted-truth)):.4f}"+' mm',fontsize=12,pad=12)
        ax.legend(loc='upper right',fontsize=9)
    ax=axes[2];truth=np.array(injected['injected_b_mm']);fixed=np.array(injected['fixed_true_geometry_fitted_b_mm']);fixed0=np.array(zero['fixed_true_geometry_fitted_b_mm'])
    ax.plot(x,truth,'D',color='#414141',ms=5,label='±0.25 mm 注入值')
    ax.plot(x,fixed,'s',color='#cf762b',ms=7,label='固定 GT 几何：同带先验 b 优化器')
    ax.plot(x,fixed0,'x',color='#3c8c5d',ms=8,mew=2,label='固定 GT 几何：零注入')
    for i,b in enumerate(fixed):ax.annotate(f'{b:+.4f}',(i,b),xytext=(0,13 if b>=0 else -18),textcoords='offset points',ha='center',fontsize=10,color='#9b5318')
    ax.set_title('单独诊断：几何固定为真实网格；不是自由主体结果\n非零注入最大偏差 '+f"{max(abs(fixed-truth)):.4f}"+' mm；零注入最大 |b| '+f"{max(abs(fixed0)):.2e}"+' mm',fontsize=12,pad=12)
    ax.legend(loc='upper right',fontsize=9);ax.set_xticks(x,labels,fontsize=10);ax.set_xlabel('实际生成的四个 FIT 来源（两个视频，公制尺度固定）')
    fig.suptitle('受控虚拟 G01：整体轴深度偏置能否由有界 b 解释\n原有虚拟几何与渲染器；合成理想轴深度输入；全部曲线来自已冻结求解结果',fontsize=13,y=.99)
    fig.text(.5,.015,'上两行：真实低维 theta/b 求解。下行：固定 GT 几何的求解器诊断，单独标记。\n所有方法使用相同偏置先验；无 median(D−GT) 替代优化；不代表真实数据已完成深度校准。',ha='center',fontsize=10)
    fig.tight_layout(rect=(0,.065,1,.94),h_pad=3)
    destination=T/'figures/CONTROL_BIAS.png';destination.parent.mkdir(parents=True,exist_ok=True);fig.savefig(destination,dpi=140);plt.close(fig)
    save(T/'evidence/CONTROL_BIAS_FIGURE.json',dict(figure=asset(destination),code=asset(Path(__file__)),inputs=files,layout='3_rows_1_column',units='mm',control_only=True,GT_scope='generation and frozen evaluation; fixed-GT geometry solver diagnostic separately labeled',new_optimization=False,source_ids=generator['selected'][:4],drawn_values={name:{k:r[k]for k in ['injected_b_mm','fitted_b_mm','fixed_true_geometry_fitted_b_mm']}for name,r in conditions.items()}))
    print(destination)
if __name__=='__main__':main()
