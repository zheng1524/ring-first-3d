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

def extend_video_tracks(old_xy,old_category,old_held,mixed_xy,mixed_category):
 """Preserve every original video observation/track ID; add unambiguous photo links.

 Mixed union tracks which merge distinct original tracks are rejected, rather than
 moving original held observations into training. New tracks have no old keypoints.
 """
 n=old_xy.shape[1];lookup={}
 for t in range(len(old_xy)):
  for i in np.flatnonzero(np.isfinite(old_xy[t,:,0])):lookup.setdefault((int(i),*old_xy[t,i]),set()).add(t)
 associations=[];owners={};ambiguous=0
 for t,row in enumerate(mixed_xy):
  found=set().union(*(lookup.get((int(i),*row[i]),set()) for i in np.flatnonzero(np.isfinite(row[:n,0]))))
  associations.append(found)
  if len(found)==1:owners.setdefault(next(iter(found)),[]).append(t)
  elif len(found)>1:ambiguous+=1
 out=np.full((len(old_xy),mixed_xy.shape[1],2),np.nan);out[:,:n]=old_xy
 rows=list(out);cats=list(old_category);held=list(old_held);mapping={};added=0
 for t,found in enumerate(associations):
  if len(found)>1:continue
  if len(found)==1:
   dest=next(iter(found))
   if len(owners[dest])!=1 or mixed_category[t]!=old_category[dest]:continue
   rows[dest][n:]=mixed_xy[t,n:];mapping[t]=dest
  else:
   dest=len(rows);mapping[t]=dest;rows.append(mixed_xy[t].copy());cats.append(mixed_category[t]);held.append(dest%5==0);added+=1
 return np.asarray(rows),np.asarray(cats),np.asarray(held,dtype=bool),mapping,dict(original_tracks=len(old_xy),new_tracks=added,ambiguous_old_track_merges=ambiguous,fragmented_old_tracks=sum(len(v)>1 for v in owners.values()),original_video_observations_unchanged=True,original_train_held_unchanged=True)
