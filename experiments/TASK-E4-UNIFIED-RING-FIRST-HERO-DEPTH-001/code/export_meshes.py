"""Export frozen world meshes for viewing, never change prediction arrays."""
from pathlib import Path
import numpy as np
import trimesh
import pipeline as p
from ring_first_3d.mainline.native.io import sha256,save_json
T=p.TASK;O=T/'runs/RF_ONLY_V1'

def main():
    assert p.read(O/'GT_EVALUATION_COMPLETE.json')['world_meshes_unchanged']
    for c in p.cases():
        for arm in ['B0','B1','B2']:
            src=Path(c['initial']['path']) if arm=='B0' else O/c['case']/'004/body'/arm/'FINAL.npz'
            if not src.exists():continue
            before=sha256(src);b=dict(np.load(src));out=O/c['case']/'004/exported'/arm;out.mkdir(parents=True,exist_ok=True);outputs=[]
            for key,name in [('F','WORLD_surface.ply'),('F_solid','WORLD_solid_cap.ply')]:
                dest=out/name;trimesh.Trimesh(b['V'],b[key],process=False).export(dest)
                loaded=trimesh.load(dest,process=False);delta=float(abs(np.asarray(loaded.vertices)-b['V']).max())
                assert delta<=1e-5 and np.array_equal(loaded.faces,b[key])
                outputs.append(dict(path=str(dest),sha256=sha256(dest),vertex_export_max_abs_mm=delta,faces_exact=True))
            assert sha256(src)==before
            save_json(out/'SOURCE.json',dict(input=str(src),sha256=before,arm=arm,world_coordinates=True,GT_transform_applied=False,unit='mm',authoritative_prediction='Original float64 NPZ; PLY coordinate precision verified with inherited 1e-5mm tolerance',inferred_base_faces=int(b['inferred_base_faces'].sum()),outputs=outputs))
    print('WORLD_MESH_EXPORT_COMPLETE',flush=True)

if __name__=='__main__':main()
