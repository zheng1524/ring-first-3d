"""Three figures from actual RGB, original CAD and unmodified HERO XYZ."""
from common import *
import matplotlib.colors as mcolors
plt=vis.configure()
def done(fig,name):
    fig.savefig(R/'figures'/name,dpi=150,facecolor='white');plt.close(fig)
def rgb(ax,cid,title=None):
    ax.imshow(source(cid)['RGB']);ax.axis('off');ax.set_title(title or short(cid),fontsize=10)
def fmt(v):return 'NaN' if v is None else f'{v:.2f}'
def fig1(original):
    fig,axes=plt.subplots(5,3,figsize=(17,15))
    for i,cid in enumerate(IDS):
        s=source(cid);r=next(r for r in original['Ring'] if r['camera']==cid);z=np.load(R/f'runtime/ring/{short(cid)}_ORIGINAL.npz')
        rgb(axes[i,0],cid,f'{short(cid)} | frozen real RGB')
        img=np.ones((360,640,3));img[s['labels']==1]=.8;img[s['labels']==2]=0
        axes[i,1].imshow(img);axes[i,1].axis('off');axes[i,1].set_title('Actual Mask: Ring black / Polyp gray',fontsize=10)
        ax=axes[i,2];rgb(ax,cid);rgba=np.zeros((360,640,4));rgba[z['CAD_mask'],3]=1;ax.imshow(rgba,interpolation='nearest')
        for key,col in [('observed_boundary','#00dfe7'),('CAD_boundary','#ffb000')]:
            p=z[key];ax.scatter(p[:,0],p[:,1],s=.4,c=col,linewidths=0)
        st=r['visible_contour'];ax.set_title(f"Opaque black CAD; observed cyan / CAD orange\nqualified boundary med {st['median']:.2f}, p95 {st['p95']:.2f} px; {'PASS' if r['Ring_pass'] else 'NOT PASS'}",fontsize=9)
    fig.suptitle('Figure 1 | Original five cameras, same frozen CAD/K/Mask; no pose ground truth\nPolyp-contact and image-clipped boundaries excluded from qualified error, raw error retained; CAD units mm',fontsize=13)
    fig.tight_layout(rect=(0,0,1,.96));done(fig,'Figure1_Ring_validation.png')
def fig2(original):
    fig,axes=plt.subplots(3,3,figsize=(23,13));plans=load(R/'config/RGB_ONLY_METHOD_SELECTION.json');cmap=plt.get_cmap('RdYlGn_r')
    for ax,plan in zip(axes.flat,plans):
        a,b=plan['A'],plan['B'];method=plan['selected_method'] or 'SIFT';d=match_data(a,b,method);s,t=source(a),source(b);ax.imshow(np.concatenate([s['RGB'],t['RGB']],axis=1));ax.axis('off')
        F=fundamental(s['K'],s['T'],t['K'],t['T']);err=sampson(F,d['p'],d['q']);sel=np.flatnonzero(d['independent_good']&d['held']) if plan['selected_method'] else np.flatnonzero(d['usable']);ii=select_uniform(sel,24)
        for j in ii:
            p,q=d['p'][j],d['q'][j];color=cmap(np.clip(err[j]/6,0,1));ax.plot([p[0],q[0]+640],[p[1],q[1]],color=color,alpha=.65,lw=.6);ax.scatter([p[0],q[0]+640],[p[1],q[1]],s=8,c=[color],linewidths=.3,edgecolors='white')
        # Four deterministic frozen-pose epilines, never selected by low error.
        for j in ii[:4]:
            line=F@np.r_[d['p'][j],1.]
            if abs(line[1])>1e-10:
                xx=np.array([0.,639.]);yy=-(line[0]*xx+line[2])/line[1];ax.plot(xx+640,yy,color='#00ffff',lw=.6,alpha=.7)
        ax.set(xlim=(-.5,1279.5),ylim=(359.5,-.5))
        rec=next(r for r in original['pairs'] if r['A']==a and r['B']==b and r['method']==method);h=rec['groups']['held'];f=rec['groups']['fit']
        role='EXTRA ref13 HOLDOUT (never pose-fit)' if plan['extra_holdout'] else 'ref03/ref08 relation'
        msg=f"{short(a)} → {short(b)} | {method} | {role}\n"
        msg+=f"RGB-F fit/held {f['N']}/{h['N']}; held Sampson med/p95 {fmt(h['error_px']['median'])}/{fmt(h['error_px']['p95'])} px\n"
        msg+=f"held <=2px {fmt(h['inlier_fraction'])}; {'PASS' if rec['pair_pass'] and plan['selected_method'] else 'INSUFFICIENT / NOT PASS'}\n"
        msg+='shown: held RGB-F consensus' if plan['selected_method'] else 'shown: raw usable matches only; insufficient RGB-F evidence'
        ax.set_title(msg,fontsize=9)
    fig.suptitle('Figure 2 | Real RGB correspondences; original frozen-pose epilines cyan; match error green→red (0→6 px)\nSame frozen fit/held protocol, all nine pairs; original poses shown; 0 bounded corrections triggered',fontsize=13)
    fig.tight_layout(rect=(0,0,1,.94));done(fig,'Figure2_real_matching_geometry.png')
def fig3(aux):
    fig,axes=plt.subplots(5,3,figsize=(17,15))
    for i,b in enumerate(IDS):
        a=IDS[0] if b==IDS[1] else IDS[1];r=next(r for r in aux if r['source']==a and r['target']==b and r['target_pose']=='ORIGINAL');p=np.load(R/f'runtime/projections/{short(a)}__{short(b)}_ORIGINAL.npz');cad=np.load(R/f'runtime/ring/{short(b)}_ORIGINAL.npz')['CAD_mask']
        rgb(axes[i,0],a,f"Actual source {short(a)} | original HERO XYZ\n{r['source_original_point_N']:,} points, no deformation")
        rgb(axes[i,1],b,f'Actual target {short(b)} | original K/c2w');axes[i,1].contour(source(b)['labels']==1,levels=[.5],colors=['#ef00c8'],linewidths=.6)
        ax=axes[i,2];ax.set_facecolor('white');black=np.zeros((360,640,4));black[cad,3]=1;ax.imshow(black,interpolation='nearest');ax.imshow(p['RGBA'],interpolation='nearest');ax.contour(source(b)['labels']==1,levels=[.5],colors=['#ef00c8'],linewidths=.6);ax.axis('off')
        camera(b).scale_bar(ax,2.5)
        ax.set_title(f"Unmodified source RGB-colored XYZ + opaque black CAD\nMask coverage {r['target_Polyp_coverage']:.1%}; precision {r['projected_Polyp_precision']:.1%}; CAD hidden {r['CAD_hidden']:,}",fontsize=9)
    fig.suptitle('Figure 3 | Original HERO cross-view projection, auxiliary only; no reconstructed or fused surface\nMagenta: actual target Polyp Mask. Source XYZ unit mm; perspective scale at Ring Z=0 only; geometry/depth/camera error conflated',fontsize=12)
    fig.tight_layout(rect=(0,0,1,.96));done(fig,'Figure3_original_HERO_projection.png')
def main():
    freeze('BEFORE_THREE_FIGURES.json',dict(no_case_reselection=True,Fig1_all5=True,Fig2_all9=True,Fig3_source='ref08 except ref08 target uses ref03',CAD_black_opaque=True))
    original=load(R/'config/ORIGINAL_TEST12.json');fig1(original);fig2(original);fig3(load(R/'config/HERO_AUXILIARY.json'))
    save('config/FIGURE_MANIFEST.json',[asset(p) for p in sorted((R/'figures').glob('*.png'))]);print('FIGURES_COMPLETE',3,flush=True)
if __name__=='__main__':main()
