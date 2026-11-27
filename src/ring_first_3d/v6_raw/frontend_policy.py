"""Identity and scheduling rules for the explicitly approved frontend pilot."""
import numpy as np
import copy

def bind_validation(validation, version):
 out=copy.deepcopy(validation);out['primary']=version
 out['coverage']=sorted(out['coverage'],key=lambda x:x['version']!=version)
 assert out['coverage'][0]['version']==version
 return out

def finite_le(value, limit):
 return value is not None and bool(np.isfinite(value)) and value<=limit

def region_scale(contour_count, region_count):
 return np.sqrt(max(1,contour_count)/max(1,region_count))

def anchor_component(n, edges, reference):
 neighbours=[set() for _ in range(n)]
 for i,j in edges:neighbours[i].add(j);neighbours[j].add(i)
 visited=set();todo=[reference]
 while todo:
  i=todo.pop()
  if i in visited:continue
  visited.add(i);todo.extend(neighbours[i]-visited)
 return sorted(visited)

def temporal_edges(full_views, retained):
 index={old:new for new,old in enumerate(retained)};out=[]
 for i in range(len(full_views)-1):
  a,b=full_views[i:i+2]
  if i in index and i+1 in index and a.get('media_type','video')==b.get('media_type','video')=='video' and a.get('video_id')==b.get('video_id'):
   out.append((index[i],index[i+1]))
 return out

def unique_eligible(views, indices, diagnostic):
 seen=set();out=[]
 for i in indices:
  if i==diagnostic:continue
  identity=views[i]['physical_view_id']
  if identity in seen:continue
  seen.add(identity);out.append(i)
 return out

def select_plan_version(plans, primary):
 if plans[primary]['budget']>0:return primary
 for version in sorted(plans):
  if version!=primary and plans[version]['budget']>0:return version
 return primary

def view_tag(view):
 return 'photo_'+view['photo_id'] if view.get('media_type')=='photo' else f"{view['raw_frame']:05d}"

def match_partners(i, views, offsets):
 return [j for j in range(i+1,len(views)) if views[i].get('media_type','video')=='photo' or views[j].get('media_type','video')=='photo' or j-i in offsets]
