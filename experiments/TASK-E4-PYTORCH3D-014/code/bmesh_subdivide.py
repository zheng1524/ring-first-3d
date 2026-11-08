"""Run in Blender background. CPU interpolation only, no smooth or projection."""
import bpy,bmesh,numpy as np,sys
p=sys.argv.index('--');source,target=sys.argv[p+1:p+3];a=np.load(source);bm=bmesh.new()
for v in a['V']:bm.verts.new(v)
bm.verts.ensure_lookup_table()
for f in a['F_solid']:bm.faces.new([bm.verts[int(i)]for i in f])
bm.faces.ensure_lookup_table();bm.edges.ensure_lookup_table();layer=bm.faces.layers.int.new('source_original_face')
for i,f in enumerate(bm.faces):f[layer]=i+1
selected=set()
for i in np.flatnonzero(a['selected_faces']):selected.update(bm.faces[int(i)].edges)
if selected:bmesh.ops.subdivide_edges(bm,edges=list(selected),cuts=1,use_grid_fill=True,smooth=0.,use_sphere=False)
bmesh.ops.triangulate(bm,faces=list(bm.faces));bm.verts.ensure_lookup_table();bm.verts.index_update();V=np.array([v.co[:]for v in bm.verts],float);F=np.array([[v.index for v in f.verts]for f in bm.faces],int);parent=np.array([f[layer]-1 for f in bm.faces],int);np.savez_compressed(target,V=V,F_solid=F,parent_coarse_face=parent);bm.free()
