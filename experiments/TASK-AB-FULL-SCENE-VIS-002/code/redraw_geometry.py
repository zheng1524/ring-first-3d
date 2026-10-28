"""Display-only update to existing neutral glyphs; all cached metric values fixed."""
from render_cases import *
def main():
    rows=load(R/'metrics/results.json');plan=load(R/'provenance/PAIRS_FROZEN.json')['pairs']
    for r in rows:
        row=next(x for x in plan if x['pair_id']==r['pair_id']);d=scene_data(row['A']);out=R/'figures/cases'/row['pair_id'];gray,info=scene_image(d,d['p']['K'],d['p']['pose'],neutral=True);Image.fromarray(gray).save(out/'A_neutral_geometry.png');A=np.asarray(Image.open(d['c']['RGB']).convert('RGB'));B=np.asarray(Image.open(row['B_target']['RGB']).convert('RGB'));full=np.asarray(Image.open(out/'Full_AtoB_Scene.png'));pred=dict(np.load(r['prediction_path']));new,diff,roi=scene_metrics(pred,B,cv2.imread(row['B_target']['Mask'],0));assert clean(new)==r['new_point_scene'];figure_pair(row,d,A,B,gray,full,new,r['legacy_Polyp_only'],pred,diff,roi,out);r['geometry_render']=info;print('DISPLAY_ONLY',r['pair_id'],flush=True)
    both('results',rows);save('provenance/DISPLAY_FINAL.json',stamp([R/'display_config.json',Path(__file__)],change='Neutral point antialias=False as existing audit_renderer; no RGB style, XYZ, ROI, pose or metric changes'))
if __name__=='__main__':main()
