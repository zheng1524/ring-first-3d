"""Small original-photo input contact sheet and cached pose validation evidence."""
from io_utils import *
plt=vis.configure()
def main():
    rows=load(R/'metrics/source_view_inventory.json');photos=[x for x in rows if x['source_type']=='photo'];fig,ax=plt.subplots(4,4,figsize=(20,14));meta=[]
    for a,s in zip(ax.ravel(),photos):
        im=Image.open(s['file_path']).convert('RGB');im.load();a.imshow(im);a.set_title(s['source_id']+'｜原文件 '+str(im.size)+'\nUNREGISTERED；未从外观猜位姿',fontsize=9);a.axis('off');meta.append(dict(source_id=s['source_id'],raw_path=s['file_path'],sha256=sha(s['file_path']),size=list(im.size),RGB_readable=True,pose_inferred_this_task=False))
    for a in ax.ravel()[len(photos):]:a.axis('off')
    fig.suptitle('四组真实静态输入只读核对｜原图不是三维表面、不是已注册观测',fontsize=15);fig.tight_layout(rect=[0,0,1,.95]);dest=R/'figures/groups';dest.mkdir(parents=True,exist_ok=True);fig.savefig(dest/'all_photos_input_audit.png',dpi=110);plt.close(fig);both('raw_photo_audit',meta)
    # Surface/height pairing provenance is explicit: inherited user-confirmed record plus actual hashes.
    copy=load(OLD/'multigroup_surface_gt_vnext/inputs/groups.json');save('provenance/GT_PAIRING_EVIDENCE.json',stamp([OLD/'multigroup_surface_gt_vnext/inputs/groups.json',OLD/'multigroup_surface_gt_vnext/gt_mapping/GT_ASSET_AUDIT.json',OLD/'multigroup_surface_gt_vnext/code/export_gt_blender.py'],records=[x for x in copy if x['id']in ['G01','G06','G07','G08']],this_is_evaluation_only=True,new_pairing_inferred_from_filename=False))
    save('provenance/EVALUATION_ONLY_RECEIPT.json',stamp([R/'evaluation_only/BLENDER_VERIFICATION.json']+list((R/'evaluation_only').glob('*.npz')),publish_full_GT_geometry=False))
    print('SUPPLEMENTAL_SOURCE_AUDIT',len(meta),'photos')
if __name__=='__main__':main()
