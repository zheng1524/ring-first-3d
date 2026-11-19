"""Exact sequential raw-frame SHA binding only; never selects training views."""
from pathlib import Path
import cv2
import numpy as np
import pipeline as p
from ring_first_3d.mainline.native.io import save_json,sha256

def main():
    cv2.setNumThreads(1);catalog=p.read(p.TASK/'audit/CALIBRATION_INPUTS.json');inventory=p.read(p.TASK/'audit/RAW_DATA_INVENTORY.json')['files'];result=[]
    for c in catalog:
        g,video=c['group'],c['video'];raw=next(r for r in inventory if r['group']==g and r['path'].endswith('_'+video+'.mp4'))
        desired={}
        for v in c['views']:desired.setdefault(v['RGB_array_SHA256'],[]).append(dict(id=v['id'],role='CALIBRATION_FIT',RGB_source=v['RGB_source']))
        for v in p.instance_views(g,video):desired.setdefault(v['meta']['RGB_content_sha'],[]).append(dict(id=v['meta']['id'],role=v['meta']['role'],RGB_source=v['meta']['RGB_source']))
        found={};cap=cv2.VideoCapture(raw['path']);idx=0
        while True:
            ok,im=cap.read()
            if not ok:break
            rgb=cv2.cvtColor(cv2.resize(im,(640,360),interpolation=cv2.INTER_AREA),cv2.COLOR_BGR2RGB);h=p.arraysha(rgb)
            if h in desired:found.setdefault(h,[]).append(idx)
            idx+=1
        cap.release()
        rows=[dict(**v,RGB_pixel_SHA256=h,status='EXACT_RAW_PIXEL_MATCH' if h in found else 'ARCHIVED_IMAGE_SHA_BOUND_RAW_INDEX_UNVERIFIED',raw_frames=found.get(h,[])) for h,vv in desired.items() for v in vv]
        result.append(dict(group=g,video=video,raw=raw,decoded_frames=idx,rows=rows,frame_selection_changed=False))
        print('RAW_BINDING',g,video,sum(h in found for h in desired),len(desired),flush=True)
    save_json(p.TASK/'audit/RAW_FRAME_BINDING.json',result)

if __name__=='__main__':main()
