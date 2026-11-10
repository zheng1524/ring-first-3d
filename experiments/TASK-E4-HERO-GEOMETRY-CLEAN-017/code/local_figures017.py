from figures017 import *
def main():
    rows=load(R/'config/SOURCE_LOCK.json');ids=['G01_004_new_r00','G03_key04_raw00554','G05_key04_raw00542','G06_004_ref04','G01_004_growth_r10'];records=[]
    for cid in ids:
        r=next(r for r in rows if r['source_id']==cid);a=dict(np.load(R/'final_results'/cid/'ARCHIVE_RAW/FACE_EVIDENCE.npz'));state=a['state'];score=np.nan_to_num(a['perspective_stretch'],nan=0.);ii=np.flatnonzero(a['two_sided_gap_face'])
        if not len(ii):ii=np.argsort(score)[-3:]
        ii=ii[:3];fig,axs=plt.subplots(len(ii),4,figsize=(16,4*len(ii)),squeeze=False);im=np.asarray(Image.open(r['RGB']));lab=np.asarray(Image.open(r['Mask']))
        for k,j in enumerate(ii):
            vids=a['F'][j];nu=a['native_uv'][vids];q=np.c_[nu,np.ones(3)]@np.linalg.inv(a['Kn']).T@np.array(r['K']).T;uv=q[:,:2]/q[:,2:];centre=uv.mean(0);ax=axs[k,0];frame(ax,r);ax.plot(*np.r_[uv,uv[:1]].T,c='red',lw=1.4);ax.annotate(str(int(a['original_face_id'][j])),xy=centre,xytext=(10,20+20*k),color='red',arrowprops=dict(arrowstyle='->',color='red'))
            ax=axs[k,1];ax.imshow(im);ax.plot(*np.r_[uv,uv[:1]].T,c='red',lw=1.3);ax.scatter(*uv.T,c=['cyan','yellow','magenta'],s=25);ax.set_xlim(max(0,centre[0]-18),min(im.shape[1],centre[0]+18));ax.set_ylim(min(im.shape[0],centre[1]+18),max(0,centre[1]-18));ax.axis('off');ax.set_title('Original RGB crop; actual triangle pixels')
            c=a['native_uv'][a['F']].mean(1);nativecentre=nu.mean(0);sel=np.linalg.norm(c-nativecentre,axis=1)<5
            render(axs[k,2],a,r,sel=sel,fc=COLORS[state],title='Source 5px neighborhood | original 3D\nfull Ring CAD, no geometry edited')
            text=f"Original archived face ID {int(a['original_face_id'][j])}\nstate={['TRUSTED','UNCERTAIN','REJECTED','UNKNOWN'][state[j]]}\npixel IDs {a['native_pixel_id'][vids].tolist()}\nperspective stretch={a['perspective_stretch'][j]:.2f}\nnormal angle={a['normal_angle_deg'][j]:.1f} deg\ntriangle quality={a['triangle_quality'][j]:.4f}\nnative depth range={a['native_depth_jump_mm'][j]:.3f} mm\nMask distance={a['boundary_distance_native_px'][j]:.2f} native px\nCAD min={a['CAD_min_signed_mm'][j]:.3f} mm\n2-sided gap={bool(a['two_sided_gap_face'][j])}\nActually removed={state[j]==2}"
            axs[k,3].text(0,.95,text,va='top',fontsize=8);axs[k,3].axis('off');records.append(dict(source=cid,original_native_face_id=int(a['original_face_id'][j]),face_index=int(j),figure='figures/local_archive/'+cid+'_Face_ID_Evidence.png',not_GT_or_model_selection=True))
        fig.suptitle(cid+' | Locatable original faces, original RGB and actual geometry\nDiagnostic crop only; full original surfaces remain in core figures. No normals/XYZ smoothing or depth filling.');fig.tight_layout(rect=[0,0,1,.94]);out(fig,'local_archive/'+cid+'_Face_ID_Evidence.png')
    table('metrics/FIGURE_ARCHIVE_FACE_ID_INDEX.csv',records);print('FIVE_FACE_ID_DETAIL_FIGURES',flush=True)
if __name__=='__main__':main()
