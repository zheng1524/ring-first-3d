"""Actual Chrome/CDP rendering checks: full Mesh, every case's exact cuts."""
import asyncio,json,urllib.request,base64
from urllib.parse import quote
from pathlib import Path
import websockets
TD=Path.cwd()/'experiments/TASK-E4-MULTISURFACE-STRESS-AND-REAL-PILOT-001';VIS=TD/'visualization';PORT=9339
async def open_page(path):
 request=urllib.request.Request(f'http://127.0.0.1:{PORT}/json/new?'+quote(path.as_uri(),safe=''),method='PUT');p=json.load(urllib.request.urlopen(request));await asyncio.sleep(.4);return p
async def check(path,kind):
 page=await open_page(path);i=0;exceptions=[]
 async with websockets.connect(page['webSocketDebuggerUrl'],max_size=30000000)as ws:
  async def cmd(method,params):
   nonlocal i
   i+=1;ident=i;await ws.send(json.dumps(dict(id=i,method=method,params=params)))
   while True:
    r=json.loads(await ws.recv())
    if r.get('method')=='Runtime.exceptionThrown':exceptions.append(r)
    if r.get('id')==ident:return r
  async def ev(expr):
   r=await cmd('Runtime.evaluate',dict(expression=expr,returnByValue=True));assert not r.get('result',{}).get('exceptionDetails'),r;return r['result']['result'].get('value')
  await cmd('Runtime.enable',{});await cmd('Emulation.setDeviceMetricsOverride',dict(width=1680,height=1900,deviceScaleFactor=1,mobile=False))
  if kind=='cuts':
   keys=await ev('S.keys');count=await ev('S.frames.length');tested=[]
   for key in keys:
    await ev('sel.value='+json.dumps(key)+';draw();true')
    for retry in range(100):
     ready=await ev('!!CUT_CASES['+json.dumps(key)+'] && document.querySelector("#details").textContent.startsWith('+json.dumps(key)+')')
     if ready:break
     await asyncio.sleep(.02)
    assert ready,(str(path),key)
    value=await ev('({exact:CUT_CASES[sel.value].exact_triangle_intersection,views:CUT_CASES[sel.value].after.length,coarse:CUT_CASES[sel.value].coarse.length,planes:CUT_CASES[sel.value].fused.length})');assert value==dict(exact=True,views=count,coarse=count,planes=4),value;tested.append(key)
   await ev("document.querySelector('#v004').checked=false;draw();true");a=(await cmd('Page.captureScreenshot',dict(format='png')))['result']['data'];await ev("document.querySelector('#v004').checked=true;document.querySelector('#v005').checked=false;draw();true");b=(await cmd('Page.captureScreenshot',dict(format='png')))['result']['data'];assert a!=b
   await ev("document.querySelector('#v005').checked=true;draw();true");result=dict(path=str(path),kind=kind,status='PASS',cases=len(keys),views=count,exact_original_triangle_intersections=True,video_toggles=True,JavaScript_exceptions=len(exceptions))
  else:
   structure=await ev('({views:S.frames.length,triangles:S.frames.reduce((n,f)=>n+S.meshes[f.id].F.length,0),webgl:!!gl,glerror:gl.getError()})');assert structure['webgl']and structure['glerror']==0 and structure['triangles']>10000,structure
   count=structure['views'];tested=[];methods=['M0','ICP','BODY_VIDEO','BODY_HIER']+(['BODY_HIER_CTF']if count==16 else[])
   for method in methods:
    for stage in ['before','after','fusion']:
     await ev('ms.value='+json.dumps(method)+';ss.value='+json.dumps(stage)+';draw();true');info=await ev('document.querySelector("#info").textContent');assert 'shown: '+str(count)+'/'+str(count)in info,info[:200];assert await ev('gl.getError()')==0;tested.append([method,stage])
   await ev("document.querySelector('#video004').checked=false;draw();true");hidden=await ev('document.querySelector("#info").textContent');expected=await ev("S.frames.filter(f=>f.video==='005').length");assert 'shown: '+str(expected)+'/'+str(count)in hidden,hidden[:200]
   await ev("document.querySelector('#video004').checked=true;checks[S.frames[0].id].checked=false;draw();true");info=await ev('document.querySelector("#info").textContent');assert 'shown: '+str(count-1)+'/'+str(count)in info
   await ev("checks[S.frames[0].id].checked=true;ms.value='BODY_HIER';ss.value='fusion';draw();true");result=dict(path=str(path),kind=kind,status='PASS',structure=structure,states=tested,video_toggle=True,per_view_toggle=True,JavaScript_exceptions=len(exceptions))
  assert not exceptions,exceptions
  shot=await cmd('Page.captureScreenshot',dict(format='png'));name=('SIM'if path.parent==VIS else path.parent.name)+'_'+kind.upper();(TD/'evidence'/('BROWSER_'+name+'.png')).write_bytes(base64.b64decode(shot['result']['data']))
  print(json.dumps({k:v for k,v in result.items()if k!='states'}),flush=True);return result
async def main():
 results=[]
 for folder in [VIS,VIS/'G01',VIS/'G03',VIS/'G05']:
  results.append(await check(folder/'sections_all.html','cuts'));results.append(await check(folder/'multisurface_3d.html','mesh'))
 receipt=dict(status='PASS',pages=len(results),exact_cut_cases=sum(r.get('cases',0)for r in results),offline=True,results=results);(TD/'evidence/OFFLINE_BROWSER_VERIFICATION.json').write_text(json.dumps(receipt,indent=2)+'\n');print('ALL OFFLINE PAGES PASSED',receipt['exact_cut_cases'])
asyncio.run(main())
