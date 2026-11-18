"""Supplement audit exports and definitions; does not execute scientific algorithms."""
import os,csv,gzip,json,sqlite3,hashlib,re,collections,shutil
from pathlib import Path
OUT=Path(__file__).resolve().parents[1];ROOT=OUT.parents[1]
c=sqlite3.connect('file:'+str(OUT/'ASSET_INVENTORY.sqlite')+'?mode=ro',uri=True)
def dump(name,d):(OUT/name).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()
def export(query,name,args=()):
 cur=c.execute(query,args)
 with gzip.open(OUT/name,'wt',newline='')as f:
  w=csv.writer(f);w.writerow([x[0]for x in cur.description]);w.writerows(cur)
# Preserve the erroneous first export before correction for independent review.
first=OUT/'SYMLINKS_INITIAL_EMPTY_EXPORT.csv.gz'
if not first.exists():shutil.copyfile(OUT/'SYMLINKS.csv.gz',first)
export('SELECT * FROM assets WHERE kind=?','SYMLINKS.csv.gz',('symlink',))
dump('AUDIT_REVISIONS.json',[dict(id='AR001',type='ENGINEERING_EXPORT_ERROR',found_by='Independent second agent IR-009',cause='SQLite double-quoted symlink was resolved as the existing symlink column, not a string literal',repair='Parameter-bound kind query on existing immutable scan database; initial empty export retained',corrected_symlinks=c.execute('SELECT count(*) FROM assets WHERE kind=?',('symlink',)).fetchone()[0],source_rescan=False),dict(id='AR002',type='RUNTIME_INVOCATION',cause='Existing shell launchers are 0644; direct subprocess invocation raises PermissionError',repair='Invoke unchanged launcher with bash; actual import results in LAYERED_RUNTIME_PROBE.json; source permissions not modified',source_write=False)])
# Same-path differing bytes represent version/run relationships, never strict duplicates.
groups=collections.defaultdict(list)
for path,root,task,h,size in c.execute('SELECT path,root,task,sha256,size FROM assets WHERE kind=?',('file',)):
 rel=str(Path(path).relative_to(root));groups[(task,rel)].append(dict(path=path,sha256=h,size=size))
versions=[dict(task=task,relative_path=rel,kind='D_DIFFERENT_RUNS' if any(x in rel.lower()for x in ['runs/','attempts/','metrics','results/']) else 'C_DIFFERENT_VERSION',assets=rows,decision='KEEP_ALL_VERSIONS',comparison='Different SHA256; no geometric/visual similarity inference')for(task,rel),rows in groups.items()if len({x['sha256']for x in rows})>1]
with gzip.open(OUT/'VERSION_AND_RUN_RELATIONSHIPS.json.gz','wt')as f:json.dump(versions,f,ensure_ascii=False)
strict=c.execute('SELECT count(*),sum(size*(n-1)) FROM (SELECT size,count(*) n FROM assets WHERE kind=? GROUP BY sha256,size HAVING count(*)>1)',('file',)).fetchone()
physical=c.execute('SELECT sum(size*(n-1)) FROM (SELECT sha256,size,count(distinct printf("%d:%d",dev,inode)) n FROM assets WHERE kind=? GROUP BY sha256,size HAVING n>1)',('file',)).fetchone()[0]
unique=c.execute('SELECT count(*),sum(size) FROM (SELECT size FROM assets WHERE kind=? GROUP BY sha256,size HAVING count(*)=1)',('file',)).fetchone()
dump('DUPLICATE_ASSET_REPORT.json',dict(strict_AB_groups=strict[0],logical_repeated_bytes=strict[1],different_inode_identical_content_logical_bytes=physical,version_or_run_groups=len(versions),single_path_hash_assets=unique[0],single_path_hash_logical_bytes=unique[1],A='Identical SHA256 and bytesize with same basename',B='Identical SHA256 and bytesize across differing names',C='Different bytes under same scoped relative path; kept as versions, semantic similarity unverified',D='Different run/attempt/metric artifacts, all retained',limitations='No deletion candidates are approved. Physical different-inode duplicate logical bytes is not filesystem savings: references, hardlinks, shared extents, metadata and recovery are separate. Identical bytes do not erase provenance. UNIQUE_* values are conservative extension/path protection heuristics, not proof of raw origin or global uniqueness. All UNKNOWN retained.'))
# Static path/import assumptions across every inventoried .py/.sh file.
patterns={'absolute_path':re.compile('/home/liu/'),'sys_path':re.compile(r'sys\.path|PYTHONPATH'),'dynamic_import':re.compile(r'importlib|__import__|\bexec\('),'relative_path':re.compile(r'__file__|getcwd|\bcwd\b|chdir'),'weights':re.compile(r'\.ckpt|\.pth|torch\.load|checkpoint'),'data_path':re.compile(r'DATA_ROOT|data_root|data_path|input_root|\.local_data')}
cache={};nfiles=0;counts=collections.Counter()
with gzip.open(OUT/'SCRIPT_DEPENDENCY_AUDIT.csv.gz','wt',newline='')as f:
 w=csv.writer(f);w.writerow(['path','sha256','pattern','line','status'])
 for path,h in c.execute('SELECT path,sha256 FROM assets WHERE kind=? AND extension IN (?,?)',('file','.py','.sh')):
  nfiles+=1
  if h not in cache:
   matches=[]
   try:
    for no,line in enumerate(Path(path).read_text(errors='replace').splitlines(),1):
     for name,p in patterns.items():
      if p.search(line):matches.append((name,no))
   except OSError:matches=[('UNREADABLE',0)]
   cache[h]=matches
  for name,no in cache[h]:counts[name]+=1;w.writerow([path,h,name,no,'STATIC_REFERENCE_ONLY_NOT_RUNTIME_PROOF'])
dump('SCRIPT_DEPENDENCY_SUMMARY.json',dict(files=nfiles,distinct_content=len(cache),counts=dict(counts),limitations='All inventoried .py/.sh scanned. Line numbers and full-file SHA, no secrets/snippets exported. Dynamic path evaluation not executed and may remain unresolved. Absence of reference is not proof unused.'))
# Runtime base prefixes are external shared dependencies, not independent project venvs.
envdata=json.loads((OUT/'RUNTIME_ENVIRONMENTS.json').read_text());base=[]
for prefix in sorted({x['probe'].get('base_prefix')for x in envdata['environments']if x['probe'].get('base_prefix')}):
 p=Path(prefix);inodes={};files=links=0;logical=0
 for d,dirs,names in os.walk(p,followlinks=False):
  dirs[:]=[x for x in dirs if x!='.git'and not Path(d,x).is_symlink()]
  for name in names:
   q=Path(d,name)
   try:
    s=q.lstat();files+=1;logical+=s.st_size;links+=q.is_symlink();inodes[(s.st_dev,s.st_ino)]=s.st_blocks*512
   except OSError:pass
 base.append(dict(path=prefix,files=files,symlinks=links,logical_bytes=logical,unique_inode_allocated_bytes=sum(inodes.values()),hash_scope='Size/ABI audit only; full environment payload SHA not claimed',referencers=[x['environment_path']for x in envdata['environments']if x['probe'].get('base_prefix')==prefix],decision='KEEP_SHARED_EXTERNAL_RUNTIME'))
dump('SHARED_BASE_ENVIRONMENTS.json',base)
# Exact ZIP categories explain why the prior 2865 figure is not a full central-directory count.
members=json.load(gzip.open(OUT/'SMART_ENDOSCOPE_ARCHIVE_MEMBERS.json.gz','rt'))
jpg=[x for x in members if Path(x['name']).suffix.lower()=='.jpg']
prefixes=collections.Counter('/'.join(x['name'].split('/')[:3])for x in jpg)
dump('SMART_ENDOSCOPE_COUNT_RECONCILIATION.json',dict(previous_reported_jpg=2865,current_all_jpg_members=len(jpg),unique_jpg_content_hashes=len({x['sha256']for x in jpg}),archive_scope='Full ZIP member listing, no extraction',prefix_counts=dict(prefixes),previous_scope='UNVERIFIED: 2865 is not the full current central-directory JPG count; no unsupported equivalence asserted',all_members_preserved=True))
# Candidate discovery for broken report paths: never promote filename-only matches as repaired identity.
with (OUT/'REPORT_LINK_AUDIT.csv').open()as f:links=list(csv.DictReader(f))
candidates=[]
needed={Path(r['resolved_path']).name for r in links if r['status']in ['BROKEN_TARGET','MISSING_ASSET']}
byname=collections.defaultdict(list)
for path,h,size in c.execute('SELECT path,sha256,size FROM assets WHERE kind=?',('file',)):
 if Path(path).name in needed:byname[Path(path).name].append((path,h,size))
for row in links:
 if row['status']not in ['BROKEN_TARGET','MISSING_ASSET']:continue
 name=Path(row['resolved_path']).name
 if not name or len(name)<6:continue
 matches=byname.get(name,[])
 task=next((x for x in Path(row['source']).parts if x.startswith('TASK-')),None)
 matches=[r for r in matches if task and '/'+task+'/'in r[0]]
 if matches:candidates.append(dict(source=row['source'],reference=row['reference'],status='CANDIDATES_ONLY_ORIGINAL_IDENTITY_UNVERIFIED',candidates=[dict(path=p,sha256=h,size=s,hash_status='HASH_INHERITED',hash_source='ASSET_INVENTORY current scan')for p,h,s in matches[:20]],total_candidates=len(matches)))
with gzip.open(OUT/'UNRESOLVED_LINK_CANDIDATES.json.gz','wt')as f:json.dump(candidates,f,ensure_ascii=False)
# Improve registry IO descriptions from the actual functional units and signatures.
registry=ROOT/'docs/registry/MODULE_REGISTRY.json';reg=json.loads(registry.read_text())
io={
 'projection_gate':('Mesh V/F, frozen FIT labels/K/c2w, Ring depth, balanced weights','Fresh visible Face/bary, R+/R-, strict contour pairs, per-view metrics and protection decisions'),
 'deformation_graph':('Reference V/F, deterministic geodesic nodes, SO(3) node rotation/translation','Shared deformed vertices, graph weights/edges and graph regularization'),
 'smooth_arap':('Reference/current V/F, lambda=.7, detached SVD local rotations','Spokes/rims ARAP, mass-weighted Laplacian smooth energy and mixed SARAP'),
 'bspline_sweep':('Attachment loop, B-spline controls, two softplus semi-axis profiles','Continuous sampled Sweep surface and shared boundary topology'),
 'rmf':('Sampled centerline positions and tangents','Double-reflection orthonormal continuous moving frame'),
 'ring_collision_gate':('Current/candidate Body material probes and fixed CAD probes','Bidirectional signed-depth/area/energy records and initial/current non-worsening decision'),
 'optimizer':('Frozen case views/weights/Ring and graph/sweep configuration','Accepted shared Body snapshots, node transforms, loss trace and gate rejections'),
 'growth_evidence':('Multi-view R+ candidates, calibrated projection Jacobians','Connected attachment proposal, two-video/3-view support, identifiability or UNDERCONSTRAINED_GROWTH'),
 'common':('Frozen case identity and historical exact013 asset references','Source-bound mm Mesh, masks, frozen FIT/HOLDOUT/camera/Ring data and independent geometry checks'),
 'recover':('Frozen iteration24 Body and saved rejected candidate, controls and root attachment','Recovered embedded candidate and immutable fixed input identities'),
 'embedded_sweep':('Frozen Body, historical controls/radii, bounded attachment parameters','Embedded B-spline Sweep and optimizable continuous surface'),
 'boolean_blender':('Body/Sweep operand OBJ and frozen Blender binary','Exact Boolean union Mesh via isolated subprocess'),
 'union_mesh':('Body and Sweep operands and Blender binary identity','Validated exterior union, face/material provenance or InvalidUnionCandidate'),
 'lengths':('Frozen spline controls and original Body signed-distance scene','Unique exit location, integrated total/embedded/exposed arc lengths'),
 'geometry_gate':('Candidate/operand Mesh and frozen geometry criteria','Watertightness, winding, intersections, root exterior-clearance records and accept/reject'),
 'ring_gate':('Current/candidate exterior union and fixed Ring CAD','Current-state-only bidirectional non-worsening collision decision and calibrated tolerance'),
 'projection':('Frozen Body/Mask/cameras, inherited candidate and fresh rendered proposal','Fresh full-view metrics, support, protection failures and accepted correspondence'),
 'optimize':('One inherited candidate, frozen Body, spline parameters, joint multiview loss','Bounded local Sweep updates, backtracks and rejection/accepted-state checkpoints'),
 'evaluate':('ALL predictions frozen and hash checked; only then Blender GT','Independent per-model SE3 and fixed INITIAL→GT copies, surface/FIT/HOLDOUT metrics, failures'),
 'io_utils':('Frozen source/input manifests and case identities','SHA-bound original Body/Mask/camera/candidate loading without GT in training'),
 'body_update':('Exact013 shared Body, balanced FIT contours and frozen geometry','Historical free-vertex/extrusion baseline, snapshots and original rejections; not current structured updater'),
 'data_adapter':('Frozen real/virtual source manifests','Same exact013 initializer, aligned input role contracts and initialization audit'),
 'hero_relocation':('Frozen Body, original HERO pixel/depth Mesh and frozen cameras','Historical bounded ray-depth relocation and preserved source topology; no Body feedback'),
 'repair_adoption':('Original failed/repaired code/inputs and stage freezes','Hash/AST-guarded valid-stage restoration evidence, no silent recomputation'),
 'pipeline':('Frozen task/run identity and authorized phase','Runner stage dispatch, regression/source audit/prediction freeze and independent evaluation records'),
 'experiment':('Frozen task and authorized scientific phase','Historical C0/real/relocation dispatch with role-separated independent GT evaluation'),
 'figures':('Frozen predictions/metrics and evaluation copies','Actual Mesh/contour/section PNGs and explicit negative evidence'),
 'visualize':('Frozen predictions/metrics, Boolean operands and root/GT diagnostics','Real surface/section/projection/root visualizations and failure reports')}
stemids=collections.defaultdict(list)
for m in reg['modules']:
 if m['id'].startswith(('SU','SB','GR')):stemids[Path(m['path']).stem].append(m['id'])
for m in reg['modules']:
 if not m['id'].startswith(('SU','SB','GR')):continue
 stem=Path(m['path']).stem
 if stem in io:m['input'],m['output']=io[stem]
 m['dependency_modules']=sorted({z for imp in m.get('dependencies',[])for z in stemids.get(imp,[])if z!=m['id']})
 m['dependency_module_note']='Import stem candidates include historical versions; exact imported version is established by frozen run source_root/contracts, not this stem map.'
registry.write_text(json.dumps(reg,ensure_ascii=False,indent=2)+'\n')
print('SUPPLEMENTS_DONE',len(versions),'version groups',len(candidates),'unresolved link candidate sets',flush=True)
